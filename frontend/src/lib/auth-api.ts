// API client for backend authentication services
import type {
  User,
  AuthResponse,
  TokenResponse,
  UserCreate,
  UserLogin,
  UserUpdate,
  SuccessResponse,
  LinkedInAuthRequest,
} from "@/types/auth";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface ApiResponse<T = unknown> {
  data?: T;
  error?: string;
  message?: string;
}

class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = `${baseUrl}/api/v1`;
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  private isRefreshing = false;
  private refreshSubscribers: ((token: string) => void)[] = [];

  private async handleResponse<T>(
    response: Response,
    requestInfo: { url: string; options: RequestInit }
  ): Promise<T> {
    const contentType = response.headers.get("content-type");

    // Short-circuit for 204 / 205 No-Content
    if (response.status === 204 || response.status === 205) {
      return undefined as T;
    }

    const isJson = contentType?.includes("application/json");

    let data;
    if (isJson) {
      // If body is empty but content-type says json, guard against parse error
      const text = await response.text();
      data = text.length ? JSON.parse(text) : undefined;
    } else {
      data = await response.text();
    }

    // If unauthorized and not a refresh token request, try to refresh the token
    if (response.status === 401 && !response.url.includes("auth/refresh")) {
      return this.handleUnauthorized(requestInfo) as Promise<T>;
    }

    if (!response.ok) {
      let errorMessage =
        data?.detail || data?.error || `HTTP ${response.status}`;

      // Handle validation errors with details
      if (
        data?.details &&
        Array.isArray(data.details) &&
        data.details.length > 0
      ) {
        // Extract the most user-friendly error message
        const validationErrors = data.details
          .map((detail: unknown) => {
            // Try to get the most readable error message
            const detailObj = detail as Record<string, unknown>;
            const ctx = detailObj.ctx as Record<string, unknown> | undefined;
            return ctx?.error || detailObj.msg || detailObj.type;
          })
          .filter(Boolean) as string[];

        if (validationErrors.length > 0) {
          errorMessage = validationErrors.join("; ");
        }
      }

      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  }

  private async handleUnauthorized<T>(requestInfo: {
    url: string;
    options: RequestInit;
  }): Promise<T> {
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
      // No refresh token available, redirect to login
      this.redirectToLogin();
      throw new Error("No refresh token available");
    }

    // If we're already refreshing the token, add this request to the queue
    if (this.isRefreshing) {
      return new Promise((resolve, reject) => {
        this.refreshSubscribers.push((newToken: string) => {
          // Update the token in the original request
          const headers = new Headers(requestInfo.options.headers);
          headers.set("Authorization", `Bearer ${newToken}`);

          // Retry the original request with the new token
          this.request<T>(requestInfo.url, {
            ...requestInfo.options,
            headers,
          })
            .then(resolve)
            .catch(reject);
        });
      });
    }

    this.isRefreshing = true;

    try {
      // Try to refresh the token
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      const data = await response.json();

      if (!response.ok) {
        // If refresh fails, clear tokens and redirect to login
        this.clearAuthTokens();
        this.redirectToLogin();
        throw new Error("Session expired. Please log in again.");
      }

      // Update tokens in storage
      localStorage.setItem("access_token", data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token);
      }

      // Update the token in the original request
      const headers = new Headers(requestInfo.options.headers);
      headers.set("Authorization", `Bearer ${data.access_token}`);

      // Retry the original request with the new token
      const retryResponse = await fetch(requestInfo.url, {
        ...requestInfo.options,
        headers,
      });

      // Process all queued requests with the new token
      this.processRefreshQueue(data.access_token);

      // Return the response of the retried request
      return this.handleResponse<T>(retryResponse, requestInfo);
    } catch (error) {
      this.clearAuthTokens();
      this.redirectToLogin();
      throw error;
    } finally {
      this.isRefreshing = false;
    }
  }

  private processRefreshQueue(newToken: string) {
    // Process all queued requests with the new token
    this.refreshSubscribers.forEach((callback) => callback(newToken));
    this.refreshSubscribers = [];
  }

  private clearAuthTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  private redirectToLogin() {
    // Clear any existing tokens
    this.clearAuthTokens();

    // Redirect to login page
    const loginUrl = "/login";
    if (window.location.pathname !== loginUrl) {
      window.location.href = loginUrl;
    }
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: this.getAuthHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      return await this.handleResponse<T>(response, { url, options: config });
    } catch (error) {
      if (error instanceof ApiError) {
        // If we get a 401 and it's not a login/refresh request, try to refresh the token
        if (
          error.status === 401 &&
          !endpoint.includes("auth/login") &&
          !endpoint.includes("auth/refresh")
        ) {
          // This will be handled by the interceptor
          throw error;
        }
        throw error;
      }
      throw new ApiError(
        error instanceof Error ? error.message : "An unknown error occurred"
      );
    }
  }

  // Authentication endpoints
  async signUp(
    userData: Omit<UserCreate, "preferred_language" | "timezone">
  ): Promise<AuthResponse> {
    return this.request<AuthResponse>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(userData),
    });
  }

  async signIn(credentials: UserLogin): Promise<AuthResponse> {
    return this.request<AuthResponse>("/auth/signin", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
  }

  async signInWithLinkedIn(
    redirectTo?: string
  ): Promise<{ url: string; message: string }> {
    const payload: Partial<LinkedInAuthRequest> = {};
    if (redirectTo) {
      payload.redirect_to = redirectTo;
    }
    return this.request<{ url: string; message: string }>(
      "/auth/signin/linkedin",
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    );
  }

  async signOut(): Promise<SuccessResponse> {
    return this.request<SuccessResponse>("/auth/signout", { method: "POST" });
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return this.request<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  async updateUser(userData: UserUpdate): Promise<User> {
    return this.request<User>("/auth/me", {
      method: "PUT",
      body: JSON.stringify(userData),
    });
  }

  async requestPasswordReset(email: string): Promise<SuccessResponse> {
    return this.request<SuccessResponse>("/auth/password/reset", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  async resendVerificationEmail(email: string): Promise<SuccessResponse> {
    return this.request<SuccessResponse>("/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }

  async deleteAccount(): Promise<SuccessResponse> {
    return this.request<SuccessResponse>("/auth/me", {
      method: "DELETE",
    });
  }
}

export const apiClient = new ApiClient();

export const authApi = {
  signUp(userData: Omit<UserCreate, "preferred_language" | "timezone">) {
    return apiClient.signUp(userData);
  },
  signIn(credentials: UserLogin) {
    return apiClient.signIn(credentials);
  },
  signInWithLinkedIn(redirectTo?: string) {
    return apiClient.signInWithLinkedIn(redirectTo);
  },
  signOut() {
    return apiClient.signOut();
  },
  refreshToken(refreshToken: string) {
    return apiClient.refreshToken(refreshToken);
  },
  getCurrentUser() {
    return apiClient.getCurrentUser();
  },
  updateUser(userData: UserUpdate) {
    return apiClient.updateUser(userData);
  },
  requestPasswordReset(email: string) {
    return apiClient.requestPasswordReset(email);
  },
  resendVerificationEmail(email: string) {
    return apiClient.resendVerificationEmail(email);
  },
  deleteAccount() {
    return apiClient.deleteAccount();
  },
};

export { ApiError };
export type { ApiResponse };
