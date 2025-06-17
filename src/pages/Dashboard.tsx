
import React from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { ContentIdeaForm } from '@/components/ContentIdeaForm';
import { Sparkles, LogOut } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-100">
      <nav className="border-b border-gray-100 bg-white/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between p-6 max-w-7xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-gray-900 via-gray-800 to-black rounded-xl flex items-center justify-center shadow-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              Promptly
            </span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Welcome, {user?.email}</span>
            <Button onClick={signOut} variant="outline" size="sm">
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </div>
      </nav>

      <main className="py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Content Creation Dashboard
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Transform your ideas into structured content outlines with AI-powered assistance
            </p>
          </div>

          <ContentIdeaForm />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
