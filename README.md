# ASX Announcements SaaS

A SaaS application that tracks ASX (Australian Securities Exchange) price-sensitive company announcements, automatically scrapes and analyzes them using AI, and presents actionable insights to investors and traders.

## Features

- Real-time tracking of price-sensitive ASX announcements
- AI-powered analysis using Google Gemini (summaries, sentiment, key insights)
- Stock price correlation and market reaction analysis
- Advanced search and filtering (date, ASX code, market cap, sentiment)
- Subscription-based access with configurable free trial
- Google OAuth authentication

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy
- **Package Manager**: UV
- **LLM**: Google Gemini API
- **Stock Data**: yfinance (Yahoo Finance)
- **Scraping**: BeautifulSoup4
- **PDF Processing**: PyMuPDF

### Frontend
- **Framework**: Next.js 14+ (React + TypeScript)
- **Styling**: Tailwind CSS
- **Authentication**: NextAuth.js (Google OAuth)
- **Charts**: Recharts

### Infrastructure
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Railway
- **Payments**: Stripe
- **Storage**: Local filesystem (dev) → S3/R2 (production)

## Project Structure

```
asx-announcement-saas/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic (scraper, PDF, LLM, stock)
│   │   ├── db/           # Database configuration
│   │   ├── auth/         # Authentication & authorization
│   │   ├── config.py     # Settings & environment variables
│   │   └── main.py       # FastAPI application
│   ├── migrations/       # Alembic database migrations
│   ├── tests/            # Backend tests
│   ├── pyproject.toml    # UV dependencies
│   └── Dockerfile        # Container configuration
├── frontend/             # Next.js frontend
│   ├── src/
│   │   ├── app/          # Next.js pages (app router)
│   │   ├── components/   # React components
│   │   ├── lib/          # API client, utilities
│   │   └── styles/       # Tailwind configuration
│   ├── public/           # Static assets
│   ├── package.json      # npm dependencies
│   └── tsconfig.json     # TypeScript configuration
├── docker-compose.yml    # Local PostgreSQL
├── CLAUDE.md             # Detailed project documentation
└── README.md             # This file
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- UV package manager
- Docker & Docker Compose
- Git

### Backend Setup

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to backend directory
cd backend

# Install dependencies with UV
uv sync

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload
```

Backend will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:3000

## Environment Variables

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/asx_announcements

# Storage
STORAGE_TYPE=local
LOCAL_STORAGE_PATH=./data/pdfs

# LLM
GEMINI_API_KEY=your_gemini_api_key

# Scraper
ASX_URL=https://www.asx.com.au/asx/v2/statistics/todayAnns.do
SCRAPE_INTERVAL_MINUTES=60

# Authentication
JWT_SECRET_KEY=your_jwt_secret

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Subscription
FREE_TRIAL_DAYS=7
```

### Frontend (.env.local)
```bash
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Development

### Running Tests

```bash
# Backend tests
cd backend
uv run pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations

```bash
# Create new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

## Deployment

This project is deployment-ready for Vercel (frontend) and Railway (backend).

### Quick Deployment Guide

1. **Generate Secrets**
   ```bash
   python scripts/generate-secrets.py
   ```

2. **Deploy Backend to Railway**
   - Create Railway project
   - Add PostgreSQL database
   - Configure environment variables (see `.env.railway.template`)
   - Deploy from GitHub repository
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions

3. **Deploy Frontend to Vercel**
   - Import GitHub repository to Vercel
   - Set root directory to `frontend`
   - Configure environment variables (see `.env.production.template`)
   - Deploy
   - See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions

4. **Verify Deployment**
   ```bash
   BACKEND_URL=https://your-backend.railway.app \
   FRONTEND_URL=https://your-app.vercel.app \
   ./scripts/deploy-check.sh
   ```

### Deployment Documentation

For comprehensive deployment instructions, including:
- Step-by-step Railway and Vercel setup
- Environment variable configuration
- Database migration guide
- Troubleshooting common issues
- Monitoring and maintenance

See **[DEPLOYMENT.md](DEPLOYMENT.md)**

### Configuration Files

- `backend/railway.json` - Railway service configuration
- `backend/Procfile` - Process definitions for Railway
- `backend/.env.railway.template` - Production environment variables
- `frontend/vercel.json` - Vercel deployment configuration
- `frontend/.env.production.template` - Frontend environment variables

## Documentation

For detailed technical documentation, architecture decisions, and implementation roadmap, see [CLAUDE.md](CLAUDE.md).

## Cost Estimation (MVP)

- **Infrastructure**: ~$25/month (Railway + Vercel)
- **APIs**: $0-100/month (Gemini, Stripe fees)
- **Total**: $25-125/month
- **Break-even**: 10 paying users at $20/month

## Roadmap

### Phase 0: Project Setup (✅ Complete)
- ✅ Project structure and Git repository
- ✅ Database schema and migrations
- ✅ Docker Compose for local development
- ✅ Documentation (CLAUDE.md, README.md)

### Phase 1: Core Engine (✅ Complete)
- ✅ ASX scraper service
- ✅ PDF downloader with Playwright
- ✅ PDF to Markdown converter
- ✅ Google Gemini LLM analyzer
- ✅ Stock data service (yfinance)
- ✅ APScheduler orchestration
- ✅ Pipeline integration

### Phase 2: Backend API (✅ Complete)
- ✅ RESTful API endpoints (FastAPI)
- ✅ Database CRUD services
- ✅ Pagination and filtering
- ✅ OpenAPI documentation
- ✅ Health check endpoints

### Phase 3: Frontend Application (✅ Complete)
- ✅ Next.js 15 with App Router
- ✅ TypeScript and Tailwind CSS
- ✅ Announcements list with filtering
- ✅ Announcement detail page
- ✅ Fully typed API client
- ✅ Responsive design

### Phase 4: Monetization (🔜 Next)
- ⏳ Google OAuth integration
- ⏳ NextAuth.js setup
- ⏳ Stripe subscriptions
- ⏳ Free trial logic
- ⏳ Payment workflows

### Phase 5: Deployment (✅ Ready)
- ✅ Railway configuration (backend)
- ✅ Vercel configuration (frontend)
- ✅ Environment templates
- ✅ Deployment documentation (DEPLOYMENT.md)
- ✅ Deployment verification scripts

### Phase 6: Future Enhancements
- ⏳ Company watchlists
- ⏳ Email/SMS notifications
- ⏳ Real-time WebSocket updates
- ⏳ Mobile applications (React Native)

## Contributing

This is a private project. Contributions are currently not accepted.

## License

Proprietary - All rights reserved

## Support

For issues or questions, please contact the development team.

---

**Last Updated**: 2025-11-07
**Version**: 0.1.0
**Status**: In Development
