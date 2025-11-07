/**
 * Authentication utilities and API client for auth endpoints
 */

import { api } from './api';

export interface User {
  id: string;
  email: string;
  full_name?: string;
  oauth_provider?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface MeResponse {
  user: User;
  has_subscription: boolean;
  subscription_status?: string;
  trial_ends_at?: string;
}

export interface SubscriptionStatus {
  has_subscription: boolean;
  status?: string;
  plan_type?: string;
  trial_start?: string;
  trial_end?: string;
  current_period_start?: string;
  current_period_end?: string;
  canceled_at?: string;
}

/**
 * Authenticate with Google OAuth ID token
 */
export async function loginWithGoogle(idToken: string): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/google', {
    id_token: idToken,
  });
  return response.data;
}

/**
 * Refresh access token using refresh token
 */
export async function refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>('/auth/refresh', {
    refresh_token: refreshToken,
  });
  return response.data;
}

/**
 * Get current user information
 */
export async function getCurrentUser(accessToken: string): Promise<MeResponse> {
  const response = await api.get<MeResponse>('/auth/me', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return response.data;
}

/**
 * Get subscription status
 */
export async function getSubscriptionStatus(accessToken: string): Promise<SubscriptionStatus> {
  const response = await api.get<SubscriptionStatus>('/auth/subscription', {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
  return response.data;
}

/**
 * Logout (client-side token removal)
 */
export async function logout(accessToken?: string): Promise<void> {
  if (accessToken) {
    try {
      await api.post('/auth/logout', {}, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });
    } catch (error) {
      // Ignore errors on logout
      console.error('Logout error:', error);
    }
  }

  // Clear tokens from localStorage
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
}

/**
 * Save tokens to localStorage
 */
export function saveTokens(tokenResponse: TokenResponse): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', tokenResponse.access_token);
    localStorage.setItem('refresh_token', tokenResponse.refresh_token);
  }
}

/**
 * Get access token from localStorage
 */
export function getAccessToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
}

/**
 * Get refresh token from localStorage
 */
export function getRefreshToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('refresh_token');
  }
  return null;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

/**
 * Save user to localStorage
 */
export function saveUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('user', JSON.stringify(user));
  }
}

/**
 * Get user from localStorage
 */
export function getUser(): User | null {
  if (typeof window !== 'undefined') {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
  }
  return null;
}
