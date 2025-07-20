"""
Root Cause Analysis Agent

This agent specializes in analyzing anomalies to determine their root causes
using advanced AI models and pattern recognition.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse, AgentStatus, AgentCapability
from ..models.schemas import (
    RootCause,
    RCAResponse,
    SeverityLevel,
    ConfidenceLevel
)


class RootCauseAgent(BaseAgent):
    """
    AI Agent specialized in root cause analysis.
    
    This agent:
    - Analyzes detected anomalies for patterns
    - Identifies potential root causes
    - Provides recommendations for remediation
    - Uses contextual analysis and historical patterns
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        capabilities = [
            AgentCapability.ROOT_CAUSE_ANALYSIS,
            AgentCapability.EXPLANATION_GENERATION
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name or "RootCauseAgent",
            capabilities=capabilities,
            config=config or {}
        )
        
        # RCA components
        self.context_window = self.config.get("context_window", 10)
        self.min_confidence = self.config.get("min_confidence", 0.6)
        self.pattern_database = {}
        self.historical_causes = []
        
    def _initialize(self):
        """Initialize the root cause analysis components."""
        try:
            self.logger.info("Initializing root cause analysis agent")
            
            # Load pattern database and historical data
            self._load_pattern_database()
            self._load_historical_causes()
            
            self.logger.info("Root cause analysis agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize root cause agent: {e}")
            raise
    
    def _load_pattern_database(self):
        """Load known patterns and their associated root causes."""
        # Mock pattern database - in production this would load from a real database
        self.pattern_database = {
            "connection_timeout": {
                "patterns": ["connection timeout", "socket timeout", "network unreachable"],
                "causes": [
                    "Network connectivity issues",
                    "Firewall blocking connections", 
                    "Target service unavailable",
                    "DNS resolution failure"
                ]
            },
            "memory_issues": {
                "patterns": ["out of memory", "heap space", "gc overhead"],
                "causes": [
                    "Memory leak in application",
                    "Insufficient heap size configuration",
                    "Heavy load causing memory pressure",
                    "Memory fragmentation"
                ]
            },
            "disk_issues": {
                "patterns": ["disk full", "no space left", "io error"],
                "causes": [
                    "Disk space exhaustion",
                    "Hardware failure",
                    "File system corruption",
                    "Permission issues"
                ]
            },
            "authentication_failure": {
                "patterns": ["authentication failed", "invalid credentials", "access denied"],
                "causes": [
                    "Expired credentials",
                    "Incorrect configuration",
                    "Security policy changes",
                    "Account lockout"
                ]
            }
        }
    
    def _load_historical_causes(self):
        """Load historical root cause data for pattern matching."""
        # Mock historical data - in production this would load from a database
        self.historical_causes = [
            {
                "pattern": "namenode connection timeout",
                "cause": "Namenode service overload",
                "frequency": 15,
                "resolution": "Scale namenode resources"
            },
            {
                "pattern": "datanode heartbeat failure", 
                "cause": "Network partition",
                "frequency": 8,
                "resolution": "Check network connectivity"
            }
        ]
    
    async def process(self, input_data: Dict[str, Any], **kwargs) -> AgentResponse:
        """
        Process anomalies for root cause analysis.
        
        Args:
            input_data: Dictionary containing:
                - log_text: Original log text
                - anomalies: List of detected anomalies
                - context_window: Optional context window override
            **kwargs: Additional processing parameters
            
        Returns:
            AgentResponse with root cause analysis results
        """
        start_time = self.get_processing_time()
        
        # Extract parameters
        log_text = input_data.get("log_text", "")
        anomalies = input_data.get("anomalies", [])
        context_window = input_data.get("context_window", self.context_window)
        
        if not anomalies:
            # No anomalies to analyze
            response_data = {
                "root_causes_found": False,
                "root_cause_count": 0,
                "root_causes": [],
                "analysis_summary": "No anomalies provided for analysis"
            }
        else:
            # Perform root cause analysis
            root_causes = await self._analyze_root_causes(
                log_text, anomalies, context_window
            )
            
            response_data = {
                "root_causes_found": len(root_causes) > 0,
                "root_cause_count": len(root_causes),
                "root_causes": [cause.dict() for cause in root_causes],
                "analysis_summary": self._generate_analysis_summary(root_causes),
                "recommendations": self._generate_recommendations(root_causes)
            }
        
        # Calculate processing time
        processing_time = self.get_processing_time() - start_time
        
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            status=AgentStatus.COMPLETED,
            result=response_data,
            processing_time_ms=processing_time,
            metadata={
                "context_window": context_window,
                "anomalies_analyzed": len(anomalies),
                "patterns_matched": len(response_data.get("root_causes", []))
            }
        )
    
    async def _analyze_root_causes(
        self,
        log_text: str,
        anomalies: List[Dict[str, Any]],
        context_window: int
    ) -> List[RootCause]:
        """
        Analyze anomalies to identify root causes.
        
        Args:
            log_text: Original log text
            anomalies: List of detected anomalies
            context_window: Context window for analysis
            
        Returns:
            List of identified root causes
        """
        root_causes = []
        log_lines = log_text.split('\n')
        
        # Group anomalies by similarity
        anomaly_groups = await self._group_anomalies(anomalies)
        
        for group in anomaly_groups:
            # Analyze each group for potential root causes
            causes = await self._analyze_anomaly_group(
                group, log_lines, context_window
            )
            root_causes.extend(causes)
        
        # Remove duplicates and rank by confidence
        root_causes = self._deduplicate_and_rank(root_causes)
        
        return root_causes
    
    async def _group_anomalies(self, anomalies: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Group similar anomalies together for analysis.
        
        Args:
            anomalies: List of anomalies
            
        Returns:
            List of anomaly groups
        """
        groups = []
        used_indices = set()
        
        for i, anomaly in enumerate(anomalies):
            if i in used_indices:
                continue
                
            # Create new group with this anomaly
            group = [anomaly]
            used_indices.add(i)
            
            # Find similar anomalies
            for j, other_anomaly in enumerate(anomalies[i+1:], i+1):
                if j in used_indices:
                    continue
                    
                if await self._are_anomalies_similar(anomaly, other_anomaly):
                    group.append(other_anomaly)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    async def _are_anomalies_similar(
        self, 
        anomaly1: Dict[str, Any], 
        anomaly2: Dict[str, Any]
    ) -> bool:
        """
        Check if two anomalies are similar.
        
        Args:
            anomaly1: First anomaly
            anomaly2: Second anomaly
            
        Returns:
            True if anomalies are similar
        """
        # Check if they have the same type
        if anomaly1.get("anomaly_type") == anomaly2.get("anomaly_type"):
            return True
        
        # Check if they have similar components
        if anomaly1.get("component") == anomaly2.get("component"):
            return True
        
        # Check for similar keywords in log entries
        entry1 = anomaly1.get("log_entry", "").lower()
        entry2 = anomaly2.get("log_entry", "").lower()
        
        common_keywords = self._find_common_keywords(entry1, entry2)
        return len(common_keywords) >= 2
    
    def _find_common_keywords(self, text1: str, text2: str) -> List[str]:
        """Find common keywords between two text strings."""
        keywords1 = set(text1.split())
        keywords2 = set(text2.split())
        
        # Filter out common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        keywords1 -= stop_words
        keywords2 -= stop_words
        
        return list(keywords1.intersection(keywords2))
    
    async def _analyze_anomaly_group(
        self,
        anomaly_group: List[Dict[str, Any]],
        log_lines: List[str],
        context_window: int
    ) -> List[RootCause]:
        """
        Analyze a group of similar anomalies for root causes.
        
        Args:
            anomaly_group: Group of similar anomalies
            log_lines: All log lines for context
            context_window: Context window size
            
        Returns:
            List of potential root causes
        """
        root_causes = []
        
        # Extract context around anomalies
        context = self._extract_context(anomaly_group, log_lines, context_window)
        
        # Pattern matching against known issues
        pattern_matches = await self._match_patterns(context)
        
        for match in pattern_matches:
            root_cause = await self._create_root_cause(
                anomaly_group, match, context
            )
            root_causes.append(root_cause)
        
        # If no patterns match, generate generic root cause
        if not root_causes:
            generic_cause = await self._generate_generic_root_cause(
                anomaly_group, context
            )
            root_causes.append(generic_cause)
        
        return root_causes
    
    def _extract_context(
        self,
        anomaly_group: List[Dict[str, Any]],
        log_lines: List[str],
        context_window: int
    ) -> Dict[str, Any]:
        """
        Extract context around anomalies.
        
        Args:
            anomaly_group: Group of anomalies
            log_lines: All log lines
            context_window: Context window size
            
        Returns:
            Context information
        """
        context_lines = []
        line_numbers = []
        
        for anomaly in anomaly_group:
            line_num = anomaly.get("line_number", 1) - 1  # Convert to 0-based
            
            # Extract context window
            start_idx = max(0, line_num - context_window)
            end_idx = min(len(log_lines), line_num + context_window + 1)
            
            for i in range(start_idx, end_idx):
                if i < len(log_lines) and log_lines[i] not in context_lines:
                    context_lines.append(log_lines[i])
                    line_numbers.append(i + 1)
        
        return {
            "context_lines": context_lines,
            "line_numbers": line_numbers,
            "anomaly_count": len(anomaly_group),
            "primary_component": anomaly_group[0].get("component"),
            "primary_type": anomaly_group[0].get("anomaly_type")
        }
    
    async def _match_patterns(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Match context against known patterns.
        
        Args:
            context: Context information
            
        Returns:
            List of pattern matches
        """
        matches = []
        context_text = " ".join(context["context_lines"]).lower()
        
        for pattern_name, pattern_info in self.pattern_database.items():
            for pattern in pattern_info["patterns"]:
                if pattern in context_text:
                    matches.append({
                        "pattern_name": pattern_name,
                        "pattern": pattern,
                        "causes": pattern_info["causes"],
                        "confidence": 0.8  # Base confidence for pattern match
                    })
        
        return matches
    
    async def _create_root_cause(
        self,
        anomaly_group: List[Dict[str, Any]],
        pattern_match: Dict[str, Any],
        context: Dict[str, Any]
    ) -> RootCause:
        """
        Create a RootCause object from pattern match.
        
        Args:
            anomaly_group: Group of anomalies
            pattern_match: Matched pattern
            context: Context information
            
        Returns:
            RootCause object
        """
        # Select most likely cause from pattern
        primary_cause = pattern_match["causes"][0]
        
        # Calculate confidence based on various factors
        confidence_score = pattern_match["confidence"]
        confidence_level = self._score_to_confidence_level(confidence_score)
        
        # Determine severity based on anomaly group
        severity = self._determine_group_severity(anomaly_group)
        
        return RootCause(
            id=f"rca_{pattern_match['pattern_name']}_{len(anomaly_group)}",
            description=primary_cause,
            category=pattern_match["pattern_name"],
            confidence=confidence_level,
            severity=severity,
            affected_components=[context.get("primary_component", "unknown")],
            related_anomaly_ids=[a.get("id", "") for a in anomaly_group],
            evidence=self._generate_evidence(anomaly_group, pattern_match),
            recommendations=self._generate_pattern_recommendations(pattern_match),
            likelihood_score=confidence_score
        )
    
    async def _generate_generic_root_cause(
        self,
        anomaly_group: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> RootCause:
        """
        Generate a generic root cause when no patterns match.
        
        Args:
            anomaly_group: Group of anomalies
            context: Context information
            
        Returns:
            Generic RootCause object
        """
        anomaly_type = context.get("primary_type", "unknown")
        component = context.get("primary_component", "system")
        
        description = f"Potential issue in {component} component based on {anomaly_type} pattern"
        
        return RootCause(
            id=f"rca_generic_{anomaly_type}_{len(anomaly_group)}",
            description=description,
            category="generic_analysis",
            confidence=ConfidenceLevel.LOW,
            severity=self._determine_group_severity(anomaly_group),
            affected_components=[component],
            related_anomaly_ids=[a.get("id", "") for a in anomaly_group],
            evidence=[f"Multiple {anomaly_type} anomalies detected in {component}"],
            recommendations=[
                f"Investigate {component} component health",
                "Check recent configuration changes",
                "Monitor resource utilization"
            ],
            likelihood_score=0.4
        )
    
    def _determine_group_severity(self, anomaly_group: List[Dict[str, Any]]) -> SeverityLevel:
        """Determine severity level for an anomaly group."""
        severity_scores = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1
        }
        
        max_severity = 0
        for anomaly in anomaly_group:
            severity = anomaly.get("severity", "low")
            score = severity_scores.get(severity, 1)
            max_severity = max(max_severity, score)
        
        # Multiple anomalies increase severity
        if len(anomaly_group) > 3:
            max_severity = min(max_severity + 1, 4)
        
        severity_map = {4: SeverityLevel.CRITICAL, 3: SeverityLevel.HIGH, 
                       2: SeverityLevel.MEDIUM, 1: SeverityLevel.LOW}
        
        return severity_map[max_severity]
    
    def _score_to_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert confidence score to confidence level."""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_evidence(
        self,
        anomaly_group: List[Dict[str, Any]],
        pattern_match: Dict[str, Any]
    ) -> List[str]:
        """Generate evidence for the root cause."""
        evidence = [
            f"Pattern '{pattern_match['pattern']}' detected in log entries",
            f"{len(anomaly_group)} related anomalies found"
        ]
        
        # Add specific evidence from anomalies
        for anomaly in anomaly_group[:3]:  # Limit to first 3
            evidence.append(f"Line {anomaly.get('line_number', 'N/A')}: {anomaly.get('log_entry', '')[:100]}...")
        
        return evidence
    
    def _generate_pattern_recommendations(
        self,
        pattern_match: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on pattern match."""
        # This would be enhanced with a proper recommendation engine
        base_recommendations = [
            "Check system logs for additional context",
            "Verify system resource availability",
            "Review recent configuration changes"
        ]
        
        pattern_specific = {
            "connection_timeout": [
                "Check network connectivity",
                "Verify firewall rules",
                "Test DNS resolution"
            ],
            "memory_issues": [
                "Increase heap size if applicable",
                "Check for memory leaks",
                "Monitor garbage collection"
            ],
            "disk_issues": [
                "Free up disk space",
                "Check disk health",
                "Verify file permissions"
            ]
        }
        
        pattern_name = pattern_match.get("pattern_name", "")
        specific = pattern_specific.get(pattern_name, [])
        
        return specific + base_recommendations
    
    def _deduplicate_and_rank(self, root_causes: List[RootCause]) -> List[RootCause]:
        """Remove duplicates and rank root causes by confidence."""
        # Simple deduplication by description
        seen_descriptions = set()
        unique_causes = []
        
        for cause in root_causes:
            if cause.description not in seen_descriptions:
                unique_causes.append(cause)
                seen_descriptions.add(cause.description)
        
        # Sort by likelihood score descending
        unique_causes.sort(key=lambda x: x.likelihood_score, reverse=True)
        
        return unique_causes
    
    def _generate_analysis_summary(self, root_causes: List[RootCause]) -> str:
        """Generate a summary of the root cause analysis."""
        if not root_causes:
            return "No specific root causes identified in the analysis."
        
        if len(root_causes) == 1:
            return f"Primary root cause identified: {root_causes[0].description}"
        
        return f"Analysis identified {len(root_causes)} potential root causes, with primary cause: {root_causes[0].description}"
    
    def _generate_recommendations(self, root_causes: List[RootCause]) -> List[str]:
        """Generate overall recommendations from root causes."""
        all_recommendations = []
        
        for cause in root_causes:
            all_recommendations.extend(cause.recommendations)
        
        # Remove duplicates while preserving order
        unique_recommendations = []
        seen = set()
        
        for rec in all_recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)
        
        return unique_recommendations[:10]  # Limit to top 10
