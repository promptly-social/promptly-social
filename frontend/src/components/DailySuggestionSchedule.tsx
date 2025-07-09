import React, { useEffect, useState } from "react";
import { scheduleApi } from "@/lib/schedule-api";
import type { DailySuggestionSchedule } from "@/lib/schedule-api";
import { useToast } from "@/hooks/use-toast";

// Using browser-native time input provides a dynamic picker across platforms.
// We store the value as "HH:MM" 24-hour format.

const DailySuggestionSchedule: React.FC = () => {
  const { toast } = useToast();
  const [schedule, setSchedule] = useState<DailySuggestionSchedule | null>(
    null
  );
  const [timeValue, setTimeValue] = useState<string>("09:00");
  const [loading, setLoading] = useState<boolean>(false);

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
  }, []);

  const buildCron = (time: string) => {
    const [hour, minute] = time.split(":");
    return `${parseInt(minute, 10)} ${parseInt(hour, 10)} * * *`;
  };

  const handleSave = async () => {
    const cron = buildCron(timeValue);
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
    }
  };

  const handleDelete = async () => {
    if (!schedule) return;
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
    }
  };

  return (
    <div className="border rounded-lg p-4 space-y-4 bg-white">
      <h3 className="text-lg font-semibold">Daily Suggestions Schedule</h3>
      <p className="text-sm text-gray-500">
        Pick a time you would like to receive your generated suggestions each
        day.
      </p>

      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Time (your timezone)
          </label>
          <input
            type="time"
            value={timeValue}
            onChange={(e) => setTimeValue(e.target.value)}
            className="border rounded-md px-3 py-2"
          />
        </div>
        <div className="mt-4 sm:mt-7 flex gap-2">
          <button
            onClick={handleSave}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50"
            disabled={loading}
          >
            {schedule ? "Update" : "Set"}
          </button>
          {schedule && (
            <button
              onClick={handleDelete}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50"
              disabled={loading}
            >
              Delete
            </button>
          )}
        </div>
      </div>

      {schedule && (
        <p className="text-xs text-gray-400">
          Current schedule: daily at {timeValue} ({timezone})
        </p>
      )}
    </div>
  );
};

export default DailySuggestionSchedule;
