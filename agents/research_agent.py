import os
import json
import anthropic
from tavily import TavilyClient
from prompts.research_prompt import RESEARCH_SYSTEM_PROMPT, DEFAULT_RESEARCH_QUERY


def run_research(query: str = None, manual_content: str = None) -> str:
    """
    Run the research agent. Searches the web and returns a structured intelligence report.

    Args:
        query: Optional custom research query. Defaults to the standard current-state analysis.
        manual_content: Optional manually provided text or document content to include.

    Returns:
        Structured intelligence report as a string.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    tools = [
        {
            "name": "web_search",
            "description": (
                "Search the web for current news and developments in utilities, energy, "
                "cybersecurity, grid modernization, OT/ICS, and critical infrastructure. "
                "Run multiple targeted searches to build a complete intelligence picture."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific search query to run"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return (default 5, max 10)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    ]

    user_message = query if query else DEFAULT_RESEARCH_QUERY

    if manual_content:
        user_message += f"\n\n---\nADDITIONAL CONTEXT PROVIDED BY USER:\n{manual_content}\n---\nIncorporate this context into your analysis."

    messages = [{"role": "user", "content": user_message}]

    print("[Research Agent] Starting research...")

    # Agentic loop — runs until the agent stops using tools
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
            result = "\n".join(text_blocks)
            print("[Research Agent] Research complete.")
            return result

        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    if tool_name == "web_search":
                        search_query = tool_input["query"]
                        max_results = tool_input.get("max_results", 5)
                        print(f"[Research Agent] Searching: {search_query}")

                        try:
                            results = tavily.search(
                                query=search_query,
                                max_results=min(max_results, 10),
                                search_depth="advanced",
                                include_answer=True
                            )
                            content = json.dumps(results, indent=2)
                        except Exception as e:
                            content = f"Search error: {str(e)}"

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": content
                        })

            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Unexpected stop reason — return whatever we have
            text_blocks = [block.text for block in response.content if hasattr(block, "text")]
            return "\n".join(text_blocks) if text_blocks else "No output generated."
