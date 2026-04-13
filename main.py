import os
from dotenv import load_dotenv
import gradio as gr

load_dotenv()

from agents.research_agent import run_research
from agents.curation_agent import run_curation
from utils.formatter import save_report, list_reports, load_report
from utils.notebooklm import upload_report, is_configured


# ── CSS ──────────────────────────────────────────────────────────────────────

CSS = """
/* Base */
body, .gradio-container {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
    font-family: 'Segoe UI', system-ui, sans-serif !important;
}

/* Header */
#header {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    border-bottom: 1px solid #00d4ff33;
    padding: 20px 28px 16px;
    margin-bottom: 0;
}
#header h1 {
    color: #00d4ff !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    margin: 0 !important;
}
#header p {
    color: #8b949e !important;
    font-size: 0.8rem !important;
    margin: 4px 0 0 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* Sidebar */
#sidebar {
    background: #161b22;
    border-right: 1px solid #30363d;
    padding: 20px 14px;
    min-height: 80vh;
}

/* Main content */
#main-content {
    background: #0d1117;
    padding: 20px 28px;
}

/* Buttons */
#run-btn {
    background: linear-gradient(135deg, #00d4ff, #0099cc) !important;
    color: #0d1117 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.05em !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 14px !important;
    width: 100% !important;
    text-transform: uppercase !important;
}
#run-btn:hover {
    background: linear-gradient(135deg, #33ddff, #00bbee) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 15px #00d4ff44 !important;
}

#notebooklm-btn {
    background: #1e2a1e !important;
    color: #4ade80 !important;
    border: 1px solid #4ade8044 !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    width: 100% !important;
}
#notebooklm-btn:hover {
    background: #243024 !important;
    border-color: #4ade80 !important;
}

#manual-run-btn {
    background: #1a1f2e !important;
    color: #00d4ff !important;
    border: 1px solid #00d4ff44 !important;
    border-radius: 6px !important;
    width: 100% !important;
}

/* Status pill */
#status-box textarea, #status-box input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #8b949e !important;
    border-radius: 20px !important;
    font-size: 0.75rem !important;
    padding: 6px 14px !important;
}

/* Report output */
#report-output {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    padding: 24px !important;
    min-height: 60vh !important;
}
#report-output h1 { color: #00d4ff !important; border-bottom: 1px solid #00d4ff33 !important; padding-bottom: 10px !important; }
#report-output h2 { color: #e6edf3 !important; border-left: 3px solid #00d4ff !important; padding-left: 12px !important; margin-top: 28px !important; }
#report-output h3 { color: #8b949e !important; font-size: 0.9rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }
#report-output li { color: #c9d1d9 !important; line-height: 1.7 !important; }
#report-output strong { color: #00d4ff !important; }
#report-output table { border-collapse: collapse !important; width: 100% !important; }
#report-output th { background: #0d1117 !important; color: #8b949e !important; padding: 8px 12px !important; font-size: 0.8rem !important; text-transform: uppercase !important; }
#report-output td { border-top: 1px solid #21262d !important; padding: 8px 12px !important; color: #c9d1d9 !important; }

/* History list */
#history-dropdown select, #history-dropdown .wrap {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
}

/* Inputs */
.gr-textbox textarea, .gr-textbox input {
    background: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    border-radius: 6px !important;
}
.gr-textbox textarea:focus, .gr-textbox input:focus {
    border-color: #00d4ff66 !important;
    outline: none !important;
}
label span { color: #8b949e !important; font-size: 0.78rem !important; text-transform: uppercase !important; letter-spacing: 0.06em !important; }

/* Accordion */
.gr-accordion { background: #0d1117 !important; border: 1px solid #30363d !important; border-radius: 6px !important; }
.gr-accordion .label-wrap { color: #8b949e !important; font-size: 0.8rem !important; }

/* Section dividers */
.section-label {
    color: #8b949e;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 12px 0 6px;
    border-top: 1px solid #21262d;
    margin-top: 12px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
"""


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run_pipeline(query=None, manual_text=None, manual_url=None):
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
        return curated_report, filepath, f"Report saved — {filepath.split('/')[-1]}"

    except Exception as e:
        return "", "", f"Error: {e}"


def handle_notebooklm_upload(filepath_state):
    if not filepath_state:
        return "Run a brief first."
    return upload_report(filepath_state)


def refresh_and_load_latest():
    reports = list_reports()
    names = [r["name"] for r in reports]
    dropdown = gr.Dropdown(choices=names, value=names[0] if names else None)
    return dropdown, reports


def load_selected_report(report_name, reports_cache):
    for r in reports_cache:
        if r["name"] == report_name:
            return load_report(r["path"])
    return ""


# ── UI ────────────────────────────────────────────────────────────────────────

def build_ui():
    with gr.Blocks(title="Utility Intelligence Agent") as app:

        filepath_state = gr.State("")
        reports_cache = gr.State([])

        # Header
        gr.HTML("""
        <div id="header">
            <h1>⚡ UTILITY INTELLIGENCE AGENT</h1>
            <p>Utilities &nbsp;·&nbsp; Energy &nbsp;·&nbsp; Critical Infrastructure &nbsp;·&nbsp; Cybersecurity</p>
        </div>
        """)

        with gr.Row(equal_height=True):

            # ── Sidebar ──────────────────────────────────────────────────────
            with gr.Column(scale=1, elem_id="sidebar", min_width=240):

                run_btn = gr.Button(
                    "▶  RUN INTELLIGENCE BRIEF",
                    variant="primary",
                    elem_id="run-btn"
                )
                status_box = gr.Textbox(
                    value="Ready",
                    interactive=False,
                    show_label=False,
                    elem_id="status-box",
                    lines=1
                )

                gr.HTML('<div class="section-label">Send to NotebookLM</div>')
                notebooklm_btn = gr.Button(
                    "◆  Add to NotebookLM",
                    elem_id="notebooklm-btn"
                )
                notebooklm_status = gr.Textbox(
                    interactive=False,
                    show_label=False,
                    lines=1,
                    elem_id="status-box"
                )

                gr.HTML('<div class="section-label">Report History</div>')
                history_dropdown = gr.Dropdown(
                    choices=[],
                    label="",
                    interactive=True,
                    elem_id="history-dropdown"
                )
                load_btn = gr.Button("Load Selected", size="sm", elem_id="manual-run-btn")

                gr.HTML('<div class="section-label">Manual Feed</div>')
                with gr.Accordion("Expand to add content", open=False):
                    manual_url = gr.Textbox(
                        label="URL",
                        placeholder="https://...",
                        lines=1
                    )
                    manual_text = gr.Textbox(
                        label="Paste Content",
                        placeholder="Article text, notes, raw intel...",
                        lines=5
                    )
                    custom_query = gr.Textbox(
                        label="Custom Focus",
                        placeholder="E.g. Focus on OT threats in Ontario...",
                        lines=2
                    )
                    manual_run_btn = gr.Button("Run with Manual Input", elem_id="manual-run-btn")

            # ── Main Report Panel ─────────────────────────────────────────────
            with gr.Column(scale=4, elem_id="main-content"):
                report_output = gr.Markdown(
                    value="> Hit **RUN INTELLIGENCE BRIEF** to generate your first report.",
                    elem_id="report-output"
                )

        # ── Event Handlers ────────────────────────────────────────────────────

        def auto_run():
            yield gr.update(), gr.update(value="Running research agent..."), gr.update(), gr.update()
            report, filepath, status = run_pipeline()
            reports = list_reports()
            names = [r["name"] for r in reports]
            yield (
                gr.update(value=report),
                gr.update(value=status),
                filepath,
                gr.update(choices=names, value=names[0] if names else None)
            )

        def manual_run(text, url, query):
            yield gr.update(), gr.update(value="Running research agent..."), gr.update(), gr.update()
            report, filepath, status = run_pipeline(
                query=query if query and query.strip() else None,
                manual_text=text,
                manual_url=url
            )
            reports = list_reports()
            names = [r["name"] for r in reports]
            yield (
                gr.update(value=report),
                gr.update(value=status),
                filepath,
                gr.update(choices=names, value=names[0] if names else None)
            )

        run_btn.click(
            fn=auto_run,
            outputs=[report_output, status_box, filepath_state, history_dropdown]
        )

        manual_run_btn.click(
            fn=manual_run,
            inputs=[manual_text, manual_url, custom_query],
            outputs=[report_output, status_box, filepath_state, history_dropdown]
        )

        notebooklm_btn.click(
            fn=handle_notebooklm_upload,
            inputs=[filepath_state],
            outputs=[notebooklm_status]
        )

        load_btn.click(
            fn=load_selected_report,
            inputs=[history_dropdown, reports_cache],
            outputs=[report_output]
        )

        # Load history on startup
        app.load(
            fn=refresh_and_load_latest,
            outputs=[history_dropdown, reports_cache]
        )

    return app


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    required = ["ANTHROPIC_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        print("Copy .env.example to .env and fill in your API keys.")
        exit(1)

    app = build_ui()
    app.launch(share=False, server_port=7860, css=CSS)
