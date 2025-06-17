
import React from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AudioRecorder } from './AudioRecorder';
import { Send } from 'lucide-react';

interface ChatInputProps {
  inputMessage: string;
  setInputMessage: (message: string) => void;
  onSendMessage: () => void;
  onTranscription: (text: string) => void;
  isLoading: boolean;
  onKeyPress: (e: React.KeyboardEvent) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  inputMessage,
  setInputMessage,
  onSendMessage,
  onTranscription,
  isLoading,
  onKeyPress
}) => {
  return (
    <div className="border-t bg-white p-4">
      <div className="space-y-3">
        <div className="flex gap-2">
          <Textarea
            placeholder="Continue the conversation..."
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={onKeyPress}
            disabled={isLoading}
            className="flex-1 min-h-[44px] max-h-[120px] resize-none"
            rows={1}
          />
          <Button 
            onClick={onSendMessage} 
            disabled={isLoading || !inputMessage.trim()}
            size="icon"
            className="h-11 w-11"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        
        <div className="flex justify-center">
          <AudioRecorder 
            onTranscription={onTranscription}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
};
