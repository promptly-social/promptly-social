
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { ContentScheduler } from '@/components/ContentScheduler';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { LogOut, Calendar, FileText, CheckCircle, XCircle, Clock, Send, AlertCircle } from 'lucide-react';

interface ContentItem {
  id: string;
  title: string;
  content_type: string;
  created_at: string;
  status?: 'draft' | 'approved' | 'scheduled' | 'published' | 'failed';
  scheduled_date?: string;
  published_date?: string;
  publication_error?: string;
  linkedin_post_id?: string;
}

const MyContent: React.FC = () => {
  const { user, signOut } = useAuth();
  const { toast } = useToast();
  const [content, setContent] = useState<ContentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [schedulingContentId, setSchedulingContentId] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchContent();
    }
  }, [user]);

  const fetchContent = async () => {
    try {
      const { data, error } = await supabase
        .from('content_ideas')
        .select('*')
        .eq('user_id', user?.id)
        .order('created_at', { ascending: false });

      if (error) throw error;
      
      // Transform data to match our interface
      const transformedData: ContentItem[] = data.map(item => ({
        id: item.id,
        title: item.title,
        content_type: item.content_type,
        created_at: item.created_at,
        status: item.status || 'draft',
        scheduled_date: item.scheduled_date,
        published_date: item.published_date,
        publication_error: item.publication_error,
        linkedin_post_id: item.linkedin_post_id,
      }));

      setContent(transformedData);
    } catch (error) {
      console.error('Error fetching content:', error);
      toast({
        title: "Error",
        description: "Failed to fetch your content",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (contentId: string) => {
    try {
      const { error } = await supabase
        .from('content_ideas')
        .update({ status: 'approved' })
        .eq('id', contentId);

      if (error) throw error;

      await fetchContent();
      toast({
        title: "Content Approved",
        description: "Content has been approved and is ready for scheduling.",
      });
    } catch (error) {
      console.error('Error approving content:', error);
      toast({
        title: "Error",
        description: "Failed to approve content",
        variant: "destructive",
      });
    }
  };

  const handleReject = async (contentId: string) => {
    try {
      const { error } = await supabase
        .from('content_ideas')
        .update({ status: 'draft' })
        .eq('id', contentId);

      if (error) throw error;

      await fetchContent();
      toast({
        title: "Content Rejected",
        description: "Content has been moved back to draft status.",
      });
    } catch (error) {
      console.error('Error rejecting content:', error);
      toast({
        title: "Error",
        description: "Failed to reject content",
        variant: "destructive",
      });
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800';
      case 'scheduled':
        return 'bg-blue-100 text-blue-800';
      case 'approved':
        return 'bg-purple-100 text-purple-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getContentTypeIcon = (type: string) => {
    return type === 'blog_post' ? FileText : FileText;
  };

  const handleSchedulingComplete = () => {
    setSchedulingContentId(null);
    fetchContent();
  };

  return (
    <SidebarInset>
      <header className="border-b border-gray-100 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-6">
          <div className="flex items-center gap-4">
            <SidebarTrigger />
            <h1 className="text-2xl font-bold text-gray-900">My Content</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Welcome, {user?.email}</span>
            <Button onClick={signOut} variant="outline" size="sm">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <main className="py-8 px-6">
        <div className="max-w-6xl mx-auto">
          {schedulingContentId && (
            <div className="mb-6">
              <ContentScheduler
                contentId={schedulingContentId}
                contentType={content.find(c => c.id === schedulingContentId)?.content_type || 'blog_post'}
                onScheduled={handleSchedulingComplete}
                onCancel={() => setSchedulingContentId(null)}
              />
            </div>
          )}

          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
              <p className="text-gray-600 mt-2">Loading your content...</p>
            </div>
          ) : content.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No content yet</h3>
              <p className="text-gray-600 mb-4">Start creating content to see it here</p>
              <Button onClick={() => window.location.href = '/dashboard'}>
                Create New Content
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {content.map((item) => {
                const ContentIcon = getContentTypeIcon(item.content_type);
                const isScheduling = schedulingContentId === item.id;
                
                return (
                  <Card key={item.id} className={isScheduling ? 'ring-2 ring-blue-500' : ''}>
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <ContentIcon className="w-5 h-5 text-gray-500 mt-1" />
                          <div>
                            <CardTitle className="text-lg">{item.title}</CardTitle>
                            <div className="flex items-center gap-2 mt-2 flex-wrap">
                              <Badge variant="outline" className="capitalize">
                                {item.content_type.replace('_', ' ')}
                              </Badge>
                              <Badge className={getStatusColor(item.status || 'draft')}>
                                {item.status || 'draft'}
                              </Badge>
                              {item.status === 'failed' && item.publication_error && (
                                <Badge variant="destructive" className="text-xs">
                                  <AlertCircle className="w-3 h-3 mr-1" />
                                  Error
                                </Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          {item.status === 'draft' && (
                            <>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-green-600 hover:text-green-700"
                                onClick={() => handleApprove(item.id)}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Approve
                              </Button>
                            </>
                          )}
                          {item.status === 'approved' && (
                            <>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-blue-600 hover:text-blue-700"
                                onClick={() => setSchedulingContentId(item.id)}
                              >
                                <Clock className="w-4 h-4 mr-1" />
                                Schedule
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline" 
                                className="text-red-600 hover:text-red-700"
                                onClick={() => handleReject(item.id)}
                              >
                                <XCircle className="w-4 h-4 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                          {item.status === 'scheduled' && (
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="text-orange-600 hover:text-orange-700"
                              onClick={() => handleReject(item.id)}
                            >
                              Cancel Schedule
                            </Button>
                          )}
                          {item.status === 'failed' && (
                            <Button 
                              size="sm" 
                              variant="outline" 
                              className="text-blue-600 hover:text-blue-700"
                              onClick={() => setSchedulingContentId(item.id)}
                            >
                              <Send className="w-4 h-4 mr-1" />
                              Retry
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-4 text-sm text-gray-600 flex-wrap">
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          Created: {new Date(item.created_at).toLocaleDateString()}
                        </div>
                        {item.scheduled_date && (
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            Scheduled: {new Date(item.scheduled_date).toLocaleString()}
                          </div>
                        )}
                        {item.published_date && (
                          <div className="flex items-center gap-1">
                            <Send className="w-4 h-4" />
                            Published: {new Date(item.published_date).toLocaleString()}
                          </div>
                        )}
                      </div>
                      {item.status === 'failed' && item.publication_error && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                          <strong>Publication Error:</strong> {item.publication_error}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </SidebarInset>
  );
};

export default MyContent;
