// Authentication types matching backend schemas

export interface User {
  id: string;
  email: string;
  full_name?: string;
  preferred_language: string;
  timezone: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  user: User;
  tokens: TokenResponse;
  message: string;
}

export interface UserCreate {
  email: string;
  password: string;
  confirm_password: string;
  full_name?: string;
  preferred_language?: string;
  timezone?: string;
}

export interface UserUpdate {
  full_name?: string;
  preferred_language?: string;
  timezone?: string;
  password?: string;
  confirm_password?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface GoogleAuthRequest {
  id_token: string;
  redirect_to?: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface SuccessResponse {
  success: boolean;
  message: string;
}

export interface ErrorResponse {
  error: string;
  message?: string;
  details?: unknown;
}
