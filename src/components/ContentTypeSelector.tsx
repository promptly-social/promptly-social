
import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { FileText, Linkedin, AlertCircle } from 'lucide-react';

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
      label: 'Blog Post',
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
      {availableContentTypes.length === 1 ? (
        <div className="p-3 border border-amber-200 bg-amber-50 rounded-lg">
          <div className="flex items-center gap-2 text-amber-800">
            <AlertCircle className="w-4 h-4" />
            <span className="text-sm">
              Only blog posts available. Connect social platforms in your Writing Profile to create posts for those platforms.
            </span>
          </div>
          <Button 
            size="sm" 
            variant="outline" 
            onClick={() => window.location.href = '/writing-profile'}
            className="mt-2 text-amber-700 border-amber-300 hover:bg-amber-100"
          >
            Connect Platforms
          </Button>
        </div>
      ) : (
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
      )}
    </div>
  );
};
