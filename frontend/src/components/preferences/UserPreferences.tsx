import React, { useState, useMemo, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useProfile } from "@/contexts/ProfileContext";
import { useUpdateUserPreferences } from "@/lib/profile-queries";
import { useToast } from "@/hooks/use-toast";
import { Settings, Plus, X, Tag, Globe } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface UserPreference {
  topics: string[];
  websites: string[];
  substacks: string[];
}

export const UserPreferences: React.FC = () => {
  const { userPreferences, loading: isLoading } = useProfile();
  const { toast } = useToast();
  const updatePreferencesMutation = useUpdateUserPreferences();
  
  // Local state for pending changes
  const [pendingChanges, setPendingChanges] = useState<UserPreference | null>(null);
  
  // Use pending changes if available, otherwise fall back to server data
  const preferences = useMemo(() => {
    if (pendingChanges) return pendingChanges;
    return {
      topics: userPreferences?.topics_of_interest || [],
      websites: userPreferences?.websites || [],
      substacks: userPreferences?.substacks || [],
    };
  }, [userPreferences, pendingChanges]);

  // Check if there are unsaved changes
  const hasUnsavedChanges = useMemo(() => {
    if (!pendingChanges || !userPreferences) return false;
    
    const serverPrefs = {
      topics: userPreferences.topics_of_interest || [],
      websites: userPreferences.websites || [],
      substacks: userPreferences.substacks || [],
    };
    
    return (
      JSON.stringify(pendingChanges.topics.sort()) !== JSON.stringify(serverPrefs.topics.sort()) ||
      JSON.stringify(pendingChanges.websites.sort()) !== JSON.stringify(serverPrefs.websites.sort()) ||
      JSON.stringify(pendingChanges.substacks.sort()) !== JSON.stringify(serverPrefs.substacks.sort())
    );
  }, [pendingChanges, userPreferences]);

  const [newTopic, setNewTopic] = useState("");
  const [newWebsite, setNewWebsite] = useState("");
  const [newSubstack, setNewSubstack] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Save changes function
  const saveChanges = useCallback(async () => {
    if (!pendingChanges) return;
    
    setIsSaving(true);
    try {
      await updatePreferencesMutation.mutateAsync({
        topics_of_interest: pendingChanges.topics,
        websites: pendingChanges.websites,
        substacks: pendingChanges.substacks,
      });
      
      // Clear pending changes after successful save
      setPendingChanges(null);
      
      toast({
        title: "Saved",
        description: "Preferences updated successfully",
      });
    } catch (error) {
      console.error("Error saving preferences:", error);
      toast({
        title: "Error",
        description: "Failed to save preferences",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  }, [pendingChanges, updatePreferencesMutation, toast]);

  // Discard changes function
  const discardChanges = useCallback(() => {
    setPendingChanges(null);
    setNewTopic("");
    setNewWebsite("");
    setNewSubstack("");
  }, []);

  const addTopic = () => {
    if (newTopic.trim() && !preferences.topics.includes(newTopic.trim())) {
      const newPreferences = {
        ...preferences,
        topics: [...preferences.topics, newTopic.trim()],
      };

      setNewTopic("");
      setPendingChanges(newPreferences);
    }
  };

  const removeTopic = (topicToRemove: string) => {
    const newPreferences = {
      ...preferences,
      topics: preferences.topics.filter((topic) => topic !== topicToRemove),
    };

    setPendingChanges(newPreferences);
  };

  const addWebsite = () => {
    if (
      newWebsite.trim() &&
      !preferences.websites.includes(newWebsite.trim())
    ) {
      const newPreferences = {
        ...preferences,
        websites: [...preferences.websites, newWebsite.trim()],
      };

      setNewWebsite("");
      setPendingChanges(newPreferences);
    }
  };

  const removeWebsite = (websiteToRemove: string) => {
    const newPreferences = {
      ...preferences,
      websites: preferences.websites.filter(
        (website) => website !== websiteToRemove
      ),
    };

    setPendingChanges(newPreferences);
  };

  const handleTopicKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTopic();
    }
  };

  const handleWebsiteKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addWebsite();
    }
  };

  const addSubstack = () => {
    if (
      newSubstack.trim() &&
      !preferences.substacks.includes(newSubstack.trim())
    ) {
      const newPreferences = {
        ...preferences,
        substacks: [...preferences.substacks, newSubstack.trim()],
      };

      setNewSubstack("");
      setPendingChanges(newPreferences);
    }
  };

  const removeSubstack = (substackToRemove: string) => {
    const newPreferences = {
      ...preferences,
      substacks: preferences.substacks.filter(
        (substack) => substack !== substackToRemove
      ),
    };

    setPendingChanges(newPreferences);
  };

  const handleSubstackKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addSubstack();
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <Settings className="w-5 h-5" />
          Content Preferences
        </CardTitle>
        <p className="text-xs sm:text-sm text-gray-600">
          Configure your topics of interest and favorite websites to get daily
          personalized content suggestions.
          {isSaving && (
            <span className="ml-2 text-blue-600 font-medium">Saving...</span>
          )}
        </p>
      </CardHeader>
      <CardContent className="space-y-4 sm:space-y-6">
        {/* Topics Section */}
        <div className="space-y-3 sm:space-y-4">
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-blue-500" />
            <h3 className="font-medium text-sm sm:text-base">
              Topics of Interest
            </h3>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Add a topic (e.g., AI, Marketing, Startups)"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              onKeyDown={handleTopicKeyPress}
              className="flex-1 text-sm sm:text-base"
              disabled={isSaving}
            />
            <Button
              onClick={addTopic}
              size="sm"
              className="w-full sm:w-auto"
              disabled={isSaving || !newTopic.trim()}
            >
              <Plus className="w-4 h-4 mr-1 sm:mr-2" />
              <span className="text-sm">Add</span>
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {isLoading ? (
              <Skeleton className="w-full h-8" />
            ) : (
              preferences.topics.map((topic, index) => (
                <Badge
                  key={index}
                  variant="secondary"
                  className="text-xs sm:text-sm"
                >
                  {topic}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeTopic(topic)}
                    className="ml-2 h-auto p-0 hover:bg-transparent"
                    disabled={isSaving}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </Badge>
              ))
            )}
          </div>

          {preferences.topics.length === 0 && (
            <p className="text-xs sm:text-sm text-gray-500 italic">
              No topics added yet. Add topics you're interested in to get
              personalized suggestions.
            </p>
          )}
        </div>

        {/* Websites Section */}
        <div className="space-y-3 sm:space-y-4">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-green-500" />
            <h3 className="font-medium text-sm sm:text-base">
              Favorite News Websites
            </h3>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Add a website (e.g., techcrunch.com, tldr.tech)"
              value={newWebsite}
              onChange={(e) => setNewWebsite(e.target.value)}
              onKeyDown={handleWebsiteKeyPress}
              className="flex-1 text-sm sm:text-base"
              disabled={isSaving}
            />
            <Button
              onClick={addWebsite}
              size="sm"
              className="w-full sm:w-auto"
              disabled={isSaving || !newWebsite.trim()}
            >
              <Plus className="w-4 h-4 mr-1 sm:mr-2" />
              <span className="text-sm">Add</span>
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {isLoading ? (
              <Skeleton className="w-full h-8" />
            ) : (
              preferences.websites.map((website, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="text-xs sm:text-sm"
                >
                  {website}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeWebsite(website)}
                    className="ml-2 h-auto p-0 hover:bg-transparent"
                    disabled={isSaving}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </Badge>
              ))
            )}
          </div>

          {preferences.websites.length === 0 && (
            <p className="text-xs sm:text-sm text-gray-500 italic">
              No websites added yet. Add your favorite content sources for
              better recommendations.
            </p>
          )}
        </div>

        {/* Substacks Section */}
        <div className="space-y-3 sm:space-y-4">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-orange-500" />
            <h3 className="font-medium text-sm sm:text-base">
              Favorite Substack Newsletters
            </h3>
          </div>

          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Add a Substack newsletter (e.g., platformer.news, stratechery.com)"
              value={newSubstack}
              onChange={(e) => setNewSubstack(e.target.value)}
              onKeyDown={handleSubstackKeyPress}
              className="flex-1 text-sm sm:text-base"
              disabled={isSaving}
            />
            <Button
              onClick={addSubstack}
              size="sm"
              className="w-full sm:w-auto"
              disabled={isSaving || !newSubstack.trim()}
            >
              <Plus className="w-4 h-4 mr-1 sm:mr-2" />
              <span className="text-sm">Add</span>
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {isLoading ? (
              <Skeleton className="w-full h-8" />
            ) : (
              preferences.substacks.map((substack, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="text-xs sm:text-sm border-orange-200 text-orange-700"
                >
                  {substack}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeSubstack(substack)}
                    className="ml-2 h-auto p-0 hover:bg-transparent"
                    disabled={isSaving}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </Badge>
              ))
            )}
          </div>

          {preferences.substacks.length === 0 && (
            <p className="text-xs sm:text-sm text-gray-500 italic">
              No Substack newsletters added yet. Add your favorite newsletters
              for personalized content inspiration.
            </p>
          )}
        </div>

        {/* Save/Discard Buttons */}
        {hasUnsavedChanges && (
          <div className="flex flex-col sm:flex-row gap-2 pt-4 border-t">
            <div className="flex-1">
              <p className="text-sm text-amber-600 mb-2">
                You have unsaved changes
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={discardChanges}
                disabled={isSaving}
                size="sm"
              >
                Discard Changes
              </Button>
              <Button
                onClick={saveChanges}
                disabled={isSaving}
                size="sm"
              >
                {isSaving ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
