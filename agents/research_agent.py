import os
import anthropic
from prompts.research_prompt import RESEARCH_SYSTEM_PROMPT, DEFAULT_RESEARCH_QUERY


def run_research(query: str = None, manual_content: str = None) -> str:
    """
    Run the research agent using Anthropic's built-in web search tool.

    Args:
        query: Optional custom research query. Defaults to the standard current-state analysis.
        manual_content: Optional manually provided text or document content to include.

    Returns:
        Structured intelligence report as a string.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Anthropic's built-in web search — no external API key required
    tools = [{"type": "web_search_20250305", "name": "web_search"}]

    user_message = query if query else DEFAULT_RESEARCH_QUERY

    if manual_content:
        user_message += (
            f"\n\n---\nADDITIONAL CONTEXT PROVIDED BY USER:\n{manual_content}"
            "\n---\nIncorporate this context into your analysis."
        )

    messages = [{"role": "user", "content": user_message}]

    print("[Research Agent] Starting research...")

    # Agentic loop — Anthropic executes web_search server-side;
    # we pass results back until the model reaches end_turn.
    while True:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            system=RESEARCH_SYSTEM_PROMPT,
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            text_blocks = [block.text for block in response.content if hasattr(block, "text")]
            print("[Research Agent] Research complete.")
            return "\n".join(text_blocks)

        if response.stop_reason == "tool_use":
            # Log each search query for visibility
            for block in response.content:
                if block.type == "tool_use" and block.name == "web_search":
                    print(f"[Research Agent] Searching: {block.input.get('query', '')}")

            # Pass assistant turn + tool results back — Anthropic fills in the results
            messages.append({"role": "assistant", "content": response.content})
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "",  # Built-in tool: Anthropic injects results server-side
                    }
                    for block in response.content
                    if block.type == "tool_use"
                ]
            })

        else:
            text_blocks = [block.text for block in response.content if hasattr(block, "text")]
            return "\n".join(text_blocks) if text_blocks else "No output generated."
