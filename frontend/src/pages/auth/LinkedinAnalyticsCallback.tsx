import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { ApiError } from "@/lib/auth-api";

import { Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const LinkedinAnalyticsCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleAnalyticsCallback = async (code: string, origin: string | null, state: string | null) => {
      try {
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const url = new URL(`${apiUrl}/api/v1/auth/linkedin-analytics/callback`);
        url.searchParams.append("code", code);
        if (origin) {
          url.searchParams.append("origin", origin);
        }
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
            .catch(() => ({ detail: "LinkedIn Analytics authentication failed" }));
          throw new ApiError(
            errorData.detail || `Request failed: ${response.status}`
          );
        }

        const data = await response.json();

        if (data.success) {
          toast({
            title: "LinkedIn Analytics Connected",
            description: "Your LinkedIn analytics access has been successfully configured.",
          });

          // Redirect to the appropriate page based on origin
          const redirectPath = data.redirect_to || "/profile";
          navigate(redirectPath, { replace: true });
        } else {
          throw new Error("Invalid response from server");
        }
      } catch (error) {
        console.error("LinkedIn Analytics callback error:", error);
        let message = "An error occurred while connecting LinkedIn Analytics.";
        if (error instanceof Error) {
          message = error.message;
        }
        toast({
          title: "LinkedIn Analytics Error",
          description: message,
          variant: "destructive",
        });
        
        // Redirect to profile page on error
        const origin = searchParams.get("origin");
        const fallbackPath = origin === "my-posts" ? "/my-posts" : "/profile";
        navigate(fallbackPath, { replace: true });
      } finally {
        setIsProcessing(false);
      }
    };

    const code = searchParams.get("code");
    const origin = searchParams.get("origin");
    const state = searchParams.get("state");

    if (!code) {
      toast({
        title: "LinkedIn Analytics Failed",
        description: "No authorization code was provided by LinkedIn.",
        variant: "destructive",
      });
      const fallbackPath = origin === "my-posts" ? "/my-posts" : "/profile";
      navigate(fallbackPath, { replace: true });
      return;
    }

    handleAnalyticsCallback(code, origin, state);
  }, [searchParams, navigate, toast]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            Connecting LinkedIn Analytics
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center text-gray-600">
          {isProcessing ? (
            <p>Setting up your LinkedIn analytics access...</p>
          ) : (
            <p>Redirecting you now...</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LinkedinAnalyticsCallback;
