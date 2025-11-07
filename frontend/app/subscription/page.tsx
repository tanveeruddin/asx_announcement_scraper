'use client';

/**
 * Subscription management page
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import Header from '@/components/Header';
import { useAuth } from '@/contexts/AuthContext';
import { getSubscriptionStatus, redirectToPortal, SubscriptionStatus } from '@/lib/auth';

export default function SubscriptionPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading, hasSubscription, subscriptionStatus } = useAuth();
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, authLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadSubscription();
    }
  }, [isAuthenticated]);

  async function loadSubscription() {
    try {
      setLoading(true);
      setError(null);
      const accessToken = localStorage.getItem('access_token');
      if (accessToken) {
        const data = await getSubscriptionStatus(accessToken);
        setSubscription(data);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load subscription');
    } finally {
      setLoading(false);
    }
  }

  async function handleManageSubscription() {
    setPortalLoading(true);
    setError(null);

    try {
      await redirectToPortal();
    } catch (err: any) {
      setError(err.message || 'Failed to open customer portal');
      setPortalLoading(false);
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading subscription...</p>
          </div>
        </main>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const getStatusBadge = (status: string | null) => {
    if (!status) return null;

    const badgeClasses: Record<string, string> = {
      trialing: 'bg-blue-100 text-blue-800',
      active: 'bg-green-100 text-green-800',
      canceled: 'bg-gray-100 text-gray-800',
      past_due: 'bg-red-100 text-red-800',
    };

    const statusLabels: Record<string, string> = {
      trialing: 'Free Trial',
      active: 'Active',
      canceled: 'Canceled',
      past_due: 'Past Due',
    };

    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${badgeClasses[status] || 'bg-gray-100 text-gray-800'}`}>
        {statusLabels[status] || status}
      </span>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Subscription</h1>
            <p className="text-gray-600">Manage your subscription and billing</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              <p className="text-sm">{error}</p>
            </div>
          )}

          {/* Subscription Status Card */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Current Plan
                </h2>
                {subscription?.has_subscription ? (
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl font-bold text-gray-900 capitalize">
                      {subscription.plan_type || 'Free Trial'}
                    </span>
                    {getStatusBadge(subscription.status)}
                  </div>
                ) : (
                  <p className="text-gray-600">No active subscription</p>
                )}
              </div>

              {subscription?.has_subscription && (
                <button
                  onClick={handleManageSubscription}
                  disabled={portalLoading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {portalLoading ? 'Loading...' : 'Manage Subscription'}
                </button>
              )}
            </div>

            {/* Subscription Details */}
            {subscription?.has_subscription && (
              <div className="border-t border-gray-200 pt-4 space-y-3">
                {subscription.status === 'trialing' && subscription.trial_end && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Trial ends:</span>
                    <span className="font-medium text-gray-900">
                      {format(new Date(subscription.trial_end), 'MMMM d, yyyy')}
                    </span>
                  </div>
                )}

                {subscription.current_period_end && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">
                      {subscription.status === 'trialing' ? 'Billing starts:' : 'Next billing date:'}
                    </span>
                    <span className="font-medium text-gray-900">
                      {format(new Date(subscription.current_period_end), 'MMMM d, yyyy')}
                    </span>
                  </div>
                )}

                {subscription.canceled_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Canceled on:</span>
                    <span className="font-medium text-gray-900">
                      {format(new Date(subscription.canceled_at), 'MMMM d, yyyy')}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* No Subscription CTA */}
            {!subscription?.has_subscription && (
              <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                <p className="text-blue-800 mb-3">
                  Subscribe to get unlimited access to AI-powered announcement analysis
                </p>
                <button
                  onClick={() => router.push('/pricing')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  View Plans
                </button>
              </div>
            )}
          </div>

          {/* Account Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Account Information
            </h2>

            <div className="space-y-3">
              <div className="flex justify-between border-b border-gray-200 pb-3">
                <span className="text-gray-600">Email:</span>
                <span className="font-medium text-gray-900">{user?.email}</span>
              </div>

              {user?.full_name && (
                <div className="flex justify-between border-b border-gray-200 pb-3">
                  <span className="text-gray-600">Name:</span>
                  <span className="font-medium text-gray-900">{user.full_name}</span>
                </div>
              )}

              <div className="flex justify-between border-b border-gray-200 pb-3">
                <span className="text-gray-600">Member since:</span>
                <span className="font-medium text-gray-900">
                  {user?.created_at ? format(new Date(user.created_at), 'MMMM d, yyyy') : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          {/* Features Card */}
          <div className="bg-white rounded-lg shadow-md p-6 mt-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Your Benefits
            </h2>

            <ul className="space-y-3">
              <li className="flex items-start">
                <svg className="w-6 h-6 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-gray-700">AI-powered announcement analysis with sentiment tracking</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-gray-700">Real-time stock performance correlation</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-gray-700">Unlimited announcements and search history</span>
              </li>
              <li className="flex items-start">
                <svg className="w-6 h-6 text-green-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-gray-700">Priority email support</span>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
