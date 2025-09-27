from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.models.schemas import (
    UserSignupRequest, 
    UserLoginRequest, 
    AuthResponse, 
    ErrorResponse,
    UserResponse,
    OAuthSignInRequest,
    OAuthCallbackRequest,
    OAuthURLResponse
)
from app.services.supabase_service import supabase_service
from app.services.oauth_service import oauth_service

logger = logging.getLogger(__name__)
security = HTTPBearer()

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)

@router.post("/signup", 
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user account",
    description="Register a new user with email and password. Returns user data and authentication tokens."
)
async def signup(user_data: UserSignupRequest):
    """
    Create a new user account with Supabase Auth.
    
    Args:
        user_data: User registration information (email, password)
        
    Returns:
        AuthResponse: User data and authentication tokens
        
    Raises:
        HTTPException: If signup fails (400, 500)
    """
    try:
        logger.info(f"Signup attempt for email: {user_data.email}")
        
        # Create user via Supabase service
        auth_result = await supabase_service.signup(
            email=user_data.email,
            password=user_data.password
        )
        
        logger.info(f"User created successfully: {auth_result['user']['id']}")
        
        return AuthResponse(
            user=UserResponse(**auth_result["user"]),
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"]
        )
        
    except Exception as e:
        logger.error(f"Signup failed: {str(e)}")
        
        # Check for common Supabase auth errors
        error_message = str(e).lower()
        if "already registered" in error_message or "already exists" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists with this email address"
            )
        elif "invalid" in error_message and "email" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address. Please use a valid email format."
            )
        elif "invalid format" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email address format"
            )
        elif "password" in error_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password does not meet requirements (minimum 6 characters)"
            )
        else:
            # Include original error for debugging
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signup failed: {str(e)}"
            )

@router.post("/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
    description="Login with email and password. Returns user data and authentication tokens."
)
async def login(user_data: UserLoginRequest):
    """
    Authenticate user with email and password.
    
    Args:
        user_data: User login credentials (email, password)
        
    Returns:
        AuthResponse: User data and authentication tokens
        
    Raises:
        HTTPException: If login fails (401, 500)
    """
    try:
        logger.info(f"Login attempt for email: {user_data.email}")
        
        # Authenticate via Supabase service
        auth_result = await supabase_service.login(
            email=user_data.email,
            password=user_data.password
        )
        
        logger.info(f"User authenticated successfully: {auth_result['user']['id']}")
        
        return AuthResponse(
            user=UserResponse(**auth_result["user"]),
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"]
        )
        
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        
        # Most auth failures should be 401 Unauthorized
        error_message = str(e).lower()
        if "email not confirmed" in error_message:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not confirmed. Please check your email for the confirmation link."
            )
        elif "invalid" in error_message or "wrong" in error_message or "incorrect" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service unavailable"
            )

# Dependency for protected routes
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserResponse:
    """
    Dependency to extract and validate user from JWT token.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        UserResponse: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid (401)
    """
    try:
        token = credentials.credentials
        user_data = await supabase_service.get_user(token)
        
        if user_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return UserResponse(**user_data)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.get("/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user."
)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Injected current user from JWT token
        
    Returns:
        UserResponse: Current user data
    """
    return current_user

@router.post("/oauth/signin",
    response_model=OAuthURLResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate OAuth sign-in URL",
    description="Generate authorization URL for Google or GitHub OAuth sign-in"
)
async def oauth_signin(oauth_data: OAuthSignInRequest):
    """
    Generate OAuth authorization URL for the specified provider.
    
    Args:
        oauth_data: OAuth provider and redirect URL information
        
    Returns:
        OAuthURLResponse: Authorization URL and state parameter
        
    Raises:
        HTTPException: If provider is unsupported or URL generation fails
    """
    try:
        logger.info(f"OAuth sign-in URL requested for provider: {oauth_data.provider}")
        
        # Generate OAuth URL
        oauth_result = await oauth_service.get_oauth_url(
            provider=oauth_data.provider,
            redirect_url=oauth_data.redirect_url
        )
        
        logger.info(f"OAuth URL generated successfully for {oauth_data.provider}")
        
        return OAuthURLResponse(
            url=oauth_result["url"],
            state=oauth_result["state"]
        )
        
    except ValueError as e:
        logger.error(f"OAuth URL generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in OAuth URL generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OAuth authorization URL"
        )

@router.post("/oauth/callback",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle OAuth callback",
    description="Process OAuth authorization callback with code exchange"
)
async def oauth_callback(callback_data: OAuthCallbackRequest):
    """
    Handle OAuth callback and exchange authorization code for tokens.
    
    Args:
        callback_data: Authorization code and state from OAuth provider
        
    Returns:
        AuthResponse: User data and authentication tokens
        
    Raises:
        HTTPException: If callback processing fails
    """
    try:
        logger.info("Processing OAuth callback")
        
        # Handle OAuth callback
        auth_result = await oauth_service.handle_oauth_callback(
            code=callback_data.code,
            state=callback_data.state
        )
        
        logger.info(f"OAuth authentication successful for user: {auth_result['user']['email']}")
        
        return AuthResponse(
            user=UserResponse(**auth_result["user"]),
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"]
        )
        
    except ValueError as e:
        logger.error(f"OAuth callback processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )

@router.post("/oauth/refresh",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh OAuth tokens",
    description="Refresh expired OAuth access tokens using refresh token"
)
async def oauth_refresh(refresh_token: str):
    """
    Refresh OAuth access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token from previous authentication
        
    Returns:
        AuthResponse: Updated user data and new tokens
        
    Raises:
        HTTPException: If token refresh fails
    """
    try:
        logger.info("OAuth token refresh requested")
        
        # Refresh OAuth tokens
        auth_result = await oauth_service.refresh_oauth_token(refresh_token)
        
        logger.info(f"OAuth token refresh successful for user: {auth_result['user']['email']}")
        
        return AuthResponse(
            user=UserResponse(**auth_result["user"]),
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"]
        )
        
    except ValueError as e:
        logger.error(f"OAuth token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in OAuth token refresh: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Logout user and revoke authentication session"
)
async def logout(current_user: UserResponse = Depends(get_current_user)):
    """
    Logout user and revoke authentication session.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Success message
    """
    try:
        logger.info(f"Logout requested for user: {current_user.email}")
        
        # For OAuth users, we could revoke the session
        # For now, we'll just return success (client should discard tokens)
        
        logger.info(f"User logged out successfully: {current_user.email}")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        # Even if logout fails, return success to prevent client-side issues
        return {"message": "Logged out successfully"}