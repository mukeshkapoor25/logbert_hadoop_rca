"""
AI Agent-Based API Routes for LogBERT Hadoop RCA

This module defines all the API endpoints using AI agents for distributed
processing and intelligent analysis.
"""

import io
import time
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse

try:
    import pandas as pd
except ImportError:
    pd = None

from ..models.schemas import (
    LogAnalysisRequest,
    LogAnalysisResponse,
    AnomalyDetectionResponse,
    RCAResponse,
    HealthResponse,
    ModelInfo,
)
# Import AI agents
from ..agents import (
    CoordinatorAgent,
    AnomalyDetectionAgent,
    RootCauseAgent,
    LogParserAgent,
    ExplanationAgent
)
from ..utils.logging import setup_logging

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize AI agents (these would be dependency-injected in production)
coordinator_agent = None
anomaly_agent = None
rca_agent = None
parser_agent = None
explanation_agent = None


async def get_coordinator_agent() -> CoordinatorAgent:
    """Dependency to get the coordinator agent."""
    global coordinator_agent
    if coordinator_agent is None:
        coordinator_agent = CoordinatorAgent(
            config={
                "enable_parallel_processing": True,
                "max_retries": 3,
                "timeout_seconds": 300,
                "anomaly_detection": {
                    "threshold": 0.5,
                    "model_name": "logbert_hadoop"
                },
                "root_cause_analysis": {
                    "context_window": 10,
                    "min_confidence": 0.6
                },
                "explanation": {
                    "explanation_style": "technical",
                    "include_code_examples": True
                }
            }
        )
    return coordinator_agent


async def get_anomaly_agent() -> AnomalyDetectionAgent:
    """Dependency to get the anomaly detection agent."""
    global anomaly_agent
    if anomaly_agent is None:
        anomaly_agent = AnomalyDetectionAgent(
            config={
                "threshold": 0.5,
                "model_name": "logbert_hadoop"
            }
        )
    return anomaly_agent


async def get_rca_agent() -> RootCauseAgent:
    """Dependency to get the root cause analysis agent."""
    global rca_agent
    if rca_agent is None:
        rca_agent = RootCauseAgent(
            config={
                "context_window": 10,
                "min_confidence": 0.6
            }
        )
    return rca_agent


async def get_parser_agent() -> LogParserAgent:
    """Dependency to get the log parser agent."""
    global parser_agent
    if parser_agent is None:
        parser_agent = LogParserAgent(
            config={
                "supported_formats": ["hadoop", "hdfs", "yarn", "generic"]
            }
        )
    return parser_agent


async def get_explanation_agent() -> ExplanationAgent:
    """Dependency to get the explanation agent."""
    global explanation_agent
    if explanation_agent is None:
        explanation_agent = ExplanationAgent(
            config={
                "explanation_style": "technical",
                "language_model": "mistral-7b"
            }
        )
    return explanation_agent


@router.post("/analyze", response_model=LogAnalysisResponse)
async def analyze_logs(
    request: LogAnalysisRequest,
    coordinator: CoordinatorAgent = Depends(get_coordinator_agent),
    background_tasks: BackgroundTasks = None,
) -> LogAnalysisResponse:
    """
    Analyze log text for anomalies and perform root cause analysis using AI agents.
    
    This endpoint orchestrates multiple AI agents to provide comprehensive log analysis:
    - Log parsing and preprocessing
    - Anomaly detection using LogBERT
    - Root cause analysis
    - Human-readable explanations
    
    Args:
        request: Log analysis request containing log text and options
        coordinator: Coordinator agent that orchestrates the analysis pipeline
        background_tasks: Background tasks for async operations
        
    Returns:
        Complete analysis results including anomalies, root causes, and explanations
    """
    try:
        logger.info(f"Starting AI agent-based log analysis for {len(request.log_text)} characters")
        
        # Prepare input for coordinator agent
        agent_input = {
            "log_text": request.log_text,
            "threshold": request.threshold,
            "model_name": request.model_name,
            "context_window": request.context_window,
            "include_rca": request.include_rca,
            "include_explanation": True,  # Always include explanations
            "explanation_style": "technical",
            "metadata": request.metadata or {}
        }
        
        # Execute the AI agent pipeline
        coordinator_response = await coordinator.execute(agent_input)
        
        if coordinator_response.status.value != "completed":
            raise Exception(f"Coordinator agent failed: {coordinator_response.error}")
        
        # Extract results from coordinator response
        pipeline_results = coordinator_response.result
        
        # Build the API response from agent results
        anomaly_data = pipeline_results.get("anomaly_detection", {})
        rca_data = pipeline_results.get("root_cause_analysis", {})
        explanation_data = pipeline_results.get("explanation", {})
        
        # Create anomaly detection response
        anomaly_response = AnomalyDetectionResponse(
            anomalies_detected=anomaly_data.get("anomalies_detected", False),
            total_anomalies=anomaly_data.get("anomaly_count", 0),
            anomalies=anomaly_data.get("anomalies", []),
            processing_time_ms=coordinator_response.processing_time_ms,
            model_version=request.model_name,
            threshold_used=request.threshold,
            statistics=anomaly_data.get("processing_statistics", {})
        )
        
        # Create RCA response if available
        rca_response = None
        if rca_data and rca_data.get("root_causes_found", False):
            rca_response = RCAResponse(
                root_causes_found=rca_data.get("root_causes_found", False),
                total_root_causes=rca_data.get("root_cause_count", 0),
                root_causes=rca_data.get("root_causes", []),
                processing_time_ms=coordinator_response.processing_time_ms,
                confidence_score=0.8,  # Could be calculated from individual confidences
                analysis_summary=rca_data.get("analysis_summary", "")
            )
        
        # Create the complete response
        response = LogAnalysisResponse(
            analysis_id=pipeline_results.get("analysis_id", f"analysis_{int(time.time())}"),
            status=pipeline_results.get("status", "completed"),
            anomaly_detection=anomaly_response,
            root_cause_analysis=rca_response,
            processing_time_ms=coordinator_response.processing_time_ms,
            metadata={
                "agent_coordination": {
                    "coordinator_id": coordinator.agent_id,
                    "pipeline_steps": coordinator_response.metadata.get("pipeline_steps", []),
                    "total_agents_used": coordinator_response.metadata.get("total_agents_used", 0)
                },
                "model_version": request.model_name,
                "timestamp": str(datetime.utcnow()),
                "input_size": len(request.log_text),
                "explanation_summary": explanation_data.get("summary", "") if explanation_data else "",
                "system_health_score": explanation_data.get("insights", {}).get("system_health_score", 0.8) if explanation_data else 0.8
            }
        )
        
        logger.info(f"AI agent analysis completed: {response.analysis_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error during AI agent log analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"AI agent analysis failed: {str(e)}"
        )


@router.post("/upload", response_model=LogAnalysisResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    threshold: float = 0.5,
    model_name: str = "logbert_hadoop",
    context_window: int = 10,
    explanation_style: str = "technical",
    coordinator: CoordinatorAgent = Depends(get_coordinator_agent),
) -> LogAnalysisResponse:
    """
    Upload a log file and analyze it using AI agents.
    
    Args:
        file: Uploaded log file
        threshold: Anomaly detection threshold (0.0-1.0)
        model_name: Name of the model to use
        context_window: Context window size for RCA
        explanation_style: Style of explanations (technical, management, brief)
        coordinator: Coordinator agent for orchestrating analysis
        
    Returns:
        Complete analysis results
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.log', '.txt')):
            raise HTTPException(
                status_code=400,
                detail="Only .log and .txt files are supported"
            )
        
        # Read file content
        content = await file.read()
        log_text = content.decode('utf-8')
        
        logger.info(f"Processing uploaded file: {file.filename} ({len(log_text)} chars)")
        
        # Create request object
        request = LogAnalysisRequest(
            log_text=log_text,
            threshold=threshold,
            model_name=model_name,
            context_window=context_window,
            metadata={"source_file": file.filename}
        )
        
        # Perform analysis using coordinator agent
        return await analyze_logs(request, coordinator)
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded text"
        )
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {str(e)}"
        )


@router.post("/detect-anomalies", response_model=AnomalyDetectionResponse)
async def detect_anomalies_only(
    request: LogAnalysisRequest,
    anomaly_agent: AnomalyDetectionAgent = Depends(get_anomaly_agent),
) -> AnomalyDetectionResponse:
    """
    Perform only anomaly detection without root cause analysis using specialized agent.
    
    Args:
        request: Log analysis request
        anomaly_agent: Anomaly detection agent
        
    Returns:
        Anomaly detection results
    """
    try:
        logger.info("Starting anomaly detection only using AI agent")
        
        # Prepare input for anomaly agent
        agent_input = {
            "log_text": request.log_text,
            "threshold": request.threshold,
            "model_name": request.model_name
        }
        
        # Execute anomaly detection agent
        agent_response = await anomaly_agent.execute(agent_input)
        
        if agent_response.status.value != "completed":
            raise Exception(f"Anomaly detection agent failed: {agent_response.error}")
        
        # Extract results
        anomaly_data = agent_response.result
        
        # Create response
        response = AnomalyDetectionResponse(
            anomalies_detected=anomaly_data.get("anomalies_detected", False),
            total_anomalies=anomaly_data.get("anomaly_count", 0),
            anomalies=anomaly_data.get("anomalies", []),
            processing_time_ms=agent_response.processing_time_ms,
            model_version=request.model_name,
            threshold_used=request.threshold,
            statistics=anomaly_data.get("processing_statistics", {})
        )
        
        logger.info(f"Anomaly detection completed: {response.total_anomalies} anomalies found")
        return response
        
    except Exception as e:
        logger.error(f"Error during anomaly detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Anomaly detection failed: {str(e)}"
        )


@router.post("/rca", response_model=RCAResponse)
async def root_cause_analysis_only(
    log_text: str,
    anomalies: List[Dict[str, Any]],
    context_window: int = 10,
    rca_agent: RootCauseAgent = Depends(get_rca_agent),
) -> RCAResponse:
    """
    Perform root cause analysis on provided anomalies using specialized agent.
    
    Args:
        log_text: Original log text
        anomalies: List of detected anomalies
        context_window: Context window for analysis
        rca_agent: Root cause analysis agent
        
    Returns:
        Root cause analysis results
    """
    try:
        logger.info(f"Starting RCA for {len(anomalies)} anomalies using AI agent")
        
        # Prepare input for RCA agent
        agent_input = {
            "log_text": log_text,
            "anomalies": anomalies,
            "context_window": context_window
        }
        
        # Execute RCA agent
        agent_response = await rca_agent.execute(agent_input)
        
        if agent_response.status.value != "completed":
            raise Exception(f"RCA agent failed: {agent_response.error}")
        
        # Extract results
        rca_data = agent_response.result
        
        # Create response
        response = RCAResponse(
            root_causes_found=rca_data.get("root_causes_found", False),
            total_root_causes=rca_data.get("root_cause_count", 0),
            root_causes=rca_data.get("root_causes", []),
            processing_time_ms=agent_response.processing_time_ms,
            confidence_score=0.8,  # Could be calculated from individual confidences
            analysis_summary=rca_data.get("analysis_summary", "")
        )
        
        logger.info(f"RCA completed: {response.total_root_causes} causes identified")
        return response
        
    except Exception as e:
        logger.error(f"Error during RCA: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Root cause analysis failed: {str(e)}"
        )


@router.get("/models", response_model=List[ModelInfo])
async def list_available_models(
    anomaly_agent: AnomalyDetectionAgent = Depends(get_anomaly_agent),
) -> List[ModelInfo]:
    """
    Get list of available models and their information.
    
    Returns:
        List of available models with metadata
    """
    try:
        # Mock model information - in production would query actual model registry
        models = [
            ModelInfo(
                id="logbert_hadoop_v1",
                name="LogBERT Hadoop v1.0",
                description="LogBERT model trained on Hadoop ecosystem logs",
                version="1.0.0",
                type="anomaly_detection",
                supported_formats=["hadoop", "hdfs", "yarn"],
                performance_metrics={
                    "accuracy": 0.94,
                    "precision": 0.91,
                    "recall": 0.89,
                    "f1_score": 0.90
                },
                training_data_info={
                    "dataset_size": "500K log entries",
                    "training_date": "2023-06-15",
                    "data_sources": ["namenode", "datanode", "resourcemanager", "nodemanager"]
                }
            )
        ]
        return models
    except Exception as e:
        logger.error(f"Error listing models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list models: {str(e)}"
        )


@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model_info(
    model_name: str,
    anomaly_agent: AnomalyDetectionAgent = Depends(get_anomaly_agent),
) -> ModelInfo:
    """
    Get detailed information about a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Model information and metadata
    """
    try:
        # Mock model info - in production would query model registry
        if model_name.startswith("logbert"):
            model_info = ModelInfo(
                id=model_name,
                name=f"LogBERT Model {model_name}",
                description=f"LogBERT model for log anomaly detection: {model_name}",
                version="1.0.0",
                type="anomaly_detection",
                supported_formats=["hadoop", "hdfs", "yarn", "generic"],
                performance_metrics={
                    "accuracy": 0.94,
                    "precision": 0.91,
                    "recall": 0.89,
                    "f1_score": 0.90
                }
            )
            return model_info
        else:
            raise ValueError(f"Model not found: {model_name}")
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found: {model_name}"
        )
    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.post("/batch-analyze")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    threshold: float = 0.5,
    model_name: str = "logbert_hadoop",
    background_tasks: BackgroundTasks = None,
    coordinator: CoordinatorAgent = Depends(get_coordinator_agent),
) -> JSONResponse:
    """
    Analyze multiple log files in batch mode using AI agents.
    
    Args:
        files: List of uploaded log files
        threshold: Anomaly detection threshold
        model_name: Model to use for analysis
        background_tasks: Background tasks for async processing
        coordinator: Coordinator agent for orchestrating analysis
        
    Returns:
        Batch job ID and status
    """
    try:
        if len(files) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 files allowed per batch"
            )
        
        # Generate batch job ID
        batch_id = f"batch_{int(time.time())}"
        
        # Schedule background processing
        if background_tasks:
            background_tasks.add_task(
                process_batch_files_with_agents,
                batch_id,
                files,
                threshold,
                model_name,
                coordinator,
            )
        
        logger.info(f"Started batch analysis: {batch_id} with {len(files)} files")
        
        return JSONResponse(
            content={
                "batch_id": batch_id,
                "status": "processing",
                "file_count": len(files),
                "estimated_completion_time": "5-10 minutes",
                "coordinator_agent_id": coordinator.agent_id,
                "processing_mode": "ai_agents"
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting batch analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse)
async def health_check(
    coordinator: CoordinatorAgent = Depends(get_coordinator_agent),
) -> HealthResponse:
    """
    Health check endpoint for the AI agent-based API.
    
    Returns:
        Health status of the system and all agents
    """
    try:
        # Get status of all agents (this is not async)
        pipeline_status = coordinator.get_pipeline_status()
        
        # Extract sub-agents from pipeline status
        sub_agents = {
            key: value for key, value in pipeline_status.items() 
            if key != "coordinator_status"
        }
        
        # Determine overall health
        all_agents_healthy = all(
            agent_info.get("status") in ["active", "initialized"] 
            for agent_info in sub_agents.values()
            if agent_info is not None
        )
        
        return HealthResponse(
            status="healthy" if all_agents_healthy else "degraded",
            timestamp=datetime.utcnow().isoformat(),
            version="2.0.0-ai-agents",
            environment="development",  # Could be read from settings
            uptime_seconds=time.time(),  # Mock uptime
            details={
                "ai_agents": {
                    "coordinator_status": pipeline_status.get("coordinator", {}).get("status", "unknown"),
                    "sub_agents_count": len([
                        agent for agent in sub_agents.values()
                        if agent is not None
                    ]),
                    "pipeline_health": "operational" if all_agents_healthy else "degraded"
                },
                "system": {
                    "memory_usage": "Normal",
                    "cpu_usage": "Normal",
                    "disk_space": "Available"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            version="2.0.0-ai-agents",
            environment="development",
            uptime_seconds=0,
            details={
                "error": str(e),
                "ai_agents": {"status": "failed"}
            }
        )


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str) -> JSONResponse:
    """
    Get status of a batch analysis job processed by AI agents.
    
    Args:
        batch_id: Batch job ID
        
    Returns:
        Batch job status and results
    """
    try:
        # In a real implementation, this would check a database or cache
        # For now, return a mock response with AI agent information
        return JSONResponse(
            content={
                "batch_id": batch_id,
                "status": "completed",
                "progress": 100,
                "files_processed": 5,
                "files_total": 5,
                "processing_method": "ai_agents",
                "agent_statistics": {
                    "total_processing_time_ms": 15000,
                    "average_file_processing_time_ms": 3000,
                    "agents_used": ["coordinator", "parser", "anomaly_detection", "rca", "explanation"]
                },
                "results_url": f"/api/v1/batch/{batch_id}/results",
            }
        )
    except Exception as e:
        logger.error(f"Error getting batch status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch status: {str(e)}"
        )


async def process_batch_files_with_agents(
    batch_id: str,
    files: List[UploadFile],
    threshold: float,
    model_name: str,
    coordinator: CoordinatorAgent,
):
    """
    Background task to process batch files using AI agents.
    
    Args:
        batch_id: Batch job ID
        files: List of files to process
        threshold: Anomaly detection threshold
        model_name: Model name to use
        coordinator: Coordinator agent for processing
    """
    try:
        logger.info(f"Processing batch {batch_id} with {len(files)} files using AI agents")
        
        # Process each file
        results = []
        for i, file in enumerate(files):
            try:
                # Read and analyze file
                content = await file.read()
                log_text = content.decode('utf-8')
                
                # Create analysis request
                agent_input = {
                    "log_text": log_text,
                    "threshold": threshold,
                    "model_name": model_name,
                    "context_window": 10,
                    "include_rca": True,
                    "include_explanation": True,
                    "metadata": {"batch_id": batch_id, "file_name": file.filename}
                }
                
                # Perform analysis using coordinator agent
                coordinator_response = await coordinator.execute(agent_input)
                
                if coordinator_response.status.value == "completed":
                    results.append({
                        "filename": file.filename,
                        "status": "success",
                        "analysis": coordinator_response.result,
                        "agent_metadata": {
                            "coordinator_id": coordinator.agent_id,
                            "processing_time_ms": coordinator_response.processing_time_ms,
                            "pipeline_steps": coordinator_response.metadata.get("pipeline_steps", [])
                        }
                    })
                else:
                    results.append({
                        "filename": file.filename,
                        "status": "error",
                        "error": coordinator_response.error,
                        "agent_metadata": {
                            "coordinator_id": coordinator.agent_id,
                            "processing_time_ms": coordinator_response.processing_time_ms
                        }
                    })
                
                logger.info(f"Processed file {i+1}/{len(files)}: {file.filename}")
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {e}")
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "error": str(e),
                })
        
        # Store results (in production, this would go to a database)
        # For now, just log the completion
        logger.info(f"Batch {batch_id} completed: {len(results)} files processed with AI agents")
        
    except Exception as e:
        logger.error(f"Error in batch processing with AI agents: {e}", exc_info=True)


# AI Agent Management Endpoints

@router.get("/agents/status")
async def get_agents_status(
    coordinator: CoordinatorAgent = Depends(get_coordinator_agent),
) -> JSONResponse:
    """
    Get status of all AI agents in the system.
    
    Returns:
        Status information for all agents
    """
    try:
        status = coordinator.get_pipeline_status()
        return JSONResponse(content=status)
    except Exception as e:
        logger.error(f"Error getting agent status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/agents/configure")
async def configure_agents(
    config: Dict[str, Any],
    coordinator: CoordinatorAgent = Depends(get_coordinator_agent),
) -> JSONResponse:
    """
    Configure AI agents with new parameters.
    
    Args:
        config: Configuration dictionary for agents
        
    Returns:
        Configuration status
    """
    try:
        # Update coordinator configuration
        coordinator.config.update(config)
        
        logger.info("Agent configuration updated successfully")
        return JSONResponse(content={
            "status": "success",
            "message": "Agent configuration updated",
            "coordinator_id": coordinator.agent_id,
            "updated_config": config
        })
    except Exception as e:
        logger.error(f"Error configuring agents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure agents: {str(e)}"
        )


@router.post("/explain")
async def generate_explanation(
    log_text: str,
    anomalies: List[Dict[str, Any]],
    root_causes: List[Dict[str, Any]],
    explanation_style: str = "technical",
    explanation_agent: ExplanationAgent = Depends(get_explanation_agent),
) -> JSONResponse:
    """
    Generate explanations for anomalies and root causes.
    
    Args:
        log_text: Original log text
        anomalies: List of detected anomalies
        root_causes: List of identified root causes
        explanation_style: Style of explanation (technical, management, brief)
        explanation_agent: Explanation agent
        
    Returns:
        Generated explanations and insights
    """
    try:
        logger.info(f"Generating explanations for {len(anomalies)} anomalies and {len(root_causes)} root causes")
        
        # Prepare input for explanation agent
        agent_input = {
            "log_text": log_text,
            "anomalies": anomalies,
            "root_causes": root_causes,
            "explanation_style": explanation_style
        }
        
        # Execute explanation agent
        agent_response = await explanation_agent.execute(agent_input)
        
        if agent_response.status.value != "completed":
            raise Exception(f"Explanation agent failed: {agent_response.error}")
        
        # Return explanation results
        return JSONResponse(content={
            "status": "success",
            "explanations": agent_response.result,
            "processing_time_ms": agent_response.processing_time_ms,
            "agent_metadata": {
                "agent_id": explanation_agent.agent_id,
                "explanation_style": explanation_style
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating explanations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Explanation generation failed: {str(e)}"
        )


@router.post("/parse")
async def parse_logs(
    log_text: str,
    format_hint: str = "auto",
    preserve_raw: bool = True,
    parser_agent: LogParserAgent = Depends(get_parser_agent),
) -> JSONResponse:
    """
    Parse raw log text into structured format.
    
    Args:
        log_text: Raw log text to parse
        format_hint: Format hint (hadoop, hdfs, yarn, auto)
        preserve_raw: Whether to preserve raw log entries
        parser_agent: Log parser agent
        
    Returns:
        Parsed log data
    """
    try:
        logger.info(f"Parsing {len(log_text)} characters of log text")
        
        # Prepare input for parser agent
        agent_input = {
            "log_text": log_text,
            "format_hint": format_hint,
            "preserve_raw": preserve_raw
        }
        
        # Execute parser agent
        agent_response = await parser_agent.execute(agent_input)
        
        if agent_response.status.value != "completed":
            raise Exception(f"Parser agent failed: {agent_response.error}")
        
        # Return parsing results
        return JSONResponse(content={
            "status": "success",
            "parsed_data": agent_response.result,
            "processing_time_ms": agent_response.processing_time_ms,
            "agent_metadata": {
                "agent_id": parser_agent.agent_id,
                "format_hint": format_hint
            }
        })
        
    except Exception as e:
        logger.error(f"Error parsing logs: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Log parsing failed: {str(e)}"
        )


@router.get("/activity/recent")
async def get_recent_activity() -> JSONResponse:
    """
    Get recent activity (basic implementation).
    """
    try:
        return JSONResponse(content=[
            {
                "type": "analysis",
                "description": "Log analysis completed: 2 anomalies found",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "type": "agent_restart",
                "description": "Coordinator agent restarted",
                "timestamp": datetime.utcnow().isoformat()
            }
        ])
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent activity: {str(e)}"
        )
