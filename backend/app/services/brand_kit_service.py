"""
Brand Kit Service - $29 Monetization Engine
Generates 5 professional brand components from selected logo
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional
from io import BytesIO
import json
from datetime import datetime, timedelta

from app.services.supabase_service import supabase_service
from app.services.image_generation_service import ImageGenerationService

logger = logging.getLogger(__name__)

class BrandKitService:
    """
    Core service for generating complete brand kits from selected logos.
    
    Generates 5 components:
    1. Business Cards (2 contrast versions)
    2. Website Mockup (homepage with logo)
    3. Social Media Headers (4 platforms)
    4. T-shirt Mockup (logo on apparel)
    5. Animated Logo (GIF + MP4)
    
    Price: $29 per brand kit
    """
    
    def __init__(self):
        self.image_service = ImageGenerationService()
        self.brand_kit_price = 29.00
        
        # Component generation templates
        self.component_templates = {
            "business_cards": {
                "prompt_template": "Professional business card design with {logo_description}, company name '{company_name}'. Create 2 versions side by side: left version with dark logo on light background, right version with light logo on dark background. Clean, modern layout with contact placeholders. High-quality print design, 3.5x2 inch business card proportions",
                "dimensions": {"width": 3000, "height": 2000},
                "format": "PNG"
            },
            "website_mockup": {
                "prompt_template": "Professional website homepage mockup featuring {logo_description} for '{company_name}'. Modern web design with logo in header, hero section, feature sections. Clean layout, responsive design aesthetic. Business website mockup, desktop view, high-quality web design",
                "dimensions": {"width": 1920, "height": 1080},
                "format": "PNG"
            },
            "social_headers": {
                "prompt_template": "Social media header bundle featuring {logo_description} for '{company_name}'. Create 4 headers in single image: Twitter (1500x500), LinkedIn (1584x396), Facebook (1200x630), YouTube (2560x1440). Professional branding, logo prominently positioned, modern design",
                "dimensions": {"width": 2560, "height": 1440},
                "format": "PNG"
            },
            "tshirt_mockup": {
                "prompt_template": "T-shirt mockup with {logo_description} for '{company_name}' on chest area. High-quality apparel mockup, professional model or flat lay, logo well-positioned, complementary t-shirt color, product photography style",
                "dimensions": {"width": 2000, "height": 2000},
                "format": "PNG"
            },
            "animated_logo": {
                "prompt_template": "Create animated version of {logo_description} for '{company_name}'. Subtle entrance animation (fade in, gentle scale, or soft rotation), professional motion graphics, 2-3 second duration, seamless loop, brand animation",
                "dimensions": {"width": 512, "height": 512},
                "format": "GIF"  # Will also generate MP4
            }
        }
    
    async def create_brand_kit_order(
        self,
        user_id: str,
        selected_asset_id: str,
        payment_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new brand kit order and start generation process.
        
        Args:
            user_id: ID of the user placing the order
            selected_asset_id: ID of the logo asset to use for brand kit
            payment_reference: Payment provider reference (e.g., Stripe payment intent)
            
        Returns:
            Dict with order details and generation status
        """
        try:
            logger.info(f"Creating brand kit order for user {user_id} with asset {selected_asset_id}")
            
            # Create order using secure RPC function
            result = supabase_service.client.rpc(
                'create_brand_kit_order',
                {
                    'p_user_id': user_id,
                    'p_selected_asset_id': selected_asset_id,
                    'p_payment_amount': self.brand_kit_price,
                    'p_payment_reference': payment_reference
                }
            ).execute()
            
            if not result.data:
                raise Exception("Failed to create brand kit order")
            
            order_id = result.data
            logger.info(f"Brand kit order created: {order_id}")
            
            # Get selected asset details for generation
            asset_data = await self._get_asset_details(selected_asset_id)
            if not asset_data:
                raise ValueError(f"Selected asset {selected_asset_id} not found")
            
            # Start background generation process
            asyncio.create_task(
                self._generate_complete_brand_kit(order_id, asset_data)
            )
            
            return {
                "order_id": order_id,
                "status": "processing",
                "estimated_completion_minutes": 5,
                "message": f"Brand kit generation started for ${self.brand_kit_price}. You'll receive updates in real-time.",
                "components": list(self.component_templates.keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to create brand kit order: {e}")
            raise
    
    async def _generate_complete_brand_kit(
        self,
        order_id: str,
        asset_data: Dict[str, Any]
    ) -> bool:
        """
        Generate all 5 brand kit components in sequence with progress updates.
        
        Args:
            order_id: UUID of the brand kit order
            asset_data: Details of the selected logo asset
            
        Returns:
            True if all components generated successfully
        """
        try:
            logger.info(f"Starting complete brand kit generation for order {order_id}")
            
            # Update order status to processing
            await self._update_order_status(order_id, "processing")
            
            # Extract company name and logo description
            company_name = asset_data.get('project_name', 'Your Company')
            logo_description = asset_data.get('generation_prompt', 'modern professional logo design')
            logo_url = asset_data.get('asset_url')
            
            # Generate each component sequentially
            component_results = {}
            
            for component_name, template in self.component_templates.items():
                logger.info(f"Generating {component_name} for order {order_id}")
                
                try:
                    # Generate the component
                    component_url = await self._generate_single_component(
                        component_name=component_name,
                        template=template,
                        company_name=company_name,
                        logo_description=logo_description,
                        original_logo_url=logo_url
                    )
                    
                    if component_url:
                        component_results[component_name] = component_url
                        
                        # Update progress in database
                        await self._update_component_progress(
                            order_id=order_id,
                            component_name=component_name,
                            component_url=component_url
                        )
                        
                        logger.info(f"✅ {component_name} completed for order {order_id}")
                    else:
                        raise Exception(f"Failed to generate {component_name}")
                        
                except Exception as e:
                    logger.error(f"Failed to generate {component_name} for order {order_id}: {e}")
                    # Continue with other components but log the failure
                    await self._update_component_progress(
                        order_id=order_id,
                        component_name=component_name,
                        component_url=None,
                        error=str(e)
                    )
            
            # Check if we have enough components to consider the order successful
            success_count = len([url for url in component_results.values() if url])
            total_components = len(self.component_templates)
            
            if success_count >= 3:  # At least 3/5 components must succeed
                logger.info(f"Brand kit generation completed: {success_count}/{total_components} components successful")
                return True
            else:
                logger.error(f"Brand kit generation failed: only {success_count}/{total_components} components successful")
                await self._update_order_status(order_id, "failed", f"Only {success_count}/{total_components} components generated successfully")
                return False
                
        except Exception as e:
            logger.error(f"Brand kit generation failed for order {order_id}: {e}")
            await self._update_order_status(order_id, "failed", str(e))
            return False
    
    async def _generate_single_component(
        self,
        component_name: str,
        template: Dict[str, Any],
        company_name: str,
        logo_description: str,
        original_logo_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a single brand kit component.
        
        Args:
            component_name: Name of component to generate
            template: Template configuration for this component
            company_name: Company name for personalization
            logo_description: Description of the original logo
            original_logo_url: URL of original logo (for reference)
            
        Returns:
            URL of generated component or None if failed
        """
        try:
            # Format the prompt with company details
            prompt = template["prompt_template"].format(
                company_name=company_name,
                logo_description=logo_description
            )
            
            logger.info(f"Generating {component_name} with prompt: {prompt[:100]}...")
            
            # Generate using image generation service
            # For now, we'll use standard image generation
            # In production, this could use specialized services for each component type
            
            # Create a temporary asset ID for this component
            temp_asset_id = str(uuid.uuid4())
            
            # Generate the component image
            result = await self.image_service.generate_image(
                prompt=prompt,
                asset_id=temp_asset_id,
                image_size=template["dimensions"]["width"]  # Use width as size parameter
            )
            
            if result and result.get("success"):
                component_url = result.get("asset_url")
                logger.info(f"Successfully generated {component_name}: {component_url}")
                return component_url
            else:
                logger.error(f"Image generation failed for {component_name}: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate {component_name}: {e}")
            return None
    
    async def _get_asset_details(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get details of the selected asset including project info."""
        try:
            result = supabase_service.client.table('generated_assets')\
                .select('*, brand_projects!inner(project_name, user_id)')\
                .eq('id', asset_id)\
                .single()\
                .execute()
            
            if result.data:
                # Flatten the project data
                asset_data = dict(result.data)
                if 'brand_projects' in asset_data:
                    project_data = asset_data.pop('brand_projects')
                    asset_data.update(project_data)
                
                return asset_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get asset details for {asset_id}: {e}")
            return None
    
    async def _update_order_status(
        self,
        order_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """Update the overall order status."""
        try:
            update_data = {
                "order_status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            supabase_service.client.table('brand_kit_orders')\
                .update(update_data)\
                .eq('id', order_id)\
                .execute()
            
            logger.info(f"Updated order {order_id} status to {status}")
            
        except Exception as e:
            logger.error(f"Failed to update order status for {order_id}: {e}")
    
    async def _update_component_progress(
        self,
        order_id: str,
        component_name: str,
        component_url: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update progress for a specific component."""
        try:
            # Use the secure RPC function to update progress
            result = supabase_service.client.rpc(
                'update_brand_kit_progress',
                {
                    'p_order_id': order_id,
                    'p_component_name': component_name,
                    'p_component_url': component_url,
                    'p_component_metadata': json.dumps({
                        'generated_at': datetime.utcnow().isoformat(),
                        'error': error
                    }) if error else '{}'
                }
            ).execute()
            
            if result.data:
                logger.info(f"Updated {component_name} progress for order {order_id}")
            
        except Exception as e:
            logger.error(f"Failed to update component progress: {e}")
    
    async def get_order_status(self, order_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get the current status of a brand kit order.
        
        Args:
            order_id: UUID of the brand kit order
            user_id: ID of the user (for authorization)
            
        Returns:
            Dict with order status and component progress
        """
        try:
            result = supabase_service.client.table('brand_kit_orders')\
                .select('*')\
                .eq('id', order_id)\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            if not result.data:
                return {
                    "status": "not_found",
                    "message": "Brand kit order not found"
                }
            
            order_data = result.data
            progress = order_data.get('generation_progress', {})
            components = order_data.get('brand_kit_components', {})
            
            # Count completed components
            completed_count = sum(1 for completed in progress.values() if completed)
            total_count = len(self.component_templates)
            
            return {
                "order_id": order_id,
                "status": order_data['order_status'],
                "progress": {
                    "completed": completed_count,
                    "total": total_count,
                    "percentage": (completed_count / total_count) * 100
                },
                "components": components,
                "created_at": order_data['created_at'],
                "completed_at": order_data.get('completed_at'),
                "payment_amount": float(order_data['payment_amount']),
                "error_message": order_data.get('error_message')
            }
            
        except Exception as e:
            logger.error(f"Failed to get order status for {order_id}: {e}")
            return {
                "status": "error",
                "message": f"Failed to get order status: {str(e)}"
            }
    
    async def process_paid_brand_kit_order(
        self,
        order_id: str,
        payment_reference: str
    ) -> Dict[str, Any]:
        """
        Process a brand kit order after payment confirmation.
        Called from Stripe webhook when payment succeeds.
        
        Args:
            order_id: UUID of the brand kit order
            payment_reference: Stripe payment intent ID
            
        Returns:
            Dict with processing status
        """
        try:
            logger.info(f"Processing paid brand kit order {order_id} with payment {payment_reference}")
            
            # Get order details
            result = await supabase_service.client.table('brand_kit_orders').select(
                'id, user_id, selected_asset_id, order_status, payment_status'
            ).eq('id', order_id).eq('payment_reference', payment_reference).single().execute()
            
            if not result.data:
                raise ValueError(f"Order {order_id} not found or payment reference mismatch")
            
            order = result.data
            
            # Verify payment is confirmed
            if order['payment_status'] != 'completed':
                logger.warning(f"Order {order_id} payment not confirmed yet, status: {order['payment_status']}")
                return {"status": "waiting_for_payment"}
            
            # Start generation process in background
            asyncio.create_task(
                self._process_brand_kit_generation(
                    order_id=order['id'],
                    selected_asset_id=order['selected_asset_id']
                )
            )
            
            logger.info(f"Started brand kit generation for order {order_id}")
            
            return {
                "status": "processing",
                "order_id": order_id,
                "message": "Brand kit generation started"
            }
            
        except Exception as e:
            logger.error(f"Failed to process paid brand kit order {order_id}: {e}")
            # Update order status to failed
            await supabase_service.client.table('brand_kit_orders').update({
                'order_status': 'failed',
                'error_message': str(e)
            }).eq('id', order_id).execute()
            
            raise ValueError(f"Failed to process order: {str(e)}")

# Export singleton instance
brand_kit_service = BrandKitService()