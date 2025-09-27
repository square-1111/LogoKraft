"""
OAuth Service for LogoKraft
Handles Google and GitHub authentication via Supabase
"""

import logging
import secrets
import urllib.parse
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from app.services.supabase_service import supabase_service
from app.config.settings import settings

logger = logging.getLogger(__name__)


class OAuthService:
    """Service for handling OAuth authentication with Google and GitHub via Supabase"""
    
    def __init__(self):
        self.oauth_state_cache = {}  # In production, use Redis
        self.supported_providers = ['google', 'github']
    
    async def get_oauth_url(
        self, 
        provider: str, 
        redirect_url: str
    ) -> Dict[str, str]:
        """
        Generate OAuth authorization URL for the specified provider.
        
        Args:
            provider: OAuth provider (google, github)
            redirect_url: Frontend URL to redirect after authentication
            
        Returns:
            Dict containing OAuth URL and state parameter
        """
        try:
            if provider not in self.supported_providers:
                raise ValueError(f"Unsupported OAuth provider: {provider}")
            
            # Generate CSRF state parameter
            state = secrets.token_urlsafe(32)
            
            # Store state with expiration (10 minutes)
            self.oauth_state_cache[state] = {
                'provider': provider,
                'redirect_url': redirect_url,
                'expires_at': datetime.utcnow() + timedelta(minutes=10)
            }
            
            # Get OAuth URL from Supabase Auth
            auth_response = supabase_service.client.auth.sign_in_with_oauth({
                'provider': provider,
                'options': {
                    'redirect_to': f"{settings.supabase_url}/auth/v1/callback?redirect_to={redirect_url}",
                    'scopes': self._get_provider_scopes(provider)
                }
            })
            
            # Extract the authorization URL
            oauth_url = auth_response.url if hasattr(auth_response, 'url') else None
            
            if not oauth_url:
                raise Exception(f"Failed to generate OAuth URL for {provider}")
            
            # Add our state parameter to the URL
            parsed_url = urllib.parse.urlparse(oauth_url)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            query_params['state'] = [state]
            
            new_query = urllib.parse.urlencode(query_params, doseq=True)
            final_url = urllib.parse.urlunparse((
                parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                parsed_url.params, new_query, parsed_url.fragment
            ))
            
            logger.info(f"Generated OAuth URL for {provider}")
            
            return {
                'url': final_url,
                'state': state
            }
            
        except Exception as e:
            logger.error(f"Failed to generate OAuth URL for {provider}: {e}")
            raise ValueError(f"OAuth URL generation failed: {str(e)}")
    
    async def handle_oauth_callback(
        self, 
        code: str, 
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle OAuth callback with authorization code.
        
        Args:
            code: Authorization code from OAuth provider
            state: State parameter for CSRF protection
            
        Returns:
            Dict containing user data and tokens
        """
        try:
            # Verify state parameter
            if state and state in self.oauth_state_cache:
                state_data = self.oauth_state_cache[state]
                
                # Check if state has expired
                if datetime.utcnow() > state_data['expires_at']:
                    del self.oauth_state_cache[state]
                    raise ValueError("OAuth state has expired")
                
                provider = state_data['provider']
                redirect_url = state_data['redirect_url']
                
                # Clean up state
                del self.oauth_state_cache[state]
                
            else:
                logger.warning("OAuth callback received without valid state")
                # For backward compatibility, we'll continue without state validation
                provider = 'google'  # Default fallback
                redirect_url = None
            
            # Exchange code for session using Supabase
            auth_response = supabase_service.client.auth.exchange_code_for_session({
                'auth_code': code
            })
            
            if not auth_response.user:
                raise Exception("Failed to authenticate with OAuth provider")
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            # Extract user information
            user_info = {
                'id': user_data.id,
                'email': user_data.email,
                'full_name': user_data.user_metadata.get('full_name') or user_data.user_metadata.get('name'),
                'avatar_url': user_data.user_metadata.get('avatar_url') or user_data.user_metadata.get('picture'),
                'provider': provider
            }
            
            # Create or update user in our users table
            await self._create_or_update_oauth_user(user_info)
            
            logger.info(f"OAuth authentication successful for user {user_data.email} via {provider}")
            
            return {
                'user': user_info,
                'access_token': session_data.access_token if session_data else None,
                'refresh_token': session_data.refresh_token if session_data else None,
                'redirect_url': redirect_url
            }
            
        except Exception as e:
            logger.error(f"OAuth callback handling failed: {e}")
            raise ValueError(f"OAuth authentication failed: {str(e)}")
    
    async def refresh_oauth_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh OAuth access token using refresh token.
        
        Args:
            refresh_token: Refresh token from previous authentication
            
        Returns:
            Dict containing new tokens and user data
        """
        try:
            # Refresh session using Supabase
            auth_response = supabase_service.client.auth.refresh_session(refresh_token)
            
            if not auth_response.user or not auth_response.session:
                raise Exception("Failed to refresh OAuth token")
            
            user_data = auth_response.user
            session_data = auth_response.session
            
            # Extract updated user information
            user_info = {
                'id': user_data.id,
                'email': user_data.email,
                'full_name': user_data.user_metadata.get('full_name') or user_data.user_metadata.get('name'),
                'avatar_url': user_data.user_metadata.get('avatar_url') or user_data.user_metadata.get('picture'),
                'provider': user_data.app_metadata.get('provider', 'email')
            }
            
            logger.info(f"OAuth token refresh successful for user {user_data.email}")
            
            return {
                'user': user_info,
                'access_token': session_data.access_token,
                'refresh_token': session_data.refresh_token
            }
            
        except Exception as e:
            logger.error(f"OAuth token refresh failed: {e}")
            raise ValueError(f"Token refresh failed: {str(e)}")
    
    async def revoke_oauth_session(self, access_token: str) -> bool:
        """
        Revoke OAuth session and logout user.
        
        Args:
            access_token: Current access token
            
        Returns:
            True if successful
        """
        try:
            # Set the session for the client
            supabase_service.client.auth.set_session(access_token, None)
            
            # Sign out the user
            supabase_service.client.auth.sign_out()
            
            logger.info("OAuth session revoked successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke OAuth session: {e}")
            return False
    
    async def _create_or_update_oauth_user(self, user_info: Dict[str, Any]) -> None:
        """
        Create or update user record in our users table.
        
        Args:
            user_info: User information from OAuth provider
        """
        try:
            # Check if user already exists
            existing_user = await supabase_service.client.table('users').select('*').eq('id', user_info['id']).execute()
            
            user_data = {
                'id': user_info['id'],
                'email': user_info['email'],
                'full_name': user_info.get('full_name'),
                'avatar_url': user_info.get('avatar_url'),
                'provider': user_info.get('provider', 'email'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            if existing_user.data:
                # Update existing user
                await supabase_service.client.table('users').update(user_data).eq('id', user_info['id']).execute()
                logger.info(f"Updated OAuth user record for {user_info['email']}")
            else:
                # Create new user
                user_data['created_at'] = datetime.utcnow().isoformat()
                user_data['credits'] = 100  # Give new OAuth users 100 credits
                await supabase_service.client.table('users').insert(user_data).execute()
                logger.info(f"Created new OAuth user record for {user_info['email']}")
                
        except Exception as e:
            logger.error(f"Failed to create/update OAuth user: {e}")
            # Don't raise - this shouldn't block OAuth authentication
    
    def _get_provider_scopes(self, provider: str) -> str:
        """
        Get OAuth scopes for the specified provider.
        
        Args:
            provider: OAuth provider name
            
        Returns:
            Space-separated scope string
        """
        scopes = {
            'google': 'openid email profile',
            'github': 'user:email'
        }
        
        return scopes.get(provider, '')
    
    def _cleanup_expired_states(self) -> None:
        """Clean up expired OAuth states from cache."""
        current_time = datetime.utcnow()
        expired_states = [
            state for state, data in self.oauth_state_cache.items()
            if current_time > data['expires_at']
        ]
        
        for state in expired_states:
            del self.oauth_state_cache[state]
        
        if expired_states:
            logger.info(f"Cleaned up {len(expired_states)} expired OAuth states")


# Global instance
oauth_service = OAuthService()