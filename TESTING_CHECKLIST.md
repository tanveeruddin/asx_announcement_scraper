# ASX Announcements SaaS - Complete Testing Checklist

**Version**: 1.0
**Last Updated**: 2025-11-07
**Purpose**: Comprehensive testing guide for all application features

---

## Table of Contents

1. [Phase 0: Environment Setup](#phase-0-environment-setup)
2. [Phase 1: Core Scraping Engine](#phase-1-core-scraping-engine)
3. [Phase 2: Backend API](#phase-2-backend-api)
4. [Phase 3: Frontend Application](#phase-3-frontend-application)
5. [Phase 4: Authentication & Payments](#phase-4-authentication--payments)
6. [Phase 5: Deployment Verification](#phase-5-deployment-verification)
7. [End-to-End User Flows](#end-to-end-user-flows)

---

## Phase 0: Environment Setup

### Local Development Environment

#### Backend Setup
- [ ] Python 3.11+ installed and accessible
- [ ] UV package manager installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [ ] Navigate to `backend/` directory
- [ ] Create `.env` file from `.env.example`
- [ ] Update `.env` with required values:
  - [ ] `DATABASE_URL` configured
  - [ ] `GEMINI_API_KEY` added
  - [ ] `JWT_SECRET_KEY` generated
  - [ ] `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` configured
  - [ ] `STRIPE_SECRET_KEY` and webhook secret configured
- [ ] Run `uv sync` successfully (all dependencies installed)
- [ ] Docker Desktop installed and running

#### Frontend Setup
- [ ] Node.js 18+ installed
- [ ] Navigate to `frontend/` directory
- [ ] Create `.env.local` file from `.env.example`
- [ ] Update `.env.local` with:
  - [ ] `NEXT_PUBLIC_API_URL=http://localhost:8000`
  - [ ] `NEXT_PUBLIC_GOOGLE_CLIENT_ID` configured
- [ ] Run `npm install` successfully (all dependencies installed)

#### Database Setup
- [ ] Docker Compose file exists in project root
- [ ] Run `docker-compose up -d postgres` successfully
- [ ] PostgreSQL container running (check with `docker ps`)
- [ ] Database accessible at configured `DATABASE_URL`
- [ ] Run `uv run alembic upgrade head` successfully
- [ ] Verify tables created:
  ```bash
  docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements -c "\dt"
  ```
- [ ] Should see tables: `users`, `subscriptions`, `companies`, `announcements`, `analysis`, `stock_data`, `watchlists`

---

## Phase 1: Core Scraping Engine

### ASX Scraper Service

#### Test Scraper Functionality
- [ ] Start backend: `uv run uvicorn app.main:app --reload`
- [ ] Backend running at `http://localhost:8000`
- [ ] Open Python shell and test scraper:
  ```python
  from app.services.scraper import ScraperService
  scraper = ScraperService()
  announcements = scraper.fetch_todays_announcements()
  print(f"Found {len(announcements)} announcements")
  ```
- [ ] Should return 200+ announcements
- [ ] Verify announcement data structure:
  - [ ] `asx_code` present (e.g., "BHP")
  - [ ] `company_name` present
  - [ ] `title` present
  - [ ] `announcement_date` present
  - [ ] `pdf_url` present and valid
  - [ ] `is_price_sensitive` boolean
  - [ ] `num_pages` integer
  - [ ] `file_size_kb` integer

#### Test Price-Sensitive Filtering
- [ ] Filter for price-sensitive only:
  ```python
  price_sensitive = scraper.filter_price_sensitive(announcements)
  print(f"Found {len(price_sensitive)} price-sensitive announcements")
  ```
- [ ] Should return 50-100 price-sensitive announcements
- [ ] Verify all have `is_price_sensitive=True`

### PDF Download Service

#### Test PDF Downloads
- [ ] Install Playwright browsers: `uv run playwright install`
- [ ] Test single PDF download:
  ```python
  from app.services.pdf_downloader import pdf_downloader
  from app.services.scraper import ScraperService

  scraper = ScraperService()
  announcements = scraper.fetch_todays_announcements()
  first_announcement = announcements[0]

  pdf_path = pdf_downloader.download_pdf(
      first_announcement.pdf_url,
      str(first_announcement.asx_code)
  )
  print(f"Downloaded to: {pdf_path}")
  ```
- [ ] PDF file exists at returned path
- [ ] File size > 0 KB
- [ ] File is valid PDF (can open with PDF reader)

#### Test Duplicate Detection
- [ ] Download same PDF again
- [ ] Verify it skips download and returns existing path
- [ ] No duplicate files created

#### Test Concurrent Downloads
- [ ] Test batch download (5 PDFs):
  ```python
  import asyncio
  announcements = scraper.fetch_todays_announcements()[:5]

  async def download_batch():
      tasks = []
      for ann in announcements:
          task = pdf_downloader.download_pdf_async(ann.pdf_url, str(ann.asx_code))
          tasks.append(task)
      results = await asyncio.gather(*tasks)
      return results

  paths = asyncio.run(download_batch())
  print(f"Downloaded {len(paths)} PDFs")
  ```
- [ ] All 5 PDFs downloaded successfully
- [ ] Download time < 30 seconds

### PDF to Markdown Conversion

#### Test PDF Processing
- [ ] Test markdown conversion:
  ```python
  from app.services.pdf_processor import pdf_processor

  # Use previously downloaded PDF
  markdown = pdf_processor.convert_to_markdown(pdf_path)
  print(f"Markdown length: {len(markdown)} characters")
  print(markdown[:500])  # First 500 chars
  ```
- [ ] Markdown text extracted successfully
- [ ] Length > 1000 characters (not empty)
- [ ] Text is readable (not garbled)
- [ ] Preserves structure (headings, paragraphs)

#### Test Metadata Extraction
- [ ] Extract PDF metadata:
  ```python
  metadata = pdf_processor.extract_metadata(pdf_path)
  print(metadata)
  ```
- [ ] Returns dictionary with:
  - [ ] `num_pages` integer
  - [ ] `file_size_kb` integer
  - [ ] Values are reasonable (pages < 100, size < 5000KB)

### LLM Analysis (Google Gemini)

#### Test Gemini Integration
- [ ] Verify `GEMINI_API_KEY` is set in `.env`
- [ ] Test LLM analysis:
  ```python
  from app.services.llm_analyzer import llm_analyzer

  # Use markdown from previous step
  analysis = llm_analyzer.analyze_announcement(
      markdown,
      "Test Company Announcement"
  )
  print(f"Summary: {analysis.summary}")
  print(f"Sentiment: {analysis.sentiment}")
  print(f"Key Insights: {analysis.key_insights}")
  ```
- [ ] Analysis returned successfully
- [ ] `summary` is 2-3 sentences
- [ ] `sentiment` is one of: "bullish", "bearish", "neutral"
- [ ] `key_insights` is list with 3-5 items
- [ ] `confidence_score` between 0.0 and 1.0
- [ ] `processing_time_ms` present

#### Test Error Handling
- [ ] Test with invalid API key (temporarily change in config)
- [ ] Should raise graceful error (not crash)
- [ ] Test with empty markdown
- [ ] Should return default/empty analysis

### Stock Data Service (yfinance)

#### Test Stock Data Fetching
- [ ] Test fetching stock metrics:
  ```python
  from app.services.stock_data import stock_data_service

  metrics = stock_data_service.get_stock_metrics("BHP")
  print(metrics)
  ```
- [ ] Returns StockMetrics object
- [ ] `current_price` is decimal > 0
- [ ] `market_cap` is large number
- [ ] `performance_1m_pct`, `performance_3m_pct`, `performance_6m_pct` present
- [ ] Values are reasonable (not None or 0)

#### Test Multiple Stocks
- [ ] Test with different ASX codes:
  - [ ] "CBA" (Commonwealth Bank)
  - [ ] "WES" (Wesfarmers)
  - [ ] "TLS" (Telstra)
- [ ] All return valid data
- [ ] No crashes or errors

#### Test Invalid Stock Code
- [ ] Test with invalid code "INVALID123"
- [ ] Should handle gracefully (return None or raise specific error)
- [ ] Should not crash application

### Pipeline Orchestration

#### Test Complete Pipeline
- [ ] Run end-to-end pipeline test:
  ```bash
  cd backend
  uv run python test_pipeline.py
  ```
- [ ] Pipeline processes at least 3 announcements
- [ ] Each step completes:
  - [ ] PDF download
  - [ ] Markdown conversion
  - [ ] LLM analysis
  - [ ] Stock data fetch
  - [ ] Database save
- [ ] Success statistics printed
- [ ] No crashes or errors

#### Test Error Recovery
- [ ] Verify pipeline continues after individual failures
- [ ] Check logs for error handling
- [ ] Failed items logged but don't stop pipeline

### APScheduler (Background Jobs)

#### Test Scheduler Setup
- [ ] Test scheduler initialization:
  ```python
  from app.services.scheduler import scheduler_service

  # Start scheduler
  scheduler_service.start()
  print(f"Scheduler running: {scheduler_service.scheduler.running}")
  ```
- [ ] Scheduler starts successfully
- [ ] No immediate errors

#### Test Manual Job Trigger
- [ ] Trigger scrape job manually:
  ```python
  scheduler_service.scrape_job()
  ```
- [ ] Job executes without errors
- [ ] Check database for new announcements:
  ```bash
  docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements -c "SELECT COUNT(*) FROM announcements;"
  ```
- [ ] Count increases

#### Test Scheduled Jobs
- [ ] Configure short interval (5 minutes) for testing
- [ ] Let scheduler run for 10 minutes
- [ ] Verify multiple scrapes occurred
- [ ] Check logs for scheduled execution
- [ ] Stop scheduler: `scheduler_service.stop()`

---

## Phase 2: Backend API

### Health Check Endpoint

#### Test Health Endpoint
- [ ] Backend running at `http://localhost:8000`
- [ ] Visit `http://localhost:8000/health`
- [ ] Response status: 200 OK
- [ ] Response JSON contains:
  - [ ] `status: "healthy"`
  - [ ] `database: "connected"`
  - [ ] `version: "0.1.0"`
  - [ ] `environment: "development"`

### API Documentation

#### Test OpenAPI Docs
- [ ] Visit `http://localhost:8000/docs`
- [ ] Swagger UI loads successfully
- [ ] All endpoints visible:
  - [ ] `/api/v1/auth/*` endpoints
  - [ ] `/api/v1/subscriptions/*` endpoints
  - [ ] `/api/v1/announcements*` endpoints
  - [ ] `/api/v1/companies*` endpoints
- [ ] Can expand each endpoint
- [ ] Request/response schemas visible

### Announcements API

#### Test List Announcements
- [ ] In Swagger UI or use curl:
  ```bash
  curl http://localhost:8000/api/v1/announcements?page=1&page_size=10
  ```
- [ ] Response status: 200 OK
- [ ] Response contains:
  - [ ] `items` array with 10 announcements
  - [ ] `metadata` with pagination info
  - [ ] `metadata.total_items` > 0
  - [ ] `metadata.total_pages` >= 1
- [ ] Each announcement has required fields

#### Test Pagination
- [ ] Request page 1: `?page=1&page_size=5`
- [ ] Request page 2: `?page=2&page_size=5`
- [ ] Different announcements returned
- [ ] No duplicates between pages
- [ ] `metadata.current_page` matches request

#### Test Filtering - Price Sensitive
- [ ] Filter for price-sensitive only:
  ```bash
  curl "http://localhost:8000/api/v1/announcements?price_sensitive_only=true&page_size=20"
  ```
- [ ] All returned items have price sensitivity indicators
- [ ] Count is less than total announcements

#### Test Filtering - Sentiment
- [ ] Filter by sentiment (requires analyzed announcements):
  ```bash
  curl "http://localhost:8000/api/v1/announcements?sentiment=bullish"
  ```
- [ ] Only bullish announcements returned
- [ ] Test "bearish" and "neutral" filters
- [ ] Each returns appropriate results

#### Test Filtering - Date Range
- [ ] Filter by date:
  ```bash
  curl "http://localhost:8000/api/v1/announcements?date_from=2025-01-01&date_to=2025-12-31"
  ```
- [ ] Only announcements in date range returned
- [ ] Dates are within specified range

#### Test Filtering - ASX Code
- [ ] Filter by company:
  ```bash
  curl "http://localhost:8000/api/v1/announcements?asx_code=BHP"
  ```
- [ ] Only BHP announcements returned
- [ ] All have matching ASX code

#### Test Get Single Announcement
- [ ] Get announcement by ID:
  ```bash
  curl http://localhost:8000/api/v1/announcements/{announcement_id}
  ```
- [ ] Response status: 200 OK
- [ ] Full announcement details returned
- [ ] Includes related data:
  - [ ] Company information
  - [ ] Analysis (if available)
  - [ ] Stock data (if available)

#### Test Invalid ID
- [ ] Request with invalid UUID:
  ```bash
  curl http://localhost:8000/api/v1/announcements/invalid-uuid
  ```
- [ ] Response status: 422 Unprocessable Entity
- [ ] Error message explains invalid UUID format

#### Test Non-existent ID
- [ ] Request with valid but non-existent UUID
- [ ] Response status: 404 Not Found
- [ ] Error message: "Announcement not found"

### Companies API

#### Test List Companies
- [ ] Request companies list:
  ```bash
  curl http://localhost:8000/api/v1/companies
  ```
- [ ] Response status: 200 OK
- [ ] Array of companies returned
- [ ] Each company has:
  - [ ] `id` (UUID)
  - [ ] `asx_code`
  - [ ] `company_name`

#### Test Get Single Company
- [ ] Get company by ASX code:
  ```bash
  curl http://localhost:8000/api/v1/companies/BHP
  ```
- [ ] Response status: 200 OK
- [ ] Company details returned
- [ ] Includes metadata

#### Test Company Announcements
- [ ] Get announcements for company:
  ```bash
  curl http://localhost:8000/api/v1/companies/BHP/announcements
  ```
- [ ] Response status: 200 OK
- [ ] Paginated announcements for BHP only
- [ ] All have `asx_code: "BHP"`

### Advanced Search

#### Test Search Endpoint
- [ ] POST search request:
  ```bash
  curl -X POST http://localhost:8000/api/v1/announcements/search \
    -H "Content-Type: application/json" \
    -d '{
      "query": "acquisition",
      "asx_codes": ["BHP", "RIO"],
      "sentiment": "bullish",
      "price_sensitive_only": true
    }'
  ```
- [ ] Response status: 200 OK
- [ ] Results match search criteria
- [ ] Pagination works with search

---

## Phase 3: Frontend Application

### Landing Page

#### Test Homepage
- [ ] Start frontend: `npm run dev` (from `frontend/` directory)
- [ ] Visit `http://localhost:3000`
- [ ] Page loads without errors
- [ ] Header displays:
  - [ ] Logo and "ASX Announcements" title
  - [ ] Navigation links (Announcements, Pricing)
  - [ ] "Sign In" button (if not authenticated)
- [ ] Hero section displays:
  - [ ] Main heading
  - [ ] Descriptive text
  - [ ] "View Announcements" button
- [ ] Features section shows 3 feature cards:
  - [ ] Real-Time Tracking
  - [ ] AI Analysis
  - [ ] Market Data
- [ ] Statistics section displays:
  - [ ] "285+ Announcements Tracked"
  - [ ] "76+ Price-Sensitive"
  - [ ] "100% API Uptime"
- [ ] Footer displays copyright and tech stack

#### Test Navigation
- [ ] Click "View Announcements" button
- [ ] Redirects to `/announcements`
- [ ] Click "ASX Announcements" logo
- [ ] Returns to homepage

### Announcements List Page

#### Test Page Load
- [ ] Visit `http://localhost:3000/announcements`
- [ ] Page loads without errors
- [ ] Header with navigation displayed
- [ ] Filter bar displayed
- [ ] Announcement cards displayed (if data exists)
- [ ] Loading state shows initially
- [ ] Content appears after loading

#### Test Filter Bar
- [ ] "Price Sensitive Only" checkbox present
- [ ] "Sentiment" dropdown present with options:
  - [ ] All (default)
  - [ ] Bullish
  - [ ] Bearish
  - [ ] Neutral
- [ ] "Reset Filters" button present

#### Test Filtering
- [ ] Check "Price Sensitive Only" checkbox
- [ ] Announcements list updates
- [ ] Only price-sensitive announcements shown
- [ ] Select "Bullish" sentiment
- [ ] List updates again
- [ ] Only bullish announcements shown
- [ ] Click "Reset Filters"
- [ ] All filters cleared
- [ ] Full list shown

#### Test Announcement Cards
- [ ] Each card displays:
  - [ ] ASX code badge (e.g., "BHP")
  - [ ] Company name
  - [ ] Announcement title
  - [ ] Date and time
  - [ ] Price sensitive indicator (if applicable)
  - [ ] Sentiment badge (if analyzed)
  - [ ] Number of pages
  - [ ] File size
- [ ] Sentiment badges colored correctly:
  - [ ] Bullish = green
  - [ ] Bearish = red
  - [ ] Neutral = gray

#### Test Pagination
- [ ] Pagination controls visible at bottom
- [ ] "Previous" button disabled on page 1
- [ ] Page numbers displayed
- [ ] Click "Next" or page number
- [ ] New announcements loaded
- [ ] URL updates with `?page=2`
- [ ] Click "Previous"
- [ ] Returns to previous page

#### Test Card Click
- [ ] Click on an announcement card
- [ ] Navigates to detail page
- [ ] URL is `/announcements/{id}`

### Announcement Detail Page

#### Test Page Load
- [ ] Visit announcement detail page
- [ ] Page loads without errors
- [ ] Header displayed
- [ ] Loading state shown initially
- [ ] Content appears after loading

#### Test Announcement Details
- [ ] Top section displays:
  - [ ] ASX code and company name
  - [ ] Announcement title
  - [ ] Date and time
  - [ ] Price sensitive indicator
  - [ ] PDF link (opens in new tab)
- [ ] "Back to Announcements" button present and works

#### Test AI Analysis Section
- [ ] "AI Analysis" section displayed (if analyzed)
- [ ] Summary text present (2-3 sentences)
- [ ] Sentiment badge with color:
  - [ ] Bullish = green background
  - [ ] Bearish = red background
  - [ ] Neutral = gray background
- [ ] Key Insights list present (3-5 bullet points)
- [ ] Each insight is meaningful text

#### Test Stock Data Section
- [ ] "Stock Performance" section displayed (if available)
- [ ] Current price shown
- [ ] Market cap displayed
- [ ] P/E ratio shown (if available)
- [ ] Performance metrics displayed:
  - [ ] 1-month percentage
  - [ ] 3-month percentage
  - [ ] 6-month percentage
- [ ] Positive percentages in green
- [ ] Negative percentages in red

#### Test PDF Download
- [ ] Click "Download PDF" link
- [ ] PDF opens in new tab or downloads
- [ ] PDF is valid and readable

#### Test Back Navigation
- [ ] Click "Back to Announcements"
- [ ] Returns to announcements list
- [ ] Preserves previous filters (if any)

### Responsive Design

#### Test Mobile View
- [ ] Resize browser to mobile width (< 768px)
- [ ] Header adjusts:
  - [ ] Navigation still accessible
  - [ ] Logo scaled appropriately
- [ ] Announcement cards stack vertically
- [ ] Filters stack vertically
- [ ] All content readable and accessible
- [ ] No horizontal scrolling

#### Test Tablet View
- [ ] Resize to tablet width (768px - 1024px)
- [ ] Layout adjusts appropriately
- [ ] Grid shows 2 columns if applicable
- [ ] Content remains accessible

---

## Phase 4: Authentication & Payments

### Google OAuth Authentication

#### Test Login Page
- [ ] Visit `http://localhost:3000/login`
- [ ] Page loads without errors
- [ ] "ASX Announcements" title displayed
- [ ] "Welcome Back" heading shown
- [ ] Google Sign-In button visible
- [ ] Features list displayed:
  - [ ] AI-powered analysis
  - [ ] Real-time sentiment
  - [ ] Stock correlation
  - [ ] 7-day free trial
- [ ] Terms of Service and Privacy Policy links present

#### Test Google Sign-In Flow
- [ ] Click "Sign in with Google" button
- [ ] Google OAuth popup appears
- [ ] Select Google account
- [ ] Authorize application
- [ ] Popup closes
- [ ] Redirected to `/announcements`
- [ ] Header now shows:
  - [ ] User avatar with initial
  - [ ] User name/email
  - [ ] "Logout" button
  - [ ] "Subscription" link
- [ ] No longer see "Sign In" button

#### Test Auto-Login
- [ ] Close browser tab
- [ ] Open new tab
- [ ] Visit `http://localhost:3000`
- [ ] Should still be logged in (tokens in localStorage)
- [ ] Header shows authenticated state

#### Test Logout
- [ ] Click "Logout" button in header
- [ ] Confirmation (no popup needed)
- [ ] Redirected to homepage
- [ ] Header shows "Sign In" button
- [ ] No longer shows user info
- [ ] Check browser localStorage:
  ```javascript
  localStorage.getItem('access_token')  // Should be null
  localStorage.getItem('refresh_token')  // Should be null
  localStorage.getItem('user')  // Should be null
  ```

#### Test Protected Routes (if implemented)
- [ ] Logout if logged in
- [ ] Try to visit `/subscription`
- [ ] Should redirect to `/login`
- [ ] Login
- [ ] Should redirect back to `/subscription`

#### Test Backend Authentication
- [ ] Login and get access token from localStorage
- [ ] Test authenticated API request:
  ```bash
  curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
    http://localhost:8000/api/v1/auth/me
  ```
- [ ] Response status: 200 OK
- [ ] Returns user information:
  - [ ] User ID
  - [ ] Email
  - [ ] Full name
  - [ ] Subscription status
- [ ] Test without token:
  ```bash
  curl http://localhost:8000/api/v1/auth/me
  ```
- [ ] Response status: 403 Forbidden

#### Test Token Refresh
- [ ] Wait for access token to expire (default 60 minutes) OR manually test:
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/refresh \
    -H "Content-Type: application/json" \
    -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
  ```
- [ ] Response status: 200 OK
- [ ] New access token returned
- [ ] New refresh token returned

### Subscription Plans (Stripe)

#### Test Pricing Page
- [ ] Visit `http://localhost:3000/pricing`
- [ ] Page loads without errors
- [ ] Header with navigation
- [ ] "Choose Your Plan" heading
- [ ] Free trial notice (7 days)
- [ ] Two plan cards displayed:

  **Monthly Plan:**
  - [ ] Title: "Monthly Plan"
  - [ ] Price: $20/month
  - [ ] Features list (5 items)
  - [ ] Subscribe button

  **Yearly Plan:**
  - [ ] Title: "Yearly Plan"
  - [ ] Price: $16.67/month ($200/year)
  - [ ] "Most Popular" badge
  - [ ] "Save 20%" indicator
  - [ ] Features list (5 items, includes bonus features)
  - [ ] Subscribe button
  - [ ] Different styling (highlighted)

- [ ] FAQ section displayed with 4 questions

#### Test Subscribe Flow (Test Mode)
- [ ] Ensure logged in
- [ ] Click "Start 7-Day Free Trial" on Monthly plan
- [ ] Loading spinner appears
- [ ] Redirected to Stripe Checkout page
- [ ] Stripe Checkout displays:
  - [ ] Product: "ASX Announcements Monthly"
  - [ ] Price: $20.00/month
  - [ ] Trial period notice
  - [ ] Email pre-filled
  - [ ] Card input field
  - [ ] Pay button

#### Test Stripe Checkout - Success
- [ ] Enter test card: `4242 4242 4242 4242`
- [ ] Expiry: any future date (e.g., `12/34`)
- [ ] CVC: any 3 digits (e.g., `123`)
- [ ] ZIP: any 5 digits (e.g., `12345`)
- [ ] Click "Subscribe"
- [ ] Processing indicator
- [ ] Redirected to `/subscription/success`
- [ ] Success page displays:
  - [ ] Green checkmark icon
  - [ ] "Subscription Successful!" message
  - [ ] Features list
  - [ ] Action buttons
  - [ ] Auto-redirect notice

#### Test Stripe Checkout - Declined Card
- [ ] Start checkout again (logout and login if needed)
- [ ] Enter declined test card: `4000 0000 0000 9995`
- [ ] Enter other details
- [ ] Click "Subscribe"
- [ ] Payment declined message from Stripe
- [ ] Stays on Stripe Checkout
- [ ] Can try again with valid card

#### Test Stripe Checkout - Cancel
- [ ] Start checkout flow
- [ ] Click browser back button or close tab
- [ ] Returns to `/pricing` page
- [ ] No subscription created
- [ ] Can try again

#### Test Webhook (Development)
- [ ] Install Stripe CLI: `brew install stripe/stripe-cli/stripe`
- [ ] Login: `stripe login`
- [ ] Forward webhooks:
  ```bash
  stripe listen --forward-to http://localhost:8000/api/v1/subscriptions/webhook
  ```
- [ ] Copy webhook signing secret
- [ ] Update backend `.env`: `STRIPE_WEBHOOK_SECRET=whsec_...`
- [ ] Restart backend
- [ ] Complete a test subscription
- [ ] Check Stripe CLI output:
  - [ ] `checkout.session.completed` received
  - [ ] Response status: 200
- [ ] Check backend logs for webhook processing
- [ ] Verify database updated:
  ```bash
  docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements \
    -c "SELECT status, plan_type FROM subscriptions ORDER BY created_at DESC LIMIT 5;"
  ```
- [ ] New subscription with status "active"

### Subscription Management

#### Test Subscription Page
- [ ] Login with subscribed account
- [ ] Visit `http://localhost:3000/subscription`
- [ ] Page loads without errors
- [ ] Current plan section displays:
  - [ ] Plan type (Monthly/Yearly/Free Trial)
  - [ ] Status badge (Active/Trialing)
  - [ ] Billing date or trial end date
  - [ ] "Manage Subscription" button

#### Test Trial User
- [ ] Login with new account (just created)
- [ ] Visit `/subscription`
- [ ] Should show:
  - [ ] "Free Trial" status
  - [ ] Blue "Trial" badge
  - [ ] Trial end date
  - [ ] Days remaining
- [ ] Header shows "Trial" badge next to Subscription link

#### Test Active Subscriber
- [ ] Login with subscribed account
- [ ] Visit `/subscription`
- [ ] Should show:
  - [ ] Plan type (Monthly or Yearly)
  - [ ] Green "Active" badge
  - [ ] Next billing date
  - [ ] "Manage Subscription" button

#### Test Customer Portal
- [ ] Click "Manage Subscription" button
- [ ] Redirected to Stripe Customer Portal
- [ ] Portal displays:
  - [ ] Current plan
  - [ ] Payment method
  - [ ] Billing history
  - [ ] Update payment method option
  - [ ] Cancel subscription option
  - [ ] "Return to [app name]" link

#### Test Update Payment Method
- [ ] In Customer Portal, click "Update payment method"
- [ ] Enter new test card: `5555 5555 5555 4444`
- [ ] Save changes
- [ ] Success message displayed
- [ ] New card shown as payment method

#### Test Cancel Subscription
- [ ] In Customer Portal, click "Cancel subscription"
- [ ] Confirmation modal appears
- [ ] Select cancellation reason (optional)
- [ ] Confirm cancellation
- [ ] Subscription set to cancel at period end
- [ ] Still shows as "Active" until period ends
- [ ] Message: "Your subscription will end on [date]"
- [ ] Return to app
- [ ] Subscription page shows:
  - [ ] Status still "Active"
  - [ ] Canceled date displayed
  - [ ] Notice about end date

#### Test Invoices
- [ ] In Customer Portal, view "Billing history"
- [ ] Should see list of invoices
- [ ] Can download PDF invoices
- [ ] Invoices show correct amounts

### Subscription Success Page

#### Test Success Page
- [ ] Complete a subscription purchase
- [ ] Redirected to `/subscription/success`
- [ ] Success icon displayed (green checkmark)
- [ ] "Subscription Successful!" message
- [ ] Features list shown
- [ ] Two action buttons:
  - [ ] "Start Exploring Announcements"
  - [ ] "View Subscription Details"
- [ ] Auto-redirect countdown (5 seconds)
- [ ] After 5 seconds, redirects to `/subscription`

#### Test Success Page Actions
- [ ] Click "Start Exploring Announcements"
- [ ] Redirects to `/announcements`
- [ ] Return to success page
- [ ] Click "View Subscription Details"
- [ ] Redirects to `/subscription`

---

## Phase 5: Deployment Verification

### Local Environment Check

#### Backend Verification
- [ ] Run health check script:
  ```bash
  curl http://localhost:8000/health
  ```
- [ ] Response: `{"status":"healthy","database":"connected"}`
- [ ] Check all dependencies installed:
  ```bash
  cd backend
  uv run pip list | grep -E "stripe|google-auth|fastapi|sqlalchemy"
  ```
- [ ] All required packages present

#### Frontend Verification
- [ ] Check build works:
  ```bash
  cd frontend
  npm run build
  ```
- [ ] Build completes successfully
- [ ] No TypeScript errors
- [ ] No ESLint errors
- [ ] Output shows `.next` directory created

#### Environment Variables
- [ ] Backend `.env` has all required variables (see `.env.example`)
- [ ] Frontend `.env.local` has all required variables
- [ ] No placeholder values like "your_key_here"
- [ ] All secrets are secure random strings

### Configuration Files

#### Backend Configuration
- [ ] `backend/railway.json` exists
- [ ] `backend/Procfile` exists with web and worker processes
- [ ] `backend/runtime.txt` specifies Python 3.11.9
- [ ] `backend/.env.railway.template` has all variables documented
- [ ] `backend/requirements.txt` or `pyproject.toml` up to date

#### Frontend Configuration
- [ ] `frontend/vercel.json` exists
- [ ] `frontend/.env.production.template` exists
- [ ] `frontend/package.json` has all dependencies
- [ ] `frontend/next.config.js` or `next.config.ts` configured correctly

### Documentation Completeness

#### Check All Documentation Files
- [ ] `README.md` exists and complete
- [ ] `CLAUDE.md` exists (project overview)
- [ ] `AUTH_SETUP.md` exists (authentication guide)
- [ ] `STRIPE_SETUP.md` exists (payment guide)
- [ ] `DEPLOYMENT.md` exists (deployment guide)
- [ ] `TODO.md` shows 100% completion
- [ ] `backend/API_README.md` exists (API docs)
- [ ] `frontend/README.md` exists (frontend docs)

#### Test Documentation Accuracy
- [ ] Follow README instructions from scratch
- [ ] All commands work as documented
- [ ] No broken links
- [ ] Code examples are accurate
- [ ] Screenshots (if any) are up to date

---

## End-to-End User Flows

### New User Journey - Free Trial

#### Complete Registration Flow
- [ ] Visit `http://localhost:3000`
- [ ] Click "View Announcements" or "Sign In"
- [ ] Redirected to `/login`
- [ ] Click "Sign in with Google"
- [ ] Complete OAuth flow
- [ ] Redirected to `/announcements`
- [ ] Check database for new user:
  ```bash
  docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements \
    -c "SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 1;"
  ```
- [ ] New user record exists
- [ ] Check for trial subscription:
  ```bash
  docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements \
    -c "SELECT status, trial_end FROM subscriptions ORDER BY created_at DESC LIMIT 1;"
  ```
- [ ] Trial subscription created with status "trialing"
- [ ] Trial end date is 7 days from now

#### Explore as Trial User
- [ ] Visit `/announcements`
- [ ] Can view announcements list
- [ ] Can filter by price sensitivity
- [ ] Can filter by sentiment
- [ ] Click on announcement card
- [ ] Can view full announcement details
- [ ] Can see AI analysis
- [ ] Can see stock data
- [ ] Header shows "Trial" badge
- [ ] Visit `/subscription`
- [ ] Shows trial status and end date

### Paid Subscription Journey

#### Upgrade from Trial
- [ ] As trial user, visit `/pricing`
- [ ] See "Already on trial" or subscription option
- [ ] Click "Start 7-Day Free Trial" (or "Subscribe")
- [ ] Stripe Checkout opens
- [ ] Enter test card: `4242 4242 4242 4242`
- [ ] Complete checkout
- [ ] Redirected to `/subscription/success`
- [ ] Wait for webhook processing (check Stripe CLI)
- [ ] Visit `/subscription`
- [ ] Status changed to "Active"
- [ ] Plan type shows "Monthly" or "Yearly"
- [ ] Check database:
  ```bash
  docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements \
    -c "SELECT status, plan_type, stripe_subscription_id FROM subscriptions WHERE stripe_subscription_id IS NOT NULL;"
  ```
- [ ] Subscription has stripe_subscription_id
- [ ] Status is "active"

#### Manage Subscription
- [ ] Visit `/subscription`
- [ ] Click "Manage Subscription"
- [ ] Stripe Portal opens
- [ ] Update payment method successfully
- [ ] View invoice history
- [ ] Set cancellation for end of period
- [ ] Return to app
- [ ] Subscription still active until period end
- [ ] Canceled date shown on `/subscription` page

### Content Consumption Flow

#### Browse Announcements
- [ ] Visit `/announcements`
- [ ] See paginated list of announcements
- [ ] Filter for "Price Sensitive Only"
- [ ] Results update
- [ ] Select "Bullish" sentiment
- [ ] Results update again
- [ ] Navigate to page 2
- [ ] Different announcements shown
- [ ] Select an announcement card

#### View Announcement Details
- [ ] Detail page loads
- [ ] Full announcement info displayed
- [ ] AI analysis section shows:
  - [ ] Summary that makes sense
  - [ ] Sentiment badge (color-coded)
  - [ ] 3-5 key insights
  - [ ] Each insight is relevant
- [ ] Stock performance section shows:
  - [ ] Current price
  - [ ] Market cap
  - [ ] 1m, 3m, 6m performance
  - [ ] Color-coded gains/losses
- [ ] Click "Download PDF"
- [ ] PDF downloads or opens
- [ ] Click "Back to Announcements"
- [ ] Returns to list with filters preserved

### Search and Filter Flow

#### Advanced Filtering
- [ ] Visit `/announcements`
- [ ] Apply multiple filters:
  - [ ] Price sensitive only
  - [ ] Sentiment: Bullish
- [ ] Results show only matching items
- [ ] Navigate to page 2
- [ ] Filters persist (URL has parameters)
- [ ] Click announcement to view details
- [ ] Use browser back button
- [ ] Returns to filtered list (filters still applied)
- [ ] Click "Reset Filters"
- [ ] All filters cleared
- [ ] Full unfiltered list shown

### Complete User Lifecycle

#### Full Journey Test
1. **Day 1 - Registration**
   - [ ] New user signs up with Google
   - [ ] Trial starts automatically
   - [ ] Explores announcements
   - [ ] Views several announcement details

2. **Day 3 - Engagement**
   - [ ] User returns to app
   - [ ] Auto-login works
   - [ ] Applies filters to find specific companies
   - [ ] Views multiple announcements

3. **Day 6 - Upgrade**
   - [ ] User sees trial ending soon
   - [ ] Visits pricing page
   - [ ] Subscribes to yearly plan
   - [ ] Receives confirmation

4. **Day 10 - Active Use**
   - [ ] User browses new announcements
   - [ ] Filters by sentiment
   - [ ] Downloads PDFs
   - [ ] No issues with subscription

5. **Day 30 - Management**
   - [ ] User visits subscription page
   - [ ] Opens customer portal
   - [ ] Views invoice
   - [ ] Updates payment method

---

## Automated Testing Checklist

### Backend Tests

#### Run Unit Tests
- [ ] Navigate to `backend/` directory
- [ ] Run tests:
  ```bash
  uv run pytest
  ```
- [ ] All tests pass
- [ ] No failures or errors
- [ ] Code coverage > 70%

#### Run Individual Test Suites
- [ ] Test scraper:
  ```bash
  uv run pytest tests/test_scraper.py -v
  ```
- [ ] Test API endpoints:
  ```bash
  uv run pytest tests/test_api.py -v
  ```
- [ ] Test authentication:
  ```bash
  uv run pytest tests/test_auth.py -v
  ```

### Frontend Tests

#### Run Frontend Tests
- [ ] Navigate to `frontend/` directory
- [ ] Run tests:
  ```bash
  npm test
  ```
- [ ] All tests pass
- [ ] No failures
- [ ] Coverage acceptable

#### Run Linting
- [ ] Run ESLint:
  ```bash
  npm run lint
  ```
- [ ] No errors
- [ ] Warnings are acceptable or explained

---

## Performance Testing

### Backend Performance

#### API Response Times
- [ ] Test health endpoint response time:
  ```bash
  time curl http://localhost:8000/health
  ```
- [ ] Response time < 100ms

- [ ] Test announcements list:
  ```bash
  time curl "http://localhost:8000/api/v1/announcements?page=1&page_size=20"
  ```
- [ ] Response time < 500ms

- [ ] Test single announcement:
  ```bash
  time curl http://localhost:8000/api/v1/announcements/{id}
  ```
- [ ] Response time < 300ms

#### Load Testing (Optional)
- [ ] Use tool like Apache Bench or wrk
- [ ] Test concurrent requests:
  ```bash
  ab -n 100 -c 10 http://localhost:8000/api/v1/announcements
  ```
- [ ] All requests succeed
- [ ] Average response time acceptable

### Frontend Performance

#### Page Load Times
- [ ] Open browser DevTools Network tab
- [ ] Visit `/announcements`
- [ ] Check metrics:
  - [ ] First Contentful Paint < 1.5s
  - [ ] Largest Contentful Paint < 2.5s
  - [ ] Time to Interactive < 3.5s

#### Bundle Size
- [ ] Check build output:
  ```bash
  npm run build
  ```
- [ ] Review bundle sizes
- [ ] First Load JS < 200KB
- [ ] No excessively large chunks

---

## Security Testing

### Authentication Security

#### Test JWT Token Validation
- [ ] Get valid access token
- [ ] Modify token slightly
- [ ] Try to access protected endpoint:
  ```bash
  curl -H "Authorization: Bearer modified_token_here" \
    http://localhost:8000/api/v1/auth/me
  ```
- [ ] Response: 401 Unauthorized
- [ ] Error message: "Invalid or expired token"

#### Test Expired Tokens
- [ ] Use old/expired access token
- [ ] Try to access protected endpoint
- [ ] Response: 401 Unauthorized
- [ ] Must use refresh token to get new access token

#### Test CORS
- [ ] Try to access API from unauthorized origin
- [ ] Should be blocked by CORS policy
- [ ] Only configured origins allowed

### Stripe Security

#### Test Webhook Signature Verification
- [ ] Send webhook without signature:
  ```bash
  curl -X POST http://localhost:8000/api/v1/subscriptions/webhook \
    -H "Content-Type: application/json" \
    -d '{"type":"test.event"}'
  ```
- [ ] Response: 400 Bad Request
- [ ] Error: "Missing Stripe signature"

#### Test Invalid Webhook Signature
- [ ] Send webhook with invalid signature
- [ ] Response: 400 Bad Request
- [ ] Error: "Webhook verification failed"

### SQL Injection Testing

#### Test Input Validation
- [ ] Try SQL injection in ASX code filter:
  ```bash
  curl "http://localhost:8000/api/v1/announcements?asx_code=BHP';DROP TABLE announcements;--"
  ```
- [ ] Should be safely handled
- [ ] No database errors
- [ ] No tables dropped

### XSS Testing

#### Test Script Injection
- [ ] Try to inject script in search:
  ```bash
  curl -X POST http://localhost:8000/api/v1/announcements/search \
    -H "Content-Type: application/json" \
    -d '{"query":"<script>alert(1)</script>"}'
  ```
- [ ] Should be safely escaped
- [ ] No script execution

---

## Database Testing

### Data Integrity

#### Check Relationships
- [ ] Verify foreign keys working:
  ```sql
  -- Announcements should have valid company references
  SELECT COUNT(*) FROM announcements a
  LEFT JOIN companies c ON a.company_id = c.id
  WHERE c.id IS NULL;
  ```
- [ ] Count should be 0 (no orphaned announcements)

#### Check Constraints
- [ ] Verify unique constraints:
  ```sql
  -- No duplicate users by email
  SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;
  ```
- [ ] No results (no duplicate emails)

#### Check Data Types
- [ ] Verify decimal fields are correct precision
- [ ] Verify dates are stored as timestamps
- [ ] Verify UUIDs are valid format

### Database Backup and Restore

#### Test Backup
- [ ] Create database backup:
  ```bash
  docker exec -it asx-announcements-db pg_dump -U asx_user asx_announcements > backup.sql
  ```
- [ ] Backup file created
- [ ] File size > 0

#### Test Restore (Caution: Destructive)
- [ ] Create test database
- [ ] Restore backup:
  ```bash
  docker exec -i asx-announcements-db psql -U asx_user test_db < backup.sql
  ```
- [ ] Restore completes successfully
- [ ] Data accessible in test database

---

## Checklist Summary

Use this quick summary to track overall progress:

### Phase 0: Environment Setup
- [ ] Backend environment configured
- [ ] Frontend environment configured
- [ ] Database running and migrated
- [ ] All dependencies installed

### Phase 1: Core Engine
- [ ] ASX scraper functional
- [ ] PDF downloads working
- [ ] PDF to Markdown conversion works
- [ ] LLM analysis returns results
- [ ] Stock data fetching works
- [ ] Pipeline orchestration complete
- [ ] Scheduler running

### Phase 2: Backend API
- [ ] Health check responds
- [ ] API documentation accessible
- [ ] Announcements endpoints work
- [ ] Companies endpoints work
- [ ] Filtering and pagination work
- [ ] Search endpoint works

### Phase 3: Frontend
- [ ] Landing page loads
- [ ] Announcements list works
- [ ] Filters update list
- [ ] Pagination works
- [ ] Detail page displays correctly
- [ ] Responsive design works

### Phase 4: Authentication & Payments
- [ ] Google OAuth login works
- [ ] Logout works
- [ ] Auto-login works
- [ ] Protected routes work
- [ ] Pricing page displays
- [ ] Stripe checkout works
- [ ] Webhooks process correctly
- [ ] Subscription page shows status
- [ ] Customer portal accessible

### Phase 5: Deployment
- [ ] All configuration files present
- [ ] Documentation complete
- [ ] Build processes work
- [ ] Environment variables documented

### End-to-End
- [ ] New user can register
- [ ] Trial subscription created
- [ ] User can browse announcements
- [ ] User can upgrade subscription
- [ ] User can manage subscription
- [ ] Complete lifecycle works

---

## Final Verification

Before marking project as complete:

- [ ] All checkboxes in all sections completed
- [ ] No critical bugs found
- [ ] All documentation accurate
- [ ] Ready for production deployment

---

**Testing Complete!** ✅

Once all items are checked, the application is ready for production deployment following the guides in:
- `AUTH_SETUP.md`
- `STRIPE_SETUP.md`
- `DEPLOYMENT.md`

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Status**: Complete Testing Guide
