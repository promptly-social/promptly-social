import React from "react";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type { IdeaBankCreate } from "@/lib/idea-bank-api";

interface EditIdeaDialogProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  editFormData: IdeaBankCreate["data"] | null;
  onEditFormDataChange: (formData: IdeaBankCreate["data"]) => void;
  onSubmit: () => void;
  onClose: () => void;
}

const EditIdeaDialog: React.FC<EditIdeaDialogProps> = ({
  isOpen,
  onOpenChange,
  editFormData,
  onEditFormDataChange,
  onSubmit,
  onClose,
}) => {
  return (
    <Dialog
      open={isOpen}
      onOpenChange={(open) => {
        onOpenChange(open);
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-[425px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Idea</DialogTitle>
          <DialogDescription>Update your idea bank entry.</DialogDescription>
        </DialogHeader>
        {editFormData && (
          <>
            <div className="space-y-4">
              <div className="space-y-2">
                <Textarea
                  key="value-textarea"
                  id="edit-value"
                  placeholder="Enter your idea or text content..."
                  value={editFormData.value}
                  onChange={(e) =>
                    onEditFormDataChange({
                      ...editFormData,
                      value: e.target.value,
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
              <Button
                onClick={onSubmit}
                disabled={!editFormData.value.trim()}
              >
                Update
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default EditIdeaDialog;