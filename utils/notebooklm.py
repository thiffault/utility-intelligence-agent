"""
NotebookLM Integration

Adds intelligence reports to the "Utility Intelligence Agent — Daily Briefs"
NotebookLM notebook using the notebooklm CLI.

REQUIREMENTS:
- notebooklm CLI installed and authenticated (run `notebooklm login` once)
"""

import subprocess

NOTEBOOK_ID = "58e1284f-beb5-41a3-8c14-b300637aa5aa"
NOTEBOOK_NAME = "Utility Intelligence Agent — Daily Briefs"


def upload_report(filepath: str) -> str | None:
    """
    Add a saved report file as a source in the NotebookLM notebook.

    Args:
        filepath: Local path to the report .md file.

    Returns:
        Success message or error string.
    """
    try:
        # Switch to the target notebook using ID (name has special chars that cause RPC errors)
        result = subprocess.run(
            ["notebooklm", "use", NOTEBOOK_ID],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return f"Failed to select notebook: {result.stderr.strip()}"

        # Add the report file as a source (filepath passed as CONTENT argument)
        result = subprocess.run(
            ["notebooklm", "source", "add", filepath],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return f"Failed to add source: {result.stderr.strip()}"

        print(f"[NotebookLM] Added to notebook: {filepath}")
        return f"Added to NotebookLM: {NOTEBOOK_NAME}"

    except subprocess.TimeoutExpired:
        return "NotebookLM upload timed out."
    except FileNotFoundError:
        return "notebooklm CLI not found. Run `notebooklm login` to set up."
    except Exception as e:
        return f"NotebookLM error: {e}"


def is_configured() -> bool:
    """Check if the notebooklm CLI is available and authenticated."""
    try:
        result = subprocess.run(
            ["notebooklm", "auth", "check"],
            capture_output=True, text=True, timeout=10
        )
        return "Authentication is valid" in result.stdout
    except Exception:
        return False
