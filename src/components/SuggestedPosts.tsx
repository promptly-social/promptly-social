
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { ThumbsUp, ThumbsDown, Calendar, Send, RefreshCw, Lightbulb } from 'lucide-react';

interface SuggestedPost {
  id: string;
  title: string;
  content: string;
  topics: string[];
  relevance_score: number;
  original_source_id?: string;
  status: string;
}

export const SuggestedPosts: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [suggestedPosts, setSuggestedPosts] = useState<SuggestedPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (user) {
      fetchSuggestedPosts();
    }
  }, [user]);

  const fetchSuggestedPosts = async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase
        .from('suggested_posts')
        .select('*')
        .eq('user_id', user?.id)
        .eq('status', 'suggested')
        .order('relevance_score', { ascending: false })
        .limit(5);

      if (error) throw error;
      setSuggestedPosts(data || []);
    } catch (error) {
      console.error('Error fetching suggested posts:', error);
      toast({
        title: "Error",
        description: "Failed to load suggested posts",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateSuggestedPosts = async () => {
    setIsGenerating(true);
    try {
      // Generate sample suggested posts based on user preferences
      const samplePosts = [
        {
          title: "The Future of AI in Content Creation",
          content: "As AI continues to evolve, content creators are finding new ways to leverage technology to enhance their storytelling. Here are 3 key trends I'm seeing:\n\n1. AI-assisted research and fact-checking\n2. Personalized content recommendations\n3. Automated content optimization\n\nWhat trends are you noticing in your industry? 🤖✨",
          topics: ["AI", "Content Creation", "Technology"],
          relevance_score: 0.95
        },
        {
          title: "5 Lessons Learned from Building a Remote Team",
          content: "After 2 years of leading a fully remote team, here's what I've learned:\n\n✅ Clear communication beats frequent meetings\n✅ Trust is built through consistent delivery\n✅ Async work requires better documentation\n✅ Culture needs intentional cultivation\n✅ Tools matter, but processes matter more\n\nRemote work isn't just about location - it's about reimagining how we collaborate. What's your biggest remote work insight?",
          topics: ["Remote Work", "Leadership", "Team Management"],
          relevance_score: 0.88
        },
        {
          title: "Why I Stopped Chasing Perfect and Started Shipping",
          content: "Perfectionism was my biggest enemy as an entrepreneur.\n\nI spent months polishing a product that nobody wanted instead of getting feedback early.\n\nNow I follow the 80/20 rule:\n• Ship at 80% perfect\n• Gather real user feedback\n• Iterate based on actual needs\n\nDone is better than perfect. What's holding you back from shipping your idea?",
          topics: ["Entrepreneurship", "Product Development", "Mindset"],
          relevance_score: 0.82
        }
      ];

      // Insert sample posts into database
      for (const post of samplePosts) {
        const { error } = await supabase
          .from('suggested_posts')
          .insert({
            user_id: user?.id,
            title: post.title,
            content: post.content,
            topics: post.topics,
            relevance_score: post.relevance_score,
            status: 'suggested'
          });

        if (error) throw error;
      }

      toast({
        title: "Success",
        description: "Generated new suggested posts based on your preferences",
      });

      fetchSuggestedPosts();
    } catch (error) {
      console.error('Error generating posts:', error);
      toast({
        title: "Error",
        description: "Failed to generate suggested posts",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const dismissPost = async (postId: string) => {
    try {
      const { error } = await supabase
        .from('suggested_posts')
        .update({ status: 'dismissed' })
        .eq('id', postId);

      if (error) throw error;

      setSuggestedPosts(prev => prev.filter(post => post.id !== postId));
      toast({
        title: "Post dismissed",
        description: "This suggestion has been removed",
      });
    } catch (error) {
      console.error('Error dismissing post:', error);
      toast({
        title: "Error",
        description: "Failed to dismiss post",
        variant: "destructive",
      });
    }
  };

  const schedulePost = (post: SuggestedPost) => {
    // This would integrate with the content scheduler
    toast({
      title: "Schedule Post",
      description: "Post scheduling feature coming soon!",
    });
  };

  if (isLoading) {
    return (
      <div className="text-center py-8">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
        <p className="text-gray-600">Loading suggested posts...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Suggested LinkedIn Posts</h2>
          <p className="text-gray-600">AI-curated content based on your interests and writing style</p>
        </div>
        <Button
          onClick={generateSuggestedPosts}
          disabled={isGenerating}
          className="flex items-center gap-2"
        >
          <Lightbulb className="w-4 h-4" />
          {isGenerating ? 'Generating...' : 'Generate New Posts'}
        </Button>
      </div>

      {suggestedPosts.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Lightbulb className="w-12 h-12 mx-auto mb-4 text-gray-400" />
            <h3 className="text-lg font-medium mb-2">No suggested posts yet</h3>
            <p className="text-gray-600 mb-4">
              Generate personalized LinkedIn post suggestions based on your preferences
            </p>
            <Button onClick={generateSuggestedPosts} disabled={isGenerating}>
              <Lightbulb className="w-4 h-4 mr-2" />
              Generate Suggestions
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {suggestedPosts.map((post, index) => (
            <Card key={post.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg font-semibold">
                      #{index + 1} {post.title}
                    </CardTitle>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="secondary" className="text-xs">
                        {Math.round(post.relevance_score * 100)}% match
                      </Badge>
                      {post.topics.map((topic, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-700 whitespace-pre-line">
                    {post.content}
                  </p>
                </div>
                
                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => schedulePost(post)}
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <Calendar className="w-4 h-4" />
                    Schedule
                  </Button>
                  <Button
                    onClick={() => schedulePost(post)}
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-2"
                  >
                    <Send className="w-4 h-4" />
                    Post Now
                  </Button>
                  <Button
                    onClick={() => dismissPost(post.id)}
                    variant="ghost"
                    size="sm"
                    className="flex items-center gap-2 text-gray-500 hover:text-red-600"
                  >
                    <ThumbsDown className="w-4 h-4" />
                    Dismiss
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};
