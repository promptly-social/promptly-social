/**
 * Topic Selector Component with color support
 */

import React, { useState, useRef, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ScrollArea } from "@/components/ui/scroll-area";
import { X, Plus, Tag, Palette } from "lucide-react";
import { useUserTopicsContext } from "@/contexts/UserTopicsContext";
import { useCreateUserTopic, useBulkCreateTopics } from "@/lib/user-topics-queries";

interface TopicSelectorProps {
  selectedTopics: string[];
  onTopicsChange: (topics: string[]) => void;
  isReadOnly?: boolean;
  className?: string;
}

export const TopicSelector: React.FC<TopicSelectorProps> = ({
  selectedTopics,
  onTopicsChange,
  isReadOnly = false,
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [newTopicInput, setNewTopicInput] = useState("");
  const [showNewTopicInput, setShowNewTopicInput] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { topics, topicColors, getTopicColor, isLoading } = useUserTopicsContext();
  const createTopicMutation = useCreateUserTopic();
  const bulkCreateMutation = useBulkCreateTopics();

  // Focus input when showing new topic input
  useEffect(() => {
    if (showNewTopicInput && inputRef.current) {
      inputRef.current.focus();
    }
  }, [showNewTopicInput]);

  const handleTopicToggle = (topic: string) => {
    if (selectedTopics.includes(topic)) {
      onTopicsChange(selectedTopics.filter((t) => t !== topic));
    } else {
      onTopicsChange([...selectedTopics, topic]);
    }
  };

  const handleRemoveTopic = (topicToRemove: string) => {
    onTopicsChange(selectedTopics.filter((topic) => topic !== topicToRemove));
  };

  const handleCreateNewTopic = async () => {
    const trimmedTopic = newTopicInput.trim();
    if (!trimmedTopic) return;

    try {
      await createTopicMutation.mutateAsync({ topic: trimmedTopic });
      
      // Add the new topic to selected topics
      if (!selectedTopics.includes(trimmedTopic)) {
        onTopicsChange([...selectedTopics, trimmedTopic]);
      }
      
      setNewTopicInput("");
      setShowNewTopicInput(false);
    } catch (error) {
      console.error("Failed to create topic:", error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleCreateNewTopic();
    } else if (e.key === "Escape") {
      setNewTopicInput("");
      setShowNewTopicInput(false);
    }
  };

  const handleBulkCreateFromSelected = async () => {
    const topicsToCreate = selectedTopics.filter(
      (topic) => !topics.some((t) => t.topic === topic)
    );

    if (topicsToCreate.length > 0) {
      try {
        await bulkCreateMutation.mutateAsync({ topics: topicsToCreate });
      } catch (error) {
        console.error("Failed to bulk create topics:", error);
      }
    }
  };

  // Filter available topics (exclude already selected ones)
  const availableTopics = topics.filter(
    (topic) => !selectedTopics.includes(topic.topic)
  );

  return (
    <div className={`space-y-2 ${className}`}>
      <Label htmlFor="topics-selector">Categories:</Label>
      
      {/* Selected Topics Display */}
      <div className="flex flex-wrap gap-2 min-h-[2rem]">
        {selectedTopics.map((topic) => {
          const color = getTopicColor(topic);
          return (
            <Badge
              key={topic}
              variant="secondary"
              className="flex items-center gap-1"
              style={{
                backgroundColor: color ? `${color}20` : undefined,
                borderColor: color || undefined,
                color: color || undefined,
              }}
            >
              <Tag className="h-3 w-3" />
              {topic}
              {!isReadOnly && (
                <button
                  type="button"
                  onClick={() => handleRemoveTopic(topic)}
                  className="ml-1 -mr-1 p-0.5 rounded-full hover:bg-background/50"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </Badge>
          );
        })}
        
        {selectedTopics.length === 0 && (
          <span className="text-sm text-muted-foreground italic">
            No categories selected
          </span>
        )}
      </div>

      {/* Topic Selector Popover */}
      {!isReadOnly && (
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              size="sm"
              className="flex items-center gap-2"
              disabled={isLoading}
            >
              <Plus className="h-4 w-4" />
              {isLoading ? "Loading..." : "Add Categories"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80" align="start">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-sm">Select Categories</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBulkCreateFromSelected}
                  disabled={
                    selectedTopics.length === 0 ||
                    selectedTopics.every((topic) =>
                      topics.some((t) => t.topic === topic)
                    )
                  }
                  className="text-xs"
                >
                  <Palette className="h-3 w-3 mr-1" />
                  Save Colors
                </Button>
              </div>

              {/* Available Topics */}
              {availableTopics.length > 0 && (
                <div>
                  <Label className="text-xs text-muted-foreground">
                    Available Categories
                  </Label>
                  <ScrollArea className="h-32 mt-1">
                    <div className="space-y-1">
                      {availableTopics.map((topic) => (
                        <button
                          key={topic.id}
                          onClick={() => handleTopicToggle(topic.topic)}
                          className="w-full text-left p-2 rounded-md hover:bg-accent hover:text-accent-foreground text-sm flex items-center gap-2"
                        >
                          <div
                            className="w-3 h-3 rounded-full border"
                            style={{ backgroundColor: topic.color }}
                          />
                          {topic.topic}
                        </button>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}

              {/* Create New Topic */}
              <div className="border-t pt-3">
                {!showNewTopicInput ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowNewTopicInput(true)}
                    className="w-full justify-start text-sm"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create New Category
                  </Button>
                ) : (
                  <div className="space-y-2">
                    <Input
                      ref={inputRef}
                      value={newTopicInput}
                      onChange={(e) => setNewTopicInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Enter category name..."
                      className="text-sm"
                    />
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={handleCreateNewTopic}
                        disabled={!newTopicInput.trim() || createTopicMutation.isPending}
                        className="text-xs"
                      >
                        {createTopicMutation.isPending ? "Creating..." : "Create"}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setNewTopicInput("");
                          setShowNewTopicInput(false);
                        }}
                        className="text-xs"
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
};
