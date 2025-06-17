
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AudioRecorder } from './AudioRecorder';
import { Send, Sparkles } from 'lucide-react';

interface InitialPromptProps {
  onSubmit: (prompt: string) => void;
}

const SUGGESTED_PROMPTS = [
  "Help me write a blog post about sustainable living tips",
  "Create a LinkedIn post about remote work productivity",
  "Write an article about AI's impact on modern business",
  "Generate content ideas for social media marketing"
];

export const InitialPrompt: React.FC<InitialPromptProps> = ({ onSubmit }) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = () => {
    if (prompt.trim()) {
      onSubmit(prompt.trim());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSuggestedPrompt = (suggestedPrompt: string) => {
    setPrompt(suggestedPrompt);
  };

  const handleTranscription = (text: string) => {
    setPrompt(text);
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-8">
      <div className="text-center space-y-4 max-w-2xl">
        <div className="flex items-center justify-center gap-2 mb-4">
          <Sparkles className="w-8 h-8 text-blue-500" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900">
          What would you like to create today?
        </h2>
        <p className="text-lg text-gray-600">
          Describe your content idea and I'll help you develop it into a structured outline
        </p>
      </div>

      <div className="w-full max-w-2xl space-y-6">
        {/* Main Input Area */}
        <div className="space-y-4">
          <Textarea
            placeholder="Tell me about your content idea..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyPress={handleKeyPress}
            className="min-h-[120px] text-base resize-none border-2 focus:border-blue-500"
          />
          
          <div className="flex gap-3">
            <div className="flex-1">
              <AudioRecorder 
                onTranscription={handleTranscription}
                disabled={false}
              />
            </div>
            <Button 
              onClick={handleSubmit} 
              disabled={!prompt.trim()}
              size="lg"
              className="px-8"
            >
              <Send className="w-4 h-4 mr-2" />
              Start Creating
            </Button>
          </div>
        </div>

        {/* Suggested Prompts */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-gray-700">Or try one of these ideas:</p>
          <div className="grid gap-2">
            {SUGGESTED_PROMPTS.map((suggestedPrompt, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedPrompt(suggestedPrompt)}
                className="text-left p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-colors text-sm text-gray-700 hover:text-blue-700"
              >
                {suggestedPrompt}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
