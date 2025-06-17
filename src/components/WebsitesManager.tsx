
import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Globe, Plus, X } from 'lucide-react';

interface WebsitesManagerProps {
  websites: string[];
  onWebsitesChange: (websites: string[]) => void;
}

export const WebsitesManager: React.FC<WebsitesManagerProps> = ({
  websites,
  onWebsitesChange
}) => {
  const [newWebsite, setNewWebsite] = useState('');

  const addWebsite = () => {
    if (newWebsite.trim() && !websites.includes(newWebsite.trim())) {
      // Add https:// if no protocol is specified
      let url = newWebsite.trim();
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
      }
      
      onWebsitesChange([...websites, url]);
      setNewWebsite('');
    }
  };

  const removeWebsite = (website: string) => {
    onWebsitesChange(websites.filter(w => w !== website));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addWebsite();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Globe className="w-4 h-4 text-green-600" />
        <Label className="font-medium">Preferred Websites</Label>
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        {websites.map((website, index) => (
          <Badge key={index} variant="outline" className="flex items-center gap-1">
            {website.replace(/^https?:\/\//, '')}
            <button
              onClick={() => removeWebsite(website)}
              className="ml-1 hover:bg-gray-300 rounded-full p-0.5"
            >
              <X className="w-3 h-3" />
            </button>
          </Badge>
        ))}
      </div>
      <div className="flex gap-2">
        <Input
          placeholder="Add a website (e.g., techcrunch.com, medium.com)"
          value={newWebsite}
          onChange={(e) => setNewWebsite(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <Button onClick={addWebsite} size="sm" disabled={!newWebsite.trim()}>
          <Plus className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
