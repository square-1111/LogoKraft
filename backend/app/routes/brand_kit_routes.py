"""
Brand Kit Routes - $29 Monetization Endpoints
Handles brand kit orders, generation, and progress tracking
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import StreamingResponse
from typing import Optional
import asyncio
import logging
from datetime import datetime

from app.models.schemas import (
    UserResponse,
    StreamMessage,
    ErrorResponse
)
from app.services.brand_kit_service import brand_kit_service
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/brand-kit",
    tags=["Brand Kit"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

@router.post("/purchase",
    status_code=status.HTTP_201_CREATED,
    summary="Purchase brand kit for $29",
    description="Create brand kit order and start generation of 5 professional components from selected logo"
)
async def purchase_brand_kit(
    selected_asset_id: str,
    payment_reference: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Purchase a complete brand kit for $29.
    
    Generates 5 components:
    - Business Cards (2 contrast versions)
    - Website Mockup (homepage design)
    - Social Media Headers (4 platforms)
    - T-shirt Mockup (apparel design)
    - Animated Logo (GIF + MP4)
    
    Args:
        selected_asset_id: ID of the logo to use for brand kit
        payment_reference: Payment provider reference (e.g., Stripe payment intent)
        current_user: Authenticated user from JWT token
        
    Returns:
        Brand kit order details and generation status
    """
    try:
        logger.info(f"Brand kit purchase request from user {current_user.id} for asset {selected_asset_id}")
        
        # Create brand kit order and start generation
        result = await brand_kit_service.create_brand_kit_order(
            user_id=current_user.id,
            selected_asset_id=selected_asset_id,
            payment_reference=payment_reference
        )
        
        return result
        
    except ValueError as e:
        # Asset not found or user doesn't own it
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Brand kit purchase failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create brand kit order"
        )

@router.get("/orders/{order_id}",
    status_code=status.HTTP_200_OK,
    summary="Get brand kit order status",
    description="Retrieve current status and progress of brand kit generation"
)
async def get_brand_kit_order(
    order_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get brand kit order status and component progress.
    
    Args:
        order_id: UUID of the brand kit order
        current_user: Authenticated user from JWT token
        
    Returns:
        Order status, progress, and component URLs when ready
    """
    try:
        result = await brand_kit_service.get_order_status(
            order_id=order_id,
            user_id=current_user.id
        )
        
        if result["status"] == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand kit order not found or access denied"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get brand kit order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve brand kit order"
        )

@router.get("/orders/{order_id}/stream",
    summary="Stream brand kit generation progress",
    description="Real-time Server-Sent Events stream for brand kit generation progress"
)
async def stream_brand_kit_progress(
    order_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Stream real-time updates for brand kit generation using Server-Sent Events.
    
    Events streamed:
    - connection: Initial connection confirmation
    - kit_progress: Individual component completion updates
    - kit_complete: All components ready for download
    - error: Generation errors or failures
    
    Args:
        order_id: UUID of the brand kit order to monitor
        current_user: Authenticated user from JWT token
        
    Returns:
        StreamingResponse: SSE stream of brand kit generation updates
    """
    try:
        logger.info(f"Starting brand kit SSE stream for order {order_id} for user {current_user.id}")
        
        # Verify user owns this order
        order_status = await brand_kit_service.get_order_status(order_id, current_user.id)
        if order_status["status"] == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Brand kit order not found or access denied"
            )
        
        async def generate_brand_kit_stream():
            """Generate SSE messages for brand kit progress updates."""
            try:
                # Send initial connection message
                initial_message = StreamMessage(
                    type="connection",
                    data={
                        "order_id": order_id,
                        "status": "connected",
                        "message": f"Connected to brand kit generation updates for order {order_id}"
                    }
                )
                yield f"data: {initial_message.model_dump_json()}\\n\\n"
                
                # Monitor brand kit generation progress
                last_progress_state = {}
                generation_complete = False
                max_duration_minutes = 10  # Maximum 10 minutes for generation
                start_time = datetime.utcnow()
                
                while not generation_complete:
                    try:
                        # Check if we've exceeded maximum duration
                        elapsed = (datetime.utcnow() - start_time).total_seconds() / 60
                        if elapsed > max_duration_minutes:
                            logger.warning(f"Brand kit generation timeout for order {order_id}")
                            timeout_message = StreamMessage(
                                type="error",
                                data={
                                    "order_id": order_id,
                                    "error": "timeout",
                                    "message": "Brand kit generation is taking longer than expected. Please check back later."
                                }
                            )
                            yield f"data: {timeout_message.model_dump_json()}\\n\\n"
                            break
                        
                        # Get current brand kit generation status
                        current_status = await brand_kit_service.get_order_status(order_id, current_user.id)
                        
                        # Check if this is a new or updated state
                        current_state = {
                            'status': current_status['status'],
                            'completed_count': current_status.get('progress', {}).get('completed', 0),
                            'total_count': current_status.get('progress', {}).get('total', 5)
                        }
                        
                        if current_state != last_progress_state:
                            # Send progress update
                            progress_message = StreamMessage(
                                type="kit_progress",
                                data={
                                    "order_id": order_id,
                                    "status": current_status['status'],
                                    "progress": current_status.get('progress', {}),
                                    "components": current_status.get('components', {}),
                                    "message": self._get_progress_message(current_status)
                                }
                            )
                            yield f"data: {progress_message.model_dump_json()}\\n\\n"
                            
                            last_progress_state = current_state
                            
                            # Check if generation is complete
                            if current_status['status'] in ['completed', 'failed']:
                                generation_complete = True
                        
                        if not generation_complete:
                            # Wait before next check
                            await asyncio.sleep(3)  # Check every 3 seconds
                        
                    except Exception as e:
                        logger.error(f"Error in brand kit stream generation: {e}")
                        error_message = StreamMessage(
                            type="error",
                            data={
                                "order_id": order_id,
                                "error": "stream_error",
                                "message": "An error occurred while monitoring brand kit progress"
                            }
                        )
                        yield f"data: {error_message.model_dump_json()}\\n\\n"
                        await asyncio.sleep(5)  # Wait before retrying
                
                # Send final completion message
                final_status = await brand_kit_service.get_order_status(order_id, current_user.id)
                final_message = StreamMessage(
                    type="kit_complete",
                    data={
                        "order_id": order_id,
                        "status": final_status['status'],
                        "message": "Brand kit generation monitoring complete",
                        "components": final_status.get('components', {}),
                        "download_ready": final_status['status'] == 'completed'
                    }
                )
                yield f"data: {final_message.model_dump_json()}\\n\\n"
                
            except Exception as e:
                logger.error(f"Fatal error in brand kit SSE stream: {e}")
                final_message = StreamMessage(
                    type="error",
                    data={
                        "order_id": order_id,
                        "error": "stream_terminated",
                        "message": "Stream has been terminated due to an error"
                    }
                )
                yield f"data: {final_message.model_dump_json()}\\n\\n"
        
        return StreamingResponse(
            generate_brand_kit_stream(),
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
        logger.error(f"Failed to setup brand kit SSE stream for order {order_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup brand kit stream"
        )

def _get_progress_message(status_data: dict) -> str:
    """Generate human-readable progress message."""
    progress = status_data.get('progress', {})
    completed = progress.get('completed', 0)
    total = progress.get('total', 5)
    
    if status_data['status'] == 'completed':
        return f"🎉 Brand kit ready! All {total} components generated successfully."
    elif status_data['status'] == 'failed':
        return f"❌ Brand kit generation failed. {completed}/{total} components completed."
    elif status_data['status'] == 'processing':
        if completed == 0:
            return "🎨 Starting brand kit generation..."
        else:
            component_names = ["Business Cards", "Website Mockup", "Social Headers", "T-shirt Mockup", "Animated Logo"]
            return f"⚡ Generated {completed}/{total} components. Working on {component_names[completed] if completed < len(component_names) else 'final component'}..."
    else:
        return f"Brand kit status: {status_data['status']}"