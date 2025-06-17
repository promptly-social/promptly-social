
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { BarChart3 } from 'lucide-react';
import { EnhancedPlatformAnalysis } from './EnhancedPlatformAnalysis';

interface SocialConnection {
  platform: string;
  is_active: boolean;
}

export const ConsolidatedPlatformAnalysis: React.FC = () => {
  const { user } = useAuth();
  const [connections, setConnections] = useState<SocialConnection[]>([]);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');

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
      const connectionsData = data || [];
      setConnections(connectionsData);
      
      // Auto-select first platform if available
      if (connectionsData.length > 0 && !selectedPlatform) {
        setSelectedPlatform(connectionsData[0].platform);
      }
    } catch (error) {
      console.error('Error fetching connections:', error);
    }
  };

  const isConnected = (platform: string) => 
    connections.some(conn => conn.platform === platform && conn.is_active);

  const getPlatformDisplayName = (platform: string) => {
    switch (platform) {
      case 'substack':
        return 'Substack';
      case 'linkedin':
        return 'LinkedIn';
      default:
        return platform.charAt(0).toUpperCase() + platform.slice(1);
    }
  };

  if (connections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Platform Writing Styles
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-gray-600">No connected platforms found</p>
            <p className="text-sm text-gray-500">Connect your social accounts to analyze your writing style</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Platform Writing Styles
            </div>
            <Select value={selectedPlatform} onValueChange={setSelectedPlatform}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select platform" />
              </SelectTrigger>
              <SelectContent>
                {connections.map((connection) => (
                  <SelectItem key={connection.platform} value={connection.platform}>
                    {getPlatformDisplayName(connection.platform)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardTitle>
        </CardHeader>
      </Card>

      {selectedPlatform && (
        <EnhancedPlatformAnalysis 
          platform={selectedPlatform} 
          platformName={getPlatformDisplayName(selectedPlatform)} 
          isConnected={isConnected(selectedPlatform)}
        />
      )}
    </div>
  );
};
