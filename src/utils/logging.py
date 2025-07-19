"""
Logging Configuration for LogBERT Hadoop RCA

This module provides centralized logging configuration with support for
structured logging, file output, and different environments.
"""

import os
import sys
import logging
import logging.config
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime


def get_log_config(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_logging: bool = False,
    app_name: str = "logbert"
) -> Dict[str, Any]:
    """
    Get logging configuration dictionary.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_logging: Enable JSON structured logging
        app_name: Application name for logging
        
    Returns:
        Logging configuration dictionary
    """
    
    # Base formatter
    if json_logging:
        formatter_class = "src.utils.logging.JSONFormatter"
        format_string = ""  # Not used for JSON formatter
    else:
        formatter_class = "logging.Formatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "class": formatter_class,
                "format": format_string,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "class": formatter_class,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            app_name: {
                "level": level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }
    
    # Add file handler if log_file is specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": level,
            "formatter": "detailed",
            "filename": log_file,
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
        config["root"]["handlers"].append("file")
    
    return config


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    json_logging: bool = False,
    app_name: str = "logbert"
) -> None:
    """
    Setup logging configuration for the application.
    
    Args:
        level: Logging level
        log_file: Optional log file path
        json_logging: Enable JSON structured logging
        app_name: Application name
    """
    
    # Get configuration from environment if available
    try:
        from .config import get_settings
        settings = get_settings()
        level = settings.LOG_LEVEL
        log_file = log_file or settings.LOG_FILE
        json_logging = json_logging or settings.ENABLE_JSON_LOGGING
        app_name = settings.APP_NAME.lower().replace(" ", "_")
    except ImportError:
        # Fallback if config module is not available
        level = os.getenv("LOGBERT_LOG_LEVEL", level)
        log_file = log_file or os.getenv("LOGBERT_LOG_FILE")
        json_logging = json_logging or os.getenv("LOGBERT_ENABLE_JSON_LOGGING", "false").lower() == "true"
    
    # Get logging configuration
    config = get_log_config(level, log_file, json_logging, app_name)
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger(app_name)
    logger.info(f"Logging initialized - Level: {level}, File: {log_file}, JSON: {json_logging}")


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON formatted log string
        """
        # Create base log entry
        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created",
                "msecs", "relativeCreated", "thread", "threadName",
                "processName", "process", "getMessage", "exc_info",
                "exc_text", "stack_info"
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ContextualLogger:
    """
    Logger wrapper that adds contextual information to log messages.
    """
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        """
        Initialize contextual logger.
        
        Args:
            logger: Base logger instance
            context: Context information to add to all log messages
        """
        self.logger = logger
        self.context = context
    
    def _log(self, level: int, message: str, *args, **kwargs) -> None:
        """Log message with context."""
        # Add context to extra
        extra = kwargs.get("extra", {})
        extra.update(self.context)
        kwargs["extra"] = extra
        
        self.logger.log(level, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Log debug message with context."""
        self._log(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Log info message with context."""
        self._log(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Log warning message with context."""
        self._log(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Log error message with context."""
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Log critical message with context."""
        self._log(logging.CRITICAL, message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Log exception with context."""
        kwargs["exc_info"] = True
        self.error(message, *args, **kwargs)


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> logging.Logger:
    """
    Get a logger instance with optional context.
    
    Args:
        name: Logger name
        context: Optional context to add to all log messages
        
    Returns:
        Logger instance (contextual if context provided)
    """
    logger = logging.getLogger(name)
    
    if context:
        return ContextualLogger(logger, context)
    
    return logger


def log_function_call(logger: logging.Logger):
    """
    Decorator to log function calls with parameters and return values.
    
    Args:
        logger: Logger instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Log function entry
            logger.debug(
                f"Calling {func.__name__}",
                extra={
                    "function": func.__name__,
                    "args": str(args)[:200],  # Limit arg length
                    "kwargs": str(kwargs)[:200],
                }
            )
            
            try:
                # Call function
                result = func(*args, **kwargs)
                
                # Log successful return
                logger.debug(
                    f"Function {func.__name__} completed successfully",
                    extra={
                        "function": func.__name__,
                        "result_type": type(result).__name__,
                    }
                )
                
                return result
                
            except Exception as e:
                # Log exception
                logger.error(
                    f"Function {func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_performance(logger: logging.Logger, message: str = "Operation"):
    """
    Decorator to log function performance metrics.
    
    Args:
        logger: Logger instance to use
        message: Message prefix for log entry
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logger.info(
                    f"{message} completed",
                    extra={
                        "function": func.__name__,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "status": "success",
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                logger.error(
                    f"{message} failed",
                    extra={
                        "function": func.__name__,
                        "execution_time_ms": round(execution_time * 1000, 2),
                        "status": "error",
                        "error": str(e),
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


# Module-level convenience functions
def debug(message: str, *args, **kwargs):
    """Module-level debug logging."""
    logging.debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Module-level info logging."""
    logging.info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Module-level warning logging."""
    logging.warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Module-level error logging."""
    logging.error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Module-level critical logging."""
    logging.critical(message, *args, **kwargs)


def exception(message: str, *args, **kwargs):
    """Module-level exception logging."""
    logging.exception(message, *args, **kwargs)
