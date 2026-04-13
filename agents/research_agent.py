import os
import re
import anthropic
from prompts.research_prompt import RESEARCH_SYSTEM_PROMPT, DEFAULT_RESEARCH_QUERY


def _extract_urls(text: str) -> list[dict]:
    """Extract URLs and their link text from markdown and plain text."""
    sources = {}

    # Markdown links: [title](url)
    for title, url in re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', text):
        if url not in sources:
            sources[url] = title.strip()

    # Bare URLs not already captured
    for url in re.findall(r'(?<!\()(https?://[^\s\)\]"\'>,]+)', text):
        if url not in sources:
            sources[url] = url

    return [{"url": url, "title": title} for url, title in sources.items()]


def run_research(query: str = None, manual_content: str = None) -> tuple[str, list[dict]]:
    """
    Run the research agent using Anthropic's built-in web search tool.

    Returns:
        (report_text, sources) where sources is a list of {"url", "title"} dicts.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    tools = [{"type": "web_search_20250305", "name": "web_search"}]

    user_message = query if query else DEFAULT_RESEARCH_QUERY

    if manual_content:
        user_message += (
            f"\n\n---\nADDITIONAL CONTEXT PROVIDED BY USER:\n{manual_content}"
            "\n---\nIncorporate this context into your analysis."
        )

    messages = [{"role": "user", "content": user_message}]
    all_text = []

    print("[Research Agent] Starting research...")

    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            system=RESEARCH_SYSTEM_PROMPT,
            tools=tools,
            messages=messages
        )

        # Collect all text blocks across turns for URL extraction
        for block in response.content:
            if hasattr(block, "text"):
                all_text.append(block.text)

        if response.stop_reason == "end_turn":
            full_text = "\n".join(all_text)
            sources = _extract_urls(full_text)
            print(f"[Research Agent] Research complete. {len(sources)} sources found.")
            return full_text, sources

        if response.stop_reason == "tool_use":
            for block in response.content:
                if block.type == "tool_use" and block.name == "web_search":
                    print(f"[Research Agent] Searching: {block.input.get('query', '')}")

            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "",
                    }
                    for block in response.content
                    if block.type == "tool_use"
                ]
            })

        else:
            full_text = "\n".join(all_text)
            return full_text, _extract_urls(full_text)
