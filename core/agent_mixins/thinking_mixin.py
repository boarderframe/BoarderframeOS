"""
ThinkingMixin - Personality-driven thinking and decision making
Implements agent reasoning based on personality traits and role
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class ThinkingMixin:
    """Personality-driven thinking capabilities"""
    
    def __init__(self):
        """Initialize thinking components"""
        self.thinking_history: List[Dict[str, Any]] = []
        self.decision_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Universal thinking process based on personality and goals"""
        thoughts = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.name,
            "personality_traits": self._get_personality_traits(),
            "current_goals": self._get_current_goals(),
            "context_analysis": await self._analyze_context(context),
            "reasoning_path": await self._generate_reasoning_path(context)
        }
        
        # Store in history
        self._add_to_thinking_history(thoughts)
        
        # Apply personality-specific thinking patterns
        thoughts = await self._apply_personality_thinking(thoughts, context)
        
        # Generate decision recommendations
        thoughts["recommendations"] = await self._generate_recommendations(thoughts, context)
        
        return thoughts
        
    async def _analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze context based on personality traits"""
        analysis = {
            "data_points": len(context),
            "complexity": self._assess_complexity(context),
            "urgency": self._assess_urgency(context),
            "risk_level": self._assess_risk(context)
        }
        
        traits = self._get_personality_traits()
        
        # Trait-specific analysis
        if "analytical" in traits:
            analysis["patterns"] = self._identify_patterns(context)
            analysis["correlations"] = self._find_correlations(context)
            
        if "strategic" in traits:
            analysis["strategic_implications"] = self._analyze_strategic_implications(context)
            analysis["long_term_impact"] = self._assess_long_term_impact(context)
            
        if "creative" in traits:
            analysis["innovation_opportunities"] = self._identify_innovation_opportunities(context)
            analysis["alternative_approaches"] = self._generate_alternatives(context)
            
        if "cautious" in traits:
            analysis["potential_risks"] = self._identify_risks(context)
            analysis["mitigation_strategies"] = self._suggest_mitigations(context)
            
        return analysis
        
    async def _generate_reasoning_path(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate step-by-step reasoning path"""
        reasoning_steps = []
        
        # Step 1: Understand the situation
        reasoning_steps.append({
            "step": 1,
            "action": "understand_situation",
            "details": self._summarize_situation(context)
        })
        
        # Step 2: Identify key factors
        reasoning_steps.append({
            "step": 2,
            "action": "identify_factors",
            "details": self._identify_key_factors(context)
        })
        
        # Step 3: Apply domain knowledge
        reasoning_steps.append({
            "step": 3,
            "action": "apply_knowledge",
            "details": self._apply_domain_knowledge(context)
        })
        
        # Step 4: Consider constraints
        reasoning_steps.append({
            "step": 4,
            "action": "consider_constraints",
            "details": self._identify_constraints(context)
        })
        
        # Step 5: Evaluate options
        reasoning_steps.append({
            "step": 5,
            "action": "evaluate_options",
            "details": await self._evaluate_options(context)
        })
        
        return reasoning_steps
        
    async def _apply_personality_thinking(self, thoughts: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply personality-specific thinking modifications"""
        traits = self._get_personality_traits()
        
        # Decisive personalities make quick judgments
        if "decisive" in traits:
            thoughts["decision_speed"] = "fast"
            thoughts["confidence_level"] = 0.85
            
        # Methodical personalities add more analysis
        elif "methodical" in traits:
            thoughts["decision_speed"] = "measured"
            thoughts["additional_analysis"] = await self._deep_analysis(context)
            
        # Wise personalities consider multiple perspectives
        if "wise" in traits:
            thoughts["perspectives_considered"] = self._gather_perspectives(context)
            thoughts["wisdom_applied"] = self._apply_wisdom(context)
            
        return thoughts
        
    async def _generate_recommendations(self, thoughts: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate action recommendations based on thinking"""
        recommendations = []
        
        # Primary recommendation based on analysis
        primary = {
            "priority": "high",
            "action": self._determine_primary_action(thoughts, context),
            "reasoning": self._explain_recommendation(thoughts),
            "expected_outcome": self._predict_outcome(thoughts, context),
            "confidence": self._calculate_confidence(thoughts)
        }
        recommendations.append(primary)
        
        # Alternative recommendations
        alternatives = self._generate_alternative_recommendations(thoughts, context)
        recommendations.extend(alternatives)
        
        # Risk mitigation recommendations if needed
        if thoughts["context_analysis"].get("risk_level", "low") != "low":
            risk_recommendations = self._generate_risk_mitigations(thoughts, context)
            recommendations.extend(risk_recommendations)
            
        return recommendations
        
    def _get_personality_traits(self) -> List[str]:
        """Get agent's personality traits"""
        if hasattr(self, 'personality') and self.personality:
            return self.personality.get("traits", [])
        return []
        
    def _get_current_goals(self) -> List[str]:
        """Get agent's current goals"""
        if hasattr(self, 'config') and self.config:
            return self.config.goals[:3]  # Top 3 goals
        return []
        
    def _assess_complexity(self, context: Dict[str, Any]) -> str:
        """Assess complexity of the context"""
        data_points = len(context)
        if data_points < 5:
            return "low"
        elif data_points < 15:
            return "moderate"
        else:
            return "high"
            
    def _assess_urgency(self, context: Dict[str, Any]) -> str:
        """Assess urgency of the situation"""
        # Check for urgency indicators
        urgent_keywords = ["urgent", "critical", "immediate", "asap", "emergency"]
        context_str = json.dumps(context).lower()
        
        for keyword in urgent_keywords:
            if keyword in context_str:
                return "high"
                
        if "deadline" in context or "due" in context:
            return "moderate"
            
        return "low"
        
    def _assess_risk(self, context: Dict[str, Any]) -> str:
        """Assess risk level of the context"""
        risk_indicators = ["delete", "remove", "modify", "change", "update", "production"]
        context_str = json.dumps(context).lower()
        
        risk_count = sum(1 for indicator in risk_indicators if indicator in context_str)
        
        if risk_count >= 3:
            return "high"
        elif risk_count >= 1:
            return "moderate"
        else:
            return "low"
            
    def _identify_patterns(self, context: Dict[str, Any]) -> List[str]:
        """Identify patterns in the context"""
        patterns = []
        
        # Look for repeated elements
        if isinstance(context, dict):
            value_types = [type(v).__name__ for v in context.values()]
            if len(set(value_types)) == 1:
                patterns.append(f"Homogeneous data types: {value_types[0]}")
                
        # Look for sequences
        for key, value in context.items():
            if isinstance(value, list) and len(value) > 1:
                patterns.append(f"Sequential data in '{key}' with {len(value)} items")
                
        return patterns
        
    def _find_correlations(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find correlations between context elements"""
        # Simplified correlation finding
        return []
        
    def _analyze_strategic_implications(self, context: Dict[str, Any]) -> List[str]:
        """Analyze strategic implications"""
        implications = []
        
        if "budget" in context:
            implications.append("Financial impact requires assessment")
        if "timeline" in context:
            implications.append("Schedule optimization needed")
        if "resources" in context:
            implications.append("Resource allocation review required")
        if "customer" in context or "client" in context:
            implications.append("Customer experience impact consideration")
            
        return implications
        
    def _assess_long_term_impact(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess long-term impact"""
        return {
            "scalability_impact": "unknown",
            "maintenance_burden": "unknown", 
            "technical_debt": "unknown"
        }
        
    def _identify_innovation_opportunities(self, context: Dict[str, Any]) -> List[str]:
        """Identify opportunities for innovation"""
        opportunities = []
        
        if "problem" in context:
            opportunities.append("Novel solution exploration possible")
        if "inefficiency" in context:
            opportunities.append("Process optimization candidate")
        if "manual" in context:
            opportunities.append("Automation opportunity identified")
        if "repetitive" in context:
            opportunities.append("Pattern automation candidate")
            
        return opportunities
        
    def _generate_alternatives(self, context: Dict[str, Any]) -> List[str]:
        """Generate alternative approaches"""
        return [
            "Traditional approach with proven methods",
            "Innovative approach with new technologies",
            "Hybrid approach combining both"
        ]
        
    def _identify_risks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential risks"""
        risks = []
        
        if self._assess_risk(context) != "low":
            risks.append({
                "type": "operational",
                "description": "Changes may impact system stability",
                "likelihood": "medium"
            })
            
        return risks
        
    def _suggest_mitigations(self, context: Dict[str, Any]) -> List[str]:
        """Suggest risk mitigation strategies"""
        return [
            "Implement changes in staging first",
            "Create rollback plan",
            "Monitor closely after deployment"
        ]
        
    def _summarize_situation(self, context: Dict[str, Any]) -> str:
        """Summarize the current situation"""
        return f"Context contains {len(context)} data points with {self._assess_complexity(context)} complexity"
        
    def _identify_key_factors(self, context: Dict[str, Any]) -> List[str]:
        """Identify key factors in the context"""
        return list(context.keys())[:5]  # Top 5 keys
        
    def _apply_domain_knowledge(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply domain-specific knowledge"""
        return {
            "domain": self.config.department if hasattr(self, 'config') else "general",
            "expertise_applied": True
        }
        
    def _identify_constraints(self, context: Dict[str, Any]) -> List[str]:
        """Identify constraints"""
        constraints = []
        
        if "deadline" in context:
            constraints.append("Time constraint present")
        if "budget" in context:
            constraints.append("Budget constraint present")
        if "resources" in context:
            constraints.append("Resource constraint present")
            
        return constraints
        
    async def _evaluate_options(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate available options"""
        # Simplified option evaluation
        return [
            {"option": "proceed", "score": 0.8},
            {"option": "defer", "score": 0.2}
        ]
        
    async def _deep_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep analysis for methodical personalities"""
        return {
            "analysis_depth": "comprehensive",
            "factors_considered": len(context),
            "confidence": 0.9
        }
        
    def _gather_perspectives(self, context: Dict[str, Any]) -> List[str]:
        """Gather multiple perspectives"""
        return [
            "Technical perspective",
            "Business perspective", 
            "User perspective"
        ]
        
    def _apply_wisdom(self, context: Dict[str, Any]) -> str:
        """Apply wisdom to the situation"""
        return "Consider long-term consequences over short-term gains"
        
    def _determine_primary_action(self, thoughts: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Determine primary action recommendation"""
        if thoughts["context_analysis"]["urgency"] == "high":
            return "immediate_action"
        elif thoughts["context_analysis"]["risk_level"] == "high":
            return "careful_planning"
        else:
            return "standard_procedure"
            
    def _explain_recommendation(self, thoughts: Dict[str, Any]) -> str:
        """Explain the reasoning behind recommendation"""
        return f"Based on {thoughts['context_analysis']['complexity']} complexity and {thoughts['context_analysis']['urgency']} urgency"
        
    def _predict_outcome(self, thoughts: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Predict expected outcome"""
        return "Positive outcome with proper execution"
        
    def _calculate_confidence(self, thoughts: Dict[str, Any]) -> float:
        """Calculate confidence in recommendation"""
        base_confidence = 0.7
        
        # Adjust based on complexity
        if thoughts["context_analysis"]["complexity"] == "low":
            base_confidence += 0.2
        elif thoughts["context_analysis"]["complexity"] == "high":
            base_confidence -= 0.2
            
        return min(max(base_confidence, 0.0), 1.0)
        
    def _generate_alternative_recommendations(self, thoughts: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate alternative recommendations"""
        return []
        
    def _generate_risk_mitigations(self, thoughts: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate risk mitigation recommendations"""
        return []
        
    def _add_to_thinking_history(self, thoughts: Dict[str, Any]) -> None:
        """Add thoughts to history with size limit"""
        self.thinking_history.append(thoughts)
        if len(self.thinking_history) > self.max_history_size:
            self.thinking_history.pop(0)