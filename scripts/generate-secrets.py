#!/usr/bin/env python3
"""
ASX Announcements SaaS - Secret Key Generator

Generates secure random keys for deployment environment variables:
- SECRET_KEY (Flask/FastAPI app secret)
- NEXTAUTH_SECRET (NextAuth.js secret)
- JWT_SECRET_KEY (JWT token signing)
"""

import secrets
import string

def generate_secret(length=32):
    """Generate a URL-safe random secret key."""
    return secrets.token_urlsafe(length)

def generate_hex_secret(length=32):
    """Generate a hexadecimal random secret key."""
    return secrets.token_hex(length)

def generate_alphanumeric(length=32):
    """Generate a random alphanumeric secret key."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("=" * 60)
    print("ASX Announcements SaaS - Secret Key Generator")
    print("=" * 60)
    print()

    print("Copy these values to your Railway and Vercel environment variables:")
    print()

    print("-" * 60)
    print("Backend (Railway)")
    print("-" * 60)
    print()

    print("SECRET_KEY (FastAPI application secret):")
    print(f"  {generate_secret(32)}")
    print()

    print("JWT_SECRET_KEY (JWT token signing):")
    print(f"  {generate_secret(32)}")
    print()

    print("-" * 60)
    print("Frontend (Vercel)")
    print("-" * 60)
    print()

    print("NEXTAUTH_SECRET (NextAuth.js secret):")
    print(f"  {generate_secret(32)}")
    print()

    print("-" * 60)
    print("Optional: Additional Secrets")
    print("-" * 60)
    print()

    print("Database encryption key (if needed):")
    print(f"  {generate_hex_secret(32)}")
    print()

    print("API key (for internal services):")
    print(f"  {generate_alphanumeric(40)}")
    print()

    print("=" * 60)
    print("Security Best Practices:")
    print("=" * 60)
    print()
    print("✓ Never commit secrets to version control")
    print("✓ Use different secrets for dev/staging/production")
    print("✓ Rotate secrets periodically (every 90 days)")
    print("✓ Store secrets in Railway/Vercel dashboards only")
    print("✓ Use strong, unique secrets for each environment")
    print()

    print("=" * 60)
    print("How to Use:")
    print("=" * 60)
    print()
    print("1. Copy SECRET_KEY to Railway:")
    print("   Railway Dashboard → Service → Variables → Add Variable")
    print()
    print("2. Copy NEXTAUTH_SECRET to Vercel:")
    print("   Vercel Dashboard → Settings → Environment Variables")
    print()
    print("3. Keep a secure backup of all secrets (use password manager)")
    print()

if __name__ == "__main__":
    main()
