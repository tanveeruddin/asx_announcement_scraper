'use client';

/**
 * Authentication context for managing user authentication state
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  User,
  TokenResponse,
  MeResponse,
  loginWithGoogle,
  getCurrentUser,
  logout as logoutApi,
  saveTokens,
  getAccessToken,
  getRefreshToken,
  saveUser,
  getUser as getStoredUser,
  refreshAccessToken,
} from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasSubscription: boolean;
  subscriptionStatus: string | null;
  login: (idToken: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [hasSubscription, setHasSubscription] = useState(false);
  const [subscriptionStatus, setSubscriptionStatus] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage and verify on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const accessToken = getAccessToken();
      const storedUser = getStoredUser();

      if (accessToken && storedUser) {
        try {
          // Verify token is still valid by fetching current user
          const meResponse = await getCurrentUser(accessToken);
          setUser(meResponse.user);
          setHasSubscription(meResponse.has_subscription);
          setSubscriptionStatus(meResponse.subscription_status || null);
          saveUser(meResponse.user);
        } catch (error) {
          // Token invalid, try to refresh
          const refreshToken = getRefreshToken();
          if (refreshToken) {
            try {
              const tokenResponse = await refreshAccessToken(refreshToken);
              saveTokens(tokenResponse);

              const meResponse = await getCurrentUser(tokenResponse.access_token);
              setUser(meResponse.user);
              setHasSubscription(meResponse.has_subscription);
              setSubscriptionStatus(meResponse.subscription_status || null);
              saveUser(meResponse.user);
            } catch (refreshError) {
              // Refresh failed, clear auth
              await logoutApi();
              setUser(null);
              setHasSubscription(false);
              setSubscriptionStatus(null);
            }
          } else {
            // No refresh token, clear auth
            await logoutApi();
            setUser(null);
            setHasSubscription(false);
            setSubscriptionStatus(null);
          }
        }
      }

      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (idToken: string) => {
    try {
      // Exchange Google ID token for our JWT tokens
      const tokenResponse: TokenResponse = await loginWithGoogle(idToken);
      saveTokens(tokenResponse);

      // Fetch user data
      const meResponse: MeResponse = await getCurrentUser(tokenResponse.access_token);
      setUser(meResponse.user);
      setHasSubscription(meResponse.has_subscription);
      setSubscriptionStatus(meResponse.subscription_status || null);
      saveUser(meResponse.user);
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = async () => {
    const accessToken = getAccessToken();
    await logoutApi(accessToken || undefined);
    setUser(null);
    setHasSubscription(false);
    setSubscriptionStatus(null);
  };

  const refreshUser = async () => {
    const accessToken = getAccessToken();
    if (!accessToken) return;

    try {
      const meResponse = await getCurrentUser(accessToken);
      setUser(meResponse.user);
      setHasSubscription(meResponse.has_subscription);
      setSubscriptionStatus(meResponse.subscription_status || null);
      saveUser(meResponse.user);
    } catch (error) {
      console.error('Refresh user error:', error);
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: user !== null,
    isLoading,
    hasSubscription,
    subscriptionStatus,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
