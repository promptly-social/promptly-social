import React from "react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Plus } from "lucide-react";
import type { IdeaBankCreate } from "@/lib/idea-bank-api";

interface CreateIdeaDialogProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  formData: IdeaBankCreate;
  onFormDataChange: (formData: IdeaBankCreate) => void;
  onSubmit: () => void;
  onReset: () => void;
}

const CreateIdeaDialog: React.FC<CreateIdeaDialogProps> = ({
  isOpen,
  onOpenChange,
  formData,
  onFormDataChange,
  onSubmit,
  onReset,
}) => {
  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        if (open) {
          onReset();
        }
        onOpenChange(open);
      }}
    >
      <DialogTrigger asChild>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Idea
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add New Idea</DialogTitle>
          <DialogDescription>
            Create a new idea bank entry to organize your content inspirations.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Textarea
              id="value"
              placeholder="Enter your idea or drop in a URL to an article..."
              value={formData.data.value}
              onChange={(e) =>
                onFormDataChange({
                  ...formData,
                  data: { ...formData.data, value: e.target.value },
                })
              }
              rows={4}
              className="min-h-[100px] resize-none"
            />
          </div>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button onClick={onSubmit} disabled={!formData.data.value.trim()}>
            Create
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default CreateIdeaDialog;