import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { PostSharingError } from '../PostSharingError';

// Mock the tooltip components
vi.mock('@/components/ui/tooltip', () => ({
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Tooltip: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TooltipContent: ({ children }: { children: React.ReactNode }) => <div data-testid="tooltip-content">{children}</div>,
}));

describe('PostSharingError', () => {
  it('renders nothing when hasError is false', () => {
    const { container } = render(<PostSharingError hasError={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders error indicator when hasError is true', () => {
    render(<PostSharingError hasError={true} />);
    
    // Check for the AlertTriangle icon by looking for the tooltip content which indicates the error is rendered
    const tooltipContent = screen.getByTestId('tooltip-content');
    expect(tooltipContent).toBeInTheDocument();
  });

  it('displays correct error message in tooltip', () => {
    render(<PostSharingError hasError={true} />);
    
    const tooltipContent = screen.getByTestId('tooltip-content');
    expect(tooltipContent).toHaveTextContent(
      'An error occurred when Promptly tried to post on your behalf. Please try to reschedule it or post it now.'
    );
  });
});