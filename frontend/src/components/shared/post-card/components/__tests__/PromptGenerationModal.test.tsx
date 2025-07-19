import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PromptGenerationModal } from "../PromptGenerationModal";

// Mock the useToast hook
vi.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

// Mock the clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: vi.fn(),
  },
});

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
    render(<PromptGenerationModal {...initialProps} />);
    expect(screen.getByText("Generated Prompt")).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveValue(initialProps.prompt);
  });

  it("allows editing the prompt", () => {
    render(<PromptGenerationModal {...initialProps} />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, {
      target: { value: "This is an edited prompt" },
    });
    expect(textarea).toHaveValue("This is an edited prompt");
  });

  it('calls onCopy and onClose with the edited prompt when "Copy" is clicked', () => {
    render(<PromptGenerationModal {...initialProps} />);
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
    render(<PromptGenerationModal {...initialProps} />);
    const closeButton = screen.getAllByText("Close")[0];
    fireEvent.click(closeButton);

    expect(mockOnClose).toHaveBeenCalled();
  });
});
