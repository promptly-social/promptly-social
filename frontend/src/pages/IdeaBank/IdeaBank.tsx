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
} from "lucide-react";
import {
  ideaBankApi,
  type IdeaBank,
  type IdeaBankCreate,
  type IdeaBankUpdate,
} from "@/lib/idea-bank-api";
import AppLayout from "@/components/AppLayout";

interface SortConfig {
  key: keyof IdeaBank | "type" | "value" | "evergreen";
  direction: "asc" | "desc";
}

const IdeaBankPage: React.FC = () => {
  const [ideaBanks, setIdeaBanks] = useState<IdeaBank[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: "updated_at",
    direction: "desc",
  });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [editingIdeaBank, setEditingIdeaBank] = useState<IdeaBank | null>(null);
  const [formData, setFormData] = useState<IdeaBankCreate>({
    data: {
      type: "text",
      value: "",
      title: "",
      time_sensitive: false,
      ai_suggested: false,
    },
  });

  useEffect(() => {
    loadIdeaBanks();
  }, [sortConfig]);

  const loadIdeaBanks = async () => {
    try {
      setLoading(true);
      const response = await ideaBankApi.list({
        order_by:
          sortConfig.key === "type" ||
          sortConfig.key === "value" ||
          sortConfig.key === "evergreen"
            ? "updated_at"
            : sortConfig.key,
        order_direction: sortConfig.direction,
        size: 100, // Load more items for better UX
      });
      setIdeaBanks(response.items);
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
      setFormData({
        data: {
          type: "text",
          value: "",
          title: "",
          time_sensitive: false,
          ai_suggested: false,
        },
      });
      loadIdeaBanks();
    } catch (error) {
      console.error("Failed to create idea bank:", error);
      toast.error("Failed to create idea bank");
    }
  };

  const handleEdit = (ideaBank: IdeaBank) => {
    setEditingIdeaBank(ideaBank);
    setFormData({
      data: {
        type: ideaBank.data.type,
        value: ideaBank.data.value,
        title: ideaBank.data.title || "",
        time_sensitive: ideaBank.data.time_sensitive || false,
        ai_suggested: ideaBank.data.ai_suggested || false,
      },
    });
    setShowEditDialog(true);
  };

  const handleUpdate = async () => {
    if (!editingIdeaBank) return;

    try {
      await ideaBankApi.update(editingIdeaBank.id, { data: formData.data });
      toast.success("Idea bank updated successfully");
      setShowEditDialog(false);
      setEditingIdeaBank(null);
      setFormData({
        data: {
          type: "text",
          value: "",
          title: "",
          time_sensitive: false,
          ai_suggested: false,
        },
      });
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

  const getSortedData = () => {
    const sorted = [...ideaBanks].sort((a, b) => {
      let aValue: string | number | boolean;
      let bValue: string | number | boolean;

      switch (sortConfig.key) {
        case "type":
          aValue = a.data.type;
          bValue = b.data.type;
          break;
        case "value":
          aValue = a.data.value;
          bValue = b.data.value;
          break;
        case "evergreen":
          aValue = !a.data.time_sensitive;
          bValue = !b.data.time_sensitive;
          break;
        case "updated_at":
          aValue = new Date(a.updated_at).getTime();
          bValue = new Date(b.updated_at).getTime();
          break;
        default:
          aValue = a[sortConfig.key as keyof IdeaBank] as string;
          bValue = b[sortConfig.key as keyof IdeaBank] as string;
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

  const addButton = (
    <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
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
              onValueChange={(value: "substack" | "text") =>
                setFormData((prev) => ({
                  ...prev,
                  data: {
                    ...prev.data,
                    type: value,
                    title: value === "text" ? "" : prev.data.title,
                  },
                }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="substack">Substack</SelectItem>
                <SelectItem value="text">Text</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {formData.data.type === "substack" && (
            <div className="space-y-2">
              <Label htmlFor="title">Title (Optional)</Label>
              <Input
                id="title"
                placeholder="Enter a title for this Substack article..."
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
          <div className="space-y-2">
            <Label htmlFor="value">
              {formData.data.type === "substack" ? "URL" : "Content"}
            </Label>
            {formData.data.type === "substack" ? (
              <Input
                id="value"
                type="url"
                placeholder="https://example.substack.com"
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
            <Label htmlFor="time-sensitive">Time Sensitive</Label>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreate} disabled={!formData.data.value.trim()}>
            Create
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  if (loading) {
    return (
      <AppLayout
        title="Idea Bank"
        emailBreakpoint="md"
        additionalActions={
          <div className="flex items-center gap-2">
            {refreshButton}
            {addButton}
          </div>
        }
      >
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
    <AppLayout
      title="Idea Bank"
      emailBreakpoint="md"
      additionalActions={
        <div className="flex items-center gap-2">
          {refreshButton}
          {addButton}
        </div>
      }
    >
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-4 sm:mb-8">
            <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto">
              Manage your content ideas and inspirations
            </p>
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
                  No idea banks found. Create your first idea to get started.
                </div>
              </div>
            ) : (
              getSortedData().map((ideaBank) => (
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
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(ideaBank)}
                        className="text-blue-600 hover:text-blue-800 p-2 min-w-[44px] min-h-[44px]"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(ideaBank.id)}
                        className="text-red-600 hover:text-red-800 p-2 min-w-[44px] min-h-[44px]"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium text-gray-500">
                        Content:
                      </span>
                      <div className="mt-1 space-y-1">
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
                            <span className="break-all">
                              {ideaBank.data.value}
                            </span>
                            <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
                          </a>
                        ) : (
                          <div className="whitespace-pre-wrap break-words text-sm">
                            {ideaBank.data.value}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <div>
                        <span className="text-gray-500">Evergreen: </span>
                        <Badge
                          variant={
                            !ideaBank.data.time_sensitive
                              ? "default"
                              : "secondary"
                          }
                          className="text-xs"
                        >
                          {!ideaBank.data.time_sensitive ? "Yes" : "No"}
                        </Badge>
                      </div>
                      <div className="text-gray-500">
                        {formatDate(ideaBank.updated_at)}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Desktop Table Layout */}
          <div className="hidden md:block border rounded-lg overflow-x-auto">
            <Table className="min-w-full">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[90px]">
                    <SortButton column="type">Type</SortButton>
                  </TableHead>
                  <TableHead className="min-w-[200px]">
                    <SortButton column="value">Value</SortButton>
                  </TableHead>
                  <TableHead className="w-[150px]">
                    <SortButton column="updated_at">Last Updated</SortButton>
                  </TableHead>
                  <TableHead className="w-[100px]">
                    <SortButton column="evergreen">Evergreen</SortButton>
                  </TableHead>
                  <TableHead className="w-[120px]">Last Post Used</TableHead>
                  <TableHead className="w-[100px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {getSortedData().length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      <div className="text-muted-foreground">
                        No idea banks found. Create your first idea to get
                        started.
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  getSortedData().map((ideaBank) => (
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
                        </div>
                      </TableCell>
                      <TableCell className="min-w-0">
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
                              className="inline-flex items-start gap-1 text-blue-600 hover:text-blue-800 hover:underline break-all"
                            >
                              <span className="break-all">
                                {ideaBank.data.value}
                              </span>
                              <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
                            </a>
                          ) : (
                            <div className="whitespace-pre-wrap break-words">
                              {ideaBank.data.value}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDate(ideaBank.updated_at)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            !ideaBank.data.time_sensitive
                              ? "default"
                              : "secondary"
                          }
                        >
                          {!ideaBank.data.time_sensitive ? "Yes" : "No"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        Not used yet
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEdit(ideaBank)}
                            className="text-blue-600 hover:text-blue-800"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete(ideaBank.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </main>

      {/* Edit Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Idea</DialogTitle>
            <DialogDescription>Update your idea bank entry.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit-type">Type</Label>
              <Select
                value={formData.data.type}
                onValueChange={(value: "substack" | "text") =>
                  setFormData((prev) => ({
                    ...prev,
                    data: {
                      ...prev.data,
                      type: value,
                      title: value === "text" ? "" : prev.data.title,
                    },
                  }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="substack">Substack</SelectItem>
                  <SelectItem value="text">Text</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {formData.data.type === "substack" && (
              <div className="space-y-2">
                <Label htmlFor="edit-title">Title (Optional)</Label>
                <Input
                  id="edit-title"
                  placeholder="Enter a title for this Substack article..."
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
            <div className="space-y-2">
              <Label htmlFor="edit-value">
                {formData.data.type === "substack" ? "URL" : "Content"}
              </Label>
              {formData.data.type === "substack" ? (
                <Input
                  id="edit-value"
                  type="url"
                  placeholder="https://example.substack.com"
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
                  id="edit-value"
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
                id="edit-time-sensitive"
                checked={formData.data.time_sensitive}
                onCheckedChange={(checked) =>
                  setFormData((prev) => ({
                    ...prev,
                    data: { ...prev.data, time_sensitive: checked },
                  }))
                }
              />
              <Label htmlFor="edit-time-sensitive">Time Sensitive</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowEditDialog(false);
                setEditingIdeaBank(null);
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdate}
              disabled={!formData.data.value.trim()}
            >
              Update
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
};

export default IdeaBankPage;
