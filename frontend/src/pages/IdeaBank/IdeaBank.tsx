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
import { Input } from "@/components/ui/input";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  ArrowUpDown,
  Plus,
  Trash2,
  ExternalLink,
  Edit,
  RefreshCw,
  Filter,
  Sparkles,
} from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
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
  key: "type" | "value" | "evergreen" | "updated_at";
  direction: "asc" | "desc";
}

interface Filters {
  ai_suggested?: boolean;
  evergreen?: boolean;
  has_post?: boolean;
}

const IdeaBankPage: React.FC = () => {
  const [ideaBanksWithPosts, setIdeaBanksWithPosts] = useState<
    IdeaBankWithPost[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: "updated_at",
    direction: "desc",
  });
  const [filters, setFilters] = useState<Filters>({
    // By default, exclude AI suggested content
    ai_suggested: false,
  });
  const [pendingFilters, setPendingFilters] = useState<Filters>({
    // By default, exclude AI suggested content
    ai_suggested: false,
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
      product_name: "",
      product_description: "",
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
        product_name: "",
        product_description: "",
        time_sensitive: false,
        ai_suggested: false,
      },
    });
  };

  useEffect(() => {
    loadIdeaBanks();
    loadScheduledPosts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortConfig, filters]);

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
        order_by:
          sortConfig.key === "type" ||
          sortConfig.key === "value" ||
          sortConfig.key === "evergreen"
            ? "updated_at"
            : sortConfig.key,
        order_direction: sortConfig.direction,
        size: 100,
        ...filters,
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

  const handlePendingFilterChange = (newFilters: Partial<Filters>) => {
    setPendingFilters((prev) => ({ ...prev, ...newFilters }));
  };

  const applyFilters = () => {
    setFilters(pendingFilters);
  };

  const clearPendingFilters = () => {
    const defaultFilters: Filters = {
      // Reset to default: exclude AI suggested content
      ai_suggested: false,
    };
    setPendingFilters(defaultFilters);
  };

  const clearAllFilters = () => {
    const defaultFilters: Filters = {
      // Reset to default: exclude AI suggested content
      ai_suggested: false,
    };
    setPendingFilters(defaultFilters);
    setFilters(defaultFilters);
  };

  const getActiveFilterCount = () => {
    let count = 0;
    // Don't count ai_suggested filter as it's always applied by default
    if (filters.evergreen !== undefined) count++;
    if (filters.has_post !== undefined) count++;
    return count;
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
      product_name: ideaBank.data.product_name || "",
      product_description: ideaBank.data.product_description || "",
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
        case "type":
          aValue = a.idea_bank.data.type;
          bValue = b.idea_bank.data.type;
          break;
        case "value":
          aValue = a.idea_bank.data.value;
          bValue = b.idea_bank.data.value;
          break;
        case "evergreen":
          aValue = !a.idea_bank.data.time_sensitive;
          bValue = !b.idea_bank.data.time_sensitive;
          break;
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
    window.open(`/my-content?post=${post.id}`, "_blank");
  };

  const renderIdeaBankContent = (ideaBank: IdeaBankWithPost["idea_bank"]) => {
    if (ideaBank.data.type === "product") {
      return (
        <div className="space-y-1">
          {ideaBank.data.product_name && (
            <div className="font-medium text-sm text-gray-900">
              {ideaBank.data.product_name}
            </div>
          )}
          {ideaBank.data.product_description && (
            <div className="text-sm text-gray-600 mb-1">
              {ideaBank.data.product_description}
            </div>
          )}
          {ideaBank.data.value && (
            <a
              href={ideaBank.data.value}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-start gap-1 text-blue-600 hover:text-blue-800 hover:underline break-all text-sm"
            >
              <span className="break-all">{ideaBank.data.value}</span>
              <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
            </a>
          )}
        </div>
      );
    }

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

  const refreshButton = (
    <Button
      onClick={loadIdeaBanks}
      disabled={loading}
      variant="outline"
      size="sm"
    >
      <RefreshCw
        className={`w-4 h-4 ${loading ? "animate-spin" : ""} sm:mr-2`}
      />
      <span className="hidden sm:inline">Refresh</span>
    </Button>
  );

  const filterButton = (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="relative">
          <Filter className="w-4 h-4 sm:mr-2" />
          <span className="hidden sm:inline">Filter</span>
          {getActiveFilterCount() > 0 && (
            <Badge className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs">
              {getActiveFilterCount()}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Filters</h4>
            <Button variant="ghost" size="sm" onClick={clearPendingFilters}>
              Clear
            </Button>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label htmlFor="evergreen-filter">Evergreen Topic</Label>
              <Select
                value={
                  pendingFilters.evergreen === undefined
                    ? "all"
                    : pendingFilters.evergreen.toString()
                }
                onValueChange={(value) =>
                  handlePendingFilterChange({
                    evergreen: value === "all" ? undefined : value === "true",
                  })
                }
              >
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="true">Yes</SelectItem>
                  <SelectItem value="false">No</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="has-post-filter">Has Post</Label>
              <Select
                value={
                  pendingFilters.has_post === undefined
                    ? "all"
                    : pendingFilters.has_post.toString()
                }
                onValueChange={(value) =>
                  handlePendingFilterChange({
                    has_post: value === "all" ? undefined : value === "true",
                  })
                }
              >
                <SelectTrigger className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="true">Yes</SelectItem>
                  <SelectItem value="false">No</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-2 pt-3 border-t">
            <Button onClick={applyFilters} size="sm" className="flex-1">
              Apply Filters
            </Button>
            <Button
              onClick={clearAllFilters}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              Clear All
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
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
            <Label htmlFor="type">Type</Label>
            <Select
              value={formData.data.type}
              onValueChange={(value: "url" | "text" | "product") =>
                setFormData((prev) => ({
                  ...prev,
                  data: {
                    ...prev.data,
                    type: value,
                    title: value === "text" ? "" : prev.data.title,
                    product_name:
                      value === "product" ? prev.data.product_name : "",
                    product_description:
                      value === "product" ? prev.data.product_description : "",
                  },
                }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="text">Text</SelectItem>
                <SelectItem value="url">URL</SelectItem>
                <SelectItem value="product">Product</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {formData.data.type === "url" && (
            <div className="space-y-2">
              <Label htmlFor="title">Title (Optional)</Label>
              <Input
                id="title"
                placeholder="Enter a title for this article or post..."
                value={formData.data.title || ""}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    data: { ...prev.data, title: e.target.value },
                  }))
                }
              />
            </div>
          )}
          {formData.data.type === "product" && (
            <>
              <div className="space-y-2">
                <Label htmlFor="product-name">Product Name (Optional)</Label>
                <Input
                  id="product-name"
                  placeholder="Enter the product name..."
                  value={formData.data.product_name || ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      data: { ...prev.data, product_name: e.target.value },
                    }))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="product-description">
                  Product Description (Optional)
                </Label>
                <Textarea
                  id="product-description"
                  placeholder="Enter the product description..."
                  value={formData.data.product_description || ""}
                  onChange={(e) =>
                    setFormData((prev) => ({
                      ...prev,
                      data: {
                        ...prev.data,
                        product_description: e.target.value,
                      },
                    }))
                  }
                  rows={3}
                  className="min-h-[80px] resize-none"
                />
              </div>
            </>
          )}
          <div className="space-y-2">
            <Label htmlFor="value">
              {formData.data.type === "url"
                ? "URL"
                : formData.data.type === "product"
                ? "Product URL"
                : "Content"}
            </Label>
            {formData.data.type === "url" ||
            formData.data.type === "product" ? (
              <Input
                id="value"
                type="url"
                placeholder={
                  formData.data.type === "url"
                    ? "https://example.com/url"
                    : "https://example.com/product"
                }
                value={formData.data.value}
                onChange={(e) =>
                  setFormData((prev) => ({
                    ...prev,
                    data: { ...prev.data, value: e.target.value },
                  }))
                }
              />
            ) : (
              <Textarea
                id="value"
                placeholder="Enter your idea or text content..."
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
            )}
          </div>
          <div className="flex items-center space-x-2">
            <Switch
              id="time-sensitive"
              checked={formData.data.time_sensitive}
              onCheckedChange={(checked) =>
                setFormData((prev) => ({
                  ...prev,
                  data: { ...prev.data, time_sensitive: checked },
                }))
              }
            />
            <Label htmlFor="time-sensitive">Trending</Label>
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
      <AppLayout title="Idea Bank" emailBreakpoint="md">
        <main className="py-4 px-4 sm:py-8 sm:px-6">
          <div className="max-w-7xl mx-auto">
            <div className="text-center py-8">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
              <p className="text-gray-600">Loading idea banks...</p>
            </div>
          </div>
        </main>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Idea Bank" emailBreakpoint="md">
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
              {refreshButton}
              {filterButton}
              {addButton}
            </div>
          </div>

          {/* Mobile Card Layout */}
          <div className="block md:hidden space-y-4">
            {/* Mobile Sort Info */}
            <div className="flex items-center justify-between text-sm text-gray-500 px-1">
              <span>
                Sorted by:{" "}
                {sortConfig.key === "type"
                  ? "Type"
                  : sortConfig.key === "value"
                  ? "Value"
                  : sortConfig.key === "evergreen"
                  ? "Evergreen"
                  : sortConfig.key === "updated_at"
                  ? "Last Updated"
                  : sortConfig.key}{" "}
                ({sortConfig.direction === "asc" ? "↑" : "↓"})
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
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="capitalize">
                          {ideaBank.data.type}
                        </Badge>
                        {ideaBank.data.ai_suggested && (
                          <Badge variant="secondary" className="text-xs">
                            AI
                          </Badge>
                        )}
                        <Badge
                          variant={
                            !ideaBank.data.time_sensitive
                              ? "default"
                              : "secondary"
                          }
                          className="text-xs"
                        >
                          {!ideaBank.data.time_sensitive
                            ? "Evergreen"
                            : "Trending"}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-1">
                        <Actions ideaBankWithPost={ideaBankWithPost} />
                      </div>
                    </div>

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
                  <TableHead className="w-[90px]">
                    <SortButton column="type">Type</SortButton>
                  </TableHead>
                  <TableHead className="min-w-[200px]">
                    <SortButton column="value">Content</SortButton>
                  </TableHead>
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
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="capitalize">
                              {ideaBank.data.type}
                            </Badge>
                            {ideaBank.data.ai_suggested && (
                              <Badge variant="secondary" className="text-xs">
                                AI
                              </Badge>
                            )}
                            <Badge
                              variant={
                                !ideaBank.data.time_sensitive
                                  ? "default"
                                  : "secondary"
                              }
                              className="text-xs"
                            >
                              {!ideaBank.data.time_sensitive
                                ? "Evergreen"
                                : "Trending"}
                            </Badge>
                          </div>
                        </TableCell>
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
                  <TableHead className="w-[90px]">
                    <SortButton column="type">Type</SortButton>
                  </TableHead>
                  <TableHead className="min-w-[250px]">
                    <SortButton column="value">Content</SortButton>
                  </TableHead>
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
                        <TableCell>
                          <div className="flex flex-col gap-1">
                            <Badge
                              variant="outline"
                              className="capitalize text-xs w-fit"
                            >
                              {ideaBank.data.type}
                            </Badge>
                            <div className="flex gap-1">
                              {ideaBank.data.ai_suggested && (
                                <Badge variant="secondary" className="text-xs">
                                  AI
                                </Badge>
                              )}
                              <Badge
                                variant={
                                  !ideaBank.data.time_sensitive
                                    ? "default"
                                    : "secondary"
                                }
                                className="text-xs"
                              >
                                {!ideaBank.data.time_sensitive
                                  ? "Evergreen"
                                  : "Trending"}
                              </Badge>
                            </div>
                          </div>
                        </TableCell>
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
                  <Label htmlFor="edit-type">Type</Label>
                  <Select
                    value={editFormData.type}
                    onValueChange={(newType: "url" | "text" | "product") => {
                      setEditFormData((prev) => {
                        if (!prev) return null;
                        return {
                          ...prev,
                          type: newType,
                          value: "",
                          title: newType !== "url" ? "" : prev.title,
                          product_name:
                            newType !== "product" ? "" : prev.product_name,
                          product_description:
                            newType !== "product"
                              ? ""
                              : prev.product_description,
                        };
                      });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="url">URL</SelectItem>
                      <SelectItem value="text">Text</SelectItem>
                      <SelectItem value="product">Product</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                {editFormData.type === "url" && (
                  <div className="space-y-2">
                    <Label htmlFor="edit-title">Title (Optional)</Label>
                    <Input
                      id="edit-title"
                      placeholder="Enter an optional title for this link..."
                      value={editFormData.title || ""}
                      onChange={(e) =>
                        setEditFormData((prev) => ({
                          ...prev!,
                          title: e.target.value,
                        }))
                      }
                    />
                  </div>
                )}
                {editFormData.type === "product" && (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="edit-product-name">
                        Product Name (Optional)
                      </Label>
                      <Input
                        id="edit-product-name"
                        placeholder="Enter the product name..."
                        value={editFormData.product_name || ""}
                        onChange={(e) =>
                          setEditFormData((prev) => ({
                            ...prev!,
                            product_name: e.target.value,
                          }))
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="edit-product-description">
                        Product Description (Optional)
                      </Label>
                      <Textarea
                        id="edit-product-description"
                        placeholder="Enter the product description..."
                        value={editFormData.product_description || ""}
                        onChange={(e) =>
                          setEditFormData((prev) => ({
                            ...prev!,
                            product_description: e.target.value,
                          }))
                        }
                        rows={3}
                        className="min-h-[80px] resize-none"
                      />
                    </div>
                  </>
                )}
                <div className="space-y-2">
                  <Label htmlFor="edit-value">
                    {editFormData.type === "url"
                      ? "URL"
                      : editFormData.type === "product"
                      ? "Product URL"
                      : "Content"}
                  </Label>
                  {editFormData.type === "url" ||
                  editFormData.type === "product" ? (
                    <Input
                      key="value-input"
                      id="edit-value"
                      type="url"
                      placeholder={
                        editFormData.type === "url"
                          ? "https://example.com/url"
                          : "https://example.com/product"
                      }
                      value={editFormData.value}
                      onChange={(e) =>
                        setEditFormData((prev) => ({
                          ...prev!,
                          value: e.target.value,
                        }))
                      }
                    />
                  ) : (
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
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <Switch
                    id="edit-time-sensitive"
                    checked={editFormData.time_sensitive}
                    onCheckedChange={(checked) =>
                      setEditFormData((prev) => ({
                        ...prev!,
                        time_sensitive: checked,
                      }))
                    }
                  />
                  <Label htmlFor="edit-time-sensitive">Trending</Label>
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

export default IdeaBankPage;
