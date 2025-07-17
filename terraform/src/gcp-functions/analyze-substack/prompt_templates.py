"""Prompt templates used across Substack, LinkedIn and import-sample analyzers.

Each helper returns a **plain string** (no markdown) ready to be passed to
`LLMClient.run_prompt`.  Where useful, keyword arguments are provided so that
call-sites can stay concise.
"""

from __future__ import annotations

from typing import List

# NOTE: All prompts must be returned as *plain text* – no markdown, code fences or extra commentary.
# Each helper below therefore ends with `.strip()` to remove any accidental leading/trailing
# whitespace that the LLM might otherwise echo back.

# ---------------------------------------------------------------------------
# Substack prompts
# ---------------------------------------------------------------------------


def writing_style_substack(urls: List[str], existing_analysis: str = "") -> str:
    urls_block = "\n".join(urls)
    return (
        f"""You are an expert at analysing an author's writing style. Given a list of
        article URLs and (optionally) a previous analysis, **enhance or create** the
        analysis while retaining any correct existing insights. Use concise,
        gender-neutral language. List each observation on its own line and keep the
        total response under ~200 words. Do NOT output markdown, bullet symbols or
        headlines – plain text only.

        Previous analysis (may be empty):
        {existing_analysis}

        URLs to analyse:
        {urls_block}
        """.strip()
    )


def topics_substack(urls: List[str]) -> str:
    urls_block = "\n".join(urls)
    # Must return **only** valid JSON (no markdown fences). Example:
    # {"topics": ["AI", "Climate"], "error": ""}
    return (
        f"""You are an expert at extracting overarching topics from a list of
        articles. For the URLs provided, return a JSON object with exactly two keys:
          • topics – a list of short topic names (Title Case)
          • error  – an empty string on success or a short description if something
            went wrong
        Respond with the JSON only, without additional text or markdown.

        URLs:
        {urls_block}
        """.strip()
    )


def bio_substack(urls: List[str], substack_bio: str, current_bio: str) -> str:
    urls_block = "\n".join(urls)
    return (
        f"""You are an expert copywriter. Create or update the author's personal bio
        using their Substack posts, their current Substack bio and the existing bio
        below. If a bio already exists, *improve it* – do not replace the author's
        voice. Use first-person perspective and gender-neutral language. Plain text
        only; no markdown or emojis. Aim for 2–3 concise sentences.

        Existing bio (may be empty):
        {current_bio}

        Substack bio (may be empty):
        {substack_bio}

        Reference posts:
        {urls_block}
        """.strip()
    )


# ---------------------------------------------------------------------------
# LinkedIn prompts
# ---------------------------------------------------------------------------


def topics_linkedin(combined_posts: str) -> str:
    return (
        f"""You are an expert at identifying recurring topics and interests from a
        user's LinkedIn activity. Provide a line-separated list of concise topic
        names (Title Case, no bullets). No additional commentary – just the topics.

        LinkedIn posts & interactions:
        {combined_posts}
        """.strip()
    )


def writing_style_linkedin(combined_posts: str) -> str:
    return (
        f"""You are an expert at analysing the writing style of LinkedIn posts. Write
        a plain-text summary (no markdown) with each insight on its own line.
        Consider tone, voice, sentence structure, humour, jargon level,
        persuasion techniques and overall personality. Keep it under ~150 words.

        LinkedIn posts:
        {combined_posts}
        """.strip()
    )


def bio_linkedin(combined_posts: str, profile_text: str, current_bio: str) -> str:
    return (
        f"""You are an expert copywriter. Draft or enhance the author's LinkedIn bio
        using the information below. Preserve their voice; write in first person with
        gender-neutral language. Plain text, no markdown or emojis. Suggest 2–3
        engaging sentences highlighting roles, expertise and passions.

        Existing bio (may be empty):
        {current_bio}

        LinkedIn profile summary (may be partial):
        {profile_text}

        Sample posts:
        {combined_posts}
        """.strip()
    )


# ---------------------------------------------------------------------------
# Import-sample prompts
# ---------------------------------------------------------------------------


def writing_style_from_text(sample: str) -> str:
    return (
        f"""You are an expert at analysing writing style. From the sample below, write
        a plain-text summary (no markdown) of the author's style. Put each insight on
        its own line and keep the entire analysis under ~150 words. Consider tone,
        voice, sentence structure, humour, jargon level, persuasion techniques and
        overall personality.

        Writing sample:
        {sample}
        """.strip()
    )
