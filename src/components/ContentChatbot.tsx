
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ContentTypeSelector } from './ContentTypeSelector';
import { StyleAdaptationToggle } from './StyleAdaptationToggle';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { FileText } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

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

interface ContentChatbotProps {
  connectedPlatforms: ConnectedPlatform[];
  hasStyleAnalysis: boolean;
  onOutlineGenerated: (outline: Outline, contentIdeaId: string) => void;
}

export const ContentChatbot: React.FC<ContentChatbotProps> = ({
  connectedPlatforms,
  hasStyleAnalysis,
  onOutlineGenerated
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hi! I\'m here to help you create amazing content. Tell me about your content idea and I\'ll help you develop it into a structured outline.',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [contentType, setContentType] = useState<'blog_post' | 'linkedin_post'>('blog_post');
  const [useStyleAdaptation, setUseStyleAdaptation] = useState(true);
  const { toast } = useToast();
  const { user } = useAuth();

  const handleSendMessage = async (messageText?: string) => {
    const textToSend = messageText || inputMessage;
    if (!textToSend.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: textToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Check if this looks like a content idea request
      const isContentIdeaRequest = textToSend.toLowerCase().includes('idea') || 
                                  textToSend.toLowerCase().includes('content') ||
                                  textToSend.toLowerCase().includes('write') ||
                                  textToSend.toLowerCase().includes('post') ||
                                  textToSend.toLowerCase().includes('blog');

      if (isContentIdeaRequest && user) {
        // Generate outline with streaming
        const response = await fetch('/functions/v1/generate-outline', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: textToSend,
            contentType: contentType,
            userId: user.id,
            useStyleAdaptation: useStyleAdaptation && hasStyleAnalysis,
            stream: true,
          }),
        });

        if (response.ok && response.body) {
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let streamingMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: '',
            timestamp: new Date()
          };

          setMessages(prev => [...prev, streamingMessage]);

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value);
              const lines = chunk.split('\n');

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const data = line.slice(6);
                  if (data === '[DONE]') {
                    break;
                  }
                  
                  try {
                    const parsed = JSON.parse(data);
                    if (parsed.content) {
                      streamingMessage.content += parsed.content;
                      setMessages(prev => 
                        prev.map(msg => 
                          msg.id === streamingMessage.id 
                            ? { ...msg, content: streamingMessage.content }
                            : msg
                        )
                      );
                    }
                    
                    if (parsed.outline) {
                      // Save to database
                      const { data: savedData, error } = await supabase
                        .from('content_ideas')
                        .insert({
                          user_id: user.id,
                          title: parsed.outline.title,
                          original_input: textToSend,
                          input_type: 'text',
                          generated_outline: parsed.outline,
                          content_type: contentType,
                          status: 'draft'
                        })
                        .select()
                        .single();

                      if (!error && savedData) {
                        onOutlineGenerated(parsed.outline, savedData.id);
                      }
                    }
                  } catch (e) {
                    console.error('Error parsing streaming data:', e);
                  }
                }
              }
            }
          } finally {
            reader.releaseLock();
          }
        } else {
          throw new Error('Failed to generate outline');
        }
      } else {
        // Regular chat response
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: "I'd love to help you with your content! Could you share more details about what you'd like to create? For example, what topic are you interested in writing about?",
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Error:', error);
      toast({
        title: "Error",
        description: "Failed to process your message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTranscription = (text: string) => {
    handleSendMessage(text);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="w-5 h-5" />
          Content Assistant
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col gap-4">
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
        </div>

        <MessageList messages={messages} isLoading={isLoading} />
        
        <ChatInput
          inputMessage={inputMessage}
          setInputMessage={setInputMessage}
          onSendMessage={handleSendMessage}
          onTranscription={handleTranscription}
          isLoading={isLoading}
          onKeyPress={handleKeyPress}
        />
      </CardContent>
    </Card>
  );
};
