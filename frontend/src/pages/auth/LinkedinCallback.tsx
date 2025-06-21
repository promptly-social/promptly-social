import React, { useEffect } from "react";
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
  };
}

const LinkedinCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  useEffect(() => {
    const handleLinkedinCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");

      if (!code || !state) {
        toast({
          title: "LinkedIn Connection Error",
          description: "Invalid callback parameters from LinkedIn.",
          variant: "destructive",
        });
        navigate("/profile"); // or wherever your settings page is
        return;
      }

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
        navigate("/profile"); // Redirect back to settings page
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
          <p>Please wait while we connect your LinkedIn account...</p>
        </CardContent>
      </Card>
    </div>
  );
};

export default LinkedinCallback;
