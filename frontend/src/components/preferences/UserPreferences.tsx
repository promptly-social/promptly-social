import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { profileApi } from "@/lib/profile-api";
import { useToast } from "@/hooks/use-toast";
import { Settings, Plus, X, Tag, Globe } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface UserPreference {
  topics: string[];
  websites: string[];
  substacks: string[];
}

export const UserPreferences: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [preferences, setPreferences] = useState<UserPreference>({
    topics: [],
    websites: [],
    substacks: [],
  });
  const [newTopic, setNewTopic] = useState("");
  const [newWebsite, setNewWebsite] = useState("");
  const [newSubstack, setNewSubstack] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user) {
      loadPreferences();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const loadPreferences = async () => {
    setIsLoading(true);
    try {
      const data = await profileApi.getUserPreferences();

      setPreferences({
        topics: data.topics_of_interest || [],
        websites: data.websites || [],
        substacks: data.substacks || [],
      });
    } catch (error) {
      console.error("Error loading preferences:", error);
      toast({
        title: "Error",
        description: "Failed to load preferences",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const savePreferencesToBackend = async (newPreferences: UserPreference) => {
    setIsSaving(true);
    try {
      await profileApi.updateUserPreferences({
        topics_of_interest: newPreferences.topics,
        websites: newPreferences.websites,
        substacks: newPreferences.substacks,
      });

      toast({
        title: "Success",
        description: "Preferences saved automatically",
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
  };

  const addTopic = async () => {
    if (newTopic.trim() && !preferences.topics.includes(newTopic.trim())) {
      const newPreferences = {
        ...preferences,
        topics: [...preferences.topics, newTopic.trim()],
      };

      setPreferences(newPreferences);
      setNewTopic("");
      await savePreferencesToBackend(newPreferences);
    }
  };

  const removeTopic = async (topicToRemove: string) => {
    const newPreferences = {
      ...preferences,
      topics: preferences.topics.filter((topic) => topic !== topicToRemove),
    };

    setPreferences(newPreferences);
    await savePreferencesToBackend(newPreferences);
  };

  const addWebsite = async () => {
    if (
      newWebsite.trim() &&
      !preferences.websites.includes(newWebsite.trim())
    ) {
      const newPreferences = {
        ...preferences,
        websites: [...preferences.websites, newWebsite.trim()],
      };

      setPreferences(newPreferences);
      setNewWebsite("");
      await savePreferencesToBackend(newPreferences);
    }
  };

  const removeWebsite = async (websiteToRemove: string) => {
    const newPreferences = {
      ...preferences,
      websites: preferences.websites.filter(
        (website) => website !== websiteToRemove
      ),
    };

    setPreferences(newPreferences);
    await savePreferencesToBackend(newPreferences);
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

  const addSubstack = async () => {
    if (
      newSubstack.trim() &&
      !preferences.substacks.includes(newSubstack.trim())
    ) {
      const newPreferences = {
        ...preferences,
        substacks: [...preferences.substacks, newSubstack.trim()],
      };

      setPreferences(newPreferences);
      setNewSubstack("");
      await savePreferencesToBackend(newPreferences);
    }
  };

  const removeSubstack = async (substackToRemove: string) => {
    const newPreferences = {
      ...preferences,
      substacks: preferences.substacks.filter(
        (substack) => substack !== substackToRemove
      ),
    };

    setPreferences(newPreferences);
    await savePreferencesToBackend(newPreferences);
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
      </CardContent>
    </Card>
  );
};
