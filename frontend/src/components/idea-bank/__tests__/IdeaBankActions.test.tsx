import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import IdeaBankActions from '../IdeaBankActions';
import type { IdeaBankWithPost } from '@/lib/idea-bank-api';

// Mock the UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, className, ...props }: any) => (
    <button 
      onClick={onClick} 
      disabled={disabled} 
      className={className}
      data-testid={props['data-testid']}
    >
      {children}
    </button>
  ),
}));

const mockIdeaBankWithPost: IdeaBankWithPost = {
  idea_bank: {
    id: '1',
    user_id: '1',
    data: {
      type: 'text',
      value: 'Test idea content',
      title: 'Test Title',
      time_sensitive: false,
      ai_suggested: false,
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  latest_post: null,
};

describe('IdeaBankActions', () => {
  const mockHandlers = {
    onGenerate: vi.fn(),
    onEdit: vi.fn(),
    onDelete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all action buttons', () => {
    render(
      <IdeaBankActions 
        ideaBankWithPost={mockIdeaBankWithPost}
        {...mockHandlers}
      />
    );
    
    expect(screen.getByText('Draft Post')).toBeInTheDocument();
    expect(screen.getByText('Edit Idea')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('calls onGenerate when Draft Post button is clicked', () => {
    render(
      <IdeaBankActions 
        ideaBankWithPost={mockIdeaBankWithPost}
        {...mockHandlers}
      />
    );
    
    fireEvent.click(screen.getByText('Draft Post'));
    expect(mockHandlers.onGenerate).toHaveBeenCalledWith(mockIdeaBankWithPost);
  });

  it('calls onEdit when Edit Idea button is clicked', () => {
    render(
      <IdeaBankActions 
        ideaBankWithPost={mockIdeaBankWithPost}
        {...mockHandlers}
      />
    );
    
    fireEvent.click(screen.getByText('Edit Idea'));
    expect(mockHandlers.onEdit).toHaveBeenCalledWith(mockIdeaBankWithPost);
  });

  it('calls onDelete when Delete button is clicked', () => {
    render(
      <IdeaBankActions 
        ideaBankWithPost={mockIdeaBankWithPost}
        {...mockHandlers}
      />
    );
    
    fireEvent.click(screen.getByText('Delete'));
    expect(mockHandlers.onDelete).toHaveBeenCalledWith(mockIdeaBankWithPost.idea_bank.id);
  });

  it('has proper styling classes for responsive design', () => {
    render(
      <IdeaBankActions 
        ideaBankWithPost={mockIdeaBankWithPost}
        {...mockHandlers}
      />
    );
    
    const buttons = screen.getAllByRole('button');
    buttons.forEach(button => {
      expect(button).toHaveClass('justify-start', 'w-full', 'min-w-0');
    });
  });
});