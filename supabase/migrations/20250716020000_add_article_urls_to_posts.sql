-- Add columns to store original and LinkedIn-shortened article URLs on posts
alter table posts
    add column if not exists article_url text,
    add column if not exists linkedin_article_url text; 