
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AudioRecorder } from './AudioRecorder';
import { OutlineBrainstorming } from './OutlineBrainstorming';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2, FileText, Linkedin } from 'lucide-react';

interface Outline {
  title: string;
  sections: {
    heading: string;
    keyPoints: string[];
  }[];
}

export const ContentIdeaForm: React.FC = () => {
  const [textInput, setTextInput] = useState('');
  const [contentType, setContentType] = useState<'blog_post' | 'linkedin_post'>('blog_post');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedOutline, setGeneratedOutline] = useState<Outline | null>(null);
  const [contentIdeaId, setContentIdeaId] = useState<string | null>(null);
  const { toast } = useToast();
  const { user } = useAuth();

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
      // Generate outline using AI
      const outlineResponse = await fetch('/functions/v1/generate-outline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: input,
          contentType: contentType,
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
          description: "Your content outline has been generated and saved!",
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
            <Select value={contentType} onValueChange={(value: 'blog_post' | 'linkedin_post') => setContentType(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="blog_post">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Blog Post
                  </div>
                </SelectItem>
                <SelectItem value="linkedin_post">
                  <div className="flex items-center gap-2">
                    <Linkedin className="w-4 h-4" />
                    LinkedIn Post
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

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
                'Generate Outline from Text'
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
