"""
User routes for LogoKraft
Handles user profile, statistics, and OAuth provider management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, Dict, Any
import logging

from app.models.schemas import UserResponse, ErrorResponse
from app.services.user_service import user_service
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


@router.get("/profile",
    status_code=status.HTTP_200_OK,
    summary="Get user profile",
    description="Get complete user profile including OAuth provider information"
)
async def get_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """
    Get comprehensive user profile data.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Complete user profile with OAuth provider data, credits, and metadata
    """
    try:
        logger.info(f"Profile request for user: {current_user.id}")
        
        profile = await user_service.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/profile",
    status_code=status.HTTP_200_OK,
    summary="Update user profile",
    description="Update user profile information"
)
async def update_user_profile(
    updates: Dict[str, Any],
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update user profile information.
    
    Args:
        updates: Dictionary of fields to update (full_name, avatar_url, etc.)
        current_user: Current authenticated user
        
    Returns:
        Success message with updated profile data
    """
    try:
        logger.info(f"Profile update request for user: {current_user.id}")
        
        # Validate allowed fields
        allowed_fields = {'full_name', 'avatar_url'}
        invalid_fields = set(updates.keys()) - allowed_fields
        
        if invalid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid fields: {', '.join(invalid_fields)}. Allowed: {', '.join(allowed_fields)}"
            )
        
        # Validate field values
        if 'full_name' in updates:
            full_name = updates['full_name']
            if not isinstance(full_name, str) or len(full_name.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Full name must be a non-empty string"
                )
            updates['full_name'] = full_name.strip()
        
        if 'avatar_url' in updates:
            avatar_url = updates['avatar_url']
            if avatar_url is not None and (not isinstance(avatar_url, str) or len(avatar_url.strip()) == 0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Avatar URL must be a valid URL string or null"
                )
        
        # Update profile
        success = await user_service.update_user_profile(current_user.id, updates)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        # Return updated profile
        updated_profile = await user_service.get_user_profile(current_user.id)
        
        return {
            "message": "Profile updated successfully",
            "profile": updated_profile
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.get("/stats",
    status_code=status.HTTP_200_OK,
    summary="Get user statistics",
    description="Get user usage statistics including projects, assets, credits, and brand kits"
)
async def get_user_stats(current_user: UserResponse = Depends(get_current_user)):
    """
    Get comprehensive user statistics.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User statistics including project count, asset count, credits usage, and brand kit purchases
    """
    try:
        logger.info(f"Stats request for user: {current_user.id}")
        
        stats = await user_service.get_user_stats(current_user.id)
        
        return {
            "user_id": current_user.id,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/providers",
    status_code=status.HTTP_200_OK,
    summary="Get linked OAuth providers",
    description="Get list of OAuth providers linked to user account"
)
async def get_linked_providers(current_user: UserResponse = Depends(get_current_user)):
    """
    Get OAuth providers linked to user account.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        List of linked OAuth providers with creation and last sign-in dates
    """
    try:
        logger.info(f"Providers request for user: {current_user.id}")
        
        profile = await user_service.get_user_profile(current_user.id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        providers = profile.get('providers', [])
        
        return {
            "user_id": current_user.id,
            "providers": providers,
            "primary_provider": profile.get('provider', 'email')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve OAuth providers"
        )


@router.post("/providers/{provider}/unlink",
    status_code=status.HTTP_200_OK,
    summary="Unlink OAuth provider",
    description="Unlink an OAuth provider from user account"
)
async def unlink_oauth_provider(
    provider: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Unlink an OAuth provider from user account.
    
    Args:
        provider: OAuth provider to unlink (google, github)
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Unlink provider {provider} request for user: {current_user.id}")
        
        if provider not in ['google', 'github']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid provider. Supported providers: google, github"
            )
        
        success = await user_service.unlink_oauth_provider(current_user.id, provider)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to unlink provider. You may need at least one authentication method."
            )
        
        return {
            "message": f"Successfully unlinked {provider} provider",
            "provider": provider
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking provider {provider}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unlink OAuth provider"
        )


@router.delete("/account",
    status_code=status.HTTP_200_OK,
    summary="Delete user account",
    description="Permanently delete user account and all associated data"
)
async def delete_user_account(
    confirmation: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete user account and all associated data.
    
    Args:
        confirmation: Must be "DELETE" to confirm account deletion
        current_user: Current authenticated user
        
    Returns:
        Account deletion confirmation
    """
    try:
        logger.info(f"Account deletion request for user: {current_user.id}")
        
        if confirmation != "DELETE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account deletion requires confirmation string 'DELETE'"
            )
        
        # TODO: Implement account deletion
        # This should:
        # 1. Delete all user projects and assets
        # 2. Cancel any active brand kit orders
        # 3. Process any pending refunds
        # 4. Delete user from auth.users
        # 5. Clean up all related data
        
        logger.warning(f"Account deletion not yet implemented for user: {current_user.id}")
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Account deletion feature is not yet implemented. Please contact support."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )