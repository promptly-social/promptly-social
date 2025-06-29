import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PenTool, Mail } from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const { signIn, signInWithGoogle, clearPendingVerification } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Clear pending verification when accessing login page
  useEffect(() => {
    clearPendingVerification();
  }, [clearPendingVerification]);

  // Handle OAuth callback
  useEffect(() => {
    const error = searchParams.get("error");
    if (error) {
      toast({
        title: "Authentication Error",
        description:
          error === "oauth_callback_failed"
            ? "OAuth authentication failed. Please try again."
            : error,
        variant: "destructive",
      });
    }
  }, [searchParams, toast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const { error } = await signIn(email, password);
      if (error) {
        toast({
          title: "Sign In Error",
          description: error.message,
          variant: "destructive",
        });
      } else {
        // Sign in successful - navigate to new-content with a small delay
        console.log("Sign in successful, navigating to /new-content");
        setTimeout(() => {
          navigate("/new-content");
        }, 100);
      }
    } catch (error) {
      toast({
        title: "Sign In Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setIsGoogleLoading(true);
    try {
      const { error } = await signInWithGoogle();
      if (error) {
        toast({
          title: "Google Sign In Error",
          description: error.message,
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Google Sign In Error",
        description: "An unexpected error occurred. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGoogleLoading(false);
    }
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
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            Welcome back
          </h1>
          <p className="text-sm sm:text-base text-gray-600">
            Sign in to continue creating amazing content
          </p>
        </div>

        <Card className="border border-gray-200 shadow-xl bg-white">
          <CardHeader className="pb-4 sm:pb-6">
            <CardTitle className="text-gray-900 text-lg sm:text-xl">
              Sign In
            </CardTitle>
            <CardDescription className="text-sm text-gray-600">
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 sm:space-y-6">
            <Button
              onClick={handleGoogleSignIn}
              variant="outline"
              className="w-full h-10 sm:h-12 border-gray-300 hover:bg-gray-50"
              disabled={isGoogleLoading}
            >
              <Mail className="w-4 h-4 mr-2" />
              {isGoogleLoading ? "Signing in..." : "Continue with Google"}
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-gray-500">
                  Or continue with
                </span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
              <div className="space-y-2">
                <Label
                  htmlFor="email"
                  className="text-gray-700 font-medium text-sm"
                >
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  className="border-gray-300 h-10 sm:h-12 text-sm sm:text-base"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label
                  htmlFor="password"
                  className="text-gray-700 font-medium text-sm"
                >
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter your password"
                  className="border-gray-300 h-10 sm:h-12 text-sm sm:text-base"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <Button
                type="submit"
                className="w-full bg-gradient-to-r from-gray-900 to-gray-800 hover:from-gray-800 hover:to-gray-700 text-white h-10 sm:h-12 font-semibold shadow-lg text-sm sm:text-base"
                disabled={isLoading}
              >
                {isLoading ? "Signing In..." : "Sign In"}
              </Button>
              <div className="text-center text-xs sm:text-sm text-gray-600">
                Don't have an account?{" "}
                <Link
                  to="/signup"
                  className="text-gray-800 hover:text-gray-900 font-semibold hover:underline"
                >
                  Join Early Access
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;
