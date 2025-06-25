import React, { useState, useEffect } from "react";
import { Button } from "./ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Alert, AlertDescription } from "./ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./ui/alert-dialog";
import { useToast } from "./ui/use-toast";
import {
  profileApi,
  LinkedInAuthInfo,
  SocialConnection,
} from "../lib/profile-api";
import {
  AlertCircle,
  CheckCircle,
  Linkedin,
  Loader2,
  XCircle,
} from "lucide-react";

interface UnipileLinkedInConnectionProps {
  onConnectionUpdate?: (connection: SocialConnection | null) => void;
}

type ConnectionStatus =
  | "idle"
  | "connecting"
  | "polling"
  | "connected"
  | "error";

export const UnipileLinkedInConnection: React.FC<
  UnipileLinkedInConnectionProps
> = ({ onConnectionUpdate }) => {
  const [authInfo, setAuthInfo] = useState<LinkedInAuthInfo | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("idle");
  const [connection, setConnection] = useState<SocialConnection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollingAttempts, setPollingAttempts] = useState(0);
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);
  const { toast } = useToast();

  const maxPollingAttempts = 30; // Poll for up to 5 minutes (10s intervals)
  const pollingInterval = 10000; // 10 seconds

  useEffect(() => {
    loadAuthInfo();
    loadExistingConnection();
  }, []);

  const loadAuthInfo = async () => {
    try {
      const info = await profileApi.linkedinAuthInfo();
      setAuthInfo(info);
    } catch (error) {
      console.error("Failed to load LinkedIn auth info:", error);
    }
  };

  const loadExistingConnection = async () => {
    try {
      const existingConnection = await profileApi.getSocialConnection(
        "linkedin"
      );
      setConnection(existingConnection);
      setConnectionStatus("connected");
      onConnectionUpdate?.(existingConnection);
    } catch (error) {
      // No existing connection, which is fine
      setConnection(null);
      onConnectionUpdate?.(null);
    }
  };

  const handleConnect = async () => {
    try {
      setConnectionStatus("connecting");
      setError(null);
      setPollingAttempts(0);

      // Get authorization URL
      const authResponse = await profileApi.linkedinAuthorize();

      // Open auth URL in new window
      const authWindow = window.open(
        authResponse.authorization_url,
        "linkedin-auth",
        "width=600,height=600,scrollbars=yes,resizable=yes"
      );

      if (!authWindow) {
        throw new Error(
          "Failed to open authentication window. Please check popup blocker settings."
        );
      }

      // For Unipile, start polling for connection status and monitor window
      if (authInfo?.auth_method === "unipile") {
        setConnectionStatus("polling");

        // Monitor if window is closed without completing auth
        const checkWindowClosed = setInterval(() => {
          if (authWindow.closed) {
            clearInterval(checkWindowClosed);

            // Give a moment for any webhook processing
            setTimeout(() => {
              if (connectionStatus === "polling") {
                setConnectionStatus("idle");
                toast({
                  title: "Authentication Window Closed",
                  description:
                    "Please complete the LinkedIn authentication to continue.",
                  variant: "default",
                });
              }
            }, 3000);
          }
        }, 1000);

        startPollingForConnection();
      } else {
        // For native LinkedIn, listen for window close
        const checkClosed = setInterval(() => {
          if (authWindow.closed) {
            clearInterval(checkClosed);
            loadExistingConnection();
            setConnectionStatus("idle");
          }
        }, 1000);
      }
    } catch (error: unknown) {
      console.error("Connection error:", error);
      setError(
        (error as Error).message || "Failed to initiate LinkedIn connection"
      );
      setConnectionStatus("error");

      toast({
        title: "Connection Failed",
        description:
          (error as Error).message || "Failed to connect LinkedIn account",
        variant: "destructive",
      });
    }
  };

  const startPollingForConnection = () => {
    const pollForConnection = async () => {
      try {
        const updatedConnection = await profileApi.getSocialConnection(
          "linkedin"
        );

        // Check if this is a Unipile connection
        if (
          updatedConnection &&
          updatedConnection.connection_data &&
          (updatedConnection.connection_data as Record<string, unknown>)
            .auth_method === "unipile"
        ) {
          setConnection(updatedConnection);
          setConnectionStatus("connected");
          onConnectionUpdate?.(updatedConnection);

          toast({
            title: "LinkedIn Connected",
            description:
              "Your LinkedIn account has been successfully connected via Unipile.",
          });

          return; // Stop polling
        }
      } catch (error) {
        // Connection not ready yet, continue polling
      }

      setPollingAttempts((prev) => prev + 1);

      if (pollingAttempts >= maxPollingAttempts) {
        setConnectionStatus("error");
        setError("Connection timeout. Please try again.");

        toast({
          title: "Connection Timeout",
          description:
            "The connection process took too long. Please try again.",
          variant: "destructive",
        });

        return;
      }

      // Continue polling
      setTimeout(pollForConnection, pollingInterval);
    };

    // Start polling after a short delay
    setTimeout(pollForConnection, 2000);
  };

  const handleDisconnectClick = () => {
    setShowDisconnectDialog(true);
  };

  const handleDisconnectConfirm = async () => {
    try {
      setShowDisconnectDialog(false);
      // Update connection to inactive
      await profileApi.updateSocialConnection("linkedin", { is_active: false });
      setConnection(null);
      setConnectionStatus("idle");
      onConnectionUpdate?.(null);

      toast({
        title: "LinkedIn Disconnected",
        description: "Your LinkedIn account has been disconnected.",
      });
    } catch (error: unknown) {
      console.error("Disconnect error:", error);
      toast({
        title: "Disconnect Failed",
        description:
          (error as Error).message || "Failed to disconnect LinkedIn account",
        variant: "destructive",
      });
    }
  };

  if (!authInfo) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-6">
          <Loader2 className="h-6 w-6 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  const isConnected = connectionStatus === "connected" && connection;
  const isLoading =
    connectionStatus === "connecting" || connectionStatus === "polling";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {isConnected ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <XCircle className="h-5 w-5" />
          )}
          LinkedIn Connection
        </CardTitle>
        <CardDescription>
          Connect your LinkedIn account to enable posting and content analysis.
          {authInfo.auth_method === "unipile" && (
            <span className="block text-sm text-blue-600 mt-1">
              Powered by Unipile
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {!authInfo.configured && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              LinkedIn integration is not configured. Please contact an
              administrator.
            </AlertDescription>
          </Alert>
        )}

        {connectionStatus === "polling" && (
          <Alert>
            <Loader2 className="h-4 w-4 animate-spin" />
            <AlertDescription>
              Waiting for LinkedIn connection... (Attempt {pollingAttempts + 1}/
              {maxPollingAttempts})
              <br />
              <span className="text-sm text-muted-foreground">
                Complete the authentication in the popup window.
              </span>
            </AlertDescription>
          </Alert>
        )}

        {isConnected ? (
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <span className="text-sm font-medium text-green-800">
                  Connected
                </span>
              </div>
              <Button
                variant="outline"
                onClick={handleDisconnectClick}
                size="sm"
              >
                Disconnect
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-3 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-600" />
                <span className="text-sm font-medium text-red-800">
                  Not Connected
                </span>
              </div>
              <Button
                onClick={handleConnect}
                disabled={!authInfo.configured || isLoading}
                size="sm"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {connectionStatus === "connecting"
                      ? "Opening Authentication..."
                      : "Connecting..."}
                  </>
                ) : (
                  "Connect"
                )}
              </Button>
            </div>
          </div>
        )}
      </CardContent>

      {/* Disconnect Confirmation Dialog */}
      <AlertDialog
        open={showDisconnectDialog}
        onOpenChange={setShowDisconnectDialog}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Disconnect LinkedIn Account?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to disconnect your LinkedIn account? This
              will:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>Remove your LinkedIn connection from this app</li>
                <li>Stop any scheduled posts to LinkedIn</li>
                <li>Clear your stored LinkedIn authentication data</li>
              </ul>
              You can reconnect at any time.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDisconnectConfirm}>
              Disconnect
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
};
