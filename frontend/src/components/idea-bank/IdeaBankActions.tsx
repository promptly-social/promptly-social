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
  <div className="flex items-center gap-1">
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onGenerate(ideaBankWithPost)}
      className="text-indigo-600 hover:text-indigo-800 p-1 h-8 w-8"
    >
      <Sparkles className="w-4 h-4" />
    </Button>
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onEdit(ideaBankWithPost)}
      className="text-blue-600 hover:text-blue-800 p-1 h-8 w-8"
    >
      <Edit className="w-4 h-4" />
    </Button>
    <Button
      variant="ghost"
      size="sm"
      onClick={() => onDelete(ideaBankWithPost.idea_bank.id)}
      className="text-red-600 hover:text-red-800 p-1 h-8 w-8"
    >
      <Trash2 className="w-4 h-4" />
    </Button>
  </div>
);

export default IdeaBankActions;
