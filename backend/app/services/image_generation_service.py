"""
Image generation service using fal.ai's Seedream v4 API.
Converts Gemini prompts into high-quality logo images.
"""

import logging
import asyncio
import uuid
from typing import Optional, Dict, Any
import httpx
import json
from io import BytesIO
import base64
import fal_client

from app.config.settings import settings
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class ImageGenerationService:
    """
    Service for generating logo images using fal.ai's Seedream v4 API.
    Handles image generation, storage upload, and database updates.
    """
    
    def __init__(self):
        """Initialize with fal.ai client and Supabase service."""
        # Use model IDs from settings for flexibility
        self.text_to_image_model = settings.fal_text_to_image_model
        self.image_to_image_model = settings.fal_image_to_image_model
        self.fal_key = settings.fal_key
        self.supabase_service = SupabaseService()
        
        # Configure fal_client
        import os
        os.environ["FAL_KEY"] = self.fal_key
        fal_client.api_key = self.fal_key
        
        # HTTP client with timeout for API calls (fallback)
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.generation_timeout),
            headers={
                "Authorization": f"Key {self.fal_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def generate_initial_concept(
        self,
        prompt: str,
        asset_id: str,
        asset_type: str = "logo_concept"
    ) -> bool:
        """
        Generate logo image from prompt and upload to storage.
        
        Args:
            prompt: Text prompt for logo generation
            asset_id: Database ID of the asset being generated
            asset_type: Type of asset (default: logo_concept)
            
        Returns:
            True if generation and upload successful, False otherwise
        """
        try:
            # Update status to generating
            await self.update_asset_status(asset_id, "generating")
            
            logger.info(f"Generating logo for asset {asset_id} with prompt: {prompt[:100]}...")
            
            # Prepare Seedream v4 payload
            payload = {
                "prompt": prompt,
                "image_size": {
                    "height": settings.logo_image_size,
                    "width": settings.logo_image_size
                },
                "num_images": 1,
                "max_images": 1,
                "seed": None,  # Random seed for variety
                "sync_mode": False,  # Use async mode for longer generations (20-30s)
                "enable_safety_checker": True
            }
            
            # Generate image using fal_client (handles async queue automatically)
            image_data = await self._generate_with_fal_client(prompt)
            
            if not image_data:
                await self.update_asset_status(
                    asset_id, 
                    "failed", 
                    error_message="Failed to generate image"
                )
                return False
            
            # Generate unique filename
            filename = f"logo_{asset_id}_{uuid.uuid4().hex[:8]}.png"
            
            # Upload to Supabase storage
            asset_url = await self.upload_to_storage(image_data, filename)
            
            if not asset_url:
                await self.update_asset_status(
                    asset_id,
                    "failed",
                    error_message="Failed to upload image to storage"
                )
                return False
            
            # Update database with success
            await self.update_asset_status(
                asset_id,
                "completed",
                asset_url=asset_url
            )
            
            logger.info(f"Successfully generated and uploaded logo for asset {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate concept for asset {asset_id}: {str(e)}")
            await self.update_asset_status(
                asset_id,
                "failed",
                error_message=str(e)
            )
            return False
    
    async def upload_to_storage(self, image_data: bytes, filename: str) -> Optional[str]:
        """
        Upload generated image to Supabase storage.
        
        Args:
            image_data: Raw image bytes
            filename: Unique filename for the image
            
        Returns:
            Public URL of uploaded image, or None if upload fails
        """
        try:
            # Upload to generated-assets bucket
            result = self.supabase_service.client.storage.from_("generated-assets").upload(
                path=filename,
                file=image_data,
                file_options={
                    "content-type": "image/png",
                    "cache-control": "3600"
                }
            )
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Storage upload error: {result.error}")
                return None
            
            # Get public URL
            public_url = self.supabase_service.client.storage.from_("generated-assets").get_public_url(filename)
            
            logger.info(f"Successfully uploaded image: {filename}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image {filename}: {str(e)}")
            return None
    
    async def update_asset_status(
        self,
        asset_id: str,
        status: str,
        asset_url: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update database with generation results.
        
        Args:
            asset_id: ID of the asset to update
            status: New status (pending, generating, completed, failed)
            asset_url: URL of generated asset (if completed)
            error_message: Error details (if failed)
        """
        try:
            update_data = {
                "status": status,
                "updated_at": "now()"
            }
            
            if asset_url:
                update_data["asset_url"] = asset_url
            
            if error_message:
                update_data["error_message"] = error_message
            
            result = self.supabase_service.client.table("generated_assets").update(
                update_data
            ).eq("id", asset_id).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Failed to update asset status: {result.error}")
            else:
                logger.debug(f"Updated asset {asset_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Failed to update asset {asset_id} status: {str(e)}")
    
    async def _generate_with_retry(
        self,
        payload: Dict[str, Any],
        max_retries: int = 3
    ) -> Optional[bytes]:
        """
        Generate image with retry logic for handling API failures.
        
        Args:
            payload: Seedream v4 API payload
            max_retries: Maximum number of retry attempts
            
        Returns:
            Raw image bytes, or None if all attempts fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1} to generate image")
                
                # Make API request to fal.ai
                response = await self.http_client.post(
                    self.fal_api_url,
                    json=payload
                )
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                
                # Extract image from response
                if "images" in result and len(result["images"]) > 0:
                    image_info = result["images"][0]
                    
                    # Check if image is base64 encoded or URL
                    if "url" in image_info:
                        # Download image from URL
                        image_response = await self.http_client.get(image_info["url"])
                        image_response.raise_for_status()
                        return image_response.content
                    
                    elif "data" in image_info:
                        # Decode base64 image
                        return base64.b64decode(image_info["data"])
                    
                else:
                    raise Exception("No images in API response")
                
            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} timed out. Retrying...")
                
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed with HTTP {e.response.status_code}: {e.response.text}")
                
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    break
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            
            # Wait before retry (exponential backoff)
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.debug(f"Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"All {max_retries} attempts failed. Last error: {str(last_error)}")
        return None
    
    async def _generate_with_fal_client(self, prompt: str) -> Optional[bytes]:
        """
        Generate image using fal_client library (handles queue automatically).
        
        Args:
            prompt: Text prompt for logo generation
            
        Returns:
            Raw image bytes, or None if generation fails
        """
        try:
            logger.info(f"Generating image with fal_client for prompt: {prompt[:100]}...")
            
            # Use fal_client.subscribe for automatic queue handling
            result = await asyncio.to_thread(
                fal_client.subscribe,
                self.text_to_image_model,
                arguments={
                    "prompt": prompt,
                    "image_size": {
                        "height": settings.logo_image_size,
                        "width": settings.logo_image_size
                    },
                    "num_images": 1,
                    "max_images": 1,
                    "enable_safety_checker": True
                },
                with_logs=False  # Disable logs for cleaner output
            )
            
            # Extract image URL from result
            if result and "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0]["url"]
                logger.info(f"Generated image URL: {image_url}")
                
                # Download the image
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    return response.content
            else:
                logger.error("No images in fal.ai response")
                return None
                
        except Exception as e:
            logger.error(f"fal_client generation failed: {str(e)}")
            return None
    
    async def generate_variation(
        self,
        original_image_url: str,
        modification_prompt: str,
        asset_id: str
    ) -> bool:
        """
        Generate a variation of an existing logo using Seedream Edit (image-to-image).
        
        Args:
            original_image_url: URL of the original image to modify
            modification_prompt: Description of the changes to make
            asset_id: Database ID of the new asset being generated
            
        Returns:
            True if generation and upload successful, False otherwise
        """
        try:
            # Update status to generating
            await self.update_asset_status(asset_id, "generating")
            
            logger.info(f"Generating variation for asset {asset_id} with prompt: {modification_prompt[:100]}...")
            
            # Download original image
            async with httpx.AsyncClient() as client:
                response = await client.get(original_image_url)
                response.raise_for_status()
                original_image_data = response.content
            
            # Convert to base64 for API
            import base64
            image_base64 = base64.b64encode(original_image_data).decode('utf-8')
            image_data_url = f"data:image/png;base64,{image_base64}"
            
            # Generate variation using Seedream Edit
            result = await asyncio.to_thread(
                fal_client.subscribe,
                self.image_to_image_model,
                arguments={
                    "image_url": image_data_url,  # Base64 data URL
                    "prompt": modification_prompt,
                    "image_size": {
                        "height": settings.logo_image_size,
                        "width": settings.logo_image_size
                    },
                    "num_images": 1,
                    "strength": 0.7,  # How much to modify (0=no change, 1=complete change)
                    "enable_safety_checker": True
                },
                with_logs=False
            )
            
            # Extract image from result
            if result and "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0]["url"]
                logger.info(f"Generated variation image URL: {image_url}")
                
                # Download the generated image
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    response.raise_for_status()
                    image_data = response.content
            else:
                logger.error("No images in variation response")
                await self.update_asset_status(
                    asset_id,
                    "failed",
                    error_message="No images in variation response"
                )
                return False
            
            # Generate unique filename
            filename = f"logo_variation_{asset_id}_{uuid.uuid4().hex[:8]}.png"
            
            # Upload to Supabase storage
            asset_url = await self.upload_to_storage(image_data, filename)
            
            if not asset_url:
                await self.update_asset_status(
                    asset_id,
                    "failed",
                    error_message="Failed to upload variation to storage"
                )
                return False
            
            # Update database with success
            await self.update_asset_status(
                asset_id,
                "completed",
                asset_url=asset_url
            )
            
            logger.info(f"Successfully generated and uploaded variation for asset {asset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate variation for asset {asset_id}: {str(e)}")
            await self.update_asset_status(
                asset_id,
                "failed",
                error_message=str(e)
            )
            return False
    
    async def close(self):
        """Close HTTP client when service is done."""
        await self.http_client.aclose()
    
    def __del__(self):
        """Cleanup on garbage collection."""
        try:
            if hasattr(self, 'http_client'):
                asyncio.create_task(self.http_client.aclose())
        except:
            pass  # Ignore cleanup errors