
import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { SocialConnections } from '@/components/SocialConnections';
import { PlatformStyleAnalysis } from '@/components/PlatformStyleAnalysis';
import { SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { supabase } from '@/integrations/supabase/client';
import { LogOut } from 'lucide-react';

interface SocialConnection {
  platform: string;
  is_active: boolean;
}

const WritingStyle: React.FC = () => {
  const { user, signOut } = useAuth();
  const [connections, setConnections] = useState<SocialConnection[]>([]);

  useEffect(() => {
    if (user) {
      fetchConnections();
    }
  }, [user]);

  const fetchConnections = async () => {
    try {
      const { data, error } = await supabase
        .from('social_connections')
        .select('platform, is_active')
        .eq('user_id', user?.id)
        .eq('is_active', true);

      if (error) throw error;
      setConnections(data || []);
    } catch (error) {
      console.error('Error fetching connections:', error);
    }
  };

  const isConnected = (platform: string) => 
    connections.some(conn => conn.platform === platform && conn.is_active);

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
              Connect your social accounts and analyze your writing style for each platform to create more personalized content
            </p>
          </div>

          <div className="space-y-8">
            {/* Social Connections */}
            <SocialConnections />

            {/* Platform-specific Style Analysis */}
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Platform Writing Styles</h2>
              
              <div className="space-y-6">
                <PlatformStyleAnalysis 
                  platform="substack" 
                  platformName="Substack" 
                  isConnected={isConnected('substack')}
                />
                <PlatformStyleAnalysis 
                  platform="linkedin" 
                  platformName="LinkedIn" 
                  isConnected={isConnected('linkedin')}
                />
              </div>
            </div>
          </div>
        </div>
      </main>
    </SidebarInset>
  );
};

export default WritingStyle;
