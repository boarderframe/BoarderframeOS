# Secret Management System

BoarderframeOS includes a comprehensive secret management system for secure handling of API keys, database credentials, and other sensitive configuration data.

## Overview

The secret management system provides:

- **Encrypted Storage**: All secrets are encrypted at rest using Fernet symmetric encryption
- **Environment Fallback**: Automatic fallback to environment variables
- **Category Organization**: Secrets are organized by category (database, api_keys, etc.)
- **Access Logging**: Track when secrets are accessed for audit purposes
- **Secret Rotation**: Built-in support for secret rotation with backup retention
- **Validation**: Validate that required secrets are properly configured

## Quick Start

### 1. Initialize Secret Management

```bash
# Initialize the secret management system
python manage_secrets.py init

# Check system status
python manage_secrets.py status

# Validate required secrets
python manage_secrets.py validate
```

### 2. Set Master Key (Recommended)

For enhanced security, set a master encryption key:

```bash
export BOARDERFRAME_MASTER_KEY="your-secure-master-key-here"
```

### 3. Add Secrets

```bash
# Set a secret (will prompt for value)
python manage_secrets.py set ANTHROPIC_API_KEY --category api_keys --description "Claude API key"

# Set with value directly (less secure)
python manage_secrets.py set JWT_SECRET --value "your-secret-here" --category authentication
```

### 4. Integration

The system automatically integrates with existing code. Use the integration script:

```bash
# Update existing code to use secret manager
python integrate_secret_management.py
```

## Command Reference

### Status and Health

```bash
# Show overall status
python manage_secrets.py status

# Quick health check
python check_secrets_health.py

# Validate required secrets
python manage_secrets.py validate
```

### Managing Secrets

```bash
# List all secrets (metadata only)
python manage_secrets.py list

# List secrets by category
python manage_secrets.py list --category api_keys

# Get a secret value
python manage_secrets.py get ANTHROPIC_API_KEY

# Set a new secret
python manage_secrets.py set SECRET_NAME --category general --description "Description"

# Delete a secret
python manage_secrets.py delete SECRET_NAME --confirm

# Rotate a secret (keeps backup)
python manage_secrets.py rotate SECRET_NAME
```

### Import/Export

```bash
# Import from environment variables
python manage_secrets.py import-env

# Import with prefix filter
python manage_secrets.py import-env --prefix BOARDERFRAME_

# Export to .env file
python manage_secrets.py export-env .env.production

# Export specific category
python manage_secrets.py export-env .env.api --category api_keys
```

## Programmatic Usage

### Basic Usage

```python
from core.secret_manager import get_secret

# Get a secret with fallback to environment variable
api_key = get_secret("ANTHROPIC_API_KEY")

# Get with default value
db_password = get_secret("DB_PASSWORD", "default_password")
```

### Advanced Usage

```python
from core.secret_manager import get_secret_manager

# Get the secret manager instance
sm = get_secret_manager()

# Set a secret programmatically
sm.set_secret(
    name="NEW_SECRET",
    value="secret_value",
    category="api_keys",
    description="New API key",
    tags=["production", "external"]
)

# Get all secrets in a category
db_secrets = sm.get_category_secrets("database")

# List secrets with metadata
secrets = sm.list_secrets(category="api_keys")
```

## Secret Categories

The system organizes secrets into predefined categories:

- **`database`**: Database credentials (POSTGRES_PASSWORD, DB_PASSWORD, etc.)
- **`api_keys`**: External API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
- **`infrastructure`**: Infrastructure secrets (REDIS_PASSWORD, DOCKER_PASSWORD)
- **`authentication`**: Auth-related secrets (JWT_SECRET, SESSION_SECRET)
- **`external_services`**: Third-party service credentials (STRIPE_API_KEY, GITHUB_TOKEN)

## Required Secrets

The following secrets are considered required for full system operation:

### Essential
- `ANTHROPIC_API_KEY`: Claude/Anthropic API key for AI agents
- `POSTGRES_PASSWORD`: PostgreSQL database password

### Optional but Recommended
- `REDIS_PASSWORD`: Redis cache password
- `JWT_SECRET`: JWT token signing secret
- `OPENAI_API_KEY`: OpenAI API key for additional AI capabilities

## Security Best Practices

### 1. Master Key Management

- Set `BOARDERFRAME_MASTER_KEY` environment variable
- Use a strong, unique key (minimum 32 characters)
- Never commit the master key to version control
- Consider using a key management service in production

### 2. File Permissions

The system automatically sets secure permissions:

- Secrets directory: `700` (owner only)
- Secret files: `600` (owner read/write only)
- Master key file: `600` (owner read/write only)

### 3. Environment Variables

- Use environment variables for CI/CD and containerized deployments
- Never log or print secret values
- Use secret rotation for long-running services

### 4. Backup and Recovery

- Regular backups of encrypted secret files
- Document secret rotation procedures
- Test recovery procedures regularly

## File Structure

```
secrets/
├── secrets.enc          # Encrypted secrets storage
├── metadata.json        # Secret metadata (NOT encrypted)
└── .master.key          # Generated master key (if no env var set)

.env.template            # Template for manual configuration
```

## Integration with Existing Code

The integration script automatically updates existing code to use the secret manager:

### Before
```python
import os
api_key = os.environ.get("ANTHROPIC_API_KEY")
db_password = os.getenv("POSTGRES_PASSWORD", "default")
```

### After
```python
from core.secret_manager import get_secret
api_key = get_secret("ANTHROPIC_API_KEY")
db_password = get_secret("POSTGRES_PASSWORD", "default")
```

## Troubleshooting

### Common Issues

**Secret not found**
```bash
# Check if secret exists
python manage_secrets.py list | grep SECRET_NAME

# Import from environment if available
python manage_secrets.py import-env
```

**Permission errors**
```bash
# Check directory permissions
ls -la secrets/

# Fix permissions
chmod 700 secrets/
chmod 600 secrets/*
```

**Encryption errors**
```bash
# Check master key
echo $BOARDERFRAME_MASTER_KEY

# Regenerate master key (WARNING: will lose existing secrets)
rm secrets/.master.key
python manage_secrets.py init
```

### Health Check

Run the health check script to diagnose issues:

```bash
python check_secrets_health.py
```

This will check:
- Secret manager initialization
- File permissions
- Required secrets availability
- Access functionality

## Migration from Environment Variables

If you're currently using environment variables, migration is straightforward:

1. **Import existing variables:**
   ```bash
   python manage_secrets.py import-env
   ```

2. **Run integration script:**
   ```bash
   python integrate_secret_management.py
   ```

3. **Validate setup:**
   ```bash
   python manage_secrets.py validate
   ```

4. **Test system functionality:**
   ```bash
   python check_secrets_health.py
   ```

## Production Deployment

### Container Deployment

Mount secrets directory as a volume:

```yaml
services:
  boarderframe:
    volumes:
      - ./secrets:/app/secrets:ro
    environment:
      - BOARDERFRAME_MASTER_KEY=${MASTER_KEY}
```

### Kubernetes Deployment

Use Kubernetes secrets for the master key:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: boarderframe-master-key
data:
  master-key: <base64-encoded-key>
```

### CI/CD Integration

```bash
# In CI/CD pipeline
export BOARDERFRAME_MASTER_KEY="$CI_MASTER_KEY"
python manage_secrets.py validate
```

## API Reference

### SecretManager Class

```python
class SecretManager:
    def set_secret(name: str, value: str, category: str = "general", 
                   description: str = "", tags: List[str] = None) -> bool
    
    def get_secret(name: str, default: Optional[str] = None) -> Optional[str]
    
    def delete_secret(name: str) -> bool
    
    def list_secrets(category: Optional[str] = None) -> List[Dict[str, Any]]
    
    def rotate_secret(name: str, new_value: str) -> bool
    
    def import_from_env(prefix: str = "") -> int
    
    def export_to_env_file(file_path: str, category: Optional[str] = None) -> bool
    
    def validate_secrets() -> Dict[str, List[str]]
    
    def get_health_status() -> Dict[str, Any]
```

### Convenience Functions

```python
def get_secret(name: str, default: Optional[str] = None) -> Optional[str]
def set_secret(name: str, value: str, category: str = "general", 
               description: str = "", tags: List[str] = None) -> bool
```

## Support and Updates

- Check system status: `python manage_secrets.py status`
- Validate configuration: `python manage_secrets.py validate`
- Health check: `python check_secrets_health.py`
- Get help: `python manage_secrets.py --help`

For additional support, check the BoarderframeOS documentation or raise an issue in the project repository.