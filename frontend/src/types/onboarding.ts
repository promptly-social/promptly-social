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
    icon: "👤",
    highlights: [
      "Add your LinkedIn handle (required)",
      "Add your Substack handle (optional)",
      "Click Analyze to analyze your bio, writing style, and preferences (takes about 5 minutes)",
    ],
  },
  {
    id: 2,
    title: "Content Preferences",
    icon: "📝",
    highlights: [
      "Enter topics you like to write about",
      "Add news websites you follow",
    ],
  },
  {
    id: 3,
    title: "Settings",
    icon: "⚙️",
    highlights: ["Set when you want to see daily suggested drafts"],
  },
  {
    id: 4,
    title: "My Posts",
    icon: "📄",
    highlights: [
      "Use 'New Post' button to create posts manually",
      "Use 'Brainstorm' button to brainstorm drafts with AI",
      "The AI will improve as your write more posts and provide feedback",
    ],
  },
  {
    id: 5,
    title: "Content Ideas",
    icon: "💡",
    highlights: [
      "Use 'Add idea' button to drop down a few notes or drop in a URL to an article",
      "Use 'Brainstorm' button to brainstorm drafts with AI using an idea",
    ],
  },
];
