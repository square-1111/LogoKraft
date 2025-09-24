from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.models.schemas import (
    UserSignupRequest, 
    UserLoginRequest, 
    AuthResponse, 
    ErrorResponse,
    UserResponse
)
from app.services.supabase_service import supabase_service

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