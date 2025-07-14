import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import {
  ArrowUpDown,
  Plus,
  Trash2,
  ExternalLink,
  Edit,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import {
  ideaBankApi,
  type IdeaBankWithPost,
  type IdeaBankCreate,
  type IdeaBankFilters,
  type SuggestedPost,
} from "@/lib/idea-bank-api";
import { postsApi, type Post } from "@/lib/posts-api";
import AppLayout from "@/components/AppLayout";
import { ScheduledPostDetails } from "@/components/ScheduledPostDetails";
import { RescheduleModal } from "@/components/RescheduleModal";
import { PostScheduleModal } from "@/components/PostScheduleModal";
import { PostGenerationChatDialog } from "@/components/chat/PostGenerationChatDialog";

interface SortConfig {
  key: "updated_at";
  direction: "asc" | "desc";
}

const IdeaBank: React.FC = () => {
  const [ideaBanksWithPosts, setIdeaBanksWithPosts] = useState<
    IdeaBankWithPost[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: "updated_at",
    direction: "desc",
  });

  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingIdeaBank, setEditingIdeaBank] =
    useState<IdeaBankWithPost | null>(null);
  const [editFormData, setEditFormData] = useState<
    IdeaBankCreate["data"] | null
  >(null);
  const [ideaToGenerate, setIdeaToGenerate] = useState<IdeaBankWithPost | null>(
    null
  );
  const [generatedPost, setGeneratedPost] = useState<Post | null>(null);
  const [showRescheduleModal, setShowRescheduleModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduledPosts, setScheduledPosts] = useState<Post[]>([]);
  const [formData, setFormData] = useState<IdeaBankCreate>({
    data: {
      type: "text",
      value: "",
      title: "",
      time_sensitive: false,
      ai_suggested: false,
    },
  });

  const resetFormData = () => {
    setFormData({
      data: {
        type: "text",
        value: "",
        title: "",
        time_sensitive: false,
        ai_suggested: false,
      },
    });
  };

  useEffect(() => {
    loadIdeaBanks();
    loadScheduledPosts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortConfig]);

  const loadScheduledPosts = async () => {
    try {
      const response = await postsApi.getPosts({
        status: ["scheduled"],
        size: 100,
      });
      setScheduledPosts(response.items);
    } catch (error) {
      console.error("Failed to load scheduled posts:", error);
      // Do not show toast here as it's a background fetch
    }
  };

  const loadIdeaBanks = async () => {
    try {
      setLoading(true);
      const filterParams: IdeaBankFilters = {
        order_by: "updated_at",
        order_direction: sortConfig.direction,
        size: 100,
        ai_suggested: false,
      };

      const response = await ideaBankApi.listWithPosts(filterParams);
      setIdeaBanksWithPosts(response.items);
    } catch (error) {
      console.error("Failed to load idea banks:", error);
      toast.error("Failed to load idea banks");
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (key: SortConfig["key"]) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  const handleCreate = async () => {
    try {
      await ideaBankApi.create(formData);
      toast.success("Idea bank created successfully");
      setShowCreateDialog(false);
      resetFormData();
      loadIdeaBanks();
    } catch (error) {
      console.error("Failed to create idea bank:", error);
      toast.error("Failed to create idea bank");
    }
  };

  const handleEdit = (ideaBankWithPost: IdeaBankWithPost) => {
    setEditingIdeaBank(ideaBankWithPost);
    const ideaBank = ideaBankWithPost.idea_bank;

    setEditFormData({
      type: ideaBank.data.type,
      value: ideaBank.data.value,
      title: ideaBank.data.title || "",
      time_sensitive: ideaBank.data.time_sensitive || false,
      ai_suggested: ideaBank.data.ai_suggested || false,
    });
    setShowEditDialog(true);
  };

  const handleUpdate = async () => {
    if (!editingIdeaBank || !editFormData) return;

    try {
      await ideaBankApi.update(editingIdeaBank.idea_bank.id, {
        data: editFormData,
      });
      toast.success("Idea bank updated successfully");
      setShowEditDialog(false);
      setEditingIdeaBank(null);
      setEditFormData(null);
      loadIdeaBanks();
    } catch (error) {
      console.error("Failed to update idea bank:", error);
      toast.error("Failed to update idea bank");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this idea bank entry?")) {
      return;
    }

    try {
      await ideaBankApi.delete(id);
      toast.success("Idea bank deleted successfully");
      loadIdeaBanks();
    } catch (error) {
      console.error("Failed to delete idea bank:", error);
      toast.error("Failed to delete idea bank");
    }
  };

  const handleSavePostForLater = async (post: Post) => {
    try {
      await postsApi.updatePost(post.id, { status: "saved" });
      toast.success("Post saved for later.");
      setGeneratedPost(null);
      loadIdeaBanks(); // Refresh to show updated post status
    } catch (error) {
      console.error("Failed to save post for later:", error);
      toast.error("Failed to save post for later.");
    }
  };

  const handleDismissPost = async (post: Post) => {
    try {
      await postsApi.dismissPost(post.id);
      toast.success("Generated post dismissed.");
      setGeneratedPost(null);
    } catch (error) {
      console.error("Failed to dismiss post:", error);
      toast.error("Failed to dismiss post.");
    }
  };

  const openScheduleModal = async (postToSchedule: Post) => {
    try {
      // Always fetch the latest scheduled posts before opening the modal
      const response = await postsApi.getPosts({
        status: ["scheduled"],
        size: 100,
      });
      setScheduledPosts(response.items);
      setGeneratedPost(postToSchedule);
      setShowScheduleModal(true);
    } catch (error) {
      console.error("Failed to load scheduled posts:", error);
      toast.error("Could not open the schedule modal. Please try again.");
    }
  };

  const handleSchedulePost = async (postId: string, scheduledAt: string) => {
    try {
      const scheduledPost = await postsApi.schedulePost(postId, scheduledAt);
      toast.success("Post scheduled successfully!");
      setGeneratedPost(null);
      setShowRescheduleModal(false);
      setShowScheduleModal(false);
      loadIdeaBanks();
      // Optimistically update the scheduled posts list
      setScheduledPosts((prev) => [...prev, scheduledPost]);
    } catch (error) {
      console.error("Failed to schedule post:", error);
      toast.error("Failed to schedule post.");
    }
  };

  const getSortedData = () => {
    const sorted = [...ideaBanksWithPosts].sort((a, b) => {
      let aValue: string | number | boolean;
      let bValue: string | number | boolean;

      switch (sortConfig.key) {
        case "updated_at":
          aValue = new Date(a.idea_bank.updated_at).getTime();
          bValue = new Date(b.idea_bank.updated_at).getTime();
          break;
        default:
          aValue = a.idea_bank.updated_at;
          bValue = b.idea_bank.updated_at;
      }

      if (sortConfig.direction === "asc") {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    return sorted;
  };

  const isUrl = (value: string) => {
    try {
      new URL(value);
      return true;
    } catch {
      return false;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getStatusColor = (status: string) => {
    const statusColors: Record<string, string> = {
      suggested: "bg-gray-100 text-gray-800",
      saved: "bg-purple-100 text-purple-800",
      posted: "bg-green-100 text-green-800",
      scheduled: "bg-yellow-100 text-yellow-800",
      canceled: "bg-orange-100 text-orange-800",
      dismissed: "bg-red-100 text-red-800",
    };
    return statusColors[status] || "bg-gray-100 text-gray-800";
  };

  const navigateToSuggestedPost = (post: SuggestedPost) => {
    // Navigate to the my content page with this post selected
    window.open(`/my-posts?post=${post.id}`, "_blank");
  };

  const renderIdeaBankContent = (ideaBank: IdeaBankWithPost["idea_bank"]) => {
    return (
      <div className="space-y-1">
        {ideaBank.data.title && (
          <div className="font-medium text-sm text-gray-900">
            {ideaBank.data.title}
          </div>
        )}
        {isUrl(ideaBank.data.value) ? (
          <a
            href={ideaBank.data.value}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-start gap-1 text-blue-600 hover:text-blue-800 hover:underline break-all text-sm"
          >
            <span className="break-all">{ideaBank.data.value}</span>
            <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
          </a>
        ) : (
          <div className="whitespace-pre-wrap break-words text-sm">
            {ideaBank.data.value}
          </div>
        )}
      </div>
    );
  };

  const renderLastPostUsed = (latestPost: SuggestedPost | undefined) => {
    if (!latestPost) {
      return <span className="text-muted-foreground">No post created yet</span>;
    }

    return (
      <div className="space-y-1">
        <button
          onClick={() => navigateToSuggestedPost(latestPost)}
          className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1"
        >
          View Post
          <ExternalLink className="w-3 h-3" />
        </button>
        <div>
          <Badge
            className={getStatusColor(latestPost.status)}
            variant="secondary"
          >
            {latestPost.status.charAt(0).toUpperCase() +
              latestPost.status.slice(1)}
          </Badge>
        </div>
      </div>
    );
  };

  const Actions: React.FC<{ ideaBankWithPost: IdeaBankWithPost }> = ({
    ideaBankWithPost,
  }) => (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIdeaToGenerate(ideaBankWithPost)}
        className="text-indigo-600 hover:text-indigo-800 p-1 h-8 w-8"
      >
        <Sparkles className="w-4 h-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleEdit(ideaBankWithPost)}
        className="text-blue-600 hover:text-blue-800 p-1 h-8 w-8"
      >
        <Edit className="w-4 h-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleDelete(ideaBankWithPost.idea_bank.id)}
        className="text-red-600 hover:text-red-800 p-1 h-8 w-8"
      >
        <Trash2 className="w-4 h-4" />
      </Button>
    </div>
  );

  const SortButton: React.FC<{
    column: SortConfig["key"];
    children: React.ReactNode;
  }> = ({ column, children }) => (
    <Button
      variant="ghost"
      onClick={() => handleSort(column)}
      className="flex items-center gap-1 font-semibold"
    >
      {children}
      <ArrowUpDown className="w-4 h-4" />
    </Button>
  );

  const addButton = (
    <Dialog
      open={showCreateDialog}
      onOpenChange={(isOpen) => {
        if (isOpen) {
          resetFormData();
        }
        setShowCreateDialog(isOpen);
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Idea
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add New Idea</DialogTitle>
          <DialogDescription>
            Create a new idea bank entry to organize your content inspirations.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Textarea
              id="value"
              placeholder="Enter your idea or drop in a URL to an article or post..."
              value={formData.data.value}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...prev,
                  data: { ...prev.data, value: e.target.value },
                }))
              }
              rows={4}
              className="min-h-[100px] resize-none"
            />
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button onClick={handleCreate} disabled={!formData.data.value.trim()}>
            Create
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  if (loading) {
    return (
      <AppLayout title="Ideas" emailBreakpoint="md">
        <main className="py-4 px-4 sm:py-8 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
              <p className="text-gray-600">Loading your ideas...</p>
            </div>
          </div>
        </main>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Ideas" emailBreakpoint="md">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-7xl mx-auto">
          {/* Page Header with Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div className="text-center sm:text-left">
              <p className="text-sm sm:text-lg text-gray-600 max-w-2xl">
                Manage your content ideas and inspirations
              </p>
            </div>
            <div className="flex items-center justify-end sm:justify-end gap-2">
              {addButton}
            </div>
          </div>

          {/* Mobile Card Layout */}
          <div className="block md:hidden space-y-4">
            {/* Mobile Sort Info */}
            <div className="flex items-center justify-between text-sm text-gray-500 px-1">
              <span>
                Sorted by: {"Last Updated"} (
                {sortConfig.direction === "asc" ? "↑" : "↓"})
              </span>
              <span>{getSortedData().length} ideas</span>
            </div>

            {getSortedData().length === 0 ? (
              <div className="text-center py-8 bg-white rounded-lg border">
                <div className="text-muted-foreground">
                  No ideas found. Create your first idea to get started.
                </div>
              </div>
            ) : (
              getSortedData().map((ideaBankWithPost) => {
                const ideaBank = ideaBankWithPost.idea_bank;
                const latestPost = ideaBankWithPost.latest_post;
                return (
                  <div
                    key={ideaBank.id}
                    className="bg-white rounded-lg border p-4 space-y-3"
                  >
                    <div className="space-y-2">
                      <div>
                        <span className="text-sm font-medium text-gray-500">
                          Content:
                        </span>
                        <div className="mt-1">
                          {renderIdeaBankContent(ideaBank)}
                        </div>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <div className="text-gray-500">
                          {formatDate(ideaBank.updated_at)}
                        </div>
                      </div>

                      <div>
                        <span className="text-sm font-medium text-gray-500">
                          Last Post Used:
                        </span>
                        <div className="mt-1">
                          {renderLastPostUsed(latestPost)}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Desktop Table Layout */}
          <div className="hidden xl:block border rounded-lg overflow-x-auto">
            <Table className="min-w-full">
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[200px]">Content</TableHead>
                  <TableHead className="w-[150px]">
                    <SortButton column="updated_at">Last Updated</SortButton>
                  </TableHead>
                  <TableHead className="w-[180px]">Last Post Used</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {getSortedData().length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      <div className="text-muted-foreground">
                        No ideas found. Create your first idea to get started.
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  getSortedData().map((ideaBankWithPost) => {
                    const ideaBank = ideaBankWithPost.idea_bank;
                    const latestPost = ideaBankWithPost.latest_post;
                    return (
                      <TableRow key={ideaBank.id}>
                        <TableCell className="min-w-0">
                          {renderIdeaBankContent(ideaBank)}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {formatDate(ideaBank.updated_at)}
                        </TableCell>
                        <TableCell>{renderLastPostUsed(latestPost)}</TableCell>
                        <TableCell>
                          <Actions ideaBankWithPost={ideaBankWithPost} />
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>

          {/* Medium Screen Table Layout */}
          <div className="hidden md:block xl:hidden border rounded-lg overflow-x-auto">
            <Table className="min-w-full">
              <TableHeader>
                <TableRow>
                  <TableHead className="min-w-[250px]">Content</TableHead>
                  <TableHead className="w-[120px]">
                    <SortButton column="updated_at">Updated</SortButton>
                  </TableHead>
                  <TableHead className="w-[140px]">Last Used</TableHead>
                  <TableHead className="w-[80px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {getSortedData().length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8">
                      <div className="text-muted-foreground">
                        No ideas found. Create your first idea to get started.
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  getSortedData().map((ideaBankWithPost) => {
                    const ideaBank = ideaBankWithPost.idea_bank;
                    const latestPost = ideaBankWithPost.latest_post;
                    return (
                      <TableRow key={ideaBank.id}>
                        <TableCell className="min-w-0">
                          {renderIdeaBankContent(ideaBank)}
                        </TableCell>
                        <TableCell className="text-muted-foreground text-sm">
                          {new Date(ideaBank.updated_at).toLocaleDateString(
                            "en-US",
                            {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            }
                          )}
                        </TableCell>
                        <TableCell className="text-sm">
                          {latestPost ? (
                            <div className="space-y-1">
                              <button
                                onClick={() =>
                                  navigateToSuggestedPost(latestPost)
                                }
                                className="text-blue-600 hover:text-blue-800 hover:underline text-xs flex items-center gap-1"
                              >
                                View
                                <ExternalLink className="w-3 h-3" />
                              </button>
                              <Badge
                                className={`${getStatusColor(
                                  latestPost.status
                                )} text-xs`}
                                variant="secondary"
                              >
                                {latestPost.status.charAt(0).toUpperCase() +
                                  latestPost.status.slice(1)}
                              </Badge>
                            </div>
                          ) : (
                            <span className="text-muted-foreground text-xs">
                              No post created yet
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col items-center gap-1">
                            <Actions ideaBankWithPost={ideaBankWithPost} />
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </main>

      {/* Edit Dialog */}
      <Dialog
        open={showEditDialog}
        onOpenChange={(isOpen) => {
          setShowEditDialog(isOpen);
          if (!isOpen) {
            setEditingIdeaBank(null);
            setEditFormData(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Idea</DialogTitle>
            <DialogDescription>Update your idea bank entry.</DialogDescription>
          </DialogHeader>
          {editFormData && (
            <>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Textarea
                    key="value-textarea"
                    id="edit-value"
                    placeholder="Enter your idea or text content..."
                    value={editFormData.value}
                    onChange={(e) =>
                      setEditFormData((prev) => ({
                        ...prev!,
                        value: e.target.value,
                      }))
                    }
                    rows={4}
                    className="min-h-[100px] resize-none"
                  />
                </div>
              </div>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="outline">Cancel</Button>
                </DialogClose>
                <Button
                  onClick={handleUpdate}
                  disabled={!editFormData.value.trim()}
                >
                  Update
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Generate Post Confirmation Dialog */}
      <PostGenerationChatDialog
        idea={ideaToGenerate}
        open={!!ideaToGenerate}
        onOpenChange={(isOpen) => !isOpen && setIdeaToGenerate(null)}
        onScheduleComplete={loadIdeaBanks}
      />

      {/* Generated Post Details Modal */}
      {generatedPost && (
        <ScheduledPostDetails
          isOpen={!!generatedPost}
          onClose={() => setGeneratedPost(null)}
          post={generatedPost}
          onSaveForLater={handleSavePostForLater}
          onReschedule={openScheduleModal}
          onDelete={handleDismissPost}
          isNewPost={true}
        />
      )}

      {/* Reschedule Modal */}
      {showRescheduleModal && generatedPost && (
        <RescheduleModal
          post={generatedPost}
          isOpen={showRescheduleModal}
          onClose={() => setShowRescheduleModal(false)}
          onReschedule={handleSchedulePost}
          scheduledPosts={scheduledPosts}
        />
      )}

      {/* Schedule Modal for new posts */}
      {showScheduleModal && generatedPost && (
        <PostScheduleModal
          post={generatedPost}
          isOpen={showScheduleModal}
          onClose={() => setShowScheduleModal(false)}
          onSchedule={handleSchedulePost}
          scheduledPosts={scheduledPosts}
        />
      )}
    </AppLayout>
  );
};

export default IdeaBank;
