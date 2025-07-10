import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { profileApi } from "@/lib/profile-api";
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
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    const handleLinkedinCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");

      // First, check what auth method is being used
      try {
        // Native LinkedIn OAuth flow - expect code and state
        if (!code || !state) {
          toast({
            title: "LinkedIn Connection Error",
            description: "Invalid callback parameters from LinkedIn.",
            variant: "destructive",
          });
          navigate("/profile");
          return;
        }
        await handleNativeCallback(code, state);
      } catch (error) {
        console.error("Error determining auth method:", error);
        // Fallback to native flow if we can't determine the method
        if (!code || !state) {
          toast({
            title: "LinkedIn Connection Error",
            description: "Invalid callback parameters from LinkedIn.",
            variant: "destructive",
          });
          navigate("/profile");
          return;
        }
        await handleNativeCallback(code, state);
      }
    };

    const handleNativeCallback = async (code: string, state: string) => {
      try {
        await profileApi.linkedinCallback(code, state);
        toast({
          title: "LinkedIn Connected",
          description: "Your LinkedIn account has been successfully connected.",
        });
      } catch (error) {
        console.error("LinkedIn callback error:", error);
        const axiosError = error as AxiosError;
        const errorMessage =
          axiosError.response?.data?.detail ||
          axiosError.message ||
          "An error occurred while connecting your LinkedIn account.";

        toast({
          title: "LinkedIn Connection Failed",
          description: errorMessage,
          variant: "destructive",
        });
      } finally {
        navigate("/profile");
      }
    };

    handleLinkedinCallback();
  }, [searchParams, navigate, toast]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center gap-2">
            <Loader2 className="w-5 h-5 animate-spin" />
            Connecting to LinkedIn
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center text-gray-600">
          {isPolling ? (
            <p>Waiting for connection confirmation...</p>
          ) : (
            <p>Please wait while we connect your LinkedIn account...</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default LinkedinCallback;
