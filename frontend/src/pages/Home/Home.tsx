import React from "react";
import { SuggestedPosts } from "@/components/SuggestedPosts";
import AppLayout from "@/components/AppLayout";

const Home: React.FC = () => {
  return (
    <AppLayout title="Home">
      <main className="py-4 px-4 sm:py-8 sm:px-6">
        <div className="max-w-4xl mx-auto">
          <SuggestedPosts />
        </div>
      </main>
    </AppLayout>
  );
};

export default Home;
