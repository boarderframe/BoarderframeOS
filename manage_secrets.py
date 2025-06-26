#!/usr/bin/env python3
"""
Secrets Management CLI for BoarderframeOS
Command-line interface for managing secrets securely
"""

import click
import sys
import os
import json
from pathlib import Path
from tabulate import tabulate
import getpass

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.secret_manager import SecretManager, get_secret_manager


@click.group()
@click.option('--secrets-file', default='secrets/secrets.enc', help='Path to secrets file')
@click.option('--master-key', help='Master key for encryption (or set BOARDERFRAME_MASTER_KEY env var)')
@click.pass_context
def cli(ctx, secrets_file, master_key):
    """BoarderframeOS Secrets Management CLI"""
    ctx.ensure_object(dict)
    
    # Initialize secret manager
    if master_key:
        ctx.obj['secret_manager'] = SecretManager(secrets_file, master_key)
    else:
        ctx.obj['secret_manager'] = SecretManager(secrets_file)


@cli.command()
@click.pass_context
def status(ctx):
    """Show secrets management status"""
    sm = ctx.obj['secret_manager']
    health = sm.get_health_status()
    
    click.echo("🔐 Secrets Management Status")
    click.echo("=" * 40)
    
    # File status
    click.echo(f"Secrets file: {'✅' if health['secrets_file_exists'] else '❌'} {sm.secrets_file}")
    click.echo(f"Metadata file: {'✅' if health['metadata_file_exists'] else '❌'} {sm.metadata_file}")
    click.echo(f"Directory secure: {'✅' if health['secrets_directory_secure'] else '❌'}")
    click.echo(f"Master key set: {'✅' if health['master_key_set'] else '❌'}")
    
    # Statistics
    click.echo(f"\nStatistics:")
    click.echo(f"  Total secrets: {health['total_secrets']}")
    click.echo(f"  Categories: {', '.join(health['categories']) if health['categories'] else 'None'}")
    
    # Validation
    validation = health['validation']
    click.echo(f"\nValidation:")
    click.echo(f"  Available: {len(validation['available'])}")
    click.echo(f"  Missing: {len(validation['missing'])}")
    click.echo(f"  Empty: {len(validation['empty'])}")
    
    if validation['missing']:
        click.echo(f"  Missing secrets: {', '.join(validation['missing'])}")
    if validation['empty']:
        click.echo(f"  Empty secrets: {', '.join(validation['empty'])}")


@cli.command()
@click.option('--category', help='Filter by category')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.pass_context
def list(ctx, category, output_format):
    """List all secrets (metadata only)"""
    sm = ctx.obj['secret_manager']
    secrets = sm.list_secrets(category)
    
    if output_format == 'json':
        click.echo(json.dumps(secrets, indent=2))
        return
    
    if not secrets:
        click.echo("No secrets found")
        return
        
    # Prepare table data
    headers = ['Name', 'Category', 'Description', 'Last Accessed', 'Access Count', 'In Env']
    rows = []
    
    for secret in secrets:
        rows.append([
            secret['name'],
            secret['category'],
            secret['description'][:50] + '...' if len(secret['description']) > 50 else secret['description'],
            secret['last_accessed'][:19] if secret['last_accessed'] else 'Never',
            secret['access_count'],
            '✅' if secret['exists_in_env'] else '❌'
        ])
    
    click.echo(f"\n📋 Secrets List ({len(secrets)} total)")
    if category:
        click.echo(f"Category: {category}")
    click.echo()
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.argument('name')
@click.pass_context
def get(ctx, name):
    """Get a secret value"""
    sm = ctx.obj['secret_manager']
    value = sm.get_secret(name)
    
    if value is None:
        click.echo(f"❌ Secret '{name}' not found", err=True)
        sys.exit(1)
    else:
        click.echo(value)


@cli.command()
@click.argument('name')
@click.option('--value', help='Secret value (will prompt if not provided)')
@click.option('--category', default='general', help='Secret category')
@click.option('--description', default='', help='Secret description')
@click.option('--tags', help='Comma-separated tags')
@click.pass_context
def set(ctx, name, value, category, description, tags):
    """Set a secret value"""
    sm = ctx.obj['secret_manager']
    
    # Get value if not provided
    if not value:
        value = getpass.getpass(f"Enter value for '{name}': ")
        if not value:
            click.echo("❌ Empty value provided", err=True)
            sys.exit(1)
    
    # Parse tags
    tag_list = [tag.strip() for tag in tags.split(',')] if tags else []
    
    # Set the secret
    success = sm.set_secret(name, value, category, description, tag_list)
    
    if success:
        click.echo(f"✅ Secret '{name}' set successfully")
    else:
        click.echo(f"❌ Failed to set secret '{name}'", err=True)
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
@click.pass_context
def delete(ctx, name, confirm):
    """Delete a secret"""
    sm = ctx.obj['secret_manager']
    
    # Check if secret exists
    if sm.get_secret(name) is None:
        click.echo(f"❌ Secret '{name}' not found", err=True)
        sys.exit(1)
    
    # Confirmation
    if not confirm:
        if not click.confirm(f"Are you sure you want to delete secret '{name}'?"):
            click.echo("❌ Cancelled")
            return
    
    # Delete the secret
    success = sm.delete_secret(name)
    
    if success:
        click.echo(f"✅ Secret '{name}' deleted successfully")
    else:
        click.echo(f"❌ Failed to delete secret '{name}'", err=True)
        sys.exit(1)


@cli.command()
@click.argument('name')
@click.option('--value', help='New secret value (will prompt if not provided)')
@click.pass_context
def rotate(ctx, name, value):
    """Rotate a secret (keeps backup)"""
    sm = ctx.obj['secret_manager']
    
    # Check if secret exists
    if sm.get_secret(name) is None:
        click.echo(f"❌ Secret '{name}' not found", err=True)
        sys.exit(1)
    
    # Get new value if not provided
    if not value:
        value = getpass.getpass(f"Enter new value for '{name}': ")
        if not value:
            click.echo("❌ Empty value provided", err=True)
            sys.exit(1)
    
    # Rotate the secret
    success = sm.rotate_secret(name, value)
    
    if success:
        click.echo(f"✅ Secret '{name}' rotated successfully (backup created)")
    else:
        click.echo(f"❌ Failed to rotate secret '{name}'", err=True)
        sys.exit(1)


@cli.command()
@click.option('--prefix', default='', help='Import only variables with this prefix')
@click.pass_context
def import_env(ctx, prefix):
    """Import secrets from environment variables"""
    sm = ctx.obj['secret_manager']
    
    count = sm.import_from_env(prefix)
    
    if count > 0:
        click.echo(f"✅ Imported {count} secrets from environment")
    else:
        click.echo("ℹ️  No new secrets imported")


@cli.command()
@click.argument('file_path')
@click.option('--category', help='Export only secrets from this category')
@click.pass_context
def export_env(ctx, file_path, category):
    """Export secrets to .env file"""
    sm = ctx.obj['secret_manager']
    
    success = sm.export_to_env_file(file_path, category)
    
    if success:
        click.echo(f"✅ Secrets exported to {file_path}")
    else:
        click.echo(f"❌ Failed to export secrets", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def validate(ctx):
    """Validate required secrets"""
    sm = ctx.obj['secret_manager']
    validation = sm.validate_secrets()
    
    click.echo("🔍 Secret Validation")
    click.echo("=" * 30)
    
    if validation['available']:
        click.echo(f"✅ Available ({len(validation['available'])}):")
        for secret in validation['available']:
            click.echo(f"   - {secret}")
    
    if validation['missing']:
        click.echo(f"\n❌ Missing ({len(validation['missing'])}):")
        for secret in validation['missing']:
            click.echo(f"   - {secret}")
    
    if validation['empty']:
        click.echo(f"\n⚠️  Empty ({len(validation['empty'])}):")
        for secret in validation['empty']:
            click.echo(f"   - {secret}")
    
    # Overall status
    total_required = len(validation['available']) + len(validation['missing']) + len(validation['empty'])
    if validation['missing'] or validation['empty']:
        click.echo(f"\n❌ Validation failed: {len(validation['available'])}/{total_required} secrets are properly configured")
        sys.exit(1)
    else:
        click.echo(f"\n✅ All {total_required} required secrets are available")


@cli.command()
@click.pass_context
def init(ctx):
    """Initialize secrets management system"""
    sm = ctx.obj['secret_manager']
    
    click.echo("🚀 Initializing BoarderframeOS Secrets Management")
    click.echo("=" * 50)
    
    # Create secrets directory
    sm.secrets_dir.mkdir(mode=0o700, exist_ok=True)
    click.echo(f"✅ Created secrets directory: {sm.secrets_dir}")
    
    # Import common secrets from environment
    click.echo("\n📥 Importing secrets from environment...")
    count = sm.import_from_env()
    click.echo(f"✅ Imported {count} secrets")
    
    # Set up common secrets if they don't exist
    common_secrets = [
        ("ANTHROPIC_API_KEY", "api_keys", "Claude/Anthropic API key for AI agents"),
        ("POSTGRES_PASSWORD", "database", "PostgreSQL database password"),
        ("REDIS_PASSWORD", "infrastructure", "Redis cache password"),
        ("JWT_SECRET", "authentication", "JWT token signing secret")
    ]
    
    click.echo("\n🔑 Setting up common secrets...")
    for name, category, description in common_secrets:
        if sm.get_secret(name) is None:
            click.echo(f"\nSecret '{name}' not found.")
            if click.confirm(f"Would you like to set '{name}' now?"):
                value = getpass.getpass(f"Enter value for '{name}': ")
                if value:
                    sm.set_secret(name, value, category, description)
                    click.echo(f"✅ Set '{name}'")
    
    # Show status
    click.echo("\n📊 Final Status:")
    health = sm.get_health_status()
    click.echo(f"Total secrets: {health['total_secrets']}")
    click.echo(f"Categories: {', '.join(health['categories']) if health['categories'] else 'None'}")
    
    click.echo("\n✅ Secrets management initialized successfully!")
    click.echo("\nNext steps:")
    click.echo("1. Set BOARDERFRAME_MASTER_KEY environment variable for better security")
    click.echo("2. Run 'python manage_secrets.py validate' to check required secrets")
    click.echo("3. Use 'python manage_secrets.py set <name>' to add more secrets")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)