import React from "react";
import { render, screen } from "@testing-library/react";
import { PostInspiration } from "../PostInspiration";
import { IdeaBankData } from "@/lib/idea-bank-api";

describe("PostInspiration", () => {
  it("renders URL-type inspiration with external link", () => {
    const inspiration: IdeaBankData = {
      type: "url",
      value: "https://example.com/article",
      title: "Example Article",
      time_sensitive: false,
      ai_suggested: false,
    };

    render(<PostInspiration inspiration={inspiration} />);

    expect(screen.getByText("Inspiration:")).toBeInTheDocument();
    expect(screen.getByText("Example Article")).toBeInTheDocument();
    
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "https://example.com/article");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("renders URL-type inspiration without title using value", () => {
    const inspiration: IdeaBankData = {
      type: "url",
      value: "https://example.com/article",
      time_sensitive: false,
      ai_suggested: false,
    };

    render(<PostInspiration inspiration={inspiration} />);

    expect(screen.getByText("https://example.com/article")).toBeInTheDocument();
  });

  it("renders text-type inspiration with truncation", () => {
    const longText = "This is a very long text that should be truncated because it exceeds the 100 character limit that we have set for inspiration display";
    const inspiration: IdeaBankData = {
      type: "text",
      value: longText,
      time_sensitive: false,
      ai_suggested: false,
    };

    render(<PostInspiration inspiration={inspiration} />);

    expect(screen.getByText("Inspiration:")).toBeInTheDocument();
    expect(screen.getByText(/This is a very long text that should be truncated.../)).toBeInTheDocument();
    expect(screen.queryByText(longText)).not.toBeInTheDocument();
  });

  it("renders short text-type inspiration without truncation", () => {
    const shortText = "Short inspiration text";
    const inspiration: IdeaBankData = {
      type: "text",
      value: shortText,
      time_sensitive: false,
      ai_suggested: false,
    };

    render(<PostInspiration inspiration={inspiration} />);

    expect(screen.getByText("Inspiration:")).toBeInTheDocument();
    expect(screen.getByText(shortText)).toBeInTheDocument();
  });

  it("renders product-type inspiration as text", () => {
    const inspiration: IdeaBankData = {
      type: "product",
      value: "Amazing Product Description",
      product_name: "Amazing Product",
      time_sensitive: false,
      ai_suggested: false,
    };

    render(<PostInspiration inspiration={inspiration} />);

    expect(screen.getByText("Inspiration:")).toBeInTheDocument();
    expect(screen.getByText("Amazing Product Description")).toBeInTheDocument();
  });
});