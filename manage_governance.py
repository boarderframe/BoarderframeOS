#!/usr/bin/env python3
"""
Governance Management CLI for BoarderframeOS
Manage policies, view compliance, and control governance
"""

import click
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from tabulate import tabulate

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.governance import (
    get_governance_controller,
    Policy,
    PolicyType,
    PolicyAction,
    ComplianceStatus,
    RiskLevel
)


@click.group()
@click.pass_context
def cli(ctx):
    """BoarderframeOS Governance Management"""
    ctx.ensure_object(dict)
    ctx.obj['governance'] = get_governance_controller()


@cli.group()
@click.pass_context
def policy(ctx):
    """Manage governance policies"""
    pass


@policy.command('list')
@click.option('--type', '-t', help='Filter by policy type')
@click.option('--enabled/--all', default=True, help='Show only enabled policies')
@click.pass_context
def list_policies(ctx, type, enabled):
    """List all policies"""
    governance = ctx.obj['governance']
    
    policies = governance.policies.values()
    
    if type:
        policies = [p for p in policies if p.type.value == type]
    
    if enabled:
        policies = [p for p in policies if p.enabled]
    
    if not policies:
        click.echo("No policies found")
        return
    
    # Format as table
    headers = ['ID', 'Name', 'Type', 'Priority', 'Enabled', 'Actions']
    rows = []
    
    for p in sorted(policies, key=lambda x: x.priority):
        rows.append([
            p.id,
            p.name[:30] + '...' if len(p.name) > 30 else p.name,
            p.type.value,
            p.priority,
            '✓' if p.enabled else '✗',
            ', '.join(a.value for a in p.actions[:2])
        ])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
    click.echo(f"\nTotal policies: {len(policies)}")


@policy.command('show')
@click.argument('policy_id')
@click.pass_context
def show_policy(ctx, policy_id):
    """Show detailed policy information"""
    governance = ctx.obj['governance']
    
    policy = governance.policies.get(policy_id)
    if not policy:
        click.echo(f"Policy {policy_id} not found", err=True)
        return
    
    click.echo(f"\n🔐 Policy Details: {policy.name}")
    click.echo("=" * 60)
    click.echo(f"ID: {policy.id}")
    click.echo(f"Type: {policy.type.value}")
    click.echo(f"Priority: {policy.priority}")
    click.echo(f"Enabled: {'Yes' if policy.enabled else 'No'}")
    click.echo(f"Created: {policy.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Updated: {policy.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"\nDescription:\n{policy.description}")
    
    click.echo(f"\nActions: {', '.join(a.value for a in policy.actions)}")
    
    click.echo("\nRules:")
    for i, rule in enumerate(policy.rules, 1):
        click.echo(f"  {i}. {json.dumps(rule, indent=4)}")


@policy.command('add')
@click.option('--file', '-f', type=click.Path(exists=True), help='Policy definition file (JSON)')
@click.pass_context
def add_policy(ctx, file):
    """Add a new policy from file"""
    if not file:
        click.echo("Please provide a policy file with --file", err=True)
        return
    
    governance = ctx.obj['governance']
    
    try:
        with open(file, 'r') as f:
            policy_data = json.load(f)
        
        # Convert string enums to actual enums
        policy_data['type'] = PolicyType(policy_data['type'])
        policy_data['actions'] = [PolicyAction(a) for a in policy_data['actions']]
        
        policy = Policy(**policy_data)
        
        if governance.add_policy(policy):
            click.echo(f"✅ Policy added: {policy.name}")
        else:
            click.echo(f"❌ Policy already exists: {policy.id}", err=True)
            
    except Exception as e:
        click.echo(f"❌ Error adding policy: {e}", err=True)


@policy.command('update')
@click.argument('policy_id')
@click.option('--enable/--disable', default=None, help='Enable or disable policy')
@click.option('--priority', type=int, help='Update priority (1-10)')
@click.pass_context
def update_policy(ctx, policy_id, enable, priority):
    """Update a policy"""
    governance = ctx.obj['governance']
    
    updates = {}
    
    if enable is not None:
        updates['enabled'] = enable
    
    if priority is not None:
        if 1 <= priority <= 10:
            updates['priority'] = priority
        else:
            click.echo("Priority must be between 1 and 10", err=True)
            return
    
    if not updates:
        click.echo("No updates specified", err=True)
        return
    
    if governance.update_policy(policy_id, updates):
        click.echo(f"✅ Policy updated: {policy_id}")
    else:
        click.echo(f"❌ Policy not found: {policy_id}", err=True)


@policy.command('remove')
@click.argument('policy_id')
@click.confirmation_option(prompt='Are you sure you want to remove this policy?')
@click.pass_context
def remove_policy(ctx, policy_id):
    """Remove a policy"""
    governance = ctx.obj['governance']
    
    if governance.remove_policy(policy_id):
        click.echo(f"✅ Policy removed: {policy_id}")
    else:
        click.echo(f"❌ Policy not found: {policy_id}", err=True)


@cli.group()
@click.pass_context
def compliance(ctx):
    """View compliance status and reports"""
    pass


@compliance.command('status')
@click.pass_context
def compliance_status(ctx):
    """Show current compliance status"""
    governance = ctx.obj['governance']
    
    loop = asyncio.get_event_loop()
    report = loop.run_until_complete(governance.generate_compliance_report())
    
    # Status indicator
    if report.status == ComplianceStatus.COMPLIANT:
        status_icon = "✅"
        status_color = "green"
    elif report.status == ComplianceStatus.WARNING:
        status_icon = "⚠️"
        status_color = "yellow"
    else:
        status_icon = "❌"
        status_color = "red"
    
    click.echo("\n📊 Compliance Status")
    click.echo("=" * 60)
    click.secho(f"{status_icon} Status: {report.status.value}", fg=status_color, bold=True)
    click.echo(f"Score: {report.compliance_score:.1f}%")
    click.echo(f"Risk Level: {report.risk_level.name}")
    click.echo(f"\nActive Policies: {report.active_policies}/{report.total_policies}")
    click.echo(f"Recent Violations: {report.violations_count}")
    
    if report.recommendations:
        click.echo("\n💡 Recommendations:")
        for rec in report.recommendations:
            click.echo(f"  • {rec}")
    
    # Policy breakdown
    breakdown = report.details.get('policy_breakdown', {})
    if breakdown:
        click.echo("\n📋 Policy Breakdown:")
        for key, value in breakdown.items():
            if isinstance(value, dict):
                click.echo(f"  {key}:")
                for k, v in value.items():
                    click.echo(f"    - {k}: {v}")
            else:
                click.echo(f"  {key}: {value}")


@compliance.command('violations')
@click.option('--limit', '-l', default=10, help='Number of violations to show')
@click.option('--unresolved', is_flag=True, help='Show only unresolved violations')
@click.pass_context
def show_violations(ctx, limit, unresolved):
    """Show policy violations"""
    governance = ctx.obj['governance']
    
    violations = governance.violations
    
    if unresolved:
        violations = [v for v in violations if not v.resolved]
    
    # Sort by timestamp (newest first)
    violations = sorted(violations, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    if not violations:
        click.echo("No violations found")
        return
    
    click.echo("\n🚨 Policy Violations")
    click.echo("=" * 60)
    
    for v in violations:
        # Severity color
        if v.severity == RiskLevel.CRITICAL:
            severity_color = "red"
        elif v.severity == RiskLevel.HIGH:
            severity_color = "yellow"
        else:
            severity_color = "white"
        
        click.echo(f"\nViolation ID: {v.id}")
        click.echo(f"Policy: {v.policy_name}")
        click.secho(f"Severity: {v.severity.name}", fg=severity_color, bold=True)
        click.echo(f"Entity: {v.entity_type}:{v.entity_id}")
        click.echo(f"Time: {v.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"Description: {v.description}")
        
        if v.resolved:
            click.echo(f"✅ Resolved: {v.resolution}")
        else:
            click.echo("❌ Unresolved")
        
        click.echo("-" * 60)


@compliance.command('audit')
@click.option('--limit', '-l', default=50, help='Number of audit events to show')
@click.option('--entity', '-e', help='Filter by entity ID')
@click.option('--risk-threshold', '-r', type=int, help='Show only events above risk score')
@click.pass_context
def show_audit(ctx, limit, entity, risk_threshold):
    """Show audit trail"""
    governance = ctx.obj['governance']
    
    events = governance.audit_trail
    
    if entity:
        events = [e for e in events if e.entity_id == entity]
    
    if risk_threshold:
        events = [e for e in events if e.risk_score >= risk_threshold]
    
    # Sort by timestamp (newest first)
    events = sorted(events, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    if not events:
        click.echo("No audit events found")
        return
    
    # Format as table
    headers = ['Time', 'Type', 'Entity', 'Action', 'Actor', 'Result', 'Risk']
    rows = []
    
    for e in events:
        rows.append([
            e.timestamp.strftime('%H:%M:%S'),
            e.event_type[:15],
            f"{e.entity_type}:{e.entity_id}"[:20],
            e.action[:15],
            e.actor[:15],
            e.result,
            e.risk_score
        ])
    
    click.echo("\n📋 Audit Trail")
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.argument('action_file', type=click.Path(exists=True))
@click.pass_context
def evaluate(ctx, action_file):
    """Evaluate an action against policies"""
    governance = ctx.obj['governance']
    
    try:
        with open(action_file, 'r') as f:
            action_context = json.load(f)
        
        loop = asyncio.get_event_loop()
        action, policies = loop.run_until_complete(
            governance.evaluate_action(action_context)
        )
        
        click.echo(f"\n🔍 Policy Evaluation Result")
        click.echo("=" * 60)
        
        # Result color
        if action == PolicyAction.ALLOW:
            result_color = "green"
            icon = "✅"
        elif action == PolicyAction.DENY:
            result_color = "red"
            icon = "❌"
        else:
            result_color = "yellow"
            icon = "⚠️"
        
        click.secho(f"{icon} Action: {action.value}", fg=result_color, bold=True)
        
        if policies:
            click.echo(f"\nApplicable Policies ({len(policies)}):")
            for p in policies:
                click.echo(f"  • {p.name} (Priority: {p.priority})")
        else:
            click.echo("\nNo policies applied")
        
        click.echo(f"\nContext evaluated:")
        click.echo(json.dumps(action_context, indent=2))
        
    except Exception as e:
        click.echo(f"❌ Error evaluating action: {e}", err=True)


@cli.command()
@click.pass_context
def monitor(ctx):
    """Start real-time compliance monitoring"""
    governance = ctx.obj['governance']
    
    click.echo("📊 Starting Real-time Compliance Monitor")
    click.echo("Press Ctrl+C to stop")
    click.echo("=" * 60)
    
    async def monitor_loop():
        while True:
            # Generate report
            report = await governance.generate_compliance_report()
            
            # Clear screen
            click.clear()
            
            # Header
            click.echo(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo("=" * 60)
            
            # Compliance status
            if report.status == ComplianceStatus.COMPLIANT:
                status_color = "green"
            elif report.status == ComplianceStatus.WARNING:
                status_color = "yellow"
            else:
                status_color = "red"
            
            click.secho(f"Compliance Score: {report.compliance_score:.1f}%", 
                       fg=status_color, bold=True)
            click.echo(f"Status: {report.status.value}")
            click.echo(f"Risk Level: {report.risk_level.name}")
            
            # Metrics
            click.echo(f"\nPolicies: {report.active_policies}/{report.total_policies} active")
            click.echo(f"Violations: {report.violations_count} recent")
            
            # Recent violations
            recent = [v for v in governance.violations if not v.resolved][:5]
            if recent:
                click.echo("\n🚨 Recent Violations:")
                for v in recent:
                    click.echo(f"  • {v.policy_name}: {v.description[:50]}...")
            
            # Recommendations
            if report.recommendations:
                click.echo("\n💡 Recommendations:")
                for rec in report.recommendations[:3]:
                    click.echo(f"  • {rec}")
            
            await asyncio.sleep(5)
    
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(monitor_loop())
    except KeyboardInterrupt:
        click.echo("\n\n✅ Monitoring stopped")


@cli.command()
@click.pass_context
def export(ctx):
    """Export governance configuration"""
    governance = ctx.obj['governance']
    
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "policies": {},
        "summary": {
            "total_policies": len(governance.policies),
            "enabled_policies": len([p for p in governance.policies.values() if p.enabled]),
            "total_violations": len(governance.violations),
            "unresolved_violations": len([v for v in governance.violations if not v.resolved])
        }
    }
    
    # Export policies
    for policy_id, policy in governance.policies.items():
        export_data["policies"][policy_id] = {
            "name": policy.name,
            "type": policy.type.value,
            "description": policy.description,
            "enabled": policy.enabled,
            "priority": policy.priority,
            "rules": policy.rules,
            "actions": [a.value for a in policy.actions],
            "created_at": policy.created_at.isoformat(),
            "updated_at": policy.updated_at.isoformat()
        }
    
    # Save to file
    filename = f"governance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    click.echo(f"✅ Governance configuration exported to: {filename}")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)