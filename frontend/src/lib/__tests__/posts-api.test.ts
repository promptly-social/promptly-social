import { postsApi } from '../posts-api';

// Mock the apiClient
jest.mock('../auth-api', () => ({
  apiClient: {
    request: jest.fn(),
  },
}));

import { apiClient } from '../auth-api';

const mockApiClient = apiClient as jest.Mocked<typeof apiClient>;

describe('PostsAPI', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('postNow', () => {
    it('calls the correct endpoint with POST method', async () => {
      const mockResponse = { message: 'Post published successfully', details: {} };
      mockApiClient.request.mockResolvedValue(mockResponse);

      const result = await postsApi.postNow('test-post-id');

      expect(mockApiClient.request).toHaveBeenCalledWith(
        '/posts/test-post-id/publish?platform=linkedin',
        {
          method: 'POST',
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it('handles API errors correctly', async () => {
      const mockError = new Error('API Error');
      mockApiClient.request.mockRejectedValue(mockError);

      await expect(postsApi.postNow('test-post-id')).rejects.toThrow('API Error');
    });
  });

  describe('publishPost', () => {
    it('calls the correct endpoint with platform parameter', async () => {
      const mockResponse = { message: 'Post published successfully', details: {} };
      mockApiClient.request.mockResolvedValue(mockResponse);

      const result = await postsApi.publishPost('test-post-id', 'linkedin');

      expect(mockApiClient.request).toHaveBeenCalledWith(
        '/posts/test-post-id/publish?platform=linkedin',
        {
          method: 'POST',
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });
});