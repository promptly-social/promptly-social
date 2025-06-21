import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Clock,
  RefreshCw,
  Calendar,
  X,
  TrendingUp,
  User,
  Globe,
  Share2,
} from "lucide-react";
import { profileApi, SocialConnection } from "@/lib/profile-api";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface SuggestedPost {
  id: string;
  content: string;
  topic: string;
  engagementScore: number;
  trendingKeywords: string[];
  estimatedReach: string;
  bestTimeToPost: string;
  source: "preferences" | "substack" | "connections";
}

export const SuggestedPosts: React.FC = () => {
  const [posts, setPosts] = useState<SuggestedPost[]>([
    {
      id: "1",
      content:
        "The future of AI in content creation is here. As we embrace these new tools, the key is finding the balance between automation and authentic human storytelling. What's your take on AI-assisted writing?",
      topic: "AI & Technology",
      engagementScore: 8.5,
      trendingKeywords: ["AI", "Content Creation", "Automation"],
      estimatedReach: "2.5K - 5K",
      bestTimeToPost: "Today, 2:00 PM",
      source: "preferences",
    },
    {
      id: "2",
      content:
        "Remote work has fundamentally changed how we think about productivity. It's not about the hours you put in, but the value you create. Here are 3 strategies that have transformed my remote work experience...",
      topic: "Remote Work",
      engagementScore: 9.2,
      trendingKeywords: ["Remote Work", "Productivity", "Work-Life Balance"],
      estimatedReach: "3K - 7K",
      bestTimeToPost: "Tomorrow, 9:00 AM",
      source: "substack",
    },
    {
      id: "3",
      content:
        "Personal branding isn't about creating a fake persona—it's about amplifying your authentic self. The most successful professionals are those who aren't afraid to show their personality alongside their expertise.",
      topic: "Personal Branding",
      engagementScore: 7.8,
      trendingKeywords: [
        "Personal Branding",
        "Authenticity",
        "Professional Growth",
      ],
      estimatedReach: "1.8K - 4K",
      bestTimeToPost: "Today, 6:00 PM",
      source: "connections",
    },
    {
      id: "4",
      content:
        "The startup ecosystem is evolving rapidly. What worked 5 years ago might not work today. Here's what I've learned about building resilient startups in an uncertain market...",
      topic: "Entrepreneurship",
      engagementScore: 8.9,
      trendingKeywords: ["Startups", "Entrepreneurship", "Market Trends"],
      estimatedReach: "4K - 8K",
      bestTimeToPost: "Tomorrow, 11:00 AM",
      source: "preferences",
    },
    {
      id: "5",
      content:
        "Data-driven decision making is crucial, but don't let analytics paralyze you. Sometimes the best insights come from customer conversations, not spreadsheets. Balance is key.",
      topic: "Data & Analytics",
      engagementScore: 7.5,
      trendingKeywords: [
        "Data Analytics",
        "Decision Making",
        "Customer Insights",
      ],
      estimatedReach: "2K - 4.5K",
      bestTimeToPost: "Today, 4:00 PM",
      source: "substack",
    },
  ]);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isSharing, setIsSharing] = useState<string | null>(null);
  const [linkedinConnection, setLinkedinConnection] =
    useState<SocialConnection | null>(null);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    const fetchConnections = async () => {
      try {
        const connections = await profileApi.getSocialConnections();
        const linkedIn =
          connections.find((c) => c.platform === "linkedin" && c.is_active) ||
          null;
        setLinkedinConnection(linkedIn);
      } catch (error) {
        console.error("Error fetching social connections:", error);
        // Do not bother user with a toast for this, as it's a background check
      }
    };

    if (user) {
      fetchConnections();
    }
  }, [user]);

  const dismissPost = (postId: string) => {
    setPosts(posts.filter((post) => post.id !== postId));
  };

  const shareOnLinkedIn = async (post: SuggestedPost) => {
    setIsSharing(post.id);
    try {
      await profileApi.shareOnLinkedIn(post.content);
      toast({
        title: "Post Shared",
        description: "Your post has been successfully shared on LinkedIn.",
      });
    } catch (error) {
      console.error("Error sharing on LinkedIn:", error);
      toast({
        title: "Sharing Failed",
        description:
          "Could not share the post on LinkedIn. Please check your connection and try again.",
        variant: "destructive",
      });
    } finally {
      setIsSharing(null);
    }
  };

  const schedulePost = (postId: string) => {
    console.log("Scheduling post:", postId);
    // TODO: Implement scheduling logic
  };

  const generateNewPosts = async () => {
    setIsGenerating(true);
    // Simulate API call
    setTimeout(() => {
      setIsGenerating(false);
      // TODO: Implement actual post generation
    }, 2000);
  };

  const getSourceIcon = (source: string) => {
    switch (source) {
      case "preferences":
        return <User className="w-3 h-3" />;
      case "substack":
        return <Globe className="w-3 h-3" />;
      case "connections":
        return <TrendingUp className="w-3 h-3" />;
      default:
        return <User className="w-3 h-3" />;
    }
  };

  const getSourceLabel = (source: string) => {
    switch (source) {
      case "preferences":
        return "Your Topics";
      case "substack":
        return "Substack Insights";
      case "connections":
        return "Network Trends";
      default:
        return "Unknown";
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900">
            Suggested LinkedIn Posts
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            AI-curated content based on your writing style and interests
          </p>
        </div>
        <Button
          onClick={generateNewPosts}
          disabled={isGenerating}
          className="bg-blue-600 hover:bg-blue-700 w-full sm:w-auto"
        >
          {isGenerating ? (
            <>
              <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              Generate New Posts
            </>
          )}
        </Button>
      </div>

      <div className="grid gap-4 sm:gap-6">
        {posts.map((post, index) => (
          <Card
            key={post.id}
            className="relative hover:shadow-md transition-shadow"
          >
            <CardHeader className="pb-3 sm:pb-4">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="secondary" className="text-xs">
                      {getSourceIcon(post.source)}
                      <span className="ml-1">
                        {getSourceLabel(post.source)}
                      </span>
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {post.topic}
                    </Badge>
                  </div>
                  <CardTitle className="text-base sm:text-lg font-semibold text-gray-900">
                    Post #{index + 1}
                  </CardTitle>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => dismissPost(post.id)}
                  className="text-gray-400 hover:text-gray-600 absolute top-2 right-2 sm:relative sm:top-0 sm:right-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-gray-50 p-3 sm:p-4 rounded-lg">
                <p className="text-sm sm:text-base text-gray-800 leading-relaxed">
                  {post.content}
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 text-xs sm:text-sm">
                <div className="flex items-center gap-2 text-gray-600">
                  <TrendingUp className="w-4 h-4 text-green-500" />
                  <span>
                    Engagement Score: <strong>{post.engagementScore}/10</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Clock className="w-4 h-4 text-blue-500" />
                  <span>
                    Best time: <strong>{post.bestTimeToPost}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <User className="w-4 h-4 text-purple-500" />
                  <span>
                    Est. Reach: <strong>{post.estimatedReach}</strong>
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs sm:text-sm font-medium text-gray-700">
                  Trending Keywords:
                </p>
                <div className="flex flex-wrap gap-1 sm:gap-2">
                  {post.trendingKeywords.map((keyword, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-3 border-t border-gray-100">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <div className="flex-1">
                      <Button
                        onClick={() => shareOnLinkedIn(post)}
                        disabled={!linkedinConnection || isSharing === post.id}
                        className="bg-blue-600 hover:bg-blue-700 w-full"
                      >
                        {isSharing === post.id ? (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Sharing...
                          </>
                        ) : (
                          <>
                            <Share2 className="w-4 h-4 mr-2" />
                            Share on LinkedIn
                          </>
                        )}
                      </Button>
                    </div>
                  </TooltipTrigger>
                  {!linkedinConnection && (
                    <TooltipContent>
                      <p>
                        Connect your LinkedIn account in Settings to share
                        posts.
                      </p>
                    </TooltipContent>
                  )}
                </Tooltip>
                <Button
                  onClick={() => schedulePost(post.id)}
                  className="bg-green-600 hover:bg-green-700 flex-1"
                >
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Post
                </Button>
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => navigator.clipboard.writeText(post.content)}
                >
                  Copy Content
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {posts.length === 0 && (
        <Card className="text-center py-8 sm:py-12">
          <CardContent>
            <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No posts available
            </h3>
            <p className="text-gray-600 mb-4 text-sm sm:text-base">
              All posts have been dismissed. Generate new content suggestions to
              continue.
            </p>
            <Button onClick={generateNewPosts} disabled={isGenerating}>
              {isGenerating ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Generate New Posts
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
