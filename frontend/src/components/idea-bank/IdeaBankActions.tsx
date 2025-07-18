import React from "react";
import { Button } from "@/components/ui/button";
import { Sparkles, Edit, Trash2 } from "lucide-react";
import type { IdeaBankWithPost } from "@/lib/idea-bank-api";

interface IdeaBankActionsProps {
  ideaBankWithPost: IdeaBankWithPost;
  onGenerate(ideaBankWithPost: IdeaBankWithPost): void;
  onEdit(ideaBankWithPost: IdeaBankWithPost): void;
  onDelete(id: string): void;
}

const IdeaBankActions: React.FC<IdeaBankActionsProps> = ({
  ideaBankWithPost,
  onGenerate,
  onEdit,
  onDelete,
}) => (
  <div className="flex flex-col items-start gap-1 w-full">
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onGenerate(ideaBankWithPost)}
      className="text-indigo-600 hover:text-indigo-800 justify-start px-2 py-1 h-auto w-full min-w-0"
    >
      <Sparkles className="h-4 w-4 mr-2 flex-shrink-0" />
      <span className="truncate">Draft Post</span>
    </Button>
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onEdit(ideaBankWithPost)}
      className="text-blue-600 hover:text-blue-800 justify-start px-2 py-1 h-auto w-full min-w-0"
    >
      <Edit className="h-4 w-4 mr-2 flex-shrink-0" />
      <span className="truncate">Edit Idea</span>
    </Button>
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onDelete(ideaBankWithPost.idea_bank.id)}
      className="text-red-600 hover:text-red-800 justify-start px-2 py-1 h-auto w-full min-w-0"
    >
      <Trash2 className="h-4 w-4 mr-2 flex-shrink-0" />
      <span className="truncate">Delete</span>
    </Button>
  </div>
);

export default IdeaBankActions;
