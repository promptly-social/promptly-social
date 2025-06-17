
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Settings, Plus, X, Globe, BookOpen } from 'lucide-react';

interface UserPreferencesData {
  topics_of_interest: string[];
  websites: string[];
}

export const UserPreferences: React.FC = () => {
  const [preferences, setPreferences] = useState<UserPreferencesData>({
    topics_of_interest: [],
    websites: []
  });
  const [newTopic, setNewTopic] = useState('');
  const [newWebsite, setNewWebsite] = useState('');
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

  const addTopic = () => {
    if (newTopic.trim() && !preferences.topics_of_interest.includes(newTopic.trim())) {
      setPreferences(prev => ({
        ...prev,
        topics_of_interest: [...prev.topics_of_interest, newTopic.trim()]
      }));
      setNewTopic('');
    }
  };

  const removeTopic = (topic: string) => {
    setPreferences(prev => ({
      ...prev,
      topics_of_interest: prev.topics_of_interest.filter(t => t !== topic)
    }));
  };

  const addWebsite = () => {
    if (newWebsite.trim() && !preferences.websites.includes(newWebsite.trim())) {
      // Add https:// if no protocol is specified
      let url = newWebsite.trim();
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
      }
      
      setPreferences(prev => ({
        ...prev,
        websites: [...prev.websites, url]
      }));
      setNewWebsite('');
    }
  };

  const removeWebsite = (website: string) => {
    setPreferences(prev => ({
      ...prev,
      websites: prev.websites.filter(w => w !== website)
    }));
  };

  const handleKeyPress = (e: React.KeyboardEvent, action: () => void) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      action();
    }
  };

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
        {/* Topics of Interest */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-600" />
            <Label className="font-medium">Topics of Interest</Label>
          </div>
          <div className="flex flex-wrap gap-2 mb-3">
            {preferences.topics_of_interest.map((topic, index) => (
              <Badge key={index} variant="secondary" className="flex items-center gap-1">
                {topic}
                <button
                  onClick={() => removeTopic(topic)}
                  className="ml-1 hover:bg-gray-300 rounded-full p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Add a topic (e.g., AI, Marketing, Technology)"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              onKeyPress={(e) => handleKeyPress(e, addTopic)}
            />
            <Button onClick={addTopic} size="sm" disabled={!newTopic.trim()}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Websites */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-green-600" />
            <Label className="font-medium">Preferred Websites</Label>
          </div>
          <div className="flex flex-wrap gap-2 mb-3">
            {preferences.websites.map((website, index) => (
              <Badge key={index} variant="outline" className="flex items-center gap-1">
                {website.replace(/^https?:\/\//, '')}
                <button
                  onClick={() => removeWebsite(website)}
                  className="ml-1 hover:bg-gray-300 rounded-full p-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2">
            <Input
              placeholder="Add a website (e.g., techcrunch.com, medium.com)"
              value={newWebsite}
              onChange={(e) => setNewWebsite(e.target.value)}
              onKeyPress={(e) => handleKeyPress(e, addWebsite)}
            />
            <Button onClick={addWebsite} size="sm" disabled={!newWebsite.trim()}>
              <Plus className="w-4 h-4" />
            </Button>
          </div>
        </div>

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
