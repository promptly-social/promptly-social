import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { setTokens } from "@/lib/api-interceptor";
import { useToast } from "@/hooks/use-toast";
import { ApiError } from "@/lib/auth-api";

import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const LinkedinCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { forceAuthRefresh } = useAuth();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleCodeExchange = async (code: string, state: string | null) => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const url = new URL(`${apiUrl}/api/v1/auth/linkedin/callback`);
        url.searchParams.append("code", code);
        if (state) {
          url.searchParams.append("state", state);
        }

        const response = await fetch(url.toString(), {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ detail: "Authentication failed" }));
          throw new ApiError(
            errorData.detail || `Request failed: ${response.status}`
          );
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

          navigate("/my-posts", { replace: true });
        } else {
          throw new Error("Invalid response from server: missing tokens.");
        }
      } catch (error) {
        console.error("LinkedIn callback error:", error);
        let message =
          "An error occurred while connecting your LinkedIn account.";
        if (error instanceof Error) {
          message = error.message;
        }
        toast({
          title: "Authentication Error",
          description: message,
          variant: "destructive",
        });
        navigate("/login", { replace: true });
      } finally {
        setIsProcessing(false);
      }
    };

    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (!code) {
      toast({
        title: "LinkedIn Authentication Failed",
        description: "No authorization code was provided by LinkedIn.",
        variant: "destructive",
      });
      navigate("/login", { replace: true });
      return;
    }

    handleCodeExchange(code, state);
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
            <p>Securely connecting with LinkedIn...</p>
          ) : (
            <p>Redirecting you now...</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LinkedinCallback;
