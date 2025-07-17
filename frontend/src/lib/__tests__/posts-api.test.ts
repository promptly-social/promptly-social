import { postsApi } from "../posts-api";
import { apiClient } from "../auth-api";

// Mock the API client
jest.mock("../auth-api", () => ({
  apiClient: {
    request: jest.fn(),
  },
}));

describe("PostsAPI", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("generateImagePrompt", () => {
    it("calls the correct endpoint with post content", async () => {
      const mockResponse = { imagePrompt: "Generated prompt for the image" };
      (apiClient.request as jest.Mock).mockResolvedValue(mockResponse);

      const result = await postsApi.generateImagePrompt("Test post content");

      expect(apiClient.request).toHaveBeenCalledWith("/posts/image-prompt", {
        method: "POST",
        body: JSON.stringify({ postContent: "Test post content" }),
      });
      expect(result).toEqual(mockResponse);
    });

    it("handles API errors", async () => {
      const error = new Error("API Error");
      (apiClient.request as jest.Mock).mockRejectedValue(error);

      await expect(postsApi.generateImagePrompt("Test content")).rejects.toThrow("API Error");
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
      (apiClient.request as jest.Mock).mockResolvedValue(mockMedia);

      const result = await postsApi.getPostMedia("post-1");

      expect(apiClient.request).toHaveBeenCalledWith("/posts/post-1/media", {
        method: "GET",
      });
      expect(result).toEqual(mockMedia);
    });

    it("handles empty media response", async () => {
      (apiClient.request as jest.Mock).mockResolvedValue([]);

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
      (apiClient.request as jest.Mock).mockResolvedValue(mockResponse);

      const result = await postsApi.uploadPostMedia("post-1", mockFiles);

      expect(apiClient.request).toHaveBeenCalledWith("/posts/post-1/media", {
        method: "POST",
        body: expect.any(FormData),
      });
      expect(result).toEqual(mockResponse);
    });

    it("handles empty file array", async () => {
      (apiClient.request as jest.Mock).mockResolvedValue([]);

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
      (apiClient.request as jest.Mock).mockResolvedValue(mockResponse);

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
      (apiClient.request as jest.Mock).mockRejectedValue(error);

      await expect(postsApi.postNow("post-1")).rejects.toThrow("Publishing failed");
    });
  });

  describe("getPostCounts", () => {
    it("fetches post counts by status", async () => {
      const mockCounts = {
        drafts: 5,
        scheduled: 3,
        posted: 10,
      };
      (apiClient.request as jest.Mock).mockResolvedValue(mockCounts);

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
      (apiClient.request as jest.Mock).mockResolvedValue(mockResponse);

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
      (apiClient.request as jest.Mock).mockResolvedValue(mockResponse);

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
});