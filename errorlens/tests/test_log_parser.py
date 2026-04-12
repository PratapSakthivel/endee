"""
Tests for ErrorLens Log Parser

This module contains comprehensive tests for the LogParser class,
including unit tests and property-based tests.
"""

import pytest
import json
from backend.log_parser import LogParser
from backend.models import LogEntry


class TestLogParser:
    """Test suite for LogParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LogParser()
    
    def test_parse_bracketed_format(self):
        """Test parsing bracketed log format."""
        line = "[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials for user"
        entry = self.parser.parse_line(line, 1)
        
        assert entry.severity == "ERROR"
        assert entry.service == "auth_service"
        assert entry.message == "Invalid credentials for user"
        assert entry.timestamp == "2024-01-15T10:30:45Z"
        assert entry.raw_log == line
        assert entry.line_number == 1
    
    def test_parse_standard_format(self):
        """Test parsing standard log format."""
        line = "2024-01-15 10:30:45 ERROR auth_service: Invalid credentials for user"
        entry = self.parser.parse_line(line, 2)
        
        assert entry.severity == "ERROR"
        assert entry.service == "auth_service"
        assert entry.message == "Invalid credentials for user"
        assert entry.timestamp == "2024-01-15 10:30:45"
        assert entry.raw_log == line
        assert entry.line_number == 2
    
    def test_parse_syslog_format(self):
        """Test parsing syslog format."""
        line = "Jan 15 10:30:45 ERROR auth_service Invalid credentials for user"
        entry = self.parser.parse_line(line, 3)
        
        assert entry.severity == "ERROR"
        assert entry.service == "auth_service"
        assert entry.message == "Invalid credentials for user"
        assert entry.timestamp == "Jan 15 10:30:45"
        assert entry.raw_log == line
        assert entry.line_number == 3
    
    def test_parse_error_first_format(self):
        """Test parsing error-first format."""
        line = "ERROR: [auth_service] Invalid credentials for user (2024-01-15T10:30:45Z)"
        entry = self.parser.parse_line(line, 4)
        
        assert entry.severity == "ERROR"
        assert entry.service == "auth_service"
        assert entry.message == "Invalid credentials for user"
        assert entry.timestamp == "2024-01-15T10:30:45Z"
        assert entry.raw_log == line
        assert entry.line_number == 4
    
    def test_parse_simple_format(self):
        """Test parsing simple format."""
        line = "ERROR Invalid credentials for user"
        entry = self.parser.parse_line(line, 5)
        
        assert entry.severity == "ERROR"
        assert entry.service == "unknown"  # No service in simple format
        assert entry.message == "Invalid credentials for user"
        assert entry.timestamp == "unknown"  # No timestamp in simple format
        assert entry.raw_log == line
        assert entry.line_number == 5
    
    def test_parse_json_format_complete(self):
        """Test parsing complete JSON log format."""
        log_data = {
            "timestamp": "2024-01-15T10:30:45Z",
            "level": "ERROR",
            "service": "auth_service",
            "message": "Invalid credentials for user"
        }
        line = json.dumps(log_data)
        entry = self.parser.parse_line(line, 6)
        
        assert entry.severity == "ERROR"
        assert entry.service == "auth_service"
        assert entry.message == "Invalid credentials for user"
        assert entry.timestamp == "2024-01-15T10:30:45Z"
        assert entry.raw_log == line
        assert entry.line_number == 6
    
    def test_parse_json_format_alternative_fields(self):
        """Test parsing JSON with alternative field names."""
        log_data = {
            "time": "2024-01-15T10:30:45Z",
            "severity": "WARN",
            "logger": "payment_service",
            "msg": "Payment timeout occurred"
        }
        line = json.dumps(log_data)
        entry = self.parser.parse_line(line, 7)
        
        assert entry.severity == "WARN"
        assert entry.service == "payment_service"
        assert entry.message == "Payment timeout occurred"
        assert entry.timestamp == "2024-01-15T10:30:45Z"
        assert entry.raw_log == line
        assert entry.line_number == 7
    
    def test_parse_json_format_minimal(self):
        """Test parsing minimal JSON format."""
        log_data = {"msg": "Something happened"}
        line = json.dumps(log_data)
        entry = self.parser.parse_line(line, 8)
        
        assert entry.severity == "UNKNOWN"  # No severity provided
        assert entry.service == "unknown"   # No service provided
        assert entry.message == "Something happened"
        assert entry.timestamp == "unknown" # No timestamp provided
        assert entry.raw_log == line
        assert entry.line_number == 8
    
    def test_parse_malformed_line(self):
        """Test parsing malformed log line."""
        line = "This is just some random text that doesn't match any pattern"
        entry = self.parser.parse_line(line, 9)
        
        assert entry.severity == "UNKNOWN"
        assert entry.service == "unknown"
        assert entry.message == line  # Entire line becomes message
        assert entry.timestamp == "unknown"
        assert entry.raw_log == line
        assert entry.line_number == 9
    
    def test_severity_normalization(self):
        """Test severity level normalization."""
        test_cases = [
            ("FATAL", "ERROR"),
            ("CRITICAL", "ERROR"),
            ("CRIT", "ERROR"),
            ("ERR", "ERROR"),
            ("WARNING", "WARN"),
            ("NOTICE", "INFO"),
            ("INFORMATION", "INFO"),
            ("TRACE", "DEBUG"),
            ("UNKNOWN_LEVEL", "UNKNOWN"),
        ]
        
        for input_severity, expected in test_cases:
            normalized = self.parser._normalize_severity(input_severity)
            assert normalized == expected, f"Expected {expected}, got {normalized} for {input_severity}"
    
    def test_parse_file_multiple_lines(self):
        """Test parsing file with multiple log lines."""
        content = """[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials
2024-01-15 10:31:00 WARN payment_service: Payment timeout
{"timestamp": "2024-01-15T10:31:15Z", "level": "INFO", "service": "api_gateway", "message": "Request processed"}
This is a malformed line"""
        
        entries = self.parser.parse_file(content, "test.log")
        
        assert len(entries) == 4
        
        # First entry (bracketed format)
        assert entries[0].severity == "ERROR"
        assert entries[0].service == "auth_service"
        assert entries[0].message == "Invalid credentials"
        assert entries[0].line_number == 1
        
        # Second entry (standard format)
        assert entries[1].severity == "WARN"
        assert entries[1].service == "payment_service"
        assert entries[1].message == "Payment timeout"
        assert entries[1].line_number == 2
        
        # Third entry (JSON format)
        assert entries[2].severity == "INFO"
        assert entries[2].service == "api_gateway"
        assert entries[2].message == "Request processed"
        assert entries[2].line_number == 3
        
        # Fourth entry (malformed)
        assert entries[3].severity == "UNKNOWN"
        assert entries[3].service == "unknown"
        assert entries[3].message == "This is a malformed line"
        assert entries[3].line_number == 4
    
    def test_parse_file_empty_lines(self):
        """Test parsing file with empty lines."""
        content = """[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials

2024-01-15 10:31:00 WARN payment_service: Payment timeout

"""
        
        entries = self.parser.parse_file(content, "test.log")
        
        # Should skip empty lines
        assert len(entries) == 2
        assert entries[0].line_number == 1
        assert entries[1].line_number == 3  # Line 2 was empty, so this is line 3
    
    def test_logentry_to_embedding_text(self):
        """Test LogEntry to_embedding_text method."""
        entry = LogEntry(
            severity="ERROR",
            service="auth_service",
            message="Invalid credentials",
            timestamp="2024-01-15T10:30:45Z",
            raw_log="[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
            line_number=1
        )
        
        embedding_text = entry.to_embedding_text()
        assert embedding_text == "ERROR auth_service: Invalid credentials"
    
    def test_logentry_to_metadata(self):
        """Test LogEntry to_metadata method."""
        entry = LogEntry(
            severity="ERROR",
            service="auth_service",
            message="Invalid credentials",
            timestamp="2024-01-15T10:30:45Z",
            raw_log="[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
            line_number=1
        )
        
        metadata = entry.to_metadata()
        expected = {
            "severity": "ERROR",
            "service": "auth_service",
            "timestamp": "2024-01-15T10:30:45Z",
            "raw_log": "[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
            "line_number": 1
        }
        assert metadata == expected
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.parser.get_supported_formats()
        assert len(formats) == 6
        assert any("JSON format" in fmt for fmt in formats)
        assert any("Bracketed format" in fmt for fmt in formats)
        assert any("Standard format" in fmt for fmt in formats)
    
    def test_case_insensitive_severity(self):
        """Test case insensitive severity parsing."""
        line = "[2024-01-15T10:30:45Z] error [auth_service] Invalid credentials"
        entry = self.parser.parse_line(line, 1)
        assert entry.severity == "ERROR"  # Should be normalized to uppercase
    
    def test_whitespace_handling(self):
        """Test handling of extra whitespace."""
        line = "  [2024-01-15T10:30:45Z]   ERROR   [auth_service]   Invalid credentials  "
        entry = self.parser.parse_line(line.strip(), 1)
        assert entry.severity == "ERROR"
        assert entry.service == "auth_service"
        assert entry.message == "Invalid credentials"


# Property-based tests (simplified versions for now)
class TestLogParserProperties:
    """Property-based tests for LogParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = LogParser()
    
    def test_property_information_preservation(self):
        """
        Property 1: Log Parsing Information Preservation
        
        For any log line (valid or malformed), when parsed by the Log_Parser,
        the resulting LogEntry SHALL contain all extractable fields AND
        preserve the complete original raw log text in the raw_log field.
        """
        test_lines = [
            "[2024-01-15T10:30:45Z] ERROR [auth_service] Invalid credentials",
            "2024-01-15 10:30:45 WARN payment_service: Timeout occurred",
            '{"level": "INFO", "message": "Request processed"}',
            "This is completely malformed text",
            "",
            "ERROR Simple message",
        ]
        
        for i, line in enumerate(test_lines, 1):
            if line.strip():  # Skip empty lines
                entry = self.parser.parse_line(line, i)
                
                # Must preserve original raw log
                assert entry.raw_log == line
                
                # Must have all required fields
                assert hasattr(entry, 'severity')
                assert hasattr(entry, 'service')
                assert hasattr(entry, 'message')
                assert hasattr(entry, 'timestamp')
                assert hasattr(entry, 'line_number')
                
                # Fields must not be None
                assert entry.severity is not None
                assert entry.service is not None
                assert entry.message is not None
                assert entry.timestamp is not None
                assert entry.line_number == i
    
    def test_property_json_parsing_correctness(self):
        """
        Property 2: JSON Log Parsing Correctness
        
        For any valid JSON log object containing log fields, when parsed by
        the Log_Parser, the resulting LogEntry SHALL correctly extract all
        fields from the JSON structure.
        """
        json_logs = [
            {
                "timestamp": "2024-01-15T10:30:45Z",
                "level": "ERROR",
                "service": "auth_service",
                "message": "Invalid credentials"
            },
            {
                "time": "2024-01-15T10:31:00Z",
                "severity": "WARN",
                "logger": "payment_service",
                "msg": "Payment timeout"
            },
            {
                "datetime": "2024-01-15T10:31:15Z",
                "loglevel": "INFO",
                "component": "api_gateway",
                "text": "Request processed"
            }
        ]
        
        for i, log_data in enumerate(json_logs, 1):
            line = json.dumps(log_data)
            entry = self.parser.parse_line(line, i)
            
            # Should correctly extract timestamp
            if "timestamp" in log_data:
                assert entry.timestamp == log_data["timestamp"]
            elif "time" in log_data:
                assert entry.timestamp == log_data["time"]
            elif "datetime" in log_data:
                assert entry.timestamp == log_data["datetime"]
            
            # Should correctly extract severity
            if "level" in log_data:
                assert entry.severity == log_data["level"].upper()
            elif "severity" in log_data:
                assert entry.severity == log_data["severity"].upper()
            elif "loglevel" in log_data:
                assert entry.severity == log_data["loglevel"].upper()
            
            # Should correctly extract service
            if "service" in log_data:
                assert entry.service == log_data["service"]
            elif "logger" in log_data:
                assert entry.service == log_data["logger"]
            elif "component" in log_data:
                assert entry.service == log_data["component"]
            
            # Should correctly extract message
            if "message" in log_data:
                assert entry.message == log_data["message"]
            elif "msg" in log_data:
                assert entry.message == log_data["msg"]
            elif "text" in log_data:
                assert entry.message == log_data["text"]
    
    def test_property_malformed_log_graceful_handling(self):
        """
        Property 3: Malformed Log Graceful Handling
        
        For any unparseable or malformed log line, when processed by the
        Log_Parser, the resulting LogEntry SHALL have severity set to "UNKNOWN"
        AND preserve the complete original text in raw_log.
        """
        malformed_lines = [
            "This is just random text",
            "123456789",
            "ERROR: Missing brackets and format",
            "{ invalid json",
            "SEVERITY_WITHOUT_MESSAGE",
            "   ",  # Just whitespace
            "Special chars: !@#$%^&*()",
        ]
        
        for i, line in enumerate(malformed_lines, 1):
            if line.strip():  # Skip whitespace-only lines
                entry = self.parser.parse_line(line, i)
                
                # Must have UNKNOWN severity for unparseable lines
                # (unless it happens to match simple format)
                if not any(pattern['regex'].match(line) for pattern in self.parser.patterns):
                    assert entry.severity == "UNKNOWN"
                
                # Must preserve original text
                assert entry.raw_log == line
                
                # Must have line number
                assert entry.line_number == i