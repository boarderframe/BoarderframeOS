"""
Secret Management System for BoarderframeOS
Secure handling of API keys, database credentials, and sensitive configuration
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


@dataclass
class SecretMetadata:
    """Metadata for a secret"""
    name: str
    category: str
    description: str
    created_at: str
    last_accessed: Optional[str] = None
    access_count: int = 0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class SecretManager:
    """
    Centralized secret management system
    
    Features:
    - Encrypted storage of secrets
    - Environment variable fallback
    - Secret rotation and versioning
    - Access logging and audit trail
    - Category-based organization
    """
    
    def __init__(self, secrets_file: str = "secrets/secrets.enc", master_key: Optional[str] = None):
        self.secrets_file = Path(secrets_file)
        self.secrets_dir = self.secrets_file.parent
        self.metadata_file = self.secrets_dir / "metadata.json"
        
        # Ensure secrets directory exists
        self.secrets_dir.mkdir(mode=0o700, exist_ok=True)
        
        # Initialize encryption
        self._cipher = self._get_cipher(master_key)
        
        # Load existing secrets and metadata
        self._secrets: Dict[str, Any] = {}
        self._metadata: Dict[str, SecretMetadata] = {}
        self._load_secrets()
        self._load_metadata()
        
        # Secret categories
        self.categories = {
            "database": ["DB_PASSWORD", "DB_USERNAME", "POSTGRES_PASSWORD"],
            "api_keys": ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CLAUDE_API_KEY"],
            "infrastructure": ["REDIS_PASSWORD", "DOCKER_PASSWORD"],
            "authentication": ["JWT_SECRET", "SESSION_SECRET", "WEBHOOK_SECRET"],
            "external_services": ["STRIPE_API_KEY", "GITHUB_TOKEN", "SLACK_TOKEN"]
        }
        
    def _get_cipher(self, master_key: Optional[str] = None) -> Fernet:
        """Get encryption cipher"""
        if master_key:
            key = master_key.encode()
        else:
            # Try to get from environment
            key = os.environ.get("BOARDERFRAME_MASTER_KEY", "").encode()
            
        if not key:
            # Generate a new key if none exists
            key_file = self.secrets_dir / ".master.key"
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                # Generate new master key
                salt = os.urandom(16)
                default_password = "boarderframe_default_key_change_me"
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(default_password.encode()))
                
                # Save key file
                with open(key_file, 'wb') as f:
                    f.write(key)
                key_file.chmod(0o600)
                
                logger.warning("Generated new master key. Please set BOARDERFRAME_MASTER_KEY environment variable")
                
        return Fernet(key)
        
    def _load_secrets(self):
        """Load encrypted secrets from file"""
        if not self.secrets_file.exists():
            return
            
        try:
            with open(self.secrets_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = self._cipher.decrypt(encrypted_data)
            self._secrets = json.loads(decrypted_data.decode())
            
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            self._secrets = {}
            
    def _save_secrets(self):
        """Save encrypted secrets to file"""
        try:
            data = json.dumps(self._secrets, indent=2).encode()
            encrypted_data = self._cipher.encrypt(data)
            
            with open(self.secrets_file, 'wb') as f:
                f.write(encrypted_data)
                
            self.secrets_file.chmod(0o600)
            
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")
            
    def _load_metadata(self):
        """Load secret metadata"""
        if not self.metadata_file.exists():
            return
            
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                
            self._metadata = {
                name: SecretMetadata(**meta_data)
                for name, meta_data in data.items()
            }
            
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            self._metadata = {}
            
    def _save_metadata(self):
        """Save secret metadata"""
        try:
            data = {
                name: asdict(metadata)
                for name, metadata in self._metadata.items()
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            self.metadata_file.chmod(0o600)
            
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            
    def set_secret(self, name: str, value: str, category: str = "general", 
                   description: str = "", tags: List[str] = None) -> bool:
        """Set a secret value"""
        try:
            import datetime
            
            # Store the secret
            self._secrets[name] = value
            
            # Update metadata
            if name not in self._metadata:
                self._metadata[name] = SecretMetadata(
                    name=name,
                    category=category,
                    description=description,
                    created_at=datetime.datetime.now().isoformat(),
                    tags=tags or []
                )
            else:
                # Update existing metadata
                self._metadata[name].description = description
                self._metadata[name].category = category
                if tags:
                    self._metadata[name].tags = tags
                    
            # Save to disk
            self._save_secrets()
            self._save_metadata()
            
            logger.info(f"Secret '{name}' set successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set secret '{name}': {e}")
            return False
            
    def get_secret(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a secret value with fallback to environment variables"""
        try:
            import datetime
            
            # Try stored secrets first
            if name in self._secrets:
                value = self._secrets[name]
                
                # Update access metadata
                if name in self._metadata:
                    self._metadata[name].last_accessed = datetime.datetime.now().isoformat()
                    self._metadata[name].access_count += 1
                    self._save_metadata()
                    
                return value
                
            # Fallback to environment variables
            env_value = os.environ.get(name)
            if env_value:
                logger.debug(f"Using environment variable for secret '{name}'")
                return env_value
                
            # Return default if provided
            if default is not None:
                logger.debug(f"Using default value for secret '{name}'")
                return default
                
            logger.warning(f"Secret '{name}' not found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get secret '{name}': {e}")
            return default
            
    def delete_secret(self, name: str) -> bool:
        """Delete a secret"""
        try:
            if name in self._secrets:
                del self._secrets[name]
                
            if name in self._metadata:
                del self._metadata[name]
                
            self._save_secrets()
            self._save_metadata()
            
            logger.info(f"Secret '{name}' deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret '{name}': {e}")
            return False
            
    def list_secrets(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available secrets (metadata only, not values)"""
        secrets_list = []
        
        for name, metadata in self._metadata.items():
            if category and metadata.category != category:
                continue
                
            secret_info = {
                "name": name,
                "category": metadata.category,
                "description": metadata.description,
                "created_at": metadata.created_at,
                "last_accessed": metadata.last_accessed,
                "access_count": metadata.access_count,
                "tags": metadata.tags,
                "exists_in_env": name in os.environ
            }
            secrets_list.append(secret_info)
            
        return sorted(secrets_list, key=lambda x: x["name"])
        
    def get_category_secrets(self, category: str) -> Dict[str, str]:
        """Get all secrets in a category"""
        secrets = {}
        
        for name, metadata in self._metadata.items():
            if metadata.category == category:
                value = self.get_secret(name)
                if value:
                    secrets[name] = value
                    
        return secrets
        
    def rotate_secret(self, name: str, new_value: str) -> bool:
        """Rotate a secret (keep old version as backup)"""
        try:
            if name not in self._secrets:
                logger.error(f"Cannot rotate non-existent secret '{name}'")
                return False
                
            # Keep old value as backup
            old_value = self._secrets[name]
            backup_name = f"{name}_backup_{secrets.token_hex(4)}"
            
            self._secrets[backup_name] = old_value
            self._secrets[name] = new_value
            
            # Update metadata
            import datetime
            if name in self._metadata:
                self._metadata[name].last_accessed = datetime.datetime.now().isoformat()
                
            # Create backup metadata
            if name in self._metadata:
                backup_metadata = SecretMetadata(
                    name=backup_name,
                    category=f"{self._metadata[name].category}_backup",
                    description=f"Backup of {name}",
                    created_at=datetime.datetime.now().isoformat(),
                    tags=["backup", "rotated"]
                )
                self._metadata[backup_name] = backup_metadata
                
            self._save_secrets()
            self._save_metadata()
            
            logger.info(f"Secret '{name}' rotated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rotate secret '{name}': {e}")
            return False
            
    def import_from_env(self, prefix: str = "") -> int:
        """Import secrets from environment variables"""
        imported_count = 0
        
        for key, value in os.environ.items():
            if prefix and not key.startswith(prefix):
                continue
                
            # Determine category
            category = "general"
            for cat_name, cat_secrets in self.categories.items():
                if any(secret in key for secret in cat_secrets):
                    category = cat_name
                    break
                    
            # Import if not already stored
            if key not in self._secrets:
                if self.set_secret(
                    name=key,
                    value=value,
                    category=category,
                    description=f"Imported from environment",
                    tags=["imported", "environment"]
                ):
                    imported_count += 1
                    
        logger.info(f"Imported {imported_count} secrets from environment")
        return imported_count
        
    def export_to_env_file(self, file_path: str, category: Optional[str] = None) -> bool:
        """Export secrets to .env file format"""
        try:
            with open(file_path, 'w') as f:
                f.write("# BoarderframeOS Secrets\n")
                f.write("# Generated by SecretManager\n\n")
                
                for name, metadata in self._metadata.items():
                    if category and metadata.category != category:
                        continue
                        
                    value = self._secrets.get(name)
                    if value:
                        f.write(f"# {metadata.description}\n")
                        f.write(f"{name}={value}\n\n")
                        
            os.chmod(file_path, 0o600)
            logger.info(f"Secrets exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export secrets: {e}")
            return False
            
    def validate_secrets(self) -> Dict[str, List[str]]:
        """Validate that required secrets are available"""
        validation_results = {
            "missing": [],
            "empty": [],
            "available": []
        }
        
        # Check common required secrets
        required_secrets = [
            "ANTHROPIC_API_KEY",
            "DB_PASSWORD", 
            "POSTGRES_PASSWORD"
        ]
        
        for secret_name in required_secrets:
            value = self.get_secret(secret_name)
            
            if value is None:
                validation_results["missing"].append(secret_name)
            elif not value.strip():
                validation_results["empty"].append(secret_name)
            else:
                validation_results["available"].append(secret_name)
                
        return validation_results
        
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of secret management system"""
        validation = self.validate_secrets()
        
        return {
            "secrets_file_exists": self.secrets_file.exists(),
            "metadata_file_exists": self.metadata_file.exists(),
            "total_secrets": len(self._secrets),
            "total_metadata": len(self._metadata),
            "categories": list(set(m.category for m in self._metadata.values())),
            "validation": validation,
            "master_key_set": bool(os.environ.get("BOARDERFRAME_MASTER_KEY")),
            "secrets_directory_secure": oct(self.secrets_dir.stat().st_mode)[-3:] == "700"
        }


# Global secret manager instance
_secret_manager = None


def get_secret_manager() -> SecretManager:
    """Get the global secret manager instance"""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret"""
    return get_secret_manager().get_secret(name, default)


def set_secret(name: str, value: str, category: str = "general", 
               description: str = "", tags: List[str] = None) -> bool:
    """Convenience function to set a secret"""
    return get_secret_manager().set_secret(name, value, category, description, tags)