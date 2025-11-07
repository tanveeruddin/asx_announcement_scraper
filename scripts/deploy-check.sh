#!/bin/bash

# ASX Announcements SaaS - Deployment Health Check Script
# This script verifies that both backend and frontend are deployed correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-}"
FRONTEND_URL="${FRONTEND_URL:-}"

echo "=================================================="
echo "ASX Announcements - Deployment Health Check"
echo "=================================================="
echo ""

# Check if URLs are provided
if [ -z "$BACKEND_URL" ]; then
    echo -e "${YELLOW}⚠️  BACKEND_URL not set. Usage:${NC}"
    echo "   BACKEND_URL=https://your-backend.railway.app FRONTEND_URL=https://your-app.vercel.app ./scripts/deploy-check.sh"
    exit 1
fi

if [ -z "$FRONTEND_URL" ]; then
    echo -e "${YELLOW}⚠️  FRONTEND_URL not set. Usage:${NC}"
    echo "   BACKEND_URL=https://your-backend.railway.app FRONTEND_URL=https://your-app.vercel.app ./scripts/deploy-check.sh"
    exit 1
fi

echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""

# Function to check HTTP status
check_endpoint() {
    local url=$1
    local expected_status=$2
    local description=$3

    echo -n "Checking $description... "

    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $status)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $status, expected $expected_status)"
        return 1
    fi
}

# Function to check JSON response
check_json_endpoint() {
    local url=$1
    local description=$2

    echo -n "Checking $description... "

    response=$(curl -s "$url" 2>/dev/null || echo "{}")

    if [ -n "$response" ] && [ "$response" != "{}" ]; then
        echo -e "${GREEN}✓ OK${NC}"
        echo "   Response: $(echo $response | jq -c . 2>/dev/null || echo $response | head -c 100)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Empty or invalid response)"
        return 1
    fi
}

# Backend Health Checks
echo "=================================================="
echo "BACKEND HEALTH CHECKS"
echo "=================================================="
echo ""

check_endpoint "$BACKEND_URL/health" "200" "Health endpoint"
check_json_endpoint "$BACKEND_URL/health" "Health endpoint JSON"
echo ""

check_endpoint "$BACKEND_URL/docs" "200" "API documentation"
echo ""

check_json_endpoint "$BACKEND_URL/api/v1/announcements?page=1&page_size=5" "Announcements API"
echo ""

check_json_endpoint "$BACKEND_URL/api/v1/companies" "Companies API"
echo ""

# Frontend Health Checks
echo "=================================================="
echo "FRONTEND HEALTH CHECKS"
echo "=================================================="
echo ""

check_endpoint "$FRONTEND_URL" "200" "Homepage"
echo ""

check_endpoint "$FRONTEND_URL/announcements" "200" "Announcements page"
echo ""

# CORS Check
echo "=================================================="
echo "CORS CONFIGURATION CHECK"
echo "=================================================="
echo ""

echo -n "Checking CORS from frontend to backend... "
cors_headers=$(curl -s -H "Origin: $FRONTEND_URL" -H "Access-Control-Request-Method: GET" -I "$BACKEND_URL/api/v1/announcements" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")

if [ -n "$cors_headers" ]; then
    echo -e "${GREEN}✓ OK${NC}"
    echo "   Headers: $cors_headers"
else
    echo -e "${RED}✗ FAILED${NC}"
    echo -e "${YELLOW}   ⚠️  CORS headers not found. Update CORS_ORIGINS in Railway backend.${NC}"
fi
echo ""

# SSL Certificate Check
echo "=================================================="
echo "SSL CERTIFICATE CHECK"
echo "=================================================="
echo ""

echo -n "Checking backend SSL certificate... "
if echo | openssl s_client -connect "$(echo $BACKEND_URL | sed 's~https://~~'):443" -servername "$(echo $BACKEND_URL | sed 's~https://~~')" 2>/dev/null | grep -q "Verify return code: 0"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (SSL verification failed or not HTTPS)"
fi

echo -n "Checking frontend SSL certificate... "
if echo | openssl s_client -connect "$(echo $FRONTEND_URL | sed 's~https://~~'):443" -servername "$(echo $FRONTEND_URL | sed 's~https://~~')" 2>/dev/null | grep -q "Verify return code: 0"; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠️  WARNING${NC} (SSL verification failed or not HTTPS)"
fi
echo ""

# Performance Check
echo "=================================================="
echo "PERFORMANCE CHECK"
echo "=================================================="
echo ""

echo -n "Backend API response time... "
backend_time=$(curl -o /dev/null -s -w "%{time_total}" "$BACKEND_URL/health")
echo "${backend_time}s"
if (( $(echo "$backend_time < 1.0" | bc -l) )); then
    echo -e "   ${GREEN}✓ Good performance${NC} (< 1s)"
elif (( $(echo "$backend_time < 3.0" | bc -l) )); then
    echo -e "   ${YELLOW}⚠️  Acceptable performance${NC} (1-3s)"
else
    echo -e "   ${RED}✗ Slow performance${NC} (> 3s)"
fi
echo ""

echo -n "Frontend page load time... "
frontend_time=$(curl -o /dev/null -s -w "%{time_total}" "$FRONTEND_URL")
echo "${frontend_time}s"
if (( $(echo "$frontend_time < 2.0" | bc -l) )); then
    echo -e "   ${GREEN}✓ Good performance${NC} (< 2s)"
elif (( $(echo "$frontend_time < 5.0" | bc -l) )); then
    echo -e "   ${YELLOW}⚠️  Acceptable performance${NC} (2-5s)"
else
    echo -e "   ${RED}✗ Slow performance${NC} (> 5s)"
fi
echo ""

# Database Check
echo "=================================================="
echo "DATABASE CHECK"
echo "=================================================="
echo ""

echo -n "Checking database connection via health endpoint... "
health_response=$(curl -s "$BACKEND_URL/health" 2>/dev/null || echo "{}")
db_status=$(echo $health_response | jq -r '.database' 2>/dev/null || echo "unknown")

if [ "$db_status" = "connected" ]; then
    echo -e "${GREEN}✓ OK${NC} (Database connected)"
else
    echo -e "${RED}✗ FAILED${NC} (Database status: $db_status)"
fi
echo ""

# Final Summary
echo "=================================================="
echo "DEPLOYMENT SUMMARY"
echo "=================================================="
echo ""
echo -e "${GREEN}✓ Deployment health check complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Monitor logs in Railway and Vercel dashboards"
echo "2. Test full user flow: browse announcements → view details"
echo "3. Verify scheduler is running (check Railway worker logs)"
echo "4. Setup monitoring (Sentry, uptime checks)"
echo ""
echo "For detailed deployment guide, see: DEPLOYMENT.md"
echo ""
