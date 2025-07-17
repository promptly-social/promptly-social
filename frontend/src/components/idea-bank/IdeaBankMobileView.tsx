import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import IdeaBankContent from "./IdeaBankContent";
import IdeaBankLastPost from "./IdeaBankLastPost";
import IdeaBankActions from "./IdeaBankActions";
import type { IdeaBankWithPost, SuggestedPost } from "@/lib/idea-bank-api";

interface SortConfig {
  key: "updated_at";
  direction: "asc" | "desc";
}

interface IdeaBankMobileViewProps {
  data: IdeaBankWithPost[];
  isLoading: boolean;
  sortConfig: SortConfig;
  onEdit: (ideaBankWithPost: IdeaBankWithPost) => void;
  onDelete: (id: string) => void;
  onGenerate: (ideaBankWithPost: IdeaBankWithPost) => void;
  onViewPost: (post: SuggestedPost) => void;
  formatDate: (dateString: string) => string;
}

const MobileSkeleton = () => (
  <div className="space-y-4">
    {Array.from({ length: 4 }).map((_, idx) => (
      <Card key={idx} className="border">
        <CardContent className="p-4 space-y-3">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
          <div className="flex gap-2">
            <Skeleton className="h-4 w-16 rounded-full" />
            <Skeleton className="h-4 w-16 rounded-full" />
          </div>
        </CardContent>
      </Card>
    ))}
  </div>
);

const IdeaBankMobileView: React.FC<IdeaBankMobileViewProps> = ({
  data,
  isLoading,
  sortConfig,
  onEdit,
  onDelete,
  onGenerate,
  onViewPost,
  formatDate,
}) => {
  return (
    <div className="block md:hidden space-y-4">
      {/* Mobile Sort Info */}
      <div className="flex items-center justify-between text-sm text-gray-500 px-1">
        <span>
          Sorted by: Last Updated ({sortConfig.direction === "asc" ? "↑" : "↓"})
        </span>
        <span>{data.length} ideas</span>
      </div>

      {isLoading ? (
        <MobileSkeleton />
      ) : data.length === 0 ? (
        <div className="text-center py-8 bg-white rounded-lg border">
          <div className="text-muted-foreground">
            No ideas found. Create your first idea to get started.
          </div>
        </div>
      ) : (
        data.map((ideaBankWithPost) => {
          const ideaBank = ideaBankWithPost.idea_bank;
          const latestPost = ideaBankWithPost.latest_post;
          return (
            <div
              key={ideaBank.id}
              className="bg-white rounded-lg border p-4 space-y-3"
            >
              <div className="space-y-2">
                <div>
                  <span className="text-sm font-medium text-gray-500">
                    Content:
                  </span>
                  <div className="mt-1">
                    <IdeaBankContent ideaBank={ideaBank} />
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <div className="text-gray-500">
                    {formatDate(ideaBank.updated_at)}
                  </div>
                </div>

                <div>
                  <span className="text-sm font-medium text-gray-500">
                    Last Post Used:
                  </span>
                  <div className="mt-1">
                    <IdeaBankLastPost
                      latestPost={latestPost}
                      onView={onViewPost}
                    />
                  </div>
                </div>
              </div>
              <IdeaBankActions
                ideaBankWithPost={ideaBankWithPost}
                onEdit={onEdit}
                onDelete={onDelete}
                onGenerate={onGenerate}
              />
            </div>
          );
        })
      )}
    </div>
  );
};

export default IdeaBankMobileView;