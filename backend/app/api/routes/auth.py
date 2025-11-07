"""
Authentication API routes for Google OAuth and JWT token management.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from app.db.base import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.auth import create_access_token, create_refresh_token, verify_token
from app.auth.dependencies import get_current_active_user, get_current_user
from app.auth.schemas import (
    GoogleOAuthRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    MeResponse,
    SubscriptionStatusResponse,
)
from app.config import settings


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/google", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def google_oauth_login(
    oauth_request: GoogleOAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Google OAuth ID token.

    Verifies the Google ID token, creates or updates user,
    and returns JWT access and refresh tokens.

    Args:
        oauth_request: Google OAuth request with ID token
        db: Database session

    Returns:
        JWT access and refresh tokens

    Raises:
        HTTPException: If token verification fails
    """
    try:
        # Verify Google ID token
        idinfo = id_token.verify_oauth2_token(
            oauth_request.id_token,
            google_requests.Request(),
            settings.google_client_id
        )

        # Extract user info from token
        google_id = idinfo.get("sub")
        email = idinfo.get("email")
        full_name = idinfo.get("name")

        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token: missing user information"
            )

        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            # Create new user
            user = User(
                email=email,
                full_name=full_name,
                oauth_provider="google",
                oauth_id=google_id,
                is_active=True,
                last_login=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Create trial subscription for new user
            trial_start = datetime.utcnow()
            trial_end = trial_start + timedelta(days=settings.free_trial_days)

            subscription = Subscription(
                user_id=user.id,
                status="trialing",
                trial_start=trial_start,
                trial_end=trial_end,
                current_period_start=trial_start,
                current_period_end=trial_end
            )
            db.add(subscription)
            db.commit()

        else:
            # Update existing user
            user.last_login = datetime.utcnow()
            if not user.oauth_id:
                user.oauth_id = google_id
                user.oauth_provider = "google"
            if not user.full_name and full_name:
                user.full_name = full_name
            db.commit()

        # Generate JWT tokens
        token_data = {"sub": str(user.id), "email": user.email}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.jwt_access_token_expire_minutes * 60
        )

    except ValueError as e:
        # Invalid token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_access_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    Args:
        refresh_request: Refresh token request
        db: Database session

    Returns:
        New JWT access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(refresh_request.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Get user from database
    user_id_str = payload.get("sub")
    email = payload.get("email")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Generate new tokens
    token_data = {"sub": str(user.id), "email": user.email}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's information.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User information with subscription status
    """
    # Fetch subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    has_subscription = subscription is not None
    subscription_status = subscription.status if subscription else None
    trial_ends_at = subscription.trial_end if subscription else None

    return MeResponse(
        user=UserResponse.model_validate(current_user),
        has_subscription=has_subscription,
        subscription_status=subscription_status,
        trial_ends_at=trial_ends_at
    )


@router.get("/subscription", response_model=SubscriptionStatusResponse, status_code=status.HTTP_200_OK)
async def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's subscription status.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Detailed subscription information
    """
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if subscription is None:
        return SubscriptionStatusResponse(
            has_subscription=False,
            status=None,
            plan_type=None,
            trial_start=None,
            trial_end=None,
            current_period_start=None,
            current_period_end=None,
            canceled_at=None
        )

    return SubscriptionStatusResponse(
        has_subscription=True,
        status=subscription.status,
        plan_type=subscription.plan_type,
        trial_start=subscription.trial_start,
        trial_end=subscription.trial_end,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        canceled_at=subscription.canceled_at
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user.

    Note: JWT tokens cannot be invalidated on the server side.
    Client should discard tokens on logout.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    return {"message": "Successfully logged out. Please discard your tokens."}
