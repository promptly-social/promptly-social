import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import {
  profileApi,
  type UserPreferences as ApiUserPreferences,
} from "@/lib/profile-api";
import { useAuth } from "@/contexts/AuthContext";

type UserPreferencesData = Pick<
  ApiUserPreferences,
  "topics_of_interest" | "websites"
>;

export const useUserPreferences = () => {
  const [preferences, setPreferences] = useState<UserPreferencesData>({
    topics_of_interest: [],
    websites: [],
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchPreferences();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchPreferences = async () => {
    setIsLoading(true);
    try {
      const data = await profileApi.getUserPreferences();

      setPreferences({
        topics_of_interest: data.topics_of_interest || [],
        websites: data.websites || [],
      });
    } catch (error) {
      console.error("Error fetching preferences:", error);
      toast({
        title: "Error",
        description: "Failed to load preferences",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const savePreferences = async () => {
    setIsSaving(true);
    try {
      await profileApi.updateUserPreferences({
        topics_of_interest: preferences.topics_of_interest,
        websites: preferences.websites,
      });

      toast({
        title: "Success",
        description: "Preferences saved successfully",
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

  const updateTopics = (topics: string[]) => {
    setPreferences((prev) => ({
      ...prev,
      topics_of_interest: topics,
    }));
  };

  const updateWebsites = (websites: string[]) => {
    setPreferences((prev) => ({
      ...prev,
      websites: websites,
    }));
  };

  return {
    preferences,
    isLoading,
    isSaving,
    savePreferences,
    updateTopics,
    updateWebsites,
  };
};
