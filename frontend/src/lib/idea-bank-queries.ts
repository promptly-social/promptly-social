import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ideaBankApi,
  type IdeaBankFilters,
  type IdeaBankListResponse,
  type IdeaBankWithPostsResponse,
  type IdeaBankCreate,
  type IdeaBankUpdate,
  type IdeaBank,
  type IdeaBankData,
  type SuggestedPost,
} from "./idea-bank-api";

export const ideaBankKeys = {
  all: ["ideaBanks"] as const,
  list: (filters: IdeaBankFilters | undefined) =>
    ["ideaBanks", filters] as const,
  withPosts: (filters: IdeaBankFilters | undefined) =>
    ["ideaBanks", "withPosts", filters] as const,
  detail: (id: string) => ["ideaBank", id] as const,
  detailWithPost: (id: string) => ["ideaBank", id, "withPost"] as const,
};

// ----------------------------- Queries -----------------------------
export const useIdeaBanks = (filters?: IdeaBankFilters) =>
  useQuery<IdeaBankListResponse, Error>({
    queryKey: ideaBankKeys.list(filters),
    queryFn: () => ideaBankApi.list(filters),
    staleTime: 5 * 60 * 1000,
  });

export const useIdeaBanksWithPosts = (filters?: IdeaBankFilters) =>
  useQuery<IdeaBankWithPostsResponse, Error>({
    queryKey: ideaBankKeys.withPosts(filters),
    queryFn: () => ideaBankApi.listWithPosts(filters),
    staleTime: 5 * 60 * 1000,
  });

export const useIdeaBank = (id?: string, enabled = true) =>
  useQuery<IdeaBank, Error>({
    queryKey: ideaBankKeys.detail(id || ""),
    queryFn: () => {
      if (!id) throw new Error("Missing id");
      return ideaBankApi.get(id);
    },
    enabled: !!id && enabled,
    staleTime: 10 * 60 * 1000,
  });

export const useIdeaBankWithPost = (id?: string, enabled = true) =>
  useQuery<{ idea_bank: IdeaBank; latest_post?: SuggestedPost }, Error>({
    queryKey: ideaBankKeys.detailWithPost(id || ""),
    queryFn: () => {
      if (!id) throw new Error("Missing id");
      return ideaBankApi.getWithPost(id);
    },
    enabled: !!id && enabled,
    staleTime: 10 * 60 * 1000,
  });

// --------------------------- Mutations -----------------------------

export const useCreateIdeaBank = () => {
  const qc = useQueryClient();
  return useMutation<IdeaBank, Error, IdeaBankCreate>({
    mutationFn: (data) => ideaBankApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ideaBankKeys.all });
    },
  });
};

export const useUpdateIdeaBank = () => {
  const qc = useQueryClient();
  return useMutation<IdeaBank, Error, { id: string; data: IdeaBankUpdate }>({
    mutationFn: ({ id, data }) => ideaBankApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ideaBankKeys.all });
      // also invalidate specific detail queries
      qc.invalidateQueries();
    },
  });
};

export const useDeleteIdeaBank = () => {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: (id) => ideaBankApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ideaBankKeys.all });
    },
  });
};

// --------------------------- New Hooks for Inspiration Display -----------------------------

export const useIdeaBankData = (id?: string, enabled = true) =>
  useQuery<IdeaBankData, Error>({
    queryKey: ["ideaBankData", id],
    queryFn: () => {
      if (!id) throw new Error("Missing id");
      return ideaBankApi.getIdeaBank(id);
    },
    enabled: !!id && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

export const useBatchIdeaBanks = (ids: string[], enabled = true) =>
  useQuery<Record<string, IdeaBankData>, Error>({
    queryKey: ["batchIdeaBanks", ids.sort()], // Sort for consistent cache key
    queryFn: () => ideaBankApi.getIdeaBanksByIds(ids),
    enabled: ids.length > 0 && enabled,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
