import React from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ArrowUpDown } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import IdeaBankContent from "./IdeaBankContent";
import IdeaBankLastPost from "./IdeaBankLastPost";
import IdeaBankActions from "./IdeaBankActions";
import type { IdeaBankWithPost, SuggestedPost } from "@/lib/idea-bank-api";

interface SortConfig {
  key: "updated_at";
  direction: "asc" | "desc";
}

interface IdeaBankMediumViewProps {
  data: IdeaBankWithPost[];
  isLoading: boolean;
  onSort: (key: SortConfig["key"]) => void;
  onEdit: (ideaBankWithPost: IdeaBankWithPost) => void;
  onDelete: (id: string) => void;
  onGenerate: (ideaBankWithPost: IdeaBankWithPost) => void;
  onViewPost: (post: SuggestedPost) => void;
}

const TableSkeleton = ({ cols }: { cols: number }) => (
  <>
    {Array.from({ length: 5 }).map((_, rowIdx) => (
      <TableRow key={rowIdx}>
        {Array.from({ length: cols }).map((__, colIdx) => (
          <TableCell key={colIdx}>
            <Skeleton className="h-4 w-full" />
          </TableCell>
        ))}
      </TableRow>
    ))}
  </>
);

const SortButton: React.FC<{
  column: SortConfig["key"];
  children: React.ReactNode;
  onSort: (key: SortConfig["key"]) => void;
}> = ({ column, children, onSort }) => (
  <Button
    variant="ghost"
    onClick={() => onSort(column)}
    className="flex items-center gap-1 font-semibold"
  >
    {children}
    <ArrowUpDown className="w-4 h-4" />
  </Button>
);

const IdeaBankMediumView: React.FC<IdeaBankMediumViewProps> = ({
  data,
  isLoading,
  onSort,
  onEdit,
  onDelete,
  onGenerate,
  onViewPost,
}) => {
  return (
    <div className="hidden md:block xl:hidden border rounded-lg overflow-x-auto">
      <Table className="min-w-full">
        <TableHeader>
          <TableRow>
            <TableHead className="min-w-[250px]">Content</TableHead>
            <TableHead className="w-[120px]">
              <SortButton column="updated_at" onSort={onSort}>
                Updated
              </SortButton>
            </TableHead>
            <TableHead className="w-[140px]">Last Used</TableHead>
            <TableHead className="w-[120px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            <TableSkeleton cols={4} />
          ) : data.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center py-8">
                <div className="text-muted-foreground">
                  No ideas found. Create your first idea to get started.
                </div>
              </TableCell>
            </TableRow>
          ) : (
            data.map((ideaBankWithPost) => {
              const ideaBank = ideaBankWithPost.idea_bank;
              const latestPost = ideaBankWithPost.latest_post;
              return (
                <TableRow key={ideaBank.id}>
                  <TableCell className="min-w-0">
                    <IdeaBankContent ideaBank={ideaBank} />
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm">
                    {new Date(ideaBank.updated_at).toLocaleDateString(
                      "en-US",
                      {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      }
                    )}
                  </TableCell>
                  <TableCell className="text-sm">
                    <IdeaBankLastPost
                      latestPost={latestPost}
                      onView={onViewPost}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="w-full max-w-[120px]">
                      <IdeaBankActions
                        ideaBankWithPost={ideaBankWithPost}
                        onEdit={onEdit}
                        onDelete={onDelete}
                        onGenerate={onGenerate}
                      />
                    </div>
                  </TableCell>
                </TableRow>
              );
            })
          )}
        </TableBody>
      </Table>
    </div>
  );
};

export default IdeaBankMediumView;