
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { Calendar, Clock, Send } from 'lucide-react';

interface ContentSchedulerProps {
  contentId: string;
  contentType: string;
  onScheduled: () => void;
  onCancel: () => void;
}

export const ContentScheduler: React.FC<ContentSchedulerProps> = ({
  contentId,
  contentType,
  onScheduled,
  onCancel,
}) => {
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [isScheduling, setIsScheduling] = useState(false);
  const [isPublishingNow, setIsPublishingNow] = useState(false);
  const { toast } = useToast();

  const handleSchedule = async () => {
    if (!scheduledDate || !scheduledTime) {
      toast({
        title: "Missing Information",
        description: "Please select both date and time for scheduling.",
        variant: "destructive",
      });
      return;
    }

    const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`);
    const now = new Date();

    if (scheduledDateTime <= now) {
      toast({
        title: "Invalid Date",
        description: "Scheduled time must be in the future.",
        variant: "destructive",
      });
      return;
    }

    setIsScheduling(true);
    try {
      const { error } = await supabase
        .from('content_ideas')
        .update({
          status: 'scheduled',
          scheduled_date: scheduledDateTime.toISOString(),
        })
        .eq('id', contentId);

      if (error) throw error;

      toast({
        title: "Content Scheduled",
        description: `Your ${contentType.replace('_', ' ')} has been scheduled for ${scheduledDateTime.toLocaleString()}.`,
      });

      onScheduled();
    } catch (error) {
      console.error('Error scheduling content:', error);
      toast({
        title: "Scheduling Failed",
        description: "Failed to schedule content. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsScheduling(false);
    }
  };

  const handlePublishNow = async () => {
    setIsPublishingNow(true);
    try {
      if (contentType === 'linkedin_post') {
        const response = await fetch('/functions/v1/linkedin-post', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            contentId,
            userId: (await supabase.auth.getUser()).data.user?.id,
            content: '', // This will be fetched from the database in the edge function
            title: '', // This will be fetched from the database in the edge function
          }),
        });

        const result = await response.json();

        if (result.success) {
          toast({
            title: "Content Published",
            description: "Your LinkedIn post has been published successfully!",
          });
          onScheduled();
        } else {
          throw new Error(result.error || 'Failed to publish content');
        }
      }
    } catch (error) {
      console.error('Error publishing content:', error);
      toast({
        title: "Publishing Failed",
        description: error.message || "Failed to publish content. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsPublishingNow(false);
    }
  };

  // Get minimum date (today)
  const today = new Date().toISOString().split('T')[0];
  const currentTime = new Date().toTimeString().slice(0, 5);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Schedule Content
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <Label htmlFor="scheduled-date">Date</Label>
            <Input
              id="scheduled-date"
              type="date"
              min={today}
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="scheduled-time">Time</Label>
            <Input
              id="scheduled-time"
              type="time"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
            />
          </div>
        </div>

        <div className="flex gap-2 pt-4">
          <Button
            onClick={handlePublishNow}
            disabled={isPublishingNow || isScheduling}
            className="flex-1"
          >
            {isPublishingNow ? (
              <>
                <Send className="w-4 h-4 mr-2 animate-spin" />
                Publishing...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Publish Now
              </>
            )}
          </Button>
          <Button
            onClick={handleSchedule}
            disabled={isScheduling || isPublishingNow}
            variant="outline"
            className="flex-1"
          >
            {isScheduling ? (
              <>
                <Clock className="w-4 h-4 mr-2 animate-spin" />
                Scheduling...
              </>
            ) : (
              <>
                <Clock className="w-4 h-4 mr-2" />
                Schedule
              </>
            )}
          </Button>
          <Button
            onClick={onCancel}
            variant="ghost"
            disabled={isScheduling || isPublishingNow}
          >
            Cancel
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
