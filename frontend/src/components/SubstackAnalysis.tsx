import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import {
  profileApi,
  type SubstackData,
  type SubstackAnalysisResponse,
} from "@/lib/profile-api";
import { useToast } from "@/hooks/use-toast";
import { BookOpen, RefreshCw, ExternalLink, TrendingUp } from "lucide-react";

// Using imported types from content-api

export const SubstackAnalysis: React.FC = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [substackData, setSubstackData] = useState<SubstackData[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (user) {
      checkSubstackConnection();
    }
  }, [user]);

  const checkSubstackConnection = async () => {
    try {
      const response = await profileApi.getSubstackAnalysis();

      setIsConnected(response.is_connected);
      if (response.substack_data) {
        setSubstackData(response.substack_data);
      }
    } catch (error) {
      console.error("Error checking Substack connection:", error);
    }
  };

  const analyzeSubstackProfile = async () => {
    setIsAnalyzing(true);
    try {
      // Simulate Substack analysis with sample data
      const sampleSubstackData: SubstackData[] = [
        {
          name: "The Tech Observer",
          url: "https://techobserver.substack.com",
          topics: ["Technology", "AI", "Startups", "Innovation"],
          subscriber_count: 12500,
          recent_posts: [
            {
              title: "The Rise of AI Agents in 2024",
              url: "https://techobserver.substack.com/p/ai-agents-2024",
              published_date: "2024-01-15",
            },
            {
              title: "Startup Funding Trends This Quarter",
              url: "https://techobserver.substack.com/p/funding-trends",
              published_date: "2024-01-10",
            },
          ],
        },
        {
          name: "Product Strategy Weekly",
          url: "https://productstrategy.substack.com",
          topics: ["Product Management", "Strategy", "UX Design"],
          subscriber_count: 8200,
          recent_posts: [
            {
              title: "Building Products Users Actually Want",
              url: "https://productstrategy.substack.com/p/building-products",
              published_date: "2024-01-12",
            },
          ],
        },
      ];

      // Run analysis via backend API
      const response = await profileApi.runSubstackAnalysis();

      setSubstackData(response.substack_data);
      setIsConnected(response.is_connected);

      toast({
        title: "Analysis Complete",
        description:
          "Successfully analyzed your Substack subscriptions and topics",
      });
    } catch (error) {
      console.error("Error analyzing Substack:", error);
      toast({
        title: "Analysis Error",
        description: "Failed to analyze Substack profile",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getAllTopics = () => {
    const allTopics = substackData.flatMap((stack) => stack.topics);
    return [...new Set(allTopics)];
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookOpen className="w-5 h-5" />
          Substack Analysis
        </CardTitle>
        <p className="text-sm text-gray-600">
          Analyze your Substack subscriptions to understand your content
          interests
        </p>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600">
              Status:{" "}
              <span className="font-medium">
                {isConnected ? "Connected" : "Not Connected"}
              </span>
            </p>
            {substackData.length > 0 && (
              <p className="text-xs text-gray-500">
                Found {substackData.length} Substack subscriptions
              </p>
            )}
          </div>
          <Button
            onClick={analyzeSubstackProfile}
            disabled={isAnalyzing}
            size="sm"
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <TrendingUp className="w-4 h-4 mr-2" />
                {isConnected ? "Re-analyze" : "Analyze Substacks"}
              </>
            )}
          </Button>
        </div>

        {substackData.length > 0 && (
          <div className="space-y-4">
            {/* Topics Overview */}
            <div>
              <h4 className="font-medium mb-2">Your Interest Topics</h4>
              <div className="flex flex-wrap gap-2">
                {getAllTopics().map((topic, index) => (
                  <Badge key={index} variant="secondary">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Substack List */}
            <div>
              <h4 className="font-medium mb-2">Subscribed Substacks</h4>
              <div className="space-y-3">
                {substackData.map((stack, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h5 className="font-medium">{stack.name}</h5>
                          <Button variant="ghost" size="sm" asChild>
                            <a
                              href={stack.url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </Button>
                        </div>
                        {stack.subscriber_count && (
                          <p className="text-xs text-gray-500 mb-2">
                            {stack.subscriber_count.toLocaleString()}{" "}
                            subscribers
                          </p>
                        )}
                        <div className="flex flex-wrap gap-1">
                          {stack.topics.map((topic, idx) => (
                            <Badge
                              key={idx}
                              variant="outline"
                              className="text-xs"
                            >
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {!isConnected && substackData.length === 0 && (
          <div className="text-center py-8">
            <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">No Substack analysis available</p>
            <p className="text-sm text-gray-500">
              Click "Analyze Substacks" to discover your content interests based
              on your subscriptions
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
