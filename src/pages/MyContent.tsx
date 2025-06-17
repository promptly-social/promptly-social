
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { LogOut, ExternalLink, RefreshCw, Calendar, CheckCircle, XCircle, Trash2 } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface ContentIdea {
  id: string;
  title: string;
  original_input: string;
  content_type: string;
  status: string;
  scheduled_date: string | null;
  published_date: string | null;
  linkedin_post_id: string | null;
  publication_error: string | null;
  created_at: string;
}

const MyContent: React.FC = () => {
  const { user, signOut } = useAuth();
  const { toast } = useToast();
  const [pastPosts, setPastPosts] = useState<ContentIdea[]>([]);
  const [scheduledPosts, setScheduledPosts] = useState<ContentIdea[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchContent();
    }
  }, [user]);

  const fetchContent = async () => {
    setIsLoading(true);
    try {
      // Fetch past posts (published or failed)
      const { data: pastData, error: pastError } = await supabase
        .from('content_ideas')
        .select('*')
        .eq('user_id', user?.id)
        .in('status', ['published', 'failed'])
        .order('published_date', { ascending: false, nullsFirst: false })
        .order('created_at', { ascending: false });

      if (pastError) throw pastError;

      // Fetch scheduled posts
      const { data: scheduledData, error: scheduledError } = await supabase
        .from('content_ideas')
        .select('*')
        .eq('user_id', user?.id)
        .eq('status', 'scheduled')
        .order('scheduled_date', { ascending: true });

      if (scheduledError) throw scheduledError;

      setPastPosts(pastData || []);
      setScheduledPosts(scheduledData || []);
    } catch (error) {
      console.error('Error fetching content:', error);
      toast({
        title: "Error",
        description: "Failed to load content",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const cancelScheduledPost = async (postId: string) => {
    setIsCancelling(postId);
    try {
      const { error } = await supabase
        .from('content_ideas')
        .update({ 
          status: 'draft',
          scheduled_date: null 
        })
        .eq('id', postId);

      if (error) throw error;

      // Move from scheduled to remove from list
      setScheduledPosts(prev => prev.filter(post => post.id !== postId));

      toast({
        title: "Success",
        description: "Scheduled post cancelled successfully",
      });
    } catch (error) {
      console.error('Error cancelling post:', error);
      toast({
        title: "Error",
        description: "Failed to cancel scheduled post",
        variant: "destructive",
      });
    } finally {
      setIsCancelling(null);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status: string, error?: string | null) => {
    switch (status) {
      case 'published':
        return <Badge className="bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1" />Published</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800"><XCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      case 'scheduled':
        return <Badge className="bg-blue-100 text-blue-800"><Calendar className="w-3 h-3 mr-1" />Scheduled</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
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
            <Button
              onClick={fetchContent}
              disabled={isLoading}
              variant="outline"
              size="sm"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <span className="text-gray-600">Welcome, {user?.email}</span>
            <Button onClick={signOut} variant="outline" size="sm">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <main className="py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-8">
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              View your published content and manage scheduled posts
            </p>
          </div>

          <Tabs defaultValue="past" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="past">Past Posts ({pastPosts.length})</TabsTrigger>
              <TabsTrigger value="scheduled">Scheduled Posts ({scheduledPosts.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="past" className="space-y-4">
              {isLoading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                  <p className="text-gray-600">Loading past posts...</p>
                </div>
              ) : pastPosts.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <CheckCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-lg font-medium mb-2">No past posts</h3>
                    <p className="text-gray-600">
                      Your published content will appear here
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Title</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Published Date</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pastPosts.map((post) => (
                        <TableRow key={post.id}>
                          <TableCell className="font-medium">
                            <div>
                              <p className="font-semibold">{post.title}</p>
                              <p className="text-sm text-gray-600 truncate max-w-md">
                                {post.original_input.substring(0, 100)}...
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {post.content_type.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {getStatusBadge(post.status, post.publication_error)}
                            {post.publication_error && (
                              <p className="text-xs text-red-600 mt-1">
                                {post.publication_error}
                              </p>
                            )}
                          </TableCell>
                          <TableCell>{formatDate(post.published_date)}</TableCell>
                          <TableCell>
                            {post.linkedin_post_id && (
                              <Button variant="outline" size="sm" asChild>
                                <a 
                                  href={`https://linkedin.com/feed/update/${post.linkedin_post_id}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  <ExternalLink className="w-4 h-4" />
                                </a>
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="scheduled" className="space-y-4">
              {isLoading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                  <p className="text-gray-600">Loading scheduled posts...</p>
                </div>
              ) : scheduledPosts.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-lg font-medium mb-2">No scheduled posts</h3>
                    <p className="text-gray-600">
                      Your scheduled content will appear here
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Title</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Scheduled Date</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scheduledPosts.map((post) => (
                        <TableRow key={post.id}>
                          <TableCell className="font-medium">
                            <div>
                              <p className="font-semibold">{post.title}</p>
                              <p className="text-sm text-gray-600 truncate max-w-md">
                                {post.original_input.substring(0, 100)}...
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline">
                              {post.content_type.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>{formatDate(post.scheduled_date)}</TableCell>
                          <TableCell>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => cancelScheduledPost(post.id)}
                              disabled={isCancelling === post.id}
                            >
                              <Trash2 className="w-4 h-4 mr-1" />
                              {isCancelling === post.id ? 'Cancelling...' : 'Cancel'}
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </SidebarInset>
  );
};

export default MyContent;
