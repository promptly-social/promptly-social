import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { profileApi, LinkedInAuthInfo } from "@/lib/profile-api";
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
        const authInfo: LinkedInAuthInfo = await profileApi.linkedinAuthInfo();

        if (authInfo.auth_method === "unipile") {
          // For Unipile, we don't expect callback parameters
          // Instead, we poll for connection status since Unipile uses webhooks
          await handleUnipileCallback();
        } else {
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
        }
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

    const handleUnipileCallback = async () => {
      setIsPolling(true);

      // Get the state parameter to check connection status
      const state = searchParams.get("state");
      if (!state) {
        console.log("No state parameter found");
        toast({
          title: "LinkedIn Connection Error",
          description: "Missing state parameter for connection verification.",
          variant: "destructive",
        });
        navigate("/profile");
        return;
      }

      // Poll for connection status for up to 30 seconds using the public endpoint
      const maxAttempts = 30;
      let attempts = 0;

      const pollConnection = async (): Promise<boolean> => {
        try {
          console.log(
            `Polling attempt ${attempts + 1}/${maxAttempts} for state: ${state}`
          );
          const connectionStatus =
            await profileApi.checkLinkedInConnectionStatus(state);
          console.log("Connection status response:", connectionStatus);

          if (
            connectionStatus.connected &&
            connectionStatus.auth_method === "unipile"
          ) {
            console.log("Unipile connection confirmed via status endpoint!");
            return true;
          }

          if (connectionStatus.error) {
            console.error("Connection status error:", connectionStatus.error);
          }

          return false;
        } catch (error) {
          console.error("Error checking connection status:", error);
          return false;
        }
      };

      const poll = async () => {
        attempts++;
        console.log(`Starting poll attempt ${attempts}`);

        const isConnected = await pollConnection();

        if (isConnected) {
          console.log("Connection confirmed, showing success toast");
          toast({
            title: "LinkedIn Connected",
            description:
              "Your LinkedIn account has been successfully connected via Unipile.",
          });
          navigate("/profile");
          return;
        }

        if (attempts < maxAttempts) {
          console.log(
            `No connection found, will retry in 1 second (${attempts}/${maxAttempts})`
          );
          setTimeout(poll, 1000); // Poll every second
        } else {
          console.log("Polling timeout reached");
          toast({
            title: "Connection Timeout",
            description:
              "LinkedIn connection was not detected. Please try again or check your connection.",
            variant: "destructive",
          });
          navigate("/profile");
        }
      };

      // Start polling after a short delay to allow webhook processing
      console.log("Starting Unipile polling in 2 seconds...");
      setTimeout(poll, 2000);
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
