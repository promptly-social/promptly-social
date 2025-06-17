
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { BarChart3, Loader2, RefreshCw, Eye } from 'lucide-react';

interface StyleAnalysisData {
  tone: string;
  formality: string;
  common_phrases: string[];
  vocabulary_level: string;
  sentence_structure: string;
  key_themes: string[];
  avg_sentence_length: number;
  reading_level: string;
}

interface AnalysisRecord {
  analysis_data: StyleAnalysisData;
  content_count: number;
  last_analyzed_at: string;
}

export const StyleAnalysis: React.FC = () => {
  const [analysis, setAnalysis] = useState<AnalysisRecord | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [contentCount, setContentCount] = useState(0);
  const { toast } = useToast();
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchAnalysis();
      fetchContentCount();
    }
  }, [user]);

  const fetchAnalysis = async () => {
    try {
      const { data, error } = await supabase
        .from('writing_style_analysis')
        .select('*')
        .eq('user_id', user?.id)
        .single();

      if (error && error.code !== 'PGRST116') throw error;
      
      if (data) {
        // Cast the Json type to StyleAnalysisData
        const analysisRecord: AnalysisRecord = {
          analysis_data: data.analysis_data as StyleAnalysisData,
          content_count: data.content_count,
          last_analyzed_at: data.last_analyzed_at,
        };
        setAnalysis(analysisRecord);
      }
    } catch (error) {
      console.error('Error fetching analysis:', error);
    }
  };

  const fetchContentCount = async () => {
    try {
      const { count, error } = await supabase
        .from('imported_content')
        .select('*', { count: 'exact', head: true })
        .eq('user_id', user?.id);

      if (error) throw error;
      setContentCount(count || 0);
    } catch (error) {
      console.error('Error fetching content count:', error);
    }
  };

  const runAnalysis = async () => {
    if (contentCount === 0) {
      toast({
        title: "No Content",
        description: "Please import some content first before running analysis",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await fetch('/functions/v1/analyze-writing-style', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: user?.id,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze writing style');
      }

      toast({
        title: "Analysis Complete",
        description: "Your writing style has been analyzed successfully",
      });

      fetchAnalysis();
    } catch (error) {
      console.error('Error analyzing writing style:', error);
      toast({
        title: "Analysis Error",
        description: "Failed to analyze writing style. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Writing Style Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">
              Content pieces: <span className="font-medium">{contentCount}</span>
            </p>
            {analysis && (
              <p className="text-xs text-gray-500">
                Last analyzed: {new Date(analysis.last_analyzed_at).toLocaleDateString()}
              </p>
            )}
          </div>
          <Button
            onClick={runAnalysis}
            disabled={isAnalyzing || contentCount === 0}
            size="sm"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                {analysis ? 'Re-analyze' : 'Analyze Style'}
              </>
            )}
          </Button>
        </div>

        {analysis ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-800">Tone</p>
                <p className="text-lg text-blue-900">{analysis.analysis_data.tone}</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-sm font-medium text-green-800">Formality</p>
                <p className="text-lg text-green-900">{analysis.analysis_data.formality}</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-sm font-medium text-purple-800">Vocabulary</p>
                <p className="text-lg text-purple-900">{analysis.analysis_data.vocabulary_level}</p>
              </div>
              <div className="p-3 bg-orange-50 rounded-lg">
                <p className="text-sm font-medium text-orange-800">Reading Level</p>
                <p className="text-lg text-orange-900">{analysis.analysis_data.reading_level}</p>
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Common Phrases</p>
                <div className="flex flex-wrap gap-2">
                  {analysis.analysis_data.common_phrases.slice(0, 6).map((phrase, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                    >
                      {phrase}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Key Themes</p>
                <div className="flex flex-wrap gap-2">
                  {analysis.analysis_data.key_themes.slice(0, 5).map((theme, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded-full"
                    >
                      {theme}
                    </span>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700">Sentence Structure</p>
                <p className="text-sm text-gray-600 mt-1">{analysis.analysis_data.sentence_structure}</p>
                <p className="text-xs text-gray-500 mt-1">
                  Average length: {analysis.analysis_data.avg_sentence_length} words
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No analysis available yet</p>
            <p className="text-sm text-gray-500">Import content and run analysis to see your writing style</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
