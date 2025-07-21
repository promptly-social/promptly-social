/**
 * User Topics Context for managing topic colors and caching across the app
 */

import React, { createContext, useContext, useMemo } from "react";
import { useTopicColors, useUserTopics } from "@/lib/user-topics-queries";
import { UserTopic, TopicColorMap } from "@/lib/user-topics-api";

interface UserTopicsContextType {
  topics: UserTopic[];
  topicColors: Record<string, string>;
  isLoading: boolean;
  error: Error | null;
  getTopicColor: (topic: string) => string | undefined;
  refetchTopics: () => void;
  refetchColors: () => void;
}

const UserTopicsContext = createContext<UserTopicsContextType | undefined>(undefined);

interface UserTopicsProviderProps {
  children: React.ReactNode;
}

export const UserTopicsProvider: React.FC<UserTopicsProviderProps> = ({ children }) => {
  const {
    data: topicsData,
    isLoading: topicsLoading,
    error: topicsError,
    refetch: refetchTopics,
  } = useUserTopics();

  const {
    data: colorsData,
    isLoading: colorsLoading,
    error: colorsError,
    refetch: refetchColors,
  } = useTopicColors();

  const contextValue = useMemo(() => {
    const topics = topicsData?.topics || [];
    const topicColors = colorsData?.topic_colors?.reduce((acc, item: TopicColorMap) => {
      acc[item.topic] = item.color;
      return acc;
    }, {} as Record<string, string>) || {};

    const getTopicColor = (topic: string): string | undefined => {
      return topicColors[topic];
    };

    return {
      topics,
      topicColors,
      isLoading: topicsLoading || colorsLoading,
      error: topicsError || colorsError,
      getTopicColor,
      refetchTopics,
      refetchColors,
    };
  }, [topicsData, colorsData, topicsLoading, colorsLoading, topicsError, colorsError, refetchTopics, refetchColors]);

  return (
    <UserTopicsContext.Provider value={contextValue}>
      {children}
    </UserTopicsContext.Provider>
  );
};

export const useUserTopicsContext = (): UserTopicsContextType => {
  const context = useContext(UserTopicsContext);
  if (context === undefined) {
    throw new Error("useUserTopicsContext must be used within a UserTopicsProvider");
  }
  return context;
};
