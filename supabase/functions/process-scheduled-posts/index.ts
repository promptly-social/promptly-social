
import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    // Get all scheduled posts that are ready to be published
    const now = new Date().toISOString();
    const { data: scheduledPosts, error: fetchError } = await supabaseClient
      .from('content_ideas')
      .select('*')
      .eq('status', 'scheduled')
      .lte('scheduled_date', now)
      .limit(10); // Process max 10 posts at a time

    if (fetchError) {
      throw new Error(`Failed to fetch scheduled posts: ${fetchError.message}`);
    }

    const results = [];

    for (const post of scheduledPosts || []) {
      try {
        if (post.content_type === 'linkedin_post') {
          // Call the LinkedIn posting function
          const response = await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/linkedin-post`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${Deno.env.get('SUPABASE_ANON_KEY')}`,
            },
            body: JSON.stringify({
              contentId: post.id,
              userId: post.user_id,
              content: post.original_input,
              title: post.title,
            }),
          });

          const result = await response.json();
          results.push({
            contentId: post.id,
            success: result.success,
            message: result.message || result.error,
          });
        }
      } catch (error) {
        console.error(`Failed to process post ${post.id}:`, error);
        
        // Update the post status to failed
        await supabaseClient
          .from('content_ideas')
          .update({
            status: 'failed',
            publication_error: error.message
          })
          .eq('id', post.id);

        results.push({
          contentId: post.id,
          success: false,
          message: error.message,
        });
      }
    }

    return new Response(JSON.stringify({
      processed: results.length,
      results
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Process scheduled posts error:', error);
    return new Response(JSON.stringify({ 
      error: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
