import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PromptGenerationModal } from "../PromptGenerationModal";
import { ProfileProvider } from "@/contexts/ProfileContext";
import { AuthProvider } from "@/contexts/AuthContext";

// Mock the useToast hook
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock profile queries
vi.mock("@/lib/profile-queries", () => ({
  useUserPreferences: () => ({
    data: {
      id: "1",
      user_id: "1",
      topics_of_interest: [],
      websites: [],
      substacks: [],
      bio: "",
      preferred_posting_time: null,
      timezone: null,
      image_generation_style: null,
      content_strategies: [],
      created_at: "2023-01-01",
      updated_at: "2023-01-01",
    },
    isLoading: false,
  }),
  useSocialConnections: () => ({
    data: [],
    isLoading: false,
  }),
  useUpdateUserPreferences: () => ({
    mutateAsync: vi.fn().mockResolvedValue({}),
  }),
  profileKeys: {
    preferences: ["profile", "preferences"],
    connections: ["profile", "connections"],
  },
}));

// Mock auth context
vi.mock("@/contexts/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => ({
    user: { id: "1", email: "test@example.com" },
    loading: false,
  }),
}));

// Mock the clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
});

// Test wrapper with providers
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ProfileProvider>
          {children}
        </ProfileProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
};

describe("PromptGenerationModal", () => {
  const mockOnClose = vi.fn();
  const mockOnCopy = vi.fn();
  const mockOnRegenerate = vi.fn();

  const initialProps = {
    isOpen: true,
    onClose: mockOnClose,
    onCopy: mockOnCopy,
    onRegenerate: mockOnRegenerate,
    prompt: "This is a test prompt",
  };

  it("renders the modal with the initial prompt", () => {
    render(
      <TestWrapper>
        <PromptGenerationModal {...initialProps} />
      </TestWrapper>
    );
    expect(screen.getByText("Generated Prompt")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue(initialProps.prompt);
  });

  it("allows editing the prompt", () => {
    render(
      <TestWrapper>
        <PromptGenerationModal {...initialProps} />
      </TestWrapper>
    );
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "This is an edited prompt" },
    });
    expect(textarea).toHaveValue("This is an edited prompt");
  });

  it('calls onCopy and onClose with the edited prompt when "Copy" is clicked', () => {
    render(
      <TestWrapper>
        <PromptGenerationModal {...initialProps} />
      </TestWrapper>
    );
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "This is an edited prompt" },
    });

    const copyButton = screen.getByText("Copy");
    fireEvent.click(copyButton);

    expect(mockOnCopy).toHaveBeenCalledWith("This is an edited prompt");
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onClose when "Close" is clicked', () => {
    render(
      <TestWrapper>
        <PromptGenerationModal {...initialProps} />
      </TestWrapper>
    );
    const closeButton = screen.getAllByText("Close")[0];
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("shows image generation style section", () => {
    render(
      <TestWrapper>
        <PromptGenerationModal {...initialProps} />
      </TestWrapper>
    );
    expect(screen.getByText("Image Generation Style")).toBeInTheDocument();
  });

  it("shows regenerate button", () => {
    render(
      <TestWrapper>
        <PromptGenerationModal {...initialProps} />
      </TestWrapper>
    );
    expect(screen.getByText("Regenerate")).toBeInTheDocument();
  });
});
