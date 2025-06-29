// API interceptor for automatic token refresh and error handling
import { apiClient } from "./auth-api";

// Token management utilities
const TOKEN_STORAGE_KEY = "access_token";
const REFRESH_TOKEN_STORAGE_KEY = "refresh_token";
const TOKEN_EXPIRY_KEY = "token_expiry";

export const getStoredToken = () => localStorage.getItem(TOKEN_STORAGE_KEY);
export const getStoredRefreshToken = () =>
  localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
export const getTokenExpiry = () => {
  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
  return expiry ? parseInt(expiry, 10) : 0;
};

export const setTokens = (
  accessToken: string,
  refreshToken: string,
  expiresIn: number
) => {
  localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refreshToken);
  localStorage.setItem(
    TOKEN_EXPIRY_KEY,
    (Date.now() + expiresIn * 1000).toString()
  );
};

export const clearTokens = () => {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
};

export const isTokenExpired = () => {
  const expiry = getTokenExpiry();
  return Date.now() >= expiry - 60000; // Refresh 1 minute before expiry
};

// Automatic token refresh function
export const refreshTokenIfNeeded = async (): Promise<boolean> => {
  if (!isTokenExpired()) {
    return true; // Token is still valid
  }

  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) {
    return false; // No refresh token available
  }

  try {
    const tokenResponse = await apiClient.refreshToken(refreshToken);
    setTokens(
      tokenResponse.access_token,
      tokenResponse.refresh_token,
      tokenResponse.expires_in
    );
    return true;
  } catch (error) {
    console.error("Automatic token refresh failed:", error);
    clearTokens();
    return false;
  }
};

// Request interceptor to add auth header and handle token refresh
export const makeAuthenticatedRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  // Try to refresh token if needed
  const tokenValid = await refreshTokenIfNeeded();

  if (!tokenValid && !endpoint.includes("/auth/")) {
    throw new Error("Authentication required");
  }

  return apiClient.request<T>(endpoint, options);
};

// Utility function to handle logout on 401 errors
export const handleAuthError = (error: Error) => {
  if (error.message.includes("401") || error.message.includes("Unauthorized")) {
    clearTokens();
    // Redirect to login page
    window.location.href = "/login";
  }
};
