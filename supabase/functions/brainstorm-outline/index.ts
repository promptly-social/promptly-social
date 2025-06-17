
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
    const { messages, currentOutline, contentType } = await req.json();
    
    if (!messages || !currentOutline) {
      throw new Error('Messages and current outline are required');
    }

    const systemPrompt = `You are an expert content strategist helping users brainstorm and refine their content outlines. 

Current outline:
Title: ${currentOutline.title}
Sections: ${JSON.stringify(currentOutline.sections, null, 2)}

Content Type: ${contentType === 'blog_post' ? 'Blog Post' : 'LinkedIn Post'}

Your role is to:
1. Answer questions about the outline
2. Suggest improvements and alternatives
3. Help expand or refine sections
4. Provide strategic content advice

If the user asks you to modify the outline, respond with both:
1. A conversational response explaining the changes
2. An updated outline structure

When providing an updated outline, end your response with:
UPDATED_OUTLINE: {JSON structure of the updated outline}

Keep your responses conversational and helpful. Focus on practical content strategy advice.`;

    // Prepare messages for OpenAI
    const openAIMessages = [
      { role: 'system', content: systemPrompt },
      ...messages.map((msg: any) => ({ role: msg.role, content: msg.content }))
    ];

    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${Deno.env.get('OPENAI_API_KEY')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: openAIMessages,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${await response.text()}`);
    }

    const data = await response.json();
    const aiResponse = data.choices[0].message.content;
    
    // Check if response contains an updated outline
    let updatedOutline = null;
    const outlineMatch = aiResponse.match(/UPDATED_OUTLINE:\s*({[\s\S]*})/);
    if (outlineMatch) {
      try {
        updatedOutline = JSON.parse(outlineMatch[1]);
      } catch (parseError) {
        console.error('Error parsing updated outline:', parseError);
      }
    }

    // Clean response by removing the outline JSON if present
    const cleanResponse = aiResponse.replace(/UPDATED_OUTLINE:\s*{[\s\S]*}/, '').trim();

    return new Response(JSON.stringify({ 
      response: cleanResponse,
      updatedOutline: updatedOutline 
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in brainstorm-outline function:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
