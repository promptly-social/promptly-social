
import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { SuggestedPosts } from '@/components/SuggestedPosts';
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { LogOut } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user, signOut } = useAuth();

  return (
    <SidebarInset>
      <header className="border-b border-gray-100 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-4 sm:p-6">
          <div className="flex items-center gap-2 sm:gap-4">
            <SidebarTrigger />
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900">New Content</h1>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-4">
            <span className="hidden sm:inline text-gray-600 text-sm">Welcome, {user?.email}</span>
            <Button onClick={signOut} variant="outline" size="sm">
              <LogOut className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Sign Out</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-4xl mx-auto">
          <SuggestedPosts />
        </div>
      </main>
    </SidebarInset>
  );
};

export default Dashboard;
