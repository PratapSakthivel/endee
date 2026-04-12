"""
ErrorLens RAG Engine

This module provides Retrieval-Augmented Generation functionality using Groq API.
Combines semantic search results with LLM analysis for root cause analysis and fix suggestions.
"""

import logging
import os
import json
import time
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

from .endee_client import EndeeClient
from .embedder import Embedder

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for log analysis.
    
    Combines semantic search from Endee with LLM analysis from Groq
    to provide intelligent root cause analysis and fix suggestions.
    """
    
    def __init__(self, endee_client: EndeeClient, embedder: Embedder, 
                 groq_api_key: Optional[str] = None, model: str = "llama3-8b-8192"):
        """
        Initialize the RAG engine.
        
        Args:
            endee_client (EndeeClient): Initialized Endee client for vector search
            embedder (Embedder): Initialized embedder for query vectorization
            groq_api_key (str, optional): Groq API key. Defaults to GROQ_API_KEY env var.
            model (str): Groq model to use. Default is "llama3-8b-8192".
        """
        self.endee_client = endee_client
        self.embedder = embedder
        self.model = model
        
        # Initialize Groq client
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.groq_client = None
        self.groq_available = False
        
        if not GROQ_AVAILABLE:
            logger.warning("Groq library not available. Install with: pip install groq")
        elif not self.groq_api_key:
            logger.warning("GROQ_API_KEY not found in environment. RAG analysis will be disabled.")
        else:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.groq_available = True
                logger.info(f"RAG engine initialized with Groq model: {model}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self.groq_available = False
        
        # Configuration
        self.max_context_logs = 5  # Maximum logs to include in context
        self.timeout_seconds = 30  # Groq API timeout
        self.max_retries = 2       # Maximum retry attempts
        
        logger.info(f"RAG engine initialized. Groq available: {self.groq_available}")
    
    def _build_prompt(self, query: str, retrieved_logs: List[Dict[str, Any]]) -> str:
        """
        Build LLM prompt with query and retrieved log context.
        
        Args:
            query (str): User's natural language query
            retrieved_logs (List[Dict]): Retrieved log entries with metadata and scores
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Start with system context
        prompt = """You are an expert system administrator and software engineer specializing in log analysis and troubleshooting. Your task is to analyze error logs and provide actionable insights.

Given a user query and related log entries, provide:
1. **Root Cause Analysis**: Identify the most likely cause of the issue
2. **Fix Suggestions**: Specific, actionable steps to resolve the problem
3. **Prevention**: Recommendations to prevent similar issues in the future

Be concise, technical, and focus on practical solutions.

"""
        
        # Add user query
        prompt += f"**User Query:** {query}\n\n"
        
        # Add retrieved logs context
        if retrieved_logs:
            prompt += "**Related Log Entries:**\n"
            for i, log in enumerate(retrieved_logs, 1):
                metadata = log.get('metadata', {})
                score = log.get('score', 0)
                
                severity = metadata.get('severity', 'UNKNOWN')
                service = metadata.get('service', 'unknown')
                message = metadata.get('message', 'No message')
                timestamp = metadata.get('timestamp', 'unknown')
                
                prompt += f"{i}. [{severity}] {service} (similarity: {score:.2f})\n"
                prompt += f"   Time: {timestamp}\n"
                prompt += f"   Message: {message}\n\n"
        else:
            prompt += "**Related Log Entries:** None found\n\n"
        
        # Add response format instructions
        prompt += """**Please provide your analysis in the following format:**

## Root Cause
[Identify the most likely cause based on the logs and query]

## Fix Suggestions
[Provide 2-3 specific, actionable steps to resolve the issue]

## Prevention
[Recommend 1-2 measures to prevent similar issues in the future]

Keep your response concise and technical. Focus on actionable insights."""
        
        logger.debug(f"Built prompt with {len(retrieved_logs)} log entries")
        
        return prompt
    
    def _call_groq(self, prompt: str) -> Dict[str, Any]:
        """
        Call Groq API with the constructed prompt.
        
        Args:
            prompt (str): LLM prompt
            
        Returns:
            dict: Groq API response with analysis
            
        Raises:
            Exception: If Groq API call fails after retries
        """
        if not self.groq_available:
            logger.warning("Groq not available, returning fallback response")
            return {
                "root_cause": "Unable to analyze - Groq API not available",
                "fix_suggestions": "Please check Groq API configuration and try again",
                "prevention": "Ensure proper API setup for future analysis"
            }
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Calling Groq API (attempt {attempt + 1}/{self.max_retries + 1})")
                
                start_time = time.time()
                
                response = self.groq_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.1,  # Low temperature for consistent, factual responses
                    timeout=self.timeout_seconds
                )
                
                elapsed_time = time.time() - start_time
                logger.info(f"Groq API call successful in {elapsed_time:.2f}s")
                
                # Extract response content
                content = response.choices[0].message.content
                
                # Parse structured response
                parsed_response = self._parse_groq_response(content)
                
                return parsed_response
                
            except Exception as e:
                logger.warning(f"Groq API call attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All Groq API attempts failed. Last error: {e}")
                    # Return graceful degradation response
                    return {
                        "root_cause": f"Analysis unavailable due to API error: {str(e)[:100]}",
                        "fix_suggestions": "Please try again later or check the logs manually for patterns",
                        "prevention": "Monitor API connectivity and consider implementing fallback analysis"
                    }
    
    def _parse_groq_response(self, content: str) -> Dict[str, str]:
        """
        Parse Groq response into structured format.
        
        Args:
            content (str): Raw response from Groq
            
        Returns:
            dict: Parsed response with root_cause, fix_suggestions, prevention
        """
        # Initialize default response
        parsed = {
            "root_cause": "",
            "fix_suggestions": "",
            "prevention": ""
        }
        
        try:
            # Split content by sections
            sections = content.split("##")
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Extract section title and content
                lines = section.split("\n", 1)
                if len(lines) < 2:
                    continue
                
                title = lines[0].strip().lower()
                content_text = lines[1].strip()
                
                # Map to response fields
                if "root cause" in title:
                    parsed["root_cause"] = content_text
                elif "fix" in title or "suggestion" in title:
                    parsed["fix_suggestions"] = content_text
                elif "prevention" in title or "prevent" in title:
                    parsed["prevention"] = content_text
            
            # Fallback: if parsing failed, use entire content as root cause
            if not any(parsed.values()):
                parsed["root_cause"] = content
                parsed["fix_suggestions"] = "Review the analysis above for potential solutions"
                parsed["prevention"] = "Implement monitoring and logging best practices"
            
            logger.debug("Successfully parsed Groq response")
            
        except Exception as e:
            logger.warning(f"Failed to parse Groq response: {e}")
            # Fallback response
            parsed = {
                "root_cause": content if content else "Unable to parse analysis",
                "fix_suggestions": "Please review the raw analysis for insights",
                "prevention": "Implement proper error handling and monitoring"
            }
        
        return parsed
    
    def analyze(self, query: str, top_k: int = 5, 
               similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Perform RAG analysis on a user query.
        
        Args:
            query (str): Natural language query about logs/errors
            top_k (int): Number of similar logs to retrieve. Default is 5.
            similarity_threshold (float): Minimum similarity score. Default is 0.3.
            
        Returns:
            dict: Analysis results with retrieved logs and LLM analysis
            
        Result format:
            {
                "query": "Why are users getting authentication errors?",
                "retrieved_logs": [
                    {
                        "id": "log_001",
                        "score": 0.95,
                        "metadata": {...}
                    }
                ],
                "analysis": {
                    "root_cause": "...",
                    "fix_suggestions": "...",
                    "prevention": "..."
                },
                "metadata": {
                    "retrieval_time": 0.15,
                    "analysis_time": 2.3,
                    "total_time": 2.45,
                    "logs_found": 3,
                    "groq_available": true
                }
            }
        """
        start_time = time.time()
        
        logger.info(f"Starting RAG analysis for query: '{query[:50]}...'")
        
        try:
            # Step 1: Generate query embedding
            logger.debug("Generating query embedding")
            query_embedding = self.embedder.embed(query)
            
            # Step 2: Retrieve similar logs from Endee
            logger.debug(f"Searching for top {top_k} similar logs")
            retrieval_start = time.time()
            
            search_result = self.endee_client.search(
                query_vector=query_embedding,
                top_k=min(top_k, self.max_context_logs),
                similarity_threshold=similarity_threshold
            )
            
            retrieval_time = time.time() - retrieval_start
            retrieved_logs = search_result.get("results", [])
            
            logger.info(f"Retrieved {len(retrieved_logs)} logs in {retrieval_time:.2f}s")
            
            # Step 3: Generate LLM analysis
            analysis_start = time.time()
            
            if retrieved_logs or not self.groq_available:
                # Build prompt and call Groq
                prompt = self._build_prompt(query, retrieved_logs)
                analysis = self._call_groq(prompt)
            else:
                # No logs found and Groq available
                analysis = {
                    "root_cause": "No similar log entries found in the database",
                    "fix_suggestions": "Try rephrasing your query or check if logs have been ingested",
                    "prevention": "Ensure comprehensive logging is enabled across all services"
                }
            
            analysis_time = time.time() - analysis_start
            total_time = time.time() - start_time
            
            logger.info(f"Analysis completed in {analysis_time:.2f}s (total: {total_time:.2f}s)")
            
            # Prepare result
            result = {
                "query": query,
                "retrieved_logs": retrieved_logs,
                "analysis": analysis,
                "metadata": {
                    "retrieval_time": round(retrieval_time, 3),
                    "analysis_time": round(analysis_time, 3),
                    "total_time": round(total_time, 3),
                    "logs_found": len(retrieved_logs),
                    "groq_available": self.groq_available,
                    "model_used": self.model if self.groq_available else "none",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"RAG analysis failed: {e}")
            
            # Return error response
            total_time = time.time() - start_time
            
            return {
                "query": query,
                "retrieved_logs": [],
                "analysis": {
                    "root_cause": f"Analysis failed due to error: {str(e)[:100]}",
                    "fix_suggestions": "Please try again or contact support if the issue persists",
                    "prevention": "Ensure all system components are properly configured and accessible"
                },
                "metadata": {
                    "retrieval_time": 0,
                    "analysis_time": 0,
                    "total_time": round(total_time, 3),
                    "logs_found": 0,
                    "groq_available": self.groq_available,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Get information about the RAG engine configuration.
        
        Returns:
            dict: Engine configuration and status
        """
        return {
            "groq_available": self.groq_available,
            "groq_model": self.model,
            "max_context_logs": self.max_context_logs,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "endee_connected": self.endee_client.base_url,
            "embedder_model": self.embedder.model_name,
            "embedder_dimension": self.embedder.get_dimension()
        }
    
    def test_groq_connection(self) -> Dict[str, Any]:
        """
        Test Groq API connectivity.
        
        Returns:
            dict: Connection test results
        """
        if not self.groq_available:
            return {
                "status": "unavailable",
                "error": "Groq client not initialized",
                "groq_library_available": GROQ_AVAILABLE,
                "api_key_configured": bool(self.groq_api_key)
            }
        
        try:
            # Simple test call
            start_time = time.time()
            
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, respond with 'OK'"}],
                max_tokens=10,
                timeout=10
            )
            
            elapsed_time = time.time() - start_time
            
            return {
                "status": "connected",
                "response_time": round(elapsed_time, 3),
                "model": self.model,
                "response_preview": response.choices[0].message.content[:50]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "model": self.model
            }
    
    def set_configuration(self, max_context_logs: Optional[int] = None,
                         timeout_seconds: Optional[int] = None,
                         max_retries: Optional[int] = None) -> None:
        """
        Update RAG engine configuration.
        
        Args:
            max_context_logs (int, optional): Maximum logs to include in context
            timeout_seconds (int, optional): Groq API timeout
            max_retries (int, optional): Maximum retry attempts
        """
        if max_context_logs is not None:
            self.max_context_logs = max(1, min(max_context_logs, 10))
            logger.info(f"Updated max_context_logs to {self.max_context_logs}")
        
        if timeout_seconds is not None:
            self.timeout_seconds = max(5, min(timeout_seconds, 120))
            logger.info(f"Updated timeout_seconds to {self.timeout_seconds}")
        
        if max_retries is not None:
            self.max_retries = max(0, min(max_retries, 5))
            logger.info(f"Updated max_retries to {self.max_retries}")