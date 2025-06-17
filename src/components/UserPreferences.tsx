
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { Settings, Plus, X, Tag, Globe } from 'lucide-react';

interface UserPreference {
  topics: string[];
  websites: string[];
}

export const UserPreferences: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [preferences, setPreferences] = useState<UserPreference>({
    topics: [],
    websites: []
  });
  const [newTopic, setNewTopic] = useState('');
  const [newWebsite, setNewWebsite] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user) {
      loadPreferences();
    }
  }, [user]);

  const loadPreferences = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', user?.id)
        .maybeSingle();

      if (error && error.code !== 'PGRST116') throw error;
      
      if (data?.preferences) {
        const prefs = data.preferences as any;
        setPreferences({
          topics: prefs.topics || [],
          websites: prefs.websites || []
        });
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
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
          preferences: preferences,
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

  const addTopic = () => {
    if (newTopic.trim() && !preferences.topics.includes(newTopic.trim())) {
      setPreferences(prev => ({
        ...prev,
        topics: [...prev.topics, newTopic.trim()]
      }));
      setNewTopic('');
    }
  };

  const removeTopic = (topicToRemove: string) => {
    setPreferences(prev => ({
      ...prev,
      topics: prev.topics.filter(topic => topic !== topicToRemove)
    }));
  };

  const addWebsite = () => {
    if (newWebsite.trim() && !preferences.websites.includes(newWebsite.trim())) {
      setPreferences(prev => ({
        ...prev,
        websites: [...prev.websites, newWebsite.trim()]
      }));
      setNewWebsite('');
    }
  };

  const removeWebsite = (websiteToRemove: string) => {
    setPreferences(prev => ({
      ...prev,
      websites: prev.websites.filter(website => website !== websiteToRemove)
    }));
  };

  const handleTopicKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTopic();
    }
  };

  const handleWebsiteKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addWebsite();
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-4 sm:p-6">
          <div className="text-center">Loading preferences...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
          <Settings className="w-5 h-5" />
          Content Preferences
        </CardTitle>
        <p className="text-xs sm:text-sm text-gray-600">
          Configure your topics of interest and favorite websites to get personalized content suggestions
        </p>
      </CardHeader>
      <CardContent className="space-y-4 sm:space-y-6">
        {/* Topics Section */}
        <div className="space-y-3 sm:space-y-4">
          <div className="flex items-center gap-2">
            <Tag className="w-4 h-4 text-blue-500" />
            <h3 className="font-medium text-sm sm:text-base">Topics of Interest</h3>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Add a topic (e.g., AI, Marketing, Startups)"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              onKeyPress={handleTopicKeyPress}
              className="flex-1 text-sm sm:text-base"
            />
            <Button onClick={addTopic} size="sm" className="w-full sm:w-auto">
              <Plus className="w-4 h-4 mr-1 sm:mr-2" />
              <span className="text-sm">Add</span>
            </Button>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {preferences.topics.map((topic, index) => (
              <Badge key={index} variant="secondary" className="text-xs sm:text-sm">
                {topic}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeTopic(topic)}
                  className="ml-2 h-auto p-0 hover:bg-transparent"
                >
                  <X className="w-3 h-3" />
                </Button>
              </Badge>
            ))}
          </div>
          
          {preferences.topics.length === 0 && (
            <p className="text-xs sm:text-sm text-gray-500 italic">
              No topics added yet. Add topics you're interested in to get personalized suggestions.
            </p>
          )}
        </div>

        {/* Websites Section */}
        <div className="space-y-3 sm:space-y-4">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-green-500" />
            <h3 className="font-medium text-sm sm:text-base">Favorite Websites</h3>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              placeholder="Add a website (e.g., techcrunch.com, medium.com)"
              value={newWebsite}
              onChange={(e) => setNewWebsite(e.target.value)}
              onKeyPress={handleWebsiteKeyPress}
              className="flex-1 text-sm sm:text-base"
            />
            <Button onClick={addWebsite} size="sm" className="w-full sm:w-auto">
              <Plus className="w-4 h-4 mr-1 sm:mr-2" />
              <span className="text-sm">Add</span>
            </Button>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {preferences.websites.map((website, index) => (
              <Badge key={index} variant="outline" className="text-xs sm:text-sm">
                {website}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeWebsite(website)}
                  className="ml-2 h-auto p-0 hover:bg-transparent"
                >
                  <X className="w-3 h-3" />
                </Button>
              </Badge>
            ))}
          </div>
          
          {preferences.websites.length === 0 && (
            <p className="text-xs sm:text-sm text-gray-500 italic">
              No websites added yet. Add your favorite content sources for better recommendations.
            </p>
          )}
        </div>

        <div className="pt-3 sm:pt-4 border-t border-gray-100">
          <Button 
            onClick={savePreferences} 
            disabled={isSaving}
            className="w-full sm:w-auto"
          >
            {isSaving ? 'Saving...' : 'Save Preferences'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
