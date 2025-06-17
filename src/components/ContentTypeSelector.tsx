
import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText, Linkedin } from 'lucide-react';

interface ConnectedPlatform {
  platform: string;
  platform_username: string | null;
  is_active: boolean;
}

interface ContentTypeSelectorProps {
  contentType: 'blog_post' | 'linkedin_post';
  onContentTypeChange: (value: 'blog_post' | 'linkedin_post') => void;
  connectedPlatforms: ConnectedPlatform[];
}

export const ContentTypeSelector: React.FC<ContentTypeSelectorProps> = ({
  contentType,
  onContentTypeChange,
  connectedPlatforms
}) => {
  const getAvailableContentTypes = () => {
    const types = [];
    
    // Always show blog post option
    types.push({
      value: 'blog_post',
      label: 'Substack Blog Post',
      icon: FileText
    });

    // Show LinkedIn option only if connected
    const linkedinConnection = connectedPlatforms.find(p => p.platform === 'linkedin');
    if (linkedinConnection) {
      types.push({
        value: 'linkedin_post',
        label: `LinkedIn Post${linkedinConnection.platform_username ? ` (@${linkedinConnection.platform_username})` : ''}`,
        icon: Linkedin
      });
    }

    return types;
  };

  const availableContentTypes = getAvailableContentTypes();

  return (
    <div>
      <label className="block text-sm font-medium mb-2">Content Type</label>
      <Select value={contentType} onValueChange={onContentTypeChange}>
        <SelectTrigger>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {availableContentTypes.map((type) => {
            const Icon = type.icon;
            return (
              <SelectItem key={type.value} value={type.value}>
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4" />
                  {type.label}
                </div>
              </SelectItem>
            );
          })}
        </SelectContent>
      </Select>
    </div>
  );
};
