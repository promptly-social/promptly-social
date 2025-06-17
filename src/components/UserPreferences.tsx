
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Settings } from 'lucide-react';
import { TopicsManager } from './TopicsManager';
import { WebsitesManager } from './WebsitesManager';
import { useUserPreferences } from '@/hooks/useUserPreferences';

export const UserPreferences: React.FC = () => {
  const {
    preferences,
    isLoading,
    isSaving,
    savePreferences,
    updateTopics,
    updateWebsites
  } = useUserPreferences();

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-gray-600">Loading preferences...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5" />
          Content Preferences
        </CardTitle>
        <p className="text-sm text-gray-600">
          Configure your interests and preferred sources for personalized content suggestions
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <TopicsManager
          topics={preferences.topics_of_interest}
          onTopicsChange={updateTopics}
        />

        <WebsitesManager
          websites={preferences.websites}
          onWebsitesChange={updateWebsites}
        />

        <Button 
          onClick={savePreferences} 
          disabled={isSaving}
          className="w-full"
        >
          {isSaving ? 'Saving...' : 'Save Preferences'}
        </Button>
      </CardContent>
    </Card>
  );
};
