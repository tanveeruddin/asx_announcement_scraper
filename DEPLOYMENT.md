# ASX Announcements SaaS - Deployment Guide

Complete guide for deploying the ASX Announcements application to production using Railway (backend) and Vercel (frontend).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Deployment (Railway)](#backend-deployment-railway)
3. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
4. [Database Setup](#database-setup)
5. [Environment Variables](#environment-variables)
6. [Post-Deployment Configuration](#post-deployment-configuration)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before deploying, ensure you have:

### Accounts
- [x] **Railway Account** (https://railway.app)
- [x] **Vercel Account** (https://vercel.com)
- [x] **GitHub Account** with repository access
- [x] **Google Cloud Project** (for Gemini API)
- [x] **AWS Account** or **Cloudflare Account** (for file storage)

### API Keys & Credentials
- [x] Google Gemini API key
- [x] AWS S3 credentials (or Cloudflare R2)
- [x] Google OAuth credentials (Phase 4)
- [x] Stripe account (Phase 4)

### Local Setup
- [x] Git configured with repository access
- [x] Backend tested locally with Docker Compose
- [x] Frontend tested locally with `npm run dev`

---

## Backend Deployment (Railway)

### Step 1: Create Railway Project

1. **Login to Railway**
   ```bash
   # Install Railway CLI (optional)
   npm install -g @railway/cli
   railway login
   ```

2. **Create New Project**
   - Go to https://railway.app/new
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your repository
   - Select `asx_announcement_scraper` repository

### Step 2: Add PostgreSQL Database

1. **Add PostgreSQL Service**
   - In Railway project dashboard, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically provision a PostgreSQL instance
   - Copy the `DATABASE_URL` connection string

2. **Database Configuration**
   - PostgreSQL 15+ will be provisioned
   - Default storage: 1GB (upgradeable)
   - Automatic backups enabled

### Step 3: Configure Backend Service

1. **Create Backend Service**
   - Click "New" → "GitHub Repo"
   - Select your repository
   - Set **Root Directory**: `backend`
   - Railway will auto-detect Python/FastAPI

2. **Build Configuration**
   - Railway will use `railway.json` automatically
   - Build command: `uv pip install --system -r requirements.txt`
   - Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables**
   - Click "Variables" tab
   - Copy all variables from `backend/.env.railway.template`
   - Update with your actual values:

   **Required Variables:**
   ```bash
   DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-provided by Railway
   GEMINI_API_KEY=your_actual_gemini_key
   STORAGE_TYPE=s3
   S3_BUCKET_NAME=asx-announcements-prod
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   SECRET_KEY=<generate_random_32_char_string>
   CORS_ORIGINS=["https://your-app.vercel.app"]
   ```

   **Generate SECRET_KEY:**
   ```python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **Deploy**
   - Click "Deploy"
   - Railway will build and deploy your backend
   - Monitor logs for any errors
   - Note your backend URL (e.g., `https://your-backend.railway.app`)

### Step 4: Configure Worker Service (Scheduler)

1. **Add Worker Service**
   - Click "New" → "GitHub Repo"
   - Select same repository
   - Set **Root Directory**: `backend`
   - Name it "Worker" or "Scheduler"

2. **Override Start Command**
   - Go to Settings → Start Command
   - Override with: `python -m app.services.scheduler`
   - This will run the APScheduler service

3. **Environment Variables**
   - Link to same PostgreSQL database
   - Copy all environment variables from main backend service
   - Ensure `SCHEDULER_ENABLED=true`

4. **Deploy Worker**
   - Worker will start scraping on configured schedule
   - Monitor logs to verify scraping job execution

### Step 5: Verify Backend Deployment

1. **Health Check**
   ```bash
   curl https://your-backend.railway.app/health
   ```

   Expected response:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "version": "0.1.0"
   }
   ```

2. **API Documentation**
   - Visit: `https://your-backend.railway.app/docs`
   - Verify all endpoints are listed
   - Test GET `/api/v1/announcements`

3. **Check Logs**
   ```bash
   # Using Railway CLI
   railway logs

   # Or view in Railway dashboard
   # Project → Service → Logs
   ```

---

## Frontend Deployment (Vercel)

### Step 1: Import Project to Vercel

1. **Login to Vercel**
   - Go to https://vercel.com
   - Click "Add New" → "Project"
   - Import your GitHub repository

2. **Configure Project**
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next` (auto-detected)
   - **Install Command**: `npm install`

### Step 2: Configure Environment Variables

1. **Add Variables in Vercel Dashboard**
   - Go to Project Settings → Environment Variables
   - Copy from `frontend/.env.production.template`

   **Required Variables:**
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   NEXT_PUBLIC_APP_NAME=ASX Announcements
   NEXT_PUBLIC_APP_VERSION=0.1.0
   ```

   **Phase 4 Variables (Authentication & Payments):**
   ```bash
   NEXTAUTH_URL=https://your-app.vercel.app
   NEXTAUTH_SECRET=<generate_random_secret>
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
   ```

2. **Environment Scopes**
   - Set variables for: Production, Preview, Development
   - Use different values for each environment

### Step 3: Deploy Frontend

1. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Deployment typically takes 1-2 minutes

2. **Verify Deployment**
   - Visit your Vercel URL (e.g., `https://your-app.vercel.app`)
   - Check homepage loads correctly
   - Navigate to `/announcements`
   - Verify API calls work (check browser console)

### Step 4: Configure Custom Domain (Optional)

1. **Add Domain**
   - Go to Project Settings → Domains
   - Add your custom domain (e.g., `asxannouncements.com`)

2. **DNS Configuration**
   - Add DNS records as shown by Vercel:
     - Type: `CNAME`, Name: `www`, Value: `cname.vercel-dns.com`
     - Type: `A`, Name: `@`, Value: `76.76.21.21`

3. **SSL Certificate**
   - Vercel automatically provisions SSL certificates
   - Typically takes 1-2 hours to activate

---

## Database Setup

### Initial Database Migration

The backend automatically runs migrations on startup via:
```bash
alembic upgrade head
```

This is configured in `railway.json` start command.

### Manual Migration (if needed)

1. **Connect to Railway PostgreSQL**
   ```bash
   # Get connection string from Railway
   railway connect Postgres

   # Or use DATABASE_URL directly
   psql <DATABASE_URL>
   ```

2. **Run Migrations Manually**
   ```bash
   # In backend directory
   alembic upgrade head
   ```

3. **Verify Tables Created**
   ```sql
   \dt  -- List all tables

   -- Should show:
   -- announcements
   -- companies
   -- analysis
   -- stock_data
   -- users (Phase 4)
   -- subscriptions (Phase 4)
   ```

### Seed Initial Data (Optional)

To test with sample data:

```bash
# Run initial scrape manually
railway run python -c "
from app.services.pipeline import AnnouncementPipeline
from app.services.scraper import ScraperService
import asyncio

async def seed():
    scraper = ScraperService()
    announcements = scraper.fetch_todays_announcements()
    pipeline = AnnouncementPipeline()
    await pipeline.process_batch(announcements[:5])  # First 5

asyncio.run(seed())
"
```

---

## Environment Variables

### Backend Environment Variables (Railway)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key | `AIzaSy...` |
| `STORAGE_TYPE` | ✅ | Storage backend type | `s3` or `r2` or `local` |
| `S3_BUCKET_NAME` | ✅ (if S3) | AWS S3 bucket name | `asx-announcements-prod` |
| `AWS_ACCESS_KEY_ID` | ✅ (if S3) | AWS access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | ✅ (if S3) | AWS secret key | `wJalr...` |
| `SECRET_KEY` | ✅ | Application secret key | Random 32+ chars |
| `CORS_ORIGINS` | ✅ | Allowed frontend origins | `["https://app.vercel.app"]` |
| `SCRAPE_INTERVAL_MINUTES` | ❌ | Scraping frequency | `60` (default) |
| `SCHEDULER_ENABLED` | ❌ | Enable scheduler | `true` (default) |
| `LOG_LEVEL` | ❌ | Logging level | `INFO` (default) |

### Frontend Environment Variables (Vercel)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend API URL | `https://backend.railway.app` |
| `NEXT_PUBLIC_APP_NAME` | ❌ | Application name | `ASX Announcements` |
| `NEXTAUTH_URL` | ✅ (Phase 4) | Frontend URL | `https://app.vercel.app` |
| `NEXTAUTH_SECRET` | ✅ (Phase 4) | NextAuth secret | Random 32+ chars |
| `GOOGLE_CLIENT_ID` | ✅ (Phase 4) | Google OAuth client ID | `123...apps.googleusercontent.com` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | ✅ (Phase 4) | Stripe publishable key | `pk_live_...` |

---

## Post-Deployment Configuration

### 1. Update CORS Origins

In Railway backend environment variables, update `CORS_ORIGINS`:

```bash
# Before deployment
CORS_ORIGINS=["http://localhost:3000"]

# After deployment
CORS_ORIGINS=["https://your-app.vercel.app","https://www.your-domain.com"]
```

### 2. Configure Cloud Storage

#### AWS S3 Setup

1. **Create S3 Bucket**
   ```bash
   aws s3 mb s3://asx-announcements-prod --region ap-southeast-2
   ```

2. **Configure Bucket Policy**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "AWS": "arn:aws:iam::ACCOUNT_ID:user/railway-backend"
         },
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject"
         ],
         "Resource": "arn:aws:s3:::asx-announcements-prod/*"
       }
     ]
   }
   ```

3. **Create IAM User**
   - Create IAM user: `railway-backend`
   - Attach policy: `AmazonS3FullAccess` (or custom policy above)
   - Generate access keys
   - Add to Railway environment variables

#### Cloudflare R2 Setup (Alternative)

1. **Create R2 Bucket**
   - Go to Cloudflare Dashboard → R2
   - Create bucket: `asx-announcements-prod`

2. **Generate API Tokens**
   - Create API token with R2 permissions
   - Copy Account ID, Access Key, Secret Key

3. **Update Railway Variables**
   ```bash
   STORAGE_TYPE=r2
   R2_ACCOUNT_ID=your_account_id
   R2_ACCESS_KEY_ID=your_access_key
   R2_SECRET_ACCESS_KEY=your_secret_key
   R2_BUCKET_NAME=asx-announcements-prod
   ```

### 3. Setup Monitoring

#### Sentry Error Tracking

1. **Create Sentry Project**
   - Go to https://sentry.io
   - Create new project for Python (backend) and Next.js (frontend)

2. **Add to Railway**
   ```bash
   SENTRY_DSN=https://xxx@sentry.io/xxx
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.1
   ```

3. **Add to Vercel**
   ```bash
   NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
   SENTRY_AUTH_TOKEN=sntrys_xxx
   ```

#### Railway Monitoring

- Built-in metrics: CPU, Memory, Network
- View in Railway Dashboard → Service → Metrics
- Set up alerts for high resource usage

#### Vercel Analytics

- Enable in Vercel Dashboard → Analytics
- Free tier includes basic page view analytics

### 4. Configure Scheduler

Verify scheduler is running:

```bash
# Check worker logs in Railway
railway logs --service worker

# Should see:
# "Scheduler started successfully"
# "Scheduled job: scrape_asx_announcements"
```

Manually trigger scrape (for testing):

```bash
railway run python -c "
from app.services.scheduler import SchedulerService
scheduler = SchedulerService()
scheduler.scrape_job()
"
```

---

## Monitoring & Maintenance

### Health Checks

1. **Backend Health**
   ```bash
   curl https://your-backend.railway.app/health
   ```

2. **Frontend Uptime**
   - Use UptimeRobot or Pingdom
   - Monitor: `https://your-app.vercel.app`
   - Alert on downtime

3. **Database Connection**
   ```bash
   # Railway CLI
   railway connect Postgres

   # Check connection
   SELECT 1;
   ```

### Log Monitoring

#### Railway Logs

```bash
# View backend logs
railway logs --service backend

# View worker logs
railway logs --service worker

# Follow logs in real-time
railway logs --follow
```

#### Vercel Logs

```bash
# Install Vercel CLI
npm install -g vercel

# View logs
vercel logs <deployment-url>

# Real-time logs
vercel logs --follow
```

### Database Backups

Railway automatic backups:
- Daily backups retained for 7 days (Starter plan)
- Manual backups via Railway CLI:
  ```bash
  railway backup create
  railway backup list
  railway backup restore <backup-id>
  ```

Manual PostgreSQL backup:
```bash
# Export database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore database
psql $DATABASE_URL < backup_20250107.sql
```

### Performance Monitoring

#### Backend Performance

Monitor in Railway dashboard:
- Request latency (p50, p95, p99)
- Error rate
- Database query performance
- Memory usage

#### Frontend Performance

Monitor in Vercel:
- Core Web Vitals (LCP, FID, CLS)
- Page load times
- API response times

### Cost Monitoring

#### Railway Costs

- Starter plan: $5/month per service
- PostgreSQL: $5/month
- Egress: $0.10/GB
- Total: ~$15-25/month for backend + database + worker

#### Vercel Costs

- Hobby plan: Free (10k requests/month)
- Pro plan: $20/month (unlimited)
- Bandwidth: Included

#### AWS S3 Costs

- Storage: $0.023/GB/month (ap-southeast-2)
- PUT requests: $0.0055/1000 requests
- GET requests: $0.00044/1000 requests
- Estimated: ~$5-10/month for MVP

#### Gemini API Costs

- Free tier: 1500 requests/day (60 RPM)
- Paid tier: $0.00025/1K characters (input), $0.001/1K characters (output)
- Estimated: $10-50/month depending on volume

**Total Monthly Cost: $30-85**

---

## Troubleshooting

### Backend Issues

#### Issue: Database Connection Failed

**Symptoms**: `database connection failed` in logs

**Solutions**:
1. Verify `DATABASE_URL` in Railway variables
2. Check PostgreSQL service is running
3. Verify database allows connections from Railway
4. Check connection pool size: `DATABASE_POOL_SIZE=20`

#### Issue: Gemini API Rate Limit

**Symptoms**: `Resource has been exhausted (e.g. check quota)`

**Solutions**:
1. Upgrade Gemini API quota
2. Reduce scraping frequency: `SCRAPE_INTERVAL_MINUTES=120`
3. Add rate limiting in LLM analyzer
4. Implement request queuing

#### Issue: PDF Download Timeout

**Symptoms**: `TimeoutError` when downloading PDFs

**Solutions**:
1. Increase Playwright timeout: `pdf_downloader.py`
2. Add retry logic with exponential backoff
3. Reduce concurrent downloads: `MAX_CONCURRENT_DOWNLOADS=3`

#### Issue: Storage Upload Failed

**Symptoms**: `ClientError: An error occurred (403)` for S3

**Solutions**:
1. Verify AWS credentials in Railway variables
2. Check S3 bucket policy allows PutObject
3. Verify IAM user has correct permissions
4. Check bucket region matches: `S3_REGION=ap-southeast-2`

### Frontend Issues

#### Issue: API Calls Failing (CORS)

**Symptoms**: Console error: `CORS policy: No 'Access-Control-Allow-Origin'`

**Solutions**:
1. Update backend `CORS_ORIGINS` in Railway:
   ```bash
   CORS_ORIGINS=["https://your-app.vercel.app"]
   ```
2. Redeploy backend service
3. Verify in browser Network tab

#### Issue: Environment Variables Not Loaded

**Symptoms**: `NEXT_PUBLIC_API_URL is undefined`

**Solutions**:
1. Verify variables in Vercel Dashboard → Settings → Environment Variables
2. Ensure variables have `NEXT_PUBLIC_` prefix for client-side
3. Redeploy frontend after adding variables
4. Check variable scope (Production/Preview/Development)

#### Issue: 404 on Announcement Detail Page

**Symptoms**: `/announcements/[id]` returns 404

**Solutions**:
1. Verify dynamic route file exists: `app/announcements/[id]/page.tsx`
2. Check Next.js build logs for errors
3. Ensure API returns correct announcement data
4. Check browser console for API errors

### Scheduler Issues

#### Issue: Scheduler Not Running

**Symptoms**: No new announcements scraped

**Solutions**:
1. Check worker service logs in Railway
2. Verify `SCHEDULER_ENABLED=true`
3. Check scheduler mode: `SCHEDULER_MODE=interval` or `market_hours`
4. Manually trigger: `railway run python -m app.services.scheduler`

#### Issue: Duplicate Announcements

**Symptoms**: Same announcement processed multiple times

**Solutions**:
1. Check database unique constraint on `announcements` table
2. Verify scraper duplicate detection logic
3. Check scheduler interval (too frequent)
4. Add idempotency checks in pipeline

### Database Issues

#### Issue: Migration Failed

**Symptoms**: `alembic upgrade head` fails

**Solutions**:
1. Check migration files in `backend/alembic/versions/`
2. Verify database schema manually:
   ```sql
   SELECT version_num FROM alembic_version;
   ```
3. Reset and rerun migrations:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

#### Issue: Slow Queries

**Symptoms**: API responses > 1 second

**Solutions**:
1. Add database indexes:
   ```sql
   CREATE INDEX idx_announcements_asx_code ON announcements(asx_code);
   CREATE INDEX idx_announcements_date ON announcements(announcement_date);
   CREATE INDEX idx_announcements_sentiment ON announcements(sentiment);
   ```
2. Optimize CRUD queries (use `joinedload`)
3. Implement query result caching
4. Upgrade Railway database plan for more resources

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing locally (`pytest` and `npm test`)
- [ ] Environment variables configured for production
- [ ] Gemini API key valid and has quota
- [ ] AWS S3 or Cloudflare R2 bucket created
- [ ] Database schema reviewed and migrations tested
- [ ] CORS origins configured for production frontend URL

### Backend Deployment

- [ ] Railway project created
- [ ] PostgreSQL database provisioned
- [ ] Backend service deployed
- [ ] Worker service deployed for scheduler
- [ ] Environment variables configured
- [ ] Health check endpoint responding: `/health`
- [ ] API documentation accessible: `/docs`
- [ ] Database migrations run successfully
- [ ] Scheduler running and scraping announcements

### Frontend Deployment

- [ ] Vercel project created and linked to GitHub
- [ ] Environment variables configured
- [ ] Frontend deployed successfully
- [ ] Homepage loads correctly
- [ ] API integration working (announcements list loads)
- [ ] Announcement detail pages loading
- [ ] Filters and pagination working

### Post-Deployment

- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active
- [ ] Monitoring setup (Sentry)
- [ ] Logs configured and accessible
- [ ] Database backups enabled
- [ ] Health checks and uptime monitoring configured
- [ ] Performance metrics tracked

### Phase 4 (Monetization) - Future

- [ ] Google OAuth configured
- [ ] NextAuth.js setup complete
- [ ] Stripe account created
- [ ] Subscription plans configured
- [ ] Payment webhooks configured
- [ ] Free trial logic tested
- [ ] Customer portal accessible

---

## Rollback Procedure

If deployment fails or issues arise:

### Railway Rollback

1. **Rollback to Previous Deployment**
   ```bash
   # Via Railway CLI
   railway rollback

   # Or in Railway Dashboard
   # Service → Deployments → Previous Deployment → Redeploy
   ```

2. **Revert Database Migration**
   ```bash
   # Downgrade one version
   alembic downgrade -1

   # Or downgrade to specific version
   alembic downgrade <revision_id>
   ```

### Vercel Rollback

1. **Rollback Deployment**
   ```bash
   # Via Vercel Dashboard
   # Deployments → Previous Deployment → Promote to Production

   # Or via CLI
   vercel rollback <deployment-url>
   ```

### Emergency Shutdown

If critical issues occur:

1. **Stop Scheduler**
   ```bash
   # In Railway Dashboard
   # Worker Service → Settings → Pause Service
   ```

2. **Disable API**
   ```bash
   # Set environment variable
   MAINTENANCE_MODE=true

   # Or scale down
   # Service → Settings → Scale to 0 instances
   ```

---

## Support & Resources

### Documentation
- **Backend API**: `backend/API_README.md`
- **Frontend**: `frontend/README.md`
- **Project Overview**: `CLAUDE.md`

### External Documentation
- Railway: https://docs.railway.app
- Vercel: https://vercel.com/docs
- Next.js: https://nextjs.org/docs
- FastAPI: https://fastapi.tiangolo.com

### Community
- GitHub Issues: https://github.com/tanveeruddin/asx_announcement_scraper/issues
- Railway Discord: https://discord.gg/railway
- Vercel Discord: https://discord.gg/vercel

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Deployment Ready**: ✅
