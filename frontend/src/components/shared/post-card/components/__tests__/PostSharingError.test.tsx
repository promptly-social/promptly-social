import React from 'react';
import { render, screen } from '@testing-library/react';
import { PostSharingError } from '../PostSharingError';

// Mock the tooltip components
jest.mock('@/components/ui/tooltip', () => ({
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
    
    // Check for the AlertTriangle icon (we can't easily test the icon itself, but we can test its container)
    const errorIndicator = screen.getByRole('generic');
    expect(errorIndicator).toBeInTheDocument();
  });

  it('displays correct error message in tooltip', () => {
    render(<PostSharingError hasError={true} />);
    
    const tooltipContent = screen.getByTestId('tooltip-content');
    expect(tooltipContent).toHaveTextContent(
      'An error occurred when Promptly tried to post on your behalf. Please try to reschedule it or post it now.'
    );
  });
});