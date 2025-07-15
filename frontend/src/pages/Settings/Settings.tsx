import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import AppLayout from "@/components/AppLayout";
import { useToast } from "@/hooks/use-toast";
import { AlertTriangle, Trash2 } from "lucide-react";
import { ContentScheduleSettings } from "@/components/settings/ContentScheduleSettings";

const Settings: React.FC = () => {
  const { deleteAccount } = useAuth();
  const { toast } = useToast();

  const handleDeleteAccount = async () => {
    if (
      window.confirm(
        "Are you sure you want to delete your account? This action cannot be undone."
      )
    ) {
      const { error } = await deleteAccount();
      if (error) {
        toast({
          title: "Error",
          description: error.message,
          variant: "destructive",
        });
      } else {
        toast({
          title: "Account Deleted",
          description: "Your account has been successfully deleted.",
        });
        // The user will be redirected to the login page by the AuthContext
      }
    }
  };

  return (
    <AppLayout title="Settings" emailBreakpoint="md">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-2xl mx-auto space-y-4 sm:space-y-6">
          <ContentScheduleSettings />
          {/* Notification Settings */}
          {/* <Card>
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
                <Switch
                  checked={emailNotifications}
                  onCheckedChange={setEmailNotifications}
                /> 
              </div>
            </CardContent>
          </Card> 
          */}

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
