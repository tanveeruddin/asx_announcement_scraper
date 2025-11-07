/**
 * Stripe utilities and API client for subscription management
 */

import { api } from './api';
import { getAccessToken } from './auth';

export interface PlanInfo {
  plan_type: 'monthly' | 'yearly';
  price: number;
  currency: string;
  features: string[];
}

export interface PlansResponse {
  plans: PlanInfo[];
  free_trial_days: number;
}

export interface CheckoutRequest {
  plan_type: 'monthly' | 'yearly';
  success_url: string;
  cancel_url: string;
}

export interface CheckoutResponse {
  checkout_session_id: string;
  checkout_url: string;
}

export interface PortalResponse {
  portal_url: string;
}

/**
 * Get available subscription plans
 */
export async function getSubscriptionPlans(): Promise<PlansResponse> {
  const response = await api.get<PlansResponse>('/subscriptions/plans');
  return response.data;
}

/**
 * Create Stripe checkout session
 */
export async function createCheckoutSession(
  planType: 'monthly' | 'yearly',
  successUrl: string,
  cancelUrl: string
): Promise<CheckoutResponse> {
  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Not authenticated');
  }

  const response = await api.post<CheckoutResponse>(
    '/subscriptions/checkout',
    {
      plan_type: planType,
      success_url: successUrl,
      cancel_url: cancelUrl,
    },
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  return response.data;
}

/**
 * Create Stripe customer portal session
 */
export async function createPortalSession(returnUrl: string): Promise<PortalResponse> {
  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Not authenticated');
  }

  const response = await api.post<PortalResponse>(
    '/subscriptions/portal',
    null,
    {
      params: {
        return_url: returnUrl,
      },
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );

  return response.data;
}

/**
 * Cancel subscription
 */
export async function cancelSubscription(): Promise<void> {
  const accessToken = getAccessToken();
  if (!accessToken) {
    throw new Error('Not authenticated');
  }

  await api.post(
    '/subscriptions/cancel',
    null,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    }
  );
}

/**
 * Redirect to Stripe checkout
 */
export async function redirectToCheckout(
  planType: 'monthly' | 'yearly'
): Promise<void> {
  const baseUrl = window.location.origin;
  const successUrl = `${baseUrl}/subscription/success`;
  const cancelUrl = `${baseUrl}/pricing`;

  try {
    const checkout = await createCheckoutSession(planType, successUrl, cancelUrl);
    window.location.href = checkout.checkout_url;
  } catch (error) {
    console.error('Checkout error:', error);
    throw error;
  }
}

/**
 * Redirect to Stripe customer portal
 */
export async function redirectToPortal(): Promise<void> {
  const returnUrl = window.location.origin + '/subscription';

  try {
    const portal = await createPortalSession(returnUrl);
    window.location.href = portal.portal_url;
  } catch (error) {
    console.error('Portal error:', error);
    throw error;
  }
}
