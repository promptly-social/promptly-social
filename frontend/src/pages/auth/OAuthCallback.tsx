import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import { setTokens } from "@/lib/api-interceptor";
import { getFrontendBaseUrl } from "@/lib/utils";

const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { forceAuthRefresh } = useAuth();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for direct tokens first (from backend redirect)
        const accessToken = searchParams.get("access_token");
        const refreshToken = searchParams.get("refresh_token");
        const expiresIn = searchParams.get("expires_in");
        const error = searchParams.get("error");

        // Check for OAuth code (from Supabase direct redirect)
        const code = searchParams.get("code");

        // Check for email verification
        const verified = searchParams.get("verified");

        if (error) {
          console.error("OAuth error detected:", error);
          toast({
            title: "Authentication Error",
            description:
              error === "oauth_callback_failed"
                ? "OAuth authentication failed. Please try again."
                : error.replace(/_/g, " "),
            variant: "destructive",
          });
          navigate("/login");
          return;
        }

        // If we have direct tokens, use them
        if (accessToken && refreshToken && expiresIn) {
          setTokens(accessToken, refreshToken, parseInt(expiresIn));

          try {
            await forceAuthRefresh();
          } catch (error) {
            console.error("Failed to refresh auth context:", error);
          }

          if (verified === "true") {
            toast({
              title: "Email Verified!",
              description:
                "Your email has been verified successfully. Welcome!",
            });
          } else {
            toast({
              title: "Sign In Successful",
              description: "Welcome! You have been signed in successfully.",
            });
          }

          navigate("/new-content", { replace: true });
        }
        // If we have a code, exchange it for tokens via backend
        else if (code) {
          try {
            const frontendUrl = getFrontendBaseUrl();
            const response = await fetch(
              `${
                import.meta.env.VITE_API_URL || "http://localhost:8000"
              }/api/v1/auth/callback/google?code=${code}&redirect_to=${frontendUrl}/new-content`,
              {
                method: "GET",
                headers: {
                  "Content-Type": "application/json",
                },
              }
            );

            if (response.ok) {
              const data = await response.json();

              if (data.access_token && data.refresh_token) {
                setTokens(
                  data.access_token,
                  data.refresh_token,
                  data.expires_in || 3600
                );

                await forceAuthRefresh();

                if (verified === "true") {
                  toast({
                    title: "Email Verified!",
                    description:
                      "Your email has been verified successfully. Welcome!",
                  });
                } else {
                  toast({
                    title: "Sign In Successful",
                    description:
                      "Welcome! You have been signed in successfully.",
                  });
                }

                navigate("/new-content", { replace: true });
              } else {
                throw new Error("Invalid response: missing tokens");
              }
            } else {
              const errorText = await response.text();
              throw new Error(
                `Backend OAuth exchange failed: ${response.status} - ${errorText}`
              );
            }
          } catch (error) {
            toast({
              title: "Authentication Error",
              description:
                "Failed to complete authentication. Please try again.",
              variant: "destructive",
            });
            navigate("/login", { replace: true });
          }
        } else {
          throw new Error("Missing authentication tokens or code");
        }
      } catch (error) {
        console.error("=== OAuth Callback Error ===");
        console.error("Error details:", error);
        toast({
          title: "Authentication Error",
          description: "Failed to complete authentication. Please try again.",
          variant: "destructive",
        });
        navigate("/login", { replace: true });
      } finally {
        setIsProcessing(false);
      }
    };

    handleCallback();
  }, [searchParams, navigate, toast, forceAuthRefresh]);

  if (isProcessing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              Completing Sign In
            </CardTitle>
          </CardHeader>
          <CardContent className="text-center text-gray-600">
            <p>Please wait while we complete your authentication...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return null;
};

export default OAuthCallback;
