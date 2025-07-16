import React, { createContext, useContext, useMemo } from "react";
import { useAuth } from "./AuthContext";
import {
  useUserPreferences,
  useSocialConnections,
  profileKeys,
} from "@/lib/profile-queries";
import { useQueryClient } from "@tanstack/react-query";
import { UserPreferences, SocialConnection } from "@/lib/profile-api";

interface ProfileContextType {
  userPreferences: UserPreferences | null;
  socialConnections: SocialConnection[];
  linkedinConnection: SocialConnection | null;
  loading: boolean;
  refreshProfile: () => Promise<void>;
}

const ProfileContext = createContext<ProfileContextType | null>(null);

export const useProfile = () => {
  const context = useContext(ProfileContext);
  if (!context) {
    throw new Error("useProfile must be used within a ProfileProvider");
  }
  return context;
};

export const ProfileProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Queries will automatically be disabled when `user` is null
  const { data: userPreferences, isLoading: isPrefsLoading } =
    useUserPreferences(!!user);

  const { data: socialConnections = [], isLoading: isConnsLoading } =
    useSocialConnections(!!user);

  const linkedinConnection = useMemo(
    () => socialConnections.find((c) => c.platform === "linkedin") || null,
    [socialConnections]
  );

  const loading = isPrefsLoading || isConnsLoading;

  const refreshProfile = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: profileKeys.preferences }),
      queryClient.invalidateQueries({ queryKey: profileKeys.connections }),
    ]);
  };

  const value = {
    userPreferences: userPreferences ?? null,
    socialConnections,
    linkedinConnection,
    loading,
    refreshProfile,
  } as const;

  return (
    <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
  );
};
