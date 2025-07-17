import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PostCard } from '../PostCard';
import { Post } from '@/types/posts';
import { postsApi } from '@/lib/posts-api';

// Mock the posts API
jest.mock('@/lib/posts-api', () => ({
  postsApi: {
    postNow: jest.fn(),
    updatePost: jest.fn(),
    getPostMedia: jest.fn(),
    uploadPostMedia: jest.fn(),
    deletePostMedia: jest.fn(),
    dismissPost: jest.fn(),
    submitFeedback: jest.fn(),
    schedulePost: jest.fn(),
  },
}));

// Mock the toast hook
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock the post editor hook
jest.mock('@/hooks/usePostEditor', () => ({
  usePostEditor: () => ({
    content: 'Test content',
    topics: ['test'],
    topicInput: '',
    articleUrl: '',
    existingMedia: [],
    mediaFiles: [],
    mediaPreviews: [],
    setContent: jest.fn(),
    setTopicInput: jest.fn(),
    addTopic: jest.fn(),
    removeTopic: jest.fn(),
    setArticleUrl: jest.fn(),
    handleMediaFileChange: jest.fn(),
    removeExistingMedia: jest.fn(),
    removeNewMedia: jest.fn(),
    reset: jest.fn(),
  }),
}));

// Mock all the child components
jest.mock('../components/PostCardHeader', () => ({
  PostCardHeader: () => <div data-testid="post-header">Header</div>,
}));

jest.mock('../components/PostContent', () => ({
  PostContent: () => <div data-testid="post-content">Content</div>,
}));

jest.mock('../components/PostCardMeta', () => ({
  PostCardMeta: () => <div data-testid="post-meta">Meta</div>,
}));

jest.mock('../components/PostCardTopics', () => ({
  PostCardTopics: () => <div data-testid="post-topics">Topics</div>,
}));

jest.mock('../components/PostSharingError', () => ({
  PostSharingError: ({ hasError }: { hasError: boolean }) => 
    hasError ? <div data-testid="sharing-error">Error</div> : null,
}));

jest.mock('../components/PostCardActions', () => ({
  PostCardActions: ({ onPostNow, post }: any) => (
    <button onClick={() => onPostNow(post)} data-testid="post-now-button">
      Post Now
    </button>
  ),
}));

// Mock UI components
jest.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div data-testid="card-content">{children}</div>,
}));

jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick }: any) => <button onClick={onClick}>{children}</button>,
}));

jest.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick }: any) => <button onClick={onClick}>{children}</button>,
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockPost: Post = {
  id: '1',
  user_id: '1',
  content: 'Test post content',
  platform: 'linkedin',
  topics: ['test'],
  status: 'suggested',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  media: [],
};

const mockPostsApi = postsApi as jest.Mocked<typeof postsApi>;

describe('PostCard Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockPostsApi.getPostMedia.mockResolvedValue([]);
  });

  it('renders post card with sharing error indicator when post has sharing_error', () => {
    const postWithError = { ...mockPost, sharing_error: 'Test error' };
    render(<PostCard post={postWithError} />);
    
    expect(screen.getByTestId('sharing-error')).toBeInTheDocument();
  });

  it('does not render sharing error indicator when post has no sharing_error', () => {
    render(<PostCard post={mockPost} />);
    
    expect(screen.queryByTestId('sharing-error')).not.toBeInTheDocument();
  });

  it('calls postNow API when Post Now button is clicked', async () => {
    mockPostsApi.postNow.mockResolvedValue({ message: 'Success', details: {} });
    const mockOnPostUpdate = jest.fn();
    
    render(<PostCard post={mockPost} onPostUpdate={mockOnPostUpdate} />);
    
    fireEvent.click(screen.getByTestId('post-now-button'));
    
    await waitFor(() => {
      expect(mockPostsApi.postNow).toHaveBeenCalledWith(mockPost.id);
    });
    
    expect(mockOnPostUpdate).toHaveBeenCalled();
  });

  it('handles postNow API error gracefully', async () => {
    mockPostsApi.postNow.mockRejectedValue(new Error('API Error'));
    const mockOnPostUpdate = jest.fn();
    
    render(<PostCard post={mockPost} onPostUpdate={mockOnPostUpdate} />);
    
    fireEvent.click(screen.getByTestId('post-now-button'));
    
    await waitFor(() => {
      expect(mockPostsApi.postNow).toHaveBeenCalledWith(mockPost.id);
    });
    
    // Should not call onPostUpdate on error
    expect(mockOnPostUpdate).not.toHaveBeenCalled();
  });
});