import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Check, X, Edit, Trash2, FileText } from "lucide-react";
import { type SocialConnection as ApiSocialConnection } from "@/lib/profile-api";
import { AnalysisOptionsModal } from "./AnalysisOptionsModal";
import { useToast } from "@/hooks/use-toast";

type SocialConnection = ApiSocialConnection;

interface PlatformConnectionCardProps {
  platformName: string;
  icon: React.ElementType;
  iconClassName?: string;
  connection: SocialConnection | null;
  onSave: (username: string) => Promise<void>;
  onDelete: () => Promise<void>;
  onAnalyze: (contentToAnalyze: string[]) => Promise<void>;
  openAnalysisModal: () => void;
  analysisModalOpen: boolean;
  setAnalysisModalOpen: (isOpen: boolean) => void;
  isLoading: boolean;
  isAnalyzing: boolean;
  usernamePlaceholder: string;
  usernamePrefix?: string;
  usernameSuffix?: string;
  children?: React.ReactNode;
}

export const PlatformConnectionCard: React.FC<PlatformConnectionCardProps> = ({
  platformName,
  icon: Icon,
  iconClassName,
  connection,
  onSave,
  onDelete,
  onAnalyze,
  openAnalysisModal,
  analysisModalOpen,
  setAnalysisModalOpen,
  isLoading,
  isAnalyzing,
  usernamePlaceholder,
  usernamePrefix,
  usernameSuffix,
  children,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [handle, setHandle] = useState("");
  const { toast } = useToast();

  useEffect(() => {
    if (connection) {
      setHandle(connection.platform_username || "");
    }
  }, [connection]);

  const handleSaveClick = async () => {
    if (!handle.trim()) {
      toast({
        title: "Error",
        description: `Please enter a valid ${platformName} handle/username`,
        variant: "destructive",
      });
      return;
    }
    await onSave(handle.trim());
    setIsEditing(false);
  };

  const handleCancelClick = () => {
    setIsEditing(false);
    setHandle(connection?.platform_username || "");
  };

  const handleEditClick = () => {
    setHandle(connection?.platform_username || "");
    setIsEditing(true);
  };

  return (
    <div className="flex flex-col justify-between p-4 border rounded-lg gap-1">
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-3">
          <Icon className={`w-5 h-5 ${iconClassName}`} />
          <div className="flex-1">
            <p className="font-medium">{platformName}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {children}
          <Button
            onClick={openAnalysisModal}
            size="sm"
            disabled={
              isLoading ||
              isAnalyzing ||
              !connection?.platform_username ||
              connection?.analysis_status === "in_progress"
            }
          >
            <FileText className="w-4 h-4 mr-2" />
            {isAnalyzing || connection?.analysis_status === "in_progress"
              ? "Analyzing..."
              : connection?.analysis_status === "completed"
              ? "Re-analyze"
              : connection?.analysis_status === "error"
              ? "Retry"
              : "Analyze"}
          </Button>
        </div>
      </div>
      <div className="flex gap-2 mt-1 w-full md:w-[50%] items-center">
        {isEditing ? (
          <>
            {usernamePrefix && (
              <span className="text-sm text-gray-500">{usernamePrefix}</span>
            )}
            <Input
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              placeholder={usernamePlaceholder}
              className="h-8 text-sm flex-grow"
              disabled={isLoading}
            />
            {usernameSuffix && (
              <span className="text-sm text-gray-500">{usernameSuffix}</span>
            )}
            <Button
              onClick={handleSaveClick}
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              disabled={isLoading}
            >
              <Check className="w-4 h-4 text-green-600" />
            </Button>
            <Button
              onClick={handleCancelClick}
              size="sm"
              variant="ghost"
              className="h-8 w-8 p-0"
              disabled={isLoading}
            >
              <X className="w-4 h-4 text-red-600" />
            </Button>
          </>
        ) : (
          <>
            <div className="flex flex-col gap-1">
              <p className="text-sm text-gray-500">
                {connection?.platform_username
                  ? `${usernamePrefix || ""}${connection.platform_username}${
                      usernameSuffix || ""
                    }`
                  : "No handle set"}
              </p>
              {connection?.analysis_completed_at &&
                connection?.analysis_status === "completed" && (
                  <p className="text-xs text-green-600">
                    Last analyzed:{" "}
                    {new Date(
                      connection.analysis_completed_at
                    ).toLocaleDateString()}
                  </p>
                )}
              {connection?.analysis_status === "error" && (
                <p className="text-xs text-red-600">Analysis failed</p>
              )}
              {connection?.analysis_status === "in_progress" && (
                <p className="text-xs text-blue-600">Analysis in progress...</p>
              )}
            </div>
            {connection?.is_active && (
              <>
                <Button
                  onClick={handleEditClick}
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  disabled={isLoading}
                >
                  <Edit className="w-3 h-3" />
                </Button>
                <Button
                  onClick={onDelete}
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                  disabled={isLoading}
                >
                  <Trash2 className="w-3 h-3 text-red-600" />
                </Button>
              </>
            )}
            {!connection?.is_active && (
              <Button onClick={handleEditClick} size="sm" variant="link">
                <Edit className="w-3 h-3" />
              </Button>
            )}
          </>
        )}
      </div>

      <AnalysisOptionsModal
        isOpen={analysisModalOpen}
        onClose={() => setAnalysisModalOpen(false)}
        onAnalyze={onAnalyze}
        platform={platformName}
        isAnalyzing={isAnalyzing}
        hasExistingAnalysis={connection?.analysis_status === "completed"}
      />
    </div>
  );
};
