import React from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PenTool, ExternalLink, Lock, Users } from "lucide-react";
import { Link } from "react-router-dom";

const EarlyAccess = () => {
  const handleEarlyAccessClick = () => {
    window.open("https://tally.so/r/3Xd1JP", "_blank", "noopener,noreferrer");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-accent/10 via-background to-muted/20 flex items-center justify-center p-4 sm:p-6">
      <div className="w-full max-w-lg">
        <div className="text-center mb-6 sm:mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4 sm:mb-6">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-primary via-secondary to-accent rounded-xl flex items-center justify-center shadow-lg">
              <PenTool className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <span className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Promptly
            </span>
          </div>
        </div>

        <Card className="border border-border shadow-xl bg-card">
          <CardHeader className="text-center pb-4 sm:pb-6">
            <div className="flex justify-center mb-4">
              <div className="w-16 h-16 bg-gradient-to-br from-accent/20 to-accent/10 rounded-full flex items-center justify-center">
                <Lock className="w-8 h-8 text-primary" />
              </div>
            </div>
            <CardTitle className="text-foreground text-xl sm:text-2xl mb-2">
              We're in Closed Testing
            </CardTitle>
            <CardDescription className="text-sm sm:text-base text-muted-foreground leading-relaxed">
              Promptly is currently being refined with a select group of early
              users. We're working hard to perfect the experience before our
              public launch.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="bg-muted/30 rounded-lg p-6 space-y-4">
              <div className="flex items-start space-x-3">
                <Users className="w-5 h-5 text-muted-foreground mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-foreground mb-1">
                    Join the Waitlist
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Be among the first to know when Promptly opens to everyone.
                    Get exclusive early access and special launch benefits.
                  </p>
                </div>
              </div>
            </div>

            <Button
              onClick={handleEarlyAccessClick}
              className="w-full bg-primary hover:bg-primary/90 text-white h-12 font-semibold shadow-lg text-base"
            >
              Sign Up for Early Access
              <ExternalLink className="w-4 h-4 ml-2" />
            </Button>

            <div className="text-center">
              <p className="text-xs text-muted-foreground mb-3">
                Already have an account?
              </p>
              <Link
                to="/login"
                className="text-primary hover:text-primary/80 font-semibold hover:underline text-sm"
              >
                Sign in here
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EarlyAccess;
