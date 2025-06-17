
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { AudioRecorder } from './AudioRecorder';
import { OutlineBrainstorming } from './OutlineBrainstorming';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2, FileText, Linkedin, Sparkles, AlertCircle } from 'lucide-react';

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
      
      // If no platforms connected, default to blog_post
      // If only specific platforms connected, set appropriate default
      if (data && data.length > 0) {
        const hasLinkedIn = data.some(p => p.platform === 'linkedin');
        if (hasLinkedIn && !data.some(p => p.platform === 'substack')) {
          setContentType('linkedin_post');
        }
      }
    } catch (error) {
      console.error('Error fetching connected platforms:', error);
    } finally {
      setIsLoadingPlatforms(false);
    }
  };

  const getAvailableContentTypes = () => {
    const types = [];
    
    // Always show blog post option
    types.push({
      value: 'blog_post',
      label: 'Blog Post',
      icon: FileText,
      connected: true
    });

    // Show LinkedIn option only if connected
    const linkedinConnection = connectedPlatforms.find(p => p.platform === 'linkedin');
    if (linkedinConnection) {
      types.push({
        value: 'linkedin_post',
        label: `LinkedIn Post${linkedinConnection.platform_username ? ` (@${linkedinConnection.platform_username})` : ''}`,
        icon: Linkedin,
        connected: true
      });
    }

    return types;
  };

  const handleAudioTranscription = (text: string) => {
    setTextInput(text);
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

  const availableContentTypes = getAvailableContentTypes();

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
          <div>
            <label className="block text-sm font-medium mb-2">Content Type</label>
            {availableContentTypes.length === 1 && availableContentTypes[0].value === 'blog_post' ? (
              <div className="p-3 border border-amber-200 bg-amber-50 rounded-lg">
                <div className="flex items-center gap-2 text-amber-800">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-sm">
                    Only blog posts available. Connect social platforms in your Writing Profile to create posts for those platforms.
                  </span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={() => window.location.href = '/writing-profile'}
                  className="mt-2 text-amber-700 border-amber-300 hover:bg-amber-100"
                >
                  Connect Platforms
                </Button>
              </div>
            ) : (
              <Select value={contentType} onValueChange={(value: 'blog_post' | 'linkedin_post') => setContentType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableContentTypes.map((type) => {
                    const Icon = type.icon;
                    return (
                      <SelectItem key={type.value} value={type.value}>
                        <div className="flex items-center gap-2">
                          <Icon className="w-4 h-4" />
                          {type.label}
                        </div>
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Style Adaptation Toggle */}
          <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Sparkles className="w-5 h-5 text-purple-600" />
                  <div>
                    <Label className="text-sm font-medium text-purple-800">
                      Style Adaptation
                    </Label>
                    <p className="text-xs text-purple-600">
                      {hasStyleAnalysis 
                        ? "Generate content matching your writing style" 
                        : "Complete writing analysis to enable this feature"
                      }
                    </p>
                  </div>
                </div>
                <Switch
                  checked={useStyleAdaptation}
                  onCheckedChange={setUseStyleAdaptation}
                  disabled={!hasStyleAnalysis}
                />
              </div>
              {!hasStyleAnalysis && (
                <div className="mt-3 pt-3 border-t border-purple-200">
                  <p className="text-xs text-purple-600 mb-2">
                    To enable style adaptation, visit your Writing Profile to analyze your writing style.
                  </p>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => window.location.href = '/writing-profile'}
                    className="text-purple-700 border-purple-300 hover:bg-purple-50"
                  >
                    Go to Writing Profile
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <div>
            <label className="block text-sm font-medium mb-2">Your Content Idea</label>
            <Textarea
              placeholder="Describe your content idea here..."
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              rows={4}
              className="resize-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button 
              onClick={handleTextSubmit} 
              disabled={isGenerating || !textInput.trim()}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Generating Outline...
                </>
              ) : (
                <>
                  {useStyleAdaptation && hasStyleAnalysis && (
                    <Sparkles className="w-4 h-4 mr-2" />
                  )}
                  Generate {useStyleAdaptation && hasStyleAnalysis ? 'Style-Adapted ' : ''}Outline
                </>
              )}
            </Button>

            <AudioRecorder 
              onTranscription={(text) => {
                handleAudioTranscription(text);
                generateOutline(text, 'audio');
              }}
              disabled={isGenerating}
            />
          </div>
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
