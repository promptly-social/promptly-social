import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PenTool, Mail, RefreshCw, CheckCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { apiClient } from "@/lib/auth-api";
import { useAuth } from "@/contexts/AuthContext";

interface EmailVerificationProps {
  email?: string;
}

const EmailVerification: React.FC<EmailVerificationProps> = ({ email }) => {
  const [isResending, setIsResending] = useState(false);
  const { toast } = useToast();
  const { clearPendingVerification } = useAuth();

  const handleResendEmail = async () => {
    if (!email) {
      toast({
        title: "Error",
        description: "No email address provided",
        variant: "destructive",
      });
      return;
    }

    setIsResending(true);
    try {
      // We'll implement this endpoint
      await apiClient.resendVerificationEmail(email);
      toast({
        title: "Verification Email Sent",
        description: "Please check your inbox for the verification link.",
      });
    } catch (error) {
      toast({
        title: "Failed to Resend",
        description:
          "There was an error resending the verification email. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsResending(false);
    }
  };

  const handleGoBack = () => {
    clearPendingVerification();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100 flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4 sm:mb-6">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-gray-900 via-gray-800 to-black rounded-xl flex items-center justify-center shadow-lg">
              <PenTool className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Promptly
            </span>
          </div>
        </div>

        <Card className="border border-gray-200 shadow-xl bg-white">
          <CardHeader className="pb-4 sm:pb-6 text-center">
            <div className="mx-auto mb-4 w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center">
              <Mail className="w-8 h-8 text-blue-600" />
            </div>
            <CardTitle className="text-gray-900 text-xl sm:text-2xl">
              Check Your Email
            </CardTitle>
            <CardDescription className="text-sm text-gray-600">
              We've sent a verification link to your email address
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 sm:space-y-6">
            <div className="text-center space-y-4">
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2 text-sm text-gray-600 mb-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>Email sent to:</span>
                </div>
                <p className="font-medium text-gray-900">{email}</p>
              </div>

              <div className="text-sm text-gray-600 space-y-2">
                <p>
                  Please check your inbox and click the verification link to
                  activate your account.
                </p>
                <p className="text-xs">
                  Don't forget to check your spam folder if you don't see the
                  email.
                </p>
              </div>

              <div className="pt-4 space-y-3">
                <Button
                  onClick={handleResendEmail}
                  variant="outline"
                  className="w-full h-10 sm:h-12 border-gray-300 hover:bg-gray-50"
                  disabled={isResending}
                >
                  {isResending ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Resending...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Resend Verification Email
                    </>
                  )}
                </Button>

                <div className="text-center text-xs sm:text-sm text-gray-600 space-y-2">
                  <div>
                    Wrong email address?{" "}
                    <Link
                      to="/signup"
                      onClick={handleGoBack}
                      className="text-gray-800 hover:text-gray-900 font-semibold hover:underline"
                    >
                      Sign up again
                    </Link>
                  </div>

                  <div>
                    Already verified?{" "}
                    <Link
                      to="/login"
                      onClick={handleGoBack}
                      className="text-gray-800 hover:text-gray-900 font-semibold hover:underline"
                    >
                      Sign in
                    </Link>
                  </div>

                  <div>
                    <Link
                      to="/"
                      onClick={handleGoBack}
                      className="text-gray-800 hover:text-gray-900 font-semibold hover:underline"
                    >
                      ← Back to home
                    </Link>
                  </div>

                  <div className="pt-2">
                    <Button
                      onClick={handleGoBack}
                      variant="ghost"
                      size="sm"
                      className="text-gray-500 hover:text-gray-700"
                    >
                      Skip for now
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 text-center text-xs text-gray-500">
          Having trouble? Contact our support team for assistance.
        </div>
      </div>
    </div>
  );
};

export default EmailVerification;
