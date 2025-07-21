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
  const [isLinkedInLoading, setIsLinkedInLoading] = useState(false);
  const { signInWithLinkedIn } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

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

  const handleLinkedInSignIn = async () => {
    setIsLinkedInLoading(true);
    try {
      const { error } = await signInWithLinkedIn();
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
      setIsLinkedInLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-accent/10 via-background to-muted/20 flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-6 sm:mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4 sm:mb-6">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary via-secondary to-accent rounded-xl flex items-center justify-center shadow-lg">
              <PenTool className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Promptly
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-2">
            Welcome back
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            Sign in to continue creating amazing content
          </p>
        </div>

        <Card className="border border-border shadow-xl bg-card">
          <CardHeader className="pb-4 sm:pb-6">
            <CardTitle className="text-foreground text-lg sm:text-xl">
              Sign In
            </CardTitle>
            <CardDescription className="text-sm text-muted-foreground">
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 sm:space-y-6">
            <Button
              onClick={handleLinkedInSignIn}
              variant="outline"
              className="w-full h-10 sm:h-12 border-border hover:bg-accent/10"
              disabled={isLinkedInLoading}
            >
              <Mail className="w-4 h-4 mr-2" />
              {isLinkedInLoading ? "Signing in..." : "Continue with LinkedIn"}
            </Button>

            <div className="text-center text-xs sm:text-sm text-muted-foreground">
              Don't have an account?{" "}
              <Link
                to="/signup"
                className="text-primary hover:text-primary/80 font-semibold hover:underline"
              >
                Join Early Access
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Login;
