
import { useState, useEffect } from 'react';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';

interface UserPreferencesData {
  topics_of_interest: string[];
  websites: string[];
}

export const useUserPreferences = () => {
  const [preferences, setPreferences] = useState<UserPreferencesData>({
    topics_of_interest: [],
    websites: []
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchPreferences();
    }
  }, [user]);

  const fetchPreferences = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', user?.id)
        .maybeSingle();

      if (error && error.code !== 'PGRST116') throw error;

      if (data) {
        setPreferences({
          topics_of_interest: data.topics_of_interest || [],
          websites: data.websites || []
        });
      }
    } catch (error) {
      console.error('Error fetching preferences:', error);
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
      const { error } = await supabase
        .from('user_preferences')
        .upsert({
          user_id: user?.id,
          topics_of_interest: preferences.topics_of_interest,
          websites: preferences.websites,
          updated_at: new Date().toISOString()
        }, {
          onConflict: 'user_id'
        });

      if (error) throw error;

      toast({
        title: "Success",
        description: "Preferences saved successfully",
      });
    } catch (error) {
      console.error('Error saving preferences:', error);
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
    setPreferences(prev => ({
      ...prev,
      topics_of_interest: topics
    }));
  };

  const updateWebsites = (websites: string[]) => {
    setPreferences(prev => ({
      ...prev,
      websites: websites
    }));
  };

  return {
    preferences,
    isLoading,
    isSaving,
    savePreferences,
    updateTopics,
    updateWebsites
  };
};
