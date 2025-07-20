import React from "react";
import { ContentStrategies } from "@/components/preferences/ContentStrategies";
import { UserPreferences } from "@/components/preferences/UserPreferences";
import { ImageGenerationStyleEditor } from "@/components/preferences/ImageGenerationStyleEditor";
import AppLayout from "@/components/AppLayout";

const ContentPreferences: React.FC = () => {
  return (
    <AppLayout title="Content Preferences">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8">

          
          <div className="text-center mb-6 sm:mb-8">
            <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto px-4">
              Define your content strategy and preferences to create more
              targeted and personalized content
            </p>
          </div>

          <div className="space-y-6 sm:space-y-8">
            <ContentStrategies />

            <UserPreferences />
            
            <ImageGenerationStyleEditor />
          </div>
        </div>
      </main>
    </AppLayout>
  );
};

export default ContentPreferences;
