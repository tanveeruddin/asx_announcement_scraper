# ASX Announcements SaaS - Project Documentation

## Project Overview

A SaaS application that tracks ASX (Australian Securities Exchange) price-sensitive company announcements, automatically scrapes and analyzes them using AI, and presents actionable insights to investors and traders.

### Vision
Enable retail investors to make faster, more informed decisions by providing:
- Real-time tracking of price-sensitive ASX announcements
- AI-powered analysis (summaries, sentiment, key insights)
- Stock price correlation and market reaction analysis
- Searchable historical database with advanced filtering
- Subscription-based access with free trial

---

## Business Requirements

### Core Features (MVP)
1. **Announcement Tracking**
   - Monitor ASX announcements page: https://www.asx.com.au/asx/v2/statistics/todayAnns.do
   - Filter price-sensitive announcements (marked with $ symbol)
   - Scrape every 30-60 minutes during market hours
   - Download PDF announcements only once (duplicate detection)

2. **AI-Powered Analysis**
   - Convert PDF to markdown for processing
   - Extract summary, sentiment (bullish/bearish/neutral), key insights using LLM
   - Configurable system prompts for analysis customization
   - Store analysis results for instant retrieval

3. **Market Context**
   - Fetch current share price, market capitalization
   - Calculate 1/3/6-month price performance
   - Analyze market reaction (price change correlation with announcement timing)
   - Additional metrics to be added over time

4. **User Features**
   - Search announcements by date range, ASX code, market cap, sentiment
   - View detailed analysis for each announcement
   - Google OAuth authentication
   - Free trial period (configurable X days)
   - Monthly/yearly subscription plans via Stripe

### Future Features (Post-MVP)
- Company watchlists
- Daily end-of-day summary emails
- Real-time SMS/email alerts for watchlist announcements
- iOS/Android mobile applications
- Advanced analytics and pattern detection

### Subscription Model
- **Free Trial**: X days (configurable via environment variable)
- **Monthly Plan**: $TBD/month
- **Yearly Plan**: $TBD/year (discounted)
- Grace period for payment failures
- Automatic renewal with Stripe webhooks

---

## Technical Architecture

### Tech Stack

#### Backend
- **Framework**: FastAPI (Python 3.11+)
  - Async/await support for concurrent operations
  - Automatic OpenAPI documentation
  - Fast performance and modern Python features

- **Database**: PostgreSQL
  - Local: Docker Compose for development
  - Production: Railway managed PostgreSQL
  - ORM: SQLAlchemy with Alembic migrations

- **Scraping**: BeautifulSoup4 + Requests
  - Parses static HTML page
  - Robust error handling for network issues

- **PDF Processing**: PyMuPDF (fitz)
  - High-quality PDF to markdown conversion
  - Text extraction with layout preservation

- **LLM**: Google Gemini API
  - Cost-effective (50-75% cheaper than OpenAI)
  - Generous free tier (1500 requests/day)
  - Excellent for long documents (multi-page announcements)
  - Structured output support

- **Stock Data**: yfinance (Yahoo Finance)
  - Free, reliable historical and current data
  - 15-minute delayed quotes (sufficient for post-announcement analysis)
  - Upgrade path to real-time APIs if needed

- **Task Scheduling**: APScheduler
  - Simple cron-like scheduling for periodic scraping
  - No external dependencies (vs Celery + Redis)
  - Can migrate to Railway cron jobs if needed

- **Authentication**: JWT tokens
  - OAuth2 flow for Google login
  - Token-based API authentication

#### Frontend
- **Framework**: Next.js 14+ (App Router)
  - React 18 with Server Components
  - TypeScript for type safety
  - Server-side rendering for SEO

- **Authentication**: NextAuth.js
  - Google OAuth provider
  - Session management
  - Protected routes

- **Styling**: Tailwind CSS
  - Rapid UI development
  - Consistent design system
  - Responsive by default

- **Charts**: Recharts or Chart.js
  - Stock price visualization
  - Performance trends

- **API Client**: Axios or Fetch API
  - TypeScript types for API responses

#### DevOps & Infrastructure
- **Version Control**: Git + GitHub
- **Containerization**: Docker + Docker Compose
- **Frontend Hosting**: Vercel
  - Automatic deployments from GitHub
  - Edge network for global performance
  - Free tier for MVP

- **Backend Hosting**: Railway
  - FastAPI + PostgreSQL + worker in one service
  - $5-20/month for MVP scale
  - Auto-scaling and monitoring
  - GitHub integration

- **File Storage**:
  - Local: File system (development)
  - Production: AWS S3 or Cloudflare R2
  - Configurable via environment variables

- **Payments**: Stripe
  - Subscription management
  - Webhook handling for events
  - Customer portal for self-service

- **Monitoring**: Sentry (errors) + Railway logs

---

## Design Decisions & Reasoning

### 1. FastAPI over Django/Flask
**Decision**: Use FastAPI for backend API

**Reasoning**:
- **Async Support**: Critical for concurrent scraping, PDF processing, and LLM calls
- **Performance**: Faster than Django for API-only workloads
- **Modern**: Type hints, Pydantic validation, automatic docs
- **Developer Experience**: Less boilerplate than Django, more structure than Flask
- **Ecosystem**: Great for ML/AI integrations (Gemini, PDF processing)

### 2. Google Gemini over OpenAI
**Decision**: Use Gemini API for LLM analysis

**Reasoning**:
- **Cost**: 50-75% cheaper than GPT-4, competitive with GPT-3.5
- **Free Tier**: 1500 requests/day = ~45K/month (enough for MVP testing)
- **Context Length**: Excellent for long documents (announcements can be 20+ pages)
- **Quality**: Comparable reasoning and extraction quality
- **Integration**: Native Google Cloud integration for future scale
- **Risk Mitigation**: Easy to swap with Claude/OpenAI (modular service design)

### 3. PostgreSQL over MongoDB/SQLite
**Decision**: Use PostgreSQL as primary database

**Reasoning**:
- **Relational Model**: Clear relationships (users → subscriptions, companies → announcements)
- **ACID Compliance**: Critical for payment/subscription data integrity
- **JSONB Support**: Flexible storage for LLM analysis results (semi-structured data)
- **Production Ready**: Easy migration from local to Railway/RDS/CloudSQL
- **Ecosystem**: Excellent Python support (SQLAlchemy, psycopg3)
- **Scale**: Can handle millions of announcements with proper indexing

### 4. Next.js over React SPA
**Decision**: Use Next.js App Router for frontend

**Reasoning**:
- **SEO**: Server-side rendering for public landing pages (marketing)
- **Performance**: Server components reduce JavaScript bundle size
- **Developer Experience**: Built-in routing, API routes, optimized images
- **Deployment**: Vercel optimized, zero-config production deployments
- **Full-Stack**: Can handle simple backend logic (webhooks, OAuth callbacks)
- **Future-Proof**: React Server Components are the future of React

### 5. Vercel + Railway over AWS/GCP
**Decision**: Deploy on Vercel (frontend) + Railway (backend)

**Reasoning**:
- **Simplicity**: Avoid AWS complexity for MVP (IAM, VPC, load balancers)
- **Cost**: Combined $5-20/month vs AWS $50-100+ for similar setup
- **Developer Experience**: Git push to deploy, no infrastructure management
- **Speed**: Get to market faster without DevOps overhead
- **Monitoring**: Built-in logs, metrics, alerting
- **Migration Path**: Can move to AWS/GCP later if scale requires (database export, Docker images)

### 6. Modular Service Architecture
**Decision**: Separate services for scraper, PDF processor, LLM, stock data

**Reasoning**:
- **Testability**: Each service can be unit tested independently
- **Swappability**: Easy to replace implementations (e.g., Gemini → Claude)
- **Maintainability**: Clear boundaries and responsibilities
- **Scalability**: Can extract to microservices later if needed
- **Development**: Team members can work on different services in parallel

### 7. yfinance over Paid APIs
**Decision**: Use free yfinance library for stock data

**Reasoning**:
- **Cost**: Free, unlimited requests for MVP validation
- **Sufficient**: 15-min delayed data is fine for post-announcement analysis
- **Reliability**: Battle-tested, widely used library
- **Upgrade Path**: Can move to Alpha Vantage, Polygon, IEX later
- **Data Coverage**: Excellent historical data for 1/3/6-month trends

### 8. Configuration-Driven Design
**Decision**: All environment-specific settings in config files

**Reasoning**:
- **Pluggability**: Zero code changes for local → production migration
- **Security**: Secrets in environment variables, not version control
- **Flexibility**: Change scrape frequency, free trial days, LLM prompts without deployment
- **Testing**: Easy to create test configurations
- **Multi-Environment**: Dev, staging, production with same codebase

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    oauth_provider VARCHAR(50), -- 'google', 'github', etc.
    oauth_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    plan_type VARCHAR(50), -- 'monthly', 'yearly'
    status VARCHAR(50), -- 'trialing', 'active', 'canceled', 'past_due'
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    canceled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Companies Table
```sql
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asx_code VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    market_cap DECIMAL(20, 2),
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Announcements Table
```sql
CREATE TABLE announcements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id),
    asx_code VARCHAR(10) NOT NULL,
    title TEXT NOT NULL,
    announcement_date TIMESTAMP NOT NULL,
    pdf_url TEXT NOT NULL,
    pdf_local_path TEXT,
    markdown_path TEXT,
    is_price_sensitive BOOLEAN DEFAULT FALSE,
    num_pages INTEGER,
    file_size_kb INTEGER,
    downloaded_at TIMESTAMP,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(asx_code, announcement_date, title) -- Prevent duplicates
);
```

### Analysis Table
```sql
CREATE TABLE analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    announcement_id UUID REFERENCES announcements(id) ON DELETE CASCADE,
    summary TEXT,
    sentiment VARCHAR(20), -- 'bullish', 'bearish', 'neutral'
    key_insights JSONB, -- Array of insights
    llm_model VARCHAR(50), -- 'gemini-1.5-pro', etc.
    llm_prompt_version VARCHAR(50),
    confidence_score DECIMAL(3, 2), -- 0.00 to 1.00
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Stock Data Table
```sql
CREATE TABLE stock_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    announcement_id UUID REFERENCES announcements(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id),
    price_at_announcement DECIMAL(10, 4),
    price_1h_after DECIMAL(10, 4),
    price_1d_after DECIMAL(10, 4),
    price_change_pct DECIMAL(6, 2),
    volume_at_announcement BIGINT,
    market_cap DECIMAL(20, 2),
    pe_ratio DECIMAL(8, 2),
    performance_1m_pct DECIMAL(6, 2),
    performance_3m_pct DECIMAL(6, 2),
    performance_6m_pct DECIMAL(6, 2),
    fetched_at TIMESTAMP DEFAULT NOW()
);
```

### Watchlists Table (Future Feature)
```sql
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, company_id)
);
```

---

## API Design

### Authentication
- `POST /auth/google` - Google OAuth callback, returns JWT
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user profile

### Announcements
- `GET /announcements` - List announcements (with pagination, filters)
  - Query params: `page`, `limit`, `asx_code`, `date_from`, `date_to`, `sentiment`, `min_market_cap`, `max_market_cap`
- `GET /announcements/{id}` - Get single announcement with full analysis
- `GET /announcements/{id}/pdf` - Download original PDF
- `GET /announcements/{id}/markdown` - Get markdown content

### Companies
- `GET /companies` - List all companies
- `GET /companies/{asx_code}` - Get company details
- `GET /companies/{asx_code}/announcements` - Company announcement history

### Search
- `POST /search` - Advanced search with full-text, filters, sorting

### Subscriptions
- `GET /subscriptions/plans` - Available subscription plans
- `POST /subscriptions/checkout` - Create Stripe checkout session
- `GET /subscriptions/status` - Current subscription status
- `POST /subscriptions/cancel` - Cancel subscription
- `POST /subscriptions/portal` - Get Stripe customer portal URL

### Webhooks
- `POST /webhooks/stripe` - Handle Stripe events (subscription lifecycle)

### Admin (Future)
- `GET /admin/stats` - Dashboard statistics
- `POST /admin/scrape/trigger` - Manual scrape trigger
- `GET /admin/scrape/status` - Scraper job status

---

## Modular Service Architecture

### 1. Scraper Service (`services/scraper.py`)
**Responsibility**: Fetch and parse ASX announcements page

**Key Methods**:
- `fetch_todays_announcements() -> List[AnnouncementData]`
- `filter_price_sensitive(announcements) -> List[AnnouncementData]`
- `check_for_new_announcements(existing_ids) -> List[AnnouncementData]`

**Configuration**:
- ASX URL (env var)
- User-agent string
- Request timeout

### 2. PDF Downloader Service (`services/pdf_downloader.py`)
**Responsibility**: Download PDFs and track storage

**Key Methods**:
- `download_pdf(url, announcement_id) -> str` (returns local path)
- `is_already_downloaded(announcement_id) -> bool`
- `get_storage_path(announcement_id) -> str`

**Storage Strategies** (pluggable):
- `LocalFileStorage` - File system (dev)
- `S3Storage` - AWS S3 (production)
- `R2Storage` - Cloudflare R2 (production alternative)

### 3. PDF Processor Service (`services/pdf_processor.py`)
**Responsibility**: Convert PDF to markdown

**Key Methods**:
- `convert_to_markdown(pdf_path) -> str`
- `extract_metadata(pdf_path) -> dict` (pages, file size)
- `save_markdown(content, announcement_id) -> str`

**Libraries**: PyMuPDF, markdown formatting

### 4. LLM Analyzer Service (`services/llm_analyzer.py`)
**Responsibility**: Extract insights using Gemini

**Key Methods**:
- `analyze_announcement(markdown_content) -> AnalysisResult`
- `extract_summary(markdown) -> str`
- `determine_sentiment(markdown) -> str`
- `extract_key_insights(markdown) -> List[str]`

**Configuration**:
- Gemini API key
- Model name (gemini-1.5-pro, gemini-1.5-flash)
- System prompt (customizable per analysis type)
- Temperature, max tokens

**Prompt Engineering**:
```python
ANALYSIS_PROMPT = """
Analyze this ASX company announcement and provide:

1. **Summary** (2-3 sentences): Concise overview of the announcement
2. **Sentiment**: Classify as BULLISH, BEARISH, or NEUTRAL
3. **Key Insights** (3-5 bullet points): Most important takeaways
4. **Financial Impact**: Estimate potential impact on stock price

Announcement:
{markdown_content}

Return as JSON:
{
  "summary": "...",
  "sentiment": "BULLISH|BEARISH|NEUTRAL",
  "key_insights": ["...", "..."],
  "financial_impact": "..."
}
"""
```

### 5. Stock Data Service (`services/stock_data.py`)
**Responsibility**: Fetch stock prices and metrics

**Key Methods**:
- `get_current_price(asx_code) -> Decimal`
- `get_market_cap(asx_code) -> Decimal`
- `get_performance_metrics(asx_code, periods) -> dict`
- `analyze_market_reaction(asx_code, announcement_time) -> dict`

**Data Sources**:
- yfinance for historical and current data
- Caching strategy to avoid rate limits
- Retry logic for network failures

### 6. Scheduler Service (`services/scheduler.py`)
**Responsibility**: Periodic scraping orchestration

**Key Methods**:
- `schedule_scraping_job(interval_minutes)`
- `run_scrape_pipeline()` - Orchestrates all services
- `handle_errors(exception)`

**Pipeline Flow**:
1. Scraper fetches new announcements
2. For each new announcement:
   - Download PDF
   - Convert to markdown
   - Analyze with LLM
   - Fetch stock data
   - Save to database
3. Log results and errors

---

## Implementation Roadmap

### Phase 1: MVP Foundation (Week 1-2)
**Goal**: Basic scraping and data pipeline working

**Tasks**:
1. Project setup (backend/frontend structure)
2. FastAPI + PostgreSQL + Docker Compose
3. SQLAlchemy models and Alembic migrations
4. Scraper service (BeautifulSoup)
5. PDF downloader with local storage
6. PyMuPDF integration
7. Basic API endpoints (GET /announcements)
8. Simple CLI script to test pipeline

**Deliverable**: Can scrape ASX, download PDFs, store in database

### Phase 2: Intelligence Layer (Week 2-3)
**Goal**: AI analysis and stock data integration

**Tasks**:
1. Gemini API integration
2. LLM analyzer service (summary, sentiment, insights)
3. Configurable system prompts
4. yfinance integration
5. Market reaction analysis
6. APScheduler setup for periodic scraping
7. Enhanced API endpoints with analysis data

**Deliverable**: Announcements enriched with AI insights and stock data

### Phase 3: Web Application (Week 3-4)
**Goal**: Functional frontend for viewing data

**Tasks**:
1. Next.js project setup
2. NextAuth.js with Google OAuth
3. Dashboard UI (announcement cards)
4. Search and filter components
5. Announcement detail page
6. Stock performance charts
7. API client integration

**Deliverable**: Users can login, search, and view analyzed announcements

### Phase 4: Monetization (Week 4-5)
**Goal**: Subscription system with free trial

**Tasks**:
1. Stripe integration (checkout, subscriptions)
2. Free trial logic (configurable days)
3. Subscription status middleware
4. Webhook handlers (subscription events)
5. Payment UI and customer portal
6. Subscription management page

**Deliverable**: Users can subscribe and access content based on plan

### Phase 5: Production Deployment (Week 5-6)
**Goal**: Live application on Vercel + Railway

**Tasks**:
1. Environment configuration (local vs production)
2. Railway setup (FastAPI + PostgreSQL + worker)
3. Vercel deployment (Next.js)
4. S3/R2 migration for file storage
5. Database migration to Railway
6. Monitoring and error tracking (Sentry)
7. Performance optimization
8. Security audit (API rate limiting, input validation)

**Deliverable**: Production-ready SaaS application

### Phase 6: Post-MVP Enhancements (Week 6+)
**Goal**: User engagement and retention features

**Tasks**:
1. Company watchlists
2. Email notifications (SendGrid)
3. SMS alerts (Twilio)
4. Daily digest emails
5. Mobile app planning (React Native)
6. Advanced analytics dashboard
7. User feedback collection

**Deliverable**: Enhanced product with retention features

---

## Development Guidelines

### Code Style
- **Python**: Black formatter, isort, flake8, mypy
- **TypeScript**: ESLint, Prettier
- **Naming**: snake_case (Python), camelCase (TypeScript)

### Testing Strategy
- **Backend**: pytest with fixtures for database, mocked external APIs
- **Frontend**: Jest + React Testing Library
- **E2E**: Playwright for critical user flows
- **Coverage**: Aim for 80%+ on business logic

### Git Workflow
- **Branches**: `main` (production), `develop` (integration), `feature/*`
- **Commits**: Conventional commits (feat, fix, docs, refactor)
- **PRs**: Required for all changes, CI checks must pass

### Environment Variables

#### Backend (`backend/.env`)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/asx_announcements
DATABASE_POOL_SIZE=10

# Storage
STORAGE_TYPE=local  # local | s3 | r2
LOCAL_STORAGE_PATH=./data/pdfs
S3_BUCKET_NAME=
S3_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# LLM
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-pro
GEMINI_TEMPERATURE=0.3
GEMINI_MAX_TOKENS=2048

# Scraper
ASX_URL=https://www.asx.com.au/asx/v2/statistics/todayAnns.do
SCRAPE_INTERVAL_MINUTES=60
MAX_CONCURRENT_DOWNLOADS=5

# Authentication
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_MONTHLY_PRICE_ID=price_...
STRIPE_YEARLY_PRICE_ID=price_...

# Subscription
FREE_TRIAL_DAYS=7

# External APIs
YFINANCE_CACHE_HOURS=1
```

#### Frontend (`frontend/.env.local`)
```bash
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

---

## Configuration Strategy

### Pluggable Components

#### 1. Database Connection
```python
# config.py
class Settings(BaseSettings):
    database_url: str
    database_pool_size: int = 10

    class Config:
        env_file = ".env"

# db.py
def get_database_url():
    settings = Settings()
    return settings.database_url

# Easy to swap: local PostgreSQL → Railway → RDS
```

#### 2. Storage Backend
```python
# storage/base.py
class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_path: str, content: bytes) -> str:
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes:
        pass

# storage/local.py
class LocalStorage(StorageBackend):
    def save(self, file_path: str, content: bytes) -> str:
        # Save to file system

# storage/s3.py
class S3Storage(StorageBackend):
    def save(self, file_path: str, content: bytes) -> str:
        # Upload to S3

# storage/factory.py
def get_storage() -> StorageBackend:
    storage_type = settings.storage_type
    if storage_type == "local":
        return LocalStorage()
    elif storage_type == "s3":
        return S3Storage()
    # Easy to add new storage types
```

#### 3. LLM Provider
```python
# llm/base.py
class LLMProvider(ABC):
    @abstractmethod
    def analyze(self, prompt: str, content: str) -> dict:
        pass

# llm/gemini.py
class GeminiProvider(LLMProvider):
    def analyze(self, prompt: str, content: str) -> dict:
        # Call Gemini API

# llm/openai.py
class OpenAIProvider(LLMProvider):
    def analyze(self, prompt: str, content: str) -> dict:
        # Call OpenAI API

# llm/factory.py
def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider
    if provider == "gemini":
        return GeminiProvider()
    elif provider == "openai":
        return OpenAIProvider()
    # Swap providers with one env var change
```

---

## Security Considerations

### Authentication & Authorization
- OAuth tokens stored securely (httpOnly cookies)
- JWT tokens with short expiration (1 hour)
- Refresh tokens for long-lived sessions
- Rate limiting on auth endpoints (prevent brute force)

### API Security
- CORS whitelist (only allow frontend domain)
- API rate limiting per user (prevent abuse)
- Input validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (React auto-escaping)

### Data Privacy
- User emails encrypted at rest (optional)
- No PII in logs
- GDPR compliance (data export, account deletion)
- Stripe handles payment data (PCI compliant)

### Infrastructure
- Environment secrets in Railway/Vercel (not git)
- HTTPS only in production
- Database connection pooling (prevent exhaustion)
- Regular dependency updates (Dependabot)

---

## Performance Optimization

### Backend
- Database indexing (ASX code, announcement date, user ID)
- Connection pooling (10-20 connections)
- Async endpoints for I/O-bound operations
- Redis caching for stock data (future)
- Background jobs for long-running tasks

### Frontend
- Next.js image optimization
- Code splitting (dynamic imports)
- API response caching (React Query)
- Virtualized lists for large datasets
- Lazy loading for charts and PDFs

### Scraping
- Parallel PDF downloads (max 5 concurrent)
- Incremental scraping (only fetch new announcements)
- Retry logic with exponential backoff
- Circuit breaker for failing external APIs

---

## Monitoring & Observability

### Metrics to Track
- Scraper success rate (% of announcements processed)
- LLM API latency and cost per request
- Database query performance
- API endpoint latency (p50, p95, p99)
- User signups and subscription conversions
- Churn rate and cancellations

### Logging
- Structured logs (JSON format)
- Log levels: DEBUG (dev), INFO (production)
- Correlation IDs for request tracing
- Error context (stack traces, user ID, timestamp)

### Alerts
- Scraper failures (email notification)
- Database connection failures
- High error rate (>5% in 5 minutes)
- Payment webhook failures
- Low balance warnings (Stripe, Gemini API)

---

## Cost Estimation (MVP)

### Infrastructure
- Railway (backend + database): $20/month
- Vercel (frontend): $0 (free tier)
- Domain: $15/year
- **Total Infrastructure**: ~$25/month

### APIs & Services
- Gemini API: $0-50/month (free tier → paid as usage grows)
- yfinance: Free
- Stripe: 2.9% + $0.30 per transaction
- SendGrid (future): $0-15/month
- **Total APIs**: $0-100/month (scales with users)

### Total MVP Cost: $25-125/month

### Break-Even Analysis
- Target: 10 paying users at $20/month = $200 revenue
- Covers infrastructure + small API costs
- Scale to 50 users = $1000/month → sustainable

---

## Success Metrics

### Product Metrics
- **Activation**: % of signups who view >5 announcements
- **Retention**: % of users returning weekly
- **Conversion**: % of free trial users who subscribe
- **Churn**: % of subscribers canceling monthly

### Technical Metrics
- **Reliability**: 99.5% uptime for scraper and API
- **Performance**: <500ms API response time (p95)
- **Accuracy**: >90% LLM sentiment accuracy (manual validation)
- **Cost Efficiency**: <$5 cost per customer per month

---

## Future Enhancements (Beyond MVP)

### Advanced Features
- Real-time WebSocket updates for live announcements
- Historical announcement database (last 5 years)
- AI-powered stock price prediction
- Portfolio tracking with announcement impact
- Company comparison tool
- Custom alert rules (e.g., market cap > $1B and sentiment bullish)

### Technical Improvements
- Multi-region deployment (latency optimization)
- Real-time data feeds (WebSocket from ASX)
- Machine learning for sentiment refinement
- Full-text search with Elasticsearch
- Data warehouse for analytics (BigQuery)
- Mobile app (React Native)

### Business Features
- Referral program (give 1 month, get 1 month)
- Team plans (multiple users, shared watchlists)
- API access tier (for developers)
- White-label solution for brokers
- Premium tier with SMS alerts

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL (via Docker)
- Git

### Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd asx-announcement-saas

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install poetry
poetry install
cp .env.example .env  # Configure environment variables

# Start PostgreSQL
docker-compose up -d postgres

# Run migrations
alembic upgrade head

# Start backend
uvicorn app.main:app --reload

# Frontend setup (new terminal)
cd ../frontend
npm install
cp .env.example .env.local  # Configure environment variables
npm run dev
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

---

## Questions & Next Steps

### Open Questions
1. What should the exact subscription pricing be? ($15/month, $120/year?)
2. How many days for free trial? (7 days recommended)
3. Should we support other OAuth providers (GitHub, Microsoft)?
4. What's the brand name for the SaaS?
5. Do we need a landing page with marketing content?

### Immediate Next Steps
1. Create project structure (backend/frontend)
2. Setup FastAPI + PostgreSQL with Docker
3. Implement basic scraper service
4. Test end-to-end scraping pipeline
5. Iterate on LLM prompts for quality analysis

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Status**: Ready for Development
