
import React, { useState, useEffect } from 'react';
import { OutlineBrainstorming } from './OutlineBrainstorming';
import { ContentChatbot } from './ContentChatbot';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface Outline {
  title: string;
  sections: {
    heading: string;
    keyPoints: string[];
  }[];
}

interface ConnectedPlatform {
  platform: string;
  platform_username: string | null;
  is_active: boolean;
}

export const ContentIdeaForm: React.FC = () => {
  const [hasStyleAnalysis, setHasStyleAnalysis] = useState(false);
  const [generatedOutline, setGeneratedOutline] = useState<Outline | null>(null);
  const [contentIdeaId, setContentIdeaId] = useState<string | null>(null);
  const [contentType, setContentType] = useState<'blog_post' | 'linkedin_post'>('blog_post');
  const [connectedPlatforms, setConnectedPlatforms] = useState<ConnectedPlatform[]>([]);
  const [isLoadingPlatforms, setIsLoadingPlatforms] = useState(true);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      checkStyleAnalysis();
      fetchConnectedPlatforms();
    }
  }, [user]);

  const checkStyleAnalysis = async () => {
    if (!user) return;
    
    try {
      const { data, error } = await supabase
        .from('writing_style_analysis')
        .select('id')
        .eq('user_id', user.id)
        .single();

      setHasStyleAnalysis(!!data && !error);
    } catch (error) {
      console.error('Error checking style analysis:', error);
    }
  };

  const fetchConnectedPlatforms = async () => {
    if (!user) return;

    try {
      const { data, error } = await supabase
        .from('social_connections')
        .select('platform, platform_username, is_active')
        .eq('user_id', user.id)
        .eq('is_active', true);

      if (error) throw error;

      setConnectedPlatforms(data || []);
      
      // Set default content type based on available platforms
      if (data && data.length > 0) {
        const hasLinkedIn = data.some(p => p.platform === 'linkedin');
        if (hasLinkedIn) {
          setContentType('linkedin_post');
        }
      }
    } catch (error) {
      console.error('Error fetching connected platforms:', error);
    } finally {
      setIsLoadingPlatforms(false);
    }
  };

  const handleOutlineGenerated = (outline: Outline, ideaId: string) => {
    setGeneratedOutline(outline);
    setContentIdeaId(ideaId);
  };

  const handleOutlineUpdate = (updatedOutline: Outline) => {
    setGeneratedOutline(updatedOutline);
  };

  if (isLoadingPlatforms) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
              <p className="text-gray-600">Loading connected platforms...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <ContentChatbot
        connectedPlatforms={connectedPlatforms}
        hasStyleAnalysis={hasStyleAnalysis}
        onOutlineGenerated={handleOutlineGenerated}
      />

      {generatedOutline && contentIdeaId && (
        <OutlineBrainstorming
          initialOutline={generatedOutline}
          contentType={contentType}
          contentIdeaId={contentIdeaId}
          onOutlineUpdate={handleOutlineUpdate}
        />
      )}
    </div>
  );
};
