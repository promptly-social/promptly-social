/**
 * Types for onboarding functionality
 */

export interface OnboardingProgress {
  id: string;
  user_id: string;
  is_completed: boolean;
  is_skipped: boolean;
  step_profile_completed: boolean;
  step_content_preferences_completed: boolean;
  step_settings_completed: boolean;
  step_my_posts_completed: boolean;
  step_content_ideas_completed: boolean;
  step_posting_schedule_completed: boolean;
  current_step: number;
  progress_percentage: number;
  notes?: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
  skipped_at?: string;
}

export interface OnboardingStepUpdate {
  step: number;
  completed?: boolean;
}

export interface OnboardingSkip {
  notes?: string;
}

export interface OnboardingUpdate {
  current_step?: number;
  notes?: string;
  step_profile_completed?: boolean;
  step_content_preferences_completed?: boolean;
  step_settings_completed?: boolean;
  step_my_posts_completed?: boolean;
  step_content_ideas_completed?: boolean;
  step_posting_schedule_completed?: boolean;
}

export interface OnboardingStep {
  id: number;
  title: string;
  description: string;
  route: string;
  icon: string;
  isCompleted: boolean;
  isActive: boolean;
  highlights?: string[];
}

export const ONBOARDING_STEPS: Omit<
  OnboardingStep,
  "isCompleted" | "isActive"
>[] = [
  {
    id: 1,
    title: "Set Up Your Profile",
    description: "Connect your LinkedIn and set up your professional profile",
    route: "/profile",
    icon: "👤",
    highlights: [
      "Add your LinkedIn handle (required)",
      "Add your Substack handle (optional)",
      "Click Analyze to analyze your bio, writing style, and preferences (takes about 5 minutes)"
    ],
  },
  {
    id: 2,
    title: "Content Preferences",
    description: "Tell us what you like to write about and your sources",
    route: "/content-preferences",
    icon: "📝",
    highlights: [
      "Enter topics you like to write about",
      "Add news websites you follow",
    ],
  },
  {
    id: 3,
    title: "Settings",
    description: "Configure your daily suggestion preferences",
    route: "/settings",
    icon: "⚙️",
    highlights: ["Set your daily suggestion time"],
  },
  {
    id: 4,
    title: "My Posts",
    description: "Learn how to create and brainstorm posts",
    route: "/my-posts",
    icon: "📄",
    highlights: [
      "Use 'New Post' button to create posts manually",
      "Use 'Brain Storm' button to brainstorm drafts with AI",
    ],
  },
  {
    id: 5,
    title: "Content Ideas",
    description: "Manage your content ideas and inspiration",
    route: "/content-ideas",
    icon: "💡",
    highlights: [
      "Add notes about topics you want to write about later",
      "Brainstorm drafts using your saved ideas",
      "Note: URLs to social media platforms are not supported yet",
    ],
  },
  {
    id: 6,
    title: "Posting Schedule",
    description: "Review and manage your scheduled posts",
    route: "/posting-schedule",
    icon: "📅",
    highlights: [
      "Review your list of scheduled posts",
      "Manage your posting calendar",
    ],
  },
];
