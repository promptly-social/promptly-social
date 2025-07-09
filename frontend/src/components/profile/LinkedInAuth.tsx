import React, { useState, useEffect } from "react";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { Alert, AlertDescription } from "../ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../ui/alert-dialog";
import { useToast } from "../ui/use-toast";
import {
  profileApi,
  LinkedInAuthInfo,
  SocialConnection,
} from "@/lib/profile-api";
import { AlertCircle, CheckCircle, Loader2, XCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface LinkedInAuthProps {
  onConnectionUpdate?: (connection: SocialConnection | null) => void;
}

type ConnectionStatus = "idle" | "connecting" | "connected" | "error";

export const LinkedInAuth: React.FC<LinkedInAuthProps> = ({
  onConnectionUpdate,
}) => {
  const [authInfo, setAuthInfo] = useState<LinkedInAuthInfo | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("idle");
  const [connection, setConnection] = useState<SocialConnection | null>(null);
  const [isConnectionLoading, setIsConnectionLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadAuthInfo();
    loadExistingConnection();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    setIsConnectionLoading(true);
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
    } finally {
      setIsConnectionLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      setConnectionStatus("connecting");
      setError(null);

      // Get authorization URL
      const authResponse = await profileApi.linkedinAuthorize();

      // Redirect the current tab to LinkedIn for authentication.
      // LinkedIn will redirect back to our frontend once the user has
      // completed the flow. Upon returning, `loadExistingConnection()`
      // will run in the useEffect and update the component state.
      window.location.assign(authResponse.authorization_url);
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

  if (!authInfo || isConnectionLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Skeleton className="h-5 w-5 rounded-full" />
            <Skeleton className="h-5 w-40" />
          </CardTitle>
          <CardDescription>
            <Skeleton className="h-4 w-64" />
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-3 rounded-lg border">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Skeleton className="h-4 w-4 rounded-full" />
                <Skeleton className="h-4 w-20" />
              </div>
              <Skeleton className="h-9 w-24 rounded-md" />
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const isConnected = connectionStatus === "connected" && connection;
  const isLoading = connectionStatus === "connecting";

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
          Connect your LinkedIn account to enable posting.
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
