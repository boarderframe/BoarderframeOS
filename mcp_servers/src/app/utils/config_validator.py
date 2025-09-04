"""
Configuration validation utilities for MCP Server Management

This module provides comprehensive validation for MCP server configurations
including security policy validation, resource limit checking, and compliance
verification.
"""

import json
import re
import ipaddress
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import jsonschema
from jsonschema import validate, ValidationError
import yaml


class ValidationSeverity(Enum):
    """Severity levels for validation errors."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ValidationResult:
    """Result of a configuration validation check."""
    severity: ValidationSeverity
    message: str
    path: str
    suggestion: Optional[str] = None
    code: Optional[str] = None


class SecurityConfigValidator:
    """Validates security-related configuration settings."""
    
    # Security best practices thresholds
    MIN_SESSION_TIMEOUT = 5  # minutes
    MAX_SESSION_TIMEOUT = 1440  # 24 hours
    MIN_TLS_VERSION = "1.2"
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    MIN_PASSWORD_LENGTH = 12
    
    # Dangerous file extensions that should be blocked
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js', 
        '.jar', '.sh', '.ps1', '.msi', '.dll', '.sys', '.bin'
    }
    
    # System paths that should be protected
    PROTECTED_PATHS = {
        '/etc', '/proc', '/sys', '/dev', '/root', '/boot', '/usr/bin',
        '/usr/sbin', '/sbin', '/bin', '/var/run', '/var/lib'
    }
    
    @classmethod
    def validate_security_policy(cls, policy: Dict[str, Any], path: str = "security.global_policy") -> List[ValidationResult]:
        """Validate global security policy configuration."""
        results = []
        
        # Check authentication requirements
        if not policy.get('require_authentication', True):
            results.append(ValidationResult(
                severity=ValidationSeverity.CRITICAL,
                message="Authentication is disabled - this is a critical security risk",
                path=f"{path}.require_authentication",
                suggestion="Set require_authentication to true",
                code="SEC001"
            ))
        
        # Check TLS configuration
        if not policy.get('require_tls', True):
            results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                message="TLS is disabled - data transmission is not encrypted",
                path=f"{path}.require_tls",
                suggestion="Set require_tls to true",
                code="SEC002"
            ))
        
        min_tls = policy.get('min_tls_version', '1.2')
        if min_tls < cls.MIN_TLS_VERSION:
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"TLS version {min_tls} is below recommended minimum {cls.MIN_TLS_VERSION}",
                path=f"{path}.min_tls_version",
                suggestion=f"Use TLS version {cls.MIN_TLS_VERSION} or higher",
                code="SEC003"
            ))
        
        # Check session timeout
        session_timeout = policy.get('session_timeout_minutes', 480)
        if session_timeout < cls.MIN_SESSION_TIMEOUT:
            results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                message=f"Session timeout {session_timeout} minutes is too short",
                path=f"{path}.session_timeout_minutes",
                suggestion=f"Use minimum {cls.MIN_SESSION_TIMEOUT} minutes",
                code="SEC004"
            ))
        elif session_timeout > cls.MAX_SESSION_TIMEOUT:
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"Session timeout {session_timeout} minutes may be too long",
                path=f"{path}.session_timeout_minutes",
                suggestion=f"Consider using maximum {cls.MAX_SESSION_TIMEOUT} minutes",
                code="SEC005"
            ))
        
        # Check MFA requirement for production
        if not policy.get('require_mfa', False):
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message="Multi-factor authentication is not required",
                path=f"{path}.require_mfa",
                suggestion="Enable MFA for enhanced security, especially in production",
                code="SEC006"
            ))
        
        # Check audit logging
        if not policy.get('enable_audit_logging', True):
            results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                message="Audit logging is disabled - security events will not be tracked",
                path=f"{path}.enable_audit_logging",
                suggestion="Enable audit logging for compliance and security monitoring",
                code="SEC007"
            ))
        
        # Check intrusion detection
        if not policy.get('enable_intrusion_detection', True):
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message="Intrusion detection is disabled",
                path=f"{path}.enable_intrusion_detection",
                suggestion="Enable intrusion detection for threat monitoring",
                code="SEC008"
            ))
        
        return results
    
    @classmethod
    def validate_network_security(cls, network_config: Dict[str, Any], path: str = "security.network_security") -> List[ValidationResult]:
        """Validate network security configuration."""
        results = []
        
        # Validate IP ranges
        allowed_ranges = network_config.get('allowed_ip_ranges', [])
        for i, ip_range in enumerate(allowed_ranges):
            try:
                ipaddress.ip_network(ip_range, strict=False)
            except ValueError as e:
                results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid IP range '{ip_range}': {str(e)}",
                    path=f"{path}.allowed_ip_ranges[{i}]",
                    suggestion="Use valid CIDR notation (e.g., 192.168.1.0/24)",
                    code="NET001"
                ))
        
        # Check for overly permissive ranges
        for i, ip_range in enumerate(allowed_ranges):
            try:
                network = ipaddress.ip_network(ip_range, strict=False)
                if network.prefixlen < 8:  # /8 or larger
                    results.append(ValidationResult(
                        severity=ValidationSeverity.WARNING,
                        message=f"IP range '{ip_range}' is very broad and may be too permissive",
                        path=f"{path}.allowed_ip_ranges[{i}]",
                        suggestion="Consider using more specific IP ranges",
                        code="NET002"
                    ))
            except ValueError:
                pass  # Already handled above
        
        # Validate rate limiting
        rate_limiting = network_config.get('rate_limiting', {})
        if rate_limiting.get('enabled', True):
            rpm = rate_limiting.get('requests_per_minute', 100)
            if rpm > 10000:
                results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    message=f"Rate limit {rpm} requests/minute is very high",
                    path=f"{path}.rate_limiting.requests_per_minute",
                    suggestion="Consider lower rate limits to prevent abuse",
                    code="NET003"
                ))
        else:
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message="Rate limiting is disabled",
                path=f"{path}.rate_limiting.enabled",
                suggestion="Enable rate limiting to prevent DoS attacks",
                code="NET004"
            ))
        
        return results
    
    @classmethod
    def validate_server_security(cls, server_config: Dict[str, Any], server_id: str) -> List[ValidationResult]:
        """Validate individual server security configuration."""
        results = []
        path = f"servers[{server_id}].security"
        
        security = server_config.get('security', {})
        access_restrictions = security.get('access_restrictions', {})
        
        # Check file system access restrictions
        allowed_paths = access_restrictions.get('allowed_paths', [])
        denied_paths = access_restrictions.get('denied_paths', [])
        
        # Check for dangerous path access
        for i, allowed_path in enumerate(allowed_paths):
            for protected_path in cls.PROTECTED_PATHS:
                if allowed_path.startswith(protected_path):
                    results.append(ValidationResult(
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Allowed path '{allowed_path}' grants access to protected system directory",
                        path=f"{path}.access_restrictions.allowed_paths[{i}]",
                        suggestion=f"Remove access to {protected_path} or use more specific paths",
                        code="SEC009"
                    ))
        
        # Check file extension restrictions
        allowed_extensions = access_restrictions.get('allowed_extensions', [])
        denied_extensions = access_restrictions.get('denied_extensions', [])
        
        for dangerous_ext in cls.DANGEROUS_EXTENSIONS:
            if dangerous_ext in allowed_extensions:
                results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    message=f"Dangerous file extension '{dangerous_ext}' is explicitly allowed",
                    path=f"{path}.access_restrictions.allowed_extensions",
                    suggestion=f"Remove '{dangerous_ext}' from allowed extensions",
                    code="SEC010"
                ))
            
            if dangerous_ext not in denied_extensions and allowed_extensions:
                results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    message=f"Dangerous file extension '{dangerous_ext}' is not explicitly denied",
                    path=f"{path}.access_restrictions.denied_extensions",
                    suggestion=f"Add '{dangerous_ext}' to denied extensions",
                    code="SEC011"
                ))
        
        # Check resource limits
        resource_limits = security.get('resource_limits', {})
        
        max_cpu = resource_limits.get('max_cpu_percent')
        if max_cpu and max_cpu > 80:
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"CPU limit {max_cpu}% is very high",
                path=f"{path}.resource_limits.max_cpu_percent",
                suggestion="Consider lower CPU limits to prevent resource exhaustion",
                code="SEC012"
            ))
        
        max_memory = resource_limits.get('max_memory_mb')
        if max_memory and max_memory > 8192:  # 8GB
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"Memory limit {max_memory}MB is very high",
                path=f"{path}.resource_limits.max_memory_mb",
                suggestion="Consider lower memory limits to prevent resource exhaustion",
                code="SEC013"
            ))
        
        # Check database security for postgres servers
        if server_config.get('name', '').startswith('postgres'):
            cls._validate_database_security(access_restrictions, f"{path}.access_restrictions", results)
        
        return results
    
    @classmethod
    def _validate_database_security(cls, restrictions: Dict[str, Any], path: str, results: List[ValidationResult]) -> None:
        """Validate database-specific security settings."""
        
        # Check for dangerous SQL operations
        allowed_operations = restrictions.get('allowed_operations', [])
        dangerous_operations = {'DELETE', 'DROP', 'TRUNCATE', 'ALTER'}
        
        for dangerous_op in dangerous_operations:
            if dangerous_op in allowed_operations:
                results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    message=f"Dangerous SQL operation '{dangerous_op}' is allowed",
                    path=f"{path}.allowed_operations",
                    suggestion=f"Remove '{dangerous_op}' from allowed operations or ensure proper authorization",
                    code="DB001"
                ))
        
        # Check for system database access
        allowed_databases = restrictions.get('allowed_databases', [])
        system_databases = {'postgres', 'template0', 'template1', 'information_schema'}
        
        for system_db in system_databases:
            if system_db in allowed_databases:
                results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    message=f"System database '{system_db}' is accessible",
                    path=f"{path}.allowed_databases",
                    suggestion=f"Consider removing access to system database '{system_db}'",
                    code="DB002"
                ))
        
        # Check WHERE clause requirement
        if not restrictions.get('require_where_clause', True):
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message="WHERE clause is not required for queries",
                path=f"{path}.require_where_clause",
                suggestion="Require WHERE clause to prevent accidental full table operations",
                code="DB003"
            ))


class ComplianceValidator:
    """Validates configuration against compliance standards."""
    
    COMPLIANCE_REQUIREMENTS = {
        'SOC2': {
            'audit_logging': True,
            'encryption_required': True,
            'access_controls': True,
            'min_log_retention_days': 365
        },
        'ISO27001': {
            'audit_logging': True,
            'encryption_required': True,
            'access_controls': True,
            'incident_response': True,
            'min_log_retention_days': 365
        },
        'GDPR': {
            'audit_logging': True,
            'encryption_required': True,
            'data_minimization': True,
            'right_to_deletion': True,
            'min_log_retention_days': 1095  # 3 years
        },
        'HIPAA': {
            'audit_logging': True,
            'encryption_required': True,
            'access_controls': True,
            'min_log_retention_days': 2190  # 6 years
        }
    }
    
    @classmethod
    def validate_compliance(cls, config: Dict[str, Any], standards: List[str]) -> List[ValidationResult]:
        """Validate configuration against specified compliance standards."""
        results = []
        
        for standard in standards:
            if standard not in cls.COMPLIANCE_REQUIREMENTS:
                results.append(ValidationResult(
                    severity=ValidationSeverity.WARNING,
                    message=f"Unknown compliance standard '{standard}'",
                    path="compliance.standards",
                    suggestion="Use supported standards: SOC2, ISO27001, GDPR, HIPAA",
                    code="COMP001"
                ))
                continue
            
            requirements = cls.COMPLIANCE_REQUIREMENTS[standard]
            results.extend(cls._check_compliance_requirements(config, standard, requirements))
        
        return results
    
    @classmethod
    def _check_compliance_requirements(cls, config: Dict[str, Any], standard: str, requirements: Dict[str, Any]) -> List[ValidationResult]:
        """Check specific compliance requirements."""
        results = []
        
        # Check audit logging requirement
        if requirements.get('audit_logging'):
            if not config.get('security', {}).get('global_policy', {}).get('enable_audit_logging', True):
                results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    message=f"{standard} requires audit logging to be enabled",
                    path="security.global_policy.enable_audit_logging",
                    suggestion="Enable audit logging for compliance",
                    code=f"COMP_{standard}_001"
                ))
        
        # Check encryption requirement
        if requirements.get('encryption_required'):
            if not config.get('security', {}).get('data_protection', {}).get('encrypt_sensitive_config', True):
                results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    message=f"{standard} requires encryption of sensitive data",
                    path="security.data_protection.encrypt_sensitive_config",
                    suggestion="Enable encryption for sensitive configuration data",
                    code=f"COMP_{standard}_002"
                ))
        
        # Check log retention
        min_retention = requirements.get('min_log_retention_days')
        if min_retention:
            compliance_config = config.get('compliance', {})
            audit_requirements = compliance_config.get('audit_requirements', {})
            retention_days = audit_requirements.get('retain_logs_days', 90)
            
            if retention_days < min_retention:
                results.append(ValidationResult(
                    severity=ValidationSeverity.ERROR,
                    message=f"{standard} requires log retention of at least {min_retention} days, configured: {retention_days}",
                    path="compliance.audit_requirements.retain_logs_days",
                    suggestion=f"Set retention to at least {min_retention} days",
                    code=f"COMP_{standard}_003"
                ))
        
        return results


class ConfigurationValidator:
    """Main configuration validator that orchestrates all validation checks."""
    
    def __init__(self, schema_path: Optional[str] = None):
        """Initialize validator with optional schema path."""
        self.schema_path = schema_path
        self.schema = None
        
        if schema_path:
            self.load_schema(schema_path)
    
    def load_schema(self, schema_path: str) -> None:
        """Load JSON schema for validation."""
        try:
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load schema from {schema_path}: {str(e)}")
    
    def validate_config(self, config_path: str) -> Tuple[bool, List[ValidationResult]]:
        """Validate configuration file and return results."""
        results = []
        
        try:
            # Load configuration
            config = self._load_config(config_path)
            
            # Schema validation
            if self.schema:
                schema_results = self._validate_schema(config)
                results.extend(schema_results)
            
            # Security validation
            security_results = self._validate_security(config)
            results.extend(security_results)
            
            # Compliance validation
            compliance_results = self._validate_compliance(config)
            results.extend(compliance_results)
            
            # Performance validation
            performance_results = self._validate_performance(config)
            results.extend(performance_results)
            
            # Check if validation passed (no ERROR or CRITICAL issues)
            has_errors = any(r.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL] for r in results)
            
            return not has_errors, results
            
        except Exception as e:
            results.append(ValidationResult(
                severity=ValidationSeverity.CRITICAL,
                message=f"Failed to validate configuration: {str(e)}",
                path="<root>",
                code="VAL001"
            ))
            return False, results
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file (supports JSON and YAML)."""
        path = Path(config_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(path, 'r') as f:
            if path.suffix.lower() == '.json':
                return json.load(f)
            elif path.suffix.lower() in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            else:
                # Try to detect format by content
                content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    try:
                        return yaml.safe_load(content)
                    except yaml.YAMLError:
                        raise ValueError(f"Unsupported configuration format: {path.suffix}")
    
    def _validate_schema(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate configuration against JSON schema."""
        results = []
        
        try:
            validate(instance=config, schema=self.schema)
        except ValidationError as e:
            # Convert jsonschema validation error to our format
            path = '.'.join(str(p) for p in e.absolute_path) if e.absolute_path else '<root>'
            results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                message=f"Schema validation failed: {e.message}",
                path=path,
                suggestion="Fix the configuration to match the required schema",
                code="SCHEMA001"
            ))
        except Exception as e:
            results.append(ValidationResult(
                severity=ValidationSeverity.ERROR,
                message=f"Schema validation error: {str(e)}",
                path="<root>",
                code="SCHEMA002"
            ))
        
        return results
    
    def _validate_security(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Perform security-specific validation."""
        results = []
        
        # Validate global security policy
        security = config.get('security', {})
        global_policy = security.get('global_policy', {})
        results.extend(SecurityConfigValidator.validate_security_policy(global_policy))
        
        # Validate network security
        network_security = security.get('network_security', {})
        results.extend(SecurityConfigValidator.validate_network_security(network_security))
        
        # Validate individual server security
        servers = config.get('servers', [])
        for server in servers:
            server_id = server.get('id', 'unknown')
            results.extend(SecurityConfigValidator.validate_server_security(server, server_id))
        
        return results
    
    def _validate_compliance(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate compliance requirements."""
        results = []
        
        compliance = config.get('compliance', {})
        standards = compliance.get('standards', [])
        
        if standards:
            results.extend(ComplianceValidator.validate_compliance(config, standards))
        
        return results
    
    def _validate_performance(self, config: Dict[str, Any]) -> List[ValidationResult]:
        """Validate performance-related settings."""
        results = []
        
        # Check server count limits
        servers = config.get('servers', [])
        max_servers = config.get('global_settings', {}).get('performance', {}).get('max_servers', 50)
        
        if len(servers) > max_servers:
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"Configuration has {len(servers)} servers, exceeds limit of {max_servers}",
                path="servers",
                suggestion=f"Reduce server count or increase max_servers limit",
                code="PERF001"
            ))
        
        # Check for resource contention
        total_cpu = 0
        total_memory = 0
        
        for server in servers:
            if not server.get('enabled', True):
                continue
                
            security = server.get('security', {})
            limits = security.get('resource_limits', {})
            
            cpu_limit = limits.get('max_cpu_percent', 50)
            memory_limit = limits.get('max_memory_mb', 512)
            
            total_cpu += cpu_limit
            total_memory += memory_limit
        
        if total_cpu > 400:  # More than 4 full CPUs
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"Total CPU allocation {total_cpu}% may cause resource contention",
                path="servers",
                suggestion="Review CPU limits to prevent over-allocation",
                code="PERF002"
            ))
        
        if total_memory > 16384:  # More than 16GB
            results.append(ValidationResult(
                severity=ValidationSeverity.WARNING,
                message=f"Total memory allocation {total_memory}MB may cause resource contention",
                path="servers", 
                suggestion="Review memory limits to prevent over-allocation",
                code="PERF003"
            ))
        
        return results
    
    def generate_report(self, results: List[ValidationResult]) -> str:
        """Generate a human-readable validation report."""
        if not results:
            return "✅ Configuration validation passed with no issues."
        
        # Group results by severity
        by_severity = {}
        for result in results:
            severity = result.severity.value
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(result)
        
        report_lines = ["🔍 Configuration Validation Report", "=" * 50, ""]
        
        # Summary
        total_issues = len(results)
        critical_count = len(by_severity.get('CRITICAL', []))
        error_count = len(by_severity.get('ERROR', []))
        warning_count = len(by_severity.get('WARNING', []))
        info_count = len(by_severity.get('INFO', []))
        
        report_lines.extend([
            f"📊 Summary: {total_issues} issues found",
            f"  🔴 Critical: {critical_count}",
            f"  🟠 Error: {error_count}",
            f"  🟡 Warning: {warning_count}",
            f"  🔵 Info: {info_count}",
            ""
        ])
        
        # Detailed results by severity
        severity_order = ['CRITICAL', 'ERROR', 'WARNING', 'INFO']
        severity_icons = {'CRITICAL': '🔴', 'ERROR': '🟠', 'WARNING': '🟡', 'INFO': '🔵'}
        
        for severity in severity_order:
            if severity not in by_severity:
                continue
                
            icon = severity_icons[severity]
            report_lines.extend([f"{icon} {severity} Issues:", ""])
            
            for result in by_severity[severity]:
                report_lines.append(f"  {result.code or 'N/A'}: {result.message}")
                report_lines.append(f"    📍 Path: {result.path}")
                if result.suggestion:
                    report_lines.append(f"    💡 Suggestion: {result.suggestion}")
                report_lines.append("")
        
        return "\n".join(report_lines)


def main():
    """CLI entry point for configuration validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate MCP Server Configuration")
    parser.add_argument("config", help="Path to configuration file")
    parser.add_argument("--schema", help="Path to JSON schema file")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--fail-on-warning", action="store_true", help="Exit with error on warnings")
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = ConfigurationValidator(args.schema)
    
    # Validate configuration
    is_valid, results = validator.validate_config(args.config)
    
    # Generate output
    if args.output == "json":
        output = {
            "valid": is_valid,
            "issues": [
                {
                    "severity": r.severity.value,
                    "message": r.message,
                    "path": r.path,
                    "suggestion": r.suggestion,
                    "code": r.code
                }
                for r in results
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print(validator.generate_report(results))
    
    # Determine exit code
    has_critical_or_error = any(r.severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR] for r in results)
    has_warning = any(r.severity == ValidationSeverity.WARNING for r in results)
    
    if has_critical_or_error:
        exit(1)
    elif args.fail_on_warning and has_warning:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()