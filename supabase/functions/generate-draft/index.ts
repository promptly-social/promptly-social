
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
    const { outline, contentType } = await req.json();
    
    if (!outline) {
      throw new Error('Outline is required');
    }

    const systemPrompt = contentType === 'blog_post' 
      ? `You are an expert blog writer. Generate a complete, well-structured blog post based on the provided outline. 

Guidelines:
- Write in an engaging, professional tone
- Include an compelling introduction that hooks the reader
- Develop each section thoroughly with detailed explanations and examples
- Use clear transitions between sections
- Include a strong conclusion with key takeaways
- Aim for 800-1500 words
- Use subheadings to structure the content
- Write in markdown format

Outline:
Title: ${outline.title}
Sections: ${JSON.stringify(outline.sections, null, 2)}

Generate a complete blog post based on this outline.`
      : `You are an expert LinkedIn content creator. Generate a compelling LinkedIn post based on the provided outline.

Guidelines:
- Write in a professional yet conversational tone
- Start with a strong hook to grab attention
- Keep it concise but impactful (aim for 200-400 words)
- Include relevant insights and actionable advice
- End with a call-to-action or thought-provoking question
- Use line breaks and emojis strategically for readability
- Make it engaging for professional networking

Outline:
Title: ${outline.title}
Sections: ${JSON.stringify(outline.sections, null, 2)}

Generate a complete LinkedIn post based on this outline.`;

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
          { role: 'user', content: 'Please generate the full draft based on the outline provided.' }
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenAI API error: ${await response.text()}`);
    }

    const data = await response.json();
    const draft = data.choices[0].message.content;
    
    return new Response(JSON.stringify({ draft }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in generate-draft function:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});
