"""
Orchestrator service for coordinating the complete AI logo generation workflow.
Manages the sequence: Project → Inspiration Analysis → Prompts → 15 Logos
"""

import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.image_generation_service import ImageGenerationService
from app.services.prompt_engineering_service import PromptEngineeringService
from app.services.supabase_service import SupabaseService
from app.models.schemas import BrandInfo
from app.config.settings import settings

logger = logging.getLogger(__name__)

class OrchestratorService:
    """
    Service that orchestrates the complete AI workflow for logo generation.
    Coordinates APEX-7 prompt generation and Seedream image generation.
    """
    
    def __init__(self):
        """Initialize with AI services and database connection."""
        # APEX-7 handles all Gemini interactions (prompts + image analysis)
        self.prompt_service = PromptEngineeringService()
        self.image_service = ImageGenerationService()
        self.supabase_service = SupabaseService()
    
    async def start_logo_generation(self, project_id: str) -> None:
        """
        Main orchestration function that coordinates the complete workflow.
        
        Args:
            project_id: ID of the project to generate logos for
            
        The workflow:
        1. Get project data from database
        2. Analyze inspiration image (if provided)
        3. Generate 15 diverse prompts via Gemini
        4. Create 15 generated_assets database entries
        5. Launch background tasks for image generation
        6. Monitor progress and handle errors
        """
        try:
            logger.info(f"Starting logo generation workflow for project {project_id}")
            
            # Step 1: Get project data
            project_data = await self._get_project_data(project_id)
            if not project_data:
                logger.error(f"Project {project_id} not found")
                return
            
            # Step 2: Analyze inspiration image (if provided)
            inspiration_analysis = ""
            if project_data.get("inspiration_image_url"):
                logger.info("Analyzing inspiration image...")
                # APEX-7 service handles image analysis
                inspiration_analysis = await self.prompt_service.analyze_inspiration_image(
                    project_data["inspiration_image_url"]
                )
                logger.info(f"Inspiration analysis: {inspiration_analysis[:100]}...")
            
            # Step 3: Generate 15 diverse prompts using APEX-7 Multi-Studio Framework
            logger.info("🎨 Invoking APEX-7 Creative Direction Engine...")
            
            # Convert project data to BrandInfo (simplified - no style fields)
            brief_data = project_data.get("brief_data", {})
            brand_info = BrandInfo(
                company_name=brief_data.get("company_name", project_data.get("project_name", "")),
                industry=brief_data.get("industry", "General Business"),
                description=brief_data.get("description"),
                # style_preferences and brand_personality REMOVED
                inspirations=[{"analysis": inspiration_analysis}] if inspiration_analysis else []
            )
            
            prompts = self.prompt_service.generate_prompts(brand_info)
            
            if len(prompts) != 15:
                logger.warning(f"Expected 15 prompts, got {len(prompts)}")
            
            # Step 4: Create database entries for all assets
            asset_ids = await self._create_asset_entries(project_id, prompts)
            
            if len(asset_ids) != len(prompts):
                logger.error("Mismatch between prompts and asset IDs")
                return
            
            # Step 5: Use batch generation service for better performance
            logger.info(f"Launching APEX-7 Portfolio Generation: {len(prompts)} concepts...")
            
            # Import here to avoid circular dependency
            from app.services.batch_image_generation_service import BatchImageGenerationService
            batch_service = BatchImageGenerationService()
            
            # Launch batch generation as background task
            asyncio.create_task(
                batch_service.generate_logos_batch(prompts, asset_ids, project_id)
            )
            
            logger.info(f"✅ APEX-7 Creative Portfolio workflow initiated for project {project_id}")
            
        except Exception as e:
            logger.error(f"Failed to start logo generation for project {project_id}: {str(e)}")
    
    async def _get_project_data(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve project data from database.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Project data dictionary, or None if not found
        """
        try:
            result = self.supabase_service.client.table("brand_projects").select(
                "id, project_name, brief_data, inspiration_image_url, user_id"
            ).eq("id", project_id).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Database error getting project: {result.error}")
                return None
            
            if not result.data:
                logger.error(f"Project {project_id} not found")
                return None
            
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {str(e)}")
            return None
    
    async def _create_asset_entries(
        self,
        project_id: str,
        prompts: List[str]
    ) -> List[str]:
        """
        Create database entries for all 15 logo assets.
        
        Args:
            project_id: ID of the parent project
            prompts: List of prompts for generation
            
        Returns:
            List of asset IDs created
        """
        try:
            asset_ids = []
            asset_entries = []
            
            # Generate asset type sequence based on archetype distribution
            asset_type_sequence = self._generate_asset_type_sequence()
            
            for i, prompt in enumerate(prompts):
                asset_id = str(uuid.uuid4())
                asset_type = asset_type_sequence[i] if i < len(asset_type_sequence) else "abstract_mark"
                
                asset_entry = {
                    "id": asset_id,
                    "project_id": project_id,
                    "parent_asset_id": None,
                    "asset_type": "logo_concept",  # Using existing enum value
                    "status": "pending",
                    "asset_url": None,
                    "generation_prompt": prompt,
                    "error_message": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                asset_entries.append(asset_entry)
                asset_ids.append(asset_id)
            
            # Batch insert all assets
            result = self.supabase_service.client.table("generated_assets").insert(
                asset_entries
            ).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Failed to create asset entries: {result.error}")
                return []
            
            logger.info(f"Created {len(asset_ids)} asset entries for project {project_id}")
            return asset_ids
            
        except Exception as e:
            logger.error(f"Failed to create asset entries: {str(e)}")
            return []
    
    def _generate_asset_type_sequence(self) -> List[str]:
        """
        Generate the sequence of asset types based on archetype distribution.
        
        Returns:
            List of asset types in the order: 4 abstract, 3 lettermark, 3 wordmark, 3 combination, 2 pictorial
        """
        sequence = []
        
        for asset_type, count in self.ASSET_TYPES.items():
            sequence.extend([asset_type] * count)
        
        return sequence
    
    async def _launch_generation_tasks(
        self,
        prompts: List[str],
        asset_ids: List[str]
    ) -> None:
        """
        Launch background tasks for image generation with concurrency control.
        
        Args:
            prompts: List of prompts for generation
            asset_ids: Corresponding asset IDs
        """
        try:
            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(settings.max_concurrent_generations)
            
            async def generate_with_semaphore(prompt: str, asset_id: str):
                """Generate single logo with semaphore control."""
                async with semaphore:
                    return await self.image_service.generate_initial_concept(
                        prompt=prompt,
                        asset_id=asset_id,
                        asset_type="logo_concept"
                    )
            
            # Create all tasks
            tasks = []
            for prompt, asset_id in zip(prompts, asset_ids):
                task = asyncio.create_task(
                    generate_with_semaphore(prompt, asset_id)
                )
                tasks.append(task)
            
            # Launch all tasks without waiting (fire and forget)
            # This allows the main request to return while generation continues
            asyncio.create_task(self._monitor_generation_tasks(tasks, asset_ids))
            
            logger.info(f"Launched {len(tasks)} generation tasks")
            
        except Exception as e:
            logger.error(f"Failed to launch generation tasks: {str(e)}")
    
    async def _monitor_generation_tasks(
        self,
        tasks: List[asyncio.Task],
        asset_ids: List[str]
    ) -> None:
        """
        Monitor background generation tasks and log completion.
        
        Args:
            tasks: List of asyncio tasks
            asset_ids: Corresponding asset IDs for logging
        """
        try:
            logger.info("Monitoring generation tasks...")
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes and failures
            successes = sum(1 for result in results if result is True)
            failures = len(results) - successes
            
            logger.info(
                f"Generation complete: {successes} successful, {failures} failed out of {len(results)} total"
            )
            
            # Log individual failures for debugging
            for i, result in enumerate(results):
                if result is not True:
                    asset_id = asset_ids[i] if i < len(asset_ids) else "unknown"
                    if isinstance(result, Exception):
                        logger.error(f"Task failed for asset {asset_id}: {str(result)}")
                    else:
                        logger.warning(f"Task returned unexpected result for asset {asset_id}: {result}")
            
        except Exception as e:
            logger.error(f"Error monitoring generation tasks: {str(e)}")
    
    async def get_generation_progress(self, project_id: str) -> Dict[str, Any]:
        """
        Get the current progress of logo generation for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Progress information including counts by status
        """
        try:
            result = self.supabase_service.client.table("generated_assets").select(
                "status"
            ).eq("project_id", project_id).execute()
            
            if hasattr(result, 'error') and result.error:
                logger.error(f"Failed to get progress: {result.error}")
                return {"error": "Failed to get progress"}
            
            # Count assets by status
            status_counts = {
                "pending": 0,
                "generating": 0,
                "completed": 0,
                "failed": 0
            }
            
            for asset in result.data:
                status = asset.get("status", "pending")
                if status in status_counts:
                    status_counts[status] += 1
            
            total = sum(status_counts.values())
            
            return {
                "total_assets": total,
                "status_counts": status_counts,
                "completed_percentage": (status_counts["completed"] / total * 100) if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get generation progress: {str(e)}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Cleanup resources when orchestrator is done."""
        try:
            await self.image_service.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")