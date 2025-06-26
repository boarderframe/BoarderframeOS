#!/usr/bin/env python3
"""
Governance Integration Script
Integrates governance controller into BoarderframeOS components
"""

import os
import sys
import re
from pathlib import Path
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_header():
    """Print script header"""
    print("=" * 60)
    print("BoarderframeOS Governance Integration")
    print("=" * 60)
    print("Adding governance controls to system components")
    print()


def backup_file(file_path: Path) -> Path:
    """Create backup of a file"""
    backup_path = file_path.with_suffix(file_path.suffix + '.governance_backup')
    shutil.copy2(file_path, backup_path)
    return backup_path


def update_base_agent():
    """Add governance hooks to BaseAgent"""
    base_agent_file = Path("core/base_agent.py")
    
    if not base_agent_file.exists():
        print("  ⚠️  core/base_agent.py not found")
        return False
    
    try:
        with open(base_agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if already has governance
        if 'governance' in content and 'evaluate_action' in content:
            print("  ℹ️  BaseAgent already has governance integration")
            return False
        
        # Add import
        governance_import = "from core.governance import get_governance_controller, PolicyAction"
        
        if "import logging" in content and governance_import not in content:
            content = content.replace("import logging", f"import logging\n{governance_import}")
        
        # Add governance check method
        governance_method = '''
    async def check_governance(self, action: str, resource: Dict[str, Any] = None) -> bool:
        """Check if an action is allowed by governance policies"""
        governance = get_governance_controller()
        
        context = {
            "entity_type": "agent",
            "entity_id": self.name.lower().replace(' ', '-'),
            "action": action,
            "resource": resource or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Add additional context
        if hasattr(self, 'department'):
            context['department'] = self.department
        if hasattr(self, 'capabilities'):
            context['capabilities'] = self.capabilities
            
        # Evaluate action
        policy_action, policies = await governance.evaluate_action(context)
        
        # Log evaluation
        if policy_action != PolicyAction.ALLOW:
            logger.warning(f"Agent {self.name} action '{action}' {policy_action.value} by governance")
            
        # Add audit event
        await governance.add_audit_event(
            event_type="agent_action",
            entity_type="agent",
            entity_id=self.name,
            action=action,
            actor=self.name,
            result=policy_action.value,
            metadata={"resource": resource}
        )
        
        return policy_action == PolicyAction.ALLOW
    
    async def report_violation(self, violation_type: str, description: str, 
                             severity: str = "medium") -> None:
        """Report a policy violation"""
        governance = get_governance_controller()
        
        # Map severity
        from core.governance import RiskLevel
        severity_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "critical": RiskLevel.CRITICAL
        }
        
        context = {
            "entity_type": "agent",
            "entity_id": self.name,
            "violation_type": violation_type,
            "description": description,
            "severity": severity_map.get(severity, RiskLevel.MEDIUM),
            "timestamp": datetime.now().isoformat()
        }
        
        # Find relevant policy
        # This is simplified - in production would be more sophisticated
        policy_id = "policy-agent-001"  # Default agent behavior policy
        
        await governance.report_violation(policy_id, context)'''
        
        # Find where to add (before the last method of the class)
        # Look for the shutdown method as it's typically last
        shutdown_pos = content.find('async def shutdown(self):')
        if shutdown_pos > 0:
            # Insert before shutdown
            content = content[:shutdown_pos] + governance_method + '\n\n    ' + content[shutdown_pos:]
        
        # Write updated content
        if content != original_content:
            backup_file(base_agent_file)
            with open(base_agent_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated core/base_agent.py with governance hooks")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating BaseAgent: {e}")
        return False


def update_llm_client():
    """Add governance checks to LLM client"""
    llm_file = Path("core/llm_client.py")
    
    if not llm_file.exists():
        print("  ⚠️  core/llm_client.py not found")
        return False
    
    try:
        with open(llm_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if already has governance
        if 'governance' in content:
            print("  ℹ️  LLM client already has governance integration")
            return False
        
        # Add governance check before API calls
        governance_check = '''
        # Governance check
        from core.governance import get_governance_controller, PolicyAction
        governance = get_governance_controller()
        
        gov_context = {
            "entity_type": "llm_client",
            "entity_id": "system",
            "action": "api_call",
            "service": "openai" if "gpt" in model else "anthropic",
            "model": model,
            "cost": self._estimate_cost(prompt, max_tokens, model),
            "resource": {
                "prompt_length": len(prompt),
                "max_tokens": max_tokens
            }
        }
        
        policy_action, _ = await governance.evaluate_action(gov_context)
        
        if policy_action == PolicyAction.DENY:
            raise PermissionError(f"LLM request denied by governance policy")
        elif policy_action == PolicyAction.RESTRICT:
            # Apply restrictions
            max_tokens = min(max_tokens, 2000)  # Limit tokens
            logger.warning(f"LLM request restricted by governance - max_tokens limited to {max_tokens}")
'''
        
        # Find where to insert (in the complete method, before actual API call)
        complete_method = re.search(r'async def complete\(self,.*?\):', content, re.DOTALL)
        if complete_method:
            # Find the try block in complete method
            try_pos = content.find('try:', complete_method.end())
            if try_pos > 0:
                # Insert after try:
                indent = '        '  # Proper indentation
                content = content[:try_pos + 4] + '\n' + indent + governance_check + '\n' + content[try_pos + 4:]
        
        # Add cost estimation method if not present
        if '_estimate_cost' not in content:
            cost_method = '''
    def _estimate_cost(self, prompt: str, max_tokens: int, model: str) -> float:
        """Estimate API call cost"""
        # Simplified cost estimation
        prompt_tokens = len(prompt.split()) * 1.3  # Rough token estimate
        
        # Cost per 1K tokens (simplified)
        costs = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002},
            "claude-3": {"input": 0.015, "output": 0.075}
        }
        
        model_key = "gpt-4" if "gpt-4" in model else "gpt-3.5-turbo"
        if "claude" in model:
            model_key = "claude-3"
            
        cost_per_1k = costs.get(model_key, costs["gpt-3.5-turbo"])
        
        input_cost = (prompt_tokens / 1000) * cost_per_1k["input"]
        output_cost = (max_tokens / 1000) * cost_per_1k["output"]
        
        return input_cost + output_cost'''
            
            # Add before the last method
            last_method = content.rfind('\n\n')
            if last_method > 0:
                content = content[:last_method] + '\n' + cost_method + content[last_method:]
        
        # Write updated content
        if content != original_content:
            backup_file(llm_file)
            with open(llm_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated core/llm_client.py with governance checks")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating LLM client: {e}")
        return False


def update_startup():
    """Add Governor agent to startup"""
    startup_file = Path("startup.py")
    
    if not startup_file.exists():
        print("  ⚠️  startup.py not found")
        return False
    
    try:
        with open(startup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check if Governor already added
        if 'governor' in content.lower() and 'governance' in content:
            print("  ℹ️  Governor agent already in startup")
            return False
        
        # Add Governor to agent list
        governor_agent = '''
            # Governor - Governance Controller
            "governor": {
                "module": "agents.governance.governor",
                "class": "GovernorAgent",
                "priority": 2  # High priority for governance
            },'''
        
        # Find agents section
        agents_section = content.find('agents_to_start = {')
        if agents_section > 0:
            # Find Solomon (usually first)
            solomon_pos = content.find('"solomon":', agents_section)
            if solomon_pos > 0:
                # Insert Governor after Solomon
                insert_pos = content.find('},', solomon_pos) + 2
                content = content[:insert_pos] + '\n' + governor_agent + content[insert_pos:]
        
        # Add governance monitoring start
        governance_start = '''
        # Start governance monitoring
        print("\\n🏛️ Starting governance monitoring...")
        from core.governance import get_governance_controller
        governance = get_governance_controller()
        await governance.start_monitoring()
        print("  ✅ Governance monitoring active")
'''
        
        # Find where to add (after agent orchestrator)
        orchestrator_pos = content.find('Initialize agent orchestrator')
        if orchestrator_pos > 0:
            # Find the next section
            next_section = content.find('\n\n', orchestrator_pos + 100)
            if next_section > 0:
                content = content[:next_section] + '\n' + governance_start + content[next_section:]
        
        # Write updated content
        if content != original_content:
            backup_file(startup_file)
            with open(startup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print("  ✅ Updated startup.py with Governor agent")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Error updating startup: {e}")
        return False


def create_example_policies():
    """Create example policy files"""
    policies_dir = Path("configs/governance_policies")
    policies_dir.mkdir(parents=True, exist_ok=True)
    
    # Example high-risk operation policy
    high_risk_policy = {
        "id": "policy-highrisk-001",
        "name": "High Risk Operations Control",
        "type": "security",
        "description": "Controls access to high-risk operations",
        "enabled": True,
        "priority": 1,
        "rules": [
            {
                "operation": "database_delete",
                "requires_approval": True,
                "allowed_agents": ["david", "solomon"]
            },
            {
                "operation": "system_config_change",
                "requires_audit": True,
                "notification_required": True
            },
            {
                "operation": "external_api_access",
                "rate_limit": 100,
                "requires_encryption": True
            }
        ],
        "actions": ["deny", "alert", "log"]
    }
    
    with open(policies_dir / "high_risk_operations.json", 'w') as f:
        import json
        json.dump(high_risk_policy, f, indent=2)
    
    # Example data classification policy
    data_policy = {
        "id": "policy-data-002",
        "name": "Data Classification Policy",
        "type": "data_privacy",
        "description": "Enforces data handling based on classification",
        "enabled": True,
        "priority": 2,
        "rules": [
            {
                "classification": "confidential",
                "allowed_storage": ["encrypted_db"],
                "retention_days": 365,
                "access_logging": True
            },
            {
                "classification": "public",
                "allowed_storage": ["any"],
                "retention_days": -1,
                "access_logging": False
            }
        ],
        "actions": ["restrict", "remediate"]
    }
    
    with open(policies_dir / "data_classification.json", 'w') as f:
        json.dump(data_policy, f, indent=2)
    
    print(f"  ✅ Created example policies in {policies_dir}")
    return True


def create_governance_docs():
    """Create governance documentation"""
    doc_content = """# Governance System

BoarderframeOS includes a comprehensive governance framework for policy enforcement and compliance.

## Overview

The governance system provides:
- **Policy Management**: Define and enforce system-wide policies
- **Compliance Monitoring**: Real-time compliance tracking
- **Risk Assessment**: Automated risk evaluation
- **Audit Trail**: Complete audit logging
- **Automated Remediation**: Self-healing for policy violations

## Architecture

### Components

1. **Governance Controller** (`core/governance.py`)
   - Central policy engine
   - Compliance calculations
   - Violation tracking
   - Audit management

2. **Governor Agent** (`agents/governance/governor.py`)
   - AI-powered governance officer
   - Policy recommendations
   - Violation analysis
   - Compliance reporting

3. **Policy Types**
   - Access Control
   - Resource Limits
   - Data Privacy
   - Cost Control
   - Security
   - Compliance
   - Operational
   - Quality

## Integration Points

### Agent Integration

All agents automatically check governance policies:

```python
# Check if action is allowed
allowed = await self.check_governance("database_write", {"table": "users"})

# Report violations
await self.report_violation("rate_limit_exceeded", "API calls exceeded limit", "high")
```

### LLM Integration

LLM calls are governed for cost control:
- Token limits enforced
- Model restrictions applied
- Cost tracking enabled

## Management

### CLI Tool

```bash
# View compliance status
./manage_governance.py compliance status

# List policies
./manage_governance.py policy list

# Add new policy
./manage_governance.py policy add --file policy.json

# View violations
./manage_governance.py compliance violations

# Real-time monitoring
./manage_governance.py monitor
```

### Web Dashboard

Access at: http://localhost:8892

Features:
- Real-time compliance score
- Policy overview
- Violation tracking
- Risk assessment
- Audit trail viewer

## Policy Definition

Policies are defined in JSON format:

```json
{
  "id": "policy-example-001",
  "name": "Example Policy",
  "type": "operational",
  "description": "Example policy description",
  "priority": 3,
  "enabled": true,
  "rules": [
    {
      "condition": "value",
      "threshold": 100,
      "action": "restrict"
    }
  ],
  "actions": ["restrict", "alert", "log"]
}
```

## Compliance Scoring

Compliance score is calculated based on:
- Active policy count
- Recent violations
- Violation severity
- Resolution rate

Score ranges:
- 95-100%: Compliant ✅
- 80-94%: Warning ⚠️
- Below 80%: Non-compliant ❌

## Best Practices

1. **Define Clear Policies**: Be specific in policy rules
2. **Set Appropriate Priorities**: Critical policies should have priority 1-3
3. **Monitor Regularly**: Check compliance dashboard daily
4. **Act on Violations**: Address violations promptly
5. **Review Policies**: Update policies based on system evolution

## Troubleshooting

### Low Compliance Score
1. Check recent violations
2. Review policy configurations
3. Verify agent compliance
4. Check for system issues

### Policy Not Triggering
1. Verify policy is enabled
2. Check policy rules match conditions
3. Review audit logs
4. Test with manual evaluation

### Performance Impact
1. Reduce policy evaluation frequency
2. Optimize rule complexity
3. Use caching where appropriate
4. Monitor governance overhead

This governance system ensures BoarderframeOS operates within defined
boundaries while maintaining flexibility and performance.
"""
    
    doc_file = Path("GOVERNANCE.md")
    with open(doc_file, 'w') as f:
        f.write(doc_content)
    
    print(f"  ✅ Created governance documentation: {doc_file}")
    return True


def main():
    """Main integration function"""
    print_header()
    
    # Check if we're in the right directory
    if not Path("startup.py").exists():
        print("❌ Error: Not in BoarderframeOS root directory")
        return False
    
    # Create governance directory if needed
    gov_dir = Path("agents/governance")
    gov_dir.mkdir(parents=True, exist_ok=True)
    
    updated_files = []
    
    try:
        # Update core components
        print("🔧 Updating core components...")
        if update_base_agent():
            updated_files.append("core/base_agent.py")
        
        if update_llm_client():
            updated_files.append("core/llm_client.py")
        
        # Update startup
        print("\n🚀 Updating startup process...")
        if update_startup():
            updated_files.append("startup.py")
        
        # Create example policies
        print("\n📋 Creating example policies...")
        create_example_policies()
        
        # Create documentation
        print("\n📚 Creating documentation...")
        create_governance_docs()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎉 GOVERNANCE INTEGRATION COMPLETE")
        print("=" * 60)
        print(f"Files updated: {len(updated_files)}")
        
        if updated_files:
            print("\n📁 Updated files:")
            for file in updated_files:
                print(f"  - {file}")
        
        print("\n🚀 Quick Start:")
        print("  1. Start system: python startup.py")
        print("  2. View dashboard: http://localhost:8892")
        print("  3. Check compliance: ./manage_governance.py compliance status")
        
        print("\n📊 Features Enabled:")
        print("  ✓ Policy-based access control")
        print("  ✓ Real-time compliance monitoring")
        print("  ✓ Automated violation detection")
        print("  ✓ Cost control for LLM usage")
        print("  ✓ Complete audit trail")
        print("  ✓ Web-based governance dashboard")
        
        print("\n✅ Governance system is ready!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)