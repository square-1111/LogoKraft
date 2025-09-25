"""
Credit Service - Production Implementation
Manages user credits for logo generation and refinement operations.
Uses secure database functions with atomic transactions.
"""

import logging
from typing import Optional
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

class CreditService:
    """
    Production service for managing user credits.
    
    Uses secure PostgreSQL functions to ensure:
    - Atomic credit operations
    - Transaction safety
    - Audit trail via credit_transactions table
    """
    
    async def check_credits(self, user_id: str, amount: int) -> bool:
        """
        Check if user has sufficient credits.
        
        Args:
            user_id: User ID to check credits for
            amount: Number of credits required
            
        Returns:
            True if user has sufficient credits
        """
        try:
            result = supabase_service.client.rpc(
                'check_user_credits',
                {
                    'p_user_id': user_id,
                    'p_required_credits': amount
                }
            ).execute()
            
            has_credits = result.data if result.data is not None else False
            logger.info(f"Credit check: user {user_id} needs {amount} credits - {'APPROVED' if has_credits else 'DENIED'}")
            return has_credits
            
        except Exception as e:
            logger.error(f"Credit check failed for user {user_id}: {e}")
            return False
    
    async def deduct_credits(
        self, 
        user_id: str, 
        amount: int, 
        reason: str,
        asset_id: Optional[str] = None
    ) -> bool:
        """
        Deduct credits from user account atomically.
        
        Args:
            user_id: User ID to deduct credits from
            amount: Number of credits to deduct
            reason: Reason for credit deduction
            asset_id: Optional asset ID for tracking
            
        Returns:
            True if deduction successful
        """
        try:
            result = supabase_service.client.rpc(
                'deduct_user_credits',
                {
                    'p_user_id': user_id,
                    'p_credits': amount,
                    'p_reason': reason,
                    'p_asset_id': asset_id
                }
            ).execute()
            
            success = result.data if result.data is not None else False
            
            if success:
                logger.info(f"Credit deduction: user {user_id} - {amount} credits for '{reason}' - SUCCESS")
            else:
                logger.warning(f"Credit deduction: user {user_id} - {amount} credits for '{reason}' - FAILED (insufficient credits)")
            
            return success
            
        except Exception as e:
            logger.error(f"Credit deduction failed for user {user_id}: {e}")
            return False
    
    async def refund_credits(
        self,
        user_id: str,
        amount: int,
        reason: str,
        asset_id: Optional[str] = None
    ) -> bool:
        """
        Refund credits to user account.
        
        Args:
            user_id: User ID to refund credits to
            amount: Number of credits to refund
            reason: Reason for credit refund
            asset_id: Optional asset ID for tracking
            
        Returns:
            True if refund successful
        """
        try:
            # Add credits back (negative deduction)
            result = supabase_service.client.rpc(
                'deduct_user_credits',
                {
                    'p_user_id': user_id,
                    'p_credits': -amount,  # Negative deduction = addition
                    'p_reason': f"REFUND: {reason}",
                    'p_asset_id': asset_id
                }
            ).execute()
            
            success = result.data if result.data is not None else False
            
            if success:
                logger.info(f"Credit refund: user {user_id} + {amount} credits for '{reason}' - SUCCESS")
            else:
                logger.error(f"Credit refund: user {user_id} + {amount} credits for '{reason}' - FAILED")
            
            return success
            
        except Exception as e:
            logger.error(f"Credit refund failed for user {user_id}: {e}")
            return False
    
    async def get_credit_balance(self, user_id: str) -> int:
        """
        Get current credit balance for user.
        
        Args:
            user_id: User ID to get balance for
            
        Returns:
            Credit balance (0 if user not found or error)
        """
        try:
            result = supabase_service.client.table('user_credits')\
                .select('credits')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            if result.data:
                credits = result.data['credits']
                logger.info(f"Credit balance: user {user_id} has {credits} credits")
                return credits
            else:
                logger.warning(f"Credit balance: user {user_id} not found, returning 0")
                return 0
                
        except Exception as e:
            logger.error(f"Failed to get credit balance for user {user_id}: {e}")
            return 0

# Export singleton instance
credit_service = CreditService()