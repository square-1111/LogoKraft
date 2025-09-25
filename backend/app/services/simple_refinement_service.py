"""
Simple Refinement Service
Handles the focused logo refinement flow: 1 logo + prompt → 5 variations
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from app.services.image_generation_service import ImageGenerationService
from app.services.prompt_engineering_service import PromptEngineeringService
from app.services.credit_service import credit_service
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

class SimpleRefinementService:
    """
    Simplified refinement service for focused user flow.
    Takes 1 selected logo + optional prompt, generates 5 variations.
    """
    
    def __init__(self):
        self.image_service = ImageGenerationService()
        self.prompt_service = PromptEngineeringService()
        self.credit_cost = 5  # 5 credits for 5 variations
    
    async def refine_logo(
        self,
        asset_id: str,
        user_id: str, 
        user_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main refinement method: 1 logo + prompt → 5 variations
        
        Args:
            asset_id: ID of the selected logo to refine
            user_id: ID of the user requesting refinement
            user_prompt: Optional text prompt for changes (e.g., "make it more modern")
            
        Returns:
            Dict with original asset info and 5 new variation asset IDs
            
        Raises:
            ValueError: If insufficient credits or asset not found
            Exception: If refinement process fails
        """
        try:
            logger.info(f"Starting simple refinement for asset {asset_id} by user {user_id}")
            
            # 1. Check user has sufficient credits
            if not await credit_service.check_credits(user_id, self.credit_cost):
                raise ValueError("Insufficient credits for refinement")
            
            # 2. Get original asset from database
            original_asset = await self._get_asset(asset_id)
            if not original_asset:
                raise ValueError(f"Asset {asset_id} not found")
            
            # 3. Deduct credits upfront
            success = await credit_service.deduct_credits(
                user_id=user_id,
                amount=self.credit_cost,
                reason=f"Simple refinement of asset {asset_id}",
                asset_id=asset_id
            )
            if not success:
                raise ValueError("Credit deduction failed")
            
            try:
                # 4. Generate 5 intelligent variation prompts using image analysis
                variation_prompts = await self._generate_variation_prompts(
                    original_asset=original_asset,
                    user_prompt=user_prompt  # Can be None - we'll always generate 5 variations
                )
                
                # 5. Create database entries for 5 variations using secure RPC
                variations_data = []
                for i, prompt in enumerate(variation_prompts):
                    variations_data.append({
                        'prompt': prompt,
                        'metadata': {
                            'user_prompt': user_prompt,
                            'variation_index': i + 1,
                            'refinement_method': 'simple'
                        }
                    })
                
                # Use secure RPC function that enforces ownership
                result = supabase_service.client.rpc(
                    'create_refinement_assets_batch',
                    {
                        'p_user_id': user_id,
                        'p_original_asset_id': asset_id,
                        'p_variations': variations_data
                    }
                ).execute()
                
                if not result.data:
                    raise Exception("Failed to create refinement assets")
                
                variation_asset_ids = [item['asset_id'] for item in result.data]
                
                # 6. Start background generation for all variations
                generation_tasks = []
                for i, (asset_id_new, prompt) in enumerate(zip(variation_asset_ids, variation_prompts)):
                    task = asyncio.create_task(
                        self._generate_single_variation(
                            original_asset_url=original_asset['asset_url'],
                            new_asset_id=asset_id_new,
                            prompt=prompt,
                            variation_index=i + 1
                        )
                    )
                    generation_tasks.append(task)
                
                # Start all generations in parallel with proper error handling
                async def monitor_generations():
                    """Monitor background generation tasks and handle errors."""
                    try:
                        results = await asyncio.gather(*generation_tasks, return_exceptions=True)
                        for i, result in enumerate(results):
                            if isinstance(result, Exception):
                                asset_id_failed = variation_asset_ids[i]
                                logger.error(f"Background generation for asset {asset_id_failed} failed: {result}")
                                
                                # Update asset status to failed
                                try:
                                    supabase_service.client.table('generated_assets')\
                                        .update({
                                            'status': 'failed',
                                            'error_message': str(result),
                                            'updated_at': 'NOW()'
                                        })\
                                        .eq('id', asset_id_failed)\
                                        .execute()
                                except Exception as update_error:
                                    logger.error(f"Failed to update asset {asset_id_failed} status: {update_error}")
                            else:
                                logger.info(f"Successfully completed background generation for variation {i+1}")
                    except Exception as monitor_error:
                        logger.error(f"Error in generation monitoring: {monitor_error}")
                
                # Schedule the monitoring task
                asyncio.create_task(monitor_generations())
                
                logger.info(f"Successfully started refinement generation for {len(variation_asset_ids)} variations")
                
                return {
                    'original_asset_id': asset_id,
                    'variation_asset_ids': variation_asset_ids,
                    'credits_used': self.credit_cost,
                    'status': 'generating',
                    'message': f'Generating {len(variation_asset_ids)} variations of your logo'
                }
                
            except Exception as e:
                # Refund credits if generation setup fails
                await credit_service.refund_credits(
                    user_id=user_id,
                    amount=self.credit_cost,
                    reason=f"Simple refinement failed: {str(e)}",
                    asset_id=asset_id
                )
                raise
                
        except Exception as e:
            logger.error(f"Simple refinement failed for asset {asset_id}: {str(e)}")
            raise
    
    async def _get_asset(self, asset_id: str) -> Optional[Dict]:
        """Get asset data from database"""
        try:
            result = supabase_service.client.table('generated_assets')\
                .select('*')\
                .eq('id', asset_id)\
                .single()\
                .execute()
            return result.data
        except Exception as e:
            logger.error(f"Failed to get asset {asset_id}: {e}")
            return None
    
    async def _generate_variation_prompts(
        self, 
        original_asset: Dict,
        user_prompt: Optional[str] = None
    ) -> List[str]:
        """
        Generate 5 intelligent variation prompts using Gemini image analysis.
        ALWAYS generates 5 variations regardless of user input.
        
        Args:
            original_asset: Asset data including asset_url and generation_prompt
            user_prompt: Optional user's request for changes
            
        Returns:
            List of 5 intelligent variation prompts
        """
        try:
            logo_url = original_asset['asset_url']
            if not logo_url:
                logger.warning("No logo URL available, using prompt-based fallback")
                return self._get_prompt_based_variations(original_asset['generation_prompt'], user_prompt)
            
            # Use Gemini to analyze the actual logo image and generate intelligent variations
            logger.info(f"🎨 Analyzing logo image for intelligent variations: {user_prompt or 'automatic refinement'}")
            
            variation_prompts = await self.prompt_service.analyze_logo_for_variations(
                logo_url=logo_url,
                user_prompt=user_prompt
            )
            
            if len(variation_prompts) >= 5:
                logger.info(f"✅ Generated {len(variation_prompts)} intelligent variation prompts based on logo analysis")
                return variation_prompts[:5]
            else:
                logger.warning("Insufficient prompts from analysis, using fallback")
                return self._get_prompt_based_variations(original_asset['generation_prompt'], user_prompt)
            
        except Exception as e:
            logger.warning(f"Intelligent variation generation failed, using fallback: {e}")
            return self._get_prompt_based_variations(original_asset['generation_prompt'], user_prompt)
    
    def _get_prompt_based_variations(self, original_prompt: str, user_prompt: Optional[str] = None) -> List[str]:
        """
        Generate fallback variations based on the original prompt when image analysis fails.
        
        Args:
            original_prompt: The original prompt used for the logo
            user_prompt: Optional user's request for changes
            
        Returns:
            List of 5 design-principle-based variation prompts
        """
        base_request = user_prompt or "professional design refinement and enhancement"
        
        # Design-principle-based variations that work with any logo prompt
        variations = [
            f"{original_prompt}, {base_request}, minimalist approach with clean lines and increased white space",
            f"{original_prompt}, {base_request}, bold contemporary style with stronger visual impact", 
            f"{original_prompt}, {base_request}, organic flowing interpretation with softer edges and curves",
            f"{original_prompt}, {base_request}, technical precision enhancement with mathematical proportions",
            f"{original_prompt}, {base_request}, dynamic modern evolution with implied movement and energy"
        ]
        
        logger.info("Using design-principle-based prompt variations")
        return variations
    
    async def _generate_single_variation(
        self,
        original_asset_url: str,
        new_asset_id: str,
        prompt: str,
        variation_index: int
    ) -> bool:
        """
        Generate a single logo variation using image-to-image editing
        
        Args:
            original_asset_url: URL of the original logo image
            new_asset_id: Database ID for the new variation asset
            prompt: Generation prompt for this variation
            variation_index: Index of this variation (1-5)
            
        Returns:
            True if successful, False if failed
        """
        try:
            logger.info(f"Generating variation {variation_index} for asset {new_asset_id}")
            
            # Generate new logo using image-to-image editing
            # The generate_variation method handles all database updates internally
            result = await self.image_service.generate_variation(
                original_image_url=original_asset_url,
                modification_prompt=prompt,
                asset_id=new_asset_id
            )
            
            if result:
                logger.info(f"Successfully generated variation {variation_index}")
                return True
            else:
                logger.error(f"Failed to generate variation {variation_index}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to generate variation {variation_index}: {e}")
            return False
    
    async def get_refinement_progress(self, original_asset_id: str) -> Dict[str, Any]:
        """
        Get progress of refinement for an asset
        
        Args:
            original_asset_id: ID of the original asset being refined
            
        Returns:
            Dict with progress information
        """
        try:
            # Get all variation assets for this refinement
            result = supabase_service.client.table('generated_assets')\
                .select('id, status, asset_url, created_at')\
                .eq('parent_asset_id', original_asset_id)\
                .eq('asset_type', 'simple_refinement')\
                .execute()
            
            variations = result.data or []
            total_variations = len(variations)
            
            if total_variations == 0:
                return {
                    'status': 'not_found',
                    'message': 'No refinement found for this asset'
                }
            
            # Count completed variations
            completed = [v for v in variations if v['status'] == 'completed']
            failed = [v for v in variations if v['status'] == 'failed']
            generating = [v for v in variations if v['status'] == 'generating']
            
            completed_count = len(completed)
            failed_count = len(failed)
            generating_count = len(generating)
            
            if completed_count == total_variations:
                status = 'completed'
                message = f'All {total_variations} variations ready!'
            elif failed_count == total_variations:
                status = 'failed'
                message = 'All variations failed to generate'
            elif completed_count + failed_count == total_variations:
                status = 'completed'
                message = f'{completed_count} variations completed, {failed_count} failed'
            else:
                status = 'generating'
                message = f'Generated {completed_count}/{total_variations} variations...'
            
            return {
                'status': status,
                'message': message,
                'progress': {
                    'total': total_variations,
                    'completed': completed_count,
                    'failed': failed_count,
                    'generating': generating_count,
                    'percentage': (completed_count / total_variations) * 100 if total_variations > 0 else 0
                },
                'completed_variations': [
                    {
                        'id': v['id'],
                        'asset_url': v['asset_url'],
                        'created_at': v['created_at']
                    }
                    for v in completed
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get refinement progress: {e}")
            return {
                'status': 'error',
                'message': 'Failed to get refinement progress'
            }

# Export singleton instance
simple_refinement_service = SimpleRefinementService()