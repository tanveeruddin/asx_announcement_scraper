# Stripe Integration Setup Guide

Complete guide for setting up Stripe subscriptions and payments for the ASX Announcements SaaS application.

## Table of Contents

1. [Overview](#overview)
2. [Stripe Account Setup](#stripe-account-setup)
3. [Product and Pricing Configuration](#product-and-pricing-configuration)
4. [Backend Configuration](#backend-configuration)
5. [Webhook Setup](#webhook-setup)
6. [Frontend Configuration](#frontend-configuration)
7. [Testing with Test Mode](#testing-with-test-mode)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The application uses Stripe for:
- **Subscription Management**: Monthly and yearly plans
- **Free Trial**: 7-day trial for new users (no credit card required)
- **Payment Processing**: Secure credit card payments
- **Customer Portal**: Self-service subscription management
- **Webhooks**: Real-time subscription status updates

### Payment Flow

1. User signs up with Google OAuth → Free trial starts
2. User browses /pricing page → Sees subscription plans
3. User clicks subscribe → Redirects to Stripe Checkout
4. User completes payment → Stripe processes payment
5. Stripe sends webhook → Backend updates subscription
6. User redirected to success page → Full access enabled

---

## Stripe Account Setup

### Step 1: Create Stripe Account

1. Go to [Stripe.com](https://stripe.com)
2. Click "Start now" to create account
3. Verify your email address
4. Complete business profile (can skip for development)

### Step 2: Enable Test Mode

1. In Stripe Dashboard, toggle "Test mode" ON (top right)
2. You'll see "Test mode" banner at the top
3. All test payments use fake credit cards (no real money)

### Step 3: Get API Keys

1. Go to **Developers** → **API keys**
2. Copy your keys:
   - **Publishable key** (starts with `pk_test_...`) - Frontend
   - **Secret key** (starts with `sk_test_...`) - Backend

**Important**: Never commit secret keys to version control!

---

## Product and Pricing Configuration

### Step 1: Create Products

1. **Go to** Products → **Add product**

2. **Create Monthly Plan**:
   - **Name**: ASX Announcements Monthly
   - **Description**: Monthly subscription with AI-powered analysis
   - **Pricing model**: Standard pricing
   - **Price**: $20.00 USD
   - **Billing period**: Monthly
   - **Currency**: USD
   - Click "Save product"
   - **Copy the Price ID** (starts with `price_...`)

3. **Create Yearly Plan**:
   - **Name**: ASX Announcements Yearly
   - **Description**: Yearly subscription (2 months free)
   - **Pricing model**: Standard pricing
   - **Price**: $200.00 USD (equivalent to ~$16.67/month)
   - **Billing period**: Yearly
   - **Currency**: USD
   - Click "Save product"
   - **Copy the Price ID** (starts with `price_...`)

### Step 2: Configure Free Trial

Free trials are configured via backend environment variables (`FREE_TRIAL_DAYS=7`). When a user signs up with Google OAuth, a trial subscription is automatically created.

### Step 3: Enable Customer Portal

1. **Go to** Settings → **Billing** → **Customer portal**
2. Click "Activate test link"
3. **Configure portal settings**:
   - ✅ Allow customers to update payment methods
   - ✅ Allow customers to view invoices
   - ✅ Allow customers to cancel subscriptions
   - ✅ Allow customers to update subscriptions
4. Click "Save changes"

---

## Backend Configuration

### Step 1: Update Environment Variables

Edit `backend/.env`:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Stripe Price IDs (from previous step)
STRIPE_MONTHLY_PRICE_ID=price_1234567890abcdefg
STRIPE_YEARLY_PRICE_ID=price_0987654321zyxwvut

# Subscription Configuration
FREE_TRIAL_DAYS=7
MONTHLY_PLAN_PRICE=20
YEARLY_PLAN_PRICE=200
```

### Step 2: Install Dependencies

```bash
cd backend
uv sync  # This will install stripe>=11.1.0
```

### Step 3: Verify Installation

```bash
# Start backend
uv run uvicorn app.main:app --reload

# Check API docs
open http://localhost:8000/docs

# You should see new endpoints:
# - GET /api/v1/subscriptions/plans
# - POST /api/v1/subscriptions/checkout
# - POST /api/v1/subscriptions/portal
# - POST /api/v1/subscriptions/cancel
# - POST /api/v1/subscriptions/webhook
```

---

## Webhook Setup

Webhooks allow Stripe to notify your backend about subscription changes in real-time.

### Development (Local Testing)

#### Option 1: Stripe CLI (Recommended)

1. **Install Stripe CLI**:
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe

   # Windows
   scoop install stripe

   # Linux
   wget https://github.com/stripe/stripe-cli/releases/download/v1.19.0/stripe_1.19.0_linux_x86_64.tar.gz
   tar -xzf stripe_1.19.0_linux_x86_64.tar.gz
   ```

2. **Login to Stripe**:
   ```bash
   stripe login
   ```

3. **Forward webhooks to local server**:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/v1/subscriptions/webhook
   ```

4. **Copy webhook signing secret** (starts with `whsec_...`)
   - Update `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`

5. **Test webhook**:
   ```bash
   stripe trigger checkout.session.completed
   ```

#### Option 2: ngrok (Alternative)

1. **Install ngrok**: https://ngrok.com
2. **Start ngrok**:
   ```bash
   ngrok http 8000
   ```
3. **Copy ngrok URL** (e.g., `https://abc123.ngrok.io`)
4. **Add webhook in Stripe Dashboard**:
   - Go to Developers → Webhooks
   - Click "Add endpoint"
   - Endpoint URL: `https://abc123.ngrok.io/api/v1/subscriptions/webhook`
   - Select events (see below)

### Production Webhook Setup

1. **Deploy backend to Railway** (see DEPLOYMENT.md)

2. **Add webhook endpoint in Stripe**:
   - Go to Developers → Webhooks
   - Click "Add endpoint"
   - Endpoint URL: `https://your-backend.railway.app/api/v1/subscriptions/webhook`

3. **Select events to listen to**:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.payment_succeeded`
   - ✅ `invoice.payment_failed`

4. **Copy webhook signing secret**:
   - Click on the webhook endpoint
   - Click "Reveal" under "Signing secret"
   - Copy the secret (starts with `whsec_...`)

5. **Update Railway environment variables**:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_production_secret_here
   ```

---

## Frontend Configuration

### Step 1: Update Environment Variables

Edit `frontend/.env.local`:

```bash
# Stripe Configuration (Publishable Key only)
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
```

**Note**: Only the **publishable key** goes in frontend. Secret key stays on backend!

### Step 2: Install Dependencies

```bash
cd frontend
npm install  # This will install @stripe/stripe-js
```

### Step 3: Verify Installation

```bash
# Start frontend
npm run dev

# Visit pricing page
open http://localhost:3000/pricing

# You should see:
# - Two subscription plan cards (Monthly & Yearly)
# - "Start 7-Day Free Trial" buttons
# - Feature lists for each plan
```

---

## Testing with Test Mode

### Test Credit Cards

Stripe provides test credit cards that simulate different scenarios:

| Card Number | Scenario |
|-------------|----------|
| `4242 4242 4242 4242` | Success |
| `4000 0025 0000 3155` | 3D Secure authentication |
| `4000 0000 0000 9995` | Declined (insufficient funds) |
| `4000 0000 0000 0341` | Declined (incorrect CVC) |

**Card Details** (use with any of the above):
- **Expiry**: Any future date (e.g., 12/34)
- **CVC**: Any 3 digits (e.g., 123)
- **ZIP**: Any 5 digits (e.g., 12345)

### End-to-End Test

1. **Sign up**:
   ```
   http://localhost:3000/login
   ```
   - Login with Google
   - Free trial subscription created automatically
   - User sees "Trial" badge in header

2. **View pricing**:
   ```
   http://localhost:3000/pricing
   ```
   - See Monthly ($20/month) and Yearly ($200/year) plans
   - Both show "Start 7-Day Free Trial" button

3. **Subscribe**:
   - Click "Start 7-Day Free Trial" on Monthly plan
   - Redirected to Stripe Checkout
   - Fill in test card: `4242 4242 4242 4242`
   - Click "Subscribe"

4. **Success**:
   - Redirected to `/subscription/success`
   - See success message with features
   - Backend receives webhook
   - Subscription status updated to "active"

5. **Manage subscription**:
   ```
   http://localhost:3000/subscription
   ```
   - See subscription details
   - Click "Manage Subscription"
   - Redirected to Stripe Customer Portal
   - Can update payment method, cancel, view invoices

### Verify Webhook Events

Check backend logs for webhook events:

```bash
# Backend terminal should show:
INFO: Received Stripe webhook: checkout.session.completed
INFO: Updated subscription for user: user_id_here
```

Or check Stripe Dashboard:
- Go to Developers → Webhooks
- Click on webhook endpoint
- View recent events and responses

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Products and prices created in Stripe (live mode)
- [ ] Live API keys obtained
- [ ] Webhook endpoint configured for production URL
- [ ] Environment variables updated in Railway/Vercel
- [ ] Customer portal configured
- [ ] Test payments in live mode with real card

### Step 1: Switch to Live Mode

1. In Stripe Dashboard, toggle "Test mode" OFF
2. Re-create products and pricing (or activate existing ones)
3. Get **live API keys**:
   - Publishable key: `pk_live_...`
   - Secret key: `sk_live_...`

### Step 2: Update Production Environment Variables

**Railway (Backend)**:
```bash
STRIPE_SECRET_KEY=sk_live_your_live_secret_key
STRIPE_WEBHOOK_SECRET=whsec_production_webhook_secret
STRIPE_MONTHLY_PRICE_ID=price_live_monthly_id
STRIPE_YEARLY_PRICE_ID=price_live_yearly_id
```

**Vercel (Frontend)**:
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_live_publishable_key
```

### Step 3: Configure Production Webhook

1. Add webhook endpoint: `https://your-backend.railway.app/api/v1/subscriptions/webhook`
2. Select same events as development
3. Copy signing secret
4. Update Railway environment variable

### Step 4: Test in Production

1. Use a **real credit card** (you will be charged!)
2. Test subscription flow end-to-end
3. Verify webhook events are received
4. Test customer portal
5. Test cancellation

**Important**: Test with small amounts first ($0.50 test subscription)

---

## Troubleshooting

### Backend Issues

#### Issue: "Stripe secret key not configured"

**Symptoms**: Error when creating checkout session

**Solutions**:
1. Verify `STRIPE_SECRET_KEY` is set in `.env`
2. Ensure key starts with `sk_test_` (test) or `sk_live_` (production)
3. Restart backend server after updating .env
4. Check settings are loaded:
   ```python
   from app.config import settings
   print(f"Stripe key: {settings.stripe_secret_key[:10]}...")
   ```

#### Issue: "Invalid price ID"

**Symptoms**: Checkout fails with price error

**Solutions**:
1. Verify price IDs in Stripe Dashboard (Products → Click product → Copy Price ID)
2. Ensure price IDs match in `.env`:
   ```bash
   STRIPE_MONTHLY_PRICE_ID=price_1234567890abcdefg
   STRIPE_YEARLY_PRICE_ID=price_0987654321zyxwvut
   ```
3. Check price is active (not archived)
4. Verify currency is USD

#### Issue: "Webhook signature verification failed"

**Symptoms**: Webhook returns 400 error

**Solutions**:
1. Verify `STRIPE_WEBHOOK_SECRET` is set correctly
2. Check webhook secret matches Stripe Dashboard
3. Ensure payload is raw bytes (not parsed JSON)
4. Test with Stripe CLI:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/v1/subscriptions/webhook
   stripe trigger checkout.session.completed
   ```

#### Issue: "Customer not found"

**Symptoms**: Can't create portal session

**Solutions**:
1. Verify user has `stripe_customer_id` in database:
   ```sql
   SELECT stripe_customer_id FROM subscriptions WHERE user_id = 'user_id_here';
   ```
2. If null, user needs to complete checkout first
3. Check checkout webhook was received

### Frontend Issues

#### Issue: "Stripe publishable key not configured"

**Symptoms**: Checkout button doesn't work

**Solutions**:
1. Verify `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` in `.env.local`
2. Restart Next.js dev server (required for env var changes)
3. Check key is accessible in browser console:
   ```javascript
   console.log(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY)
   ```

#### Issue: Checkout redirect fails

**Symptoms**: Clicking subscribe does nothing

**Solutions**:
1. Check browser console for errors
2. Verify user is authenticated (has access token)
3. Check backend API is running and accessible
4. Verify CORS is configured correctly
5. Test API endpoint directly:
   ```bash
   curl -X POST http://localhost:8000/api/v1/subscriptions/checkout \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"plan_type":"monthly","success_url":"http://localhost:3000/success","cancel_url":"http://localhost:3000/pricing"}'
   ```

#### Issue: Customer portal shows "No subscription found"

**Symptoms**: Error when clicking "Manage Subscription"

**Solutions**:
1. User must have completed checkout first
2. Verify subscription exists in database
3. Check webhook was received and processed
4. Reload subscription status:
   ```javascript
   await refreshUser(); // In AuthContext
   ```

### Webhook Issues

#### Issue: Webhooks not received in development

**Symptoms**: Subscription status not updated after checkout

**Solutions**:
1. Use Stripe CLI to forward webhooks:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/v1/subscriptions/webhook
   ```
2. Or use ngrok for public URL
3. Check backend logs for webhook events
4. Verify webhook endpoint is accessible:
   ```bash
   curl -X POST http://localhost:8000/api/v1/subscriptions/webhook
   ```

#### Issue: Webhook events not processing

**Symptoms**: Webhook received but subscription not updated

**Solutions**:
1. Check backend logs for errors
2. Verify database connection
3. Check user_id in webhook metadata
4. Manually trigger webhook:
   ```bash
   stripe trigger checkout.session.completed
   ```
5. Check Stripe Dashboard → Webhooks → Recent events for error details

---

## Security Best Practices

### API Keys

1. **Never commit API keys** to version control
2. Use different keys for dev/staging/production
3. Rotate keys quarterly
4. Store keys in Railway/Vercel env vars (not in code)

### Webhook Security

1. **Always verify webhook signatures**
   - Our implementation uses `stripe.Webhook.construct_event()`
   - Never trust webhook data without verification

2. **Use HTTPS in production**
   - Webhooks must be sent over HTTPS
   - Railway provides HTTPS by default

3. **Handle idempotency**
   - Stripe may send duplicate events
   - Our implementation uses database constraints to prevent duplicates

### Customer Data

1. **PCI Compliance**
   - Never store credit card numbers
   - Stripe handles all payment data
   - Only store Stripe customer/subscription IDs

2. **User Privacy**
   - Don't log sensitive data (card numbers, CVV)
   - Encrypt customer email if required by regulations

---

## Monitoring & Analytics

### Stripe Dashboard

Monitor your business metrics:
- **Home**: Overview of revenue, customers, payments
- **Payments**: All payment transactions
- **Customers**: Customer list with subscription status
- **Subscriptions**: Active, canceled, past due subscriptions
- **Analytics**: MRR, churn rate, customer lifetime value

### Key Metrics to Track

1. **MRR (Monthly Recurring Revenue)**
   - Target: $1,000+ for sustainability
   - Growth rate: 10%+ month-over-month

2. **Churn Rate**
   - Target: <5% monthly churn
   - Monitor cancellation reasons

3. **Trial Conversion**
   - Target: 25%+ trial-to-paid conversion
   - Optimize based on conversion funnel

4. **Customer Lifetime Value (LTV)**
   - Target: LTV > 3x customer acquisition cost
   - Increase with yearly plans and retention

---

## Additional Resources

- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Subscriptions Guide](https://stripe.com/docs/billing/subscriptions/overview)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe CLI Documentation](https://stripe.com/docs/stripe-cli)

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Status**: Stripe Integration Ready ✅
