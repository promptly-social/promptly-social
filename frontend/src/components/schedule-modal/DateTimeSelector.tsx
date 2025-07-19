import React from "react";
import { Calendar } from "@/components/ui/calendar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Clock } from "lucide-react";

interface DateTimeSelectorProps {
  selectedDate: Date;
  selectedHour: string;
  selectedMinute: string;
  onDateSelect: (date: Date) => void;
  onHourChange: (hour: string) => void;
  onMinuteChange: (minute: string) => void;
  availableHours: string[];
  availableMinutes: string[];
  datesWithScheduledPosts: Date[];
  onMonthChange: (month: Date) => void;
  isDateDisabled: (date: Date) => boolean;
}

export const DateTimeSelector: React.FC<DateTimeSelectorProps> = ({
  selectedDate,
  selectedHour,
  selectedMinute,
  onDateSelect,
  onHourChange,
  onMinuteChange,
  availableHours,
  availableMinutes,
  datesWithScheduledPosts,
  onMonthChange,
  isDateDisabled,
}) => {
  return (
    <div className="space-y-4">
      <h3 className="font-medium mb-3 flex items-center gap-2">
        <Clock className="w-4 h-4" />
        Select New Date & Time
      </h3>
      
      <div className="space-y-3">
        <div className="flex justify-center">
          <Calendar
            mode="single"
            selected={selectedDate}
            onSelect={(date) => date && onDateSelect(date)}
            disabled={isDateDisabled}
            modifiers={{
              hasScheduledPost: datesWithScheduledPosts,
            }}
            modifiersClassNames={{
              hasScheduledPost:
                'relative after:absolute after:top-1 after:right-1 after:w-2 after:h-2 after:bg-green-500 after:rounded-full after:content-[""]',
            }}
            className="rounded-md border"
            onMonthChange={onMonthChange}
          />
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="text-xs font-medium mb-1 block">
              Hour
            </label>
            <Select
              value={selectedHour}
              onValueChange={onHourChange}
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableHours.map((hour) => (
                  <SelectItem key={hour} value={hour}>
                    {hour}:00
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-xs font-medium mb-1 block">
              Minute
            </label>
            <Select
              value={selectedMinute}
              onValueChange={onMinuteChange}
            >
              <SelectTrigger className="h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableMinutes.map((minute) => (
                  <SelectItem key={minute} value={minute}>
                    :{minute}
                  </SelectItem>
                ))}
                {availableMinutes.length === 0 && (
                  <SelectItem value="" disabled>
                    No valid times available
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>
    </div>
  );
};
