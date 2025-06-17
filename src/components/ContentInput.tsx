
import React from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { AudioRecorder } from './AudioRecorder';
import { Loader2, Sparkles } from 'lucide-react';

interface ContentInputProps {
  textInput: string;
  onTextInputChange: (value: string) => void;
  onTextSubmit: () => void;
  onAudioTranscription: (text: string) => void;
  isGenerating: boolean;
  useStyleAdaptation: boolean;
  shouldShowStyleAdaptation: boolean;
}

export const ContentInput: React.FC<ContentInputProps> = ({
  textInput,
  onTextInputChange,
  onTextSubmit,
  onAudioTranscription,
  isGenerating,
  useStyleAdaptation,
  shouldShowStyleAdaptation
}) => {
  return (
    <>
      <div>
        <label className="block text-sm font-medium mb-2">Your Content Idea</label>
        <Textarea
          placeholder="Describe your content idea here..."
          value={textInput}
          onChange={(e) => onTextInputChange(e.target.value)}
          rows={4}
          className="resize-none"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Button 
          onClick={onTextSubmit} 
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
              {useStyleAdaptation && shouldShowStyleAdaptation && (
                <Sparkles className="w-4 h-4 mr-2" />
              )}
              Generate {useStyleAdaptation && shouldShowStyleAdaptation ? 'Style-Adapted ' : ''}Outline
            </>
          )}
        </Button>

        <AudioRecorder 
          onTranscription={onAudioTranscription}
          disabled={isGenerating}
        />
      </div>
    </>
  );
};
