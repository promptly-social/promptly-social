import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { apiClient, ApiError } from "@/lib/auth-api";
import {
  getStoredToken,
  getStoredRefreshToken,
  setTokens,
  clearTokens,
  isTokenExpired,
} from "@/lib/api-interceptor";
import { getFrontendBaseUrl } from "@/lib/utils";
import type { User, UserUpdate } from "@/types/auth";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  pendingEmailVerification: string | null; // Email waiting for verification
  signUp: (
    email: string,
    password: string,
    fullName?: string
  ) => Promise<{ error: Error | null; needsVerification?: boolean }>;
  signIn: (email: string, password: string) => Promise<{ error: Error | null }>;
  signInWithGoogle: () => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  refreshAuthToken: () => Promise<boolean>;
  refreshUser: () => Promise<void>;
  forceAuthRefresh: () => Promise<void>;
  updateUser: (userData: UserUpdate) => Promise<{ error: Error | null }>;
  deleteAccount: () => Promise<{ error: Error | null }>;
  clearPendingVerification: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [pendingEmailVerification, setPendingEmailVerification] = useState<
    string | null
  >(null);

  const refreshAuthToken = useCallback(async (): Promise<boolean> => {
    const refreshToken = getStoredRefreshToken();
    if (!refreshToken) {
      return false;
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
      console.error("Token refresh failed:", error);
      return false;
    }
  }, []);

  // Initialize auth state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      const token = getStoredToken();

      if (!token) {
        setLoading(false);
        return;
      }

      // Check if token is expired
      if (isTokenExpired()) {
        const refreshed = await refreshAuthToken();
        if (!refreshed) {
          clearTokens();
          setLoading(false);
          return;
        }
      }

      // Fetch current user
      try {
        const currentUser = await apiClient.getCurrentUser();
        setUser(currentUser);
      } catch (error) {
        console.error("Failed to fetch current user:", error);
        // Only clear tokens if it's an auth error, not a network error
        if (
          error instanceof ApiError &&
          (error.status === 401 || error.status === 403)
        ) {
          console.log("Auth error detected, clearing tokens");
          clearTokens();
          setUser(null);
        }
      }

      setLoading(false);
    };

    initializeAuth();
  }, [refreshAuthToken]);

  const signUp = async (email: string, password: string, fullName?: string) => {
    try {
      const response = await apiClient.signUp({
        email,
        password,
        confirm_password: password,
        full_name: fullName,
      });

      // Check if tokens were returned (user is verified)
      if (response.tokens && response.tokens.access_token) {
        // Store tokens and set user (OAuth users)
        setTokens(
          response.tokens.access_token,
          response.tokens.refresh_token,
          response.tokens.expires_in
        );
        setUser(response.user);
        return { error: null, needsVerification: false };
      } else {
        // No tokens returned - user needs email verification
        setPendingEmailVerification(email);
        return { error: null, needsVerification: true };
      }
    } catch (error) {
      console.error("Sign up failed:", error);
      return {
        error:
          error instanceof ApiError
            ? new Error(error.message)
            : new Error("Sign up failed"),
        needsVerification: false,
      };
    }
  };

  const signIn = async (email: string, password: string) => {
    try {
      const response = await apiClient.signIn({ email, password });

      console.log("Sign in response:", response);

      // Store tokens
      setTokens(
        response.tokens.access_token,
        response.tokens.refresh_token,
        response.tokens.expires_in
      );

      // Set user
      setUser(response.user);
      console.log("User set in context:", response.user);

      return { error: null };
    } catch (error) {
      console.error("Sign in failed:", error);
      return {
        error:
          error instanceof ApiError
            ? new Error(error.message)
            : new Error("Sign in failed"),
      };
    }
  };

  const signInWithGoogle = async () => {
    try {
      const redirectUrl = `${getFrontendBaseUrl()}/new-content`;
      const response = await apiClient.signInWithGoogle(redirectUrl);

      // Redirect to Google OAuth URL
      window.location.href = response.url;

      return { error: null };
    } catch (error) {
      console.error("Google sign in failed:", error);
      return {
        error:
          error instanceof ApiError
            ? new Error(error.message)
            : new Error("Google sign in failed"),
      };
    }
  };

  const signOut = async () => {
    try {
      await apiClient.signOut();
    } catch (error) {
      console.error("Sign out API call failed:", error);
      // Continue with local cleanup even if API call fails
    }

    // Clear local state and tokens
    clearTokens();
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
      console.log("User refreshed in context:", currentUser);
    } catch (error) {
      console.error("Failed to refresh user:", error);
      // If this fails, the user might still be valid, just network issues
      // Don't clear tokens unless it's an auth error
      if (
        error instanceof ApiError &&
        (error.status === 401 || error.status === 403)
      ) {
        clearTokens();
        setUser(null);
      }
    }
  };

  const forceAuthRefresh = async () => {
    try {
      const token = getStoredToken();
      if (token) {
        const currentUser = await apiClient.getCurrentUser();
        setUser(currentUser);
      }
    } catch (error) {
      console.error("Failed to force auth refresh:", error);
      if (
        error instanceof ApiError &&
        (error.status === 401 || error.status === 403)
      ) {
        clearTokens();
        setUser(null);
      }
    }
  };

  const deleteAccount = async () => {
    try {
      await apiClient.deleteAccount();
      // After successful deletion, sign the user out
      await signOut();
      return { error: null };
    } catch (error) {
      console.error("Delete account failed:", error);
      return {
        error:
          error instanceof ApiError
            ? new Error(error.message)
            : new Error("Failed to delete account"),
      };
    }
  };

  const updateUser = async (userData: UserUpdate) => {
    if (!user) {
      return { error: new Error("User not authenticated") };
    }
    try {
      const updatedUser = await apiClient.updateUser(userData);
      setUser(updatedUser);
      return { error: null };
    } catch (error) {
      console.error("Failed to update user:", error);
      return {
        error:
          error instanceof ApiError
            ? new Error(error.message)
            : new Error("Failed to update user"),
      };
    }
  };

  const clearPendingVerification = () => {
    setPendingEmailVerification(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        pendingEmailVerification,
        signUp,
        signIn,
        signInWithGoogle,
        signOut,
        refreshAuthToken,
        refreshUser,
        forceAuthRefresh,
        updateUser,
        deleteAccount,
        clearPendingVerification,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
