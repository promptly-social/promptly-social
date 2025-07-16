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
import { useQuery, useQueryClient } from "@tanstack/react-query";
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
import { Loader2 } from "lucide-react";

export const ContentScheduleSettings: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [preferences, setPreferences] = useState<Partial<UserPreferences>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [timezones, setTimezones] = useState<string[]>([]);

  // React Query --------------------------------------------------------
  const queryClient = useQueryClient();
  const {
    data: fetchedPreferences,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["userPreferences"],
    queryFn: profileApi.getUserPreferences,
    enabled: !!user, // Only run once user is available
    staleTime: 1000 * 60 * 60, // 1 hour
  });

  // Show load error (once)
  useEffect(() => {
    if (error) {
      toast({
        title: "Error",
        description: "Could not load schedule settings.",
        variant: "destructive",
      });
    }
  }, [error, toast]);

  // Sync fetched preferences into local editable state once loaded
  useEffect(() => {
    if (fetchedPreferences) {
      const newPrefs = { ...fetchedPreferences };
      if (!newPrefs.timezone) {
        newPrefs.timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      }
      if (!newPrefs.preferred_posting_time) {
        newPrefs.preferred_posting_time = "09:00";
      }
      setPreferences(newPrefs);
    }
  }, [fetchedPreferences]);

  useEffect(() => {
    setTimezones(Intl.supportedValuesOf("timeZone"));
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await profileApi.updateUserPreferences({
        preferred_posting_time: preferences.preferred_posting_time,
        timezone: preferences.timezone,
      });

      // Refresh cached preferences so other components stay in sync
      await queryClient.invalidateQueries({ queryKey: ["userPreferences"] });

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

  return (
    <Card>
      {headerSection}
      <CardContent className="space-y-4">
        {/* Daily Suggestions Schedule */}
        {isLoading ? (
          <Skeleton className="h-8 w-full rounded-md" />
        ) : (
          <DailySuggestionSchedule />
        )}

        <div className="w-full gap-4 mt-2">
          <div className="space-y-2">
            <Label htmlFor="posting-time">Preferred Posting Time</Label>
            <p className="text-sm text-gray-500">
              The default values in your datepicker when scheduling new posts.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {isLoading ? (
                <Skeleton className="h-10 w-full" />
              ) : (
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
              )}
              {isLoading ? (
                <Skeleton className="h-10 w-full" />
              ) : (
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
              )}
            </div>
          </div>
        </div>
        <Button onClick={handleSave} disabled={isSaving || isLoading}>
          {(isSaving || isLoading) && (
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
          )}
          {isSaving ? "Saving..." : "Save"}
        </Button>
      </CardContent>
    </Card>
  );
};
