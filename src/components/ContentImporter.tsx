
import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Upload, Download, Loader2, FileText, Users } from 'lucide-react';

export const ContentImporter: React.FC = () => {
  const [isImporting, setIsImporting] = useState(false);
  const [manualContent, setManualContent] = useState('');
  const [manualTitle, setManualTitle] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  const { user } = useAuth();

  const importFromSubstack = async () => {
    setIsImporting(true);
    try {
      const response = await fetch('/functions/v1/import-substack-content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: user?.id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to import Substack content');
      }

      const { imported_count } = await response.json();

      toast({
        title: "Import Successful",
        description: `Imported ${imported_count} posts from Substack`,
      });
    } catch (error) {
      console.error('Error importing Substack content:', error);
      toast({
        title: "Import Error",
        description: "Failed to import Substack content. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    Array.from(files).forEach(file => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const content = e.target?.result as string;
        await saveManualContent(file.name, content);
      };
      reader.readAsText(file);
    });
  };

  const saveManualContent = async (title: string, content: string) => {
    try {
      const { error } = await supabase
        .from('imported_content')
        .insert({
          user_id: user?.id,
          platform: 'linkedin',
          title: title,
          content: content,
          created_at: new Date().toISOString(),
        });

      if (error) throw error;

      toast({
        title: "Content Saved",
        description: `Successfully saved "${title}"`,
      });
    } catch (error) {
      console.error('Error saving content:', error);
      toast({
        title: "Save Error",
        description: "Failed to save content",
        variant: "destructive",
      });
    }
  };

  const handleManualSubmit = async () => {
    if (!manualContent.trim()) {
      toast({
        title: "Content Required",
        description: "Please enter some content to save",
        variant: "destructive",
      });
      return;
    }

    await saveManualContent(manualTitle || 'Manual Entry', manualContent);
    setManualContent('');
    setManualTitle('');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="w-5 h-5" />
          Content Import
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Substack Import */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-orange-600" />
            <span className="font-medium">Import from Substack</span>
          </div>
          <Button
            onClick={importFromSubstack}
            disabled={isImporting}
            className="w-full"
          >
            {isImporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Import Substack Posts
              </>
            )}
          </Button>
          <p className="text-sm text-gray-600">
            This will fetch your recent public posts from Substack for analysis.
          </p>
        </div>

        {/* LinkedIn File Upload */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-600" />
            <span className="font-medium">Upload LinkedIn Posts</span>
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".txt,.md"
            multiple
            className="hidden"
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            variant="outline"
            className="w-full"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload Text Files
          </Button>
          <p className="text-sm text-gray-600">
            Upload .txt or .md files containing your LinkedIn posts.
          </p>
        </div>

        {/* Manual Entry */}
        <div className="space-y-3">
          <span className="font-medium">Manual Entry</span>
          <input
            type="text"
            placeholder="Post title (optional)"
            value={manualTitle}
            onChange={(e) => setManualTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md"
          />
          <Textarea
            placeholder="Paste your content here..."
            value={manualContent}
            onChange={(e) => setManualContent(e.target.value)}
            rows={6}
          />
          <Button onClick={handleManualSubmit} variant="outline" className="w-full">
            Save Content
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
