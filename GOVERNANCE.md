# Governance System

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
