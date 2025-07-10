import React, {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
} from "react";
import { useAuth } from "./AuthContext";
import {
  profileApi,
  UserPreferences,
  SocialConnection,
} from "@/lib/profile-api";

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
  const [userPreferences, setUserPreferences] =
    useState<UserPreferences | null>(null);
  const [socialConnections, setSocialConnections] = useState<
    SocialConnection[]
  >([]);
  const [linkedinConnection, setLinkedinConnection] =
    useState<SocialConnection | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfileData = useCallback(async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const [prefs, connections] = await Promise.all([
        profileApi.getUserPreferences(),
        profileApi.getSocialConnections(),
      ]);
      setUserPreferences(prefs);
      setSocialConnections(connections);
      const linkedinConn =
        connections.find((c) => c.platform === "linkedin") || null;
      setLinkedinConnection(linkedinConn);
    } catch (error) {
      console.error("Failed to fetch profile data:", error);
      // Handle error appropriately, maybe with a toast notification
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchProfileData();
  }, [fetchProfileData]);

  const value = {
    userPreferences,
    socialConnections,
    linkedinConnection,
    loading,
    refreshProfile: fetchProfileData,
  };

  return (
    <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
  );
};
