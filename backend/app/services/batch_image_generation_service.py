"""
Optimized batch image generation service using fal.ai async queue
Sends all 15 logo requests simultaneously for faster generation
"""

import logging
import asyncio
import uuid
from typing import Optional, Dict, Any, List
import httpx
import json
from io import BytesIO
import base64
import fal_client
import time

from app.config.settings import settings
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class BatchImageGenerationService:
    """
    Optimized service for generating multiple logos simultaneously using fal.ai async queue.
    Much faster than sequential generation.
    """
    
    def __init__(self):
        """Initialize with fal.ai client and Supabase service."""
        self.fal_key = settings.fal_key
        self.supabase_service = SupabaseService()
        
        # Configure fal_client
        import os
        os.environ["FAL_KEY"] = self.fal_key
        fal_client.api_key = self.fal_key
    
    async def generate_logos_batch(
        self,
        prompts: List[str],
        asset_ids: List[str],
        project_id: str
    ) -> Dict[str, Any]:
        """
        Generate multiple logos simultaneously using async queue pattern.
        
        Args:
            prompts: List of 15 prompts for logo generation
            asset_ids: Corresponding asset IDs
            project_id: Project ID for tracking
            
        Returns:
            Dictionary with generation results and statistics
        """
        try:
            logger.info(f"Starting batch generation of {len(prompts)} logos")
            start_time = time.time()
            
            # Step 1: Submit all requests to fal.ai queue simultaneously
            logger.info("📤 Submitting all requests to fal.ai queue...")
            submitted_requests = []
            
            for i, (prompt, asset_id) in enumerate(zip(prompts, asset_ids)):
                # Update status to generating
                await self._update_asset_status(asset_id, "generating")
                
                # Submit async request (non-blocking)
                request = await asyncio.to_thread(
                    fal_client.submit,
                    "fal-ai/bytedance/seedream/v4/text-to-image",
                    arguments={
                        "prompt": prompt,
                        "image_size": {
                            "height": settings.logo_image_size,
                            "width": settings.logo_image_size
                        },
                        "num_images": 1,
                        "enable_safety_checker": True,
                        "sync_mode": False  # Async for speed
                    }
                )
                
                submitted_requests.append({
                    "request": request,
                    "asset_id": asset_id,
                    "prompt": prompt[:50] + "...",
                    "index": i + 1
                })
                
                logger.info(f"  ✅ Submitted {i+1}/{len(prompts)}: {prompt[:50]}...")
            
            submission_time = time.time() - start_time
            logger.info(f"📤 All {len(prompts)} requests submitted in {submission_time:.1f}s")
            
            # Step 2: Poll for results (can be done in parallel)
            logger.info("📥 Polling for results...")
            results = await self._poll_all_results(submitted_requests)
            
            total_time = time.time() - start_time
            
            # Step 3: Process results and update database
            success_count = 0
            failed_count = 0
            
            for result_data in results:
                if result_data["success"]:
                    success_count += 1
                    # Download and upload image
                    await self._process_successful_result(result_data)
                else:
                    failed_count += 1
                    # Update with error
                    await self._update_asset_status(
                        result_data["asset_id"], 
                        "failed", 
                        error_message=result_data["error"]
                    )
            
            # Return statistics
            return {
                "total_requested": len(prompts),
                "successful": success_count,
                "failed": failed_count,
                "success_rate": success_count / len(prompts) * 100,
                "total_time": total_time,
                "submission_time": submission_time,
                "average_time_per_logo": total_time / len(prompts),
                "cost_estimate": success_count * 0.03
            }
            
        except Exception as e:
            logger.error(f"Batch generation failed: {str(e)}")
            return {
                "total_requested": len(prompts),
                "successful": 0,
                "failed": len(prompts),
                "error": str(e)
            }
    
    async def _poll_all_results(self, submitted_requests: List[Dict]) -> List[Dict]:
        """Poll all submitted requests for results."""
        results = []
        
        # Create polling tasks for all requests
        polling_tasks = []
        for req_data in submitted_requests:
            task = asyncio.create_task(
                self._poll_single_result(req_data)
            )
            polling_tasks.append(task)
        
        # Wait for all polling to complete
        logger.info(f"⏳ Waiting for {len(polling_tasks)} generations to complete...")
        completed_results = await asyncio.gather(*polling_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(completed_results):
            if isinstance(result, Exception):
                results.append({
                    "asset_id": submitted_requests[i]["asset_id"],
                    "success": False,
                    "error": str(result)
                })
            else:
                results.append(result)
        
        return results
    
    async def _poll_single_result(self, req_data: Dict) -> Dict:
        """Poll a single request for completion."""
        request = req_data["request"]
        asset_id = req_data["asset_id"]
        index = req_data["index"]
        
        try:
            logger.info(f"🔄 Polling result {index}/15...")
            
            # Get result (this blocks until complete)
            result = await asyncio.to_thread(fal_client.result, request)
            
            if result and "images" in result and len(result["images"]) > 0:
                image_url = result["images"][0]["url"]
                logger.info(f"✅ Logo {index} completed: {image_url}")
                
                return {
                    "asset_id": asset_id,
                    "success": True,
                    "image_url": image_url,
                    "result": result
                }
            else:
                logger.error(f"❌ Logo {index} failed: No images in result")
                return {
                    "asset_id": asset_id,
                    "success": False,
                    "error": "No images in result"
                }
                
        except Exception as e:
            logger.error(f"❌ Logo {index} failed: {str(e)}")
            return {
                "asset_id": asset_id,
                "success": False,
                "error": str(e)
            }
    
    async def _process_successful_result(self, result_data: Dict):
        """Download image and upload to storage."""
        try:
            asset_id = result_data["asset_id"]
            image_url = result_data["image_url"]
            
            # Download image
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)
                response.raise_for_status()
                image_data = response.content
            
            # Upload to storage
            filename = f"logo_{asset_id}_{uuid.uuid4().hex[:8]}.png"
            storage_url = await self._upload_to_storage(image_data, filename)
            
            if storage_url:
                await self._update_asset_status(asset_id, "completed", asset_url=storage_url)
            else:
                await self._update_asset_status(asset_id, "failed", error_message="Storage upload failed")
                
        except Exception as e:
            logger.error(f"Failed to process result for {result_data['asset_id']}: {str(e)}")
            await self._update_asset_status(
                result_data["asset_id"], 
                "failed", 
                error_message=f"Processing failed: {str(e)}"
            )
    
    async def _upload_to_storage(self, image_data: bytes, filename: str) -> Optional[str]:
        """Upload image to Supabase storage."""
        try:
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
            
            public_url = self.supabase_service.client.storage.from_("generated-assets").get_public_url(filename)
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload {filename}: {str(e)}")
            return None
    
    async def _update_asset_status(
        self,
        asset_id: str,
        status: str,
        asset_url: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Update database with generation results."""
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
                
        except Exception as e:
            logger.error(f"Failed to update asset {asset_id} status: {str(e)}")