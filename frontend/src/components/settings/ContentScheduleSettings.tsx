import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import DailySuggestionSchedule from "@/components/preferences/DailySuggestionSchedule";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { profileApi, UserPreferences } from "@/lib/profile-api";
import { useAuth } from "@/contexts/AuthContext";

export const ContentScheduleSettings: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [preferences, setPreferences] = useState<Partial<UserPreferences>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [timezones, setTimezones] = useState<string[]>([]);

  useEffect(() => {
    setTimezones(Intl.supportedValuesOf("timeZone"));
  }, []);

  useEffect(() => {
    if (user) {
      setIsLoading(true);
      profileApi
        .getUserPreferences()
        .then((data) => {
          const newPrefs = { ...data };
          if (!newPrefs.timezone) {
            newPrefs.timezone =
              Intl.DateTimeFormat().resolvedOptions().timeZone;
          }
          if (!newPrefs.preferred_posting_time) {
            // Set default to 9:00 AM
            newPrefs.preferred_posting_time = "09:00";
          }
          setPreferences(newPrefs);
        })
        .catch((err) => {
          console.error("Failed to get user preferences", err);
          toast({
            title: "Error",
            description: "Could not load schedule settings.",
            variant: "destructive",
          });
        })
        .finally(() => setIsLoading(false));
    }
  }, [user, toast]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await profileApi.updateUserPreferences({
        preferred_posting_time: preferences.preferred_posting_time,
        timezone: preferences.timezone,
      });
      toast({
        title: "Success",
        description: "Your settings have been saved.",
      });
    } catch (error) {
      toast({
        title: "Error saving settings",
        description: "Could not save your schedule settings.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const headerSection = (
    <CardHeader>
      <CardTitle>Schedule</CardTitle>
      <CardDescription></CardDescription>
    </CardHeader>
  );

  if (isLoading) {
    return (
      <Card>
        {headerSection}
        <CardContent>
          <Skeleton className="h-6 w-1/3" />
          <Skeleton className="h-4 w-1/2" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
          <Skeleton className="h-10 w-32" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      {headerSection}
      <CardContent className="space-y-4">
        {/* Daily Suggestions Schedule */}
        <DailySuggestionSchedule />

        <div className="w-full gap-4 mt-2">
          <div className="space-y-2">
            <Label htmlFor="posting-time">Preferred Posting Time</Label>
            <p className="text-sm text-gray-500">
              The default values in your datepicker when scheduling new posts.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                id="posting-time"
                type="time"
                value={preferences.preferred_posting_time || ""}
                onChange={(e) =>
                  setPreferences((p) => ({
                    ...p,
                    preferred_posting_time: e.target.value,
                  }))
                }
              />
              <Select
                value={preferences.timezone || ""}
                onValueChange={(value) =>
                  setPreferences((p) => ({ ...p, timezone: value }))
                }
              >
                <SelectTrigger id="timezone">
                  <SelectValue placeholder="Select a timezone" />
                </SelectTrigger>
                <SelectContent>
                  {timezones.map((tz) => (
                    <SelectItem key={tz} value={tz}>
                      {tz}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? "Saving..." : "Save"}
        </Button>
      </CardContent>
    </Card>
  );
};
