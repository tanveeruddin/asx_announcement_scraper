"""
Subscription API routes for Stripe integration.
"""

from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.db.base import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.auth.dependencies import get_current_active_user
from app.services.stripe_service import stripe_service
from app.config import settings


router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


class CheckoutRequest(BaseModel):
    """Request model for creating checkout session."""

    plan_type: Literal["monthly", "yearly"] = Field(..., description="Subscription plan type")
    success_url: str = Field(..., description="URL to redirect after successful payment")
    cancel_url: str = Field(..., description="URL to redirect if payment is canceled")


class CheckoutResponse(BaseModel):
    """Response model for checkout session."""

    checkout_session_id: str = Field(..., description="Stripe checkout session ID")
    checkout_url: str = Field(..., description="URL to redirect user to Stripe checkout")


class PortalResponse(BaseModel):
    """Response model for customer portal."""

    portal_url: str = Field(..., description="URL to Stripe customer portal")


class PlanInfo(BaseModel):
    """Subscription plan information."""

    plan_type: Literal["monthly", "yearly"]
    price: int  # Price in dollars
    currency: str = "USD"
    features: list[str]


class PlansResponse(BaseModel):
    """Response model for available plans."""

    plans: list[PlanInfo]
    free_trial_days: int


@router.get("/plans", response_model=PlansResponse, status_code=status.HTTP_200_OK)
async def get_subscription_plans():
    """
    Get available subscription plans.

    Returns:
        Available subscription plans with pricing
    """
    return PlansResponse(
        plans=[
            PlanInfo(
                plan_type="monthly",
                price=settings.monthly_plan_price,
                currency="USD",
                features=[
                    "AI-powered announcement analysis",
                    "Real-time sentiment tracking",
                    "Stock performance correlation",
                    "Unlimited announcements",
                    "Email support",
                ]
            ),
            PlanInfo(
                plan_type="yearly",
                price=settings.yearly_plan_price,
                currency="USD",
                features=[
                    "All monthly features",
                    "2 months free (20% savings)",
                    "Priority support",
                    "Early access to new features",
                    "Advanced analytics (coming soon)",
                ]
            ),
        ],
        free_trial_days=settings.free_trial_days
    )


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_200_OK)
async def create_checkout_session(
    checkout_request: CheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for subscription.

    Args:
        checkout_request: Checkout request with plan type and URLs
        current_user: Current authenticated user
        db: Database session

    Returns:
        Checkout session with URL to redirect user

    Raises:
        HTTPException: If checkout session creation fails
    """
    # Get Stripe price ID based on plan type
    if checkout_request.plan_type == "monthly":
        price_id = settings.stripe_monthly_price_id
    else:
        price_id = settings.stripe_yearly_price_id

    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe {checkout_request.plan_type} price ID not configured"
        )

    try:
        checkout_data = stripe_service.create_checkout_session(
            user=current_user,
            price_id=price_id,
            success_url=checkout_request.success_url,
            cancel_url=checkout_request.cancel_url,
            db=db
        )

        return CheckoutResponse(**checkout_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.post("/portal", response_model=PortalResponse, status_code=status.HTTP_200_OK)
async def create_portal_session(
    return_url: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe customer portal session for subscription management.

    Args:
        return_url: URL to return to after portal session
        current_user: Current authenticated user
        db: Database session

    Returns:
        Portal session with URL

    Raises:
        HTTPException: If user has no Stripe customer ID
    """
    # Get user's subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found. Please subscribe first."
        )

    try:
        portal_data = stripe_service.create_customer_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url
        )

        return PortalResponse(**portal_data)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create portal session: {str(e)}"
        )


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel user's subscription at end of billing period.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If subscription not found or cancellation fails
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription or not subscription.stripe_subscription_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    try:
        success = stripe_service.cancel_subscription(
            subscription.stripe_subscription_id
        )

        if success:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
            db.commit()

            return {
                "message": "Subscription will be canceled at the end of the billing period"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events.

    This endpoint receives events from Stripe about subscription changes,
    payments, and other important updates.

    Args:
        request: FastAPI request with webhook payload
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If webhook verification fails
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )

    success = stripe_service.handle_webhook_event(payload, signature, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook verification failed"
        )

    return {"status": "success"}
