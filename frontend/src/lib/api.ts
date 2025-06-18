// API client for backend authentication services
import type {
  User,
  AuthResponse,
  TokenResponse,
  UserCreate,
  UserLogin,
  SuccessResponse,
  GoogleAuthRequest,
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

  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get("content-type");
    const isJson = contentType?.includes("application/json");

    let data;
    if (isJson) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      let errorMessage = data?.detail || data?.error || `HTTP ${response.status}`;
      
      // Handle validation errors with details
      if (data?.details && Array.isArray(data.details) && data.details.length > 0) {
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
          errorMessage = validationErrors.join('; ');
        }
      }

      throw new ApiError(errorMessage, response.status, data);
    }

    return data;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: this.getAuthHeaders(),
      ...options,
    };

    try {
      const response = await fetch(url, config);
      return await this.handleResponse<T>(response);
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        `Network error: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
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

  async signInWithGoogle(
    redirectTo?: string
  ): Promise<{ url: string; message: string }> {
    return this.request<{ url: string; message: string }>(
      "/auth/signin/google",
      {
        method: "POST",
        body: JSON.stringify({ redirect_to: redirectTo }),
      }
    );
  }

  async signOut(): Promise<SuccessResponse> {
    return this.request<SuccessResponse>("/auth/signout", {
      method: "POST",
    });
  }

  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return this.request<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>("/auth/me", {
      method: "GET",
    });
  }

  async requestPasswordReset(email: string): Promise<SuccessResponse> {
    return this.request<SuccessResponse>("/auth/password/reset", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  }
}

export const apiClient = new ApiClient();
export { ApiError };
export type { ApiResponse };
