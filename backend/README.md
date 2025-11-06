# ASX Announcements Backend

FastAPI backend service for the ASX Announcements SaaS application.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Package Manager**: UV
- **Python**: 3.11+

## Setup

### Prerequisites

- Python 3.11 or higher
- UV package manager
- PostgreSQL (via Docker or local installation)

### Installation

1. Install dependencies:
```bash
uv sync
```

2. Install development dependencies:
```bash
uv sync --dev
```

3. Copy environment variables:
```bash
cp .env.example .env
```

4. Edit `.env` with your configuration (API keys, database URL, etc.)

5. Start PostgreSQL (if using Docker):
```bash
cd ..
docker-compose up -d postgres
```

6. Run database migrations:
```bash
uv run alembic upgrade head
```

7. Start development server:
```bash
uv run uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000
API documentation: http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   │   ├── v1/
│   │   │   ├── announcements.py
│   │   │   ├── auth.py
│   │   │   ├── companies.py
│   │   │   ├── subscriptions.py
│   │   │   └── webhooks.py
│   │   └── deps.py       # Dependencies (auth, database)
│   ├── models/           # SQLAlchemy models
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── announcement.py
│   │   ├── subscription.py
│   │   ├── analysis.py
│   │   └── stock_data.py
│   ├── services/         # Business logic
│   │   ├── scraper.py
│   │   ├── pdf_downloader.py
│   │   ├── pdf_processor.py
│   │   ├── llm_analyzer.py
│   │   ├── stock_data.py
│   │   └── scheduler.py
│   ├── db/               # Database configuration
│   │   ├── base.py
│   │   └── session.py
│   ├── auth/             # Authentication & authorization
│   │   ├── jwt.py
│   │   └── oauth.py
│   ├── config.py         # Settings (Pydantic)
│   └── main.py           # FastAPI application
├── migrations/           # Alembic migrations
├── tests/                # Test suite
├── pyproject.toml        # UV dependencies
├── .env.example          # Example environment variables
└── README.md             # This file
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_scraper.py
```

### Code Formatting

```bash
# Format code with Black
uv run black app/ tests/

# Sort imports with isort
uv run isort app/ tests/

# Lint with flake8
uv run flake8 app/ tests/

# Type check with mypy
uv run mypy app/
```

### Database Migrations

```bash
# Create new migration (auto-generate from models)
uv run alembic revision --autogenerate -m "Add new table"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Show migration history
uv run alembic history
```

### Manual Scraper Execution

```bash
# Run scraper manually (useful for testing)
uv run python -m app.services.scraper
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/google` - Google OAuth login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### Announcements
- `GET /api/v1/announcements` - List announcements (paginated, filtered)
- `GET /api/v1/announcements/{id}` - Get announcement details
- `GET /api/v1/announcements/{id}/pdf` - Download PDF
- `GET /api/v1/announcements/{id}/markdown` - Get markdown content

### Companies
- `GET /api/v1/companies` - List companies
- `GET /api/v1/companies/{asx_code}` - Get company details
- `GET /api/v1/companies/{asx_code}/announcements` - Company announcements

### Subscriptions
- `GET /api/v1/subscriptions/plans` - Available plans
- `POST /api/v1/subscriptions/checkout` - Create checkout session
- `GET /api/v1/subscriptions/status` - Current subscription status
- `POST /api/v1/subscriptions/cancel` - Cancel subscription
- `POST /api/v1/subscriptions/portal` - Get customer portal URL

### Webhooks
- `POST /api/v1/webhooks/stripe` - Stripe webhook handler

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Google Gemini API key
- `STRIPE_SECRET_KEY`: Stripe secret key
- `JWT_SECRET_KEY`: Secret for JWT token signing
- `STORAGE_TYPE`: Storage backend (local, s3, r2)

## Services

### Scraper Service
Monitors ASX announcements page and detects new price-sensitive announcements.

### PDF Downloader
Downloads PDF announcements and stores them (local filesystem or cloud).

### PDF Processor
Converts PDF files to markdown using PyMuPDF.

### LLM Analyzer
Analyzes announcements using Google Gemini to extract:
- Summary
- Sentiment (bullish/bearish/neutral)
- Key insights
- Financial impact

### Stock Data Service
Fetches stock prices and metrics from Yahoo Finance:
- Current price
- Market capitalization
- 1/3/6-month performance
- Volume and trading data

### Scheduler Service
Orchestrates periodic scraping (every 30-60 minutes) and data processing pipeline.

## Deployment

### Railway

1. Install Railway CLI:
```bash
npm install -g railway
```

2. Login and link project:
```bash
railway login
railway link
```

3. Set environment variables in Railway dashboard

4. Deploy:
```bash
railway up
```

### Docker

Build and run with Docker:
```bash
docker build -t asx-backend .
docker run -p 8000:8000 --env-file .env asx-backend
```

## Monitoring

- Health check: `GET /health`
- Metrics: `GET /metrics` (Prometheus format)
- Logs: Structured JSON logging to stdout

## License

Proprietary - All rights reserved
