
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2, MessageCircle, Edit3, Wand2, FileText } from 'lucide-react';

interface Outline {
  title: string;
  sections: {
    heading: string;
    keyPoints: string[];
  }[];
}

interface OutlineBrainstormingProps {
  initialOutline: Outline;
  contentType: 'blog_post' | 'linkedin_post';
  contentIdeaId: string;
  onOutlineUpdate: (outline: Outline) => void;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export const OutlineBrainstorming: React.FC<OutlineBrainstormingProps> = ({
  initialOutline,
  contentType,
  contentIdeaId,
  onOutlineUpdate,
}) => {
  const [outline, setOutline] = useState<Outline>(initialOutline);
  const [isEditing, setIsEditing] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [generatedDraft, setGeneratedDraft] = useState<string | null>(null);
  const { toast } = useToast();
  const { user } = useAuth();

  const handleSectionEdit = (sectionIndex: number, field: 'heading' | 'keyPoints', value: string | string[]) => {
    const updatedOutline = { ...outline };
    if (field === 'heading') {
      updatedOutline.sections[sectionIndex].heading = value as string;
    } else {
      updatedOutline.sections[sectionIndex].keyPoints = value as string[];
    }
    setOutline(updatedOutline);
    onOutlineUpdate(updatedOutline);
  };

  const handleTitleEdit = (newTitle: string) => {
    const updatedOutline = { ...outline, title: newTitle };
    setOutline(updatedOutline);
    onOutlineUpdate(updatedOutline);
  };

  const addSection = () => {
    const updatedOutline = {
      ...outline,
      sections: [...outline.sections, { heading: 'New Section', keyPoints: ['Key point'] }]
    };
    setOutline(updatedOutline);
    onOutlineUpdate(updatedOutline);
  };

  const removeSection = (index: number) => {
    const updatedOutline = {
      ...outline,
      sections: outline.sections.filter((_, i) => i !== index)
    };
    setOutline(updatedOutline);
    onOutlineUpdate(updatedOutline);
  };

  const sendChatMessage = async () => {
    if (!currentMessage.trim()) return;

    const userMessage: ChatMessage = { role: 'user', content: currentMessage };
    const updatedMessages = [...chatMessages, userMessage];
    setChatMessages(updatedMessages);
    setCurrentMessage('');
    setIsProcessing(true);

    try {
      const response = await fetch('/functions/v1/brainstorm-outline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: updatedMessages,
          currentOutline: outline,
          contentType: contentType,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process chat message');
      }

      const { response: aiResponse, updatedOutline } = await response.json();
      
      setChatMessages([...updatedMessages, { role: 'assistant', content: aiResponse }]);
      
      if (updatedOutline) {
        setOutline(updatedOutline);
        onOutlineUpdate(updatedOutline);
      }
    } catch (error) {
      console.error('Error in chat:', error);
      toast({
        title: "Chat Error",
        description: "Failed to process your message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const generateFullDraft = async () => {
    setIsGeneratingDraft(true);
    try {
      const response = await fetch('/functions/v1/generate-draft', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          outline: outline,
          contentType: contentType,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate draft');
      }

      const { draft } = await response.json();
      setGeneratedDraft(draft);

      // Save draft to database - properly cast outline to Json type
      if (user) {
        await supabase
          .from('content_ideas')
          .update({
            generated_outline: outline as any,
            updated_at: new Date().toISOString(),
          })
          .eq('id', contentIdeaId);
      }

      toast({
        title: "Draft Generated",
        description: "Your full content draft has been generated!",
      });
    } catch (error) {
      console.error('Error generating draft:', error);
      toast({
        title: "Generation Error",
        description: "Failed to generate draft. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Edit3 className="w-5 h-5" />
            Outline Editor
            <Button
              onClick={() => setIsEditing(!isEditing)}
              variant="outline"
              size="sm"
              className="ml-auto"
            >
              {isEditing ? 'View Mode' : 'Edit Mode'}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Title</label>
            {isEditing ? (
              <Input
                value={outline.title}
                onChange={(e) => handleTitleEdit(e.target.value)}
                className="text-lg font-semibold"
              />
            ) : (
              <h3 className="text-xl font-semibold text-gray-900">{outline.title}</h3>
            )}
          </div>

          <div className="space-y-4">
            {outline.sections.map((section, index) => (
              <div key={index} className="border-l-4 border-gray-200 pl-4 space-y-2">
                {isEditing ? (
                  <>
                    <div className="flex items-center gap-2">
                      <Input
                        value={section.heading}
                        onChange={(e) => handleSectionEdit(index, 'heading', e.target.value)}
                        className="font-medium"
                      />
                      <Button
                        onClick={() => removeSection(index)}
                        variant="destructive"
                        size="sm"
                      >
                        Remove
                      </Button>
                    </div>
                    <Textarea
                      value={section.keyPoints.join('\n')}
                      onChange={(e) => handleSectionEdit(index, 'keyPoints', e.target.value.split('\n').filter(point => point.trim()))}
                      placeholder="Enter key points (one per line)"
                      rows={3}
                    />
                  </>
                ) : (
                  <>
                    <h4 className="font-medium text-gray-900">{section.heading}</h4>
                    <ul className="space-y-1">
                      {section.keyPoints.map((point, pointIndex) => (
                        <li key={pointIndex} className="text-gray-700 text-sm">
                          • {point}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            ))}
          </div>

          {isEditing && (
            <Button onClick={addSection} variant="outline" className="w-full">
              Add Section
            </Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            AI Brainstorming Chat
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="h-64 overflow-y-auto border rounded-lg p-4 space-y-3">
            {chatMessages.length === 0 ? (
              <p className="text-gray-500 text-center">
                Start brainstorming! Ask me to expand sections, suggest alternatives, or refine the structure.
              </p>
            ) : (
              chatMessages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-gray-900 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="flex gap-2">
            <Textarea
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              placeholder="Ask me to expand a section, suggest alternatives, or refine the structure..."
              rows={2}
              className="flex-1"
            />
            <Button
              onClick={sendChatMessage}
              disabled={isProcessing || !currentMessage.trim()}
              className="self-end"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                'Send'
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="w-5 h-5" />
            Generate Full Draft
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Button
            onClick={generateFullDraft}
            disabled={isGeneratingDraft}
            className="w-full mb-4"
          >
            {isGeneratingDraft ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating Draft...
              </>
            ) : (
              <>
                <FileText className="w-4 h-4 mr-2" />
                Generate Full Draft
              </>
            )}
          </Button>

          {generatedDraft && (
            <div className="border rounded-lg p-4 bg-gray-50">
              <h4 className="font-medium mb-3">Generated Draft:</h4>
              <div className="prose max-w-none text-sm whitespace-pre-wrap">
                {generatedDraft}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
