import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { setTokens } from "@/lib/api-interceptor";
import { getFrontendBaseUrl } from "@/lib/utils";

import { useToast } from "@/hooks/use-toast";

import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AxiosError extends Error {
  response?: {
    data?: {
      detail?: string;
    };
    status?: number;
  };
}

const LinkedinCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { forceAuthRefresh } = useAuth();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleLinkedinCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");

      // Handle LinkedIn OAuth login callback
      try {
        // Native LinkedIn OAuth flow - expect code and state
        if (!code) {
          toast({
            title: "LinkedIn Connection Error",
            description: "Missing authorization code from LinkedIn.",
            variant: "destructive",
          });
          navigate("/profile");
          return;
        }
        await handleCodeExchange(code, state);
      } catch (error) {
        console.error("Error determining auth method:", error);
        // Fallback to native flow if we can't determine the method
        if (!code) {
          toast({
            title: "LinkedIn Connection Error",
            description: "Missing authorization code from LinkedIn.",
            variant: "destructive",
          });
          navigate("/profile");
          return;
        }
        await handleCodeExchange(code);
      }
    };

    const handleCodeExchange = async (code: string, state?: string) => {
      try {
        const frontendUrl = getFrontendBaseUrl();
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const response = await fetch(
          `${apiUrl}/api/v1/auth/callback/linkedin_oidc?code=${code}&redirect_to=${frontendUrl}/new-auth${
            state ? `&state=${state}` : ""
          }`,
          {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Backend OAuth exchange failed: ${response.status}`);
        }

        const data = await response.json();

        if (data.access_token && data.refresh_token) {
          setTokens(
            data.access_token,
            data.refresh_token,
            data.expires_in || 3600
          );

          await forceAuthRefresh();

          toast({
            title: "Sign In Successful",
            description: "Welcome! You have been signed in successfully.",
          });

          navigate("/new-content", { replace: true });
          return;
        }

        throw new Error("Invalid response: missing tokens");
      } catch (error) {
        console.error("LinkedIn callback error:", error);
        const axiosError = error as AxiosError;
        const errorMessage =
          axiosError.response?.data?.detail ||
          axiosError.message ||
          "An error occurred while connecting your LinkedIn account.";

        toast({
          title: "Authentication Error",
          description: errorMessage,
          variant: "destructive",
        });
        navigate("/profile", { replace: true });
      }
    };

    handleLinkedinCallback();
  }, [searchParams, navigate, toast, forceAuthRefresh]);

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
          {isProcessing ? (
            <p>Waiting for connection confirmation...</p>
          ) : (
            <p>Please wait while we complete your authentication...</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LinkedinCallback;
