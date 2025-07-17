import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PostCardActions } from '../PostCardActions';
import { Post } from '@/types/posts';

// Mock the UI components
jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, className, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      className={className}
      data-testid={props['data-testid']}
    >
      {children}
    </button>
  ),
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

describe('PostCardActions', () => {
  const mockHandlers = {
    onSchedulePost: jest.fn(),
    onRemoveFromSchedule: jest.fn(),
    onReschedulePost: jest.fn(),
    onSaveForLater: jest.fn(),
    onDismissPost: jest.fn(),
    onPostNow: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders nothing for posted posts', () => {
    const postedPost = { ...mockPost, status: 'posted' as const };
    const { container } = render(<PostCardActions post={postedPost} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders Post Now and Schedule buttons for suggested posts', () => {
    render(<PostCardActions post={mockPost} {...mockHandlers} />);
    
    expect(screen.getByText('Post Now')).toBeInTheDocument();
    expect(screen.getByText('Schedule Post')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('renders Post Now, Remove, and Reschedule buttons for scheduled posts', () => {
    const scheduledPost = { ...mockPost, status: 'scheduled' as const };
    render(<PostCardActions post={scheduledPost} {...mockHandlers} />);
    
    expect(screen.getByText('Post Now')).toBeInTheDocument();
    expect(screen.getByText('Remove from Schedule')).toBeInTheDocument();
    expect(screen.getByText('Reschedule')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('shows loading state when posting', () => {
    render(
      <PostCardActions 
        post={mockPost} 
        postingPostId={mockPost.id}
        {...mockHandlers} 
      />
    );
    
    expect(screen.getByText('Posting...')).toBeInTheDocument();
    expect(screen.getByText('Posting...').closest('button')).toBeDisabled();
  });

  it('calls onPostNow when Post Now button is clicked', () => {
    render(<PostCardActions post={mockPost} {...mockHandlers} />);
    
    fireEvent.click(screen.getByText('Post Now'));
    expect(mockHandlers.onPostNow).toHaveBeenCalledWith(mockPost);
  });

  it('calls onSchedulePost when Schedule Post button is clicked', () => {
    render(<PostCardActions post={mockPost} {...mockHandlers} />);
    
    fireEvent.click(screen.getByText('Schedule Post'));
    expect(mockHandlers.onSchedulePost).toHaveBeenCalledWith(mockPost.id);
  });

  it('calls onDismissPost when Delete button is clicked', () => {
    render(<PostCardActions post={mockPost} {...mockHandlers} />);
    
    fireEvent.click(screen.getByText('Delete'));
    expect(mockHandlers.onDismissPost).toHaveBeenCalledWith(mockPost);
  });

  it('shows loading state when dismissing', () => {
    render(
      <PostCardActions 
        post={mockPost} 
        dismissingPostId={mockPost.id}
        {...mockHandlers} 
      />
    );
    
    expect(screen.getByText('Deleting...')).toBeInTheDocument();
    expect(screen.getByText('Deleting...').closest('button')).toBeDisabled();
  });
});