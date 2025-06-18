import React from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { LogOut } from "lucide-react";

interface AppLayoutProps {
  title: string;
  showWelcome?: boolean;
  emailBreakpoint?: "sm" | "md";
  additionalActions?: React.ReactNode;
  children?: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({
  title,
  showWelcome = false,
  emailBreakpoint = "sm",
  additionalActions,
  children,
}) => {
  const { user, signOut } = useAuth();

  const emailClasses =
    emailBreakpoint === "md"
      ? "hidden md:inline text-gray-600 text-sm"
      : "hidden sm:inline text-gray-600 text-sm";

  return (
    <SidebarInset>
      <header className="border-b border-gray-100 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-4 sm:p-6">
          <div className="flex items-center gap-2 sm:gap-4">
            <SidebarTrigger />
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900">
              {title}
            </h1>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-4">
            {additionalActions}
            <span className={emailClasses}>
              {showWelcome ? `Welcome, ${user?.email}` : user?.email}
            </span>
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
