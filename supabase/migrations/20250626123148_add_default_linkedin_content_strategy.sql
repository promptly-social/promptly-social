-- Add default LinkedIn content strategy for all users
-- This migration creates a default content strategy for LinkedIn platform for all existing users

DO $$
DECLARE
    user_record RECORD;
    linkedin_strategy TEXT := 'Best Practices for Crafting Engaging LinkedIn Post Text

Start with a Strong Hook: Begin the post with a compelling question, a surprising statistic, or a bold statement to immediately capture the reader''s attention and stop them from scrolling.

Encourage Conversation: End your post with a clear call-to-action or an open-ended question that prompts readers to share their own experiences, opinions, or advice in the comments. Frame the text to start a discussion, not just to broadcast information.

Write for Readability: Use short paragraphs, single-sentence lines, and bullet points to break up large blocks of text. This makes the post easier to scan and digest on a mobile device.

Provide Genuine Value: The core of the text should offer insights, tips, or a personal story that is valuable to your target audience. Avoid pure self-promotion and focus on sharing expertise or relatable experiences.

Incorporate Strategic Mentions: When mentioning other people or companies, tag them using @. Limit this to a maximum of five relevant tags per post to encourage a response without appearing spammy.

Use Niche Hashtags: Integrate up to three specific and relevant hashtags at the end of your post. These should act as keywords for your topic (e.g., #ProjectManagementTips instead of just #Management) to connect with interested communities.';
BEGIN
    -- Insert default LinkedIn content strategy for all users who don't already have one
    INSERT INTO public.content_strategies (user_id, platform, strategy, created_at, updated_at)
    SELECT 
        u.id as user_id,
        'linkedin' as platform,
        linkedin_strategy as strategy,
        NOW() as created_at,
        NOW() as updated_at
    FROM auth.users u
    WHERE u.id NOT IN (
        -- Exclude users who already have a LinkedIn content strategy
        SELECT cs.user_id 
        FROM public.content_strategies cs 
        WHERE cs.platform = 'linkedin'
    );

    RAISE NOTICE 'Default LinkedIn content strategy added for users without existing LinkedIn strategies';
END $$; 