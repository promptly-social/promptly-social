/**
 * Unit tests for DroppableMonthDay component
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DndContext } from '@dnd-kit/core';
import { DroppableMonthDay } from '../DroppableMonthDay';
import { Post } from '@/types/posts';

// Mock the useIsMobile hook
vi.doMock('@/hooks/use-mobile', () => ({
  useIsMobile: () => false
}));

// Mock post data for testing
const createMockPost = (overrides: Partial<Post> = {}): Post => ({
  id: 'test-id',
  user_id: 'user-id',
  content: 'Test content',
  platform: 'linkedin',
  topics: [],
  status: 'draft',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  media: [],
  ...overrides
});

const renderWithDndContext = (component: React.ReactElement) => {
  return render(
    <DndContext>
      {component}
    </DndContext>
  );
};

describe('DroppableMonthDay', () => {
  const testDate = new Date('2024-01-15T00:00:00Z');

  it('renders scheduled and posted posts separately', () => {
    const posts = [
      createMockPost({
        id: 'scheduled-1',
        status: 'scheduled',
        content: 'Scheduled post content',
        scheduled_at: '2024-01-15T10:00:00Z'
      }),
      createMockPost({
        id: 'posted-1',
        status: 'posted',
        content: 'Posted post content',
        posted_at: '2024-01-15T14:00:00Z'
      })
    ];

    renderWithDndContext(
      <DroppableMonthDay
        date={testDate}
        posts={posts}
        isCurrentMonth={true}
        isToday={false}
      />
    );

    // Both posts should be rendered
    expect(screen.getByText('Scheduled post content')).toBeInTheDocument();
    expect(screen.getByText('Posted post content')).toBeInTheDocument();
  });

  it('shows separator between posted and scheduled posts when both exist', () => {
    const posts = [
      createMockPost({
        id: 'scheduled-1',
        status: 'scheduled',
        content: 'Scheduled post',
        scheduled_at: '2024-01-15T10:00:00Z'
      }),
      createMockPost({
        id: 'posted-1',
        status: 'posted',
        content: 'Posted post',
        posted_at: '2024-01-15T14:00:00Z'
      })
    ];

    const { container } = renderWithDndContext(
      <DroppableMonthDay
        date={testDate}
        posts={posts}
        isCurrentMonth={true}
        isToday={false}
      />
    );

    // Check for separator element
    const separator = container.querySelector('.border-t.border-gray-200');
    expect(separator).toBeInTheDocument();
  });

  it('does not show separator when only scheduled posts exist', () => {
    const posts = [
      createMockPost({
        id: 'scheduled-1',
        status: 'scheduled',
        content: 'Scheduled post',
        scheduled_at: '2024-01-15T10:00:00Z'
      })
    ];

    const { container } = renderWithDndContext(
      <DroppableMonthDay
        date={testDate}
        posts={posts}
        isCurrentMonth={true}
        isToday={false}
      />
    );

    // Check that separator is not present
    const separator = container.querySelector('.border-t.border-gray-200');
    expect(separator).not.toBeInTheDocument();
  });

  it('does not show separator when only posted posts exist', () => {
    const posts = [
      createMockPost({
        id: 'posted-1',
        status: 'posted',
        content: 'Posted post',
        posted_at: '2024-01-15T14:00:00Z'
      })
    ];

    const { container } = renderWithDndContext(
      <DroppableMonthDay
        date={testDate}
        posts={posts}
        isCurrentMonth={true}
        isToday={false}
      />
    );

    // Check that separator is not present
    const separator = container.querySelector('.border-t.border-gray-200');
    expect(separator).not.toBeInTheDocument();
  });

  it('shows correct post count when mixed post types exist', () => {
    const posts = [
      createMockPost({ id: '1', status: 'scheduled' }),
      createMockPost({ id: '2', status: 'posted' }),
      createMockPost({ id: '3', status: 'scheduled' }),
      createMockPost({ id: '4', status: 'posted' }),
      createMockPost({ id: '5', status: 'scheduled' })
    ];

    renderWithDndContext(
      <DroppableMonthDay
        date={testDate}
        posts={posts}
        isCurrentMonth={true}
        isToday={false}
      />
    );

    // Should show "+3 more" since maxPostsToShow is 2 and we have 5 posts
    expect(screen.getByText('+3 more')).toBeInTheDocument();
  });
});