from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List
import json
import asyncio
import logging
from datetime import datetime

from app.models.schemas import (
    ProjectCreateRequest,
    ProjectResponse, 
    ProjectCreateResponse,
    AssetResponse,
    ErrorResponse,
    UserResponse,
    StreamMessage
)
from app.services.supabase_service import supabase_service
from app.services.orchestrator_service import OrchestratorService
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

@router.post("",
    response_model=ProjectCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new project with APEX-7",
    description="Create a new brand project and start APEX-7 Creative Direction workflow. Simplified Designer-Led approach - we handle the creative strategy."
)
async def create_project(
    # SIMPLIFIED FORM FIELDS - Designer-Led Approach
    company_name: str = Form(..., description="Company or brand name"),
    industry: str = Form(..., description="Industry or business sector"),
    description: str = Form("", description="Company description (optional)"),
    inspiration_image: Optional[UploadFile] = File(None, description="Optional inspiration image"),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new brand project using the APEX-7 Designer-Led approach.
    
    This endpoint:
    1. Takes only essential brand information (name, industry, description)
    2. Uploads inspiration image to storage if provided
    3. Creates a project record in the database 
    4. Triggers APEX-7 Creative Direction workflow in background
    5. Returns immediately while 15 elite concepts are generated
    
    Args:
        company_name: Company or brand name
        industry: Industry or business sector
        description: Optional company description
        inspiration_image: Optional uploaded image file
        current_user: Authenticated user from JWT token
        
    Returns:
        ProjectCreateResponse: Created project data and status message
        
    Raises:
        HTTPException: If validation or creation fails
    """
    try:
        project_name = company_name  # Use company name as project name
        logger.info(f"🎨 Creating APEX-7 project '{project_name}' for user {current_user.id}")
        
        # Structure the simplified brief data (Designer-Led approach)
        brief_data = {
            "company_name": company_name,
            "industry": industry,
            "description": description
            # style_preferences and brand_personality REMOVED - We are the designers
        }
        
        # Validate required fields
        if not company_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name cannot be empty"
            )
        if not industry.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Industry cannot be empty"
            )
        
        # Handle inspiration image upload if provided
        inspiration_image_url = None
        if inspiration_image:
            # Validate file type
            if not inspiration_image.content_type or not inspiration_image.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file must be an image"
                )
            
            # Read file content
            file_content = await inspiration_image.read()
            
            # Upload to storage
            try:
                inspiration_image_url = await supabase_service.upload_inspiration_image(
                    file_content=file_content,
                    filename=inspiration_image.filename or "inspiration.jpg",
                    user_id=current_user.id
                )
                logger.info(f"Inspiration image uploaded: {inspiration_image_url}")
            except Exception as e:
                logger.error(f"Image upload failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to upload inspiration image"
                )
        
        # Create project in database
        project_data = {
            "project_name": project_name.strip(),
            "brief_data": brief_data,  # Use the simplified brief_data
            "inspiration_image_url": inspiration_image_url
        }
        
        created_project = await supabase_service.create_project(
            user_id=current_user.id,
            project_data=project_data
        )
        
        logger.info(f"✅ Project created successfully: {created_project['id']}")
        
        # Trigger APEX-7 Creative Direction workflow in background
        orchestrator = OrchestratorService()
        asyncio.create_task(
            orchestrator.start_logo_generation(created_project['id'])
        )
        
        return ProjectCreateResponse(
            project=ProjectResponse(**created_project),
            message=f"Project '{company_name}' created. APEX-7 is generating 15 elite design concepts!"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Project creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )

@router.get("/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project details",
    description="Retrieve details of a specific project. User can only access their own projects."
)
async def get_project(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get project details by ID.
    
    Args:
        project_id: UUID of the project to retrieve
        current_user: Authenticated user from JWT token
        
    Returns:
        ProjectResponse: Project data
        
    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        logger.info(f"Getting project {project_id} for user {current_user.id}")
        
        # Get project from database (includes user authorization check)
        project = await supabase_service.get_project(project_id, current_user.id)
        
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        
        return ProjectResponse(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )

@router.get("/{project_id}/assets",
    response_model=List[AssetResponse],
    status_code=status.HTTP_200_OK,
    summary="Get project assets",
    description="Retrieve all generated assets for a project."
)
async def get_project_assets(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get all generated assets for a project.
    
    Args:
        project_id: UUID of the project
        current_user: Authenticated user from JWT token
        
    Returns:
        List[AssetResponse]: List of project assets
        
    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        logger.info(f"Getting assets for project {project_id} for user {current_user.id}")
        
        # Verify user owns this project
        project = await supabase_service.get_project(project_id, current_user.id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        
        # Get assets
        assets = await supabase_service.get_project_assets(project_id)
        
        return [AssetResponse(**asset) for asset in assets]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assets for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project assets"
        )

@router.get("/{project_id}/stream",
    summary="Stream project updates",
    description="Server-Sent Events stream for real-time project updates. Monitors database changes and streams status updates."
)
async def stream_project_updates(
    project_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Stream real-time updates for a project using Server-Sent Events.
    
    This endpoint:
    1. Verifies user has access to the project
    2. Sets up SSE stream with proper headers
    3. Monitors generated_assets table for changes
    4. Streams status updates as JSON messages
    
    Args:
        project_id: UUID of the project to monitor
        current_user: Authenticated user from JWT token
        
    Returns:
        StreamingResponse: SSE stream of project updates
        
    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        logger.info(f"Starting SSE stream for project {project_id} for user {current_user.id}")
        
        # Verify user owns this project
        project = await supabase_service.get_project(project_id, current_user.id)
        if project is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        
        async def generate_stream():
            """Generate SSE messages for project updates."""
            try:
                # Send initial connection message
                initial_message = StreamMessage(
                    type="connection",
                    data={
                        "project_id": project_id,
                        "status": "connected",
                        "message": f"Connected to project {project['project_name']} updates"
                    }
                )
                yield f"data: {initial_message.model_dump_json()}\n\n"
                
                # Track last known asset state
                last_assets_state = {}
                
                # Monitor for changes
                while True:
                    try:
                        # Get current assets
                        current_assets = await supabase_service.get_project_assets(project_id)
                        
                        # Check for changes
                        for asset in current_assets:
                            asset_id = asset['id']
                            asset_status = asset['status']
                            asset_updated = asset['updated_at']
                            
                            # Check if this is new or updated
                            if (asset_id not in last_assets_state or 
                                last_assets_state[asset_id]['status'] != asset_status or
                                last_assets_state[asset_id]['updated_at'] != asset_updated):
                                
                                # Asset has changed - send update
                                update_message = StreamMessage(
                                    type="asset_update",
                                    data={
                                        "project_id": project_id,
                                        "asset_id": asset_id,
                                        "asset_type": asset['asset_type'],
                                        "status": asset_status,
                                        "asset_url": asset.get('asset_url'),
                                        "message": f"Asset {asset['asset_type']} is {asset_status}"
                                    }
                                )
                                yield f"data: {update_message.model_dump_json()}\n\n"
                                
                                # Update tracking state
                                last_assets_state[asset_id] = {
                                    'status': asset_status,
                                    'updated_at': asset_updated
                                }
                        
                        # Send periodic heartbeat (every 30 seconds)
                        heartbeat_message = StreamMessage(
                            type="heartbeat",
                            data={
                                "project_id": project_id,
                                "timestamp": datetime.utcnow().isoformat(),
                                "assets_count": len(current_assets)
                            }
                        )
                        yield f"data: {heartbeat_message.model_dump_json()}\n\n"
                        
                        # Wait before next check
                        await asyncio.sleep(5)  # Check every 5 seconds
                        
                    except Exception as e:
                        logger.error(f"Error in stream generation: {e}")
                        error_message = StreamMessage(
                            type="error",
                            data={
                                "project_id": project_id,
                                "error": "Stream error",
                                "message": "An error occurred while monitoring project updates"
                            }
                        )
                        yield f"data: {error_message.model_dump_json()}\n\n"
                        await asyncio.sleep(5)  # Wait before retrying
                        
            except Exception as e:
                logger.error(f"Fatal error in SSE stream: {e}")
                final_message = StreamMessage(
                    type="error",
                    data={
                        "project_id": project_id,
                        "error": "Stream terminated",
                        "message": "Stream has been terminated due to an error"
                    }
                )
                yield f"data: {final_message.model_dump_json()}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup SSE stream for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup project stream"
        )