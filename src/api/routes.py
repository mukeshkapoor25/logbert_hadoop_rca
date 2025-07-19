"""
API Routes for LogBERT Hadoop RCA

This module defines all the API endpoints for the LogBERT system.
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
# Import services lazily to avoid heavy dependencies
# from ..services.inference import LogBERTInference
# from ..services.rca import RootCauseAnalyzer
from ..utils.logging import setup_logging

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize services (these would be dependency-injected in production)
# For now, we'll use simple initialization
logbert_service = None
rca_service = None


async def get_logbert_service() -> LogBERTInference:
    """Dependency to get LogBERT inference service."""
    global logbert_service
    if logbert_service is None:
        logbert_service = LogBERTInference()
    return logbert_service


async def get_rca_service() -> RootCauseAnalyzer:
    """Dependency to get RCA service."""
    global rca_service
    if rca_service is None:
        rca_service = RootCauseAnalyzer()
    return rca_service


@router.post("/analyze", response_model=LogAnalysisResponse)
async def analyze_logs(
    request: LogAnalysisRequest,
    logbert: LogBERTInference = Depends(get_logbert_service),
    rca: RootCauseAnalyzer = Depends(get_rca_service),
    background_tasks: BackgroundTasks = None,
) -> LogAnalysisResponse:
    """
    Analyze log text for anomalies and perform root cause analysis.
    
    Args:
        request: Log analysis request containing log text and options
        logbert: LogBERT inference service
        rca: Root cause analysis service
        background_tasks: Background tasks for async operations
        
    Returns:
        Complete analysis results including anomalies and root causes
    """
    try:
        logger.info(f"Starting log analysis for {len(request.log_text)} characters")
        
        # Step 1: Anomaly detection
        anomaly_result = await logbert.detect_anomalies(
            log_text=request.log_text,
            threshold=request.threshold,
            model_name=request.model_name,
        )
        
        # Step 2: Root cause analysis (if anomalies detected)
        rca_result = None
        if anomaly_result.anomalies_detected:
            rca_result = await rca.analyze_root_causes(
                log_text=request.log_text,
                anomalies=anomaly_result.anomalies,
                context_window=request.context_window,
            )
        
        # Step 3: Prepare response
        response = LogAnalysisResponse(
            analysis_id=f"analysis_{int(time.time())}",
            status="completed",
            anomaly_detection=anomaly_result,
            root_cause_analysis=rca_result,
            processing_time_ms=anomaly_result.processing_time_ms + (
                rca_result.processing_time_ms if rca_result else 0
            ),
            metadata={
                "model_version": logbert.model_version,
                "timestamp": str(datetime.utcnow()),
                "input_size": len(request.log_text),
            }
        )
        
        logger.info(f"Analysis completed: {response.analysis_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error during log analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/upload", response_model=LogAnalysisResponse)
async def upload_and_analyze(
    file: UploadFile = File(...),
    threshold: float = 0.5,
    model_name: str = "logbert_hadoop",
    context_window: int = 10,
    logbert: LogBERTInference = Depends(get_logbert_service),
    rca: RootCauseAnalyzer = Depends(get_rca_service),
) -> LogAnalysisResponse:
    """
    Upload a log file and analyze it for anomalies.
    
    Args:
        file: Uploaded log file
        threshold: Anomaly detection threshold (0.0-1.0)
        model_name: Name of the model to use
        context_window: Context window size for RCA
        logbert: LogBERT inference service
        rca: Root cause analysis service
        
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
        )
        
        # Perform analysis
        return await analyze_logs(request, logbert, rca)
        
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
    logbert: LogBERTInference = Depends(get_logbert_service),
) -> AnomalyDetectionResponse:
    """
    Perform only anomaly detection without root cause analysis.
    
    Args:
        request: Log analysis request
        logbert: LogBERT inference service
        
    Returns:
        Anomaly detection results
    """
    try:
        logger.info("Starting anomaly detection only")
        
        result = await logbert.detect_anomalies(
            log_text=request.log_text,
            threshold=request.threshold,
            model_name=request.model_name,
        )
        
        logger.info(f"Anomaly detection completed: {len(result.anomalies)} anomalies found")
        return result
        
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
    rca: RootCauseAnalyzer = Depends(get_rca_service),
) -> RCAResponse:
    """
    Perform root cause analysis on provided anomalies.
    
    Args:
        log_text: Original log text
        anomalies: List of detected anomalies
        context_window: Context window for analysis
        rca: Root cause analysis service
        
    Returns:
        Root cause analysis results
    """
    try:
        logger.info(f"Starting RCA for {len(anomalies)} anomalies")
        
        result = await rca.analyze_root_causes(
            log_text=log_text,
            anomalies=anomalies,
            context_window=context_window,
        )
        
        logger.info(f"RCA completed: {len(result.root_causes)} causes identified")
        return result
        
    except Exception as e:
        logger.error(f"Error during RCA: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Root cause analysis failed: {str(e)}"
        )


@router.get("/models", response_model=List[ModelInfo])
async def list_available_models(
    logbert: LogBERTInference = Depends(get_logbert_service),
) -> List[ModelInfo]:
    """
    Get list of available models and their information.
    
    Returns:
        List of available models with metadata
    """
    try:
        models = await logbert.list_available_models()
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
    logbert: LogBERTInference = Depends(get_logbert_service),
) -> ModelInfo:
    """
    Get detailed information about a specific model.
    
    Args:
        model_name: Name of the model
        
    Returns:
        Model information and metadata
    """
    try:
        model_info = await logbert.get_model_info(model_name)
        return model_info
    except ValueError as e:
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
) -> JSONResponse:
    """
    Analyze multiple log files in batch mode.
    
    Args:
        files: List of uploaded log files
        threshold: Anomaly detection threshold
        model_name: Model to use for analysis
        background_tasks: Background tasks for async processing
        
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
                process_batch_files,
                batch_id,
                files,
                threshold,
                model_name,
            )
        
        logger.info(f"Started batch analysis: {batch_id} with {len(files)} files")
        
        return JSONResponse(
            content={
                "batch_id": batch_id,
                "status": "processing",
                "file_count": len(files),
                "estimated_completion_time": "5-10 minutes",
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting batch analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )


@router.get("/batch/{batch_id}")
async def get_batch_status(batch_id: str) -> JSONResponse:
    """
    Get status of a batch analysis job.
    
    Args:
        batch_id: Batch job ID
        
    Returns:
        Batch job status and results
    """
    try:
        # In a real implementation, this would check a database or cache
        # For now, return a mock response
        return JSONResponse(
            content={
                "batch_id": batch_id,
                "status": "completed",
                "progress": 100,
                "files_processed": 5,
                "files_total": 5,
                "results_url": f"/api/v1/batch/{batch_id}/results",
            }
        )
    except Exception as e:
        logger.error(f"Error getting batch status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get batch status: {str(e)}"
        )


async def process_batch_files(
    batch_id: str,
    files: List[UploadFile],
    threshold: float,
    model_name: str,
):
    """
    Background task to process batch files.
    
    Args:
        batch_id: Batch job ID
        files: List of files to process
        threshold: Anomaly detection threshold
        model_name: Model name to use
    """
    try:
        logger.info(f"Processing batch {batch_id} with {len(files)} files")
        
        # Process each file
        results = []
        for i, file in enumerate(files):
            try:
                # Read and analyze file
                content = await file.read()
                log_text = content.decode('utf-8')
                
                # Create analysis request
                request = LogAnalysisRequest(
                    log_text=log_text,
                    threshold=threshold,
                    model_name=model_name,
                )
                
                # Perform analysis
                result = await analyze_logs(request)
                results.append({
                    "filename": file.filename,
                    "status": "success",
                    "analysis": result,
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
        logger.info(f"Batch {batch_id} completed: {len(results)} files processed")
        
    except Exception as e:
        logger.error(f"Error in batch processing: {e}", exc_info=True)
