import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/contexts/AuthContext";
import { profileApi } from "@/lib/profile-api";
import { useToast } from "@/hooks/use-toast";
import { User, Edit3, Check, X } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export const UserBio: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [bio, setBio] = useState("");
  const [editingBio, setEditingBio] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (user) {
      loadBio();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const loadBio = async () => {
    setIsLoading(true);
    try {
      const data = await profileApi.getUserPreferences();
      setBio(data.bio || "");
    } catch (error) {
      console.error("Error loading bio:", error);
      toast({
        title: "Error",
        description: "Failed to load bio",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = () => {
    setEditingBio(bio);
    setIsEditing(true);
  };

  const handleCancel = () => {
    setEditingBio("");
    setIsEditing(false);
  };

  const handleConfirm = async () => {
    setIsSaving(true);
    try {
      await profileApi.updateUserPreferences({
        bio: editingBio,
      });

      setBio(editingBio);
      setIsEditing(false);
      setEditingBio("");

      toast({
        title: "Success",
        description: "Bio updated successfully",
      });
    } catch (error) {
      console.error("Error saving bio:", error);
      toast({
        title: "Error",
        description: "Failed to save bio",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <User className="w-5 h-5" />
          About Me
        </CardTitle>
        <p className="text-xs sm:text-sm text-gray-600">
          Your bio is used to personalize your content. Connect your social
          media account(s) to get a more personalized analysis.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <Skeleton className="w-full h-24" />
        ) : (
          <div className="space-y-3">
            {/* Edit button positioned at top right, outside the text box */}
            {!isEditing && (
              <div className="flex justify-end">
                <Button
                  onClick={handleEdit}
                  size="sm"
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <Edit3 className="w-4 h-4" />
                  Edit
                </Button>
              </div>
            )}

            {!isEditing ? (
              // Display mode
              <div className="min-h-[100px] p-4 bg-gray-50 rounded-lg border border-gray-200">
                {bio ? (
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">
                    {bio}
                  </p>
                ) : (
                  <p className="text-sm text-gray-500 italic">
                    No bio added yet. Click edit to add a brief description
                    about yourself.
                  </p>
                )}
              </div>
            ) : (
              // Edit mode
              <div className="border rounded-lg p-4 space-y-3 bg-blue-50">
                <Textarea
                  value={editingBio}
                  onChange={(e) => setEditingBio(e.target.value)}
                  placeholder="Tell us about yourself, your interests, and what you're passionate about..."
                  className="min-h-[250px] text-sm bg-white border-gray-200 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  disabled={isSaving}
                />
                <div className="flex justify-end items-center">
                  <div className="flex gap-2">
                    <Button
                      onClick={handleCancel}
                      size="sm"
                      variant="outline"
                      disabled={isSaving}
                    >
                      <X className="w-4 h-4 mr-1" />
                      Cancel
                    </Button>
                    <Button
                      onClick={handleConfirm}
                      size="sm"
                      disabled={isSaving}
                    >
                      <Check className="w-4 h-4 mr-1" />
                      {isSaving ? "Saving..." : "Save"}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};
