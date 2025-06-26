#!/usr/bin/env python3
"""
LLM Policy Management CLI for BoarderframeOS
Command-line interface for managing LLM cost optimization policies
"""

import click
import asyncio
import sys
import os
import json
from pathlib import Path
from tabulate import tabulate
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_policy_engine import get_policy_engine, PolicyRule, PolicyAction, ModelTier
from core.llm_cost_optimizer import CostAwareLLMClient


@click.group()
@click.pass_context
def cli(ctx):
    """BoarderframeOS LLM Policy Management CLI"""
    ctx.ensure_object(dict)
    ctx.obj['policy_engine'] = get_policy_engine()
    ctx.obj['llm_client'] = CostAwareLLMClient()


@cli.command()
@click.pass_context
def status(ctx):
    """Show policy engine status"""
    engine = ctx.obj['policy_engine']
    
    click.echo("📊 LLM Policy Engine Status")
    click.echo("=" * 50)
    
    # Budget status
    click.echo("\n💰 Budget Status:")
    click.echo(f"  Daily Budget: ${engine.cost_budget['daily']:.2f}")
    click.echo(f"  Daily Spent: ${engine.current_spend['daily']:.2f}")
    click.echo(f"  Daily Remaining: ${engine.cost_budget['daily'] - engine.current_spend['daily']:.2f}")
    click.echo(f"  Monthly Budget: ${engine.cost_budget['monthly']:.2f}")
    click.echo(f"  Monthly Spent: ${engine.current_spend['monthly']:.2f}")
    
    # Policy summary
    click.echo(f"\n📋 Active Policies: {len(engine.policies)}")
    enabled_policies = sum(1 for p in engine.policies if p.enabled)
    click.echo(f"  Enabled: {enabled_policies}")
    click.echo(f"  Disabled: {len(engine.policies) - enabled_policies}")
    
    # Model inventory
    click.echo(f"\n🤖 Available Models: {len(engine.model_costs)}")
    by_tier = {}
    for model_name, model_cost in engine.model_costs.items():
        tier = model_cost.tier.value
        if tier not in by_tier:
            by_tier[tier] = []
        by_tier[tier].append(model_name)
    
    for tier, models in sorted(by_tier.items()):
        click.echo(f"  {tier.capitalize()}: {len(models)} models")


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def list_policies(ctx, output_format):
    """List all policies"""
    engine = ctx.obj['policy_engine']
    
    if output_format == 'json':
        policies_data = []
        for policy in engine.policies:
            policies_data.append({
                "name": policy.name,
                "description": policy.description,
                "action": policy.action.value,
                "priority": policy.priority,
                "enabled": policy.enabled,
                "parameters": policy.parameters
            })
        click.echo(json.dumps(policies_data, indent=2))
    else:
        headers = ['Name', 'Action', 'Priority', 'Status', 'Description']
        rows = []
        
        for policy in engine.policies:
            status = '✅ Enabled' if policy.enabled else '❌ Disabled'
            rows.append([
                policy.name,
                policy.action.value,
                policy.priority,
                status,
                policy.description[:50] + '...' if len(policy.description) > 50 else policy.description
            ])
        
        click.echo("\n📋 Policy Rules:")
        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def list_models(ctx, output_format):
    """List available models and costs"""
    engine = ctx.obj['policy_engine']
    
    if output_format == 'json':
        models_data = {}
        for model_name, model_cost in engine.model_costs.items():
            models_data[model_name] = {
                "tier": model_cost.tier.value,
                "input_cost_per_1k": model_cost.input_cost_per_1k,
                "output_cost_per_1k": model_cost.output_cost_per_1k,
                "max_context": model_cost.max_context,
                "capabilities": model_cost.capabilities
            }
        click.echo(json.dumps(models_data, indent=2))
    else:
        headers = ['Model', 'Tier', 'Input $/1K', 'Output $/1K', 'Context', 'Capabilities']
        rows = []
        
        for model_name, model_cost in sorted(engine.model_costs.items(), 
                                           key=lambda x: (x[1].tier.value, x[1].input_cost_per_1k)):
            rows.append([
                model_name,
                model_cost.tier.value,
                f"${model_cost.input_cost_per_1k:.4f}",
                f"${model_cost.output_cost_per_1k:.4f}",
                f"{model_cost.max_context:,}",
                ', '.join(model_cost.capabilities[:3])
            ])
        
        click.echo("\n🤖 Available Models:")
        click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.argument('policy_name')
@click.pass_context
def enable_policy(ctx, policy_name):
    """Enable a policy"""
    engine = ctx.obj['policy_engine']
    
    for policy in engine.policies:
        if policy.name == policy_name:
            policy.enabled = True
            click.echo(f"✅ Policy '{policy_name}' enabled")
            return
    
    click.echo(f"❌ Policy '{policy_name}' not found", err=True)
    sys.exit(1)


@cli.command()
@click.argument('policy_name')
@click.pass_context
def disable_policy(ctx, policy_name):
    """Disable a policy"""
    engine = ctx.obj['policy_engine']
    
    for policy in engine.policies:
        if policy.name == policy_name:
            policy.enabled = False
            click.echo(f"✅ Policy '{policy_name}' disabled")
            return
    
    click.echo(f"❌ Policy '{policy_name}' not found", err=True)
    sys.exit(1)


@cli.command()
@click.option('--daily', type=float, help='Daily budget limit')
@click.option('--monthly', type=float, help='Monthly budget limit')
@click.pass_context
def set_budget(ctx, daily, monthly):
    """Set cost budget limits"""
    engine = ctx.obj['policy_engine']
    
    if daily is not None:
        engine.set_budget(daily=daily)
        click.echo(f"✅ Daily budget set to ${daily:.2f}")
    
    if monthly is not None:
        engine.set_budget(monthly=monthly)
        click.echo(f"✅ Monthly budget set to ${monthly:.2f}")
    
    if daily is None and monthly is None:
        click.echo("ℹ️  Current budgets:")
        click.echo(f"  Daily: ${engine.cost_budget['daily']:.2f}")
        click.echo(f"  Monthly: ${engine.cost_budget['monthly']:.2f}")


@cli.command()
@click.option('--agent', help='Show report for specific agent')
@click.option('--format', 'output_format', type=click.Choice(['table', 'json']), default='table')
@click.pass_context
def usage_report(ctx, agent, output_format):
    """Show usage and cost report"""
    engine = ctx.obj['policy_engine']
    llm_client = ctx.obj['llm_client']
    
    report = llm_client.get_cost_report(agent)
    
    if output_format == 'json':
        click.echo(json.dumps(report, indent=2, default=str))
    else:
        if agent:
            # Agent-specific report
            click.echo(f"\n📊 Usage Report for {agent}")
            click.echo("=" * 40)
            click.echo(f"Total Requests: {report['total_requests']}")
            click.echo(f"Total Cost: ${report['total_cost']:.4f}")
            click.echo(f"Average Cost: ${report['average_cost']:.4f}")
            click.echo(f"Total Tokens: {report['total_tokens']:,}")
            click.echo(f"Cache Hit Rate: {report.get('cache_hit_rate', 0):.1%}")
            
            if 'optimization_metrics' in report:
                opt = report['optimization_metrics']
                click.echo("\n🎯 Optimization Metrics:")
                click.echo(f"  Cache Hit Rate: {opt['cache_hit_rate']:.1%}")
                click.echo(f"  Throttled Requests: {opt['throttled_requests']}")
                click.echo(f"  Denied Requests: {opt['denied_requests']}")
                click.echo(f"  Downgraded Requests: {opt['downgraded_requests']}")
        else:
            # Overall report
            click.echo("\n📊 Overall Usage Report")
            click.echo("=" * 40)
            click.echo(f"Total Cost: ${report['total_cost']:.2f}")
            click.echo(f"Total Requests: {report['total_requests']}")
            click.echo(f"Daily Spend: ${report['daily_spend']:.2f}")
            click.echo(f"Monthly Spend: ${report['monthly_spend']:.2f}")
            click.echo(f"Daily Budget Remaining: ${report['daily_budget_remaining']:.2f}")
            
            if report.get('top_spenders'):
                click.echo("\n💸 Top Spenders:")
                headers = ['Agent', 'Cost']
                rows = [[s['agent'], f"${s['cost']:.2f}"] for s in report['top_spenders']]
                click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.argument('prompt')
@click.option('--model', help='Model to test')
@click.option('--agent', default='test', help='Agent name for testing')
@click.pass_context
def test_request(ctx, prompt, model, agent):
    """Test a request through the policy engine"""
    llm_client = ctx.obj['llm_client']
    
    async def run_test():
        click.echo(f"🧪 Testing request from {agent}")
        click.echo(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
        
        if model:
            click.echo(f"Requested Model: {model}")
        
        try:
            result = await llm_client.complete(
                prompt=prompt,
                model=model,
                agent_name=agent
            )
            
            click.echo("\n✅ Request Completed")
            click.echo(f"Original Model: {result.original_model}")
            click.echo(f"Optimized Model: {result.optimized_model}")
            click.echo(f"Original Cost: ${result.original_cost:.4f}")
            click.echo(f"Optimized Cost: ${result.optimized_cost:.4f}")
            click.echo(f"Savings: ${result.savings:.4f} ({(result.savings/result.original_cost*100):.1f}%)")
            
            if result.optimizations_applied:
                click.echo(f"Optimizations: {', '.join(result.optimizations_applied)}")
            
            if result.from_cache:
                click.echo("📦 Response from cache")
            
            click.echo(f"\nResponse: {result.response[:200]}..." if len(result.response) > 200 else f"\nResponse: {result.response}")
            
        except Exception as e:
            click.echo(f"❌ Request failed: {e}", err=True)
    
    asyncio.run(run_test())


@cli.command()
@click.argument('task_type')
@click.argument('max_cost', type=float)
@click.pass_context
def recommend_model(ctx, task_type, max_cost):
    """Get model recommendations for a task within budget"""
    engine = ctx.obj['policy_engine']
    
    recommendations = engine.get_model_recommendations(task_type, max_cost)
    
    if not recommendations:
        click.echo(f"❌ No models found for '{task_type}' within ${max_cost:.4f} budget")
        return
    
    click.echo(f"\n🎯 Model Recommendations for '{task_type}' (max ${max_cost:.4f}):")
    
    headers = ['Model', 'Tier', 'Est. Cost', 'Capabilities']
    rows = []
    
    for rec in recommendations:
        rows.append([
            rec['model'],
            rec['tier'],
            f"${rec['estimated_cost']:.4f}",
            ', '.join(rec['capabilities'][:3])
        ])
    
    click.echo(tabulate(rows, headers=headers, tablefmt='grid'))


@cli.command()
@click.pass_context
def reset_daily(ctx):
    """Reset daily spend counter"""
    engine = ctx.obj['policy_engine']
    
    old_spend = engine.current_spend['daily']
    engine.reset_daily_spend()
    
    click.echo(f"✅ Daily spend reset (was ${old_spend:.2f})")


@cli.command()
@click.pass_context
def reset_monthly(ctx):
    """Reset monthly spend counter"""
    engine = ctx.obj['policy_engine']
    
    old_spend = engine.current_spend['monthly']
    engine.reset_monthly_spend()
    
    click.echo(f"✅ Monthly spend reset (was ${old_spend:.2f})")


@cli.command()
@click.argument('output_file', type=click.Path())
@click.pass_context
def export_policies(ctx, output_file):
    """Export policies to file"""
    engine = ctx.obj['policy_engine']
    
    policies_data = []
    for policy in engine.policies:
        policies_data.append({
            "name": policy.name,
            "description": policy.description,
            "action": policy.action.value,
            "priority": policy.priority,
            "enabled": policy.enabled,
            "parameters": policy.parameters
        })
    
    export_data = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "policies": policies_data,
        "budget": engine.cost_budget,
        "model_count": len(engine.model_costs)
    }
    
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    click.echo(f"✅ Exported {len(policies_data)} policies to {output_file}")


@cli.command()
@click.option('--days', default=7, help='Number of days to simulate')
@click.option('--requests-per-day', default=1000, help='Requests per day')
@click.pass_context
def simulate_costs(ctx, days, requests_per_day):
    """Simulate costs with current policies"""
    engine = ctx.obj['policy_engine']
    
    click.echo(f"🔮 Simulating {days} days with {requests_per_day} requests/day")
    click.echo("=" * 50)
    
    # Simulate different request types
    request_types = [
        ("simple_query", 0.3, 100, 200),
        ("analysis", 0.4, 500, 1000),
        ("generation", 0.2, 1000, 2000),
        ("complex_task", 0.1, 2000, 4000)
    ]
    
    total_original_cost = 0
    total_optimized_cost = 0
    
    for day in range(days):
        daily_original = 0
        daily_optimized = 0
        
        for req_type, probability, avg_input, avg_output in request_types:
            num_requests = int(requests_per_day * probability)
            
            # Calculate costs without optimization
            for model_cost in engine.model_costs.values():
                if model_cost.tier == ModelTier.PREMIUM:
                    original_cost = model_cost.calculate_cost(avg_input, avg_output) * num_requests
                    daily_original += original_cost
                    break
            
            # Estimate with optimizations
            # Assume 30% cache hits, 20% downgrades, 10% compressions
            cache_hits = num_requests * 0.3
            downgrades = num_requests * 0.2
            compressions = num_requests * 0.1
            
            # Cached requests cost nothing
            optimized_requests = num_requests - cache_hits
            
            # Downgraded requests use standard tier
            for model_cost in engine.model_costs.values():
                if model_cost.tier == ModelTier.STANDARD:
                    downgrade_cost = model_cost.calculate_cost(avg_input, avg_output) * downgrades
                    daily_optimized += downgrade_cost
                    break
            
            # Compressed requests use less tokens
            compressed_input = int(avg_input * 0.6)
            for model_cost in engine.model_costs.values():
                if model_cost.tier == ModelTier.PREMIUM:
                    compression_cost = model_cost.calculate_cost(compressed_input, avg_output) * compressions
                    daily_optimized += compression_cost
                    
                    # Regular requests
                    regular = optimized_requests - downgrades - compressions
                    regular_cost = model_cost.calculate_cost(avg_input, avg_output) * regular
                    daily_optimized += regular_cost
                    break
        
        total_original_cost += daily_original
        total_optimized_cost += daily_optimized
        
        click.echo(f"Day {day+1}: Original ${daily_original:.2f} → Optimized ${daily_optimized:.2f} (Saved ${daily_original-daily_optimized:.2f})")
    
    savings = total_original_cost - total_optimized_cost
    savings_percent = (savings / total_original_cost * 100) if total_original_cost > 0 else 0
    
    click.echo("\n📊 Simulation Results:")
    click.echo(f"Total Original Cost: ${total_original_cost:.2f}")
    click.echo(f"Total Optimized Cost: ${total_optimized_cost:.2f}")
    click.echo(f"Total Savings: ${savings:.2f} ({savings_percent:.1f}%)")
    click.echo(f"Average Daily Cost: ${total_optimized_cost/days:.2f}")
    click.echo(f"Projected Monthly Cost: ${total_optimized_cost/days*30:.2f}")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n❌ Cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)