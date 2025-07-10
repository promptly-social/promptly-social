import React, { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import AppLayout from "@/components/AppLayout";
import { useToast } from "@/hooks/use-toast";
import { User, Bell, AlertTriangle, Trash2 } from "lucide-react";
import type { UserUpdate } from "@/types/auth";

const Settings: React.FC = () => {
  const { user, updateUser } = useAuth();
  const { toast } = useToast();
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [formData, setFormData] = useState<UserUpdate>({
    full_name: user?.full_name || "",
    password: "",
    confirm_password: "",
  });

  const handleInputChange = (field: keyof UserUpdate, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleUpdateProfile = async () => {
    // Validate passwords match if both are provided
    if (formData.password && formData.password !== formData.confirm_password) {
      toast({
        title: "Error",
        description: "Passwords do not match",
        variant: "destructive",
      });
      return;
    }

    // Only include password fields if password is being updated
    const updateData: UserUpdate = {
      full_name: formData.full_name,
    };

    if (formData.password) {
      updateData.password = formData.password;
      updateData.confirm_password = formData.confirm_password;
    }

    setIsUpdating(true);
    try {
      const result = await updateUser(updateData);

      if (result.error) {
        toast({
          title: "Error",
          description: result.error.message,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Profile Updated",
          description: "Your profile has been updated successfully",
        });

        // Clear password fields after successful update
        setFormData((prev) => ({
          ...prev,
          password: "",
          confirm_password: "",
        }));
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update profile",
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDeleteAccount = () => {
    if (
      window.confirm(
        "Are you sure you want to delete your account? This action cannot be undone."
      )
    ) {
      toast({
        title: "Account Deletion",
        description: "Account deletion is not implemented yet",
        variant: "destructive",
      });
    }
  };

  return (
    <AppLayout title="Settings" emailBreakpoint="md">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-2xl mx-auto space-y-4 sm:space-y-6">
          {/* Account Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
                <User className="w-4 sm:w-5 h-4 sm:h-5" />
                Account Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-sm sm:text-base">
                  Full Name
                </Label>
                <Input
                  id="name"
                  placeholder="Enter your full name"
                  value={formData.full_name}
                  onChange={(e) =>
                    handleInputChange("full_name", e.target.value)
                  }
                  className="text-sm sm:text-base"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm sm:text-base">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={user?.email || ""}
                  disabled
                  className="text-sm sm:text-base bg-gray-50"
                />
                <p className="text-xs sm:text-sm text-gray-500">
                  Email cannot be changed
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm sm:text-base">
                  New Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter new password"
                  value={formData.password}
                  onChange={(e) =>
                    handleInputChange("password", e.target.value)
                  }
                  className="text-sm sm:text-base"
                />
              </div>
              <div className="space-y-2">
                <Label
                  htmlFor="confirm-password"
                  className="text-sm sm:text-base"
                >
                  Confirm Password
                </Label>
                <Input
                  id="confirm-password"
                  type="password"
                  placeholder="Confirm new password"
                  value={formData.confirm_password}
                  onChange={(e) =>
                    handleInputChange("confirm_password", e.target.value)
                  }
                  className="text-sm sm:text-base"
                />
              </div>
              <Button
                onClick={handleUpdateProfile}
                disabled={isUpdating}
                className="w-full sm:w-auto"
              >
                {isUpdating ? "Updating..." : "Update Profile"}
              </Button>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
                <Bell className="w-4 sm:w-5 h-4 sm:h-5" />
                Notification Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 sm:space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex-1 pr-4">
                  <Label className="text-sm sm:text-base font-medium">
                    Email Notifications
                  </Label>
                  <p className="text-xs sm:text-sm text-gray-500 mt-1">
                    FEATURE COMING SOON!
                  </p>
                </div>
                {/* <Switch
                  checked={emailNotifications}
                  onCheckedChange={setEmailNotifications}
                /> */}
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-700 text-lg sm:text-xl">
                <AlertTriangle className="w-4 sm:w-5 h-4 sm:h-5" />
                Danger Zone
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-red-700 text-sm sm:text-base">
                    Delete Account
                  </h4>
                  <p className="text-xs sm:text-sm text-gray-600 mb-3 mt-1">
                    Permanently delete your account and all associated data.
                    This action cannot be undone.
                  </p>
                  <Button
                    variant="destructive"
                    onClick={handleDeleteAccount}
                    className="flex items-center gap-2 w-full sm:w-auto"
                    size="sm"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </AppLayout>
  );
};

export default Settings;
