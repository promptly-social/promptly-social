
import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { SocialConnections } from '@/components/SocialConnections';
import { ContentImporter } from '@/components/ContentImporter';
import { StyleAnalysis } from '@/components/StyleAnalysis';
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { LogOut } from 'lucide-react';

const WritingStyle: React.FC = () => {
  const { user, signOut } = useAuth();

  return (
    <SidebarInset>
      <header className="border-b border-gray-100 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-6">
          <div className="flex items-center gap-4">
            <SidebarTrigger />
            <h1 className="text-2xl font-bold text-gray-900">Writing Profile</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Welcome, {user?.email}</span>
            <Button onClick={signOut} variant="outline" size="sm">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <main className="py-8 px-6">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="text-center mb-8">
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Connect your social accounts and analyze your writing style to create more personalized content
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-6">
              <SocialConnections />
              <ContentImporter />
            </div>
            <div>
              <StyleAnalysis />
            </div>
          </div>
        </div>
      </main>
    </SidebarInset>
  );
};

export default WritingStyle;
