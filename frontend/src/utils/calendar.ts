/**
 * Calendar utility functions for post date resolution and filtering
 */

import { Post } from "@/types/posts";

/**
 * Get the relevant date for a post based on its status
 * - For scheduled posts: returns scheduled_at
 * - For posted posts: returns posted_at
 * - For other statuses: returns null
 */
export const getRelevantPostDate = (post: Post): string | null => {
  switch (post.status) {
    case 'scheduled':
      return post.scheduled_at || null;
    case 'posted':
      return post.posted_at || null;
    default:
      return null;
  }
};

/**
 * Check if a post should be displayed on a specific calendar date
 * Compares the relevant post date with the target date
 */
export const isPostRelevantForDate = (post: Post, targetDate: Date): boolean => {
  const relevantDate = getRelevantPostDate(post);
  if (!relevantDate) return false;
  
  try {
    const postDate = new Date(relevantDate);
    
    // Normalize both dates to UTC for comparison to avoid timezone issues
    const postUTC = new Date(postDate.getUTCFullYear(), postDate.getUTCMonth(), postDate.getUTCDate());
    const targetUTC = new Date(targetDate.getUTCFullYear(), targetDate.getUTCMonth(), targetDate.getUTCDate());
    
    return postUTC.getTime() === targetUTC.getTime();
  } catch (error) {
    // Handle invalid date formats gracefully
    console.warn(`Invalid date format for post ${post.id}:`, relevantDate);
    return false;
  }
};

/**
 * Separate posts into scheduled and posted categories
 */
export const separatePostsByType = (posts: Post[]) => {
  const scheduledPosts = posts.filter(post => post.status === 'scheduled');
  const postedPosts = posts.filter(post => post.status === 'posted');
  return { scheduledPosts, postedPosts };
};

/**
 * Filter posts that should be displayed on a specific date
 * Works with both scheduled and posted posts
 */
export const getPostsForDate = (date: Date, posts: Post[]): Post[] => {
  return posts.filter(post => isPostRelevantForDate(post, date));
};

/**
 * Get the date range for a calendar month view
 * Includes padding days from previous/next months to fill the calendar grid
 */
export const getMonthDateRange = (currentDate: Date) => {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();
  
  // Get first and last day of the month
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  
  // Get full calendar view range (includes prev/next month days)
  const firstCalendarDay = new Date(firstDay);
  firstCalendarDay.setDate(firstDay.getDate() - firstDay.getDay());
  
  const lastCalendarDay = new Date(lastDay);
  lastCalendarDay.setDate(lastDay.getDate() + (6 - lastDay.getDay()));
  
  return {
    startDate: firstCalendarDay.toISOString().split('T')[0],
    endDate: lastCalendarDay.toISOString().split('T')[0],
    firstCalendarDay,
    lastCalendarDay
  };
};

/**
 * Check if a post is draggable based on its status and other conditions
 */
export const isPostDraggable = (post: Post): boolean => {
  // Posted posts should never be draggable
  if (post.status === 'posted') return false;
  
  // Check if scheduled post is in the past
  if (post.status === 'scheduled' && post.scheduled_at) {
    const scheduledDate = new Date(post.scheduled_at);
    const now = new Date();
    return scheduledDate >= now;
  }
  
  // Default to draggable for other cases
  return true;
};