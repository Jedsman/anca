"""
ANCA API Schemas
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class JobStatusEnum(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerateRequest(BaseModel):
    """Request model for content generation"""
    topic: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Topic for content generation (alphanumeric, spaces, hyphens, basic punctuation)",
        pattern=r"^[a-zA-Z0-9\s\-_,.:;!?()&]+$"
    )

    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate and sanitize topic input"""
        # Strip leading/trailing whitespace
        v = v.strip()

        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',  # Script injection
            r'javascript:',  # JavaScript protocol
            r'eval\(',  # Eval injection
            r'system\(',  # System command injection
            r'__import__',  # Python import injection
            r'exec\(',  # Exec injection
        ]

        v_lower = v.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, v_lower):
                raise ValueError(
                    f"Topic contains suspicious content. "
                    f"Please use only alphanumeric characters, spaces, and basic punctuation."
                )

        # Ensure it's not just whitespace or special characters
        if not re.search(r'[a-zA-Z0-9]', v):
            raise ValueError("Topic must contain at least one alphanumeric character")

        # Collapse multiple spaces into single space
        v = re.sub(r'\s+', ' ', v)

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "home coffee brewing"
            }
        }


class JobResponse(BaseModel):
    """Response model for job status"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatusEnum = Field(..., description="Current job status")
    topic: str = Field(..., description="Topic being processed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    result: Optional[str] = Field(None, description="Job result message")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "completed",
                "topic": "home coffee brewing",
                "created_at": "2025-12-08T16:00:00",
                "completed_at": "2025-12-08T16:15:00",
                "result": "Article generated successfully"
            }
        }


class ArticleInfo(BaseModel):
    """Article metadata"""
    filename: str = Field(..., description="Article filename")
    size: int = Field(..., description="File size in bytes")
    created: datetime = Field(..., description="Creation timestamp")
    modified: datetime = Field(..., description="Last modified timestamp")


class ArticleListResponse(BaseModel):
    """Response model for article list"""
    articles: List[ArticleInfo] = Field(..., description="List of articles")
    total: int = Field(..., description="Total number of articles")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service health status")
    ollama_url: str = Field(..., description="Ollama service URL")
    articles_dir: str = Field(..., description="Articles directory path")
    articles_count: int = Field(..., description="Number of articles")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")


class ErrorResponse(BaseModel):
    """Error response model"""
    detail: str = Field(..., description="Error detail message")
    error_code: Optional[str] = Field(None, description="Error code")
