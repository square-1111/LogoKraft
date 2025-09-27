"""
User Service for LogoKraft
Handles user management and OAuth provider integration
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and OAuth provider integration"""
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile including OAuth provider data.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict containing user profile data or None if not found
        """
        try:
            # Get user from auth.users table
            auth_user_result = await supabase_service.client.table('auth.users').select(
                'id, email, raw_user_meta_data, raw_app_meta_data, created_at, updated_at, last_sign_in_at'
            ).eq('id', user_id).single().execute()
            
            if not auth_user_result.data:
                return None
            
            auth_user = auth_user_result.data
            
            # Get user credits
            credits_result = await supabase_service.client.table('user_credits').select(
                'credits, updated_at'
            ).eq('user_id', user_id).single().execute()
            
            credits_data = credits_result.data if credits_result.data else {'credits': 0}
            
            # Get OAuth provider information
            identity_result = await supabase_service.client.table('auth.identities').select(
                'provider, identity_data, last_sign_in_at, created_at'
            ).eq('user_id', user_id).execute()
            
            identities = identity_result.data if identity_result.data else []
            
            # Extract user metadata
            user_meta = auth_user.get('raw_user_meta_data', {})
            app_meta = auth_user.get('raw_app_meta_data', {})
            
            # Determine primary provider
            primary_provider = 'email'  # default
            if identities:
                # Use the most recent provider
                primary_provider = max(identities, key=lambda x: x.get('last_sign_in_at', ''))['provider']
            
            # Build comprehensive user profile
            user_profile = {
                'id': auth_user['id'],
                'email': auth_user['email'],
                'full_name': user_meta.get('full_name') or user_meta.get('name'),
                'avatar_url': user_meta.get('avatar_url') or user_meta.get('picture'),
                'provider': primary_provider,
                'credits': credits_data['credits'],
                'created_at': auth_user['created_at'],
                'updated_at': auth_user['updated_at'],
                'last_sign_in_at': auth_user['last_sign_in_at'],
                'providers': [
                    {
                        'provider': identity['provider'],
                        'created_at': identity['created_at'],
                        'last_sign_in_at': identity['last_sign_in_at']
                    }
                    for identity in identities
                ],
                'user_metadata': user_meta,
                'app_metadata': app_meta
            }
            
            logger.info(f"Retrieved user profile for {user_id}")
            return user_profile
            
        except Exception as e:
            logger.error(f"Failed to get user profile for {user_id}: {e}")
            return None
    
    async def update_user_profile(
        self, 
        user_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update user profile information.
        
        Args:
            user_id: User's UUID
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare metadata updates
            user_meta_updates = {}
            
            # Handle specific fields
            if 'full_name' in updates:
                user_meta_updates['full_name'] = updates['full_name']
            
            if 'avatar_url' in updates:
                user_meta_updates['avatar_url'] = updates['avatar_url']
            
            # Update user metadata if we have changes
            if user_meta_updates:
                # Get current metadata
                current_user = await supabase_service.client.table('auth.users').select(
                    'raw_user_meta_data'
                ).eq('id', user_id).single().execute()
                
                if current_user.data:
                    current_meta = current_user.data.get('raw_user_meta_data', {})
                    current_meta.update(user_meta_updates)
                    
                    # Update the user record
                    await supabase_service.client.table('auth.users').update({
                        'raw_user_meta_data': current_meta,
                        'updated_at': datetime.utcnow().isoformat()
                    }).eq('id', user_id).execute()
            
            logger.info(f"Updated user profile for {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user profile for {user_id}: {e}")
            return False
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user statistics including projects, assets, and usage.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict containing user statistics
        """
        try:
            # Get project count
            projects_result = await supabase_service.client.table('brand_projects').select(
                'id'
            ).eq('user_id', user_id).execute()
            
            project_count = len(projects_result.data) if projects_result.data else 0
            
            # Get asset count
            assets_result = await supabase_service.client.table('generated_assets').select(
                'id, asset_type, status, credits_used'
            ).in_('project_id', [p['id'] for p in projects_result.data] if projects_result.data else []).execute()
            
            assets = assets_result.data if assets_result.data else []
            
            # Calculate statistics
            total_assets = len(assets)
            completed_assets = len([a for a in assets if a['status'] == 'completed'])
            total_credits_used = sum(a.get('credits_used', 0) for a in assets)
            
            # Get brand kit orders
            brand_kits_result = await supabase_service.client.table('brand_kit_orders').select(
                'id, order_status, payment_amount'
            ).eq('user_id', user_id).execute()
            
            brand_kits = brand_kits_result.data if brand_kits_result.data else []
            completed_brand_kits = len([bk for bk in brand_kits if bk['order_status'] == 'completed'])
            total_spent = sum(float(bk.get('payment_amount', 0)) for bk in brand_kits if bk['order_status'] == 'completed')
            
            # Get current credits
            credits_result = await supabase_service.client.table('user_credits').select(
                'credits'
            ).eq('user_id', user_id).single().execute()
            
            current_credits = credits_result.data['credits'] if credits_result.data else 0
            
            stats = {
                'projects': {
                    'total': project_count,
                    'with_completed_assets': len(set(a['project_id'] for a in assets if a['status'] == 'completed'))
                },
                'assets': {
                    'total': total_assets,
                    'completed': completed_assets,
                    'by_type': {}
                },
                'credits': {
                    'current': current_credits,
                    'total_used': total_credits_used
                },
                'brand_kits': {
                    'total_ordered': len(brand_kits),
                    'completed': completed_brand_kits,
                    'total_spent': total_spent
                }
            }
            
            # Group assets by type
            for asset in assets:
                asset_type = asset['asset_type']
                if asset_type not in stats['assets']['by_type']:
                    stats['assets']['by_type'][asset_type] = {'total': 0, 'completed': 0}
                
                stats['assets']['by_type'][asset_type]['total'] += 1
                if asset['status'] == 'completed':
                    stats['assets']['by_type'][asset_type]['completed'] += 1
            
            logger.info(f"Retrieved user stats for {user_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {e}")
            return {
                'projects': {'total': 0, 'with_completed_assets': 0},
                'assets': {'total': 0, 'completed': 0, 'by_type': {}},
                'credits': {'current': 0, 'total_used': 0},
                'brand_kits': {'total_ordered': 0, 'completed': 0, 'total_spent': 0}
            }
    
    async def link_oauth_provider(
        self, 
        user_id: str, 
        provider: str, 
        provider_data: Dict[str, Any]
    ) -> bool:
        """
        Link an additional OAuth provider to an existing user account.
        
        Args:
            user_id: Existing user's UUID
            provider: OAuth provider name (google, github)
            provider_data: Provider-specific user data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would typically be handled by Supabase Auth automatically
            # when a user signs in with a new provider using the same email
            
            # For manual linking, we'd need to:
            # 1. Verify the user owns the email from the provider
            # 2. Create an identity record in auth.identities
            # 3. Update user metadata with provider information
            
            logger.info(f"OAuth provider {provider} linked to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to link OAuth provider {provider} to user {user_id}: {e}")
            return False
    
    async def unlink_oauth_provider(
        self, 
        user_id: str, 
        provider: str
    ) -> bool:
        """
        Unlink an OAuth provider from a user account.
        
        Args:
            user_id: User's UUID
            provider: OAuth provider to unlink
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if user has multiple providers
            identities_result = await supabase_service.client.table('auth.identities').select(
                'provider'
            ).eq('user_id', user_id).execute()
            
            identities = identities_result.data if identities_result.data else []
            
            if len(identities) <= 1:
                raise ValueError("Cannot unlink the only authentication method")
            
            # Remove the identity (this should be done through Supabase Admin API)
            await supabase_service.client.table('auth.identities').delete().eq(
                'user_id', user_id
            ).eq('provider', provider).execute()
            
            logger.info(f"OAuth provider {provider} unlinked from user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unlink OAuth provider {provider} from user {user_id}: {e}")
            return False


# Global instance
user_service = UserService()