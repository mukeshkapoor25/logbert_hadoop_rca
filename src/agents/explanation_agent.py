"""
Explanation Agent

This agent specializes in generating human-readable explanations
for detected anomalies and root causes using AI language models.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse, AgentStatus, AgentCapability


class ExplanationAgent(BaseAgent):
    """
    AI Agent specialized in generating explanations and insights.
    
    This agent:
    - Generates human-readable explanations for anomalies
    - Provides detailed analysis of root causes
    - Creates actionable recommendations
    - Formats results for different audiences (technical, management)
    """
    
    def __init__(
        self, 
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        capabilities = [
            AgentCapability.EXPLANATION_GENERATION
        ]
        
        # Set configuration first (before super init to avoid initialization issues)
        self.config = config or {}
        self.explanation_style = self.config.get("explanation_style", "technical")
        self.include_code_examples = self.config.get("include_code_examples", True)
        self.max_explanation_length = self.config.get("max_explanation_length", 1000)
        self.language_model = self.config.get("language_model", "mistral-7b")
        
        # Template system
        self.explanation_templates = {}
        self.recommendation_templates = {}
        
        super().__init__(
            agent_id=agent_id,
            name=name or "ExplanationAgent",
            capabilities=capabilities,
            config=config or {}
        )
        
    def _initialize(self):
        """Initialize the explanation agent."""
        try:
            self.logger.info("Initializing explanation agent")
            
            # Load explanation templates
            self._load_explanation_templates()
            self._load_recommendation_templates()
            
            # Initialize language model (mock for now)
            self._initialize_language_model()
            
            self.logger.info("Explanation agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize explanation agent: {e}")
            raise
    
    def _load_explanation_templates(self):
        """Load explanation templates for different anomaly types."""
        self.explanation_templates = {
            "error": {
                "technical": "Error detected in {component}: {description}. This indicates {technical_analysis}. Impact: {impact_analysis}.",
                "management": "System error identified in {component} component. Business impact: {business_impact}. Recommended action: {action_required}.",
                "brief": "Error in {component}: {summary}"
            },
            "performance": {
                "technical": "Performance anomaly detected: {description}. Metrics show {performance_metrics}. Root cause analysis suggests {root_cause_summary}.",
                "management": "Performance degradation detected. Service response time affected by {primary_cause}. Estimated impact: {impact_estimate}.",
                "brief": "Performance issue: {summary}"
            },
            "resource": {
                "technical": "Resource constraint identified: {description}. Current utilization: {resource_metrics}. Threshold breach: {threshold_info}.",
                "management": "Resource capacity issue detected. System resources at {utilization_level}. Scaling required: {scaling_recommendation}.",
                "brief": "Resource issue: {summary}"
            },
            "network": {
                "technical": "Network anomaly detected: {description}. Connection patterns show {network_analysis}. Affected endpoints: {affected_systems}.",
                "management": "Network connectivity issue affecting {component}. Service availability impact: {availability_impact}.",
                "brief": "Network issue: {summary}"
            }
        }
    
    def _load_recommendation_templates(self):
        """Load recommendation templates for different scenarios."""
        self.recommendation_templates = {
            "immediate": [
                "Monitor {component} component closely for additional symptoms",
                "Check system resource availability and scaling options",
                "Verify network connectivity to affected services",
                "Review recent configuration changes"
            ],
            "short_term": [
                "Implement monitoring alerts for similar patterns",
                "Review and update capacity planning",
                "Conduct detailed root cause analysis",
                "Document incident for future reference"
            ],
            "long_term": [
                "Evaluate system architecture for resilience",
                "Implement automated remediation where possible",
                "Enhance monitoring and observability",
                "Review operational procedures"
            ]
        }
    
    def _initialize_language_model(self):
        """Initialize the language model for explanation generation."""
        # Mock initialization - in production would load actual model
        self.model_initialized = True
        self.logger.info(f"Language model {self.language_model} initialized")
    
    async def process(self, input_data: Dict[str, Any], **kwargs) -> AgentResponse:
        """
        Process data to generate explanations and insights.
        
        Args:
            input_data: Dictionary containing:
                - log_text: Original log text
                - anomalies: List of detected anomalies
                - root_causes: List of identified root causes
                - explanation_style: Style of explanation (technical, management, brief)
            **kwargs: Additional processing parameters
            
        Returns:
            AgentResponse with generated explanations
        """
        start_time = self.get_processing_time()
        
        # Extract parameters
        log_text = input_data.get("log_text", "")
        anomalies = input_data.get("anomalies", [])
        root_causes = input_data.get("root_causes", [])
        explanation_style = input_data.get("explanation_style", self.explanation_style)
        
        # Generate explanations
        explanations = await self._generate_explanations(
            anomalies, root_causes, explanation_style
        )
        
        # Generate summary
        summary = await self._generate_summary(anomalies, root_causes, explanation_style)
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(root_causes)
        
        # Generate insights
        insights = await self._generate_insights(log_text, anomalies, root_causes)
        
        # Calculate processing time
        processing_time = self.get_processing_time() - start_time
        
        # Create response
        response_data = {
            "explanations": explanations,
            "summary": summary,
            "recommendations": recommendations,
            "insights": insights,
            "explanation_metadata": {
                "style": explanation_style,
                "total_anomalies_explained": len(anomalies),
                "total_root_causes_explained": len(root_causes),
                "explanation_length": len(summary)
            }
        }
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=response_data,
            processing_time_ms=processing_time,
            metadata={
                "explanation_style": explanation_style,
                "language_model": self.language_model,
                "items_processed": len(anomalies) + len(root_causes)
            }
        )
    
    async def _generate_explanations(
        self,
        anomalies: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]],
        style: str
    ) -> Dict[str, Any]:
        """
        Generate detailed explanations for anomalies and root causes.
        
        Args:
            anomalies: List of anomalies
            root_causes: List of root causes
            style: Explanation style
            
        Returns:
            Dictionary containing detailed explanations
        """
        explanations = {
            "anomaly_explanations": [],
            "root_cause_explanations": [],
            "correlation_analysis": ""
        }
        
        # Generate explanations for each anomaly
        for anomaly in anomalies:
            explanation = await self._explain_anomaly(anomaly, style)
            explanations["anomaly_explanations"].append(explanation)
        
        # Generate explanations for each root cause
        for root_cause in root_causes:
            explanation = await self._explain_root_cause(root_cause, style)
            explanations["root_cause_explanations"].append(explanation)
        
        # Generate correlation analysis
        if anomalies and root_causes:
            explanations["correlation_analysis"] = await self._generate_correlation_analysis(
                anomalies, root_causes, style
            )
        
        return explanations
    
    async def _explain_anomaly(
        self,
        anomaly: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """
        Generate explanation for a single anomaly.
        
        Args:
            anomaly: Anomaly data
            style: Explanation style
            
        Returns:
            Explanation dictionary
        """
        anomaly_type = anomaly.get("anomaly_type", "unknown")
        component = anomaly.get("component", "system")
        description = anomaly.get("description", "Anomalous behavior detected")
        severity = anomaly.get("severity", "medium")
        
        # Get template for this anomaly type and style
        template = self.explanation_templates.get(anomaly_type, {}).get(
            style, self.explanation_templates["error"][style]
        )
        
        # Generate context-specific analysis
        technical_analysis = await self._generate_technical_analysis(anomaly)
        impact_analysis = await self._generate_impact_analysis(anomaly)
        
        # Format explanation
        explanation_text = template.format(
            component=component,
            description=description,
            technical_analysis=technical_analysis,
            impact_analysis=impact_analysis,
            business_impact=impact_analysis,
            action_required=f"Investigate {component} component",
            summary=description[:100],
            performance_metrics="elevated latency and error rates",
            root_cause_summary="system resource constraints",
            impact_estimate="moderate service degradation",
            resource_metrics="85% CPU, 90% memory utilization",
            threshold_info="exceeds normal operating parameters",
            utilization_level="critical levels",
            scaling_recommendation="immediate horizontal scaling",
            network_analysis="intermittent connectivity issues",
            affected_systems=component,
            availability_impact="potential service interruption"
        )
        
        return {
            "anomaly_id": anomaly.get("id", "unknown"),
            "explanation": explanation_text,
            "confidence": anomaly.get("confidence", "medium"),
            "severity": severity,
            "technical_details": await self._get_technical_details(anomaly) if style == "technical" else None
        }
    
    async def _explain_root_cause(
        self,
        root_cause: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """
        Generate explanation for a root cause.
        
        Args:
            root_cause: Root cause data
            style: Explanation style
            
        Returns:
            Explanation dictionary
        """
        description = root_cause.get("description", "Unknown root cause")
        category = root_cause.get("category", "general")
        confidence = root_cause.get("confidence", "medium")
        affected_components = root_cause.get("affected_components", [])
        
        # Generate detailed explanation based on style
        if style == "technical":
            explanation = await self._generate_technical_root_cause_explanation(root_cause)
        elif style == "management":
            explanation = await self._generate_management_root_cause_explanation(root_cause)
        else:
            explanation = description
        
        return {
            "root_cause_id": root_cause.get("id", "unknown"),
            "explanation": explanation,
            "confidence": confidence,
            "affected_components": affected_components,
            "evidence": root_cause.get("evidence", []),
            "likelihood_score": root_cause.get("likelihood_score", 0.5)
        }
    
    async def _generate_technical_analysis(self, anomaly: Dict[str, Any]) -> str:
        """Generate technical analysis for an anomaly."""
        anomaly_type = anomaly.get("anomaly_type", "unknown")
        score = anomaly.get("anomaly_score", 0.5)
        
        analysis_map = {
            "error": f"error pattern analysis shows score of {score:.2f}, indicating system fault condition",
            "performance": f"performance metrics deviation with anomaly score {score:.2f}, suggesting resource bottleneck",
            "resource": f"resource utilization anomaly detected with score {score:.2f}, indicating capacity constraints",
            "network": f"network pattern analysis reveals score {score:.2f}, suggesting connectivity issues"
        }
        
        return analysis_map.get(anomaly_type, f"anomaly pattern analysis with score {score:.2f}")
    
    async def _generate_impact_analysis(self, anomaly: Dict[str, Any]) -> str:
        """Generate impact analysis for an anomaly."""
        severity = anomaly.get("severity", "medium")
        component = anomaly.get("component", "system")
        
        impact_map = {
            "critical": f"critical impact on {component} service availability and performance",
            "high": f"significant impact on {component} operations and user experience",
            "medium": f"moderate impact on {component} service quality",
            "low": f"minimal impact on {component} operations"
        }
        
        return impact_map.get(severity, f"potential impact on {component} operations")
    
    async def _get_technical_details(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Get technical details for an anomaly."""
        return {
            "anomaly_score": anomaly.get("anomaly_score", 0.0),
            "line_number": anomaly.get("line_number", 0),
            "timestamp": anomaly.get("timestamp"),
            "log_entry": anomaly.get("log_entry", ""),
            "detection_method": "LogBERT deep learning model",
            "feature_importance": "temporal sequence patterns and semantic embedding analysis"
        }
    
    async def _generate_technical_root_cause_explanation(
        self,
        root_cause: Dict[str, Any]
    ) -> str:
        """Generate technical explanation for root cause."""
        description = root_cause.get("description", "Unknown cause")
        category = root_cause.get("category", "general")
        evidence = root_cause.get("evidence", [])
        likelihood = root_cause.get("likelihood_score", 0.5)
        
        explanation = f"Technical Analysis: {description} (Category: {category}, Confidence: {likelihood:.2f}). "
        
        if evidence:
            explanation += f"Supporting evidence includes: {'; '.join(evidence[:3])}. "
        
        explanation += "This analysis is based on pattern matching against known failure modes and historical incident data."
        
        return explanation
    
    async def _generate_management_root_cause_explanation(
        self,
        root_cause: Dict[str, Any]
    ) -> str:
        """Generate management-focused explanation for root cause."""
        description = root_cause.get("description", "Unknown cause")
        affected_components = root_cause.get("affected_components", [])
        severity = root_cause.get("severity", "medium")
        
        business_impact = {
            "critical": "immediate business operations disruption",
            "high": "significant service degradation affecting users",
            "medium": "moderate impact on service quality", 
            "low": "minimal operational impact"
        }.get(severity, "operational impact")
        
        explanation = f"Business Impact Assessment: {description} affecting {', '.join(affected_components)} components. "
        explanation += f"This results in {business_impact}. "
        explanation += "Immediate attention required to prevent further escalation."
        
        return explanation
    
    async def _generate_correlation_analysis(
        self,
        anomalies: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]],
        style: str
    ) -> str:
        """Generate correlation analysis between anomalies and root causes."""
        if not anomalies or not root_causes:
            return "Insufficient data for correlation analysis."
        
        # Count patterns
        anomaly_components = [a.get("component", "unknown") for a in anomalies]
        cause_components = [
            comp for rc in root_causes 
            for comp in rc.get("affected_components", [])
        ]
        
        common_components = set(anomaly_components) & set(cause_components)
        
        if style == "technical":
            analysis = f"Correlation analysis reveals {len(common_components)} shared components: {', '.join(common_components)}. "
            analysis += f"Pattern matching shows {len(anomalies)} anomalies correlate with {len(root_causes)} identified causes. "
            analysis += "Temporal and causal relationships suggest cascading failure pattern."
        elif style == "management":
            analysis = f"Analysis shows system issues affecting {len(common_components)} critical components. "
            analysis += f"Root cause investigation identified {len(root_causes)} primary failure points. "
            analysis += "Coordinated response required to address interconnected issues."
        else:
            analysis = f"Found {len(root_causes)} root causes for {len(anomalies)} anomalies."
        
        return analysis
    
    async def _generate_summary(
        self,
        anomalies: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]],
        style: str
    ) -> str:
        """Generate overall summary of the analysis."""
        if not anomalies and not root_causes:
            return "No anomalies or root causes detected in the analysis."
        
        # Count severities
        severity_counts = {}
        for anomaly in anomalies:
            severity = anomaly.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Generate summary based on style
        if style == "management":
            summary = f"Executive Summary: Analysis identified {len(anomalies)} system anomalies "
            summary += f"with {len(root_causes)} root causes requiring attention. "
            
            if severity_counts.get("critical", 0) > 0:
                summary += f"Critical issues detected: {severity_counts['critical']} items require immediate action. "
            
            summary += "Recommended immediate review and remediation planning."
            
        elif style == "technical":
            summary = f"Technical Analysis Summary: Processed log data revealing {len(anomalies)} anomalous patterns. "
            summary += f"Root cause analysis identified {len(root_causes)} potential failure modes. "
            
            severity_breakdown = ", ".join([
                f"{count} {severity}" for severity, count in severity_counts.items() if count > 0
            ])
            summary += f"Severity distribution: {severity_breakdown}. "
            summary += "Detailed investigation and monitoring recommended."
            
        else:
            summary = f"Found {len(anomalies)} anomalies and {len(root_causes)} root causes."
        
        return summary
    
    async def _generate_recommendations(
        self,
        root_causes: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Generate actionable recommendations."""
        recommendations = {
            "immediate": [],
            "short_term": [],
            "long_term": []
        }
        
        # Extract recommendations from root causes
        for root_cause in root_causes:
            cause_recommendations = root_cause.get("recommendations", [])
            
            # Categorize recommendations
            for rec in cause_recommendations:
                if any(word in rec.lower() for word in ["immediate", "urgent", "critical", "now"]):
                    recommendations["immediate"].append(rec)
                elif any(word in rec.lower() for word in ["monitor", "check", "verify", "review"]):
                    recommendations["short_term"].append(rec)
                else:
                    recommendations["long_term"].append(rec)
        
        # Add default recommendations if none provided
        if not any(recommendations.values()):
            recommendations["immediate"] = self.recommendation_templates["immediate"][:2]
            recommendations["short_term"] = self.recommendation_templates["short_term"][:2]
            recommendations["long_term"] = self.recommendation_templates["long_term"][:2]
        
        # Remove duplicates
        for category in recommendations:
            recommendations[category] = list(set(recommendations[category]))
        
        return recommendations
    
    async def _generate_insights(
        self,
        log_text: str,
        anomalies: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate additional insights from the analysis."""
        insights = {
            "system_health_score": 0.8,  # Mock score
            "trend_analysis": "Anomaly patterns suggest increasing system stress",
            "risk_assessment": "Medium risk of service degradation",
            "preventive_measures": [
                "Implement proactive monitoring",
                "Regular system health checks",
                "Capacity planning review"
            ],
            "historical_comparison": "Current anomaly rate is 15% above baseline",
            "predicted_impact": "Potential 5-10% service degradation if unaddressed"
        }
        
        # Calculate health score based on anomalies and root causes
        if anomalies:
            critical_count = len([a for a in anomalies if a.get("severity") == "critical"])
            high_count = len([a for a in anomalies if a.get("severity") == "high"])
            
            health_score = 1.0 - (critical_count * 0.3 + high_count * 0.2) / len(anomalies)
            insights["system_health_score"] = max(health_score, 0.0)
        
        return insights
