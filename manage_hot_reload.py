#!/usr/bin/env python3
"""
Hot Reload Management CLI for BoarderframeOS
Command-line interface for managing blue-green hot reloading
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

from core.hot_reload import get_hot_reload_manager
from core.hot_reload_config import get_config_manager
from core.agent_hot_reload import AgentReloadHandler
from core.agent_orchestrator import get_orchestrator


@click.group()
@click.pass_context
def cli(ctx):
    """BoarderframeOS Hot Reload Management CLI"""
    ctx.ensure_object(dict)
    

@cli.command()
@click.pass_context
def status(ctx):
    """Show hot reload system status"""
    click.echo("🔄 Hot Reload System Status")
    click.echo("=" * 50)
    
    # Get managers
    hot_reload = get_hot_reload_manager()
    config_manager = get_config_manager()
    
    # Module reload status
    metrics = hot_reload.get_metrics()
    
    click.echo("\n📊 Module Reload Status:")
    click.echo(f"  Current State: {metrics['current_state']}")
    click.echo(f"  Total Reloads: {metrics['total_reloads']}")
    click.echo(f"  Successful: {metrics['successful_reloads']}")
    click.echo(f"  Failed: {metrics['failed_reloads']}")
    click.echo(f"  Average Time: {metrics['average_reload_time']}")
    click.echo(f"  Tracked Modules: {metrics['tracked_modules']}")
    
    # Config reload status  
    config_status = config_manager.get_status()
    
    click.echo("\n📋 Config Reload Status:")
    click.echo(f"  Watched Files: {config_status['watched_files']}")
    click.echo(f"  Loaded Configs: {len(config_status['loaded_configs'])}")
    
    if config_status['loaded_configs']:
        click.echo("  Config Files:")
        for config_file in config_status['loaded_configs']:
            version_info = config_status['config_versions'].get(config_file, {})
            click.echo(f"    - {config_file} (v{version_info.get('version', 'unknown')})")


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def list_modules(ctx, output_format):
    """List tracked modules"""
    hot_reload = get_hot_reload_manager()
    
    modules = []
    for module_name, version in hot_reload.module_versions.items():
        modules.append({
            'Module': module_name,
            'Version': version.version,
            'File': version.file_path,
            'Last Modified': datetime.fromtimestamp(version.last_modified).strftime('%Y-%m-%d %H:%M:%S'),
            'Loaded': version.loaded_at.strftime('%Y-%m-%d %H:%M:%S') if version.loaded_at else 'Not loaded',
            'Errors': version.error_count
        })
    
    if output_format == 'json':
        click.echo(json.dumps(modules, indent=2, default=str))
    else:
        if modules:
            headers = ['Module', 'Version', 'Last Modified', 'Loaded', 'Errors']
            rows = [[m['Module'], m['Version'], m['Last Modified'], m['Loaded'], m['Errors']] for m in modules]
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            click.echo("No modules tracked")


@cli.command()
@click.argument('module_name')
@click.option('--force', is_flag=True, help='Force reload even if no changes detected')
@click.pass_context
def reload_module(ctx, module_name, force):
    """Reload a specific module"""
    async def do_reload():
        hot_reload = get_hot_reload_manager()
        
        # Check if module is tracked
        if module_name not in hot_reload.module_versions and not force:
            click.echo(f"❌ Module '{module_name}' not tracked", err=True)
            return False
        
        click.echo(f"🔄 Reloading module: {module_name}")
        
        # Start hot reload manager if not running
        if not hot_reload._watch_task:
            await hot_reload.start()
        
        # Force reload
        success = await hot_reload.force_reload(module_name)
        
        if success:
            click.echo(f"✅ Module '{module_name}' reloaded successfully")
        else:
            click.echo(f"❌ Failed to reload module '{module_name}'", err=True)
        
        return success
    
    success = asyncio.run(do_reload())
    sys.exit(0 if success else 1)


@cli.command()
@click.argument('agent_name')
@click.pass_context
def reload_agent(ctx, agent_name):
    """Reload a specific agent"""
    async def do_reload():
        orchestrator = get_orchestrator()
        agent_handler = AgentReloadHandler(orchestrator)
        
        click.echo(f"🤖 Reloading agent: {agent_name}")
        
        try:
            await agent_handler._reload_single_agent(agent_name)
            click.echo(f"✅ Agent '{agent_name}' reloaded successfully")
            return True
        except Exception as e:
            click.echo(f"❌ Failed to reload agent '{agent_name}': {e}", err=True)
            return False
    
    success = asyncio.run(do_reload())
    sys.exit(0 if success else 1)


@cli.command()
@click.argument('config_file')
@click.pass_context
def reload_config(ctx, config_file):
    """Reload a configuration file"""
    async def do_reload():
        config_manager = get_config_manager()
        
        # Start config manager if not running
        if not config_manager._observer:
            await config_manager.start()
        
        click.echo(f"📋 Reloading config: {config_file}")
        
        success = await config_manager.reload_config(config_file)
        
        if success:
            click.echo(f"✅ Config '{config_file}' reloaded successfully")
            
            # Show new version
            version = config_manager.get_version(config_file)
            if version:
                click.echo(f"  Version: {version.version}")
                click.echo(f"  Applied: {version.applied_at}")
        else:
            click.echo(f"❌ Failed to reload config '{config_file}'", err=True)
        
        return success
    
    success = asyncio.run(do_reload())
    sys.exit(0 if success else 1)


@cli.command()
@click.option('--agents', is_flag=True, help='Watch agent modules')
@click.option('--core', is_flag=True, help='Watch core modules')
@click.option('--mcp', is_flag=True, help='Watch MCP modules')
@click.option('--configs', is_flag=True, help='Watch config files')
@click.option('--all', 'watch_all', is_flag=True, help='Watch everything')
@click.pass_context
def watch(ctx, agents, core, mcp, configs, watch_all):
    """Start watching for changes"""
    async def do_watch():
        hot_reload = get_hot_reload_manager()
        config_manager = get_config_manager()
        
        # Configure watch paths
        if watch_all:
            agents = core = mcp = configs = True
        
        watch_paths = []
        if agents:
            watch_paths.append("agents/")
        if core:
            watch_paths.append("core/")
        if mcp:
            watch_paths.append("mcp/")
        
        if watch_paths:
            hot_reload.watch_paths = watch_paths
            
        click.echo("👁️  Starting hot reload watchers...")
        
        # Start module watcher
        if watch_paths:
            await hot_reload.start()
            click.echo(f"  Watching modules in: {', '.join(watch_paths)}")
        
        # Start config watcher
        if configs or watch_all:
            await config_manager.start()
            click.echo("  Watching config files")
        
        click.echo("\n✅ Hot reload system active. Press Ctrl+C to stop.")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            click.echo("\n🛑 Stopping watchers...")
            
            if watch_paths:
                await hot_reload.stop()
            if configs or watch_all:
                await config_manager.stop()
                
            click.echo("✅ Watchers stopped")
    
    asyncio.run(do_watch())


@cli.command()
@click.pass_context
def test(ctx):
    """Test hot reload functionality"""
    click.echo("🧪 Testing Hot Reload System")
    click.echo("=" * 50)
    
    async def run_tests():
        results = []
        
        # Test 1: Module tracking
        try:
            hot_reload = get_hot_reload_manager()
            hot_reload._scan_modules()
            module_count = len(hot_reload.module_versions)
            results.append(("Module Tracking", module_count > 0, f"{module_count} modules tracked"))
        except Exception as e:
            results.append(("Module Tracking", False, str(e)))
        
        # Test 2: Config loading
        try:
            config_manager = get_config_manager()
            await config_manager._load_initial_configs()
            config_count = len(config_manager.configs)
            results.append(("Config Loading", config_count > 0, f"{config_count} configs loaded"))
        except Exception as e:
            results.append(("Config Loading", False, str(e)))
        
        # Test 3: Blue-green state
        try:
            state = hot_reload.current_state.value
            results.append(("Blue-Green State", True, f"Current: {state}"))
        except Exception as e:
            results.append(("Blue-Green State", False, str(e)))
        
        return results
    
    results = asyncio.run(run_tests())
    
    # Display results
    headers = ['Test', 'Result', 'Details']
    rows = []
    
    for test_name, passed, details in results:
        result = '✅ Pass' if passed else '❌ Fail'
        rows.append([test_name, result, details])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    
    # Summary
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    
    click.echo(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        click.echo("✅ All tests passed!")
    else:
        click.echo("❌ Some tests failed")
        sys.exit(1)


@cli.command()
@click.argument('module_name')
@click.pass_context
def module_info(ctx, module_name):
    """Show detailed info about a module"""
    hot_reload = get_hot_reload_manager()
    
    version = hot_reload.get_module_version(module_name)
    
    if not version:
        click.echo(f"❌ Module '{module_name}' not found", err=True)
        sys.exit(1)
    
    click.echo(f"📦 Module Information: {module_name}")
    click.echo("=" * 50)
    click.echo(f"File Path: {version.file_path}")
    click.echo(f"Version: {version.version}")
    click.echo(f"Checksum: {version.checksum}")
    click.echo(f"Last Modified: {datetime.fromtimestamp(version.last_modified)}")
    click.echo(f"Loaded At: {version.loaded_at or 'Not loaded'}")
    click.echo(f"Instance Count: {version.instance_count}")
    click.echo(f"Error Count: {version.error_count}")
    
    if version.last_error:
        click.echo(f"Last Error: {version.last_error}")
    
    # Check current deployment
    module = hot_reload.get_module(module_name)
    if module:
        click.echo(f"\n🟢 Module is loaded in {hot_reload.current_state.value} environment")
    else:
        click.echo(f"\n⚪ Module is not currently loaded")


@cli.command()
@click.option('--output', type=click.Path(), help='Save metrics to file')
@click.pass_context  
def metrics(ctx, output):
    """Show hot reload metrics"""
    hot_reload = get_hot_reload_manager()
    metrics = hot_reload.get_metrics()
    
    click.echo("📊 Hot Reload Metrics")
    click.echo("=" * 40)
    
    # Format metrics
    formatted = {
        "Deployment State": metrics['current_state'],
        "Total Reloads": metrics['total_reloads'],
        "Successful": metrics['successful_reloads'],
        "Failed": metrics['failed_reloads'],
        "Success Rate": f"{(metrics['successful_reloads'] / metrics['total_reloads'] * 100):.1f}%" if metrics['total_reloads'] > 0 else "N/A",
        "Avg Reload Time": metrics['average_reload_time'],
        "Last Reload": metrics['last_reload_time'] or "Never",
        "Tracked Modules": metrics['tracked_modules'],
        "Blue Modules": metrics['blue_modules'],
        "Green Modules": metrics['green_modules']
    }
    
    # Display as table
    rows = [[k, v] for k, v in formatted.items()]
    click.echo(tabulate(rows, headers=['Metric', 'Value'], tablefmt='grid'))
    
    # Save to file if requested
    if output:
        with open(output, 'w') as f:
            json.dump(metrics, f, indent=2)
        click.echo(f"\n✅ Metrics saved to: {output}")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)