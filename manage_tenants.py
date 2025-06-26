#!/usr/bin/env python3
"""
Tenant Management CLI for BoarderframeOS
Command-line interface for managing multi-tenant operations
"""

import click
import asyncio
import sys
import os
from pathlib import Path
from tabulate import tabulate
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.multi_tenancy import (
    get_multi_tenancy_manager, 
    TenantType, 
    IsolationLevel,
    TenantContext
)


@click.group()
@click.pass_context
def cli(ctx):
    """BoarderframeOS Tenant Management CLI"""
    ctx.ensure_object(dict)
    

@cli.command()
@click.pass_context
def init(ctx):
    """Initialize multi-tenancy system"""
    async def run():
        click.echo("🏢 Initializing multi-tenancy system...")
        
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        click.echo("✅ Multi-tenancy system initialized")
        click.echo("\nCapabilities enabled:")
        click.echo("  • Row Level Security (RLS) policies")
        click.echo("  • Tenant isolation at database level")
        click.echo("  • Resource quota management")
        click.echo("  • Cross-tenant resource sharing")
        
    asyncio.run(run())


@cli.command()
@click.option('--name', prompt=True, help='Tenant name')
@click.option('--type', type=click.Choice(['enterprise', 'team', 'individual', 'trial']), 
              prompt=True, help='Tenant type')
@click.option('--isolation', type=click.Choice(['strict', 'shared', 'collaborative']), 
              default='strict', help='Isolation level')
@click.option('--max-agents', type=int, default=10, help='Maximum agents allowed')
@click.option('--max-departments', type=int, default=5, help='Maximum departments allowed')
@click.option('--max-storage-gb', type=int, default=100, help='Maximum storage in GB')
@click.option('--max-api-calls', type=int, default=10000, help='Maximum API calls per day')
@click.pass_context
def create(ctx, name, type, isolation, max_agents, max_departments, max_storage_gb, max_api_calls):
    """Create a new tenant"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        click.echo(f"\n🏢 Creating tenant: {name}")
        
        # Set feature flags based on type
        features = {
            "advanced_analytics": type in ['enterprise', 'team'],
            "custom_agents": type == 'enterprise',
            "api_access": True,
            "data_export": type != 'trial',
            "cross_tenant_messaging": isolation == 'collaborative'
        }
        
        tenant = await mt_manager.create_tenant(
            name=name,
            type=TenantType(type),
            isolation_level=IsolationLevel(isolation),
            max_agents=max_agents,
            max_departments=max_departments,
            max_storage_gb=max_storage_gb,
            max_api_calls_per_day=max_api_calls,
            features=features
        )
        
        click.echo(f"\n✅ Tenant created successfully!")
        click.echo(f"\nTenant Details:")
        click.echo(f"  ID: {tenant.id}")
        click.echo(f"  Name: {tenant.name}")
        click.echo(f"  Type: {tenant.type.value}")
        click.echo(f"  Isolation: {tenant.isolation_level.value}")
        click.echo(f"\nResource Limits:")
        click.echo(f"  Max Agents: {tenant.max_agents}")
        click.echo(f"  Max Departments: {tenant.max_departments}")
        click.echo(f"  Max Storage: {tenant.max_storage_gb} GB")
        click.echo(f"  Max API Calls/Day: {tenant.max_api_calls_per_day}")
        click.echo(f"\nFeatures Enabled:")
        for feature, enabled in tenant.features.items():
            status = "✅" if enabled else "❌"
            click.echo(f"  {status} {feature}")
        
    asyncio.run(run())


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def list(ctx, output_format):
    """List all tenants"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        if output_format == 'json':
            tenants_data = []
            for tenant in mt_manager._tenants.values():
                tenants_data.append({
                    "id": tenant.id,
                    "name": tenant.name,
                    "type": tenant.type.value,
                    "isolation_level": tenant.isolation_level.value,
                    "is_active": tenant.is_active,
                    "created_at": tenant.created_at.isoformat()
                })
            click.echo(json.dumps(tenants_data, indent=2))
        else:
            headers = ['ID', 'Name', 'Type', 'Isolation', 'Status', 'Created']
            rows = []
            
            for tenant in mt_manager._tenants.values():
                status = '✅ Active' if tenant.is_active else '❌ Inactive'
                rows.append([
                    tenant.id[:8] + '...',
                    tenant.name,
                    tenant.type.value,
                    tenant.isolation_level.value,
                    status,
                    tenant.created_at.strftime('%Y-%m-%d')
                ])
            
            click.echo("\n🏢 Tenants:")
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
            
    asyncio.run(run())


@cli.command()
@click.argument('tenant_id')
@click.pass_context
def usage(ctx, tenant_id):
    """Show resource usage for a tenant"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        try:
            usage_data = await mt_manager.get_tenant_usage(tenant_id)
            
            click.echo(f"\n📊 Resource Usage for {usage_data['tenant_name']}")
            click.echo("=" * 50)
            
            # Agents
            agents = usage_data['agents']
            click.echo(f"\n👥 Agents: {agents['used']}/{agents['limit']} ({agents['percentage']:.1f}%)")
            progress_bar('Agents', agents['percentage'])
            
            # Departments
            depts = usage_data['departments']
            click.echo(f"\n🏢 Departments: {depts['used']}/{depts['limit']} ({depts['percentage']:.1f}%)")
            progress_bar('Departments', depts['percentage'])
            
            # Storage
            storage = usage_data['storage']
            click.echo(f"\n💾 Storage: {storage['used_gb']:.2f}/{storage['limit_gb']} GB ({storage['percentage']:.1f}%)")
            progress_bar('Storage', storage['percentage'])
            
            # API Calls
            api = usage_data['api_calls']
            click.echo(f"\n📡 API Calls Today: {api['today']}/{api['daily_limit']} ({api['percentage']:.1f}%)")
            progress_bar('API Calls', api['percentage'])
            
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            
    asyncio.run(run())


def progress_bar(label, percentage, width=40):
    """Display a progress bar"""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    color = 'green' if percentage < 80 else 'yellow' if percentage < 95 else 'red'
    click.echo(click.style(f"[{bar}]", fg=color))


@cli.command()
@click.argument('tenant_id')
@click.argument('table')
@click.option('--where', default='1=1', help='WHERE clause for migration')
@click.option('--update-refs/--no-update-refs', default=True, help='Update references')
@click.pass_context
def migrate(ctx, tenant_id, table, where, update_refs):
    """Migrate existing data to a tenant"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        click.echo(f"\n🔄 Migrating data to tenant {tenant_id}")
        click.echo(f"Table: {table}")
        click.echo(f"Condition: {where}")
        
        if click.confirm("Continue with migration?"):
            await mt_manager.migrate_to_tenant(tenant_id, table, where, update_refs)
            click.echo("✅ Migration completed")
        else:
            click.echo("❌ Migration cancelled")
            
    asyncio.run(run())


@cli.command()
@click.argument('tenant_id')
@click.argument('resource_type')
@click.argument('resource_id')
@click.argument('target_tenant_ids', nargs=-1)
@click.pass_context
def share(ctx, tenant_id, resource_type, resource_id, target_tenant_ids):
    """Share a resource with other tenants"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        try:
            await mt_manager.share_resource(
                tenant_id, 
                resource_type, 
                resource_id, 
                list(target_tenant_ids)
            )
            click.echo(f"✅ Resource shared successfully")
            click.echo(f"Resource: {resource_type}/{resource_id}")
            click.echo(f"Shared with: {', '.join(target_tenant_ids)}")
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            
    asyncio.run(run())


@cli.command()
@click.argument('tenant_id')
@click.pass_context
def shared_resources(ctx, tenant_id):
    """Show resources shared with a tenant"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        resources = await mt_manager.get_shared_resources(tenant_id)
        
        if not resources:
            click.echo("No shared resources found")
            return
            
        headers = ['Type', 'Resource ID', 'Owner Tenant', 'Shared On']
        rows = []
        
        for resource in resources:
            rows.append([
                resource['resource_type'],
                resource['resource_id'],
                resource['tenant_id'][:8] + '...',
                resource['created_at'].strftime('%Y-%m-%d')
            ])
            
        click.echo("\n🔗 Shared Resources:")
        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        
    asyncio.run(run())


@cli.command()
@click.argument('tenant_id')
@click.option('--hard/--soft', default=False, help='Hard delete (remove all data) or soft delete')
@click.pass_context
def delete(ctx, tenant_id, hard):
    """Delete a tenant"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        tenant = mt_manager._tenants.get(tenant_id)
        if not tenant:
            click.echo(f"❌ Tenant not found: {tenant_id}", err=True)
            return
            
        click.echo(f"\n⚠️  WARNING: About to delete tenant '{tenant.name}'")
        if hard:
            click.echo("This will PERMANENTLY DELETE all tenant data!")
        else:
            click.echo("This will mark the tenant as inactive (soft delete)")
            
        if click.confirm("Are you sure you want to continue?"):
            await mt_manager.cleanup_tenant(tenant_id, hard_delete=hard)
            click.echo(f"✅ Tenant {'deleted' if hard else 'deactivated'} successfully")
        else:
            click.echo("❌ Deletion cancelled")
            
    asyncio.run(run())


@cli.command()
@click.argument('tenant_id')
@click.argument('user_id')
@click.pass_context
def test_context(ctx, tenant_id, user_id):
    """Test tenant context operations"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        click.echo(f"\n🧪 Testing tenant context for {tenant_id}")
        
        async with mt_manager.with_tenant_context(tenant_id, user_id) as context:
            click.echo(f"\nContext established:")
            click.echo(f"  Tenant ID: {context.tenant_id}")
            click.echo(f"  User ID: {context.user_id}")
            click.echo(f"  Session ID: {context.session_id}")
            click.echo(f"  Request ID: {context.request_id}")
            
            # Test database operations
            async with mt_manager.get_tenant_connection(tenant_id) as conn:
                # Test query
                agent_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM agents WHERE tenant_id = $1",
                    tenant_id
                )
                click.echo(f"\n📊 Test Results:")
                click.echo(f"  Agents in tenant: {agent_count}")
                
                # Test RLS
                click.echo(f"\n🔒 Testing Row Level Security...")
                
                # This should only return tenant's data
                all_agents = await conn.fetchval("SELECT COUNT(*) FROM agents")
                click.echo(f"  Visible agents (with RLS): {all_agents}")
                
                if all_agents == agent_count:
                    click.echo("  ✅ RLS is working correctly - tenant isolation verified")
                else:
                    click.echo("  ❌ RLS issue detected - seeing other tenant data!")
                    
    asyncio.run(run())


@cli.command()
@click.pass_context
def simulate(ctx):
    """Simulate multi-tenant operations"""
    async def run():
        mt_manager = get_multi_tenancy_manager()
        await mt_manager.initialize()
        
        click.echo("\n🎮 Running multi-tenant simulation...")
        
        # Create test tenants
        tenants = []
        for i in range(3):
            tenant = await mt_manager.create_tenant(
                name=f"Test Company {i+1}",
                type=TenantType.TEAM if i < 2 else TenantType.TRIAL,
                isolation_level=IsolationLevel.SHARED if i < 2 else IsolationLevel.STRICT
            )
            tenants.append(tenant)
            click.echo(f"  ✅ Created tenant: {tenant.name}")
            
        # Simulate operations
        click.echo("\n📊 Simulating tenant operations...")
        
        for tenant in tenants:
            async with mt_manager.with_tenant_context(tenant.id):
                # Check usage
                usage = await mt_manager.get_tenant_usage(tenant.id)
                click.echo(f"\n  Tenant: {tenant.name}")
                click.echo(f"    Agents: {usage['agents']['used']}/{usage['agents']['limit']}")
                click.echo(f"    Storage: {usage['storage']['used_gb']:.2f} GB")
                
        # Test resource sharing
        if len(tenants) >= 2:
            click.echo("\n🔗 Testing resource sharing...")
            try:
                await mt_manager.share_resource(
                    tenants[0].id,
                    "agent",
                    "shared-agent-123",
                    [tenants[1].id]
                )
                click.echo(f"  ✅ Shared resource from {tenants[0].name} to {tenants[1].name}")
            except Exception as e:
                click.echo(f"  ❌ Sharing failed: {e}")
                
        click.echo("\n✅ Simulation completed")
        
    asyncio.run(run())


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)