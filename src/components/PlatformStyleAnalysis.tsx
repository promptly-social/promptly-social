
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { supabase } from '@/integrations/supabase/client';
import { useAuth } from '@/contexts/AuthContext';
import { BarChart3, Loader2, RefreshCw, Eye, Edit2, Save, X } from 'lucide-react';

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

interface PlatformAnalysis {
  platform: string;
  analysis_data: StyleAnalysisData;
  last_analyzed_at: string;
}

interface Props {
  platform: string;
  platformName: string;
  isConnected: boolean;
}

export const PlatformStyleAnalysis: React.FC<Props> = ({ platform, platformName, isConnected }) => {
  const [analysis, setAnalysis] = useState<PlatformAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedAnalysis, setEditedAnalysis] = useState<StyleAnalysisData | null>(null);
  const { toast } = useToast();
  const { user } = useAuth();

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
        .single();

      if (error && error.code !== 'PGRST116') throw error;
      
      if (data) {
        const platformAnalysis: PlatformAnalysis = {
          platform: data.platform || platform,
          analysis_data: data.analysis_data as unknown as StyleAnalysisData,
          last_analyzed_at: data.last_analyzed_at,
        };
        setAnalysis(platformAnalysis);
      }
    } catch (error) {
      console.error('Error fetching analysis:', error);
    }
  };

  const runAnalysis = async () => {
    if (!isConnected) {
      toast({
        title: "Connection Required",
        description: `Please connect your ${platformName} account first`,
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
          platform: platform,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to analyze writing style');
      }

      toast({
        title: "Analysis Complete",
        description: `Your ${platformName} writing style has been analyzed successfully`,
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

  const startEditing = () => {
    if (analysis) {
      setEditedAnalysis({ ...analysis.analysis_data });
      setIsEditing(true);
    }
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditedAnalysis(null);
  };

  const saveChanges = async () => {
    if (!editedAnalysis) return;

    try {
      const { error } = await supabase
        .from('writing_style_analysis')
        .upsert({
          user_id: user?.id,
          platform: platform,
          analysis_data: editedAnalysis,
          content_count: 0,
          last_analyzed_at: new Date().toISOString(),
        }, {
          onConflict: 'user_id,platform'
        });

      if (error) throw error;

      toast({
        title: "Saved",
        description: "Writing style updated successfully",
      });

      setIsEditing(false);
      fetchAnalysis();
    } catch (error) {
      console.error('Error saving changes:', error);
      toast({
        title: "Save Error",
        description: "Failed to save changes",
        variant: "destructive",
      });
    }
  };

  const updateEditedField = (field: keyof StyleAnalysisData, value: any) => {
    if (editedAnalysis) {
      setEditedAnalysis({
        ...editedAnalysis,
        [field]: value
      });
    }
  };

  const displayData = isEditing ? editedAnalysis : analysis?.analysis_data;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            {platformName} Writing Style
          </div>
          <div className="flex items-center gap-2">
            {analysis && !isEditing && (
              <Button onClick={startEditing} variant="outline" size="sm">
                <Edit2 className="w-4 h-4 mr-2" />
                Edit
              </Button>
            )}
            {isEditing && (
              <>
                <Button onClick={saveChanges} size="sm">
                  <Save className="w-4 h-4 mr-2" />
                  Save
                </Button>
                <Button onClick={cancelEditing} variant="outline" size="sm">
                  <X className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
              </>
            )}
            <Button
              onClick={runAnalysis}
              disabled={isAnalyzing || !isConnected}
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
                  {analysis ? 'Re-analyze' : 'Analyze'}
                </>
              )}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!isConnected ? (
          <div className="text-center py-8">
            <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">Connect your {platformName} account to analyze your writing style</p>
          </div>
        ) : displayData ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm font-medium text-blue-800">Tone</p>
                {isEditing ? (
                  <Input
                    value={displayData.tone}
                    onChange={(e) => updateEditedField('tone', e.target.value)}
                    className="mt-1"
                  />
                ) : (
                  <p className="text-lg text-blue-900">{displayData.tone}</p>
                )}
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-sm font-medium text-green-800">Formality</p>
                {isEditing ? (
                  <Input
                    value={displayData.formality}
                    onChange={(e) => updateEditedField('formality', e.target.value)}
                    className="mt-1"
                  />
                ) : (
                  <p className="text-lg text-green-900">{displayData.formality}</p>
                )}
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-sm font-medium text-purple-800">Vocabulary</p>
                {isEditing ? (
                  <Input
                    value={displayData.vocabulary_level}
                    onChange={(e) => updateEditedField('vocabulary_level', e.target.value)}
                    className="mt-1"
                  />
                ) : (
                  <p className="text-lg text-purple-900">{displayData.vocabulary_level}</p>
                )}
              </div>
              <div className="p-3 bg-orange-50 rounded-lg">
                <p className="text-sm font-medium text-orange-800">Reading Level</p>
                {isEditing ? (
                  <Input
                    value={displayData.reading_level}
                    onChange={(e) => updateEditedField('reading_level', e.target.value)}
                    className="mt-1"
                  />
                ) : (
                  <p className="text-lg text-orange-900">{displayData.reading_level}</p>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Common Phrases</p>
                {isEditing ? (
                  <Textarea
                    value={displayData.common_phrases.join(', ')}
                    onChange={(e) => updateEditedField('common_phrases', e.target.value.split(', '))}
                    rows={2}
                  />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {displayData.common_phrases.slice(0, 6).map((phrase, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full"
                      >
                        {phrase}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Key Themes</p>
                {isEditing ? (
                  <Textarea
                    value={displayData.key_themes.join(', ')}
                    onChange={(e) => updateEditedField('key_themes', e.target.value.split(', '))}
                    rows={2}
                  />
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {displayData.key_themes.slice(0, 5).map((theme, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-indigo-100 text-indigo-700 text-xs rounded-full"
                      >
                        {theme}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700">Sentence Structure</p>
                {isEditing ? (
                  <Textarea
                    value={displayData.sentence_structure}
                    onChange={(e) => updateEditedField('sentence_structure', e.target.value)}
                    className="mt-1"
                    rows={3}
                  />
                ) : (
                  <p className="text-sm text-gray-600 mt-1">{displayData.sentence_structure}</p>
                )}
                <p className="text-xs text-gray-500 mt-1">
                  Average length: {displayData.avg_sentence_length} words
                </p>
              </div>
            </div>

            {analysis && (
              <p className="text-xs text-gray-500 text-center">
                Last analyzed: {new Date(analysis.last_analyzed_at).toLocaleDateString()}
              </p>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <Eye className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No analysis available yet</p>
            <p className="text-sm text-gray-500">Click "Analyze" to analyze your {platformName} writing style</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
