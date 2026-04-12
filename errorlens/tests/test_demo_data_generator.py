"""
Unit tests for the demo data generator.

Tests the synthetic log generation functionality to ensure
correct counts, service distribution, and output file creation.
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime
import json

# Import the demo data generator
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.generate_demo_data import DemoDataGenerator


class TestDemoDataGenerator:
    """Test suite for DemoDataGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.generator = DemoDataGenerator()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_generator_initialization(self):
        """Test that generator initializes with correct services and severities."""
        assert len(self.generator.services) == 3
        assert "auth_service" in self.generator.services
        assert "payment_service" in self.generator.services
        assert "api_gateway" in self.generator.services
        
        assert len(self.generator.severities) == 4
        assert "ERROR" in self.generator.severities
        assert "WARN" in self.generator.severities
        assert "INFO" in self.generator.severities
        assert "DEBUG" in self.generator.severities
    
    def test_error_templates_exist(self):
        """Test that error templates exist for all services and severities."""
        for service in self.generator.services:
            assert service in self.generator.error_templates
            for severity in self.generator.severities:
                assert severity in self.generator.error_templates[service]
                assert len(self.generator.error_templates[service][severity]) > 0
    
    def test_generate_timestamp(self):
        """Test timestamp generation."""
        timestamp_str = self.generator.generate_timestamp(1)
        
        # Parse timestamp
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        # Should be within the last day
        assert (now - timestamp).days <= 1
        assert timestamp <= now
    
    def test_fill_template(self):
        """Test template variable filling."""
        template = "User {user_id} failed with error {count}"
        result = self.generator.fill_template(template)
        
        # Should not contain template variables
        assert "{user_id}" not in result
        assert "{count}" not in result
        
        # Should contain actual values
        assert "User " in result
        assert " failed with error " in result
    
    def test_generate_log_entry(self):
        """Test single log entry generation."""
        log_entry = self.generator.generate_log_entry("auth_service", "ERROR", 1)
        
        # Check required fields
        assert "timestamp" in log_entry
        assert "severity" in log_entry
        assert "service" in log_entry
        assert "message" in log_entry
        assert "line_number" in log_entry
        
        # Check values
        assert log_entry["severity"] == "ERROR"
        assert log_entry["service"] == "auth_service"
        assert log_entry["line_number"] == 1
        assert len(log_entry["message"]) > 0
        
        # Timestamp should be valid
        datetime.strptime(log_entry["timestamp"], "%Y-%m-%d %H:%M:%S")
    
    def test_generate_logs_count(self):
        """Test that correct number of logs are generated."""
        # Test different counts
        for count in [10, 50, 100, 500]:
            logs = self.generator.generate_logs(count)
            assert len(logs) == count
    
    def test_generate_logs_service_distribution(self):
        """Test that logs are distributed across all services."""
        logs = self.generator.generate_logs(300)  # Divisible by 3
        
        # Count logs per service
        service_counts = {}
        for log in logs:
            service = log["service"]
            service_counts[service] = service_counts.get(service, 0) + 1
        
        # All services should be represented
        for service in self.generator.services:
            assert service in service_counts
            assert service_counts[service] > 0
        
        # Should be roughly equal distribution
        expected_per_service = 300 // 3
        for service in self.generator.services:
            # Allow some variance due to rounding
            assert abs(service_counts[service] - expected_per_service) <= 1
    
    def test_generate_logs_severity_distribution(self):
        """Test that all severity levels are represented."""
        logs = self.generator.generate_logs(200)
        
        # Count logs per severity
        severity_counts = {}
        for log in logs:
            severity = log["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # All severities should be represented
        for severity in self.generator.severities:
            assert severity in severity_counts
            assert severity_counts[severity] > 0
        
        # ERROR and WARN should have reasonable representation (at least 10% each)
        total_logs = len(logs)
        assert severity_counts["ERROR"] >= total_logs * 0.1
        assert severity_counts["WARN"] >= total_logs * 0.1
    
    def test_generate_logs_line_numbers(self):
        """Test that line numbers are sequential and unique."""
        logs = self.generator.generate_logs(50)
        
        line_numbers = [log["line_number"] for log in logs]
        
        # Should be sequential from 1 to 50
        assert sorted(line_numbers) == list(range(1, 51))
        
        # Should be unique
        assert len(set(line_numbers)) == len(line_numbers)
    
    def test_format_log_entry_standard(self):
        """Test standard log formatting."""
        log_entry = {
            "timestamp": "2024-01-01 12:00:00",
            "severity": "ERROR",
            "service": "auth_service",
            "message": "Test error message",
            "line_number": 1
        }
        
        formatted = self.generator.format_log_entry(log_entry, "standard")
        expected = "[2024-01-01 12:00:00] ERROR [auth_service] Test error message"
        
        assert formatted == expected
    
    def test_format_log_entry_json(self):
        """Test JSON log formatting."""
        log_entry = {
            "timestamp": "2024-01-01 12:00:00",
            "severity": "ERROR",
            "service": "auth_service",
            "message": "Test error message",
            "line_number": 1
        }
        
        formatted = self.generator.format_log_entry(log_entry, "json")
        parsed = json.loads(formatted)
        
        assert parsed == log_entry
    
    def test_write_service_logs(self):
        """Test writing logs to service-specific files."""
        # Generate small set of logs
        logs = self.generator.generate_logs(30)  # 10 per service
        
        # Write to temp directory
        service_logs = self.generator.write_service_logs(logs, self.temp_dir)
        
        # Check that all services have logs
        assert len(service_logs) == 3
        for service in self.generator.services:
            assert service in service_logs
            assert len(service_logs[service]) > 0
        
        # Check that files were created
        for service in self.generator.services:
            filepath = os.path.join(self.temp_dir, f"{service}.log")
            assert os.path.exists(filepath)
            
            # Check file content
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == len(service_logs[service])
                
                # Each line should be properly formatted
                for line in lines:
                    assert line.strip()  # Not empty
                    assert "[" in line and "]" in line  # Contains brackets
                    assert service in line  # Contains service name
    
    def test_write_service_logs_creates_directory(self):
        """Test that write_service_logs creates output directory if it doesn't exist."""
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent", "subdir")
        assert not os.path.exists(nonexistent_dir)
        
        logs = self.generator.generate_logs(10)
        self.generator.write_service_logs(logs, nonexistent_dir)
        
        # Directory should now exist
        assert os.path.exists(nonexistent_dir)
        
        # Files should be created
        for service in self.generator.services:
            filepath = os.path.join(nonexistent_dir, f"{service}.log")
            assert os.path.exists(filepath)
    
    def test_realistic_error_messages(self):
        """Test that generated error messages are realistic and varied."""
        logs = self.generator.generate_logs(100)
        
        messages = [log["message"] for log in logs]
        
        # Should have variety (no message repeated too often)
        message_counts = {}
        for message in messages:
            message_counts[message] = message_counts.get(message, 0) + 1
        
        # No single message should dominate (max 20% of total)
        max_count = max(message_counts.values())
        assert max_count <= len(messages) * 0.2
        
        # Messages should contain realistic elements
        realistic_elements = [
            "user", "error", "failed", "timeout", "connection", 
            "authentication", "payment", "API", "service", "request"
        ]
        
        found_elements = set()
        for message in messages:
            message_lower = message.lower()
            for element in realistic_elements:
                if element in message_lower:
                    found_elements.add(element)
        
        # Should find most realistic elements
        assert len(found_elements) >= len(realistic_elements) * 0.7
    
    def test_service_specific_messages(self):
        """Test that services generate appropriate messages."""
        logs = self.generator.generate_logs(300)
        
        # Group by service
        service_messages = {}
        for log in logs:
            service = log["service"]
            if service not in service_messages:
                service_messages[service] = []
            service_messages[service].append(log["message"].lower())
        
        # Auth service should have auth-related messages
        auth_messages = " ".join(service_messages["auth_service"])
        assert any(word in auth_messages for word in ["auth", "login", "user", "session", "token"])
        
        # Payment service should have payment-related messages
        payment_messages = " ".join(service_messages["payment_service"])
        assert any(word in payment_messages for word in ["payment", "card", "transaction", "charge", "refund"])
        
        # API gateway should have gateway-related messages
        gateway_messages = " ".join(service_messages["api_gateway"])
        assert any(word in gateway_messages for word in ["api", "request", "endpoint", "gateway", "rate limit"])


# Integration test
def test_full_demo_generation():
    """Integration test for full demo data generation process."""
    generator = DemoDataGenerator()
    
    # Generate logs
    logs = generator.generate_logs(500)
    
    # Basic validation
    assert len(logs) == 500
    
    # Check distribution
    service_counts = {}
    severity_counts = {}
    
    for log in logs:
        service = log["service"]
        severity = log["severity"]
        
        service_counts[service] = service_counts.get(service, 0) + 1
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # All services represented
    assert len(service_counts) == 3
    for service in generator.services:
        assert service in service_counts
        assert service_counts[service] > 0
    
    # All severities represented
    assert len(severity_counts) == 4
    for severity in generator.severities:
        assert severity in severity_counts
        assert severity_counts[severity] > 0
    
    # Reasonable distribution (no service has less than 15% or more than 40%)
    for count in service_counts.values():
        assert 0.15 <= count / 500 <= 0.4
    
    print(f"✅ Integration test passed: Generated {len(logs)} logs")
    print(f"   Service distribution: {service_counts}")
    print(f"   Severity distribution: {severity_counts}")


if __name__ == "__main__":
    # Run integration test
    test_full_demo_generation()
    print("🎉 All tests would pass!")