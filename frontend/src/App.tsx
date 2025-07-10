import React from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { ProfileProvider } from "@/contexts/ProfileContext";
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

const queryClient = new QueryClient();

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  }

  const hasToken = getStoredToken();

  if (!user && !hasToken) {
    return <Navigate to="/login" replace />;
  }

  if (user && !user.is_verified) {
    return <Navigate to="/verify-email" replace />;
  }

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        {children}
      </div>
    </SidebarProvider>
  );
};

const EmailVerificationRoute = () => {
  const { pendingEmailVerification, user } = useAuth();
  const email =
    pendingEmailVerification || (user && !user.is_verified ? user.email : null);

  if (!email) {
    return <Navigate to="/login" replace />;
  }

  if (user && user.is_verified) {
    return <Navigate to="/new-content" replace />;
  }

  return <EmailVerification email={email} />;
};

const AuthRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );
  }

  if (user && user.is_verified) {
    return <Navigate to="/new-content" replace />;
  }

  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <AuthProvider>
        <ProfileProvider>
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
              <Route
                path="/signup"
                element={
                  <AuthRoute>
                    <EarlyAccess />
                  </AuthRoute>
                }
              />
              <Route
                path="/new-content"
                element={
                  <ProtectedRoute>
                    <NewContent />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <Profile />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/content-preferences"
                element={
                  <ProtectedRoute>
                    <ContentPreferences />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/my-posts"
                element={
                  <ProtectedRoute>
                    <MyContent />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/posting-schedule"
                element={
                  <ProtectedRoute>
                    <PostingSchedule />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/content-ideas"
                element={
                  <ProtectedRoute>
                    <IdeaBank />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/settings"
                element={
                  <ProtectedRoute>
                    <Settings />
                  </ProtectedRoute>
                }
              />
              <Route path="/auth/callback" element={<OAuthCallback />} />
              <Route
                path="/auth/linkedin/callback"
                element={<LinkedinCallback />}
              />
              <Route
                path="/verify-email"
                element={<EmailVerificationRoute />}
              />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </BrowserRouter>
          <Toaster />
          <Sonner />
        </ProfileProvider>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
