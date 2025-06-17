
import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

interface LinkedInPostRequest {
  contentId: string;
  userId: string;
  content: string;
  title: string;
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    );

    const { contentId, userId, content, title }: LinkedInPostRequest = await req.json();

    // Get LinkedIn connection data
    const { data: connection, error: connectionError } = await supabaseClient
      .from('social_connections')
      .select('connection_data')
      .eq('user_id', userId)
      .eq('platform', 'linkedin')
      .eq('is_active', true)
      .single();

    if (connectionError || !connection) {
      throw new Error('LinkedIn connection not found or inactive');
    }

    const connectionData = connection.connection_data as any;
    const accessToken = connectionData?.access_token;

    if (!accessToken) {
      throw new Error('LinkedIn access token not found');
    }

    // Get LinkedIn user ID (person URN)
    const profileResponse = await fetch('https://api.linkedin.com/v2/people/~', {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!profileResponse.ok) {
      if (profileResponse.status === 401) {
        throw new Error('LinkedIn access token expired - reauthorization required');
      }
      throw new Error(`Failed to get LinkedIn profile: ${profileResponse.statusText}`);
    }

    const profile = await profileResponse.json();
    const personUrn = profile.id;

    // Create LinkedIn post
    const postData = {
      author: `urn:li:person:${personUrn}`,
      lifecycleState: 'PUBLISHED',
      specificContent: {
        'com.linkedin.ugc.ShareContent': {
          shareCommentary: {
            text: `${title}\n\n${content}`
          },
          shareMediaCategory: 'NONE'
        }
      },
      visibility: {
        'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
      }
    };

    const postResponse = await fetch('https://api.linkedin.com/v2/ugcPosts', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
      },
      body: JSON.stringify(postData),
    });

    if (!postResponse.ok) {
      const errorText = await postResponse.text();
      console.error('LinkedIn API error:', errorText);
      
      if (postResponse.status === 429) {
        throw new Error('LinkedIn API rate limit exceeded - please try again later');
      }
      if (postResponse.status === 401) {
        throw new Error('LinkedIn access token expired - reauthorization required');
      }
      throw new Error(`Failed to create LinkedIn post: ${postResponse.statusText}`);
    }

    const postResult = await postResponse.json();
    const linkedinPostId = postResult.id;

    // Update content_ideas record
    const { error: updateError } = await supabaseClient
      .from('content_ideas')
      .update({
        status: 'published',
        published_date: new Date().toISOString(),
        linkedin_post_id: linkedinPostId,
        publication_error: null
      })
      .eq('id', contentId);

    if (updateError) {
      console.error('Failed to update content record:', updateError);
    }

    return new Response(JSON.stringify({ 
      success: true, 
      linkedinPostId,
      message: 'Post published successfully to LinkedIn'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('LinkedIn post error:', error);
    
    // Try to update the content record with the error
    try {
      const supabaseClient = createClient(
        Deno.env.get('SUPABASE_URL') ?? '',
        Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
      );
      
      const { contentId } = await req.json();
      await supabaseClient
        .from('content_ideas')
        .update({
          status: 'failed',
          publication_error: error.message
        })
        .eq('id', contentId);
    } catch (updateError) {
      console.error('Failed to update error status:', updateError);
    }

    return new Response(JSON.stringify({ 
      error: error.message,
      success: false
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
