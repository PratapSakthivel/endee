#!/usr/bin/env python3
"""
ErrorLens Demo Data Generator

Generates realistic synthetic log entries for demonstration purposes.
Creates 500 log entries across 3 services: auth_service, payment_service, api_gateway
with various severity levels and realistic error messages.

Usage:
    python scripts/generate_demo_data.py
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os


class DemoDataGenerator:
    """Generates realistic synthetic log data for ErrorLens demonstration."""
    
    def __init__(self):
        self.services = ["auth_service", "payment_service", "api_gateway"]
        self.severities = ["ERROR", "WARN", "INFO", "DEBUG"]
        
        # Realistic error messages by service
        self.error_templates = {
            "auth_service": {
                "ERROR": [
                    "Authentication failed for user {user_id}: Invalid credentials",
                    "JWT token validation failed: Token expired at {timestamp}",
                    "Failed to connect to LDAP server: Connection timeout after 30s",
                    "Password reset failed for {email}: User not found",
                    "OAuth2 callback error: Invalid state parameter",
                    "Session validation failed: Session {session_id} not found",
                    "Two-factor authentication failed: Invalid TOTP code",
                    "Account locked after 5 failed login attempts for user {user_id}",
                    "API key validation failed: Key {api_key} revoked",
                    "Database connection failed: Unable to reach auth_db on port 5432"
                ],
                "WARN": [
                    "Suspicious login attempt from IP {ip_address} for user {user_id}",
                    "Password strength below policy requirements for user {user_id}",
                    "Rate limit approaching for IP {ip_address}: 45/50 requests",
                    "Session {session_id} expires in 5 minutes",
                    "Failed login attempt #{attempt} for user {user_id}",
                    "Deprecated API endpoint /v1/auth accessed by client {client_id}",
                    "User {user_id} attempting access to restricted resource",
                    "Certificate expires in 7 days: auth.example.com"
                ],
                "INFO": [
                    "User {user_id} successfully authenticated from {ip_address}",
                    "New user registration: {email}",
                    "Password successfully updated for user {user_id}",
                    "Session {session_id} created for user {user_id}",
                    "User {user_id} logged out successfully",
                    "API key generated for application {app_name}",
                    "Two-factor authentication enabled for user {user_id}",
                    "OAuth2 authorization granted for client {client_id}"
                ],
                "DEBUG": [
                    "Validating JWT token signature for user {user_id}",
                    "Loading user permissions for {user_id} from cache",
                    "Checking rate limits for IP {ip_address}",
                    "Session cleanup: Removed {count} expired sessions",
                    "LDAP query executed: cn={user_id},ou=users,dc=example,dc=com",
                    "Cache hit for user profile {user_id}",
                    "Generating CSRF token for session {session_id}"
                ]
            },
            "payment_service": {
                "ERROR": [
                    "Payment processing failed: Card {card_number} declined by issuer",
                    "Stripe API error: insufficient_funds for charge {charge_id}",
                    "Database transaction rollback: Payment {payment_id} failed",
                    "Webhook delivery failed: {webhook_url} returned HTTP 500",
                    "Refund processing error: Original transaction {txn_id} not found",
                    "Currency conversion failed: USD to {currency} rate unavailable",
                    "Payment gateway timeout: No response from processor after 30s",
                    "Fraud detection triggered: Suspicious transaction {txn_id}",
                    "Insufficient account balance: Required ${amount}, available ${balance}",
                    "Credit card validation failed: Invalid CVV for card {card_number}"
                ],
                "WARN": [
                    "High transaction volume detected: {count} payments in last hour",
                    "Payment retry attempt #{attempt} for transaction {txn_id}",
                    "Unusual spending pattern for customer {customer_id}",
                    "Payment processor latency high: Average {latency}ms",
                    "Webhook retry #{retry} for event {event_id}",
                    "Daily transaction limit approaching for merchant {merchant_id}",
                    "Currency exchange rate fluctuation: {old_rate} -> {new_rate}",
                    "Payment method {method} will expire in 30 days"
                ],
                "INFO": [
                    "Payment ${amount} processed successfully for order {order_id}",
                    "Refund ${amount} issued for transaction {txn_id}",
                    "New payment method added for customer {customer_id}",
                    "Subscription {subscription_id} renewed successfully",
                    "Webhook delivered successfully to {webhook_url}",
                    "Daily settlement completed: ${total_amount} in {count} transactions",
                    "Payment method updated for customer {customer_id}",
                    "Chargeback resolved in favor of merchant for transaction {txn_id}"
                ],
                "DEBUG": [
                    "Validating payment request for amount ${amount}",
                    "Loading merchant configuration for {merchant_id}",
                    "Calculating fees for transaction {txn_id}: ${fee_amount}",
                    "Checking fraud rules for transaction pattern",
                    "Updating payment status: {old_status} -> {new_status}",
                    "Cache miss for customer {customer_id} payment methods",
                    "Encrypting sensitive payment data for storage"
                ]
            },
            "api_gateway": {
                "ERROR": [
                    "Upstream service unavailable: {service_name} returned HTTP 503",
                    "Request timeout: {endpoint} exceeded 30s limit",
                    "Rate limit exceeded: Client {client_id} hit 1000 req/min limit",
                    "Authentication failed: Invalid API key {api_key}",
                    "Circuit breaker opened for service {service_name}",
                    "Load balancer error: No healthy backends for {service_name}",
                    "SSL handshake failed: Certificate verification error",
                    "Request validation failed: Missing required parameter {param}",
                    "Upstream connection refused: {service_name}:{port}",
                    "Internal server error: Unhandled exception in request processing"
                ],
                "WARN": [
                    "High latency detected: {endpoint} responding in {latency}ms",
                    "Retry attempt #{attempt} for failed request to {service_name}",
                    "Client {client_id} approaching rate limit: {current}/{limit}",
                    "Deprecated API version v{version} accessed by client {client_id}",
                    "Unusual traffic pattern: {spike}% increase in requests",
                    "Backend service {service_name} health check failed",
                    "Request queue length high: {queue_size} pending requests",
                    "SSL certificate expires in 14 days: {domain}"
                ],
                "INFO": [
                    "Request processed successfully: {method} {endpoint} -> HTTP {status}",
                    "New API client registered: {client_id}",
                    "Rate limit reset for client {client_id}",
                    "Backend service {service_name} health restored",
                    "API key {api_key} renewed for client {client_id}",
                    "Load balancer added new backend: {service_name}:{port}",
                    "Request routed to {service_name} instance {instance_id}",
                    "Circuit breaker closed for service {service_name}"
                ],
                "DEBUG": [
                    "Routing request {request_id} to service {service_name}",
                    "Applying rate limit policy for client {client_id}",
                    "Request headers validated for {endpoint}",
                    "Load balancing algorithm selected backend {backend_id}",
                    "Caching response for {endpoint} with TTL {ttl}s",
                    "Request transformation applied: {transformation}",
                    "Metrics collected for request {request_id}: {duration}ms"
                ]
            }
        }
        
        # Sample data for template variables
        self.sample_data = {
            "user_id": ["user123", "alice_smith", "bob_jones", "charlie_brown", "diana_prince"],
            "email": ["alice@example.com", "bob@company.org", "charlie@test.net", "diana@sample.io"],
            "ip_address": ["192.168.1.100", "10.0.0.50", "172.16.0.25", "203.0.113.42"],
            "session_id": ["sess_abc123", "sess_def456", "sess_ghi789", "sess_jkl012"],
            "api_key": ["ak_1234567890", "ak_abcdef1234", "ak_xyz9876543"],
            "client_id": ["client_web", "client_mobile", "client_api", "client_admin"],
            "card_number": ["****1234", "****5678", "****9012", "****3456"],
            "charge_id": ["ch_1A2B3C", "ch_4D5E6F", "ch_7G8H9I"],
            "payment_id": ["pay_abc123", "pay_def456", "pay_ghi789"],
            "txn_id": ["txn_001234", "txn_567890", "txn_abcdef"],
            "customer_id": ["cust_alice", "cust_bob", "cust_charlie"],
            "order_id": ["ord_2024001", "ord_2024002", "ord_2024003"],
            "merchant_id": ["merch_store1", "merch_shop2", "merch_outlet3"],
            "service_name": ["auth_service", "payment_service", "user_service", "notification_service"],
            "endpoint": ["/api/v1/users", "/api/v1/payments", "/api/v1/orders", "/api/v2/auth"],
            "method": ["GET", "POST", "PUT", "DELETE"],
            "status": ["200", "201", "400", "401", "403", "404", "500", "503"],
            "domain": ["api.example.com", "gateway.company.org", "service.test.net"]
        }
    
    def generate_timestamp(self, days_back: int = 7) -> str:
        """Generate a realistic timestamp within the last N days."""
        now = datetime.now()
        start_time = now - timedelta(days=days_back)
        random_time = start_time + timedelta(
            seconds=random.randint(0, int((now - start_time).total_seconds()))
        )
        return random_time.strftime("%Y-%m-%d %H:%M:%S")
    
    def fill_template(self, template: str) -> str:
        """Fill template variables with sample data."""
        result = template
        
        # Replace template variables
        for key, values in self.sample_data.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, random.choice(values))
        
        # Replace numeric placeholders
        numeric_placeholders = {
            "{amount}": lambda: f"{random.randint(10, 5000)}.{random.randint(10, 99)}",
            "{balance}": lambda: f"{random.randint(0, 1000)}.{random.randint(0, 99)}",
            "{count}": lambda: str(random.randint(1, 100)),
            "{attempt}": lambda: str(random.randint(1, 5)),
            "{retry}": lambda: str(random.randint(1, 3)),
            "{latency}": lambda: str(random.randint(50, 2000)),
            "{port}": lambda: str(random.choice([5432, 3306, 6379, 8080, 9000])),
            "{duration}": lambda: str(random.randint(10, 500)),
            "{ttl}": lambda: str(random.randint(60, 3600)),
            "{spike}": lambda: str(random.randint(150, 500)),
            "{queue_size}": lambda: str(random.randint(10, 100)),
            "{version}": lambda: str(random.randint(1, 3)),
            "{limit}": lambda: str(random.choice([100, 500, 1000])),
            "{current}": lambda: str(random.randint(80, 95))
        }
        
        for placeholder, generator in numeric_placeholders.items():
            if placeholder in result:
                result = result.replace(placeholder, generator())
        
        return result
    
    def generate_log_entry(self, service: str, severity: str, line_number: int) -> Dict[str, Any]:
        """Generate a single log entry."""
        timestamp = self.generate_timestamp()
        
        # Select random message template
        templates = self.error_templates[service][severity]
        template = random.choice(templates)
        message = self.fill_template(template)
        
        return {
            "timestamp": timestamp,
            "severity": severity,
            "service": service,
            "message": message,
            "line_number": line_number
        }
    
    def generate_logs(self, total_count: int = 500) -> List[Dict[str, Any]]:
        """Generate the specified number of log entries."""
        logs = []
        
        # Distribute logs across services (roughly equal)
        logs_per_service = total_count // len(self.services)
        remaining_logs = total_count % len(self.services)
        
        line_number = 1
        
        for i, service in enumerate(self.services):
            service_log_count = logs_per_service
            if i < remaining_logs:
                service_log_count += 1
            
            # Distribute severity levels (more errors and warnings for demo)
            severity_distribution = {
                "ERROR": int(service_log_count * 0.3),  # 30% errors
                "WARN": int(service_log_count * 0.25),   # 25% warnings  
                "INFO": int(service_log_count * 0.35),   # 35% info
                "DEBUG": int(service_log_count * 0.1)    # 10% debug
            }
            
            # Adjust for rounding
            total_distributed = sum(severity_distribution.values())
            if total_distributed < service_log_count:
                severity_distribution["INFO"] += service_log_count - total_distributed
            
            # Generate logs for each severity level
            for severity, count in severity_distribution.items():
                for _ in range(count):
                    log_entry = self.generate_log_entry(service, severity, line_number)
                    logs.append(log_entry)
                    line_number += 1
        
        # Shuffle logs to mix timestamps and services
        random.shuffle(logs)
        
        # Re-assign line numbers after shuffle
        for i, log in enumerate(logs, 1):
            log["line_number"] = i
        
        return logs
    
    def format_log_entry(self, log: Dict[str, Any], format_type: str = "standard") -> str:
        """Format log entry according to specified format."""
        if format_type == "json":
            return json.dumps(log)
        elif format_type == "standard":
            return f"[{log['timestamp']}] {log['severity']} [{log['service']}] {log['message']}"
        else:
            # Simple format
            return f"{log['timestamp']} {log['severity']}: {log['message']}"
    
    def write_service_logs(self, logs: List[Dict[str, Any]], output_dir: str = "data/sample_logs"):
        """Write logs to separate files by service."""
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Group logs by service
        service_logs = {service: [] for service in self.services}
        for log in logs:
            service_logs[log["service"]].append(log)
        
        # Write each service's logs to separate files
        for service, service_log_list in service_logs.items():
            filename = f"{service}.log"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for log in service_log_list:
                    formatted_log = self.format_log_entry(log, "standard")
                    f.write(formatted_log + "\n")
            
            print(f"✅ Generated {len(service_log_list)} log entries for {service} -> {filepath}")
        
        return service_logs


def main():
    """Main function to generate demo data."""
    print("🚀 ErrorLens Demo Data Generator")
    print("=" * 50)
    
    generator = DemoDataGenerator()
    
    # Generate 500 log entries
    print("📝 Generating 500 synthetic log entries...")
    logs = generator.generate_logs(500)
    
    # Write to service-specific files
    print("💾 Writing logs to service-specific files...")
    service_logs = generator.write_service_logs(logs)
    
    # Print summary
    print("\n📊 Generation Summary:")
    print("-" * 30)
    total_logs = 0
    for service, service_log_list in service_logs.items():
        severity_counts = {}
        for log in service_log_list:
            severity = log["severity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print(f"{service}: {len(service_log_list)} logs")
        for severity in ["ERROR", "WARN", "INFO", "DEBUG"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                print(f"  - {severity}: {count}")
        
        total_logs += len(service_log_list)
    
    print(f"\n✅ Total: {total_logs} log entries generated")
    print("📁 Files created in: data/sample_logs/")
    print("   - auth_service.log")
    print("   - payment_service.log") 
    print("   - api_gateway.log")
    print("\n🎉 Demo data generation complete!")


if __name__ == "__main__":
    main()