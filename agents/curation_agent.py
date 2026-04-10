import os
from datetime import datetime
import anthropic
from prompts.curation_prompt import CURATION_SYSTEM_PROMPT


def run_curation(research_output: str) -> str:
    """
    Run the curation agent on raw research output.

    Args:
        research_output: Raw intelligence report from the research agent.

    Returns:
        Curated, formatted intelligence brief as a string.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    today = datetime.now().strftime("%Y-%m-%d")
    report_id = datetime.now().strftime("%Y%m%d-%H%M")

    user_message = f"""Curate and format the following raw intelligence report.

Today's date: {today}
Report ID: {report_id}

RAW RESEARCH OUTPUT:
---
{research_output}
---

Apply the mandatory output format. Eliminate redundancy. Amplify signal."""

    print("[Curation Agent] Curating report...")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        system=CURATION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )

    curated = response.content[0].text
    print("[Curation Agent] Curation complete.")
    return curated
