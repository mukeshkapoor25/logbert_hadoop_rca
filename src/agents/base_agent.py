"""
Base Agent Class for AI Agent Architecture

This module defines the base class and common interfaces for all AI agents
in the LogBERT Hadoop RCA system.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
import uuid


class AgentStatus(str, Enum):
    """Status of an agent operation."""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentCapability(str, Enum):
    """Capabilities that agents can provide."""
    LOG_PARSING = "log_parsing"
    ANOMALY_DETECTION = "anomaly_detection"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"
    EXPLANATION_GENERATION = "explanation_generation"
    COORDINATION = "coordination"
    PREPROCESSING = "preprocessing"


class AgentResponse(BaseModel):
    """Response from an agent operation."""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent")
    status: AgentStatus = Field(..., description="Status of the operation")
    result: Optional[Dict[str, Any]] = Field(None, description="Operation result")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "anomaly_agent_001",
                "agent_type": "AnomalyDetectionAgent",
                "status": "completed",
                "result": {
                    "anomalies_detected": 3,
                    "anomalies": [...]
                },
                "error": None,
                "processing_time_ms": 1500.0,
                "metadata": {
                    "model_version": "1.0.0",
                    "confidence_threshold": 0.8
                },
                "timestamp": "2023-07-19T10:30:00.000Z"
            }
        }


class AgentMessage(BaseModel):
    """Message passed between agents."""
    sender_id: str = Field(..., description="ID of sending agent")
    receiver_id: str = Field(..., description="ID of receiving agent")
    message_type: str = Field(..., description="Type of message")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class BaseAgent(ABC):
    """
    Base class for all AI agents in the system.
    
    Agents are autonomous components that perform specific tasks in the
    log analysis pipeline. Each agent has its own capabilities and can
    communicate with other agents through a message passing system.
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.agent_id = agent_id or f"{self.__class__.__name__}_{uuid.uuid4().hex[:8]}"
        self.name = name or self.__class__.__name__
        self.capabilities = capabilities or []
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.start_time = None
        self.message_queue = asyncio.Queue()
        self.subscribers = set()
        
        # Initialize agent-specific components
        self._initialize()
    
    def _initialize(self):
        """Initialize agent-specific components. Override in subclasses."""
        pass
    
    @property
    def agent_type(self) -> str:
        """Get the agent type."""
        return self.__class__.__name__
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any], **kwargs) -> AgentResponse:
        """
        Main processing method for the agent.
        
        Args:
            input_data: Input data to process
            **kwargs: Additional processing parameters
            
        Returns:
            AgentResponse with processing results
        """
        pass
    
    async def execute(self, input_data: Dict[str, Any], **kwargs) -> AgentResponse:
        """
        Execute the agent's processing with proper error handling and timing.
        
        Args:
            input_data: Input data to process
            **kwargs: Additional processing parameters
            
        Returns:
            AgentResponse with processing results
        """
        self.start_time = time.time()
        self.status = AgentStatus.PROCESSING
        
        try:
            self.logger.info(f"Agent {self.agent_id} starting processing")
            
            # Validate input
            await self._validate_input(input_data)
            
            # Process the data
            response = await self.process(input_data, **kwargs)
            
            # Update status
            self.status = AgentStatus.COMPLETED
            response.status = AgentStatus.COMPLETED
            
            self.logger.info(f"Agent {self.agent_id} completed processing in {response.processing_time_ms}ms")
            return response
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            error_msg = f"Agent {self.agent_id} failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            processing_time = (time.time() - self.start_time) * 1000 if self.start_time else 0
            
            return AgentResponse(
                agent_id=self.agent_id,
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                error=error_msg,
                processing_time_ms=processing_time,
                metadata={"error_type": type(e).__name__}
            )
    
    async def _validate_input(self, input_data: Dict[str, Any]):
        """
        Validate input data. Override in subclasses for specific validation.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")
    
    def get_processing_time(self) -> float:
        """Get processing time in milliseconds."""
        if self.start_time is None:
            return 0.0
        return (time.time() - self.start_time) * 1000
    
    async def send_message(self, receiver_id: str, message_type: str, payload: Dict[str, Any]):
        """
        Send a message to another agent.
        
        Args:
            receiver_id: ID of receiving agent
            message_type: Type of message
            payload: Message payload
        """
        message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload
        )
        
        # In a real implementation, this would use a message broker
        self.logger.debug(f"Sending message from {self.agent_id} to {receiver_id}: {message_type}")
    
    async def receive_message(self) -> Optional[AgentMessage]:
        """
        Receive a message from the message queue.
        
        Returns:
            AgentMessage or None if no messages available
        """
        try:
            message = await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
            return message
        except asyncio.TimeoutError:
            return None
    
    def subscribe_to_agent(self, agent_id: str):
        """Subscribe to messages from another agent."""
        self.subscribers.add(agent_id)
    
    def unsubscribe_from_agent(self, agent_id: str):
        """Unsubscribe from messages from another agent."""
        self.subscribers.discard(agent_id)
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type,
            "capabilities": [cap.value for cap in self.capabilities],
            "status": self.status.value,
            "config": self.config,
            "processing_time_ms": self.get_processing_time()
        }
    
    def __str__(self) -> str:
        return f"{self.agent_type}(id={self.agent_id}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}', status='{self.status.value}')"
