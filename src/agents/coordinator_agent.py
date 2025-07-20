"""
Coordinator Agent

This agent orchestrates the entire log analysis pipeline by coordinating
multiple specialized agents and managing the overall workflow.
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from .base_agent import BaseAgent, AgentResponse, AgentStatus, AgentCapability
from .anomaly_detection_agent import AnomalyDetectionAgent
from .root_cause_agent import RootCauseAgent
from .log_parser_agent import LogParserAgent
from .explanation_agent import ExplanationAgent


class CoordinatorAgent(BaseAgent):
    """
    AI Agent that coordinates the entire log analysis pipeline.
    
    This agent:
    - Orchestrates multiple specialized agents
    - Manages the analysis workflow
    - Handles agent communication and data flow
    - Provides comprehensive analysis results
    """
    
    def __init__(
        self, 
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        capabilities = [
            AgentCapability.COORDINATION
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name or "CoordinatorAgent",
            capabilities=capabilities,
            config=config or {}
        )
        
        # Initialize sub-agents as None (will be set in _initialize)
        self.log_parser_agent = None
        self.anomaly_agent = None
        self.rca_agent = None
        self.explanation_agent = None
        
        # Pipeline configuration
        self.parallel_processing = self.config.get("parallel_processing", True)
        self.max_retries = self.config.get("max_retries", 3)
        self.timeout_seconds = self.config.get("timeout_seconds", 300)
        
    def _initialize(self):
        """Initialize the coordinator and sub-agents."""
        try:
            self.logger.info("Initializing coordinator agent and sub-agents")
            
            # Initialize sub-agents
            self.log_parser_agent = LogParserAgent(
                config=self.config.get("log_parser", {})
            )
            
            self.anomaly_agent = AnomalyDetectionAgent(
                config=self.config.get("anomaly_detection", {})
            )
            
            self.rca_agent = RootCauseAgent(
                config=self.config.get("root_cause_analysis", {})
            )
            
            self.explanation_agent = ExplanationAgent(
                config=self.config.get("explanation", {})
            )
            
            self.logger.info("All sub-agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize coordinator agent: {e}")
            raise
    
    async def process(self, input_data: Dict[str, Any], **kwargs) -> AgentResponse:
        """
        Coordinate the complete log analysis pipeline.
        
        Args:
            input_data: Dict containing:
                - log_text: The log content to analyze
                - include_rca: Whether to perform root cause analysis
                - include_explanation: Whether to generate explanations
                - context_window: Number of lines for context
                
        Returns:
            AgentResponse with comprehensive analysis results
        """
        try:
            self.logger.info("Starting coordinated log analysis pipeline")
            
            log_text = input_data.get("log_text", "")
            include_rca = input_data.get("include_rca", True)
            include_explanation = input_data.get("include_explanation", True)
            
            if not log_text:
                raise ValueError("log_text is required for analysis")
            
            self.logger.info("Starting coordinated log analysis pipeline")
            
            # Debug: Check if agents are initialized
            self.logger.debug(f"log_parser_agent: {self.log_parser_agent}")
            self.logger.debug(f"anomaly_agent: {self.anomaly_agent}")
            self.logger.debug(f"rca_agent: {self.rca_agent}")
            self.logger.debug(f"explanation_agent: {self.explanation_agent}")
            
            # Step 1: Log Parsing and Preprocessing
            parsing_result = await self._execute_with_retry(
                self.log_parser_agent.process,
                input_data,
                "log_parsing"
            )
            pipeline_results = {"parsing": parsing_result}
            
            if parsing_result.status == AgentStatus.FAILED:
                raise Exception(f"Log parsing failed: {parsing_result.error}")
            
            # Step 2: Anomaly Detection
            anomaly_input = {
                **input_data,
                "parsed_logs": parsing_result.result.get("parsed_logs", [])
            }
            
            anomaly_result = await self._execute_with_retry(
                self.anomaly_agent.process,
                anomaly_input,
                "anomaly_detection"
            )
            pipeline_results["anomaly_detection"] = anomaly_result
            
            if anomaly_result.status == AgentStatus.FAILED:
                raise Exception(f"Anomaly detection failed: {anomaly_result.error}")
            
            # Step 3: Root Cause Analysis (if requested and anomalies found)
            rca_result = None
            if include_rca and anomaly_result.result.get("anomalies_detected", False):
                rca_input = {
                    "log_text": log_text,
                    "anomalies": anomaly_result.result.get("anomalies", []),
                    "context_window": input_data.get("context_window", 10)
                }
                
                rca_result = await self._execute_with_retry(
                    self.rca_agent.process,
                    rca_input,
                    "root_cause_analysis"
                )
                pipeline_results["root_cause_analysis"] = rca_result
                
                if rca_result.status == AgentStatus.FAILED:
                    self.logger.warning(f"RCA failed: {rca_result.error}")
            
            # Step 4: Explanation Generation (if requested)
            explanation_result = None
            if include_explanation:
                explanation_input = {
                    "log_text": log_text,
                    "anomalies": anomaly_result.result.get("anomalies", []),
                    "root_causes": rca_result.result.get("root_causes", []) if rca_result else []
                }
                
                explanation_result = await self._execute_with_retry(
                    self.explanation_agent.process,
                    explanation_input,
                    "explanation_generation"
                )
                pipeline_results["explanation"] = explanation_result
                
                if explanation_result.status == AgentStatus.FAILED:
                    self.logger.warning(f"Explanation generation failed: {explanation_result.error}")
            
            # Compile final results
            final_results = {
                "analysis_summary": {
                    "total_logs_processed": len(parsing_result.result.get("parsed_logs", [])),
                    "anomalies_detected": anomaly_result.result.get("anomalies_detected", False),
                    "anomaly_count": len(anomaly_result.result.get("anomalies", [])),
                    "root_causes_identified": len(rca_result.result.get("root_causes", [])) if rca_result else 0,
                    "pipeline_status": "completed"
                },
                "parsed_logs": parsing_result.result.get("parsed_logs", []),
                "anomalies": anomaly_result.result.get("anomalies", []),
                "root_causes": rca_result.result.get("root_causes", []) if rca_result else [],
                "explanations": explanation_result.result.get("explanations", []) if explanation_result else [],
                "recommendations": explanation_result.result.get("recommendations", []) if explanation_result else [],
                "pipeline_results": pipeline_results
            }
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type="CoordinatorAgent",
                status=AgentStatus.SUCCESS,
                result=final_results,
                processing_time_ms=0,  # Will be updated by BaseAgent
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Pipeline coordination failed: {e}")
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type="CoordinatorAgent",
                status=AgentStatus.FAILED,
                error=str(e),
                processing_time_ms=0,
                timestamp=datetime.now().isoformat()
            )
    
    async def _execute_with_retry(
        self, 
        agent_method: Callable,
        input_data: Dict[str, Any],
        operation_name: str
    ) -> AgentResponse:
        """
        Execute an agent method with retry logic.
        
        Args:
            agent_method: The agent method to call
            input_data: Input data for the method
            operation_name: Name of the operation for logging
            
        Returns:
            AgentResponse from the operation
        """
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Executing {operation_name} (attempt {attempt + 1}/{self.max_retries})")
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    agent_method(input_data),
                    timeout=self.timeout_seconds
                )
                
                if result.status == AgentStatus.SUCCESS:
                    self.logger.debug(f"{operation_name} completed successfully")
                    return result
                else:
                    self.logger.warning(f"{operation_name} failed: {result.error}")
                    if attempt == self.max_retries - 1:
                        return result
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"{operation_name} timed out after {self.timeout_seconds}s (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return AgentResponse(
                        agent_id=self.agent_id,
                        agent_type="CoordinatorAgent",
                        status=AgentStatus.FAILED,
                        error=f"{operation_name} timed out after {self.timeout_seconds}s",
                        processing_time_ms=0,
                        timestamp=datetime.now().isoformat()
                    )
            except Exception as e:
                self.logger.error(f"{operation_name} failed with exception: {e} (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return AgentResponse(
                        agent_id=self.agent_id,
                        agent_type="CoordinatorAgent",
                        status=AgentStatus.FAILED,
                        error=str(e),
                        processing_time_ms=0,
                        timestamp=datetime.now().isoformat()
                    )
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                self.logger.debug(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        # This should not be reached, but just in case
        return AgentResponse(
            agent_id=self.agent_id,
            agent_type="CoordinatorAgent",
            status=AgentStatus.FAILED,
            error=f"{operation_name} failed after {self.max_retries} attempts",
            processing_time_ms=0,
            timestamp=datetime.now().isoformat()
        )
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get the current status of all sub-agents."""
        return {
            "coordinator": {
                "status": "active" if self.agent_id else "inactive",
                "agent_id": self.agent_id
            },
            "log_parser": {
                "status": "initialized" if self.log_parser_agent else "not_initialized",
                "agent_id": self.log_parser_agent.agent_id if self.log_parser_agent else None
            },
            "anomaly_detection": {
                "status": "initialized" if self.anomaly_agent else "not_initialized",
                "agent_id": self.anomaly_agent.agent_id if self.anomaly_agent else None
            },
            "root_cause_analysis": {
                "status": "initialized" if self.rca_agent else "not_initialized",
                "agent_id": self.rca_agent.agent_id if self.rca_agent else None
            },
            "explanation": {
                "status": "initialized" if self.explanation_agent else "not_initialized",
                "agent_id": self.explanation_agent.agent_id if self.explanation_agent else None
            }
        }
