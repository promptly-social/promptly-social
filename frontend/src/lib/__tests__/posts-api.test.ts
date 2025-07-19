import { describe, it, expect, beforeEach, vi } from "vitest";
import { postsApi } from "../posts-api";
import { apiClient } from "../auth-api";
import { vi } from "vitest";

// Mock the API client
vi.mock("../auth-api", () => ({
  apiClient: {
    request: vi.fn(),
  },
}));

describe("PostsAPI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("generateImagePrompt", () => {
    it("calls the correct endpoint with post content", async () => {
      const mockResponse = { imagePrompt: "Generated prompt for the image" };
      (apiClient.request as any).mockResolvedValue(mockResponse);

      const result = await postsApi.generateImagePrompt("Test post content");

      expect(apiClient.request).toHaveBeenCalledWith("/posts/image-prompt", {
        method: "POST",
        body: JSON.stringify({ postContent: "Test post content" }),
      });
      expect(result).toEqual(mockResponse);
    });

    it("handles API errors", async () => {
      const error = new Error("API Error");
      (apiClient.request as any).mockRejectedValue(error);

      await expect(
        postsApi.generateImagePrompt("Test content")
      ).rejects.toThrow("API Error");
    });
  });

  describe("getPostMedia", () => {
    it("fetches media for a specific post", async () => {
      const mockMedia = [
        {
          id: "1",
          post_id: "post-1",
          user_id: "user-1",
          media_type: "image",
          file_name: "test.jpg",
          gcs_url: "https://signed-url.com/test.jpg",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
      ];
      (apiClient.request as any).mockResolvedValue(mockMedia);

      const result = await postsApi.getPostMedia("post-1");

      expect(apiClient.request).toHaveBeenCalledWith("/posts/post-1/media", {
        method: "GET",
      });
      expect(result).toEqual(mockMedia);
    });

    it("handles empty media response", async () => {
      (apiClient.request as any).mockResolvedValue([]);

      const result = await postsApi.getPostMedia("post-1");

      expect(result).toEqual([]);
    });
  });

  describe("uploadPostMedia", () => {
    it("uploads media files for a post", async () => {
      const mockFiles = [
        new File(["test"], "test.jpg", { type: "image/jpeg" }),
        new File(["test2"], "test2.png", { type: "image/png" }),
      ];
      const mockResponse = [
        {
          id: "1",
          post_id: "post-1",
          user_id: "user-1",
          media_type: "image",
          file_name: "test.jpg",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
      ];
      (apiClient.request as any).mockResolvedValue(mockResponse);

      const result = await postsApi.uploadPostMedia("post-1", mockFiles);

      expect(apiClient.request).toHaveBeenCalledWith("/posts/post-1/media", {
        method: "POST",
        body: expect.any(FormData),
      });
      expect(result).toEqual(mockResponse);
    });

    it("handles empty file array", async () => {
      (apiClient.request as any).mockResolvedValue([]);

      const result = await postsApi.uploadPostMedia("post-1", []);

      const expectedFormData = new FormData();
      expect(apiClient.request).toHaveBeenCalledWith("/posts/post-1/media", {
        method: "POST",
        body: expect.any(FormData),
      });
      expect(result).toEqual([]);
    });
  });

  describe("postNow", () => {
    it("publishes a post immediately", async () => {
      const mockResponse = {
        message: "Post published successfully",
        details: { linkedin_id: "12345" },
      };
      (apiClient.request as any).mockResolvedValue(mockResponse);

      const result = await postsApi.postNow("post-1");

      expect(apiClient.request).toHaveBeenCalledWith(
        "/posts/post-1/publish?platform=linkedin",
        {
          method: "POST",
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it("handles publishing errors", async () => {
      const error = new Error("Publishing failed");
      (apiClient.request as any).mockRejectedValue(error);

      await expect(postsApi.postNow("post-1")).rejects.toThrow(
        "Publishing failed"
      );
    });
  });

  describe("getPostCounts", () => {
    it("fetches post counts by status", async () => {
      const mockCounts = {
        drafts: 5,
        scheduled: 3,
        posted: 10,
      };
      (apiClient.request as any).mockResolvedValue(mockCounts);

      const result = await postsApi.getPostCounts();

      expect(apiClient.request).toHaveBeenCalledWith("/posts/counts");
      expect(result).toEqual(mockCounts);
    });
  });

  describe("getPosts", () => {
    it("fetches posts with default parameters", async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        size: 20,
        total_pages: 0,
      };
      (apiClient.request as any).mockResolvedValue(mockResponse);

      const result = await postsApi.getPosts();

      expect(apiClient.request).toHaveBeenCalledWith("/posts/");
      expect(result).toEqual(mockResponse);
    });

    it("fetches posts with custom parameters", async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 2,
        size: 10,
        total_pages: 0,
      };
      (apiClient.request as unknown).mockResolvedValue(mockResponse);

      const params = {
        status: ["draft", "scheduled"],
        page: 2,
        size: 10,
        platform: "linkedin",
      };

      const result = await postsApi.getPosts(params);

      expect(apiClient.request).toHaveBeenCalledWith(
        "/posts/?platform=linkedin&status=draft&status=scheduled&page=2&size=10"
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getPostsForCalendar", () => {
    it("fetches calendar posts for date range", async () => {
      const mockPosts = [
        {
          id: "1",
          content: "Scheduled post",
          status: "scheduled",
          scheduled_at: "2024-01-15T10:00:00Z",
          posted_at: null,
        },
        {
          id: "2",
          content: "Posted post",
          status: "posted",
          scheduled_at: null,
          posted_at: "2024-01-20T14:00:00Z",
        },
      ];
      const mockResponse = {
        items: mockPosts,
        total: 2,
        page: 1,
        size: 50,
        total_pages: 1,
      };
      (apiClient.request as any).mockResolvedValue(mockResponse);

      const result = await postsApi.getPostsForCalendar(
        "2024-01-01",
        "2024-01-31"
      );

      expect(apiClient.request).toHaveBeenCalledWith(
        "/posts/?status=scheduled&status=posted&after_date=2024-01-01&before_date=2024-01-31&size=50&order_by=scheduled_at%2Cposted_at&order_direction=asc"
      );
      expect(result).toEqual(mockPosts);
    });

    it("returns empty array on API error", async () => {
      const error = new Error("API Error");
      (apiClient.request as any).mockRejectedValue(error);

      // Mock console.error to avoid test output noise
      const consoleSpy = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      const result = await postsApi.getPostsForCalendar(
        "2024-01-01",
        "2024-01-31"
      );

      expect(result).toEqual([]);
      expect(consoleSpy).toHaveBeenCalledWith(
        "Failed to fetch calendar posts:",
        error
      );

      consoleSpy.mockRestore();
    });

    it("handles empty response gracefully", async () => {
      const mockResponse = {
        items: [],
        total: 0,
        page: 1,
        size: 1000,
        total_pages: 0,
      };
      (apiClient.request as unknown).mockResolvedValue(mockResponse);

      const result = await postsApi.getPostsForCalendar(
        "2024-01-01",
        "2024-01-31"
      );

      expect(result).toEqual([]);
    });
  });
});
