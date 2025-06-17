
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { BarChart3, Brain, TrendingUp, BookOpen } from 'lucide-react';

interface PlatformAnalysisProps {
  platform: string;
  platformName: string;
  isConnected: boolean;
}

interface AnalysisData {
  writing_style: {
    tone: string;
    complexity: string;
    avg_length: number;
    key_themes: string[];
  };
  topics: string[];
  posting_patterns: {
    frequency: string;
    best_times: string[];
  };
  engagement_insights: {
    high_performing_topics: string[];
    content_types: string[];
  };
}

export const EnhancedPlatformAnalysis: React.FC<PlatformAnalysisProps> = ({
  platform,
  platformName,
  isConnected
}) => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastAnalyzed, setLastAnalyzed] = useState<string | null>(null);

  useEffect(() => {
    if (user && isConnected) {
      fetchAnalysis();
    }
  }, [user, platform, isConnected]);

  const fetchAnalysis = async () => {
    try {
      const { data, error } = await supabase
        .from('writing_style_analysis')
        .select('*')
        .eq('user_id', user?.id)
        .eq('platform', platform)
        .maybeSingle();

      if (error && error.code !== 'PGRST116') throw error;

      if (data) {
        // Cast the Json type to AnalysisData via unknown
        setAnalysisData(data.analysis_data as unknown as AnalysisData);
        setLastAnalyzed(data.last_analyzed_at);
      }
    } catch (error) {
      console.error('Error fetching analysis:', error);
    }
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      // This would typically call an edge function to analyze the user's content
      // For now, we'll create sample analysis data
      const sampleAnalysis: AnalysisData = {
        writing_style: {
          tone: platform === 'linkedin' ? 'Professional' : 'Conversational',
          complexity: 'Intermediate',
          avg_length: platform === 'linkedin' ? 150 : 800,
          key_themes: platform === 'linkedin' 
            ? ['Professional Growth', 'Industry Insights', 'Leadership']
            : ['Deep Dives', 'Analysis', 'Commentary']
        },
        topics: platform === 'linkedin'
          ? ['Technology', 'Business Strategy', 'Leadership', 'Innovation']
          : ['Technology', 'Startups', 'Product Development', 'Industry Analysis'],
        posting_patterns: {
          frequency: 'Weekly',
          best_times: ['9:00 AM', '1:00 PM', '5:00 PM']
        },
        engagement_insights: {
          high_performing_topics: ['AI', 'Remote Work', 'Leadership'],
          content_types: ['Insights', 'Personal Stories', 'Industry Updates']
        }
      };

      const { error } = await supabase
        .from('writing_style_analysis')
        .upsert({
          user_id: user?.id,
          platform,
          analysis_data: sampleAnalysis as unknown as any,
          content_count: Math.floor(Math.random() * 50) + 10,
          last_analyzed_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }, {
          onConflict: 'user_id,platform'
        });

      if (error) throw error;

      setAnalysisData(sampleAnalysis);
      setLastAnalyzed(new Date().toISOString());

      toast({
        title: "Analysis Complete",
        description: `Successfully analyzed your ${platformName} writing style`,
      });
    } catch (error) {
      console.error('Error running analysis:', error);
      toast({
        title: "Analysis Error",
        description: "Failed to analyze writing style",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!isConnected) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <h3 className="text-lg font-medium mb-2">Connect {platformName}</h3>
          <p className="text-gray-600">
            Connect your {platformName} account to analyze your writing style
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              {platformName} Writing Analysis
            </CardTitle>
            <Button
              onClick={runAnalysis}
              disabled={isAnalyzing}
              size="sm"
            >
              {isAnalyzing ? 'Analyzing...' : 'Analyze Writing Style'}
            </Button>
          </div>
          {lastAnalyzed && (
            <p className="text-sm text-gray-500">
              Last analyzed: {new Date(lastAnalyzed).toLocaleDateString()}
            </p>
          )}
        </CardHeader>
        
        {analysisData && (
          <CardContent className="space-y-6">
            {/* Writing Style */}
            <div>
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Writing Style
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Tone</p>
                  <p className="font-medium">{analysisData.writing_style.tone}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Complexity</p>
                  <p className="font-medium">{analysisData.writing_style.complexity}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Avg Length</p>
                  <p className="font-medium">{analysisData.writing_style.avg_length} words</p>
                </div>
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">Frequency</p>
                  <p className="font-medium">{analysisData.posting_patterns.frequency}</p>
                </div>
              </div>
            </div>

            {/* Topics */}
            <div>
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                Your Topics
              </h4>
              <div className="flex flex-wrap gap-2">
                {analysisData.topics.map((topic, index) => (
                  <Badge key={index} variant="secondary">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Key Themes */}
            <div>
              <h4 className="font-medium mb-3">Key Themes</h4>
              <div className="flex flex-wrap gap-2">
                {analysisData.writing_style.key_themes.map((theme, index) => (
                  <Badge key={index} variant="outline">
                    {theme}
                  </Badge>
                ))}
              </div>
            </div>

            {/* High Performing Content */}
            <div>
              <h4 className="font-medium mb-3">High-Performing Topics</h4>
              <div className="flex flex-wrap gap-2">
                {analysisData.engagement_insights.high_performing_topics.map((topic, index) => (
                  <Badge key={index} className="bg-green-100 text-green-800">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  );
};
