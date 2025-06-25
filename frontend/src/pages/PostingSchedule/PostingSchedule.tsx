import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import AppLayout from "@/components/AppLayout";
import { Calendar } from "lucide-react";

const PostingSchedule: React.FC = () => {
  return (
    <AppLayout title="Posting Schedule" emailBreakpoint="md">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <div className="space-y-4 sm:space-y-6">
            <div className="text-center">
              <p className="text-sm sm:text-lg text-gray-600 max-w-2xl mx-auto">
                Manage your content calendar and scheduled posts
              </p>
            </div>

            <Card>
              <CardContent className="py-8 sm:py-12 text-center">
                <Calendar className="w-8 sm:w-12 h-8 sm:h-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-base sm:text-lg font-medium mb-2">
                  Posting Schedule Coming Soon
                </h3>
                <p className="text-sm sm:text-base text-gray-600">
                  Your scheduled content and posting calendar will appear here
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </AppLayout>
  );
};

export default PostingSchedule;
