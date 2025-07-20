import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ImageGenerationStyleEditor } from "../ImageGenerationStyleEditor";
import { ProfileProvider } from "@/contexts/ProfileContext";
import { AuthProvider } from "@/contexts/AuthContext";

// Mock the useToast hook
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock profile queries
const mockMutateAsync = vi.fn().mockResolvedValue({});
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
      image_generation_style: "Minimalist vector illustrations with blue palette",
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
    mutateAsync: mockMutateAsync,
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

describe("ImageGenerationStyleEditor", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders as card variant by default", () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    expect(screen.getByText("Image Generation Preferences")).toBeInTheDocument();
    expect(screen.getByText("Image Generation Style")).toBeInTheDocument();
  });

  it("renders as content variant when specified", () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor variant="content" />
      </TestWrapper>
    );
    
    expect(screen.queryByText("Image Generation Preferences")).not.toBeInTheDocument();
    expect(screen.getByText("Image Generation Style")).toBeInTheDocument();
  });

  it("displays current style when available", () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    expect(screen.getByText("Minimalist vector illustrations with blue palette")).toBeInTheDocument();
  });

  it("shows edit button when style exists", () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    expect(screen.getByText("Edit Style")).toBeInTheDocument();
  });

  it("enters edit mode when edit button is clicked", async () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    const editButton = screen.getByText("Edit Style");
    fireEvent.click(editButton);
    
    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.getByText("Save Style")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("allows editing the style text", async () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    const editButton = screen.getByText("Edit Style");
    fireEvent.click(editButton);
    
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "New custom style description" },
    });
    
    expect(textarea).toHaveValue("New custom style description");
  });

  it("saves the style when save button is clicked", async () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    const editButton = screen.getByText("Edit Style");
    fireEvent.click(editButton);
    
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "New custom style description" },
    });
    
    const saveButton = screen.getByText("Save Style");
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        image_generation_style: "New custom style description",
      });
    });
  });

  it("cancels editing when cancel button is clicked", async () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    const editButton = screen.getByText("Edit Style");
    fireEvent.click(editButton);
    
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "New custom style description" },
    });
    
    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);
    
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByText("Edit Style")).toBeInTheDocument();
  });

  it("calls onSave callback when provided", async () => {
    const mockOnSave = vi.fn();
    
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor onSave={mockOnSave} />
      </TestWrapper>
    );
    
    const editButton = screen.getByText("Edit Style");
    fireEvent.click(editButton);
    
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "New style" },
    });
    
    const saveButton = screen.getByText("Save Style");
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith("New style");
    });
  });

  it("calls onCancel callback when provided", async () => {
    const mockOnCancel = vi.fn();
    
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor onCancel={mockOnCancel} />
      </TestWrapper>
    );
    
    const editButton = screen.getByText("Edit Style");
    fireEvent.click(editButton);
    
    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalled();
  });

  it("saves null when empty string is provided", async () => {
    render(
      <TestWrapper>
        <ImageGenerationStyleEditor />
      </TestWrapper>
    );
    
    const editButton = screen.getByText("Edit Style");
    fireEvent.click(editButton);
    
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "   " }, // whitespace only
    });
    
    const saveButton = screen.getByText("Save Style");
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({
        image_generation_style: null,
      });
    });
  });
});
