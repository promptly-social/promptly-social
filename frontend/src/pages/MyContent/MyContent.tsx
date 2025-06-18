import React, { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import AppLayout from "@/components/AppLayout";
import {
  contentApi,
  type ContentIdea as ApiContentIdea,
} from "@/lib/content-api";
import { useToast } from "@/hooks/use-toast";
import {
  ExternalLink,
  RefreshCw,
  Calendar,
  CheckCircle,
  XCircle,
  Trash2,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type ContentIdea = ApiContentIdea;

const MyContent: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [pastPosts, setPastPosts] = useState<ContentIdea[]>([]);
  const [scheduledPosts, setScheduledPosts] = useState<ContentIdea[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCancelling, setIsCancelling] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchContent();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const fetchContent = async () => {
    setIsLoading(true);
    try {
      // Fetch past posts (published or failed)
      const pastData = await contentApi.getContentIdeas({
        status: ["published", "failed"],
        order_by: "published_date",
        order_direction: "desc",
        size: 100, // Get more past posts
      });

      // Fetch scheduled posts
      const scheduledData = await contentApi.getContentIdeas({
        status: ["scheduled"],
        order_by: "scheduled_date",
        order_direction: "asc",
        size: 100, // Get all scheduled posts
      });

      setPastPosts(pastData.items || []);
      setScheduledPosts(scheduledData.items || []);
    } catch (error) {
      console.error("Error fetching content:", error);
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
      await contentApi.updateContentIdea(postId, {
        status: "draft",
        scheduled_date: undefined,
      });

      // Move from scheduled to remove from list
      setScheduledPosts((prev) => prev.filter((post) => post.id !== postId));

      toast({
        title: "Success",
        description: "Scheduled post cancelled successfully",
      });
    } catch (error) {
      console.error("Error cancelling post:", error);
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
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusBadge = (status: string, error?: string | null) => {
    switch (status) {
      case "published":
        return (
          <Badge className="bg-green-100 text-green-800">
            <CheckCircle className="w-3 h-3 mr-1" />
            Published
          </Badge>
        );
      case "failed":
        return (
          <Badge className="bg-red-100 text-red-800">
            <XCircle className="w-3 h-3 mr-1" />
            Failed
          </Badge>
        );
      case "scheduled":
        return (
          <Badge className="bg-blue-100 text-blue-800">
            <Calendar className="w-3 h-3 mr-1" />
            Scheduled
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const refreshButton = (
    <Button
      onClick={fetchContent}
      disabled={isLoading}
      variant="outline"
      size="sm"
    >
      <RefreshCw
        className={`w-4 h-4 ${isLoading ? "animate-spin" : ""} sm:mr-2`}
      />
      <span className="hidden sm:inline">Refresh</span>
    </Button>
  );

  return (
    <AppLayout
      title="My Content"
      emailBreakpoint="md"
      additionalActions={refreshButton}
    >
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-4 sm:mb-8">
            <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto">
              View your published content and manage scheduled posts
            </p>
          </div>

          <Tabs defaultValue="past" className="space-y-4 sm:space-y-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="past" className="text-xs sm:text-sm">
                Past Posts ({pastPosts.length})
              </TabsTrigger>
              <TabsTrigger value="scheduled" className="text-xs sm:text-sm">
                Scheduled Posts ({scheduledPosts.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="past" className="space-y-4">
              {isLoading ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                  <p className="text-gray-600">Loading past posts...</p>
                </div>
              ) : pastPosts.length === 0 ? (
                <Card>
                  <CardContent className="py-8 sm:py-12 text-center">
                    <CheckCircle className="w-8 sm:w-12 h-8 sm:h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-base sm:text-lg font-medium mb-2">
                      No past posts
                    </h3>
                    <p className="text-sm sm:text-base text-gray-600">
                      Your published content will appear here
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {/* Mobile Card View */}
                  <div className="block sm:hidden space-y-4">
                    {pastPosts.map((post) => (
                      <Card key={post.id}>
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-sm truncate">
                                {post.title}
                              </h4>
                              <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                {post.original_input.substring(0, 80)}...
                              </p>
                            </div>
                            {getStatusBadge(
                              post.status,
                              post.publication_error
                            )}
                          </div>
                        </CardHeader>
                        <CardContent className="pt-0">
                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <span>{formatDate(post.published_date)}</span>
                            {post.linkedin_post_id && (
                              <Button variant="outline" size="sm" asChild>
                                <a
                                  href={`https://linkedin.com/feed/update/${post.linkedin_post_id}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              </Button>
                            )}
                          </div>
                          {post.publication_error && (
                            <p className="text-xs text-red-600 mt-2">
                              {post.publication_error}
                            </p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Desktop Table View */}
                  <Card className="hidden sm:block">
                    <div className="overflow-x-auto">
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
                                  {post.content_type.replace("_", " ")}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                {getStatusBadge(
                                  post.status,
                                  post.publication_error
                                )}
                                {post.publication_error && (
                                  <p className="text-xs text-red-600 mt-1">
                                    {post.publication_error}
                                  </p>
                                )}
                              </TableCell>
                              <TableCell>
                                {formatDate(post.published_date)}
                              </TableCell>
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
                    </div>
                  </Card>
                </div>
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
                  <CardContent className="py-8 sm:py-12 text-center">
                    <Calendar className="w-8 sm:w-12 h-8 sm:h-12 mx-auto mb-4 text-gray-400" />
                    <h3 className="text-base sm:text-lg font-medium mb-2">
                      No scheduled posts
                    </h3>
                    <p className="text-sm sm:text-base text-gray-600">
                      Your scheduled content will appear here
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-4">
                  {/* Mobile Card View */}
                  <div className="block sm:hidden space-y-4">
                    {scheduledPosts.map((post) => (
                      <Card key={post.id}>
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-sm truncate">
                                {post.title}
                              </h4>
                              <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                                {post.original_input.substring(0, 80)}...
                              </p>
                            </div>
                            <Badge variant="outline" className="text-xs">
                              {post.content_type.replace("_", " ")}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent className="pt-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500">
                              {formatDate(post.scheduled_date)}
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => cancelScheduledPost(post.id)}
                              disabled={isCancelling === post.id}
                            >
                              <Trash2 className="w-3 h-3 mr-1" />
                              {isCancelling === post.id
                                ? "Cancelling..."
                                : "Cancel"}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {/* Desktop Table View */}
                  <Card className="hidden sm:block">
                    <div className="overflow-x-auto">
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
                                  {post.content_type.replace("_", " ")}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                {formatDate(post.scheduled_date)}
                              </TableCell>
                              <TableCell>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => cancelScheduledPost(post.id)}
                                  disabled={isCancelling === post.id}
                                >
                                  <Trash2 className="w-4 h-4 mr-1" />
                                  {isCancelling === post.id
                                    ? "Cancelling..."
                                    : "Cancel"}
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </Card>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </AppLayout>
  );
};

export default MyContent;
