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
  signInWithLinkedIn: () => Promise<{ error: Error | null }>;
  signOut: () => Promise<void>;
  refreshAuthToken: () => Promise<boolean>;
  refreshUser: () => Promise<void>;
  forceAuthRefresh: () => Promise<void>;
  updateUser: (userData: UserUpdate) => Promise<{ error: Error | null }>;
  deleteAccount: () => Promise<{ error: Error | null }>;
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

  const signInWithLinkedIn = useCallback(async () => {
    try {
      const redirectUrl = `${getFrontendBaseUrl()}/auth/callback`;
      const response = await apiClient.signInWithLinkedIn(redirectUrl);

      // Redirect to Google OAuth URL
      window.location.href = response.url;

      return { error: null };
    } catch (error) {
      console.error("LinkedIn sign in failed:", error);
      return {
        error:
          error instanceof ApiError
            ? new Error(error.message)
            : new Error("LinkedIn sign in failed"),
      };
    }
  }, []);

  const signOut = useCallback(async () => {
    try {
      await apiClient.signOut();
    } catch (error) {
      console.error("Sign out API call failed:", error);
      // Continue with local cleanup even if API call fails
    }

    // Clear local state and tokens
    clearTokens();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
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
  }, []);

  const forceAuthRefresh = useCallback(async () => {
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
  }, []);

  const deleteAccount = useCallback(async () => {
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
  }, [signOut]);

  const updateUser = useCallback(
    async (userData: UserUpdate) => {
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
    },
    [user]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        signInWithLinkedIn,
        signOut,
        refreshAuthToken,
        refreshUser,
        forceAuthRefresh,
        updateUser,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
