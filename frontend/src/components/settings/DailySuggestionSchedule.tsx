import React, { useEffect, useState } from "react";
import { scheduleApi } from "@/lib/schedule-api";
import type { DailySuggestionSchedule } from "@/lib/schedule-api";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Loader2 } from "lucide-react";

// Using browser-native time input provides a dynamic picker across platforms.
// We store the value as "HH:MM" 24-hour format.

const DailySuggestionSchedule: React.FC = () => {
  const { toast } = useToast();
  const [schedule, setSchedule] = useState<DailySuggestionSchedule | null>(
    null
  );
  const [timeValue, setTimeValue] = useState<string>("09:00");
  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);

  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const fetchSchedule = async () => {
    setLoading(true);
    try {
      const data = await scheduleApi.getSchedule();
      if (data) {
        setSchedule(data);
        // parse cron "M H * * *"
        const [minute, hour] = data.cron_expression.split(" ");
        setTimeValue(`${hour.padStart(2, "0")}:${minute.padStart(2, "0")}`);
      }
    } catch (e: unknown) {
      const err = e as Error;
      toast({
        title: "Error",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchedule();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const buildCron = (time: string) => {
    const [hour, minute] = time.split(":");
    return `${parseInt(minute, 10)} ${parseInt(hour, 10)} * * *`;
  };

  const handleSave = async () => {
    const cron = buildCron(timeValue);
    setSaving(true);
    try {
      let res: DailySuggestionSchedule;
      if (schedule) {
        res = await scheduleApi.updateSchedule({
          cron_expression: cron,
          timezone,
        });
      } else {
        res = await scheduleApi.createSchedule({
          cron_expression: cron,
          timezone,
        });
      }
      setSchedule(res);
      await fetchSchedule();
      toast({ title: "Schedule saved" });
    } catch (e: unknown) {
      const err = e as Error;
      toast({
        title: "Error",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!schedule) return;
    setSaving(true);
    try {
      await scheduleApi.deleteSchedule();
      setSchedule(null);
      toast({ title: "Schedule deleted" });
    } catch (e: unknown) {
      const err = e as Error;
      toast({
        title: "Error",
        description: err.message,
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading && !schedule) {
    return (
      <div className="space-y-4 bg-white">
        <Skeleton className="h-6 w-1/2" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-10 w-32" />
      </div>
    );
  }

  return (
    <div className="space-y-4 bg-white">
      <div className="flex flex-col">
        <div className="space-y-2">
          <Label htmlFor="suggestion-time">Daily Suggestions Time</Label>
          <p className="text-sm text-gray-500">
            The time of day when up to 5 daily suggested posts will be generated
            in the Drafts tab.
          </p>
          <p className="text-sm text-gray-500">
            Note: it may take up to 10 minutes for the suggestions to be
            populated.
          </p>

          <Input
            id="suggestion-time"
            type="time"
            value={timeValue}
            onChange={(e) => setTimeValue(e.target.value)}
          />
        </div>
        <div className="mt-4 flex space-x-2">
          <Button onClick={handleSave} disabled={loading || saving}>
            {saving && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
            {schedule
              ? saving
                ? "Updating..."
                : "Update"
              : saving
              ? "Scheduling..."
              : "Schedule"}
          </Button>
          {schedule && (
            <Button
              onClick={handleDelete}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
              disabled={loading || saving}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" /> Disabling...
                </>
              ) : (
                "Disable"
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default DailySuggestionSchedule;
