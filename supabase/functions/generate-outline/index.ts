
import "https://deno.land/x/xhr@0.1.0/mod.ts";
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { content, contentType } = await req.json();
    
    if (!content) {
      throw new Error('No content provided');
    }

    const systemPrompt = contentType === 'blog_post' 
      ? `You are an expert content strategist specializing in blog posts. Generate a comprehensive outline for a blog post based on the user's idea. Return a JSON object with the following structure:
{
  "title": "Compelling blog post title",
  "sections": [
    {
      "heading": "Section title",
      "keyPoints": ["Key point 1", "Key point 2", "Key point 3"]
    }
  ]
}
Make the outline detailed and actionable for professional content creators.`
      : `You are an expert LinkedIn content strategist. Generate a structured outline for a LinkedIn post based on the user's idea. Return a JSON object with the following structure:
{
  "title": "Engaging LinkedIn post hook/title",
  "sections": [
    {
      "heading": "Section purpose (e.g., 'Hook', 'Story', 'Insight', 'Call to Action')",
      "keyPoints": ["Key point 1", "Key point 2", "Key point 3"]
    }
  ]
}
Focus on engagement, professional insights, and LinkedIn best practices.`;

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: content }
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${await response.text()}`);
    }

    const data = await response.json();
    const outlineText = data.choices[0].message.content;
    
    try {
      const outline = JSON.parse(outlineText);
      return new Response(JSON.stringify({ outline }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    } catch (parseError) {
      console.error('Error parsing AI response:', parseError);
      return new Response(JSON.stringify({ error: 'Failed to parse AI response' }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

  } catch (error) {
    console.error('Error in generate-outline function:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
