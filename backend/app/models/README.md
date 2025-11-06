# Database Models

This directory contains all SQLAlchemy ORM models for the ASX Announcements SaaS application.

## Models Overview

### 1. User (`user.py`)
**Purpose**: Store user accounts and authentication information

**Key Fields**:
- `email`: Unique user email
- `oauth_provider`: OAuth provider (Google, GitHub, etc.)
- `is_active`: Account status

**Relationships**:
- One-to-One with Subscription
- One-to-Many with Watchlist

### 2. Company (`company.py`)
**Purpose**: Store ASX listed company information

**Key Fields**:
- `asx_code`: Unique ASX ticker code (e.g., "BHP", "CBA")
- `company_name`: Full company name
- `market_cap`: Current market capitalization

**Relationships**:
- One-to-Many with Announcement
- One-to-Many with StockData
- One-to-Many with Watchlist

### 3. Announcement (`announcement.py`)
**Purpose**: Store ASX company announcements

**Key Fields**:
- `title`: Announcement title
- `pdf_url`: URL to original PDF
- `pdf_local_path`: Local storage path
- `markdown_path`: Converted markdown path
- `is_price_sensitive`: Flag for price-sensitive announcements

**Relationships**:
- Many-to-One with Company
- One-to-One with Analysis
- One-to-Many with StockData

### 4. Subscription (`subscription.py`)
**Purpose**: Manage user subscriptions and billing

**Key Fields**:
- `stripe_customer_id`: Stripe customer reference
- `plan_type`: 'monthly' or 'yearly'
- `status`: 'trialing', 'active', 'canceled', etc.
- `trial_end`: Trial expiration date

**Relationships**:
- One-to-One with User

**Helper Methods**:
- `is_active()`: Check if subscription is active
- `is_trial_active()`: Check if trial is valid

### 5. Analysis (`analysis.py`)
**Purpose**: Store LLM-powered analysis results

**Key Fields**:
- `summary`: Brief summary of announcement
- `sentiment`: 'bullish', 'bearish', or 'neutral'
- `key_insights`: JSON array of insights
- `llm_model`: Model used (e.g., "gemini-1.5-pro")
- `confidence_score`: 0.00 to 1.00

**Relationships**:
- One-to-One with Announcement

### 6. StockData (`stock_data.py`)
**Purpose**: Store stock price and market data

**Key Fields**:
- `price_at_announcement`: Price when announcement was made
- `price_1h_after`: Price 1 hour after
- `price_1d_after`: Price 1 day after
- `performance_1m_pct`: 1-month performance percentage
- `performance_3m_pct`: 3-month performance percentage
- `performance_6m_pct`: 6-month performance percentage

**Relationships**:
- Many-to-One with Announcement
- Many-to-One with Company

### 7. Watchlist (`watchlist.py`)
**Purpose**: Store user company watchlists (future feature)

**Key Fields**:
- `notification_enabled`: Enable/disable notifications

**Relationships**:
- Many-to-One with User
- Many-to-One with Company

**Constraints**:
- Unique constraint on (user_id, company_id)

---

## Database Schema Diagram

```
┌──────────────┐
│    User      │
│──────────────│
│ id (PK)      │
│ email        │
│ oauth_*      │
└──────┬───────┘
       │ 1:1
       ↓
┌──────────────┐
│ Subscription │
│──────────────│
│ user_id (FK) │
│ stripe_*     │
│ status       │
└──────────────┘

┌──────────────┐
│   Company    │
│──────────────│
│ id (PK)      │
│ asx_code     │
│ company_name │
└──────┬───────┘
       │ 1:N
       ↓
┌──────────────────┐
│  Announcement    │
│──────────────────│
│ id (PK)          │
│ company_id (FK)  │
│ title            │
│ pdf_url          │
│ is_price_sens... │
└────┬──────┬──────┘
     │ 1:1  │ 1:N
     ↓      ↓
┌────────┐  ┌────────────┐
│Analysis│  │ StockData  │
│────────│  │────────────│
│summary │  │price_*     │
│sentim..│  │volume      │
└────────┘  └────────────┘

User ←──→ Watchlist ←──→ Company
(Many-to-Many relationship via Watchlist)
```

---

## Usage Examples

### Creating a New Company
```python
from app.models import Company
from app.db import get_db

company = Company(
    asx_code="BHP",
    company_name="BHP Group Limited",
    industry="Mining",
    market_cap=250000000000.00
)
db.add(company)
db.commit()
```

### Creating an Announcement
```python
from app.models import Announcement
from datetime import datetime

announcement = Announcement(
    company_id=company.id,
    asx_code="BHP",
    title="Quarterly Production Report",
    announcement_date=datetime.utcnow(),
    pdf_url="https://asx.com.au/...",
    is_price_sensitive=True
)
db.add(announcement)
db.commit()
```

### Querying with Relationships
```python
# Get all price-sensitive announcements for a company
announcements = db.query(Announcement)\
    .filter(Announcement.asx_code == "BHP")\
    .filter(Announcement.is_price_sensitive == True)\
    .all()

# Get announcement with analysis
announcement = db.query(Announcement)\
    .join(Analysis)\
    .filter(Announcement.id == announcement_id)\
    .first()
```

---

## Model Conventions

### All models include:
- UUID primary keys (for security and scalability)
- Timestamps (`created_at`, updated_at when applicable)
- `to_dict()` method for JSON serialization
- `__repr__()` for debugging
- Proper indexes on frequently queried fields
- Foreign key relationships with CASCADE options

### Column Types:
- `UUID`: Primary keys and foreign keys
- `String`: Short text (emails, codes, names)
- `Text`: Long text (titles, summaries)
- `Numeric`: Decimal numbers (prices, percentages)
- `BigInteger`: Large numbers (volume)
- `Boolean`: Flags
- `DateTime`: Timestamps
- `JSONB`: Flexible JSON data (PostgreSQL specific)

---

## Database Migrations

After modifying models, create a new migration:

```bash
cd backend
uv run alembic revision --autogenerate -m "Description of changes"
uv run alembic upgrade head
```

---

## Testing Models

Example test structure:

```python
def test_create_user():
    user = User(
        email="test@example.com",
        full_name="Test User"
    )
    assert user.email == "test@example.com"
    assert user.is_active == True

def test_subscription_is_active():
    subscription = Subscription(
        status='active'
    )
    assert subscription.is_active() == True
```

---

**Last Updated**: 2025-11-07
