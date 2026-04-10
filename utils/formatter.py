import os
from datetime import datetime
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent.parent / "output"


def save_report(content: str, prefix: str = "intel-brief") -> str:
    """
    Save a report to the output directory as a timestamped Markdown file.

    Args:
        content: Report content as a string.
        prefix: Filename prefix (default: 'intel-brief').

    Returns:
        Full path to the saved file.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{prefix}-{timestamp}.md"
    filepath = OUTPUT_DIR / filename

    filepath.write_text(content, encoding="utf-8")
    print(f"[Formatter] Report saved: {filepath}")
    return str(filepath)


def list_reports() -> list[dict]:
    """
    List all saved reports in the output directory.

    Returns:
        List of dicts with 'name', 'path', and 'modified' keys.
    """
    if not OUTPUT_DIR.exists():
        return []

    reports = []
    for f in sorted(OUTPUT_DIR.glob("*.md"), reverse=True):
        reports.append({
            "name": f.name,
            "path": str(f),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        })
    return reports


def load_report(filepath: str) -> str:
    """Load a report from disk."""
    return Path(filepath).read_text(encoding="utf-8")
