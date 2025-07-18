import React, { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import IdeaBankMobileView from "@/components/idea-bank/IdeaBankMobileView";
import IdeaBankDesktopView from "@/components/idea-bank/IdeaBankDesktopView";
import IdeaBankMediumView from "@/components/idea-bank/IdeaBankMediumView";
import CreateIdeaDialog from "@/components/idea-bank/CreateIdeaDialog";
import EditIdeaDialog from "@/components/idea-bank/EditIdeaDialog";
import {
  ideaBankApi,
  type IdeaBankWithPost,
  type IdeaBankCreate,
  type IdeaBankFilters,
  type SuggestedPost,
} from "@/lib/idea-bank-api";
import { postsApi } from "@/lib/posts-api";
import { Post } from "@/types/posts";
import AppLayout from "@/components/AppLayout";
import { ScheduledPostDetails } from "@/components/schedule-modal/ScheduledPostDetails";
import { RescheduleModal } from "@/components/schedule-modal/RescheduleModal";
import { PostScheduleModal } from "@/components/schedule-modal/PostScheduleModal";
import { PostGenerationChatDialog } from "@/components/chat/PostGenerationChatDialog";
import { PostCard } from "@/components/shared/post-card/PostCard";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationPrevious,
  PaginationNext,
} from "@/components/ui/pagination";

interface SortConfig {
  key: "updated_at";
  direction: "asc" | "desc";
}

const IdeaBank: React.FC = () => {
  const [ideaBanksWithPosts, setIdeaBanksWithPosts] = useState<
    IdeaBankWithPost[]
  >([]);
  // Local cache for quick UI updates; primary source is React Query data
  // No explicit loading state – we use React Query's `isLoading`.
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: "updated_at",
    direction: "desc",
  });

  // Pagination state
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

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
  const [formData, setFormData] = useState<IdeaBankCreate>({
    data: {
      type: "text",
      value: "",
      title: "",
      time_sensitive: false,
      ai_suggested: false,
    },
  });
  const [selectedPost, setSelectedPost] = useState<Post | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

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

  // React Query fetch + cache
  const queryClient = useQueryClient();

  const { data: queryIdeaBanksData, isLoading: isIdeasLoading } = useQuery({
    queryKey: ["ideaBanks", sortConfig.direction, page, pageSize],
    queryFn: async () => {
      const filterParams: IdeaBankFilters = {
        order_by: "updated_at",
        order_direction: sortConfig.direction,
        size: pageSize,
        page,
        ai_suggested: false,
      };
      return ideaBankApi.listWithPosts(filterParams);
    },
    staleTime: 1000 * 60 * 10, // 10 minutes
  });

  useEffect(() => {
    setIdeaBanksWithPosts(queryIdeaBanksData?.items ?? []);
  }, [queryIdeaBanksData]);

  // Total pages calculation
  const totalItems = queryIdeaBanksData?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));

  // Wrapper to refresh cached data (keeps existing call sites)
  const loadIdeaBanks = async () => {
    await queryClient.invalidateQueries({ queryKey: ["ideaBanks"] });
  };

  const handleSort = (key: SortConfig["key"]) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
    setPage(1); // Reset to first page when sorting changes
  };

  const handleCreate = async () => {
    try {
      await ideaBankApi.create(formData);
      toast.success("Idea bank created successfully");
      setShowCreateDialog(false);
      resetFormData();
      await loadIdeaBanks();
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
      await loadIdeaBanks();
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
      await loadIdeaBanks();
    } catch (error) {
      console.error("Failed to delete idea bank:", error);
      toast.error("Failed to delete idea bank");
    }
  };

  const handleSavePostForLater = async (post: Post) => {
    try {
      await postsApi.updatePost(post.id, { status: "draft" });
      toast.success("Post moved to Drafts.");
      setGeneratedPost(null);
      await loadIdeaBanks(); // Refresh to show updated post status
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
      setGeneratedPost(postToSchedule);
      setShowScheduleModal(true);
    } catch (error) {
      console.error("Failed to load scheduled posts:", error);
      toast.error("Could not open the schedule modal. Please try again.");
    }
  };

  const handleSchedulePost = async (postId: string, scheduledAt: string) => {
    try {
      await postsApi.schedulePost(postId, scheduledAt);
      toast.success("Post scheduled successfully!");
      setGeneratedPost(null);
      setShowRescheduleModal(false);
      setShowScheduleModal(false);
      await loadIdeaBanks();
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const viewPostDetails = (post: SuggestedPost) => {
    setSelectedPost(post as Post);
    setIsModalOpen(true);
  };

  // Removed in-file render components; replaced with extracted ones



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
              {/* Page size selector */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Show</span>
                <Select
                  value={pageSize.toString()}
                  onValueChange={(value) => {
                    setPageSize(Number(value));
                    setPage(1);
                  }}
                >
                  <SelectTrigger className="w-[80px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <CreateIdeaDialog
                isOpen={showCreateDialog}
                onOpenChange={setShowCreateDialog}
                formData={formData}
                onFormDataChange={setFormData}
                onSubmit={handleCreate}
                onReset={resetFormData}
              />
            </div>
          </div>

          {/* Mobile View */}
          <IdeaBankMobileView
            data={getSortedData()}
            isLoading={isIdeasLoading}
            sortConfig={sortConfig}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onGenerate={(ibwp) => setIdeaToGenerate(ibwp)}
            onViewPost={viewPostDetails}
            formatDate={formatDate}
          />

          {/* Desktop View */}
          <IdeaBankDesktopView
            data={getSortedData()}
            isLoading={isIdeasLoading}
            onSort={handleSort}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onGenerate={(ibwp) => setIdeaToGenerate(ibwp)}
            onViewPost={viewPostDetails}
            formatDate={formatDate}
          />

          {/* Medium Screen View */}
          <IdeaBankMediumView
            data={getSortedData()}
            isLoading={isIdeasLoading}
            onSort={handleSort}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onGenerate={(ibwp) => setIdeaToGenerate(ibwp)}
            onViewPost={viewPostDetails}
          />
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <Pagination className="mt-6">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
                  className={page === 1 ? "pointer-events-none opacity-50" : ""}
                />
              </PaginationItem>

              {Array.from({ length: totalPages }).map((_, idx) => (
                <PaginationItem key={idx}>
                  <PaginationLink
                    href="#"
                    isActive={page === idx + 1}
                    onClick={() => setPage(idx + 1)}
                  >
                    {idx + 1}
                  </PaginationLink>
                </PaginationItem>
              ))}

              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={() =>
                    setPage((prev) => Math.min(prev + 1, totalPages))
                  }
                  className={
                    page === totalPages ? "pointer-events-none opacity-50" : ""
                  }
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </main>

      {/* Edit Dialog */}
      <EditIdeaDialog
        isOpen={showEditDialog}
        onOpenChange={setShowEditDialog}
        editFormData={editFormData}
        onEditFormDataChange={setEditFormData}
        onSubmit={handleUpdate}
        onClose={() => {
          setEditingIdeaBank(null);
          setEditFormData(null);
        }}
      />

      {/* Generate Post Confirmation Dialog */}
      <PostGenerationChatDialog
        conversationType="post_generation"
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
        />
      )}

      {/* Schedule Modal for new posts */}
      {showScheduleModal && generatedPost && (
        <PostScheduleModal
          post={generatedPost}
          isOpen={showScheduleModal}
          onClose={() => setShowScheduleModal(false)}
          onSchedule={handleSchedulePost}
        />
      )}

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Post Details</DialogTitle>
          </DialogHeader>
          {selectedPost && (
            <PostCard post={selectedPost} onPostUpdate={loadIdeaBanks} />
          )}
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
};

export default IdeaBank;
