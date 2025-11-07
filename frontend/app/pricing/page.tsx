'use client';

/**
 * Pricing page with subscription plans
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import { useAuth } from '@/contexts/AuthContext';
import { getSubscriptionPlans, redirectToCheckout, PlansResponse } from '@/lib/stripe';

export default function PricingPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading: authLoading, hasSubscription } = useAuth();
  const [plans, setPlans] = useState<PlansResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);

  useEffect(() => {
    loadPlans();
  }, []);

  async function loadPlans() {
    try {
      setLoading(true);
      setError(null);
      const data = await getSubscriptionPlans();
      setPlans(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load subscription plans');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubscribe(planType: 'monthly' | 'yearly') {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    setCheckoutLoading(planType);
    setError(null);

    try {
      await redirectToCheckout(planType);
    } catch (err: any) {
      setError(err.message || 'Failed to start checkout');
      setCheckoutLoading(null);
    }
  }

  if (loading || authLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading plans...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            Start with a {plans?.free_trial_days || 7}-day free trial. No credit card required.
          </p>
          <p className="text-gray-500">
            Cancel anytime. All plans include AI-powered analysis and real-time updates.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="max-w-4xl mx-auto mb-6">
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          {plans?.plans.map((plan) => {
            const isYearly = plan.plan_type === 'yearly';
            const monthlyPrice = isYearly ? plan.price / 12 : plan.price;
            const savings = isYearly ? ((plan.price / 10) * 100 / plan.price).toFixed(0) : null;
            const isLoadingThis = checkoutLoading === plan.plan_type;

            return (
              <div
                key={plan.plan_type}
                className={`bg-white rounded-lg shadow-lg overflow-hidden ${
                  isYearly ? 'border-2 border-blue-600 relative' : 'border border-gray-200'
                }`}
              >
                {isYearly && (
                  <div className="bg-blue-600 text-white text-center py-2 px-4 text-sm font-semibold">
                    Most Popular - Save {savings}%
                  </div>
                )}

                <div className="p-8">
                  {/* Plan Header */}
                  <div className="text-center mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                      {isYearly ? 'Yearly Plan' : 'Monthly Plan'}
                    </h2>
                    <div className="flex items-baseline justify-center">
                      <span className="text-5xl font-extrabold text-gray-900">
                        ${Math.round(monthlyPrice)}
                      </span>
                      <span className="text-xl text-gray-500 ml-2">/month</span>
                    </div>
                    {isYearly && (
                      <p className="text-sm text-gray-500 mt-2">
                        Billed ${plan.price} annually
                      </p>
                    )}
                    {!isYearly && (
                      <p className="text-sm text-gray-500 mt-2">
                        Billed ${plan.price} monthly
                      </p>
                    )}
                  </div>

                  {/* Features List */}
                  <ul className="space-y-4 mb-8">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <svg
                          className="w-6 h-6 text-green-500 mr-3 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Subscribe Button */}
                  {hasSubscription ? (
                    <button
                      disabled
                      className="w-full py-3 px-6 text-center font-semibold rounded-lg bg-gray-300 text-gray-500 cursor-not-allowed"
                    >
                      Already Subscribed
                    </button>
                  ) : (
                    <button
                      onClick={() => handleSubscribe(plan.plan_type)}
                      disabled={isLoadingThis}
                      className={`w-full py-3 px-6 text-center font-semibold rounded-lg transition-colors ${
                        isYearly
                          ? 'bg-blue-600 text-white hover:bg-blue-700'
                          : 'bg-gray-800 text-white hover:bg-gray-900'
                      } disabled:bg-gray-400 disabled:cursor-not-allowed`}
                    >
                      {isLoadingThis ? (
                        <span className="flex items-center justify-center">
                          <svg
                            className="animate-spin h-5 w-5 mr-2"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Processing...
                        </span>
                      ) : (
                        <>
                          {isAuthenticated
                            ? `Start ${plans?.free_trial_days || 7}-Day Free Trial`
                            : 'Sign In to Subscribe'}
                        </>
                      )}
                    </button>
                  )}

                  {!isAuthenticated && (
                    <p className="text-xs text-center text-gray-500 mt-3">
                      You'll be redirected to sign in
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto mt-16">
          <h2 className="text-2xl font-bold text-center text-gray-900 mb-8">
            Frequently Asked Questions
          </h2>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                How does the free trial work?
              </h3>
              <p className="text-gray-600">
                Start with a {plans?.free_trial_days || 7}-day free trial. No credit card required. You'll have full access to all features during the trial period.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I cancel anytime?
              </h3>
              <p className="text-gray-600">
                Yes! You can cancel your subscription at any time from your account settings. Your subscription will remain active until the end of your current billing period.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                What payment methods do you accept?
              </h3>
              <p className="text-gray-600">
                We accept all major credit cards (Visa, Mastercard, American Express) through our secure Stripe payment processor.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I switch plans?
              </h3>
              <p className="text-gray-600">
                Yes! You can upgrade or downgrade your plan at any time from your subscription settings. Changes will be prorated.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
