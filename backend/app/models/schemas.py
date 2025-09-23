from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# Authentication Models

class UserSignupRequest(BaseModel):
    """Request model for user registration."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password (minimum 6 characters)")

class UserLoginRequest(BaseModel):
    """Request model for user authentication."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

class UserResponse(BaseModel):
    """Response model for user data."""
    id: str = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")

class AuthResponse(BaseModel):
    """Response model for authentication endpoints."""
    user: UserResponse = Field(..., description="User information")
    access_token: Optional[str] = Field(None, description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")

# Project Models

class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    project_name: str = Field(..., min_length=1, max_length=100, description="Name of the project")
    brief_data: Dict[str, Any] = Field(..., description="Project brief including brand keywords, industry, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "project_name": "TechCorp Rebranding",
                "brief_data": {
                    "industry": "Technology",
                    "keywords": ["innovative", "modern", "reliable"],
                    "target_audience": "B2B Enterprise",
                    "brand_personality": "Professional yet approachable",
                    "color_preferences": ["blue", "gray", "white"]
                }
            }
        }

class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: str = Field(..., description="Project's unique identifier")
    project_name: str = Field(..., description="Name of the project")
    brief_data: Dict[str, Any] = Field(..., description="Project brief data")
    inspiration_image_url: Optional[str] = Field(None, description="URL of uploaded inspiration image")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Project last update timestamp")

class ProjectCreateResponse(BaseModel):
    """Response model for project creation."""
    project: ProjectResponse = Field(..., description="Created project data")
    message: str = Field(..., description="Status message")

# Asset Models

class AssetResponse(BaseModel):
    """Response model for generated assets."""
    id: str = Field(..., description="Asset's unique identifier")
    project_id: str = Field(..., description="Parent project ID")
    asset_type: str = Field(..., description="Type of asset (logo, variation, etc.)")
    status: str = Field(..., description="Asset status: pending, generating, completed, failed")
    asset_url: Optional[str] = Field(None, description="URL of the generated asset")
    generation_prompt: str = Field(..., description="Prompt used for generation")
    parent_asset_id: Optional[str] = Field(None, description="ID of parent asset for variations")
    created_at: datetime = Field(..., description="Asset creation timestamp")
    updated_at: datetime = Field(..., description="Asset last update timestamp")

# SSE Stream Models

class StreamMessage(BaseModel):
    """Model for Server-Sent Events messages."""
    type: str = Field(..., description="Message type (status_update, asset_ready, error, etc.)")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "status_update",
                "data": {
                    "project_id": "uuid-here",
                    "status": "generating",
                    "message": "Creating logo concepts..."
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }

# Error Models

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

# Health Check Models

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    services: Dict[str, bool] = Field(..., description="Individual service status")