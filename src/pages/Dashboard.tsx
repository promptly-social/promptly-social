
import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { ContentIdeaForm } from '@/components/ContentIdeaForm';
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { LogOut } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user, signOut } = useAuth();

  return (
    <SidebarInset>
      <header className="border-b border-gray-100 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-6">
          <div className="flex items-center gap-4">
            <SidebarTrigger />
            <h1 className="text-2xl font-bold text-gray-900">New Content</h1>
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
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <p className="text-lg text-gray-600">
              Transform your ideas into structured content outlines with AI-powered assistance
            </p>
          </div>
          <ContentIdeaForm />
        </div>
      </main>
    </SidebarInset>
  );
};

export default Dashboard;
