import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { getStoredToken } from "@/lib/api-interceptor";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import Landing from "./pages/Landing";
import { Login, EmailVerification } from "./pages/auth";
import NewContent from "./pages/NewContent/NewContent";
import Profile from "./pages/Profile/Profile";
import ContentPreferences from "./pages/ContentPreferences/ContentPreferences";
import MyContent from "./pages/MyContent/MyContent";
import PostingSchedule from "./pages/PostingSchedule/PostingSchedule";
import IdeaBank from "./pages/IdeaBank/IdeaBank";
import Settings from "./pages/Settings/Settings";
import NotFound from "./pages/NotFound";
import OAuthCallback from "./pages/auth/OAuthCallback";
import LinkedinCallback from "./pages/auth/LinkedinCallback";
import EarlyAccess from "./pages/EarlyAccess";
import Signup from "./pages/auth/Signup";

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();

  console.log("ProtectedRoute - user:", user, "loading:", loading);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  }

  // Check for stored token as fallback to handle OAuth callback race condition
  const hasToken = getStoredToken();
  console.log("ProtectedRoute - hasToken:", hasToken);

  if (!user && !hasToken) {
    console.log("ProtectedRoute - no user or token, redirecting to login");
    return <Navigate to="/login" replace />;
  }

  // If user exists but isn't verified, redirect to verification page
  if (user && !user.is_verified) {
    console.log(
      "ProtectedRoute - user not verified, redirecting to verify-email"
    );
    return <Navigate to="/verify-email" replace />;
  }

  console.log("ProtectedRoute - allowing access to protected route");
  return <>{children}</>;
};

const EmailVerificationRoute = () => {
  const { pendingEmailVerification, user } = useAuth();

  const email =
    pendingEmailVerification || (user && !user.is_verified ? user.email : null);

  // If no email verification is needed, redirect to login
  if (!email) {
    return <Navigate to="/login" replace />;
  }

  // If user is already verified, redirect to new-content
  if (user && user.is_verified) {
    return <Navigate to="/new-content" replace />;
  }

  return <EmailVerification email={email} />;
};

const AuthRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading, pendingEmailVerification } = useAuth();

  console.log(
    "AuthRoute - user:",
    user,
    "loading:",
    loading,
    "pendingEmailVerification:",
    pendingEmailVerification
  );

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  }

  // If user is verified and authenticated, redirect to new-content
  if (user && user.is_verified) {
    console.log("AuthRoute - redirecting verified user to /new-content");
    return <Navigate to="/new-content" replace />;
  }

  // If user exists but isn't verified, allow access to public pages
  // (they can still access landing, login, signup while waiting for verification)
  if (user && !user.is_verified) {
    console.log("AuthRoute - allowing unverified user access to public pages");
    return <>{children}</>;
  }

  // If no user but has pending verification, allow access to public pages
  if (pendingEmailVerification) {
    console.log("AuthRoute - allowing access with pending verification");
    return <>{children}</>;
  }

  console.log("AuthRoute - allowing access to public pages");
  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route
              path="/"
              element={
                <AuthRoute>
                  <Landing />
                </AuthRoute>
              }
            />
            <Route
              path="/login"
              element={
                <AuthRoute>
                  <Login />
                </AuthRoute>
              }
            />
            {/* <Route
              path="/signup"
              element={
                <AuthRoute>
                  <EarlyAccess />
                </AuthRoute>
              }
            /> */}
            <Route
              path="/signup"
              element={
                <AuthRoute>
                  <Signup />
                </AuthRoute>
              }
            />
            <Route
              path="/new-content"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <div className="min-h-screen flex w-full">
                      <AppSidebar />
                      <NewContent />
                    </div>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <div className="min-h-screen flex w-full">
                      <AppSidebar />
                      <Profile />
                    </div>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/content-preferences"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <div className="min-h-screen flex w-full">
                      <AppSidebar />
                      <ContentPreferences />
                    </div>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/my-content"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <div className="min-h-screen flex w-full">
                      <AppSidebar />
                      <MyContent />
                    </div>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/posting-schedule"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <div className="min-h-screen flex w-full">
                      <AppSidebar />
                      <PostingSchedule />
                    </div>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/idea-bank"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <div className="min-h-screen flex w-full">
                      <AppSidebar />
                      <IdeaBank />
                    </div>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SidebarProvider>
                    <div className="min-h-screen flex w-full">
                      <AppSidebar />
                      <Settings />
                    </div>
                  </SidebarProvider>
                </ProtectedRoute>
              }
            />
            <Route path="/auth/callback" element={<OAuthCallback />} />
            <Route
              path="/auth/linkedin/callback"
              element={<LinkedinCallback />}
            />
            <Route path="/verify-email" element={<EmailVerificationRoute />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
