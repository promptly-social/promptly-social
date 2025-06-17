
import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookOpen, Plus, X } from 'lucide-react';

interface TopicsManagerProps {
  topics: string[];
  onTopicsChange: (topics: string[]) => void;
}

export const TopicsManager: React.FC<TopicsManagerProps> = ({
  topics,
  onTopicsChange
}) => {
  const [newTopic, setNewTopic] = useState('');

  const addTopic = () => {
    if (newTopic.trim() && !topics.includes(newTopic.trim())) {
      onTopicsChange([...topics, newTopic.trim()]);
      setNewTopic('');
    }
  };

  const removeTopic = (topic: string) => {
    onTopicsChange(topics.filter(t => t !== topic));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTopic();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <BookOpen className="w-4 h-4 text-blue-600" />
        <Label className="font-medium">Topics of Interest</Label>
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        {topics.map((topic, index) => (
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
          onKeyPress={handleKeyPress}
        />
        <Button onClick={addTopic} size="sm" disabled={!newTopic.trim()}>
          <Plus className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
