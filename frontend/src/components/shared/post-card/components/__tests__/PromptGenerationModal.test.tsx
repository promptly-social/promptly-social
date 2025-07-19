import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { PromptGenerationModal } from "../PromptGenerationModal";
import { useToast } from "@/hooks/use-toast";

// Mock the useToast hook
jest.mock("@/hooks/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

describe("PromptGenerationModal", () => {
  const mockOnClose = jest.fn();
  const mockOnCopy = jest.fn();
  const mockOnRegenerate = jest.fn();

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
    fireEvent.change(textarea, { target: { value: "This is an edited prompt" } });
    expect(textarea).toHaveValue("This is an edited prompt");
  });

  it('calls onCopy and onClose with the edited prompt when "Copy" is clicked', () => {
    render(<PromptGenerationModal {...initialProps} />);
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "This is an edited prompt" } });

    const copyButton = screen.getByText("Copy");
    fireEvent.click(copyButton);

    expect(mockOnCopy).toHaveBeenCalledWith("This is an edited prompt");
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onRegenerate and onClose when "Regenerate" is clicked', () => {
    render(<PromptGenerationModal {...initialProps} />);
    const regenerateButton = screen.getByText("Regenerate");
    fireEvent.click(regenerateButton);

    expect(mockOnRegenerate).toHaveBeenCalled();
    expect(mockOnClose).toHaveBeenCalled();
  });
});
