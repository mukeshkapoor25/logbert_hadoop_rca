"""
Configuration Management for LogBERT Hadoop RCA

This module handles all configuration settings for the application using Pydantic.
It supports environment variables, configuration files, and runtime overrides.
"""

import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from functools import lru_cache

try:
    from pydantic import BaseSettings, Field, validator
except ImportError:
    # Fallback for environments without pydantic
    class BaseSettings:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(default=None, **kwargs):
        return default
    
    def validator(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden using environment variables with
    the prefix 'LOGBERT_'. For example: LOGBERT_DEBUG=true
    """
    
    # Application Settings
    APP_NAME: str = Field(default="LogBERT Hadoop RCA", description="Application name")
    VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: str = Field(default="development", description="Environment (development, production, testing)")
    DEBUG: bool = Field(default=True, description="Enable debug mode")
    
    # API Settings
    API_HOST: str = Field(default="127.0.0.1", description="API host address")
    API_PORT: int = Field(default=8000, description="API port number")
    API_WORKERS: int = Field(default=1, description="Number of API workers")
    API_RELOAD: bool = Field(default=True, description="Enable auto-reload in development")
    
    # Model Settings
    MODEL_PATH: str = Field(default="AI_MODELS/trained_models", description="Path to trained models")
    DEFAULT_MODEL: str = Field(default="logbert_hadoop", description="Default model name")
    MAX_SEQUENCE_LENGTH: int = Field(default=512, description="Maximum sequence length for tokenization")
    BATCH_SIZE: int = Field(default=32, description="Default batch size for inference")
    
    # Deep Learning Settings
    DEVICE: str = Field(default="auto", description="Device for inference (cpu, cuda, mps, auto)")
    TORCH_THREADS: int = Field(default=4, description="Number of PyTorch threads")
    CUDA_MEMORY_FRACTION: float = Field(default=0.8, description="CUDA memory fraction to use")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    LOG_FILE: Optional[str] = Field(default=None, description="Log file path")
    ENABLE_JSON_LOGGING: bool = Field(default=False, description="Enable JSON structured logging")
    
    # Security Settings
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production", description="Secret key for encryption")
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    ENABLE_API_KEY_AUTH: bool = Field(default=False, description="Enable API key authentication")
    ALLOWED_HOSTS: List[str] = Field(default=["*"], description="Allowed hosts for CORS")
    
    # CORS Settings
    CORS_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")
    CORS_CREDENTIALS: bool = Field(default=True, description="Allow CORS credentials")
    CORS_METHODS: List[str] = Field(default=["*"], description="Allowed CORS methods")
    CORS_HEADERS: List[str] = Field(default=["*"], description="Allowed CORS headers")
    
    # Database Settings (if needed in future)
    DATABASE_URL: Optional[str] = Field(default=None, description="Database connection URL")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    
    # Cache Settings
    ENABLE_CACHING: bool = Field(default=True, description="Enable response caching")
    CACHE_TTL_SECONDS: int = Field(default=300, description="Cache TTL in seconds")
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL for caching")
    
    # Monitoring & Metrics
    ENABLE_METRICS: bool = Field(default=True, description="Enable metrics collection")
    METRICS_PORT: int = Field(default=9090, description="Metrics server port")
    HEALTH_CHECK_INTERVAL: int = Field(default=30, description="Health check interval in seconds")
    
    # File Upload Settings
    MAX_FILE_SIZE_MB: int = Field(default=100, description="Maximum file upload size in MB")
    UPLOAD_DIR: str = Field(default="uploads", description="Directory for uploaded files")
    ALLOWED_FILE_EXTENSIONS: List[str] = Field(
        default=[".log", ".txt", ".csv"],
        description="Allowed file extensions"
    )
    
    # Anomaly Detection Settings
    DEFAULT_ANOMALY_THRESHOLD: float = Field(default=0.5, description="Default anomaly detection threshold")
    MIN_ANOMALY_THRESHOLD: float = Field(default=0.1, description="Minimum allowed threshold")
    MAX_ANOMALY_THRESHOLD: float = Field(default=0.9, description="Maximum allowed threshold")
    
    # Root Cause Analysis Settings
    RCA_CONTEXT_WINDOW: int = Field(default=10, description="Default context window for RCA")
    RCA_MAX_CAUSES: int = Field(default=5, description="Maximum number of root causes to return")
    ENABLE_LLM_EXPLANATIONS: bool = Field(default=True, description="Enable LLM-powered explanations")
    
    # Rate Limiting Settings
    ENABLE_RATE_LIMITING: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, description="Requests per minute limit")
    RATE_LIMIT_BURST: int = Field(default=10, description="Burst limit for rate limiting")
    
    # Background Tasks
    MAX_BACKGROUND_TASKS: int = Field(default=10, description="Maximum concurrent background tasks")
    TASK_TIMEOUT_SECONDS: int = Field(default=3600, description="Task timeout in seconds")
    
    @validator('ENVIRONMENT')
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed = ['development', 'testing', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'Environment must be one of: {allowed}')
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level setting."""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed:
            raise ValueError(f'Log level must be one of: {allowed}')
        return v.upper()
    
    @validator('DEVICE')
    def validate_device(cls, v):
        """Validate device setting."""
        allowed = ['cpu', 'cuda', 'mps', 'auto']
        if v not in allowed:
            raise ValueError(f'Device must be one of: {allowed}')
        return v
    
    @validator('API_PORT', 'METRICS_PORT')
    def validate_port(cls, v):
        """Validate port numbers."""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('DEFAULT_ANOMALY_THRESHOLD', 'MIN_ANOMALY_THRESHOLD', 'MAX_ANOMALY_THRESHOLD')
    def validate_threshold(cls, v):
        """Validate threshold values."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Threshold must be between 0.0 and 1.0')
        return v
    
    @validator('CUDA_MEMORY_FRACTION')
    def validate_cuda_memory_fraction(cls, v):
        """Validate CUDA memory fraction."""
        if not 0.1 <= v <= 1.0:
            raise ValueError('CUDA memory fraction must be between 0.1 and 1.0')
        return v
    
    def get_model_path(self, model_name: str) -> Path:
        """Get the full path to a specific model."""
        return Path(self.MODEL_PATH) / model_name
    
    def get_upload_path(self, filename: str) -> Path:
        """Get the full path for an uploaded file."""
        upload_dir = Path(self.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir / filename
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == 'development'
    
    def get_cors_config(self) -> Dict[str, Any]:
        """Get CORS configuration."""
        return {
            'allow_origins': self.CORS_ORIGINS,
            'allow_credentials': self.CORS_CREDENTIALS,
            'allow_methods': self.CORS_METHODS,
            'allow_headers': self.CORS_HEADERS,
        }
    
    def get_database_config(self) -> Optional[Dict[str, Any]]:
        """Get database configuration if available."""
        if not self.DATABASE_URL:
            return None
        
        return {
            'url': self.DATABASE_URL,
            'pool_size': self.DATABASE_POOL_SIZE,
        }
    
    class Config:
        env_prefix = "LOGBERT_"
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


class DevelopmentSettings(Settings):
    """Development-specific settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    API_RELOAD: bool = True
    ENABLE_METRICS: bool = False
    ENABLE_RATE_LIMITING: bool = False


class ProductionSettings(Settings):
    """Production-specific settings."""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_RELOAD: bool = False
    ENABLE_METRICS: bool = True
    ENABLE_RATE_LIMITING: bool = True
    CORS_ORIGINS: List[str] = []  # Must be explicitly set in production


class TestingSettings(Settings):
    """Testing-specific settings."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENVIRONMENT: str = "testing"
    DATABASE_URL: str = "sqlite:///test.db"
    ENABLE_CACHING: bool = False
    ENABLE_RATE_LIMITING: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    This function creates and caches the settings instance based on the
    current environment. It automatically selects the appropriate settings
    class based on the LOGBERT_ENVIRONMENT variable.
    
    Returns:
        Settings instance for the current environment
    """
    environment = os.getenv("LOGBERT_ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """Get the data directory."""
    return get_project_root() / "AI_MODELS" / "datasets"


def get_models_dir() -> Path:
    """Get the models directory."""
    return get_project_root() / "AI_MODELS" / "trained_models"


def get_logs_dir() -> Path:
    """Get the logs directory."""
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def create_directories():
    """Create necessary directories if they don't exist."""
    settings = get_settings()
    
    # Create model directory
    Path(settings.MODEL_PATH).mkdir(parents=True, exist_ok=True)
    
    # Create upload directory
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    
    # Create logs directory
    get_logs_dir()
    
    # Create data directory
    get_data_dir().mkdir(parents=True, exist_ok=True)


# Initialize directories on import
create_directories()
