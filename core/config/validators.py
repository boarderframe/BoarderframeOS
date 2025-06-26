"""
ConfigValidator - Validates agent configurations before storage
Prevents invalid configs from breaking the system
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
from jsonschema import validate, ValidationError, Draft7Validator


class ConfigValidator:
    """Validates agent configurations against schema"""
    
    # Agent config schema
    AGENT_CONFIG_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["name", "role", "department", "goals", "tools", "system_prompt"],
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100,
                "pattern": "^[A-Za-z][A-Za-z0-9_-]*$"
            },
            "role": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200
            },
            "department": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            },
            "personality": {
                "type": "object",
                "properties": {
                    "traits": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 10
                    },
                    "communication_style": {
                        "type": "string",
                        "enum": ["formal", "friendly", "professional", "casual", "adaptive"]
                    }
                },
                "additionalProperties": True
            },
            "goals": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "maxItems": 20
            },
            "tools": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 50
            },
            "llm_model": {
                "type": "string",
                "enum": [
                    "claude-3-opus",
                    "claude-3-sonnet", 
                    "claude-3-haiku",
                    "gpt-4-turbo",
                    "gpt-3.5-turbo",
                    "local-llama",
                    "local-mistral"
                ]
            },
            "temperature": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 2.0
            },
            "max_tokens": {
                "type": "integer",
                "minimum": 1,
                "maximum": 32768
            },
            "system_prompt": {
                "type": "string",
                "minLength": 1,
                "maxLength": 10000
            },
            "context_prompt": {
                "type": ["string", "null"],
                "maxLength": 5000
            },
            "priority_level": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10
            },
            "compute_allocation": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 100.0
            },
            "memory_limit_gb": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 64.0
            },
            "max_concurrent_tasks": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100
            },
            "is_active": {
                "type": "boolean"
            },
            "development_status": {
                "type": "string",
                "enum": ["planned", "in_development", "testing", "operational", "deprecated"]
            }
        },
        "additionalProperties": False
    }
    
    # Risky operations that require additional validation
    RISKY_KEYWORDS = [
        "sudo", "rm -rf", "delete", "drop table", "truncate",
        "format", "wipe", "destroy", "kill", "terminate"
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r";\s*DROP\s+TABLE",
        r";\s*DELETE\s+FROM",
        r";\s*UPDATE\s+SET",
        r"'\s*OR\s*'1'\s*=\s*'1",
        r"--\s*$",
        r"/\*.*\*/",
        r"UNION\s+SELECT"
    ]
    
    def __init__(self):
        """Initialize config validator"""
        self.logger = logging.getLogger("ConfigValidator")
        self.schema_validator = Draft7Validator(self.AGENT_CONFIG_SCHEMA)
        
        # Validation statistics
        self.stats = {
            "total_validations": 0,
            "passed": 0,
            "failed": 0,
            "security_blocks": 0
        }
        
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate agent configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        self.stats["total_validations"] += 1
        errors = []
        
        # 1. Schema validation
        schema_errors = self._validate_schema(config)
        errors.extend(schema_errors)
        
        # 2. Security validation
        security_errors = self._validate_security(config)
        errors.extend(security_errors)
        
        # 3. Business rule validation
        business_errors = self._validate_business_rules(config)
        errors.extend(business_errors)
        
        # 4. Resource limit validation
        resource_errors = self._validate_resource_limits(config)
        errors.extend(resource_errors)
        
        # Update stats
        if errors:
            self.stats["failed"] += 1
            self.logger.warning(f"Config validation failed for {config.get('name', 'unknown')}: {errors}")
        else:
            self.stats["passed"] += 1
            
        return (len(errors) == 0, errors)
        
    def validate_update(self, current_config: Dict[str, Any], 
                       updates: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate config updates
        
        Args:
            current_config: Current configuration
            updates: Proposed updates
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        # Merge configs for validation
        new_config = {**current_config, **updates}
        
        # Validate merged config
        is_valid, errors = self.validate_config(new_config)
        
        # Additional update-specific checks
        if is_valid:
            update_errors = self._validate_update_rules(current_config, updates)
            if update_errors:
                is_valid = False
                errors.extend(update_errors)
                
        return (is_valid, errors)
        
    def sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize configuration to remove dangerous content
        
        Args:
            config: Configuration to sanitize
            
        Returns:
            Sanitized configuration
        """
        sanitized = config.copy()
        
        # Sanitize string fields
        string_fields = ["name", "role", "department", "system_prompt", "context_prompt"]
        
        for field in string_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = self._sanitize_string(sanitized[field])
                
        # Sanitize arrays
        if "goals" in sanitized:
            sanitized["goals"] = [self._sanitize_string(g) for g in sanitized["goals"]]
            
        if "tools" in sanitized:
            sanitized["tools"] = [self._sanitize_string(t) for t in sanitized["tools"]]
            
        # Sanitize personality traits
        if "personality" in sanitized and "traits" in sanitized["personality"]:
            sanitized["personality"]["traits"] = [
                self._sanitize_string(t) for t in sanitized["personality"]["traits"]
            ]
            
        return sanitized
        
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total = self.stats["total_validations"]
        success_rate = (self.stats["passed"] / total * 100) if total > 0 else 0
        
        return {
            **self.stats,
            "success_rate": round(success_rate, 2),
            "security_block_rate": round(
                (self.stats["security_blocks"] / total * 100) if total > 0 else 0, 
                2
            )
        }
        
    def _validate_schema(self, config: Dict[str, Any]) -> List[str]:
        """Validate against JSON schema"""
        errors = []
        
        try:
            validate(instance=config, schema=self.AGENT_CONFIG_SCHEMA)
        except ValidationError as e:
            # Extract all validation errors
            for error in self.schema_validator.iter_errors(config):
                path = " -> ".join(str(p) for p in error.path)
                errors.append(f"Schema error at {path}: {error.message}")
                
        return errors
        
    def _validate_security(self, config: Dict[str, Any]) -> List[str]:
        """Validate security aspects"""
        errors = []
        
        # Check all string fields for injection attempts
        for key, value in self._flatten_dict(config).items():
            if isinstance(value, str):
                # Check for SQL injection
                for pattern in self.SQL_INJECTION_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        errors.append(f"Potential SQL injection in {key}")
                        self.stats["security_blocks"] += 1
                        break
                        
                # Check for risky operations
                value_lower = value.lower()
                for keyword in self.RISKY_KEYWORDS:
                    if keyword in value_lower:
                        errors.append(f"Risky keyword '{keyword}' found in {key}")
                        self.stats["security_blocks"] += 1
                        
        # Validate system prompt doesn't contain secrets
        if "system_prompt" in config:
            if self._contains_secrets(config["system_prompt"]):
                errors.append("System prompt appears to contain secrets or credentials")
                self.stats["security_blocks"] += 1
                
        return errors
        
    def _validate_business_rules(self, config: Dict[str, Any]) -> List[str]:
        """Validate business logic rules"""
        errors = []
        
        # Executive agents must use premium models
        if config.get("department") == "Executive":
            model = config.get("llm_model", "")
            if model not in ["claude-3-opus", "gpt-4-turbo"]:
                errors.append("Executive agents must use premium LLM models")
                
        # Operational agents must have at least 3 goals
        if config.get("development_status") == "operational":
            goals = config.get("goals", [])
            if len(goals) < 3:
                errors.append("Operational agents must have at least 3 goals")
                
        # High priority agents need more resources
        if config.get("priority_level", 5) >= 8:
            compute = config.get("compute_allocation", 0)
            if compute < 10.0:
                errors.append("High priority agents require at least 10GB compute allocation")
                
        # Deprecated agents should not be active
        if config.get("development_status") == "deprecated" and config.get("is_active", True):
            errors.append("Deprecated agents should not be active")
            
        return errors
        
    def _validate_resource_limits(self, config: Dict[str, Any]) -> List[str]:
        """Validate resource allocation limits"""
        errors = []
        
        # Check combined resource usage
        compute = config.get("compute_allocation", 0)
        memory = config.get("memory_limit_gb", 0)
        tasks = config.get("max_concurrent_tasks", 0)
        
        # Total resource score
        resource_score = (compute * 0.5) + (memory * 0.3) + (tasks * 0.2)
        
        if resource_score > 50:
            errors.append("Total resource allocation exceeds limits")
            
        # LLM model specific limits
        model = config.get("llm_model", "")
        if model == "claude-3-opus" and tasks > 10:
            errors.append("Opus model limited to 10 concurrent tasks")
            
        return errors
        
    def _validate_update_rules(self, current: Dict[str, Any], 
                              updates: Dict[str, Any]) -> List[str]:
        """Validate update-specific rules"""
        errors = []
        
        # Cannot change agent name
        if "name" in updates and updates["name"] != current.get("name"):
            errors.append("Agent name cannot be changed")
            
        # Cannot downgrade operational to planned
        current_status = current.get("development_status", "")
        new_status = updates.get("development_status", current_status)
        
        status_order = ["planned", "in_development", "testing", "operational", "deprecated"]
        
        if (current_status in status_order and new_status in status_order and
            status_order.index(new_status) < status_order.index(current_status) and
            new_status != "deprecated"):
            errors.append(f"Cannot downgrade from {current_status} to {new_status}")
            
        return errors
        
    def _sanitize_string(self, value: str) -> str:
        """Sanitize string value"""
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Escape HTML/XML
        value = value.replace('<', '&lt;').replace('>', '&gt;')
        
        # Remove control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        # Truncate if too long
        max_length = 10000
        if len(value) > max_length:
            value = value[:max_length] + "..."
            
        return value.strip()
        
    def _contains_secrets(self, text: str) -> bool:
        """Check if text contains potential secrets"""
        secret_patterns = [
            r'api[_-]?key\s*[:=]\s*["\']?[\w-]+',
            r'password\s*[:=]\s*["\']?[\w-]+',
            r'secret\s*[:=]\s*["\']?[\w-]+',
            r'token\s*[:=]\s*["\']?[\w-]+',
            r'-----BEGIN\s+\w+\s+PRIVATE\s+KEY-----',
            r'[a-zA-Z0-9+/]{40,}={0,2}'  # Base64 encoded strings
        ]
        
        text_lower = text.lower()
        
        for pattern in secret_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
                
        return False
        
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', 
                     sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(
                            self._flatten_dict(item, f"{new_key}[{i}]", sep=sep).items()
                        )
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
                
        return dict(items)