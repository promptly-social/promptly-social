
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { OutlineBrainstorming } from './OutlineBrainstorming';
import { ContentTypeSelector } from './ContentTypeSelector';
import { StyleAdaptationToggle } from './StyleAdaptationToggle';
import { ContentInput } from './ContentInput';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2, FileText } from 'lucide-react';

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
  const [textInput, setTextInput] = useState('');
  const [contentType, setContentType] = useState<'blog_post' | 'linkedin_post'>('blog_post');
  const [useStyleAdaptation, setUseStyleAdaptation] = useState(true);
  const [hasStyleAnalysis, setHasStyleAnalysis] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedOutline, setGeneratedOutline] = useState<Outline | null>(null);
  const [contentIdeaId, setContentIdeaId] = useState<string | null>(null);
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

  const shouldShowStyleAdaptation = () => {
    return connectedPlatforms.length > 0 && hasStyleAnalysis;
  };

  const handleAudioTranscription = (text: string) => {
    setTextInput(text);
    generateOutline(text, 'audio');
  };

  const generateOutline = async (input: string, inputType: 'text' | 'audio') => {
    if (!user) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to generate content outlines.",
        variant: "destructive",
      });
      return;
    }

    setIsGenerating(true);
    try {
      // Generate outline using AI with optional style adaptation
      const outlineResponse = await fetch('/functions/v1/generate-outline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: input,
          contentType: contentType,
          userId: user.id,
          useStyleAdaptation: useStyleAdaptation && hasStyleAnalysis,
        }),
      });

      if (!outlineResponse.ok) {
        throw new Error('Failed to generate outline');
      }

      const { outline } = await outlineResponse.json();
      setGeneratedOutline(outline);

      // Save to database
      const { data, error } = await supabase
        .from('content_ideas')
        .insert({
          user_id: user.id,
          title: outline.title,
          original_input: input,
          input_type: inputType,
          generated_outline: outline,
          content_type: contentType,
          status: 'draft'
        })
        .select()
        .single();

      if (error) {
        console.error('Database error:', error);
        toast({
          title: "Outline Generated",
          description: "Your outline was generated but couldn't be saved. You can still use it.",
          variant: "destructive",
        });
      } else {
        setContentIdeaId(data.id);
        toast({
          title: "Outline Generated",
          description: useStyleAdaptation && hasStyleAnalysis 
            ? "Your style-adapted content outline has been generated!" 
            : "Your content outline has been generated!",
        });
      }
    } catch (error) {
      console.error('Error generating outline:', error);
      toast({
        title: "Generation Error",
        description: "Failed to generate outline. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleTextSubmit = () => {
    if (!textInput.trim()) {
      toast({
        title: "Input Required",
        description: "Please enter your content idea.",
        variant: "destructive",
      });
      return;
    }
    generateOutline(textInput, 'text');
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
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Content Idea Input
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ContentTypeSelector
            contentType={contentType}
            onContentTypeChange={setContentType}
            connectedPlatforms={connectedPlatforms}
          />

          <StyleAdaptationToggle
            useStyleAdaptation={useStyleAdaptation}
            onStyleAdaptationChange={setUseStyleAdaptation}
            connectedPlatforms={connectedPlatforms}
            hasStyleAnalysis={hasStyleAnalysis}
          />

          <ContentInput
            textInput={textInput}
            onTextInputChange={setTextInput}
            onTextSubmit={handleTextSubmit}
            onAudioTranscription={handleAudioTranscription}
            isGenerating={isGenerating}
            useStyleAdaptation={useStyleAdaptation}
            shouldShowStyleAdaptation={shouldShowStyleAdaptation()}
          />
        </CardContent>
      </Card>

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
