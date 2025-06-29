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
  const { forceAuthRefresh, clearPendingVerification } = useAuth();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for tokens in URL parameters first
        let accessToken = searchParams.get("access_token");
        let refreshToken = searchParams.get("refresh_token");
        let expiresIn = searchParams.get("expires_in");
        let error = searchParams.get("error");
        let code = searchParams.get("code");
        let verified = searchParams.get("verified");
        let type = searchParams.get("type");

        // If no tokens in parameters, check URL fragment (common for Supabase email verification)
        if (!accessToken && window.location.hash) {
          const fragment = window.location.hash.substring(1); // Remove #
          const fragmentParams = new URLSearchParams(fragment);

          accessToken = fragmentParams.get("access_token");
          refreshToken = fragmentParams.get("refresh_token");
          expiresIn = fragmentParams.get("expires_in");
          error = fragmentParams.get("error");
          code = fragmentParams.get("code") || code;
          verified = fragmentParams.get("verified") || verified;
          type = fragmentParams.get("type");
        }

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
          // Check if this is email verification (type=signup indicates email verification)
          if (type === "signup") {
            try {
              // Extract email from the Supabase JWT
              const tokenPayload = JSON.parse(atob(accessToken.split(".")[1]));
              const email = tokenPayload.email;

              // Call backend to exchange Supabase tokens for backend tokens
              const response = await fetch(
                `${
                  import.meta.env.VITE_API_URL || "http://localhost:8000"
                }/api/v1/auth/verify`,
                {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify({
                    supabase_access_token: accessToken,
                    supabase_refresh_token: refreshToken,
                    email: email,
                  }),
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

                  // Clear any pending email verification state
                  clearPendingVerification();

                  // Clean up URL to remove tokens from browser history
                  if (window.location.hash) {
                    window.history.replaceState(
                      {},
                      document.title,
                      window.location.pathname
                    );
                  }

                  try {
                    await forceAuthRefresh();
                  } catch (error) {
                    console.error("Failed to refresh auth context:", error);
                  }

                  toast({
                    title: "Email Verified! 🎉",
                    description:
                      "Your email has been verified successfully. Welcome to Promptly!",
                    duration: 5000,
                  });

                  navigate("/new-content", { replace: true });
                  return;
                }
              } else {
                console.error("Failed to exchange tokens with backend");
              }
            } catch (error) {
              console.error("Error exchanging tokens:", error);
            }
          }

          // If not email verification or token exchange failed, use the tokens as-is
          setTokens(accessToken, refreshToken, parseInt(expiresIn));

          // Clear any pending email verification state
          clearPendingVerification();

          // Clean up URL to remove tokens from browser history
          if (window.location.hash) {
            window.history.replaceState(
              {},
              document.title,
              window.location.pathname
            );
          }

          try {
            await forceAuthRefresh();
          } catch (error) {
            console.error("Failed to refresh auth context:", error);
          }

          // Check if this is email verification (type=signup indicates email verification)
          if (type === "signup" || verified === "true") {
            // Update user verification status in database
            try {
              await fetch(
                `${
                  import.meta.env.VITE_API_URL || "http://localhost:8000"
                }/api/v1/auth/me`,
                {
                  method: "PUT",
                  headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${accessToken}`,
                  },
                  body: JSON.stringify({ is_verified: true }),
                }
              );
            } catch (error) {
              console.error(
                "Failed to update user verification status:",
                error
              );
              // Don't block the flow if this fails
            }

            toast({
              title: "Email Verified! 🎉",
              description:
                "Your email has been verified successfully. Welcome to Promptly!",
              duration: 5000,
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

                // Clear any pending email verification state
                clearPendingVerification();

                await forceAuthRefresh();

                if (type === "signup" || verified === "true") {
                  // Update user verification status in database
                  try {
                    await fetch(
                      `${
                        import.meta.env.VITE_API_URL || "http://localhost:8000"
                      }/api/v1/auth/me`,
                      {
                        method: "PUT",
                        headers: {
                          "Content-Type": "application/json",
                          Authorization: `Bearer ${data.access_token}`,
                        },
                        body: JSON.stringify({ is_verified: true }),
                      }
                    );
                  } catch (error) {
                    console.error(
                      "Failed to update user verification status:",
                      error
                    );
                    // Don't block the flow if this fails
                  }

                  toast({
                    title: "Email Verified! 🎉",
                    description:
                      "Your email has been verified successfully. Welcome to Promptly!",
                    duration: 5000,
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
        console.error("OAuth callback error:", error);
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
