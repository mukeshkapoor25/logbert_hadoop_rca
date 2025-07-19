"""
Log Preprocessing Module for LogBERT Hadoop RCA

This module provides comprehensive log preprocessing capabilities including:
- Log parsing and template extraction using Drain algorithm
- Text normalization and cleaning
- Feature extraction and tokenization
- Hadoop-specific log handling
"""

import re
import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime
import hashlib

# Import Drain algorithm from logparser
try:
    from ...logparser.Drain import LogParser as DrainParser
except ImportError:
    # Fallback if logparser is not available
    DrainParser = None

from ..utils.logging import get_logger

logger = get_logger(__name__)


class LogPreprocessor:
    """
    Main log preprocessing class for LogBERT.
    
    This class handles all aspects of log preprocessing including:
    - Raw log parsing and cleaning
    - Template extraction using Drain algorithm
    - Hadoop-specific log pattern recognition
    - Text normalization for BERT input
    """
    
    def __init__(
        self,
        use_drain: bool = True,
        drain_config: Optional[Dict[str, Any]] = None,
        hadoop_specific: bool = True,
    ):
        """
        Initialize the log preprocessor.
        
        Args:
            use_drain: Whether to use Drain algorithm for template extraction
            drain_config: Configuration for Drain algorithm
            hadoop_specific: Enable Hadoop-specific preprocessing
        """
        self.use_drain = use_drain and DrainParser is not None
        self.hadoop_specific = hadoop_specific
        
        # Default Drain configuration
        self.drain_config = drain_config or {
            'sim_th': 0.4,          # Similarity threshold
            'depth': 4,             # Depth of parsing tree
            'max_child': 100,       # Maximum children per node
            'remove_col': [],       # Columns to remove
            'rex': [                # Regular expressions for preprocessing
                r'blk_-?\d+',       # Block IDs
                r'(\d+\.){3}\d+',   # IP addresses
                r'\d{2,}',          # Numbers with 2+ digits
            ]
        }
        
        # Initialize Drain parser if enabled
        self.drain_parser = None
        if self.use_drain:
            self._initialize_drain()
        
        # Hadoop-specific patterns
        self.hadoop_patterns = self._get_hadoop_patterns()
        
        # Common log patterns
        self.timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}',     # 2023-07-19 10:30:45,123
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',           # 2023-07-19 10:30:45
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',           # 07/19/2023 10:30:45
            r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}',           # 2023/07/19 10:30:45
        ]
        
        logger.info(f"LogPreprocessor initialized - Drain: {self.use_drain}, Hadoop: {self.hadoop_specific}")
    
    def _initialize_drain(self):
        """Initialize the Drain log parser."""
        try:
            if DrainParser:
                self.drain_parser = DrainParser(
                    log_format='<Date> <Time> <Level> <Component>: <Content>',
                    indir='.',
                    outdir='./drain_output',
                    **self.drain_config
                )
                logger.info("Drain parser initialized successfully")
            else:
                logger.warning("Drain parser not available, template extraction disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Drain parser: {e}")
            self.use_drain = False
    
    def _get_hadoop_patterns(self) -> Dict[str, List[str]]:
        """Get Hadoop-specific log patterns."""
        return {
            'components': [
                r'namenode', r'datanode', r'resourcemanager', r'nodemanager',
                r'jobtracker', r'tasktracker', r'yarn', r'hdfs', r'mapreduce',
                r'historyserver', r'timelineservice', r'applicationmaster'
            ],
            'operations': [
                r'addBlock', r'receiveBlock', r'deleteBlock', r'getBlockLocations',
                r'startContainer', r'stopContainer', r'allocateContainer',
                r'submitApplication', r'finishApplication', r'killApplication'
            ],
            'error_keywords': [
                r'exception', r'error', r'failed', r'timeout', r'connection',
                r'refused', r'denied', r'cannot', r'unable', r'invalid'
            ],
            'resource_patterns': [
                r'memory', r'cpu', r'disk', r'network', r'io', r'heap',
                r'gc', r'thread', r'queue', r'capacity'
            ]
        }
    
    def preprocess_log_file(
        self,
        file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """
        Preprocess an entire log file.
        
        Args:
            file_path: Path to the input log file
            output_path: Optional path for processed output
            
        Returns:
            Dictionary containing preprocessing results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")
        
        logger.info(f"Preprocessing log file: {file_path}")
        
        try:
            # Read log file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                raw_lines = f.readlines()
            
            # Process each line
            processed_logs = []
            templates = {}
            template_count = 0
            
            for i, line in enumerate(raw_lines):
                if line.strip():  # Skip empty lines
                    result = self.preprocess_log_line(line, line_number=i+1)
                    processed_logs.append(result)
                    
                    # Track templates if using Drain
                    if self.use_drain and 'template_id' in result:
                        template_id = result['template_id']
                        if template_id not in templates:
                            templates[template_id] = {
                                'template': result.get('template', ''),
                                'count': 0,
                                'first_occurrence': i+1
                            }
                        templates[template_id]['count'] += 1
            
            # Prepare results
            results = {
                'file_path': str(file_path),
                'total_lines': len(raw_lines),
                'processed_lines': len(processed_logs),
                'empty_lines': len(raw_lines) - len(processed_logs),
                'templates': templates,
                'template_count': len(templates),
                'processed_logs': processed_logs,
                'preprocessing_stats': self._calculate_stats(processed_logs),
            }
            
            # Save processed output if requested
            if output_path:
                self._save_processed_logs(results, output_path)
            
            logger.info(f"Preprocessing completed: {len(processed_logs)} lines processed")
            return results
            
        except Exception as e:
            logger.error(f"Error preprocessing log file {file_path}: {e}", exc_info=True)
            raise
    
    def preprocess_log_line(
        self,
        log_line: str,
        line_number: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Preprocess a single log line.
        
        Args:
            log_line: Raw log line text
            line_number: Optional line number for tracking
            
        Returns:
            Dictionary containing processed log information
        """
        result = {
            'line_number': line_number,
            'original_text': log_line.strip(),
            'processed_text': '',
            'timestamp': None,
            'level': None,
            'component': None,
            'message': '',
            'template': None,
            'template_id': None,
            'features': {},
        }
        
        try:
            # Extract basic components
            parsed = self._parse_log_structure(log_line)
            result.update(parsed)
            
            # Extract template if using Drain
            if self.use_drain:
                template_info = self._extract_template(log_line)
                result.update(template_info)
            
            # Normalize text for BERT
            result['processed_text'] = self._normalize_for_bert(result['message'])
            
            # Extract features
            result['features'] = self._extract_features(log_line)
            
        except Exception as e:
            logger.warning(f"Error processing log line {line_number}: {e}")
            result['processed_text'] = self._normalize_for_bert(log_line)
        
        return result
    
    def _parse_log_structure(self, log_line: str) -> Dict[str, Any]:
        """Parse basic log structure (timestamp, level, component, message)."""
        result = {
            'timestamp': None,
            'level': None,
            'component': None,
            'message': log_line.strip(),
        }
        
        # Extract timestamp
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, log_line)
            if match:
                result['timestamp'] = match.group(0)
                break
        
        # Extract log level
        level_pattern = r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b'
        level_match = re.search(level_pattern, log_line, re.IGNORECASE)
        if level_match:
            result['level'] = level_match.group(0).upper()
        
        # Extract component (Hadoop-specific)
        if self.hadoop_specific:
            for component in self.hadoop_patterns['components']:
                if re.search(component, log_line, re.IGNORECASE):
                    result['component'] = component.lower()
                    break
        
        # Extract message content (after timestamp and level)
        message = log_line
        if result['timestamp']:
            message = re.sub(re.escape(result['timestamp']), '', message, count=1)
        if result['level']:
            message = re.sub(r'\b' + re.escape(result['level']) + r'\b', '', message, count=1, flags=re.IGNORECASE)
        
        result['message'] = message.strip()
        
        return result
    
    def _extract_template(self, log_line: str) -> Dict[str, Any]:
        """Extract log template using Drain algorithm."""
        if not self.drain_parser:
            return {'template': None, 'template_id': None}
        
        try:
            # Use Drain to parse the log line
            # Note: This is a simplified version - real Drain integration
            # would require proper file handling
            
            # For now, we'll create a simple template by replacing
            # variable parts with placeholders
            template = self._create_simple_template(log_line)
            template_id = self._hash_template(template)
            
            return {
                'template': template,
                'template_id': template_id,
            }
            
        except Exception as e:
            logger.warning(f"Template extraction failed: {e}")
            return {'template': None, 'template_id': None}
    
    def _create_simple_template(self, log_line: str) -> str:
        """Create a simple template by replacing variable parts."""
        template = log_line
        
        # Replace common variable patterns
        replacements = [
            (r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.]?\d*', '<TIMESTAMP>'),
            (r'\b\d+\.\d+\.\d+\.\d+\b', '<IP>'),
            (r'\bblk_-?\d+', '<BLOCK_ID>'),
            (r'\b\d{10,}', '<LARGE_NUMBER>'),
            (r'\b\d+\b', '<NUMBER>'),
            (r'/[a-zA-Z0-9/_.-]+', '<PATH>'),
            (r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', '<UUID>'),
        ]
        
        for pattern, replacement in replacements:
            template = re.sub(pattern, replacement, template)
        
        return template
    
    def _hash_template(self, template: str) -> str:
        """Create a hash ID for a template."""
        return hashlib.md5(template.encode()).hexdigest()[:8]
    
    def _normalize_for_bert(self, text: str) -> str:
        """Normalize text for BERT input."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that don't add meaning
        text = re.sub(r'[^\w\s\-_./:]', ' ', text)
        
        # Normalize common patterns
        normalizations = [
            # Normalize numbers
            (r'\b\d+\b', '<NUM>'),
            # Normalize paths
            (r'/[a-zA-Z0-9/_.-]+', '<PATH>'),
            # Normalize IPs
            (r'\b\d+\.\d+\.\d+\.\d+\b', '<IP>'),
            # Normalize block IDs
            (r'blk_-?\d+', '<BLOCK>'),
            # Normalize UUIDs
            (r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '<UUID>'),
        ]
        
        for pattern, replacement in normalizations:
            text = re.sub(pattern, replacement, text)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_features(self, log_line: str) -> Dict[str, Any]:
        """Extract various features from log line."""
        features = {
            'line_length': len(log_line),
            'word_count': len(log_line.split()),
            'has_error': False,
            'has_warning': False,
            'has_ip': False,
            'has_number': False,
            'has_path': False,
            'hadoop_component': None,
            'log_level': None,
        }
        
        # Check for error indicators
        error_patterns = ['error', 'exception', 'failed', 'timeout', 'denied']
        features['has_error'] = any(
            re.search(pattern, log_line, re.IGNORECASE)
            for pattern in error_patterns
        )
        
        # Check for warning indicators
        warning_patterns = ['warn', 'warning', 'deprecated']
        features['has_warning'] = any(
            re.search(pattern, log_line, re.IGNORECASE)
            for pattern in warning_patterns
        )
        
        # Check for IP addresses
        features['has_ip'] = bool(re.search(r'\b\d+\.\d+\.\d+\.\d+\b', log_line))
        
        # Check for numbers
        features['has_number'] = bool(re.search(r'\d+', log_line))
        
        # Check for file paths
        features['has_path'] = bool(re.search(r'/[a-zA-Z0-9/_.-]+', log_line))
        
        # Extract Hadoop component
        if self.hadoop_specific:
            for component in self.hadoop_patterns['components']:
                if re.search(component, log_line, re.IGNORECASE):
                    features['hadoop_component'] = component.lower()
                    break
        
        # Extract log level
        level_match = re.search(r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|TRACE)\b', log_line, re.IGNORECASE)
        if level_match:
            features['log_level'] = level_match.group(0).upper()
        
        return features
    
    def _calculate_stats(self, processed_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate preprocessing statistics."""
        if not processed_logs:
            return {}
        
        stats = {
            'total_logs': len(processed_logs),
            'with_timestamp': sum(1 for log in processed_logs if log.get('timestamp')),
            'with_level': sum(1 for log in processed_logs if log.get('level')),
            'with_component': sum(1 for log in processed_logs if log.get('component')),
            'error_logs': sum(1 for log in processed_logs if log.get('features', {}).get('has_error')),
            'warning_logs': sum(1 for log in processed_logs if log.get('features', {}).get('has_warning')),
            'avg_line_length': sum(log.get('features', {}).get('line_length', 0) for log in processed_logs) / len(processed_logs),
            'avg_word_count': sum(log.get('features', {}).get('word_count', 0) for log in processed_logs) / len(processed_logs),
        }
        
        # Level distribution
        level_counts = {}
        for log in processed_logs:
            level = log.get('level', 'UNKNOWN')
            level_counts[level] = level_counts.get(level, 0) + 1
        stats['level_distribution'] = level_counts
        
        # Component distribution
        component_counts = {}
        for log in processed_logs:
            component = log.get('component', 'unknown')
            component_counts[component] = component_counts.get(component, 0) + 1
        stats['component_distribution'] = component_counts
        
        return stats
    
    def _save_processed_logs(self, results: Dict[str, Any], output_path: Union[str, Path]):
        """Save processed logs to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Processed logs saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save processed logs: {e}")
    
    def get_preprocessing_summary(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable preprocessing summary."""
        stats = results.get('preprocessing_stats', {})
        
        summary = f"""
Log Preprocessing Summary
========================
File: {results.get('file_path', 'N/A')}
Total Lines: {results.get('total_lines', 0)}
Processed Lines: {results.get('processed_lines', 0)}
Empty Lines: {results.get('empty_lines', 0)}
Templates Found: {results.get('template_count', 0)}

Statistics:
- With Timestamp: {stats.get('with_timestamp', 0)}
- With Log Level: {stats.get('with_level', 0)}
- With Component: {stats.get('with_component', 0)}
- Error Logs: {stats.get('error_logs', 0)}
- Warning Logs: {stats.get('warning_logs', 0)}
- Avg Line Length: {stats.get('avg_line_length', 0):.1f}
- Avg Word Count: {stats.get('avg_word_count', 0):.1f}

Level Distribution:
{self._format_distribution(stats.get('level_distribution', {}))}

Component Distribution:
{self._format_distribution(stats.get('component_distribution', {}))}
        """.strip()
        
        return summary
    
    def _format_distribution(self, distribution: Dict[str, int]) -> str:
        """Format distribution dictionary for display."""
        if not distribution:
            return "  No data"
        
        sorted_items = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for key, count in sorted_items[:10]:  # Show top 10
            lines.append(f"  {key}: {count}")
        
        if len(sorted_items) > 10:
            lines.append(f"  ... and {len(sorted_items) - 10} more")
        
        return "\n".join(lines)
