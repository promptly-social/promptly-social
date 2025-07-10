import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Link2 } from "lucide-react";
import { SubstackConnection } from "./SubstackConnection";
import { LinkedInConnection } from "./LinkedInConnection";

export const SocialConnections: React.FC = () => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link2 className="w-5 h-5" />
          Social Media Connections
        </CardTitle>
        <CardDescription>
          Set up your social media accounts to get personalized content
          recommendations by analyzing your bio and content preferences.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <LinkedInConnection />
        <SubstackConnection />
      </CardContent>
    </Card>
  );
};
