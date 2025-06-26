"""
Governance Framework for BoarderframeOS
Provides policy enforcement, compliance monitoring, and governance controls
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json
import re
from collections import defaultdict

logger = logging.getLogger(__name__)


class PolicyType(Enum):
    """Types of governance policies"""
    ACCESS_CONTROL = "access_control"
    RESOURCE_LIMITS = "resource_limits"
    DATA_PRIVACY = "data_privacy"
    COST_CONTROL = "cost_control"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    QUALITY = "quality"


class PolicyAction(Enum):
    """Actions that can be taken by policies"""
    ALLOW = "allow"
    DENY = "deny"
    RESTRICT = "restrict"
    ALERT = "alert"
    LOG = "log"
    REVIEW = "review"
    REMEDIATE = "remediate"


class ComplianceStatus(Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    PENDING_REVIEW = "pending_review"
    EXEMPTED = "exempted"


class RiskLevel(Enum):
    """Risk assessment levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    MINIMAL = 5


@dataclass
class Policy:
    """Governance policy definition"""
    id: str
    name: str
    type: PolicyType
    description: str
    rules: List[Dict[str, Any]]
    actions: List[PolicyAction]
    enabled: bool = True
    priority: int = 5  # 1-10, lower is higher priority
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyViolation:
    """Record of a policy violation"""
    id: str
    policy_id: str
    policy_name: str
    entity_type: str  # agent, user, resource, etc.
    entity_id: str
    violation_type: str
    severity: RiskLevel
    description: str
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution: Optional[str] = None


@dataclass
class ComplianceReport:
    """Compliance status report"""
    report_id: str
    timestamp: datetime
    total_policies: int
    active_policies: int
    violations_count: int
    compliance_score: float  # 0-100
    status: ComplianceStatus
    risk_level: RiskLevel
    details: Dict[str, Any]
    recommendations: List[str]


@dataclass
class AuditEvent:
    """Audit trail event"""
    event_id: str
    event_type: str
    entity_type: str
    entity_id: str
    action: str
    actor: str
    result: str
    timestamp: datetime
    metadata: Dict[str, Any]
    risk_score: int  # 0-100


class GovernanceController:
    """
    Central governance controller for BoarderframeOS
    
    Responsibilities:
    - Policy management and enforcement
    - Compliance monitoring
    - Risk assessment
    - Audit trail management
    - Automated remediation
    """
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.violations: List[PolicyViolation] = []
        self.audit_trail: List[AuditEvent] = []
        self.compliance_cache: Dict[str, ComplianceReport] = {}
        self.risk_matrix: Dict[Tuple[str, str], RiskLevel] = {}
        self.enforcement_handlers: Dict[PolicyType, callable] = {}
        self._monitoring_task = None
        
        # Initialize default policies
        self._initialize_default_policies()
    
    async def initialize(self):
        """Async initialization for startup compatibility"""
        logger.info("Initializing Governance Controller")
        
        # Start monitoring if needed
        if not self._monitoring_task:
            self._monitoring_task = asyncio.create_task(self._monitor_compliance())
            
        logger.info(f"Governance Controller initialized with {len(self.policies)} policies")
        return True
    
    async def load_default_policies(self):
        """Load default policies - returns number of policies loaded"""
        # Policies are already loaded in __init__ via _initialize_default_policies
        return len(self.policies)
        
    def _initialize_default_policies(self):
        """Initialize default governance policies"""
        # Access Control Policy
        self.add_policy(Policy(
            id="policy-access-001",
            name="Agent Access Control",
            type=PolicyType.ACCESS_CONTROL,
            description="Controls agent access to system resources",
            rules=[
                {
                    "resource_type": "database",
                    "allowed_agents": ["solomon", "david"],
                    "permissions": ["read", "write"]
                },
                {
                    "resource_type": "financial_data",
                    "allowed_agents": ["david"],
                    "permissions": ["read"]
                }
            ],
            actions=[PolicyAction.DENY, PolicyAction.LOG, PolicyAction.ALERT],
            priority=1
        ))
        
        # Resource Limits Policy
        self.add_policy(Policy(
            id="policy-resource-001",
            name="Resource Usage Limits",
            type=PolicyType.RESOURCE_LIMITS,
            description="Enforces resource usage limits",
            rules=[
                {
                    "resource": "cpu",
                    "max_percent": 80,
                    "action_threshold": 70
                },
                {
                    "resource": "memory",
                    "max_mb": 4096,
                    "action_threshold": 3500
                },
                {
                    "resource": "api_calls",
                    "max_per_minute": 100,
                    "max_per_hour": 5000
                }
            ],
            actions=[PolicyAction.RESTRICT, PolicyAction.ALERT],
            priority=2
        ))
        
        # Data Privacy Policy
        self.add_policy(Policy(
            id="policy-privacy-001",
            name="Data Privacy Protection",
            type=PolicyType.DATA_PRIVACY,
            description="Ensures data privacy compliance",
            rules=[
                {
                    "data_type": "pii",
                    "allowed_operations": ["read_masked", "aggregate"],
                    "forbidden_operations": ["export", "log"]
                },
                {
                    "data_type": "financial",
                    "encryption_required": True,
                    "audit_required": True
                }
            ],
            actions=[PolicyAction.DENY, PolicyAction.LOG, PolicyAction.REMEDIATE],
            priority=1
        ))
        
        # Cost Control Policy
        self.add_policy(Policy(
            id="policy-cost-001",
            name="API Cost Control",
            type=PolicyType.COST_CONTROL,
            description="Controls API usage costs",
            rules=[
                {
                    "service": "openai",
                    "daily_limit_usd": 100,
                    "hourly_limit_usd": 20
                },
                {
                    "service": "anthropic",
                    "daily_limit_usd": 150,
                    "model_restrictions": ["claude-3-opus"]
                }
            ],
            actions=[PolicyAction.RESTRICT, PolicyAction.ALERT],
            priority=3
        ))
        
    def add_policy(self, policy: Policy) -> bool:
        """Add a new governance policy"""
        if policy.id in self.policies:
            logger.warning(f"Policy {policy.id} already exists")
            return False
            
        self.policies[policy.id] = policy
        logger.info(f"Added policy: {policy.name} ({policy.type.value})")
        return True
        
    def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing policy"""
        if policy_id not in self.policies:
            logger.error(f"Policy {policy_id} not found")
            return False
            
        policy = self.policies[policy_id]
        
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
                
        policy.updated_at = datetime.now()
        logger.info(f"Updated policy: {policy.name}")
        return True
        
    def remove_policy(self, policy_id: str) -> bool:
        """Remove a policy"""
        if policy_id in self.policies:
            del self.policies[policy_id]
            logger.info(f"Removed policy: {policy_id}")
            return True
        return False
        
    async def evaluate_action(self, action_context: Dict[str, Any]) -> Tuple[PolicyAction, List[Policy]]:
        """
        Evaluate an action against all policies
        
        Returns:
            Tuple of (action to take, list of applicable policies)
        """
        entity_type = action_context.get("entity_type", "unknown")
        entity_id = action_context.get("entity_id", "unknown")
        action = action_context.get("action", "unknown")
        resource = action_context.get("resource", None)
        
        applicable_policies = []
        final_action = PolicyAction.ALLOW
        
        # Sort policies by priority
        sorted_policies = sorted(
            [p for p in self.policies.values() if p.enabled],
            key=lambda x: x.priority
        )
        
        for policy in sorted_policies:
            if await self._is_policy_applicable(policy, action_context):
                applicable_policies.append(policy)
                
                # Evaluate policy rules
                policy_action = await self._evaluate_policy_rules(policy, action_context)
                
                # Update final action based on priority
                if policy_action in [PolicyAction.DENY, PolicyAction.RESTRICT]:
                    final_action = policy_action
                    break  # Deny/Restrict takes precedence
                elif policy_action == PolicyAction.REVIEW and final_action == PolicyAction.ALLOW:
                    final_action = policy_action
                    
        # Log the evaluation
        await self._log_policy_evaluation(action_context, final_action, applicable_policies)
        
        return final_action, applicable_policies
        
    async def _is_policy_applicable(self, policy: Policy, context: Dict[str, Any]) -> bool:
        """Check if a policy applies to the given context"""
        # Check policy type relevance
        if policy.type == PolicyType.ACCESS_CONTROL:
            return "resource" in context and "entity_id" in context
        elif policy.type == PolicyType.RESOURCE_LIMITS:
            return "resource_usage" in context
        elif policy.type == PolicyType.DATA_PRIVACY:
            return "data_type" in context or "data_classification" in context
        elif policy.type == PolicyType.COST_CONTROL:
            return "service" in context and "cost" in context
        elif policy.type == PolicyType.SECURITY:
            return "security_context" in context
        elif policy.type == PolicyType.COMPLIANCE:
            return "compliance_framework" in context
        elif policy.type == PolicyType.OPERATIONAL:
            return "operation_type" in context
        elif policy.type == PolicyType.QUALITY:
            return "quality_metrics" in context
            
        return False
        
    async def _evaluate_policy_rules(self, policy: Policy, context: Dict[str, Any]) -> PolicyAction:
        """Evaluate policy rules against context"""
        for rule in policy.rules:
            if await self._evaluate_rule(rule, context):
                # Rule matched, determine action
                if PolicyAction.DENY in policy.actions:
                    return PolicyAction.DENY
                elif PolicyAction.RESTRICT in policy.actions:
                    return PolicyAction.RESTRICT
                elif PolicyAction.REVIEW in policy.actions:
                    return PolicyAction.REVIEW
                    
        return PolicyAction.ALLOW
        
    async def _evaluate_rule(self, rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a single rule"""
        # This is a simplified rule engine
        # In production, this would be more sophisticated
        
        # Check resource type rules
        if "resource_type" in rule:
            if context.get("resource", {}).get("type") != rule["resource_type"]:
                return False
                
        # Check allowed agents
        if "allowed_agents" in rule:
            if context.get("entity_id") not in rule["allowed_agents"]:
                return True  # Rule matches (agent not allowed)
                
        # Check resource limits
        if "max_percent" in rule:
            if context.get("resource_usage", {}).get("percent", 0) > rule["max_percent"]:
                return True  # Rule matches (limit exceeded)
                
        # Check data type rules
        if "data_type" in rule:
            if context.get("data_type") == rule["data_type"]:
                # Check forbidden operations
                if "forbidden_operations" in rule:
                    if context.get("operation") in rule["forbidden_operations"]:
                        return True  # Rule matches (forbidden operation)
                        
        return False
        
    async def report_violation(self, policy_id: str, context: Dict[str, Any]) -> PolicyViolation:
        """Report a policy violation"""
        policy = self.policies.get(policy_id)
        if not policy:
            raise ValueError(f"Policy {policy_id} not found")
            
        violation = PolicyViolation(
            id=f"violation-{datetime.now().timestamp()}",
            policy_id=policy_id,
            policy_name=policy.name,
            entity_type=context.get("entity_type", "unknown"),
            entity_id=context.get("entity_id", "unknown"),
            violation_type=context.get("violation_type", "unknown"),
            severity=self._assess_risk_level(policy, context),
            description=context.get("description", "Policy violation detected"),
            context=context
        )
        
        self.violations.append(violation)
        
        # Trigger alerts if necessary
        if violation.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            await self._trigger_violation_alert(violation)
            
        return violation
        
    def _assess_risk_level(self, policy: Policy, context: Dict[str, Any]) -> RiskLevel:
        """Assess risk level of a violation"""
        # Simple risk assessment based on policy priority and context
        if policy.priority <= 2:
            if context.get("impact", "low") == "high":
                return RiskLevel.CRITICAL
            return RiskLevel.HIGH
        elif policy.priority <= 5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
            
    async def _trigger_violation_alert(self, violation: PolicyViolation):
        """Trigger alerts for policy violations"""
        logger.warning(f"POLICY VIOLATION: {violation.policy_name} - {violation.description}")
        
        # In production, this would integrate with alerting systems
        # For now, just log
        alert_data = {
            "violation_id": violation.id,
            "policy": violation.policy_name,
            "severity": violation.severity.name,
            "entity": f"{violation.entity_type}:{violation.entity_id}",
            "timestamp": violation.timestamp.isoformat()
        }
        
        logger.info(f"Alert triggered: {json.dumps(alert_data)}")
        
    async def generate_compliance_report(self) -> ComplianceReport:
        """Generate a compliance report"""
        report_id = f"report-{datetime.now().timestamp()}"
        
        # Calculate compliance metrics
        total_policies = len(self.policies)
        active_policies = sum(1 for p in self.policies.values() if p.enabled)
        
        # Count recent violations (last 24 hours)
        recent_violations = [
            v for v in self.violations
            if datetime.now() - v.timestamp < timedelta(hours=24)
        ]
        
        # Calculate compliance score
        if active_policies > 0:
            violation_rate = len(recent_violations) / (active_policies * 10)  # Normalized
            compliance_score = max(0, min(100, 100 - (violation_rate * 100)))
        else:
            compliance_score = 100
            
        # Determine status and risk
        if compliance_score >= 95:
            status = ComplianceStatus.COMPLIANT
            risk = RiskLevel.MINIMAL
        elif compliance_score >= 80:
            status = ComplianceStatus.WARNING
            risk = RiskLevel.LOW
        else:
            status = ComplianceStatus.NON_COMPLIANT
            risk = RiskLevel.HIGH
            
        # Generate recommendations
        recommendations = self._generate_recommendations(recent_violations, compliance_score)
        
        report = ComplianceReport(
            report_id=report_id,
            timestamp=datetime.now(),
            total_policies=total_policies,
            active_policies=active_policies,
            violations_count=len(recent_violations),
            compliance_score=compliance_score,
            status=status,
            risk_level=risk,
            details={
                "policy_breakdown": self._get_policy_breakdown(),
                "violation_trends": self._get_violation_trends(),
                "risk_areas": self._identify_risk_areas()
            },
            recommendations=recommendations
        )
        
        # Cache the report
        self.compliance_cache[report_id] = report
        
        return report
        
    def _generate_recommendations(self, violations: List[PolicyViolation], score: float) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if score < 80:
            recommendations.append("Immediate action required to address compliance issues")
            
        # Analyze violation patterns
        violation_types = defaultdict(int)
        for v in violations:
            violation_types[v.policy_id] += 1
            
        # Top violated policies
        for policy_id, count in sorted(violation_types.items(), key=lambda x: x[1], reverse=True)[:3]:
            policy = self.policies.get(policy_id)
            if policy:
                recommendations.append(f"Review and strengthen {policy.name} - {count} violations")
                
        if len(violations) > 10:
            recommendations.append("Implement automated compliance monitoring")
            
        return recommendations
        
    def _get_policy_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of policies by type and status"""
        breakdown = {
            "by_type": defaultdict(int),
            "by_status": {"enabled": 0, "disabled": 0},
            "by_priority": defaultdict(int)
        }
        
        for policy in self.policies.values():
            breakdown["by_type"][policy.type.value] += 1
            breakdown["by_status"]["enabled" if policy.enabled else "disabled"] += 1
            breakdown["by_priority"][f"priority_{policy.priority}"] += 1
            
        return dict(breakdown)
        
    def _get_violation_trends(self) -> Dict[str, Any]:
        """Analyze violation trends"""
        trends = {
            "hourly": defaultdict(int),
            "daily": defaultdict(int),
            "by_severity": defaultdict(int)
        }
        
        for violation in self.violations:
            hour_key = violation.timestamp.strftime("%Y-%m-%d %H:00")
            day_key = violation.timestamp.strftime("%Y-%m-%d")
            
            trends["hourly"][hour_key] += 1
            trends["daily"][day_key] += 1
            trends["by_severity"][violation.severity.name] += 1
            
        return dict(trends)
        
    def _identify_risk_areas(self) -> List[Dict[str, Any]]:
        """Identify high-risk areas"""
        risk_areas = []
        
        # Analyze violations by entity
        entity_violations = defaultdict(list)
        for v in self.violations:
            entity_violations[f"{v.entity_type}:{v.entity_id}"].append(v)
            
        # Find entities with multiple violations
        for entity, violations in entity_violations.items():
            if len(violations) > 3:
                risk_areas.append({
                    "entity": entity,
                    "violation_count": len(violations),
                    "risk_level": "high",
                    "policies_violated": list(set(v.policy_name for v in violations))
                })
                
        return risk_areas
        
    async def add_audit_event(self, event_type: str, entity_type: str, 
                            entity_id: str, action: str, actor: str,
                            result: str, metadata: Dict[str, Any] = None):
        """Add an event to the audit trail"""
        event = AuditEvent(
            event_id=f"audit-{datetime.now().timestamp()}",
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            result=result,
            timestamp=datetime.now(),
            metadata=metadata or {},
            risk_score=self._calculate_risk_score(event_type, action, result)
        )
        
        self.audit_trail.append(event)
        
        # Maintain audit trail size
        if len(self.audit_trail) > 10000:
            self.audit_trail = self.audit_trail[-10000:]
            
        return event
        
    def _calculate_risk_score(self, event_type: str, action: str, result: str) -> int:
        """Calculate risk score for an audit event"""
        score = 0
        
        # High-risk event types
        high_risk_types = ["security_breach", "data_export", "privilege_escalation"]
        if event_type in high_risk_types:
            score += 50
            
        # High-risk actions
        high_risk_actions = ["delete", "modify_permissions", "bypass_control"]
        if action in high_risk_actions:
            score += 30
            
        # Failed actions might indicate attempted breaches
        if result == "failed":
            score += 20
            
        return min(100, score)
        
    async def start_monitoring(self):
        """Start governance monitoring"""
        if self._monitoring_task:
            logger.warning("Governance monitoring already running")
            return
            
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Governance monitoring started")
        
    async def stop_monitoring(self):
        """Stop governance monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            logger.info("Governance monitoring stopped")
            
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Generate periodic compliance reports
                if datetime.now().minute == 0:  # Every hour
                    await self.generate_compliance_report()
                    
                # Check for policy violations
                await self._check_active_violations()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in governance monitoring: {e}")
                await asyncio.sleep(60)
                
    async def _check_active_violations(self):
        """Check for and remediate active violations"""
        unresolved = [v for v in self.violations if not v.resolved]
        
        for violation in unresolved:
            # Check if violation can be auto-remediated
            policy = self.policies.get(violation.policy_id)
            if policy and PolicyAction.REMEDIATE in policy.actions:
                await self._attempt_remediation(violation)
                
    async def _attempt_remediation(self, violation: PolicyViolation):
        """Attempt to automatically remediate a violation"""
        logger.info(f"Attempting remediation for violation: {violation.id}")
        
        # Remediation logic would go here
        # For now, just mark some as resolved
        if violation.severity in [RiskLevel.LOW, RiskLevel.MINIMAL]:
            violation.resolved = True
            violation.resolution = "Auto-remediated"
            logger.info(f"Violation {violation.id} auto-remediated")
            
    async def _cleanup_old_data(self):
        """Clean up old audit and violation data"""
        cutoff = datetime.now() - timedelta(days=30)
        
        # Clean old violations
        self.violations = [
            v for v in self.violations
            if v.timestamp > cutoff or not v.resolved
        ]
        
        # Clean old audit events
        self.audit_trail = [
            e for e in self.audit_trail
            if e.timestamp > cutoff
        ]
        
    async def _log_policy_evaluation(self, context: Dict[str, Any], 
                                   action: PolicyAction, 
                                   policies: List[Policy]):
        """Log policy evaluation for audit trail"""
        await self.add_audit_event(
            event_type="policy_evaluation",
            entity_type=context.get("entity_type", "unknown"),
            entity_id=context.get("entity_id", "unknown"),
            action=context.get("action", "unknown"),
            actor="governance_controller",
            result=action.value,
            metadata={
                "policies_evaluated": [p.id for p in policies],
                "context": context
            }
        )
    
    async def _monitor_compliance(self):
        """Monitor compliance in the background"""
        while True:
            try:
                # Generate compliance report periodically
                report = await self.generate_compliance_report()
                
                # Check if compliance score is below threshold
                if report.compliance_score < 70:
                    logger.warning(f"Low compliance score: {report.compliance_score}%")
                    
                # Auto-remediate violations
                await self._check_active_violations()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in compliance monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error


# Global governance controller instance
_governance_controller = None


def get_governance_controller() -> GovernanceController:
    """Get the global governance controller instance"""
    global _governance_controller
    if _governance_controller is None:
        _governance_controller = GovernanceController()
    return _governance_controller