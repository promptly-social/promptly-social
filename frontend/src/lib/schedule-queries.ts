import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  scheduleApi,
  type DailySuggestionSchedule,
  type DailySuggestionScheduleCreate,
  type DailySuggestionScheduleUpdate,
} from "./schedule-api";

export const scheduleKeys = {
  dailySuggestions: ["dailySuggestionSchedule"] as const,
};

// ------------------ Query ------------------
export const useDailySuggestionSchedule = () =>
  useQuery<DailySuggestionSchedule | null, Error>({
    queryKey: scheduleKeys.dailySuggestions,
    queryFn: () => scheduleApi.getSchedule(),
    staleTime: 10 * 60 * 1000,
  });

// ------------------ Mutations --------------
export const useCreateDailySuggestionSchedule = () => {
  const qc = useQueryClient();
  return useMutation<
    DailySuggestionSchedule,
    Error,
    DailySuggestionScheduleCreate
  >({
    mutationFn: (data) => scheduleApi.createSchedule(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: scheduleKeys.dailySuggestions });
    },
  });
};

export const useUpdateDailySuggestionSchedule = () => {
  const qc = useQueryClient();
  return useMutation<
    DailySuggestionSchedule,
    Error,
    DailySuggestionScheduleUpdate
  >({
    mutationFn: (data) => scheduleApi.updateSchedule(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: scheduleKeys.dailySuggestions });
    },
  });
};

export const useDeleteDailySuggestionSchedule = () => {
  const qc = useQueryClient();
  return useMutation<void, Error, void>({
    mutationFn: () => scheduleApi.deleteSchedule(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: scheduleKeys.dailySuggestions });
    },
  });
};
