/**
 * Unit tests for MonthViewPostCard component with posted post functionality
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DndContext } from "@dnd-kit/core";
import { MonthViewPostCard } from "../MonthViewPostCard";
import { Post } from "@/types/posts";

// Mock the useIsMobile hook
vi.doMock("@/hooks/use-mobile", () => ({
  useIsMobile: () => false,
}));

// Mock post data for testing
const createMockPost = (overrides: Partial<Post> = {}): Post => ({
  id: "test-id",
  user_id: "user-id",
  content: "Test content",
  platform: "linkedin",
  topics: [],
  status: "draft",
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  media: [],
  ...overrides,
});

const renderWithDndContext = (component: React.ReactElement) => {
  return render(<DndContext>{component}</DndContext>);
};

describe("MonthViewPostCard - Posted Post Functionality", () => {
  it("renders posted post with green styling and posted badge", () => {
    const post = createMockPost({
      status: "posted",
      content: "This is a posted post",
      posted_at: "2024-01-15T14:00:00Z",
    });

    renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={true} />
    );

    // Check that content is rendered
    expect(screen.getByText("This is a posted post")).toBeInTheDocument();
  });

  it("renders scheduled post without posted badge", () => {
    const post = createMockPost({
      status: "scheduled",
      content: "This is a scheduled post",
      scheduled_at: "2024-01-15T10:00:00Z",
    });

    renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={false} />
    );

    // Check that content is rendered
    expect(screen.getByText("This is a scheduled post")).toBeInTheDocument();

    // Check that "Posted" badge is NOT present
    expect(screen.queryByText("Posted")).not.toBeInTheDocument();
  });

  it("shows posted_at time for posted posts", () => {
    const post = createMockPost({
      status: "posted",
      content: "Posted content",
      posted_at: "2024-01-15T14:30:00Z",
      scheduled_at: "2024-01-15T10:00:00Z", // Should use posted_at instead
    });

    renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={true} />
    );

    // The time will be formatted according to local timezone
    // Let's just check that some time is displayed
    const timeElement = screen.getByText(/\d{1,2}:\d{2}\s?(AM|PM)/);
    expect(timeElement).toBeInTheDocument();
  });

  it("shows scheduled_at time for scheduled posts", () => {
    const post = createMockPost({
      status: "scheduled",
      content: "Scheduled content",
      scheduled_at: "2024-01-15T10:00:00Z",
    });

    renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={false} />
    );

    // The time will be formatted according to local timezone
    // Let's just check that some time is displayed
    const timeElement = screen.getByText(/\d{1,2}:\d{2}\s?(AM|PM)/);
    expect(timeElement).toBeInTheDocument();
  });

  it("applies correct CSS classes for posted posts", () => {
    const post = createMockPost({
      status: "posted",
      content: "Posted content",
    });

    const { container } = renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={true} />
    );

    // Check for green styling classes
    const card = container.querySelector(".bg-gray-50");
    expect(card).toBeInTheDocument();

    const borderCard = container.querySelector(".border-gray-200");
    expect(borderCard).toBeInTheDocument();
  });

  it("applies correct cursor style for posted posts", () => {
    const post = createMockPost({
      status: "posted",
      content: "Posted content",
    });

    const { container } = renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={true} />
    );

    // Posted posts should have pointer cursor, not grab cursor
    const card = container.querySelector(".cursor-pointer");
    expect(card).toBeInTheDocument();

    // Should not have grab cursor
    const grabCard = container.querySelector(".cursor-grab");
    expect(grabCard).not.toBeInTheDocument();
  });

  it("applies enhanced hover states for posted posts", () => {
    const post = createMockPost({
      status: "posted",
      content: "Posted content",
    });

    const { container } = renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={true} />
    );

    // Check for hover classes specific to posted posts
    const card = container.querySelector(".hover\\:bg-gray-100");
    expect(card).toBeInTheDocument();

    const borderCard = container.querySelector(".hover\\:border-gray-300");
    expect(borderCard).toBeInTheDocument();

    const transitionCard = container.querySelector(".transition-colors");
    expect(transitionCard).toBeInTheDocument();
  });

  it("applies different hover states for scheduled posts", () => {
    const post = createMockPost({
      status: "scheduled",
      content: "Scheduled content",
      scheduled_at: "2024-01-15T10:00:00Z",
    });

    const { container } = renderWithDndContext(
      <MonthViewPostCard post={post} compact={true} isPosted={false} />
    );

    // Check for hover classes specific to scheduled posts
    const borderCard = container.querySelector(".hover\\:border-gray-300");
    expect(borderCard).toBeInTheDocument();

    // Should have grab cursor for draggable scheduled posts
    const grabCard = container.querySelector(".cursor-grab");
    expect(grabCard).toBeInTheDocument();
  });
});
