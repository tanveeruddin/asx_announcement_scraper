# ASX Announcements API - Quick Start Guide

## Overview

The ASX Announcements API provides RESTful endpoints for accessing Australian Securities Exchange (ASX) company announcements with AI-powered analysis and stock market data.

**Base URL**: `http://localhost:8000` (development)
**API Version**: `v1`
**API Prefix**: `/api/v1`

## Quick Start

### 1. Start the API Server

```bash
# From backend directory
cd backend

# Make sure dependencies are installed
uv sync

# Make sure PostgreSQL is running
docker-compose up -d postgres

# Run database migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 2. Access Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

**Check API health and database connection**

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-07T01:30:00.000000",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected"
}
```

---

### Announcements

#### List Announcements (Paginated)

```http
GET /api/v1/announcements?page=1&page_size=20
```

**Query Parameters:**
- `page` (int, default: 1): Page number (1-indexed)
- `page_size` (int, default: 20, max: 100): Items per page
- `asx_code` (string, optional): Filter by ASX code (e.g., "BHP")
- `price_sensitive_only` (bool, default: false): Only price-sensitive announcements
- `date_from` (datetime, optional): Filter from date (ISO 8601)
- `date_to` (datetime, optional): Filter to date (ISO 8601)
- `sentiment` (string, optional): Filter by sentiment ("bullish", "bearish", "neutral")

**Example:**
```bash
curl "http://localhost:8000/api/v1/announcements?page=1&page_size=10&price_sensitive_only=true"
```

**Response:**
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "company_id": "...",
      "asx_code": "BHP",
      "title": "Quarterly Production Report",
      "announcement_date": "2025-11-07T09:30:00",
      "pdf_url": "https://www.asx.com.au/asxpdf/...",
      "is_price_sensitive": true,
      "num_pages": 15,
      "file_size_kb": 250,
      "sentiment": "bullish",
      "company": {
        "id": "...",
        "asx_code": "BHP",
        "company_name": "BHP Group Limited",
        "industry": "Mining",
        "market_cap": 228500000000
      },
      "downloaded_at": "2025-11-07T09:35:00",
      "processed_at": "2025-11-07T09:36:00",
      "created_at": "2025-11-07T09:30:00"
    }
  ],
  "metadata": {
    "total": 150,
    "page": 1,
    "page_size": 10,
    "total_pages": 15
  }
}
```

#### Get Single Announcement

```http
GET /api/v1/announcements/{announcement_id}
```

**Parameters:**
- `announcement_id` (UUID): Announcement ID

**Response:** Full announcement details including:
- Company information
- LLM analysis (summary, sentiment, key insights)
- Stock data and market metrics

**Example:**
```bash
curl "http://localhost:8000/api/v1/announcements/123e4567-e89b-12d3-a456-426614174000"
```

#### Advanced Search

```http
POST /api/v1/announcements/search
```

**Request Body:**
```json
{
  "query": "quarterly",
  "asx_codes": ["BHP", "RIO", "FMG"],
  "date_from": "2025-01-01T00:00:00",
  "date_to": "2025-12-31T23:59:59",
  "price_sensitive_only": true,
  "sentiment": "bullish",
  "min_market_cap": 1000000000,
  "max_market_cap": 500000000000,
  "page": 1,
  "page_size": 20,
  "sort_by": "date",
  "sort_order": "desc"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/announcements/search" \
  -H "Content-Type: application/json" \
  -d '{
    "asx_codes": ["BHP"],
    "price_sensitive_only": true,
    "sentiment": "bullish",
    "page": 1,
    "page_size": 10
  }'
```

---

### Companies

#### List All Companies

```http
GET /api/v1/companies?skip=0&limit=100
```

**Query Parameters:**
- `skip` (int, default: 0): Number of companies to skip
- `limit` (int, default: 100, max: 500): Max companies to return

**Example:**
```bash
curl "http://localhost:8000/api/v1/companies?limit=10"
```

**Response:**
```json
[
  {
    "id": "...",
    "asx_code": "BHP",
    "company_name": "BHP Group Limited",
    "industry": "Mining",
    "market_cap": 228500000000,
    "last_updated": "2025-11-07T10:00:00",
    "created_at": "2025-11-01T00:00:00"
  }
]
```

#### Get Company Details

```http
GET /api/v1/companies/{asx_code}
```

**Parameters:**
- `asx_code` (string): ASX stock code (e.g., "BHP", "CBA")

**Example:**
```bash
curl "http://localhost:8000/api/v1/companies/BHP"
```

#### Get Company Announcements

```http
GET /api/v1/companies/{asx_code}/announcements?page=1&page_size=20
```

**Parameters:**
- `asx_code` (string): ASX stock code

**Query Parameters:**
- `page` (int, default: 1): Page number
- `page_size` (int, default: 20, max: 100): Items per page
- `price_sensitive_only` (bool, default: false): Only price-sensitive announcements

**Example:**
```bash
curl "http://localhost:8000/api/v1/companies/BHP/announcements?price_sensitive_only=true"
```

---

## Response Formats

### Success Response

All successful responses return data with appropriate HTTP status codes:
- `200 OK`: Successful GET/POST/PUT
- `201 Created`: Successful resource creation
- `204 No Content`: Successful DELETE

### Error Response

Errors return standard HTTP error codes with details:

```json
{
  "detail": "Announcement with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

Common error codes:
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Database connection error

---

## Data Models

### Announcement
- `id` (UUID): Unique identifier
- `asx_code` (string): ASX stock code
- `title` (string): Announcement title
- `announcement_date` (datetime): When announced
- `pdf_url` (string): Link to PDF
- `is_price_sensitive` (bool): Price sensitivity flag
- `sentiment` (string): LLM-analyzed sentiment

### Company
- `id` (UUID): Unique identifier
- `asx_code` (string): ASX stock code
- `company_name` (string): Full company name
- `industry` (string): Industry sector
- `market_cap` (decimal): Market capitalization

### Analysis
- `summary` (string): 2-3 sentence summary
- `sentiment` (string): bullish/bearish/neutral
- `key_insights` (array): List of key insights
- `confidence_score` (decimal): 0.0-1.0

### Stock Data
- `price_at_announcement` (decimal): Price at announcement time
- `market_cap` (decimal): Market capitalization
- `performance_1m_pct` (decimal): 1-month performance
- `performance_3m_pct` (decimal): 3-month performance
- `performance_6m_pct` (decimal): 6-month performance

---

## Rate Limiting

Currently no rate limiting in development. Production will implement:
- 60 requests/minute per IP
- 1000 requests/hour per user

---

## Development Tips

### Using with Python Requests

```python
import requests

# Get announcements
response = requests.get(
    "http://localhost:8000/api/v1/announcements",
    params={
        "page": 1,
        "page_size": 10,
        "price_sensitive_only": True,
    }
)
data = response.json()

# Search announcements
response = requests.post(
    "http://localhost:8000/api/v1/announcements/search",
    json={
        "asx_codes": ["BHP", "RIO"],
        "sentiment": "bullish",
        "page": 1,
        "page_size": 20,
    }
)
results = response.json()
```

### Using with JavaScript/Fetch

```javascript
// Get announcements
const response = await fetch(
  'http://localhost:8000/api/v1/announcements?page=1&page_size=10'
);
const data = await response.json();

// Search announcements
const searchResponse = await fetch(
  'http://localhost:8000/api/v1/announcements/search',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      asx_codes: ['BHP'],
      price_sensitive_only: true,
      page: 1,
      page_size: 20,
    }),
  }
);
const results = await searchResponse.json();
```

---

## Next Steps

1. **Authentication**: JWT-based authentication coming in next iteration
2. **WebSockets**: Real-time announcement updates
3. **Webhooks**: Subscribe to announcement notifications
4. **Advanced Search**: Full-text search with Elasticsearch

---

## Support

- **Documentation**: http://localhost:8000/docs
- **GitHub**: https://github.com/tanveeruddin/asx_announcement_scraper
- **Issues**: Report bugs via GitHub Issues

---

**Last Updated**: 2025-11-07
**API Version**: 0.1.0
