import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  profileApi,
  type UserPreferences,
  type SocialConnection,
  type UserPreferencesUpdate,
  type SocialConnectionUpdate,
} from "./profile-api";

export const profileKeys = {
  root: ["profile"] as const,
  preferences: ["profile", "preferences"] as const,
  connections: ["profile", "connections"] as const,
};

// -------------------- Queries --------------------
export const useUserPreferences = (enabled: boolean = true) =>
  useQuery<UserPreferences, Error>({
    queryKey: profileKeys.preferences,
    queryFn: () => profileApi.getUserPreferences(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled,
  });

export const useSocialConnections = (enabled: boolean = true) =>
  useQuery<SocialConnection[], Error>({
    queryKey: profileKeys.connections,
    queryFn: () => profileApi.getSocialConnections(),
    staleTime: 5 * 60 * 1000,
    enabled,
  });

// -------------------- Mutations ------------------
export const useUpdateUserPreferences = () => {
  const qc = useQueryClient();
  return useMutation<UserPreferences, Error, UserPreferencesUpdate>({
    mutationFn: (data) => profileApi.updateUserPreferences(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: profileKeys.preferences });
    },
  });
};

export const useUpdateSocialConnection = (platform: string) => {
  const qc = useQueryClient();
  return useMutation<SocialConnection, Error, SocialConnectionUpdate>({
    mutationFn: (data) => profileApi.updateSocialConnection(platform, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: profileKeys.connections });
    },
  });
};
