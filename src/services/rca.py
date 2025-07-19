"""
Root Cause Analysis Service

This module provides intelligent root cause analysis for detected anomalies
using pattern analysis, correlation detection, and domain knowledge.
"""

import re
import time
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

from ..models.schemas import (
    RCAResponse,
    RootCause,
    SeverityLevel,
    ConfidenceLevel,
    Anomaly,
)
from ..utils.config import get_settings

# Setup logging
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


class RootCauseAnalyzer:
    """
    Intelligent root cause analysis for Hadoop log anomalies.
    
    This service provides:
    - Pattern-based analysis of anomalies
    - Correlation detection between related issues
    - Domain-specific knowledge for Hadoop systems
    - Actionable recommendations for remediation
    """
    
    def __init__(self):
        """Initialize the root cause analyzer."""
        self.knowledge_base = self._load_knowledge_base()
        self.pattern_rules = self._load_pattern_rules()
        self.correlation_rules = self._load_correlation_rules()
        
        logger.info("Root cause analyzer initialized")
    
    async def analyze_root_causes(
        self,
        log_text: str,
        anomalies: List[Dict[str, Any]],
        context_window: int = 10,
    ) -> RCAResponse:
        """
        Perform comprehensive root cause analysis on detected anomalies.
        
        Args:
            log_text: Original log text for context
            anomalies: List of detected anomalies
            context_window: Number of lines to analyze around each anomaly
            
        Returns:
            Root cause analysis results
        """
        try:
            start_time = time.time()
            logger.info(f"Starting RCA for {len(anomalies)} anomalies")
            
            if not anomalies:
                return RCAResponse(
                    root_causes_found=False,
                    total_root_causes=0,
                    root_causes=[],
                    processing_time_ms=0.0,
                    confidence_score=0.0,
                    analysis_summary="No anomalies provided for analysis"
                )
            
            # Parse log lines for context
            log_lines = log_text.strip().split('\n')
            
            # Step 1: Extract context around anomalies
            anomaly_contexts = self._extract_anomaly_contexts(
                log_lines, anomalies, context_window
            )
            
            # Step 2: Pattern-based analysis
            pattern_causes = await self._analyze_patterns(anomaly_contexts)
            
            # Step 3: Correlation analysis
            correlation_causes = await self._analyze_correlations(anomaly_contexts)
            
            # Step 4: Temporal analysis
            temporal_causes = await self._analyze_temporal_patterns(anomaly_contexts)
            
            # Step 5: Component-based analysis
            component_causes = await self._analyze_components(anomaly_contexts)
            
            # Step 6: Merge and rank root causes
            all_causes = pattern_causes + correlation_causes + temporal_causes + component_causes
            root_causes = self._merge_and_rank_causes(all_causes)
            
            # Step 7: Generate analysis summary
            summary = self._generate_analysis_summary(root_causes, anomalies)
            
            # Calculate processing time and confidence
            processing_time = (time.time() - start_time) * 1000
            overall_confidence = self._calculate_overall_confidence(root_causes)
            
            response = RCAResponse(
                root_causes_found=len(root_causes) > 0,
                total_root_causes=len(root_causes),
                root_causes=root_causes,
                processing_time_ms=processing_time,
                confidence_score=overall_confidence,
                analysis_summary=summary
            )
            
            logger.info(f"RCA completed: {len(root_causes)} root causes identified")
            return response
            
        except Exception as e:
            logger.error(f"Root cause analysis failed: {e}", exc_info=True)
            raise RuntimeError(f"RCA failed: {e}")
    
    def _extract_anomaly_contexts(
        self,
        log_lines: List[str],
        anomalies: List[Dict[str, Any]],
        context_window: int
    ) -> List[Dict[str, Any]]:
        """Extract context around each anomaly for analysis."""
        contexts = []
        
        for anomaly in anomalies:
            line_number = anomaly.get('line_number', 0) - 1  # Convert to 0-based
            
            # Extract context window
            start_line = max(0, line_number - context_window)
            end_line = min(len(log_lines), line_number + context_window + 1)
            
            context = {
                'anomaly': anomaly,
                'line_number': line_number,
                'context_lines': log_lines[start_line:end_line],
                'before_lines': log_lines[start_line:line_number],
                'anomaly_line': log_lines[line_number] if line_number < len(log_lines) else "",
                'after_lines': log_lines[line_number + 1:end_line],
                'timestamp': self._extract_timestamp(anomaly.get('log_entry', '')),
                'component': self._extract_component(anomaly.get('log_entry', '')),
            }
            
            contexts.append(context)
        
        return contexts
    
    async def _analyze_patterns(self, contexts: List[Dict[str, Any]]) -> List[RootCause]:
        """Analyze anomalies using pattern-based rules."""
        causes = []
        
        for context in contexts:
            anomaly_line = context['anomaly_line']
            context_lines = context['context_lines']
            
            # Check each pattern rule
            for rule in self.pattern_rules:
                if self._matches_pattern(anomaly_line, context_lines, rule):
                    cause = self._create_root_cause_from_pattern(context, rule)
                    causes.append(cause)
        
        return causes
    
    async def _analyze_correlations(self, contexts: List[Dict[str, Any]]) -> List[RootCause]:
        """Analyze correlations between anomalies."""
        causes = []
        
        if len(contexts) < 2:
            return causes
        
        # Group anomalies by component and time
        component_groups = defaultdict(list)
        time_groups = defaultdict(list)
        
        for context in contexts:
            component = context.get('component')
            timestamp = context.get('timestamp')
            
            if component:
                component_groups[component].append(context)
            
            if timestamp:
                # Group by time windows (e.g., within 5 minutes)
                time_key = self._get_time_window(timestamp, window_minutes=5)
                time_groups[time_key].append(context)
        
        # Analyze component correlations
        for component, group_contexts in component_groups.items():
            if len(group_contexts) > 1:
                cause = self._create_component_correlation_cause(component, group_contexts)
                causes.append(cause)
        
        # Analyze temporal correlations
        for time_window, group_contexts in time_groups.items():
            if len(group_contexts) > 2:  # Multiple anomalies in same time window
                cause = self._create_temporal_correlation_cause(time_window, group_contexts)
                causes.append(cause)
        
        return causes
    
    async def _analyze_temporal_patterns(self, contexts: List[Dict[str, Any]]) -> List[RootCause]:
        """Analyze temporal patterns in anomalies."""
        causes = []
        
        # Extract timestamps and sort
        timestamped_contexts = [
            (ctx, ctx.get('timestamp')) for ctx in contexts
            if ctx.get('timestamp')
        ]
        
        if len(timestamped_contexts) < 2:
            return causes
        
        # Sort by timestamp
        timestamped_contexts.sort(key=lambda x: x[1] or "")
        
        # Look for cascading failures
        cascading_groups = self._detect_cascading_failures(timestamped_contexts)
        for group in cascading_groups:
            cause = self._create_cascading_failure_cause(group)
            causes.append(cause)
        
        # Look for periodic patterns
        periodic_patterns = self._detect_periodic_patterns(timestamped_contexts)
        for pattern in periodic_patterns:
            cause = self._create_periodic_pattern_cause(pattern)
            causes.append(cause)
        
        return causes
    
    async def _analyze_components(self, contexts: List[Dict[str, Any]]) -> List[RootCause]:
        """Analyze component-specific issues."""
        causes = []
        
        # Group by component
        component_issues = defaultdict(list)
        for context in contexts:
            component = context.get('component', 'unknown')
            component_issues[component].append(context)
        
        # Analyze each component
        for component, component_contexts in component_issues.items():
            if len(component_contexts) > 0:
                # Check for component-specific patterns
                component_cause = self._analyze_component_health(component, component_contexts)
                if component_cause:
                    causes.append(component_cause)
        
        return causes
    
    def _matches_pattern(self, anomaly_line: str, context_lines: List[str], rule: Dict[str, Any]) -> bool:
        """Check if an anomaly matches a pattern rule."""
        pattern = rule.get('pattern', '')
        context_patterns = rule.get('context_patterns', [])
        
        # Check main pattern
        if not re.search(pattern, anomaly_line, re.IGNORECASE):
            return False
        
        # Check context patterns if specified
        if context_patterns:
            context_text = '\n'.join(context_lines)
            for ctx_pattern in context_patterns:
                if not re.search(ctx_pattern, context_text, re.IGNORECASE):
                    return False
        
        return True
    
    def _create_root_cause_from_pattern(self, context: Dict[str, Any], rule: Dict[str, Any]) -> RootCause:
        """Create a root cause from a pattern match."""
        anomaly = context['anomaly']
        
        return RootCause(
            id=f"rc_pattern_{rule['id']}_{int(time.time())}",
            title=rule['title'],
            description=rule['description'],
            category=rule.get('category', 'pattern'),
            severity=SeverityLevel(rule.get('severity', 'medium')),
            confidence=ConfidenceLevel(rule.get('confidence', 'medium')),
            affected_components=[context.get('component', 'unknown')],
            related_anomalies=[anomaly.get('id', '')],
            recommended_actions=rule.get('actions', []),
            evidence=[context['anomaly_line']]
        )
    
    def _create_component_correlation_cause(self, component: str, contexts: List[Dict[str, Any]]) -> RootCause:
        """Create root cause for component correlation."""
        anomaly_ids = [ctx['anomaly'].get('id', '') for ctx in contexts]
        evidence = [ctx['anomaly_line'] for ctx in contexts]
        
        return RootCause(
            id=f"rc_component_{component}_{int(time.time())}",
            title=f"{component.title()} Component Issues",
            description=f"Multiple anomalies detected in {component} component, indicating potential component-level problems",
            category="component_correlation",
            severity=SeverityLevel.HIGH,
            confidence=ConfidenceLevel.HIGH,
            affected_components=[component],
            related_anomalies=anomaly_ids,
            recommended_actions=[
                f"Check {component} health and status",
                f"Review {component} configuration",
                f"Monitor {component} resource usage",
                "Check for recent changes to the component"
            ],
            evidence=evidence
        )
    
    def _create_temporal_correlation_cause(self, time_window: str, contexts: List[Dict[str, Any]]) -> RootCause:
        """Create root cause for temporal correlation."""
        anomaly_ids = [ctx['anomaly'].get('id', '') for ctx in contexts]
        components = list(set(ctx.get('component', 'unknown') for ctx in contexts))
        evidence = [ctx['anomaly_line'] for ctx in contexts]
        
        return RootCause(
            id=f"rc_temporal_{time_window.replace(':', '_')}_{int(time.time())}",
            title="Simultaneous System Issues",
            description=f"Multiple anomalies occurred within the same time window ({time_window}), suggesting a system-wide issue",
            category="temporal_correlation",
            severity=SeverityLevel.HIGH,
            confidence=ConfidenceLevel.MEDIUM,
            affected_components=components,
            related_anomalies=anomaly_ids,
            recommended_actions=[
                "Check system-wide events at the specified time",
                "Review network connectivity and stability",
                "Check for infrastructure changes or maintenance",
                "Monitor system resource usage during this period"
            ],
            evidence=evidence
        )
    
    def _detect_cascading_failures(self, timestamped_contexts: List[Tuple[Dict[str, Any], str]]) -> List[List[Dict[str, Any]]]:
        """Detect cascading failure patterns."""
        groups = []
        current_group = []
        
        for i, (context, timestamp) in enumerate(timestamped_contexts):
            if not current_group:
                current_group.append(context)
                continue
            
            # Check if this anomaly is within cascading window of previous
            prev_timestamp = timestamped_contexts[i-1][1]
            if self._is_within_cascading_window(prev_timestamp, timestamp):
                current_group.append(context)
            else:
                if len(current_group) > 2:  # At least 3 for cascading
                    groups.append(current_group)
                current_group = [context]
        
        # Add final group if it qualifies
        if len(current_group) > 2:
            groups.append(current_group)
        
        return groups
    
    def _create_cascading_failure_cause(self, contexts: List[Dict[str, Any]]) -> RootCause:
        """Create root cause for cascading failures."""
        anomaly_ids = [ctx['anomaly'].get('id', '') for ctx in contexts]
        components = list(set(ctx.get('component', 'unknown') for ctx in contexts))
        evidence = [ctx['anomaly_line'] for ctx in contexts[:3]]  # First few as evidence
        
        return RootCause(
            id=f"rc_cascading_{int(time.time())}",
            title="Cascading System Failures",
            description=f"Detected cascading failures across {len(contexts)} components, indicating a root system issue",
            category="cascading_failure",
            severity=SeverityLevel.CRITICAL,
            confidence=ConfidenceLevel.HIGH,
            affected_components=components,
            related_anomalies=anomaly_ids,
            recommended_actions=[
                "Identify and resolve the initial failure point",
                "Check system dependencies and interconnections",
                "Review system load balancing and failover mechanisms",
                "Implement circuit breakers to prevent cascade propagation"
            ],
            evidence=evidence
        )
    
    def _detect_periodic_patterns(self, timestamped_contexts: List[Tuple[Dict[str, Any], str]]) -> List[Dict[str, Any]]:
        """Detect periodic anomaly patterns."""
        # Simple periodic detection - could be enhanced with more sophisticated analysis
        patterns = []
        
        if len(timestamped_contexts) < 3:
            return patterns
        
        # Look for regular intervals
        intervals = []
        for i in range(1, len(timestamped_contexts)):
            prev_time = timestamped_contexts[i-1][1]
            curr_time = timestamped_contexts[i][1]
            interval = self._calculate_time_difference(prev_time, curr_time)
            if interval:
                intervals.append(interval)
        
        # Check for consistent intervals
        if len(intervals) >= 2:
            avg_interval = sum(intervals) / len(intervals)
            if all(abs(interval - avg_interval) < avg_interval * 0.2 for interval in intervals):
                patterns.append({
                    'type': 'periodic',
                    'interval_minutes': avg_interval,
                    'contexts': [ctx for ctx, _ in timestamped_contexts]
                })
        
        return patterns
    
    def _create_periodic_pattern_cause(self, pattern: Dict[str, Any]) -> RootCause:
        """Create root cause for periodic patterns."""
        contexts = pattern['contexts']
        interval = pattern['interval_minutes']
        anomaly_ids = [ctx['anomaly'].get('id', '') for ctx in contexts]
        
        return RootCause(
            id=f"rc_periodic_{int(time.time())}",
            title="Periodic System Issues",
            description=f"Detected periodic anomalies occurring every ~{interval:.1f} minutes, suggesting a recurring system issue",
            category="periodic_pattern",
            severity=SeverityLevel.MEDIUM,
            confidence=ConfidenceLevel.MEDIUM,
            affected_components=list(set(ctx.get('component', 'unknown') for ctx in contexts)),
            related_anomalies=anomaly_ids,
            recommended_actions=[
                "Investigate scheduled tasks or cron jobs",
                "Check for periodic maintenance operations",
                "Review system monitoring and alerting schedules",
                "Analyze resource utilization patterns"
            ],
            evidence=[ctx['anomaly_line'] for ctx in contexts[:3]]
        )
    
    def _analyze_component_health(self, component: str, contexts: List[Dict[str, Any]]) -> Optional[RootCause]:
        """Analyze health issues for a specific component."""
        if len(contexts) < 2:
            return None
        
        # Check severity of issues
        high_severity_count = sum(
            1 for ctx in contexts 
            if ctx['anomaly'].get('severity') in ['high', 'critical']
        )
        
        if high_severity_count >= len(contexts) * 0.5:  # At least 50% high severity
            anomaly_ids = [ctx['anomaly'].get('id', '') for ctx in contexts]
            
            return RootCause(
                id=f"rc_health_{component}_{int(time.time())}",
                title=f"{component.title()} Component Health Issues",
                description=f"High-severity issues detected in {component} component affecting system stability",
                category="component_health",
                severity=SeverityLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                affected_components=[component],
                related_anomalies=anomaly_ids,
                recommended_actions=self._get_component_specific_actions(component),
                evidence=[ctx['anomaly_line'] for ctx in contexts[:3]]
            )
        
        return None
    
    def _get_component_specific_actions(self, component: str) -> List[str]:
        """Get component-specific recommended actions."""
        actions_map = {
            'namenode': [
                "Check NameNode health and SafeMode status",
                "Verify filesystem integrity with fsck",
                "Monitor NameNode memory usage",
                "Check NameNode logs for detailed errors"
            ],
            'datanode': [
                "Check DataNode disk space and health",
                "Verify DataNode connectivity to NameNode",
                "Monitor DataNode block reports",
                "Check for disk errors and failures"
            ],
            'resourcemanager': [
                "Check ResourceManager health and status",
                "Verify YARN configuration",
                "Monitor resource allocation and usage",
                "Check for application queue issues"
            ],
            'nodemanager': [
                "Check NodeManager health and status",
                "Verify container execution environment",
                "Monitor node resource usage",
                "Check for local directory issues"
            ]
        }
        
        return actions_map.get(component, [
            f"Check {component} health and status",
            f"Review {component} configuration",
            f"Monitor {component} resource usage",
            f"Check {component} logs for detailed information"
        ])
    
    def _merge_and_rank_causes(self, all_causes: List[RootCause]) -> List[RootCause]:
        """Merge similar causes and rank by importance."""
        # Simple deduplication based on title similarity
        unique_causes = []
        seen_titles = set()
        
        # Sort by severity and confidence
        sorted_causes = sorted(
            all_causes,
            key=lambda x: (
                ['low', 'medium', 'high', 'critical'].index(x.severity.value),
                ['low', 'medium', 'high'].index(x.confidence.value)
            ),
            reverse=True
        )
        
        for cause in sorted_causes:
            if cause.title not in seen_titles:
                unique_causes.append(cause)
                seen_titles.add(cause.title)
        
        return unique_causes[:10]  # Return top 10 causes
    
    def _generate_analysis_summary(self, root_causes: List[RootCause], anomalies: List[Dict[str, Any]]) -> str:
        """Generate a high-level summary of the analysis."""
        if not root_causes:
            return f"Analysis of {len(anomalies)} anomalies completed but no specific root causes identified"
        
        # Count by category
        category_counts = Counter(cause.category for cause in root_causes)
        severity_counts = Counter(cause.severity.value for cause in root_causes)
        
        # Generate summary
        summary_parts = [
            f"Identified {len(root_causes)} potential root causes from {len(anomalies)} anomalies."
        ]
        
        if 'critical' in severity_counts:
            summary_parts.append(f"Found {severity_counts['critical']} critical issues requiring immediate attention.")
        
        if category_counts:
            top_category = category_counts.most_common(1)[0][0]
            summary_parts.append(f"Primary issue category: {top_category.replace('_', ' ')}")
        
        # Add specific recommendations
        if any(cause.severity == SeverityLevel.CRITICAL for cause in root_causes):
            summary_parts.append("Immediate action recommended for critical severity issues.")
        
        return " ".join(summary_parts)
    
    def _calculate_overall_confidence(self, root_causes: List[RootCause]) -> float:
        """Calculate overall confidence score for the analysis."""
        if not root_causes:
            return 0.0
        
        confidence_values = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.9
        }
        
        weighted_sum = sum(
            confidence_values[cause.confidence.value] 
            for cause in root_causes
        )
        
        return min(1.0, weighted_sum / len(root_causes))
    
    # Helper methods
    
    def _extract_timestamp(self, log_entry: str) -> Optional[str]:
        """Extract timestamp from log entry."""
        import re
        patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, log_entry)
            if match:
                return match.group(0)
        return None
    
    def _extract_component(self, log_entry: str) -> Optional[str]:
        """Extract component from log entry."""
        components = ['namenode', 'datanode', 'resourcemanager', 'nodemanager', 'yarn', 'hdfs']
        log_lower = log_entry.lower()
        
        for component in components:
            if component in log_lower:
                return component
        return None
    
    def _get_time_window(self, timestamp: str, window_minutes: int = 5) -> str:
        """Get time window key for grouping."""
        # Simple time window - could be enhanced
        return timestamp[:16]  # Group by hour and minute
    
    def _is_within_cascading_window(self, prev_timestamp: str, curr_timestamp: str, window_minutes: int = 2) -> bool:
        """Check if timestamps are within cascading failure window."""
        # Simple implementation - could be enhanced with proper datetime parsing
        return True  # For now, assume they're close enough
    
    def _calculate_time_difference(self, time1: str, time2: str) -> Optional[float]:
        """Calculate time difference in minutes."""
        # Simple implementation - would need proper datetime parsing
        return 5.0  # Return a default interval for now
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load domain-specific knowledge base."""
        return {
            'hadoop_components': ['namenode', 'datanode', 'resourcemanager', 'nodemanager'],
            'common_errors': ['connection_timeout', 'out_of_memory', 'disk_full', 'network_error'],
            'severity_keywords': {
                'critical': ['fatal', 'critical', 'severe'],
                'high': ['error', 'exception', 'failed'],
                'medium': ['warning', 'warn'],
                'low': ['info', 'debug']
            }
        }
    
    def _load_pattern_rules(self) -> List[Dict[str, Any]]:
        """Load pattern-based analysis rules."""
        return [
            {
                'id': 'connection_timeout',
                'pattern': r'connection.*timeout|timeout.*connection',
                'title': 'Connection Timeout Issues',
                'description': 'Network connectivity issues causing connection timeouts',
                'category': 'network',
                'severity': 'high',
                'confidence': 'high',
                'actions': [
                    'Check network connectivity',
                    'Verify firewall settings',
                    'Monitor network latency',
                    'Check DNS resolution'
                ]
            },
            {
                'id': 'out_of_memory',
                'pattern': r'out of memory|outofmemoryerror|java heap space',
                'title': 'Memory Exhaustion',
                'description': 'System running out of available memory',
                'category': 'resource',
                'severity': 'critical',
                'confidence': 'high',
                'actions': [
                    'Increase heap size',
                    'Optimize memory usage',
                    'Check for memory leaks',
                    'Monitor garbage collection'
                ]
            },
            {
                'id': 'disk_full',
                'pattern': r'no space left|disk.*full|insufficient disk space',
                'title': 'Disk Space Exhaustion',
                'description': 'Storage device running out of available space',
                'category': 'resource',
                'severity': 'critical',
                'confidence': 'high',
                'actions': [
                    'Free up disk space',
                    'Add more storage capacity',
                    'Archive old data',
                    'Monitor disk usage'
                ]
            }
        ]
    
    def _load_correlation_rules(self) -> List[Dict[str, Any]]:
        """Load correlation analysis rules."""
        return [
            {
                'components': ['namenode', 'datanode'],
                'pattern': 'hdfs connectivity',
                'description': 'HDFS connectivity issues between NameNode and DataNode'
            },
            {
                'components': ['resourcemanager', 'nodemanager'],
                'pattern': 'yarn resource allocation',
                'description': 'YARN resource allocation issues'
            }
        ]
