/**
 * Unit tests for calendar utility functions
 */

import { describe, it, expect } from 'vitest';
import { Post } from '@/types/posts';
import {
  getRelevantPostDate,
  isPostRelevantForDate,
  separatePostsByType,
  getPostsForDate,
  getMonthDateRange,
  isPostDraggable
} from '../calendar';

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

describe('getRelevantPostDate', () => {
  it('returns scheduled_at for scheduled posts', () => {
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: '2024-01-15T10:00:00Z'
    });
    expect(getRelevantPostDate(post)).toBe('2024-01-15T10:00:00Z');
  });

  it('returns posted_at for posted posts', () => {
    const post = createMockPost({
      status: 'posted',
      posted_at: '2024-01-15T10:00:00Z'
    });
    expect(getRelevantPostDate(post)).toBe('2024-01-15T10:00:00Z');
  });

  it('returns null for draft posts', () => {
    const post = createMockPost({ status: 'draft' });
    expect(getRelevantPostDate(post)).toBeNull();
  });

  it('returns null when scheduled post has no scheduled_at', () => {
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: undefined
    });
    expect(getRelevantPostDate(post)).toBeNull();
  });

  it('returns null when posted post has no posted_at', () => {
    const post = createMockPost({
      status: 'posted',
      posted_at: undefined
    });
    expect(getRelevantPostDate(post)).toBeNull();
  });
});

describe('isPostRelevantForDate', () => {
  const targetDate = new Date('2024-01-15T00:00:00Z');

  it('returns true when scheduled post matches target date', () => {
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: '2024-01-15T10:00:00Z'
    });
    expect(isPostRelevantForDate(post, targetDate)).toBe(true);
  });

  it('returns true when posted post matches target date', () => {
    const post = createMockPost({
      status: 'posted',
      posted_at: '2024-01-15T14:30:00Z'
    });
    expect(isPostRelevantForDate(post, targetDate)).toBe(true);
  });

  it('returns false when post date does not match target date', () => {
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: '2024-01-16T10:00:00Z'
    });
    expect(isPostRelevantForDate(post, targetDate)).toBe(false);
  });

  it('returns false when post has no relevant date', () => {
    const post = createMockPost({ status: 'draft' });
    expect(isPostRelevantForDate(post, targetDate)).toBe(false);
  });

  it('handles invalid date formats gracefully', () => {
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: 'invalid-date'
    });
    expect(isPostRelevantForDate(post, targetDate)).toBe(false);
  });
});

describe('separatePostsByType', () => {
  it('correctly separates scheduled and posted posts', () => {
    const posts = [
      createMockPost({ id: '1', status: 'scheduled' }),
      createMockPost({ id: '2', status: 'posted' }),
      createMockPost({ id: '3', status: 'scheduled' }),
      createMockPost({ id: '4', status: 'draft' }),
      createMockPost({ id: '5', status: 'posted' })
    ];

    const { scheduledPosts, postedPosts } = separatePostsByType(posts);

    expect(scheduledPosts).toHaveLength(2);
    expect(scheduledPosts.map(p => p.id)).toEqual(['1', '3']);
    
    expect(postedPosts).toHaveLength(2);
    expect(postedPosts.map(p => p.id)).toEqual(['2', '5']);
  });

  it('handles empty array', () => {
    const { scheduledPosts, postedPosts } = separatePostsByType([]);
    expect(scheduledPosts).toHaveLength(0);
    expect(postedPosts).toHaveLength(0);
  });
});

describe('getPostsForDate', () => {
  const targetDate = new Date('2024-01-15T00:00:00Z');

  it('returns posts that match the target date', () => {
    const posts = [
      createMockPost({
        id: '1',
        status: 'scheduled',
        scheduled_at: '2024-01-15T10:00:00Z'
      }),
      createMockPost({
        id: '2',
        status: 'posted',
        posted_at: '2024-01-15T14:00:00Z'
      }),
      createMockPost({
        id: '3',
        status: 'scheduled',
        scheduled_at: '2024-01-16T10:00:00Z'
      })
    ];

    const result = getPostsForDate(targetDate, posts);
    expect(result).toHaveLength(2);
    expect(result.map(p => p.id)).toEqual(['1', '2']);
  });

  it('returns empty array when no posts match', () => {
    const posts = [
      createMockPost({
        status: 'scheduled',
        scheduled_at: '2024-01-16T10:00:00Z'
      })
    ];

    const result = getPostsForDate(targetDate, posts);
    expect(result).toHaveLength(0);
  });
});

describe('getMonthDateRange', () => {
  it('returns correct date range for January 2024', () => {
    const currentDate = new Date('2024-01-15T00:00:00Z');
    const result = getMonthDateRange(currentDate);

    // January 1, 2024 was a Monday, so calendar should start on Dec 31, 2023 (Sunday)
    expect(result.startDate).toBe('2023-12-31');
    // January 31, 2024 was a Wednesday, so calendar should end on Feb 3, 2024 (Saturday)
    expect(result.endDate).toBe('2024-02-03');
  });

  it('returns correct date range for February 2024 (leap year)', () => {
    const currentDate = new Date('2024-02-15T00:00:00Z');
    const result = getMonthDateRange(currentDate);

    // February 1, 2024 was a Thursday, so calendar should start on Jan 28, 2024 (Sunday)
    expect(result.startDate).toBe('2024-01-28');
    // February 29, 2024 was a Thursday, so calendar should end on Mar 2, 2024 (Saturday)
    expect(result.endDate).toBe('2024-03-02');
  });
});

describe('isPostDraggable', () => {
  it('returns false for posted posts', () => {
    const post = createMockPost({ status: 'posted' });
    expect(isPostDraggable(post)).toBe(false);
  });

  it('returns true for future scheduled posts', () => {
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 1);
    
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: futureDate.toISOString()
    });
    expect(isPostDraggable(post)).toBe(true);
  });

  it('returns false for past scheduled posts', () => {
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 1);
    
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: pastDate.toISOString()
    });
    expect(isPostDraggable(post)).toBe(false);
  });

  it('returns true for draft posts', () => {
    const post = createMockPost({ status: 'draft' });
    expect(isPostDraggable(post)).toBe(true);
  });

  it('returns true for scheduled posts without scheduled_at', () => {
    const post = createMockPost({
      status: 'scheduled',
      scheduled_at: undefined
    });
    expect(isPostDraggable(post)).toBe(true);
  });
});