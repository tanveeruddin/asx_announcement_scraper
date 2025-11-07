"""
Stripe service for subscription and payment management.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.subscription import Subscription


# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service for handling Stripe subscription operations."""

    def __init__(self):
        """Initialize Stripe service with API key."""
        stripe.api_key = settings.stripe_secret_key

    def create_customer(self, user: User) -> str:
        """
        Create a Stripe customer for a user.

        Args:
            user: User model

        Returns:
            Stripe customer ID
        """
        customer = stripe.Customer.create(
            email=user.email,
            name=user.full_name,
            metadata={
                "user_id": str(user.id),
            }
        )
        return customer.id

    def create_checkout_session(
        self,
        user: User,
        price_id: str,
        success_url: str,
        cancel_url: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription.

        Args:
            user: User model
            price_id: Stripe price ID (monthly or yearly)
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels
            db: Database session

        Returns:
            Checkout session data
        """
        # Get or create Stripe customer
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            customer_id = self.create_customer(user)

            # Update subscription with customer ID
            if subscription:
                subscription.stripe_customer_id = customer_id
                db.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
            },
            subscription_data={
                "metadata": {
                    "user_id": str(user.id),
                }
            }
        )

        return {
            "checkout_session_id": checkout_session.id,
            "checkout_url": checkout_session.url,
        }

    def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe customer portal session for subscription management.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            Portal session data
        """
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

        return {
            "portal_url": portal_session.url,
        }

    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancel a Stripe subscription.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            True if successful
        """
        try:
            stripe.Subscription.delete(subscription_id)
            return True
        except stripe.error.StripeError:
            return False

    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Stripe subscription details.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Subscription data or None
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return {
                "id": subscription.id,
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end),
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }
        except stripe.error.StripeError:
            return None

    def handle_webhook_event(self, payload: bytes, signature: str, db: Session) -> bool:
        """
        Handle Stripe webhook events.

        Args:
            payload: Webhook payload
            signature: Stripe signature header
            db: Database session

        Returns:
            True if event was handled successfully
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.stripe_webhook_secret
            )
        except ValueError:
            # Invalid payload
            return False
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return False

        # Handle different event types
        if event.type == "checkout.session.completed":
            self._handle_checkout_completed(event.data.object, db)

        elif event.type == "customer.subscription.created":
            self._handle_subscription_created(event.data.object, db)

        elif event.type == "customer.subscription.updated":
            self._handle_subscription_updated(event.data.object, db)

        elif event.type == "customer.subscription.deleted":
            self._handle_subscription_deleted(event.data.object, db)

        elif event.type == "invoice.payment_succeeded":
            self._handle_payment_succeeded(event.data.object, db)

        elif event.type == "invoice.payment_failed":
            self._handle_payment_failed(event.data.object, db)

        return True

    def _handle_checkout_completed(self, session: Any, db: Session):
        """Handle checkout.session.completed event."""
        user_id = session.metadata.get("user_id")
        if not user_id:
            return

        # Update subscription with Stripe subscription ID
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if subscription:
            subscription.stripe_subscription_id = session.subscription
            subscription.stripe_customer_id = session.customer
            subscription.status = "active"
            db.commit()

    def _handle_subscription_created(self, stripe_subscription: Any, db: Session):
        """Handle customer.subscription.created event."""
        user_id = stripe_subscription.metadata.get("user_id")
        if not user_id:
            return

        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()

        if subscription:
            # Determine plan type from price ID
            price_id = stripe_subscription.items.data[0].price.id
            plan_type = "monthly" if price_id == settings.stripe_monthly_price_id else "yearly"

            subscription.stripe_subscription_id = stripe_subscription.id
            subscription.stripe_customer_id = stripe_subscription.customer
            subscription.plan_type = plan_type
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription.current_period_start
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription.current_period_end
            )
            db.commit()

    def _handle_subscription_updated(self, stripe_subscription: Any, db: Session):
        """Handle customer.subscription.updated event."""
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription.id
        ).first()

        if subscription:
            subscription.status = stripe_subscription.status
            subscription.current_period_start = datetime.fromtimestamp(
                stripe_subscription.current_period_start
            )
            subscription.current_period_end = datetime.fromtimestamp(
                stripe_subscription.current_period_end
            )

            if stripe_subscription.cancel_at_period_end:
                subscription.canceled_at = datetime.utcnow()

            db.commit()

    def _handle_subscription_deleted(self, stripe_subscription: Any, db: Session):
        """Handle customer.subscription.deleted event."""
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription.id
        ).first()

        if subscription:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
            db.commit()

    def _handle_payment_succeeded(self, invoice: Any, db: Session):
        """Handle invoice.payment_succeeded event."""
        if not invoice.subscription:
            return

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == invoice.subscription
        ).first()

        if subscription and subscription.status != "active":
            subscription.status = "active"
            db.commit()

    def _handle_payment_failed(self, invoice: Any, db: Session):
        """Handle invoice.payment_failed event."""
        if not invoice.subscription:
            return

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == invoice.subscription
        ).first()

        if subscription:
            subscription.status = "past_due"
            db.commit()


# Singleton instance
stripe_service = StripeService()
