export interface PostMedia {
  id: string;
  post_id: string;
  user_id: string;
  media_type: "image" | "video" | "article" | null;
  file_name: string | null;
  gcs_url: string | null;
  linkedin_asset_urn: string | null;
  created_at: string;
  updated_at: string;
}

export interface Post {
  id: string;
  user_id: string;
  idea_bank_id?: string;
  title?: string;
  content: string;
  platform: string;
  topics: string[];
  status: "suggested" | "scheduled" | "posted" | "dismissed" | "draft";
  user_feedback?: "positive" | "negative";
  feedback_comment?: string;
  feedback_at?: string;
  scheduled_at?: string;
  posted_at?: string;
  article_url?: string;
  linkedin_article_url?: string;
  sharing_error?: string;
  created_at: string;
  updated_at: string;
  media: PostMedia[];
}

export interface PostUpdate {
  title?: string;
  content?: string;
  platform?: string;
  topics?: string[];
  status?: "suggested" | "scheduled" | "posted" | "dismissed" | "draft";
  scheduled_at?: string;
  user_feedback?: "positive" | "negative";
  feedback_comment?: string;
  posted_at?: string;
  article_url?: string;
  linkedin_article_url?: string;
  sharing_error?: string;
}
