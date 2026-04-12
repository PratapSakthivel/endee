"""
ErrorLens Log Parser

This module provides log parsing functionality for multiple log formats including
standard syslog, application logs, and JSON-formatted logs.
"""

import re
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .models import LogEntry

logger = logging.getLogger(__name__)


class LogParser:
    """
    Log parser that handles multiple log formats.
    
    Supports:
    - Standard syslog format: [TIMESTAMP] SEVERITY [SERVICE] MESSAGE
    - Application format: TIMESTAMP SEVERITY SERVICE: MESSAGE  
    - JSON format: {"timestamp": ..., "level": ..., "service": ..., "message": ...}
    - Custom formats with regex patterns
    """
    
    def __init__(self):
        """Initialize the log parser with regex patterns."""
        # Standard log format patterns
        self.patterns = [
            # Pattern 1: [2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials
            {
                'name': 'bracketed_format',
                'regex': re.compile(
                    r'^\[(?P<timestamp>[^\]]+)\]\s+(?P<severity>\w+)\s+\[(?P<service>[^\]]+)\]\s+(?P<message>.+)$'
                ),
            },
            # Pattern 2: 2024-01-15 10:30:45 ERROR auth_service: Invalid credentials
            {
                'name': 'standard_format',
                'regex': re.compile(
                    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(?P<severity>\w+)\s+(?P<service>\w+):\s+(?P<message>.+)$'
                ),
            },
            # Pattern 3: Jan 15 10:30:45 ERROR auth_service Invalid credentials
            {
                'name': 'syslog_format',
                'regex': re.compile(
                    r'^(?P<timestamp>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(?P<severity>\w+)\s+(?P<service>\w+)\s+(?P<message>.+)$'
                ),
            },
            # Pattern 4: ERROR: [auth_service] Invalid credentials (2024-01-15T10:30:45Z)
            {
                'name': 'error_first_format',
                'regex': re.compile(
                    r'^(?P<severity>\w+):\s+\[(?P<service>[^\]]+)\]\s+(?P<message>.+?)\s+\((?P<timestamp>[^)]+)\)$'
                ),
            },
            # Pattern 5: Simple format: ERROR Invalid credentials (only if severity is valid)
            {
                'name': 'simple_format',
                'regex': re.compile(
                    r'^(?P<severity>ERROR|WARN|INFO|DEBUG|FATAL|CRITICAL|CRIT|ERR|WARNING|NOTICE|INFORMATION|TRACE)\s+(?P<message>.+)$'
                ),
            },
        ]
        
        # Common severity level mappings
        self.severity_mappings = {
            'FATAL': 'ERROR',
            'CRIT': 'ERROR', 
            'CRITICAL': 'ERROR',
            'ERR': 'ERROR',
            'WARNING': 'WARN',
            'WARN': 'WARN',
            'NOTICE': 'INFO',
            'INFORMATION': 'INFO',
            'DEBUG': 'DEBUG',
            'TRACE': 'DEBUG',
        }
    
    def parse_file(self, content: str, filename: str) -> List[LogEntry]:
        """
        Parse log file content into structured entries.
        
        Args:
            content (str): Raw log file content
            filename (str): Name of the log file
            
        Returns:
            List[LogEntry]: List of parsed log entries
        """
        logger.info(f"Parsing log file: {filename}")
        
        lines = content.strip().split('\n')
        entries = []
        
        for line_num, line in enumerate(lines, 1):
            if line.strip():  # Skip empty lines
                entry = self.parse_line(line.strip(), line_num)
                entries.append(entry)
        
        logger.info(f"Parsed {len(entries)} log entries from {filename}")
        return entries
    
    def parse_line(self, line: str, line_num: int) -> LogEntry:
        """
        Parse a single log line.
        
        Args:
            line (str): Raw log line
            line_num (int): Line number in the file
            
        Returns:
            LogEntry: Parsed log entry
        """
        # First try JSON parsing
        json_result = self._parse_json_format(line)
        if json_result:
            return LogEntry(
                severity=self._normalize_severity(json_result.get('severity', 'UNKNOWN')),
                service=json_result.get('service', 'unknown'),
                message=json_result.get('message', line),
                timestamp=json_result.get('timestamp', 'unknown'),
                raw_log=line,
                line_number=line_num
            )
        
        # Try standard format patterns
        standard_result = self._parse_standard_format(line)
        if standard_result:
            return LogEntry(
                severity=self._normalize_severity(standard_result.get('severity', 'UNKNOWN')),
                service=standard_result.get('service', 'unknown'),
                message=standard_result.get('message', line),
                timestamp=standard_result.get('timestamp', 'unknown'),
                raw_log=line,
                line_number=line_num
            )
        
        # If no pattern matches, create entry with UNKNOWN severity
        logger.debug(f"No pattern matched for line {line_num}: {line[:50]}...")
        return LogEntry(
            severity='UNKNOWN',
            service='unknown',
            message=line,
            timestamp='unknown',
            raw_log=line,
            line_number=line_num
        )
    
    def _parse_standard_format(self, line: str) -> Optional[Dict[str, str]]:
        """
        Parse standard log formats using regex patterns.
        
        Args:
            line (str): Log line to parse
            
        Returns:
            Optional[Dict[str, str]]: Parsed fields or None if no match
        """
        for pattern_info in self.patterns:
            match = pattern_info['regex'].match(line)
            if match:
                result = match.groupdict()
                logger.debug(f"Matched pattern '{pattern_info['name']}' for line: {line[:50]}...")
                return result
        
        return None
    
    def _parse_json_format(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON log format.
        
        Args:
            line (str): Log line to parse
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON fields or None if not JSON
        """
        try:
            data = json.loads(line)
            if isinstance(data, dict):
                # Map common JSON field names to our standard fields
                result = {}
                
                # Extract severity/level
                for field in ['level', 'severity', 'loglevel', 'priority']:
                    if field in data:
                        result['severity'] = str(data[field]).upper()
                        break
                
                # Extract service/logger/component
                for field in ['service', 'logger', 'component', 'app', 'application']:
                    if field in data:
                        result['service'] = str(data[field])
                        break
                
                # Extract message/msg
                for field in ['message', 'msg', 'text', 'description']:
                    if field in data:
                        result['message'] = str(data[field])
                        break
                
                # Extract timestamp/time
                for field in ['timestamp', 'time', 'datetime', '@timestamp']:
                    if field in data:
                        result['timestamp'] = str(data[field])
                        break
                
                logger.debug(f"Parsed JSON log: {result}")
                return result
                
        except (json.JSONDecodeError, TypeError):
            # Not a JSON line, return None
            pass
        
        return None
    
    def _normalize_severity(self, severity: str) -> str:
        """
        Normalize severity level to standard values.
        
        Args:
            severity (str): Raw severity level
            
        Returns:
            str: Normalized severity (ERROR, WARN, INFO, DEBUG, UNKNOWN)
        """
        severity_upper = severity.upper().strip()
        
        # Direct mapping
        if severity_upper in ['ERROR', 'WARN', 'INFO', 'DEBUG']:
            return severity_upper
        
        # Use mapping table
        return self.severity_mappings.get(severity_upper, 'UNKNOWN')
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported log formats.
        
        Returns:
            List[str]: List of supported format descriptions
        """
        return [
            "JSON format: {\"timestamp\": \"...\", \"level\": \"...\", \"service\": \"...\", \"message\": \"...\"}",
            "Bracketed format: [TIMESTAMP] SEVERITY [SERVICE] MESSAGE",
            "Standard format: TIMESTAMP SEVERITY SERVICE: MESSAGE",
            "Syslog format: MMM DD HH:MM:SS SEVERITY SERVICE MESSAGE",
            "Error-first format: SEVERITY: [SERVICE] MESSAGE (TIMESTAMP)",
            "Simple format: SEVERITY MESSAGE"
        ]