
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { Link2, Unlink, Users, FileText } from 'lucide-react';

interface SocialConnection {
  id: string;
  platform: string;
  platform_username: string | null;
  is_active: boolean;
  created_at: string;
}

export const SocialConnections: React.FC = () => {
  const [connections, setConnections] = useState<SocialConnection[]>([]);
  const [substackUsername, setSubstackUsername] = useState('');
  const [linkedinUsername, setLinkedinUsername] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchConnections();
    }
  }, [user]);

  const fetchConnections = async () => {
    try {
      const { data, error } = await supabase
        .from('social_connections')
        .select('*')
        .eq('user_id', user?.id);

      if (error) throw error;
      setConnections(data || []);
    } catch (error) {
      console.error('Error fetching connections:', error);
      toast({
        title: "Error",
        description: "Failed to fetch social connections",
        variant: "destructive",
      });
    }
  };

  const connectPlatform = async (platform: 'substack' | 'linkedin', username: string) => {
    if (!username.trim()) {
      toast({
        title: "Username Required",
        description: `Please enter your ${platform} username`,
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const { error } = await supabase
        .from('social_connections')
        .upsert({
          user_id: user?.id,
          platform,
          platform_username: username,
          is_active: true,
        }, {
          onConflict: 'user_id,platform'
        });

      if (error) throw error;

      toast({
        title: "Connected",
        description: `Successfully connected to ${platform}`,
      });

      fetchConnections();
      if (platform === 'substack') setSubstackUsername('');
      if (platform === 'linkedin') setLinkedinUsername('');
    } catch (error) {
      console.error('Error connecting platform:', error);
      toast({
        title: "Connection Error",
        description: `Failed to connect to ${platform}`,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const disconnectPlatform = async (platform: 'substack' | 'linkedin') => {
    setIsLoading(true);
    try {
      const { error } = await supabase
        .from('social_connections')
        .update({ is_active: false })
        .eq('user_id', user?.id)
        .eq('platform', platform);

      if (error) throw error;

      toast({
        title: "Disconnected",
        description: `Successfully disconnected from ${platform}`,
      });

      fetchConnections();
    } catch (error) {
      console.error('Error disconnecting platform:', error);
      toast({
        title: "Disconnection Error",
        description: `Failed to disconnect from ${platform}`,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getConnection = (platform: string) => 
    connections.find(conn => conn.platform === platform && conn.is_active);

  const substackConnection = getConnection('substack');
  const linkedinConnection = getConnection('linkedin');

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Link2 className="w-5 h-5" />
          Social Media Connections
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Substack Connection */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-orange-600" />
            <span className="font-medium">Substack</span>
          </div>
          
          {substackConnection ? (
            <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
              <div>
                <p className="text-sm font-medium text-green-800">
                  Connected as @{substackConnection.platform_username}
                </p>
                <p className="text-xs text-green-600">
                  Connected on {new Date(substackConnection.created_at).toLocaleDateString()}
                </p>
              </div>
              <Button
                onClick={() => disconnectPlatform('substack')}
                variant="outline"
                size="sm"
                disabled={isLoading}
              >
                <Unlink className="w-4 h-4 mr-2" />
                Disconnect
              </Button>
            </div>
          ) : (
            <div className="flex gap-2">
              <Input
                placeholder="Enter your Substack username"
                value={substackUsername}
                onChange={(e) => setSubstackUsername(e.target.value)}
              />
              <Button
                onClick={() => connectPlatform('substack', substackUsername)}
                disabled={isLoading}
              >
                <Link2 className="w-4 h-4 mr-2" />
                Connect
              </Button>
            </div>
          )}
        </div>

        {/* LinkedIn Connection */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-blue-600" />
            <span className="font-medium">LinkedIn</span>
          </div>
          
          {linkedinConnection ? (
            <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
              <div>
                <p className="text-sm font-medium text-green-800">
                  Connected as @{linkedinConnection.platform_username}
                </p>
                <p className="text-xs text-green-600">
                  Connected on {new Date(linkedinConnection.created_at).toLocaleDateString()}
                </p>
              </div>
              <Button
                onClick={() => disconnectPlatform('linkedin')}
                variant="outline"
                size="sm"
                disabled={isLoading}
              >
                <Unlink className="w-4 h-4 mr-2" />
                Disconnect
              </Button>
            </div>
          ) : (
            <div className="flex gap-2">
              <Input
                placeholder="Enter your LinkedIn username"
                value={linkedinUsername}
                onChange={(e) => setLinkedinUsername(e.target.value)}
              />
              <Button
                onClick={() => connectPlatform('linkedin', linkedinUsername)}
                disabled={isLoading}
              >
                <Link2 className="w-4 h-4 mr-2" />
                Connect
              </Button>
            </div>
          )}
        </div>

        <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
          <p className="font-medium mb-1">Note:</p>
          <p>For Substack, we'll analyze your public posts. For LinkedIn, you can upload your posts manually due to API limitations.</p>
        </div>
      </CardContent>
    </Card>
  );
};
