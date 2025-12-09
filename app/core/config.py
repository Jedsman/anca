"""
ANCA API Configuration
Centralized configuration management
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    api_title: str = "ANCA API"
    api_description: str = "Autonomous Niche Content Agent - Generate SEO-optimized blog posts"
    api_version: str = "1.0.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    
    # CrewAI Configuration
    crewai_telemetry: bool = False
    
    # Paths - Adjusted for app/core/ location
    # Root is app/../
    root_dir: Path = Path(__file__).parent.parent.parent
    articles_dir: Path = root_dir / "articles"
    cache_dir: Path = root_dir / ".cache"
    chroma_dir: Path = root_dir / ".chroma"
    logs_dir: Path = root_dir / "logs"
    
    # Cache Configuration
    cache_ttl_days: int = 7
    
    # Logging
    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024  # 10MB per log file
    log_backup_count: int = 5               # Keep 5 backup files

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Allow extra env vars


settings = Settings()
