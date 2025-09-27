"""
Stripe Payment Service for LogoKraft
Handles payment intents, webhooks, and refunds for $29 brand kit purchases
"""

import stripe
import logging
from typing import Dict, Optional, Any
from datetime import datetime
import json

from app.config.settings import settings

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe payment operations"""
    
    def __init__(self):
        """Initialize Stripe with API key"""
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key
            logger.info("✅ Stripe service initialized")
        else:
            logger.warning("⚠️ Stripe secret key not configured")
    
    async def create_payment_intent(
        self,
        user_id: str,
        selected_asset_id: str,
        user_email: str,
        amount: int = 2900  # $29.00 in cents
    ) -> Dict[str, Any]:
        """
        Create a payment intent for brand kit purchase.
        
        Args:
            user_id: UUID of the purchasing user
            selected_asset_id: UUID of the selected logo asset
            user_email: User's email for receipt
            amount: Amount in cents (default $29.00)
            
        Returns:
            Dict containing payment intent details
        """
        try:
            # Create payment intent with metadata
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="usd",
                metadata={
                    "user_id": user_id,
                    "asset_id": selected_asset_id,
                    "product": "brand_kit",
                    "price": "29.00"
                },
                receipt_email=user_email,
                description="LogoKraft Brand Kit - Professional brand assets package",
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never"  # For embedded checkout
                }
            )
            
            logger.info(f"Created payment intent {payment_intent.id} for user {user_id}")
            
            return {
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            raise ValueError(f"Payment processing error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {e}")
            raise
    
    async def create_checkout_session(
        self,
        user_id: str,
        selected_asset_id: str,
        user_email: str,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for hosted payment page.
        
        Args:
            user_id: UUID of the purchasing user
            selected_asset_id: UUID of the selected logo asset
            user_email: User's email
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment cancelled
            
        Returns:
            Dict containing checkout session details
        """
        try:
            # Create line item for brand kit
            line_items = [{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "LogoKraft Brand Kit",
                        "description": "Complete brand identity package with 5 professional assets",
                        "images": ["https://logokraft.com/brand-kit-preview.png"]  # Add actual preview image
                    },
                    "unit_amount": 2900,  # $29.00
                },
                "quantity": 1,
            }]
            
            # Use configured price_id if available (for production)
            if settings.stripe_price_id:
                line_items = [{
                    "price": settings.stripe_price_id,
                    "quantity": 1,
                }]
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                metadata={
                    "user_id": user_id,
                    "asset_id": selected_asset_id,
                    "product": "brand_kit"
                },
                payment_intent_data={
                    "description": "LogoKraft Brand Kit Purchase",
                    "metadata": {
                        "user_id": user_id,
                        "asset_id": selected_asset_id
                    }
                }
            )
            
            logger.info(f"Created checkout session {session.id} for user {user_id}")
            
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "expires_at": session.expires_at
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise ValueError(f"Checkout session error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {e}")
            raise
    
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature and parse event.
        
        Args:
            payload: Raw request body
            signature: Stripe signature header
            
        Returns:
            Parsed and verified webhook event
        """
        try:
            if not settings.stripe_webhook_secret:
                logger.warning("Webhook secret not configured, skipping verification")
                return json.loads(payload)
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret
            )
            
            logger.info(f"Verified webhook event: {event['type']}")
            return event
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise ValueError("Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise
    
    async def retrieve_payment_intent(
        self,
        payment_intent_id: str
    ) -> Dict[str, Any]:
        """
        Retrieve payment intent details from Stripe.
        
        Args:
            payment_intent_id: Stripe payment intent ID
            
        Returns:
            Payment intent details
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return {
                "id": payment_intent.id,
                "amount": payment_intent.amount,
                "currency": payment_intent.currency,
                "status": payment_intent.status,
                "metadata": payment_intent.metadata,
                "receipt_email": payment_intent.receipt_email,
                "created": payment_intent.created,
                "charges": payment_intent.charges.data if payment_intent.charges else []
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving payment intent {payment_intent_id}: {e}")
            raise ValueError(f"Payment retrieval error: {str(e)}")
    
    async def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[int] = None,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """
        Create a refund for a payment.
        
        Args:
            payment_intent_id: Payment intent to refund
            amount: Amount to refund in cents (None for full refund)
            reason: Refund reason (requested_by_customer, duplicate, fraudulent)
            
        Returns:
            Refund details
        """
        try:
            refund_data = {
                "payment_intent": payment_intent_id,
                "reason": reason
            }
            
            if amount:
                refund_data["amount"] = amount
            
            refund = stripe.Refund.create(**refund_data)
            
            logger.info(f"Created refund {refund.id} for payment {payment_intent_id}")
            
            return {
                "refund_id": refund.id,
                "amount": refund.amount,
                "currency": refund.currency,
                "status": refund.status,
                "reason": refund.reason,
                "created": refund.created
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund for {payment_intent_id}: {e}")
            raise ValueError(f"Refund error: {str(e)}")
    
    async def list_customer_payments(
        self,
        user_email: str,
        limit: int = 10
    ) -> list:
        """
        List recent payments for a customer.
        
        Args:
            user_email: Customer email
            limit: Number of payments to retrieve
            
        Returns:
            List of payment records
        """
        try:
            # Search for customer by email
            customers = stripe.Customer.list(email=user_email, limit=1)
            
            if not customers.data:
                return []
            
            customer_id = customers.data[0].id
            
            # Get payment intents for customer
            payment_intents = stripe.PaymentIntent.list(
                customer=customer_id,
                limit=limit
            )
            
            return [
                {
                    "id": pi.id,
                    "amount": pi.amount,
                    "currency": pi.currency,
                    "status": pi.status,
                    "created": pi.created,
                    "description": pi.description
                }
                for pi in payment_intents.data
            ]
            
        except stripe.error.StripeError as e:
            logger.error(f"Error listing customer payments: {e}")
            return []
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return bool(settings.stripe_secret_key)


# Global instance
stripe_service = StripeService()