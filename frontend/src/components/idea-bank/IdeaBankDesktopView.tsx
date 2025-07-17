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

interface IdeaBankDesktopViewProps {
  data: IdeaBankWithPost[];
  isLoading: boolean;
  onSort: (key: SortConfig["key"]) => void;
  onEdit: (ideaBankWithPost: IdeaBankWithPost) => void;
  onDelete: (id: string) => void;
  onGenerate: (ideaBankWithPost: IdeaBankWithPost) => void;
  onViewPost: (post: SuggestedPost) => void;
  formatDate: (dateString: string) => string;
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

const IdeaBankDesktopView: React.FC<IdeaBankDesktopViewProps> = ({
  data,
  isLoading,
  onSort,
  onEdit,
  onDelete,
  onGenerate,
  onViewPost,
  formatDate,
}) => {
  return (
    <div className="hidden xl:block border rounded-lg overflow-x-auto">
      <Table className="min-w-full">
        <TableHeader>
          <TableRow>
            <TableHead className="min-w-[200px]">Content</TableHead>
            <TableHead className="w-[150px]">
              <SortButton column="updated_at" onSort={onSort}>
                Last Updated
              </SortButton>
            </TableHead>
            <TableHead className="w-[180px]">Last Post Used</TableHead>
            <TableHead className="w-[100px]">Actions</TableHead>
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
                  <TableCell className="text-muted-foreground">
                    {formatDate(ideaBank.updated_at)}
                  </TableCell>
                  <TableCell>
                    <IdeaBankLastPost
                      latestPost={latestPost}
                      onView={onViewPost}
                    />
                  </TableCell>
                  <TableCell>
                    <IdeaBankActions
                      ideaBankWithPost={ideaBankWithPost}
                      onEdit={onEdit}
                      onDelete={onDelete}
                      onGenerate={onGenerate}
                    />
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

export default IdeaBankDesktopView;