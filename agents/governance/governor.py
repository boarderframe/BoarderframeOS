"""
Governor Agent - Governance Controller for BoarderframeOS
Responsible for policy enforcement, compliance, and system governance
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from core.base_agent import BaseAgent
from core.governance import (
    get_governance_controller, 
    PolicyType, 
    PolicyAction,
    ComplianceStatus,
    RiskLevel,
    Policy,
    PolicyViolation
)
from core.llm_client import LLMClient
from core.message_bus import MessagePriority

logger = logging.getLogger(__name__)


class GovernorAgent(BaseAgent):
    """
    The Governor - Chief Governance Officer of BoarderframeOS
    
    Named after the biblical concept of governance and order,
    this agent ensures all system operations comply with policies,
    regulations, and best practices.
    
    Responsibilities:
    - Policy creation and management
    - Compliance monitoring and reporting
    - Risk assessment and mitigation
    - Audit trail management
    - Violation detection and remediation
    - Governance dashboard and insights
    """
    
    def __init__(self):
        super().__init__(
            name="Governor",
            description="Chief Governance Officer - Policy enforcement and compliance",
            capabilities=[
                "policy_management",
                "compliance_monitoring", 
                "risk_assessment",
                "audit_management",
                "violation_detection",
                "automated_remediation",
                "governance_reporting"
            ]
        )
        
        self.governance = get_governance_controller()
        self.llm = LLMClient()
        self.monitoring_active = False
        self.compliance_threshold = 85.0  # Minimum acceptable compliance score
        
        # Policy evaluation cache
        self.evaluation_cache: Dict[str, Tuple[PolicyAction, datetime]] = {}
        self.cache_ttl = timedelta(minutes=5)
        
    async def initialize(self) -> bool:
        """Initialize the Governor agent"""
        try:
            logger.info("Initializing Governor agent...")
            
            # Start governance monitoring
            await self.governance.start_monitoring()
            self.monitoring_active = True
            
            # Load any custom policies
            await self._load_custom_policies()
            
            # Generate initial compliance report
            report = await self.governance.generate_compliance_report()
            logger.info(f"Initial compliance score: {report.compliance_score:.1f}%")
            
            self.initialized = True
            logger.info("Governor agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Governor: {e}")
            return False
            
    async def _load_custom_policies(self):
        """Load custom policies from configuration"""
        # Add BoarderframeOS-specific policies
        
        # Agent behavior policy
        self.governance.add_policy(Policy(
            id="policy-agent-001",
            name="Agent Behavior Standards",
            type=PolicyType.OPERATIONAL,
            description="Ensures agents follow operational standards",
            rules=[
                {
                    "metric": "response_time",
                    "max_seconds": 30,
                    "applies_to": "all_agents"
                },
                {
                    "metric": "error_rate", 
                    "max_percent": 5,
                    "applies_to": "all_agents"
                },
                {
                    "metric": "memory_usage",
                    "max_mb": 2048,
                    "applies_to": "all_agents"
                }
            ],
            actions=[PolicyAction.ALERT, PolicyAction.RESTRICT],
            priority=3
        ))
        
        # LLM usage policy
        self.governance.add_policy(Policy(
            id="policy-llm-001",
            name="LLM Usage Governance",
            type=PolicyType.COST_CONTROL,
            description="Governs LLM API usage",
            rules=[
                {
                    "model": "gpt-4",
                    "max_tokens_per_request": 4000,
                    "max_requests_per_hour": 100
                },
                {
                    "model": "claude-3",
                    "max_tokens_per_request": 8000,
                    "max_requests_per_hour": 150
                }
            ],
            actions=[PolicyAction.RESTRICT, PolicyAction.LOG],
            priority=2
        ))
        
        # Data handling policy
        self.governance.add_policy(Policy(
            id="policy-data-001",
            name="Data Handling Standards",
            type=PolicyType.DATA_PRIVACY,
            description="Ensures proper data handling",
            rules=[
                {
                    "data_classification": "sensitive",
                    "required_encryption": True,
                    "retention_days": 90
                },
                {
                    "data_classification": "pii",
                    "anonymization_required": True,
                    "access_logging": True
                }
            ],
            actions=[PolicyAction.DENY, PolicyAction.REMEDIATE],
            priority=1
        ))
        
    async def think(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Governor's thinking process"""
        context = context or {}
        
        thoughts = {
            "timestamp": datetime.now().isoformat(),
            "analysis": {}
        }
        
        # Analyze system compliance
        report = await self.governance.generate_compliance_report()
        thoughts["analysis"]["compliance"] = {
            "score": report.compliance_score,
            "status": report.status.value,
            "risk_level": report.risk_level.name
        }
        
        # Check for critical violations
        recent_violations = [
            v for v in self.governance.violations
            if not v.resolved and v.severity in [RiskLevel.CRITICAL, RiskLevel.HIGH]
        ]
        
        if recent_violations:
            thoughts["analysis"]["critical_violations"] = len(recent_violations)
            thoughts["concerns"] = [
                f"{v.policy_name}: {v.description}" 
                for v in recent_violations[:5]
            ]
            
        # Determine necessary actions
        if report.compliance_score < self.compliance_threshold:
            thoughts["recommended_actions"] = [
                "Investigate compliance issues",
                "Review policy violations", 
                "Implement remediation measures"
            ]
            
        # Risk assessment
        risk_areas = self.governance._identify_risk_areas()
        if risk_areas:
            thoughts["analysis"]["high_risk_entities"] = len(risk_areas)
            
        return thoughts
        
    async def act(self, decision: Dict[str, Any] = None) -> Dict[str, Any]:
        """Governor's action execution"""
        decision = decision or {}
        actions_taken = []
        
        # Generate compliance report
        report = await self.governance.generate_compliance_report()
        
        # Handle non-compliance
        if report.compliance_score < self.compliance_threshold:
            action_result = await self._handle_non_compliance(report)
            actions_taken.append(action_result)
            
        # Process pending policy evaluations
        if "evaluate_request" in decision:
            evaluation_result = await self._evaluate_policy_request(
                decision["evaluate_request"]
            )
            actions_taken.append(evaluation_result)
            
        # Handle critical violations
        critical_violations = [
            v for v in self.governance.violations
            if not v.resolved and v.severity == RiskLevel.CRITICAL
        ]
        
        for violation in critical_violations[:5]:  # Process top 5
            remediation_result = await self._handle_critical_violation(violation)
            actions_taken.append(remediation_result)
            
        # Update governance dashboard
        await self._update_governance_dashboard(report)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": actions_taken,
            "compliance_score": report.compliance_score,
            "violations_processed": len(critical_violations)
        }
        
    async def _handle_non_compliance(self, report) -> Dict[str, Any]:
        """Handle non-compliance situations"""
        logger.warning(f"Non-compliance detected: {report.compliance_score:.1f}%")
        
        # Analyze root causes
        prompt = f"""
        Analyze this compliance report and suggest remediation actions:
        
        Compliance Score: {report.compliance_score}%
        Status: {report.status.value}
        Violations: {report.violations_count}
        Risk Level: {report.risk_level.name}
        
        Policy Breakdown: {report.details.get('policy_breakdown', {})}
        
        Provide specific, actionable recommendations.
        """
        
        analysis = await self.llm.complete(prompt, max_tokens=500)
        
        # Send alert to leadership
        await self.send_message(
            to_agent="david",  # CEO
            content={
                "type": "compliance_alert",
                "severity": "high",
                "score": report.compliance_score,
                "analysis": analysis,
                "report_id": report.report_id
            },
            priority=MessagePriority.HIGH
        )
        
        return {
            "action": "non_compliance_handled",
            "alert_sent": True,
            "analysis_generated": True
        }
        
    async def _evaluate_policy_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a policy request"""
        # Check cache first
        cache_key = f"{request.get('entity_id')}:{request.get('action')}:{request.get('resource')}"
        
        if cache_key in self.evaluation_cache:
            cached_action, cached_time = self.evaluation_cache[cache_key]
            if datetime.now() - cached_time < self.cache_ttl:
                return {
                    "action": "policy_evaluated",
                    "result": cached_action.value,
                    "cached": True
                }
                
        # Evaluate against policies
        action, policies = await self.governance.evaluate_action(request)
        
        # Cache result
        self.evaluation_cache[cache_key] = (action, datetime.now())
        
        # Clean old cache entries
        if len(self.evaluation_cache) > 1000:
            self._clean_evaluation_cache()
            
        return {
            "action": "policy_evaluated",
            "result": action.value,
            "policies_applied": [p.name for p in policies],
            "cached": False
        }
        
    def _clean_evaluation_cache(self):
        """Clean expired cache entries"""
        now = datetime.now()
        self.evaluation_cache = {
            k: v for k, v in self.evaluation_cache.items()
            if now - v[1] < self.cache_ttl
        }
        
    async def _handle_critical_violation(self, violation: PolicyViolation) -> Dict[str, Any]:
        """Handle critical policy violations"""
        logger.error(f"Handling critical violation: {violation.id}")
        
        policy = self.governance.policies.get(violation.policy_id)
        if not policy:
            return {"action": "violation_skipped", "reason": "policy_not_found"}
            
        # Determine remediation action
        if PolicyAction.REMEDIATE in policy.actions:
            # Attempt automated remediation
            if violation.entity_type == "agent":
                # Restrict agent capabilities
                await self.send_message(
                    to_agent=violation.entity_id,
                    content={
                        "type": "capability_restriction",
                        "reason": violation.description,
                        "duration_minutes": 60
                    },
                    priority=MessagePriority.CRITICAL
                )
                
                violation.resolved = True
                violation.resolution = "Agent capabilities restricted"
                
            elif violation.entity_type == "resource":
                # Implement resource restrictions
                # This would integrate with actual resource management
                violation.resolved = True
                violation.resolution = "Resource access restricted"
                
        return {
            "action": "violation_remediated",
            "violation_id": violation.id,
            "resolution": violation.resolution
        }
        
    async def _update_governance_dashboard(self, report):
        """Update governance dashboard with latest data"""
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "compliance_score": report.compliance_score,
            "compliance_status": report.status.value,
            "risk_level": report.risk_level.name,
            "total_policies": report.total_policies,
            "active_policies": report.active_policies,
            "recent_violations": report.violations_count,
            "recommendations": report.recommendations,
            "policy_breakdown": report.details.get("policy_breakdown", {}),
            "violation_trends": report.details.get("violation_trends", {}),
            "high_risk_areas": report.details.get("risk_areas", [])
        }
        
        # Store in state for UI access
        self.state["dashboard"] = dashboard_data
        
        # Notify UI of update
        await self.send_message(
            to_agent="corporate_hq",
            content={
                "type": "dashboard_update",
                "component": "governance",
                "data": dashboard_data
            },
            priority=MessagePriority.LOW
        )
        
    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages"""
        msg_type = message.get("type", "unknown")
        
        if msg_type == "evaluate_action":
            # Policy evaluation request
            result = await self._evaluate_policy_request(message.get("context", {}))
            return {"status": "evaluated", "result": result}
            
        elif msg_type == "report_violation":
            # Violation report
            violation = await self.governance.report_violation(
                policy_id=message.get("policy_id"),
                context=message.get("context", {})
            )
            return {"status": "violation_reported", "violation_id": violation.id}
            
        elif msg_type == "get_compliance_report":
            # Generate compliance report
            report = await self.governance.generate_compliance_report()
            return {
                "status": "report_generated",
                "report": {
                    "id": report.report_id,
                    "score": report.compliance_score,
                    "status": report.status.value,
                    "violations": report.violations_count,
                    "recommendations": report.recommendations
                }
            }
            
        elif msg_type == "add_policy":
            # Add new policy
            policy_data = message.get("policy", {})
            policy = Policy(**policy_data)
            success = self.governance.add_policy(policy)
            return {"status": "policy_added" if success else "policy_exists"}
            
        elif msg_type == "update_policy":
            # Update existing policy
            policy_id = message.get("policy_id")
            updates = message.get("updates", {})
            success = self.governance.update_policy(policy_id, updates)
            return {"status": "policy_updated" if success else "policy_not_found"}
            
        else:
            return {"status": "unknown_message_type", "type": msg_type}
            
    async def handle_user_message(self, message: str, metadata: Dict[str, Any] = None) -> str:
        """Handle user interactions"""
        # Use LLM to understand user intent
        prompt = f"""
        You are the Governor, the Chief Governance Officer of BoarderframeOS.
        
        User message: {message}
        
        Current compliance score: {self.state.get('dashboard', {}).get('compliance_score', 'N/A')}%
        Active policies: {len(self.governance.policies)}
        Recent violations: {len([v for v in self.governance.violations if not v.resolved])}
        
        Respond professionally about governance, compliance, and policy matters.
        """
        
        response = await self.llm.complete(prompt, max_tokens=300)
        
        # Check if user is asking for specific information
        lower_message = message.lower()
        
        if "compliance" in lower_message or "report" in lower_message:
            report = await self.governance.generate_compliance_report()
            response += f"\n\nCurrent Compliance Status:\n"
            response += f"- Score: {report.compliance_score:.1f}%\n"
            response += f"- Status: {report.status.value}\n"
            response += f"- Risk Level: {report.risk_level.name}\n"
            response += f"- Active Violations: {report.violations_count}"
            
        elif "policy" in lower_message or "policies" in lower_message:
            response += f"\n\nActive Policies: {len([p for p in self.governance.policies.values() if p.enabled])}"
            policy_types = {}
            for p in self.governance.policies.values():
                policy_types[p.type.value] = policy_types.get(p.type.value, 0) + 1
            response += f"\nPolicy Types: {dict(policy_types)}"
            
        return response
        
    async def shutdown(self):
        """Shutdown the Governor agent"""
        logger.info("Shutting down Governor agent...")
        
        # Stop monitoring
        if self.monitoring_active:
            await self.governance.stop_monitoring()
            
        # Generate final report
        final_report = await self.governance.generate_compliance_report()
        logger.info(f"Final compliance score: {final_report.compliance_score:.1f}%")
        
        await super().shutdown()


# Agent registration
agent = GovernorAgent()