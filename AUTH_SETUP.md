# Authentication Setup Guide

Complete guide for setting up JWT authentication and Google OAuth integration for the ASX Announcements SaaS application.

## Table of Contents

1. [Overview](#overview)
2. [Google OAuth Setup](#google-oauth-setup)
3. [Backend Configuration](#backend-configuration)
4. [Frontend Configuration](#frontend-configuration)
5. [Testing Authentication](#testing-authentication)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The application uses a hybrid authentication system:

- **Google OAuth 2.0**: For user sign-in (frontend)
- **JWT Tokens**: For API authentication (backend)

### Authentication Flow

1. User clicks "Sign in with Google" on frontend
2. Google OAuth popup appears
3. User authenticates with Google
4. Frontend receives Google ID token
5. Frontend sends ID token to backend `/api/v1/auth/google`
6. Backend verifies Google token
7. Backend creates/updates user in database
8. Backend returns JWT access + refresh tokens
9. Frontend stores tokens and user data
10. Frontend uses JWT access token for API requests

### Token Lifecycle

- **Access Token**: 60 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Refresh Token**: 7 days (configurable via `JWT_REFRESH_TOKEN_EXPIRE_DAYS`)

---

## Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Enter project name: `ASX Announcements`
4. Click "Create"

### Step 2: Enable Google+ API

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for "Google+ API"
3. Click on it and click "Enable"

### Step 3: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: **External**
   - App name: `ASX Announcements`
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Add `email` and `profile` (default scopes)
   - Click "Save and Continue"
   - Test users: Add your Gmail for testing
   - Click "Save and Continue"

4. Create OAuth Client ID:
   - Application type: **Web application**
   - Name: `ASX Announcements Web`
   - Authorized JavaScript origins:
     - `http://localhost:3000` (development)
     - `https://your-app.vercel.app` (production)
   - Authorized redirect URIs:
     - `http://localhost:3000` (development)
     - `https://your-app.vercel.app` (production)
   - Click "Create"

5. Copy your credentials:
   - **Client ID**: `123456789-abc123.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-abc123xyz...`

**Important**: Never commit these credentials to version control!

---

## Backend Configuration

### Step 1: Update Environment Variables

Edit `backend/.env`:

```bash
# Authentication & Security
JWT_SECRET_KEY=<generate_random_32_char_string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google OAuth Configuration
GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz...
```

**Generate JWT Secret Key**:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or use the provided script
python scripts/generate-secrets.py
```

### Step 2: Install Dependencies

```bash
cd backend
uv sync
```

This will install the following authentication dependencies:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing (for future features)
- `google-auth` - Google ID token verification

### Step 3: Run Database Migrations

Authentication uses the existing `users` table. Ensure migrations are up to date:

```bash
uv run alembic upgrade head
```

### Step 4: Start Backend Server

```bash
uv run uvicorn app.main:app --reload
```

Backend will be available at: `http://localhost:8000`

### Step 5: Verify Backend Endpoints

Check API documentation at `http://localhost:8000/docs`

Authentication endpoints:
- `POST /api/v1/auth/google` - Google OAuth login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/subscription` - Get subscription status
- `POST /api/v1/auth/logout` - Logout

---

## Frontend Configuration

### Step 1: Update Environment Variables

Edit `frontend/.env.local` (create if doesn't exist):

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Google OAuth Configuration
NEXT_PUBLIC_GOOGLE_CLIENT_ID=123456789-abc123.apps.googleusercontent.com
```

**Important**: Only the `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is needed on frontend. The client secret stays on backend only.

### Step 2: Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- `@react-oauth/google` - Google OAuth React components
- Other dependencies from package.json

### Step 3: Start Frontend Server

```bash
npm run dev
```

Frontend will be available at: `http://localhost:3000`

---

## Testing Authentication

### Manual Testing

1. **Navigate to Login Page**
   ```
   http://localhost:3000/login
   ```

2. **Click "Sign in with Google"**
   - Google OAuth popup should appear
   - Sign in with your Google account (must be added as test user)

3. **After Successful Login**
   - You should be redirected to `/announcements`
   - Header should show your name/email with logout button
   - Check browser localStorage for tokens:
     ```javascript
     localStorage.getItem('access_token')
     localStorage.getItem('refresh_token')
     localStorage.getItem('user')
     ```

4. **Test Protected Routes**
   - Navigate to `/announcements` - should work
   - Logout and try `/announcements` again - should redirect to login

5. **Test Token Refresh**
   - Wait for access token to expire (default 60 minutes)
   - Make an API request
   - Frontend should automatically refresh token using refresh token

### API Testing with cURL

1. **Login with Google (get token from browser first)**

   After logging in via the UI, get your access token from localStorage and test API endpoints:

   ```bash
   # Get current user info
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/v1/auth/me

   # Get subscription status
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/v1/auth/subscription

   # Test protected announcement endpoint
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     http://localhost:8000/api/v1/announcements
   ```

2. **Test Token Refresh**

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
   ```

---

## Troubleshooting

### Backend Issues

#### Issue: "Invalid Google token"

**Symptoms**: Error when logging in

**Solutions**:
1. Verify `GOOGLE_CLIENT_ID` matches the one in Google Cloud Console
2. Verify `GOOGLE_CLIENT_SECRET` is correct
3. Check Google OAuth consent screen is configured
4. Ensure email and profile scopes are enabled
5. Check backend logs for detailed error:
   ```bash
   # View backend logs
   uv run uvicorn app.main:app --reload --log-level debug
   ```

#### Issue: "User not found" after login

**Symptoms**: User created but token verification fails

**Solutions**:
1. Check database connection
2. Verify `users` table exists:
   ```bash
   docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements -c "\dt"
   ```
3. Check user was created:
   ```bash
   docker exec -it asx-announcements-db psql -U asx_user -d asx_announcements -c "SELECT * FROM users;"
   ```

#### Issue: JWT token verification fails

**Symptoms**: "Invalid or expired token" errors

**Solutions**:
1. Verify `JWT_SECRET_KEY` is set in `.env`
2. Ensure `JWT_SECRET_KEY` is the same across requests (not regenerating)
3. Check token hasn't expired (default 60 minutes)
4. Use refresh token endpoint to get new access token

### Frontend Issues

#### Issue: "Google Client ID not configured"

**Symptoms**: Error message on login page

**Solutions**:
1. Verify `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set in `.env.local`
2. Restart Next.js dev server after adding env var:
   ```bash
   # Stop server (Ctrl+C), then:
   npm run dev
   ```

#### Issue: Google OAuth popup doesn't appear

**Symptoms**: Nothing happens when clicking "Sign in with Google"

**Solutions**:
1. Check browser console for errors
2. Verify Google Client ID is correct
3. Check popup blockers are disabled
4. Try in incognito mode
5. Clear browser cache

#### Issue: "Failed to fetch" or CORS errors

**Symptoms**: Network errors when calling backend

**Solutions**:
1. Verify backend is running on `http://localhost:8000`
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Verify backend CORS settings in `backend/app/config.py`:
   ```python
   CORS_ORIGINS=http://localhost:3000,http://localhost:3001
   ```

#### Issue: User redirected to login after successful authentication

**Symptoms**: Login succeeds but immediately redirected back to login

**Solutions**:
1. Check browser localStorage for tokens
2. Verify `AuthContext` is wrapping app in `layout.tsx`
3. Check browser console for JavaScript errors
4. Ensure tokens are being saved to localStorage

### Database Issues

#### Issue: "Subscription not found" for new users

**Symptoms**: User can login but no trial subscription

**Solutions**:
1. Check backend logs during user creation
2. Verify `subscriptions` table exists
3. Check `FREE_TRIAL_DAYS` is set in backend `.env`
4. Manually create trial subscription:
   ```sql
   INSERT INTO subscriptions (user_id, status, trial_start, trial_end, current_period_start, current_period_end)
   VALUES (
     'USER_ID_HERE',
     'trialing',
     NOW(),
     NOW() + INTERVAL '7 days',
     NOW(),
     NOW() + INTERVAL '7 days'
   );
   ```

---

## Security Best Practices

### Production Deployment

1. **Use HTTPS Only**
   - Never send tokens over HTTP in production
   - Configure SSL certificates on both frontend and backend

2. **Environment Variables**
   - Never commit `.env` files to version control
   - Use Railway/Vercel environment variable dashboards
   - Rotate secrets regularly (every 90 days)

3. **Token Security**
   - Use `httpOnly` cookies for production (instead of localStorage)
   - Implement token blacklisting for logout
   - Set short expiration times (15-60 minutes for access tokens)

4. **OAuth Configuration**
   - Restrict authorized origins to production domain only
   - Use different OAuth clients for dev/staging/production
   - Monitor OAuth console for suspicious activity

5. **Rate Limiting**
   - Implement rate limiting on auth endpoints
   - Limit failed login attempts per IP
   - Use CAPTCHA for suspicious activity

---

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Next.js Authentication](https://nextjs.org/docs/authentication)

---

**Last Updated**: 2025-11-07
**Version**: 1.0
**Status**: Authentication Ready ✅
