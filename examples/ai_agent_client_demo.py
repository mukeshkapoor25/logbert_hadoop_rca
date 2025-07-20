"""
Example Client for AI Agent-based LogBERT Hadoop RCA API

This script demonstrates how to interact with the new AI agent-based API
for log analysis, anomaly detection, and root cause analysis.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List


class LogBERTAIAgentClient:
    """
    Client for interacting with the AI agent-based LogBERT API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000/api"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def analyze_logs(
        self,
        log_text: str,
        threshold: float = 0.5,
        model_name: str = "logbert_hadoop",
        context_window: int = 10,
        include_rca: bool = True
    ) -> Dict[str, Any]:
        """
        Perform complete log analysis using AI agents.
        
        Args:
            log_text: Raw log text to analyze
            threshold: Anomaly detection threshold
            model_name: Model name to use
            context_window: Context window for RCA
            include_rca: Whether to include root cause analysis
            
        Returns:
            Complete analysis results
        """
        url = f"{self.base_url}/analyze"
        payload = {
            "log_text": log_text,
            "threshold": threshold,
            "model_name": model_name,
            "context_window": context_window,
            "include_rca": include_rca
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API call failed: {response.status} - {await response.text()}")
    
    async def detect_anomalies_only(
        self,
        log_text: str,
        threshold: float = 0.5,
        model_name: str = "logbert_hadoop"
    ) -> Dict[str, Any]:
        """
        Perform only anomaly detection using AI agents.
        
        Args:
            log_text: Raw log text to analyze
            threshold: Anomaly detection threshold
            model_name: Model name to use
            
        Returns:
            Anomaly detection results
        """
        url = f"{self.base_url}/detect-anomalies"
        payload = {
            "log_text": log_text,
            "threshold": threshold,
            "model_name": model_name
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API call failed: {response.status} - {await response.text()}")
    
    async def perform_rca(
        self,
        log_text: str,
        anomalies: List[Dict[str, Any]],
        context_window: int = 10
    ) -> Dict[str, Any]:
        """
        Perform root cause analysis on detected anomalies.
        
        Args:
            log_text: Original log text
            anomalies: List of detected anomalies
            context_window: Context window for analysis
            
        Returns:
            Root cause analysis results
        """
        url = f"{self.base_url}/rca"
        payload = {
            "log_text": log_text,
            "anomalies": anomalies,
            "context_window": context_window
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API call failed: {response.status} - {await response.text()}")
    
    async def generate_explanation(
        self,
        log_text: str,
        anomalies: List[Dict[str, Any]],
        root_causes: List[Dict[str, Any]],
        explanation_style: str = "technical"
    ) -> Dict[str, Any]:
        """
        Generate explanations for anomalies and root causes.
        
        Args:
            log_text: Original log text
            anomalies: List of detected anomalies
            root_causes: List of identified root causes
            explanation_style: Style of explanation (technical, management, brief)
            
        Returns:
            Generated explanations and insights
        """
        url = f"{self.base_url}/explain"
        payload = {
            "log_text": log_text,
            "anomalies": anomalies,
            "root_causes": root_causes,
            "explanation_style": explanation_style
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API call failed: {response.status} - {await response.text()}")
    
    async def parse_logs(
        self,
        log_text: str,
        format_hint: str = "auto",
        preserve_raw: bool = True
    ) -> Dict[str, Any]:
        """
        Parse raw log text into structured format.
        
        Args:
            log_text: Raw log text to parse
            format_hint: Format hint (hadoop, hdfs, yarn, auto)
            preserve_raw: Whether to preserve raw log entries
            
        Returns:
            Parsed log data
        """
        url = f"{self.base_url}/parse"
        payload = {
            "log_text": log_text,
            "format_hint": format_hint,
            "preserve_raw": preserve_raw
        }
        
        async with self.session.post(url, json=payload) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API call failed: {response.status} - {await response.text()}")
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """
        Get status of all AI agents.
        
        Returns:
            Agent status information
        """
        url = f"{self.base_url}/agents/status"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API call failed: {response.status} - {await response.text()}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the API and agents.
        
        Returns:
            Health status information
        """
        url = f"{self.base_url}/health"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API call failed: {response.status} - {await response.text()}")


async def demo_ai_agent_workflow():
    """
    Demonstrate the AI agent-based log analysis workflow.
    """
    # Sample log data for demonstration
    sample_log_text = """
2023-07-19 10:00:01 INFO org.apache.hadoop.hdfs.server.namenode.NameNode: STARTUP_MSG: Starting NameNode
2023-07-19 10:00:02 INFO org.apache.hadoop.hdfs.server.namenode.NameNode: STARTUP_MSG: args = []
2023-07-19 10:00:05 ERROR org.apache.hadoop.hdfs.server.namenode.NameNode: Connection timeout to datanode 192.168.1.10
2023-07-19 10:00:06 WARN org.apache.hadoop.hdfs.server.datanode.DataNode: Slow block report from datanode
2023-07-19 10:00:10 ERROR org.apache.hadoop.yarn.server.resourcemanager.ResourceManager: Failed to connect to NodeManager
2023-07-19 10:00:15 INFO org.apache.hadoop.hdfs.server.namenode.NameNode: Registered datanode 192.168.1.11
2023-07-19 10:00:20 ERROR java.net.ConnectException: Connection refused: connect
2023-07-19 10:00:25 WARN org.apache.hadoop.util.NativeCodeLoader: Unable to load native-hadoop library
"""
    
    async with LogBERTAIAgentClient() as client:
        print("🤖 AI Agent-based LogBERT Hadoop RCA Demo")
        print("=" * 50)
        
        # 1. Health Check
        print("\n1. 🏥 Health Check")
        try:
            health = await client.health_check()
            print(f"   System Status: {health['status']}")
            print(f"   AI Agents: {health['details']['ai_agents']}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
        
        # 2. Agent Status
        print("\n2. 📊 Agent Status")
        try:
            status = await client.get_agent_status()
            print(f"   Coordinator Status: {status['coordinator_status']}")
            print(f"   Sub-agents Available: {len([a for a in status['sub_agents'].values() if a])}")
        except Exception as e:
            print(f"   ❌ Agent status check failed: {e}")
        
        # 3. Log Parsing
        print("\n3. 📝 Log Parsing")
        try:
            parsed_result = await client.parse_logs(
                log_text=sample_log_text,
                format_hint="hadoop"
            )
            parsed_data = parsed_result['parsed_data']
            print(f"   Parsed Entries: {parsed_data['parsing_statistics']['parsed_entries']}")
            print(f"   Detected Format: {parsed_data['metadata']['detected_format']}")
        except Exception as e:
            print(f"   ❌ Log parsing failed: {e}")
        
        # 4. Anomaly Detection Only
        print("\n4. 🔍 Anomaly Detection")
        try:
            anomaly_result = await client.detect_anomalies_only(
                log_text=sample_log_text,
                threshold=0.6
            )
            print(f"   Anomalies Detected: {anomaly_result['anomalies_detected']}")
            print(f"   Total Anomalies: {anomaly_result['total_anomalies']}")
            if anomaly_result['anomalies_detected']:
                for i, anomaly in enumerate(anomaly_result['anomalies'][:3], 1):
                    print(f"   Anomaly {i}: {anomaly['anomaly_type']} (Score: {anomaly['anomaly_score']:.2f})")
        except Exception as e:
            print(f"   ❌ Anomaly detection failed: {e}")
        
        # 5. Complete Analysis
        print("\n5. 🔬 Complete AI Agent Analysis")
        try:
            complete_result = await client.analyze_logs(
                log_text=sample_log_text,
                threshold=0.5,
                include_rca=True
            )
            
            # Display results
            analysis_meta = complete_result['metadata']['agent_coordination']
            print(f"   Analysis ID: {complete_result['analysis_id']}")
            print(f"   Coordinator Agent: {analysis_meta['coordinator_id']}")
            print(f"   Pipeline Steps: {', '.join(analysis_meta['pipeline_steps'])}")
            print(f"   Total Processing Time: {complete_result['processing_time_ms']:.2f}ms")
            
            # Anomaly results
            anomaly_data = complete_result['anomaly_detection']
            print(f"   Anomalies Found: {anomaly_data['total_anomalies']}")
            
            # RCA results
            if complete_result.get('root_cause_analysis'):
                rca_data = complete_result['root_cause_analysis']
                print(f"   Root Causes Identified: {rca_data['total_root_causes']}")
                print(f"   Analysis Summary: {rca_data['analysis_summary'][:100]}...")
            
            # System health
            health_score = complete_result['metadata'].get('system_health_score', 0)
            print(f"   System Health Score: {health_score:.2f}")
            
        except Exception as e:
            print(f"   ❌ Complete analysis failed: {e}")
        
        # 6. Generate Explanations
        print("\n6. 💬 Generate Explanations")
        try:
            if 'complete_result' in locals() and complete_result.get('anomaly_detection', {}).get('anomalies'):
                explanation_result = await client.generate_explanation(
                    log_text=sample_log_text,
                    anomalies=complete_result['anomaly_detection']['anomalies'],
                    root_causes=complete_result.get('root_cause_analysis', {}).get('root_causes', []),
                    explanation_style="management"
                )
                
                explanations = explanation_result['explanations']
                print(f"   Summary: {explanations['summary'][:150]}...")
                print(f"   Recommendations: {len(explanations['recommendations']['immediate'])} immediate actions")
                print(f"   System Health Score: {explanations['insights']['system_health_score']:.2f}")
        except Exception as e:
            print(f"   ❌ Explanation generation failed: {e}")
        
        print("\n🎉 AI Agent Demo Complete!")


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demo_ai_agent_workflow())
