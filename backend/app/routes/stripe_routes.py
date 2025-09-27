"""
Stripe webhook and payment routes for LogoKraft
Handles payment confirmations and webhook events
"""

from fastapi import APIRouter, HTTPException, Request, Header, Depends, status
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import json

from app.models.schemas import UserResponse
from app.services.stripe_service import stripe_service
from app.services.brand_kit_service import brand_kit_service
from app.services.supabase_service import supabase_service
from app.routes.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/stripe",
    tags=["Stripe"],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal Server Error"}
    }
)


@router.post("/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook endpoint",
    description="Receives and processes Stripe webhook events for payment confirmation"
)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """
    Handle Stripe webhook events.
    
    Processes:
    - payment_intent.succeeded: Confirms brand kit purchase
    - payment_intent.payment_failed: Handles failed payments
    - checkout.session.completed: Alternative payment confirmation
    
    Args:
        request: Raw request with body
        stripe_signature: Stripe signature header for verification
    
    Returns:
        Success acknowledgment for Stripe
    """
    try:
        # Get raw body for signature verification
        payload = await request.body()
        
        # Verify webhook signature and parse event
        event = await stripe_service.verify_webhook_signature(
            payload,
            stripe_signature
        )
        
        logger.info(f"Processing webhook event: {event['type']}")
        
        # Handle different event types
        if event['type'] == 'payment_intent.succeeded':
            await handle_payment_success(event['data']['object'])
            
        elif event['type'] == 'payment_intent.payment_failed':
            await handle_payment_failure(event['data']['object'])
            
        elif event['type'] == 'checkout.session.completed':
            await handle_checkout_completed(event['data']['object'])
            
        elif event['type'] == 'charge.refunded':
            await handle_refund(event['data']['object'])
            
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        # Return success to Stripe
        return {"status": "success", "event_type": event['type']}
        
    except ValueError as e:
        # Invalid signature or verification failed
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Return 200 to prevent Stripe retries for processing errors
        return {"status": "error", "message": str(e)}


async def handle_payment_success(payment_intent: dict):
    """
    Process successful payment and trigger brand kit generation.
    
    Args:
        payment_intent: Stripe payment intent object
    """
    try:
        metadata = payment_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        asset_id = metadata.get('asset_id')
        
        if not user_id or not asset_id:
            logger.error(f"Missing metadata in payment intent {payment_intent['id']}")
            return
        
        logger.info(f"Payment successful for user {user_id}, asset {asset_id}")
        
        # Update brand kit order status
        await supabase_service.client.table('brand_kit_orders').update({
            'payment_status': 'completed',
            'payment_reference': payment_intent['id'],
            'payment_confirmed_at': 'now()',
            'order_status': 'processing'
        }).eq('user_id', user_id).eq('selected_asset_id', asset_id).eq('order_status', 'pending').execute()
        
        # Find the order and start generation
        result = await supabase_service.client.table('brand_kit_orders').select('*').eq(
            'payment_reference', payment_intent['id']
        ).single().execute()
        
        if result.data:
            order = result.data
            # Trigger brand kit generation using the paid order processor
            logger.info(f"Starting brand kit generation for order {order['id']}")
            await brand_kit_service.process_paid_brand_kit_order(
                order_id=order['id'],
                payment_reference=payment_intent['id']
            )
        
    except Exception as e:
        logger.error(f"Error processing payment success: {e}")
        # Don't raise - we don't want Stripe to retry


async def handle_payment_failure(payment_intent: dict):
    """
    Handle failed payment attempts.
    
    Args:
        payment_intent: Stripe payment intent object
    """
    try:
        metadata = payment_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        asset_id = metadata.get('asset_id')
        
        logger.warning(f"Payment failed for user {user_id}, asset {asset_id}")
        
        # Update order status if exists
        if user_id and asset_id:
            await supabase_service.client.table('brand_kit_orders').update({
                'payment_status': 'failed',
                'payment_reference': payment_intent['id'],
                'error_message': payment_intent.get('last_payment_error', {}).get('message', 'Payment failed')
            }).eq('user_id', user_id).eq('selected_asset_id', asset_id).eq('order_status', 'pending').execute()
        
    except Exception as e:
        logger.error(f"Error processing payment failure: {e}")


async def handle_checkout_completed(session: dict):
    """
    Handle completed checkout session (alternative to payment_intent.succeeded).
    
    Args:
        session: Stripe checkout session object
    """
    try:
        # Extract payment intent ID from session
        payment_intent_id = session.get('payment_intent')
        
        if payment_intent_id:
            # Retrieve full payment intent details
            payment_intent = await stripe_service.retrieve_payment_intent(payment_intent_id)
            
            # Process as successful payment
            await handle_payment_success(payment_intent)
        
    except Exception as e:
        logger.error(f"Error processing checkout completion: {e}")


async def handle_refund(charge: dict):
    """
    Handle refund events.
    
    Args:
        charge: Stripe charge object with refund details
    """
    try:
        payment_intent_id = charge.get('payment_intent')
        refunded_amount = charge.get('amount_refunded', 0)
        
        logger.info(f"Refund processed for payment {payment_intent_id}: ${refunded_amount/100:.2f}")
        
        # Update order status
        if payment_intent_id:
            await supabase_service.client.table('brand_kit_orders').update({
                'order_status': 'refunded',
                'refunded_amount': refunded_amount / 100,  # Convert to dollars
                'refunded_at': 'now()'
            }).eq('payment_reference', payment_intent_id).execute()
        
    except Exception as e:
        logger.error(f"Error processing refund: {e}")


@router.post("/create-payment-intent",
    status_code=status.HTTP_201_CREATED,
    summary="Create payment intent for brand kit",
    description="Create a Stripe payment intent for embedded checkout"
)
async def create_payment_intent(
    selected_asset_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a payment intent for brand kit purchase.
    
    Args:
        selected_asset_id: ID of the selected logo asset
        current_user: Authenticated user from JWT
        
    Returns:
        Payment intent details including client secret
    """
    try:
        # Verify user owns the asset
        asset_result = await supabase_service.client.table('generated_assets').select(
            'id, project_id'
        ).eq('id', selected_asset_id).single().execute()
        
        if not asset_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        project_result = await supabase_service.client.table('brand_projects').select(
            'user_id'
        ).eq('id', asset_result.data['project_id']).single().execute()
        
        if not project_result.data or project_result.data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this asset"
            )
        
        # Create payment intent
        payment_intent = await stripe_service.create_payment_intent(
            user_id=current_user.id,
            selected_asset_id=selected_asset_id,
            user_email=current_user.email
        )
        
        # Create pending order in database
        order_result = await supabase_service.client.table('brand_kit_orders').insert({
            'user_id': current_user.id,
            'project_id': asset_result.data['project_id'],
            'selected_asset_id': selected_asset_id,
            'order_status': 'pending',
            'payment_amount': 29.00,
            'payment_provider': 'stripe',
            'payment_reference': payment_intent['payment_intent_id'],
            'payment_status': 'pending'
        }).execute()
        
        return {
            "payment_intent": payment_intent,
            "order_id": order_result.data[0]['id'] if order_result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment intent"
        )


@router.post("/create-checkout-session",
    status_code=status.HTTP_201_CREATED,
    summary="Create checkout session for hosted payment",
    description="Create a Stripe checkout session for hosted payment page"
)
async def create_checkout_session(
    selected_asset_id: str,
    success_url: str,
    cancel_url: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a Stripe checkout session for hosted payment.
    
    Args:
        selected_asset_id: ID of the selected logo asset
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment cancelled
        current_user: Authenticated user from JWT
        
    Returns:
        Checkout session details including URL
    """
    try:
        # Verify asset ownership (same as above)
        asset_result = await supabase_service.client.table('generated_assets').select(
            'id, project_id'
        ).eq('id', selected_asset_id).single().execute()
        
        if not asset_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        project_result = await supabase_service.client.table('brand_projects').select(
            'user_id'
        ).eq('id', asset_result.data['project_id']).single().execute()
        
        if not project_result.data or project_result.data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this asset"
            )
        
        # Create checkout session
        session = await stripe_service.create_checkout_session(
            user_id=current_user.id,
            selected_asset_id=selected_asset_id,
            user_email=current_user.email,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        # Create pending order
        order_result = await supabase_service.client.table('brand_kit_orders').insert({
            'user_id': current_user.id,
            'project_id': asset_result.data['project_id'],
            'selected_asset_id': selected_asset_id,
            'order_status': 'pending',
            'payment_amount': 29.00,
            'payment_provider': 'stripe',
            'payment_reference': session['session_id'],
            'payment_status': 'pending'
        }).execute()
        
        return {
            "checkout_session": session,
            "order_id": order_result.data[0]['id'] if order_result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )


@router.post("/refund/{order_id}",
    status_code=status.HTTP_200_OK,
    summary="Process refund for brand kit order",
    description="Create a refund for a completed brand kit order"
)
async def process_refund(
    order_id: str,
    refund_amount: Optional[float] = None,
    reason: str = "requested_by_customer",
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Process a refund for a brand kit order.
    
    Args:
        order_id: UUID of the brand kit order to refund
        refund_amount: Amount to refund (None for full refund)
        reason: Reason for refund
        current_user: Authenticated user (admin only)
        
    Returns:
        Refund details
    """
    try:
        # TODO: Add admin role check here
        # For now, only allow users to refund their own orders
        
        # Get order details
        order_result = await supabase_service.client.table('brand_kit_orders').select(
            '*'
        ).eq('id', order_id).eq('user_id', current_user.id).single().execute()
        
        if not order_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or access denied"
            )
        
        order = order_result.data
        
        # Verify order can be refunded
        if order['payment_status'] != 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order payment not completed - cannot refund"
            )
        
        if order['order_status'] == 'refunded':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order already refunded"
            )
        
        # Process refund through Stripe
        refund_amount_cents = None
        if refund_amount:
            refund_amount_cents = int(refund_amount * 100)
        
        refund_result = await stripe_service.create_refund(
            payment_intent_id=order['payment_reference'],
            amount=refund_amount_cents,
            reason=reason
        )
        
        logger.info(f"Refund processed for order {order_id}: {refund_result}")
        
        return {
            "order_id": order_id,
            "refund": refund_result,
            "message": "Refund processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund for order {order_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund"
        )