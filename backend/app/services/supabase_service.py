from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import asyncio
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from app.config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    """
    Service for interacting with Supabase database and authentication.
    Handles user auth, project CRUD, and file uploads.
    """
    
    def __init__(self):
        """Initialize Supabase client with service role key for backend operations."""
        try:
            self.client: Client = create_client(
                settings.supabase_url,
                settings.supabase_service_key,
                options=ClientOptions(
                    auto_refresh_token=False,
                    persist_session=False
                )
            )
            logger.info("Supabase service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    # Authentication Methods
    
    async def signup(self, email: str, password: str) -> Dict[str, Any]:
        """
        Create a new user account with Supabase Auth.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing user data and tokens
            
        Raises:
            Exception: If signup fails
        """
        try:
            response = await asyncio.to_thread(
                self.client.auth.sign_up,
                {"email": email, "password": password}
            )
            
            if response.user is None:
                raise Exception("User creation failed")
                
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                },
                "access_token": response.session.access_token if response.session else None,
                "refresh_token": response.session.refresh_token if response.session else None
            }
        except Exception as e:
            logger.error(f"Signup failed for {email}: {e}")
            raise Exception(f"Signup failed: {str(e)}")
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate existing user with Supabase Auth.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing user data and tokens
            
        Raises:
            Exception: If login fails
        """
        try:
            response = await asyncio.to_thread(
                self.client.auth.sign_in_with_password,
                {"email": email, "password": password}
            )
            
            if response.user is None:
                raise Exception("Authentication failed")
                
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                },
                "access_token": response.session.access_token if response.session else None,
                "refresh_token": response.session.refresh_token if response.session else None
            }
        except Exception as e:
            logger.error(f"Login failed for {email}: {e}")
            raise Exception(f"Login failed: {str(e)}")
    
    async def get_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from JWT token.
        
        Args:
            token: JWT access token
            
        Returns:
            User data if token is valid, None otherwise
        """
        try:
            response = await asyncio.to_thread(
                self.client.auth.get_user, 
                token
            )
            if response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email
                }
            return None
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return None
    
    # Project CRUD Operations
    
    async def create_project(self, user_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new brand project in the database.
        
        Args:
            user_id: ID of the user creating the project
            project_data: Project information including name and brief_data
            
        Returns:
            Created project data
            
        Raises:
            Exception: If project creation fails
        """
        try:
            project_record = {
                "user_id": user_id,
                "project_name": project_data["project_name"],
                "brief_data": project_data["brief_data"],
                "inspiration_image_url": project_data.get("inspiration_image_url")
            }
            
            response = self.client.table("brand_projects").insert(project_record).execute()
            
            if not response.data:
                raise Exception("Failed to create project")
                
            created_project = response.data[0]
            logger.info(f"Project created: {created_project['id']} for user {user_id}")
            
            return created_project
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            raise Exception(f"Failed to create project: {str(e)}")
    
    async def get_project(self, project_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project by ID, ensuring it belongs to the user.
        
        Args:
            project_id: Project ID to retrieve
            user_id: ID of the requesting user
            
        Returns:
            Project data if found and authorized, None otherwise
        """
        try:
            response = self.client.table("brand_projects").select("*").eq("id", project_id).eq("user_id", user_id).execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None
    
    async def get_project_assets(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all generated assets for a project.
        
        Args:
            project_id: Project ID to get assets for
            
        Returns:
            List of asset records
        """
        try:
            response = self.client.table("generated_assets").select("*").eq("project_id", project_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get assets for project {project_id}: {e}")
            return []
    
    async def get_asset_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single asset by its ID.
        
        Args:
            asset_id: Asset ID to retrieve
            
        Returns:
            Asset record or None if not found
        """
        try:
            response = self.client.table("generated_assets").select("*").eq("id", asset_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get asset {asset_id}: {e}")
            return None
    
    # File Upload Methods
    
    async def upload_inspiration_image(self, file_content: bytes, filename: str, user_id: str) -> str:
        """
        Upload inspiration image to Supabase storage.
        
        Args:
            file_content: Binary file content
            filename: Original filename
            user_id: ID of the user uploading
            
        Returns:
            Public URL of uploaded file
            
        Raises:
            Exception: If upload fails
        """
        try:
            # Create unique filename with user_id prefix
            unique_filename = f"{user_id}/{datetime.utcnow().timestamp()}_{filename}"
            
            # Upload to inspiration-images bucket
            response = self.client.storage.from_("inspiration-images").upload(
                unique_filename,
                file_content
            )
            
            if response.path is None:
                raise Exception("Upload failed - no path returned")
            
            # Get public URL
            public_url = self.client.storage.from_("inspiration-images").get_public_url(unique_filename)
            
            logger.info(f"Image uploaded: {unique_filename} for user {user_id}")
            return public_url
            
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            raise Exception(f"Failed to upload image: {str(e)}")
    
    # Database Health Check
    
    async def health_check(self) -> bool:
        """
        Check if database connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            response = self.client.table("brand_projects").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global service instance
supabase_service = SupabaseService()