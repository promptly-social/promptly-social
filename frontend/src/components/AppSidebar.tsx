import React from "react";
import { NavLink, useMatch } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  PenTool,
  Home,
  User,
  Settings,
  List,
  Lightbulb,
  Calendar,
  Target,
} from "lucide-react";

const contentMenuItems = [
  {
    title: "My Posts",
    url: "/my-posts",
    icon: List,
  },
  {
    title: "Content Ideas",
    url: "/content-ideas",
    icon: Lightbulb,
  },
  {
    title: "Posting Schedule",
    url: "/posting-schedule",
    icon: Calendar,
  },
];

const personalizationMenuItems = [
  {
    title: "Profile",
    url: "/profile",
    icon: User,
  },
  {
    title: "Content Preferences",
    url: "/content-preferences",
    icon: Target,
  },
  {
    title: "Settings",
    url: "/settings",
    icon: Settings,
  },
];

const AppSidebarMenuItem = ({
  item,
  isCollapsed,
}: {
  item: { url: string; title: string; icon: React.ElementType };
  isCollapsed: boolean;
}) => {
  const match = useMatch({ path: item.url, end: true });

  return (
    <SidebarMenuItem>
      <SidebarMenuButton isActive={!!match} asChild>
        <NavLink to={item.url} end>
          <item.icon className="w-4 h-4" />
          {!isCollapsed && <span>{item.title}</span>}
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );
};

export function AppSidebar() {
  const { state } = useSidebar();

  const isCollapsed = state === "collapsed";

  return (
    <Sidebar className={isCollapsed ? "w-14" : "w-60"} collapsible="icon">
      <SidebarHeader className="border-b p-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-gray-900 via-gray-800 to-black rounded-lg flex items-center justify-center">
            <PenTool className="w-5 h-5 text-white" />
          </div>
          {!isCollapsed && (
            <span className="text-lg font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Promptly
            </span>
          )}
        </div>
        <SidebarTrigger className="ml-auto" />
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Content</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {contentMenuItems.map((item) => (
                <AppSidebarMenuItem
                  key={item.title}
                  item={item}
                  isCollapsed={isCollapsed}
                />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup>
          <SidebarGroupLabel>Personalization</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {personalizationMenuItems.map((item) => (
                <AppSidebarMenuItem
                  key={item.title}
                  item={item}
                  isCollapsed={isCollapsed}
                />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
