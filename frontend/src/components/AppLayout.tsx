import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { LogOut } from "lucide-react";

interface AppLayoutProps {
  title: string;
  emailBreakpoint?: "sm" | "md";
  additionalActions?: React.ReactNode;
  children?: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({
  title,
  emailBreakpoint = "sm",
  additionalActions,
  children,
}) => {
  const { user, signOut } = useAuth();

  const emailClasses =
    emailBreakpoint === "md"
      ? "hidden md:inline text-sm text-gray-900"
      : "hidden sm:inline text-sm text-gray-900";

  // Helper function to get display name (first name or email fallback)
  const getDisplayName = () => {
    if (!user) return "";

    // If user has a full name, extract the first name
    if (user.full_name) {
      const firstName = user.full_name.split(" ")[0];
      return firstName;
    }

    // Fallback to email
    return user.email;
  };

  const displayName = getDisplayName();

  return (
    <SidebarInset>
      <header className="border-b border-border bg-background/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-4 sm:p-6">
          <div className="flex items-center gap-2 sm:gap-4">
            <SidebarTrigger />
            <h1 className="text-lg sm:text-2xl font-bold text-foreground">
              {title}
            </h1>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-4">
            {additionalActions}
            <span className={emailClasses}>Welcome, {displayName}</span>
            <Button onClick={signOut} variant="outline" size="sm">
              <LogOut className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Sign Out</span>
            </Button>
          </div>
        </div>
      </header>
      {children}
    </SidebarInset>
  );
};

export default AppLayout;
