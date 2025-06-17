
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { LogOut, Sparkles, ExternalLink, RefreshCw, ThumbsUp, ThumbsDown, Share } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface SuggestedPost {
  id: string;
  title: string;
  content: string;
  relevance_score: number;
  topics: string[];
  created_at: string;
  status: string;
  original_source_id: string | null;
}

interface ScrapedContent {
  id: string;
  title: string;
  content: string;
  source_url: string;
  source_type: string;
  topics: string[];
  scraped_at: string;
  relevance_score: number;
}

const MyContent: React.FC = () => {
  const { user, signOut } = useAuth();
  const { toast } = useToast();
  const [suggestedPosts, setSuggestedPosts] = useState<SuggestedPost[]>([]);
  const [scrapedContent, setScrapedContent] = useState<ScrapedContent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (user) {
      fetchContent();
    }
  }, [user]);

  const fetchContent = async () => {
    setIsLoading(true);
    try {
      // Fetch suggested posts
      const { data: postsData, error: postsError } = await supabase
        .from('suggested_posts')
        .select('*')
        .eq('user_id', user?.id)
        .order('created_at', { ascending: false })
        .limit(10);

      if (postsError) throw postsError;

      // Fetch scraped content
      const { data: contentData, error: contentError } = await supabase
        .from('scraped_content')
        .select('*')
        .eq('user_id', user?.id)
        .order('scraped_at', { ascending: false })
        .limit(20);

      if (contentError) throw contentError;

      setSuggestedPosts(postsData || []);
      setScrapedContent(contentData || []);
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

  const generateSuggestions = async () => {
    setIsGenerating(true);
    try {
      // This would typically call an edge function to scrape content and generate suggestions
      // For now, we'll create some sample data
      const samplePost = {
        user_id: user?.id,
        title: "AI Revolution in Content Creation",
        content: "The landscape of content creation is rapidly evolving with AI tools...",
        relevance_score: 0.85,
        topics: ['AI', 'Content Creation', 'Technology'],
        status: 'suggested'
      };

      const { error } = await supabase
        .from('suggested_posts')
        .insert([samplePost]);

      if (error) throw error;

      toast({
        title: "Success",
        description: "New content suggestions generated!",
      });

      fetchContent();
    } catch (error) {
      console.error('Error generating suggestions:', error);
      toast({
        title: "Error",
        description: "Failed to generate suggestions",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const updatePostStatus = async (postId: string, status: string) => {
    try {
      const { error } = await supabase
        .from('suggested_posts')
        .update({ status })
        .eq('id', postId);

      if (error) throw error;

      setSuggestedPosts(prev => 
        prev.map(post => 
          post.id === postId ? { ...post, status } : post
        )
      );

      toast({
        title: "Success",
        description: `Post ${status === 'posted' ? 'marked as posted' : 'dismissed'}`,
      });
    } catch (error) {
      console.error('Error updating post status:', error);
      toast({
        title: "Error",
        description: "Failed to update post status",
        variant: "destructive",
      });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
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
              onClick={generateSuggestions}
              disabled={isGenerating}
              variant="outline"
              size="sm"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isGenerating ? 'animate-spin' : ''}`} />
              {isGenerating ? 'Generating...' : 'Generate New'}
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
              Discover personalized LinkedIn post suggestions based on your interests and writing style
            </p>
          </div>

          <Tabs defaultValue="suggestions" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="suggestions">Suggested Posts ({suggestedPosts.length})</TabsTrigger>
              <TabsTrigger value="sources">Source Content ({scrapedContent.length})</TabsTrigger>
            </TabsList>

            <TabsContent value="suggestions" className="space-y-4">
              {isLoading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                  <p className="text-gray-600">Loading suggestions...</p>
                </div>
              ) : suggestedPosts.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <Sparkles className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-lg font-medium mb-2">No suggestions yet</h3>
                    <p className="text-gray-600 mb-4">
                      Set up your preferences and connected platforms to get personalized content suggestions
                    </p>
                    <Button onClick={generateSuggestions} disabled={isGenerating}>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generate Suggestions
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {suggestedPosts.map((post) => (
                    <Card key={post.id} className="overflow-hidden">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg mb-2">{post.title}</CardTitle>
                            <div className="flex items-center gap-2 mb-2">
                              <Badge className={getRelevanceColor(post.relevance_score)}>
                                {Math.round(post.relevance_score * 100)}% match
                              </Badge>
                              <span className="text-sm text-gray-500">
                                {formatDate(post.created_at)}
                              </span>
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {post.topics.map((topic, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {topic}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="flex gap-2">
                            {post.status === 'suggested' && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => updatePostStatus(post.id, 'dismissed')}
                                >
                                  <ThumbsDown className="w-4 h-4" />
                                </Button>
                                <Button
                                  size="sm"
                                  onClick={() => updatePostStatus(post.id, 'posted')}
                                >
                                  <Share className="w-4 h-4 mr-1" />
                                  Use
                                </Button>
                              </>
                            )}
                            {post.status === 'posted' && (
                              <Badge variant="secondary">Posted</Badge>
                            )}
                            {post.status === 'dismissed' && (
                              <Badge variant="outline">Dismissed</Badge>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-700 leading-relaxed">
                          {post.content.length > 300 
                            ? `${post.content.substring(0, 300)}...` 
                            : post.content
                          }
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="sources" className="space-y-4">
              {scrapedContent.length === 0 ? (
                <Card>
                  <CardContent className="py-12 text-center">
                    <ExternalLink className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-lg font-medium mb-2">No source content</h3>
                    <p className="text-gray-600">
                      Content will appear here once we start scraping your preferred websites
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4">
                  {scrapedContent.map((content) => (
                    <Card key={content.id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg mb-2">{content.title}</CardTitle>
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline">{content.source_type}</Badge>
                              <span className="text-sm text-gray-500">
                                {formatDate(content.scraped_at)}
                              </span>
                              <a
                                href={content.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:text-blue-800"
                              >
                                <ExternalLink className="w-4 h-4" />
                              </a>
                            </div>
                            <div className="flex flex-wrap gap-1">
                              {content.topics.map((topic, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {topic}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-700 leading-relaxed">
                          {content.content.length > 200 
                            ? `${content.content.substring(0, 200)}...` 
                            : content.content
                          }
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </SidebarInset>
  );
};

export default MyContent;
