import os
from datetime import datetime
from dotenv import load_dotenv
import gradio as gr

load_dotenv()

from agents.research_agent import run_research
from agents.curation_agent import run_curation
from utils.formatter import save_report, list_reports, load_report
from utils.notebooklm import upload_report, is_configured


# ── Pipeline ────────────────────────────────────────────────────────────────

def run_pipeline(query: str = None, manual_text: str = None, manual_url: str = None) -> tuple[str, str, str]:
    """Run both agents and save the report. Returns (report, filepath, status)."""
    try:
        manual_content = None

        if manual_text and manual_text.strip():
            manual_content = manual_text.strip()

        if manual_url and manual_url.strip():
            try:
                import requests
                resp = requests.get(manual_url.strip(), timeout=15)
                resp.raise_for_status()
                url_content = f"URL: {manual_url}\n\n{resp.text[:8000]}"
                manual_content = (manual_content + "\n\n" + url_content) if manual_content else url_content
            except Exception as e:
                return "", "", f"Failed to fetch URL: {e}"

        research_output = run_research(query=query or None, manual_content=manual_content)
        curated_report = run_curation(research_output)
        filepath = save_report(curated_report)

        return curated_report, filepath, f"Report saved: {filepath}"

    except Exception as e:
        return "", "", f"Error: {e}"


# ── Gradio Handlers ──────────────────────────────────────────────────────────

def handle_auto_run():
    report, filepath, status = run_pipeline()
    return report, status


def handle_manual_run(manual_text, manual_url, custom_query):
    report, filepath, status = run_pipeline(
        query=custom_query if custom_query.strip() else None,
        manual_text=manual_text,
        manual_url=manual_url
    )
    return report, status


def handle_notebooklm_upload(filepath_state):
    if not filepath_state:
        return "No report to upload. Run a research session first."
    if not is_configured():
        return (
            "Google Drive not configured.\n"
            "Set GOOGLE_SERVICE_ACCOUNT_JSON and NOTEBOOKLM_DRIVE_FOLDER_ID in your .env file.\n"
            "See utils/notebooklm.py for setup instructions."
        )
    return upload_report(filepath_state)


def handle_load_report(report_name, reports_cache):
    for r in reports_cache:
        if r["name"] == report_name:
            content = load_report(r["path"])
            return content
    return "Report not found."


def refresh_reports():
    reports = list_reports()
    names = [r["name"] for r in reports]
    return gr.Dropdown(choices=names, value=names[0] if names else None), reports


# ── UI ───────────────────────────────────────────────────────────────────────

def build_ui():
    with gr.Blocks(title="Utility Intelligence Agent") as app:

        gr.Markdown("""
# Utility Intelligence Agent
**Utilities | Energy | Critical Infrastructure | Cybersecurity**

Elite sector intelligence powered by Claude + real-time web research.
        """)

        filepath_state = gr.State("")
        reports_cache = gr.State([])

        with gr.Tabs():

            # ── Tab 1: Auto Research ─────────────────────────────────────────
            with gr.Tab("Auto Research"):
                gr.Markdown("Runs the full intelligence pipeline — web search → research → curation → report.")

                run_btn = gr.Button("Run Intelligence Brief", variant="primary", size="lg")
                auto_status = gr.Textbox(label="Status", interactive=False, lines=1)
                auto_output = gr.Markdown(label="Intelligence Brief")

                upload_btn = gr.Button("Upload to NotebookLM (Google Drive)", variant="secondary")
                upload_status = gr.Textbox(label="Upload Status", interactive=False, lines=1)

                def auto_run_and_store():
                    report, filepath, status = run_pipeline()
                    return report, filepath, status

                run_btn.click(
                    fn=auto_run_and_store,
                    outputs=[auto_output, filepath_state, auto_status]
                )

                upload_btn.click(
                    fn=handle_notebooklm_upload,
                    inputs=[filepath_state],
                    outputs=[upload_status]
                )

            # ── Tab 2: Manual Feed ───────────────────────────────────────────
            with gr.Tab("Manual Feed"):
                gr.Markdown("Provide your own content — paste text, a URL, or add a custom query focus.")

                with gr.Row():
                    with gr.Column():
                        manual_url = gr.Textbox(
                            label="URL (optional)",
                            placeholder="https://example.com/article",
                            lines=1
                        )
                        manual_text = gr.Textbox(
                            label="Paste Content (optional)",
                            placeholder="Paste article text, report excerpts, or raw notes here...",
                            lines=8
                        )
                        custom_query = gr.Textbox(
                            label="Custom Research Focus (optional)",
                            placeholder="E.g. 'Focus on OT security incidents in Canadian utilities this week'",
                            lines=2
                        )
                        manual_run_btn = gr.Button("Run with Manual Input", variant="primary")

                manual_status = gr.Textbox(label="Status", interactive=False, lines=1)
                manual_output = gr.Markdown(label="Intelligence Brief")

                manual_upload_btn = gr.Button("Upload to NotebookLM (Google Drive)", variant="secondary")
                manual_upload_status = gr.Textbox(label="Upload Status", interactive=False, lines=1)

                def manual_run_and_store(text, url, query):
                    report, filepath, status = run_pipeline(
                        query=query if query.strip() else None,
                        manual_text=text,
                        manual_url=url
                    )
                    return report, filepath, status

                manual_run_btn.click(
                    fn=manual_run_and_store,
                    inputs=[manual_text, manual_url, custom_query],
                    outputs=[manual_output, filepath_state, manual_status]
                )

                manual_upload_btn.click(
                    fn=handle_notebooklm_upload,
                    inputs=[filepath_state],
                    outputs=[manual_upload_status]
                )

            # ── Tab 3: Saved Reports ─────────────────────────────────────────
            with gr.Tab("Saved Reports"):
                gr.Markdown("Browse and read previously generated intelligence briefs.")

                with gr.Row():
                    refresh_btn = gr.Button("Refresh List", variant="secondary")
                    report_dropdown = gr.Dropdown(label="Select Report", choices=[], interactive=True)

                load_btn = gr.Button("Load Report", variant="primary")
                saved_output = gr.Markdown(label="Report Content")

                refresh_btn.click(
                    fn=refresh_reports,
                    outputs=[report_dropdown, reports_cache]
                )

                load_btn.click(
                    fn=handle_load_report,
                    inputs=[report_dropdown, reports_cache],
                    outputs=[saved_output]
                )

    return app


# ── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    required = ["ANTHROPIC_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your API keys.")
        exit(1)

    app = build_ui()
    app.launch(share=False, server_port=7860, theme=gr.themes.Soft())
