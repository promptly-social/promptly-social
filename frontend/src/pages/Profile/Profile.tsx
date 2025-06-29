import React from "react";
import { SocialConnections } from "@/components/SocialConnections";
import { WritingAnalysis } from "@/components/WritingAnalysis";
import { UserBio } from "@/components/UserBio";
import AppLayout from "@/components/AppLayout";
import { UnipileLinkedInConnection } from "@/components/UnipileLinkedInConnection";

const Profile: React.FC = () => {
  return (
    <AppLayout title="Profile">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8">
          <div className="text-center mb-6 sm:mb-8">
            <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto px-4">
              Connect your social accounts, and analyze your bio, writing style,
              and content preferences for personalized content creation
            </p>
          </div>

          <div className="space-y-6 sm:space-y-8">
            <UnipileLinkedInConnection />

            <SocialConnections />

            <UserBio />

            <WritingAnalysis />
          </div>
        </div>
      </main>
    </AppLayout>
  );
};

export default Profile;
