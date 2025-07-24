/**
 * React Query hooks for user topics
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { userTopicsApi, UserTopicCreate, UserTopicUpdate, BulkTopicCreateRequest } from "./user-topics-api";
import { useToast } from "@/hooks/use-toast";

// Query keys
export const userTopicsKeys = {
  all: ["user-topics"] as const,
  lists: () => [...userTopicsKeys.all, "list"] as const,
  list: (filters: string) => [...userTopicsKeys.lists(), { filters }] as const,
  details: () => [...userTopicsKeys.all, "detail"] as const,
  detail: (id: string) => [...userTopicsKeys.details(), id] as const,
  colors: () => [...userTopicsKeys.all, "colors"] as const,
};

/**
 * Hook to get all user topics
 */
export const useUserTopics = () => {
  return useQuery({
    queryKey: userTopicsKeys.lists(),
    queryFn: () => userTopicsApi.getUserTopics(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

/**
 * Hook to get topic colors mapping
 */
export const useTopicColors = () => {
  return useQuery({
    queryKey: userTopicsKeys.colors(),
    queryFn: () => userTopicsApi.getTopicColors(),
    staleTime: 10 * 60 * 1000, // 10 minutes - colors change less frequently
  });
};

/**
 * Hook to get a specific user topic
 */
export const useUserTopic = (topicId: string) => {
  return useQuery({
    queryKey: userTopicsKeys.detail(topicId),
    queryFn: () => userTopicsApi.getUserTopic(topicId),
    enabled: !!topicId,
  });
};

/**
 * Hook to create a new user topic
 */
export const useCreateUserTopic = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: UserTopicCreate) => userTopicsApi.createUserTopic(data),
    onSuccess: (newTopic) => {
      // Invalidate and refetch user topics list
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.lists() });
      // Invalidate colors cache
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.colors() });
      
      toast({
        title: "Topic created",
        description: `Topic "${newTopic.topic}" has been created with color ${newTopic.color}`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create topic",
        description: error.message || "An error occurred while creating the topic",
        variant: "destructive",
      });
    },
  });
};

/**
 * Hook to bulk create user topics
 */
export const useBulkCreateTopics = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: BulkTopicCreateRequest) => userTopicsApi.bulkCreateTopics(data),
    onSuccess: (newTopics) => {
      // Invalidate and refetch user topics list
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.lists() });
      // Invalidate colors cache
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.colors() });
      
      if (newTopics.length > 0) {
        toast({
          title: "Topics created",
          description: `${newTopics.length} new topics have been created`,
        });
      }
    },
    onError: (error: any) => {
      toast({
        title: "Failed to create topics",
        description: error.message || "An error occurred while creating topics",
        variant: "destructive",
      });
    },
  });
};

/**
 * Hook to sync topics from posts
 */
export const useSyncTopicsFromPosts = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: () => userTopicsApi.syncTopicsFromPosts(),
    onSuccess: (newTopics) => {
      // Invalidate and refetch user topics list
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.lists() });
      // Invalidate colors cache
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.colors() });
      
      if (newTopics.length > 0) {
        toast({
          title: "Topics synced",
          description: `${newTopics.length} topics have been synced from your posts`,
        });
      } else {
        toast({
          title: "Topics up to date",
          description: "All topics from your posts are already available",
        });
      }
    },
    onError: (error: any) => {
      toast({
        title: "Failed to sync topics",
        description: error.message || "An error occurred while syncing topics",
        variant: "destructive",
      });
    },
  });
};

/**
 * Hook to update a user topic
 */
export const useUpdateUserTopic = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ topicId, data }: { topicId: string; data: UserTopicUpdate }) =>
      userTopicsApi.updateUserTopic(topicId, data),
    onSuccess: (updatedTopic) => {
      // Invalidate and refetch user topics list
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.lists() });
      // Invalidate colors cache
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.colors() });
      // Update the specific topic in cache
      queryClient.setQueryData(
        userTopicsKeys.detail(updatedTopic.id),
        updatedTopic
      );
      
      toast({
        title: "Topic updated",
        description: `Topic "${updatedTopic.topic}" has been updated`,
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to update topic",
        description: error.message || "An error occurred while updating the topic",
        variant: "destructive",
      });
    },
  });
};

/**
 * Hook to delete a user topic
 */
export const useDeleteUserTopic = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (topicId: string) => userTopicsApi.deleteUserTopic(topicId),
    onSuccess: (_, topicId) => {
      // Invalidate and refetch user topics list
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.lists() });
      // Invalidate colors cache
      queryClient.invalidateQueries({ queryKey: userTopicsKeys.colors() });
      // Remove the specific topic from cache
      queryClient.removeQueries({ queryKey: userTopicsKeys.detail(topicId) });
      
      toast({
        title: "Topic deleted",
        description: "The topic has been successfully deleted",
      });
    },
    onError: (error: any) => {
      toast({
        title: "Failed to delete topic",
        description: error.message || "An error occurred while deleting the topic",
        variant: "destructive",
      });
    },
  });
};
