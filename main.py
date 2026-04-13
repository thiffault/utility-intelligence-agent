import os
from dotenv import load_dotenv
import gradio as gr

load_dotenv()

from agents.research_agent import run_research
from agents.curation_agent import run_curation
from utils.formatter import save_report, list_reports, load_report
from utils.notebooklm import upload_report, is_configured


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
/* ── Reset & Base ── */
body, .gradio-container {
    background-color: #0a0e17 !important;
    color: #dce3ed !important;
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
}
.gradio-container { max-width: 100% !important; padding: 0 !important; }
footer { display: none !important; }

/* ── Header ── */
#app-header {
    background: #0d1220;
    border-bottom: 1px solid #1e2d45;
    padding: 18px 32px;
    display: flex;
    align-items: center;
    gap: 14px;
}
#app-header .title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
#app-header .subtitle {
    font-size: 0.72rem;
    color: #4a6080;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 2px;
}
#app-header .badge {
    background: #0f3460;
    border: 1px solid #1a4a80;
    color: #5b9bd5;
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    padding: 3px 10px;
    border-radius: 3px;
    text-transform: uppercase;
    font-weight: 600;
}

/* ── Layout ── */
#sidebar {
    background: #0d1220;
    border-right: 1px solid #1e2d45;
    padding: 24px 18px;
    min-height: calc(100vh - 65px);
}
#main-panel {
    background: #0a0e17;
    padding: 28px 36px;
}

/* ── Buttons ── */
.btn-primary {
    background: #0f3460 !important;
    color: #7ab8e8 !important;
    border: 1px solid #1a4a80 !important;
    border-radius: 4px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 12px 16px !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
    cursor: pointer !important;
}
.btn-primary:hover {
    background: #143d70 !important;
    border-color: #2a6aaa !important;
    color: #a8d0f0 !important;
    box-shadow: 0 0 12px #0f346044 !important;
}

.btn-green {
    background: #0d2218 !important;
    color: #4ade80 !important;
    border: 1px solid #1a4a2e !important;
    border-radius: 4px !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 16px !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}
.btn-green:hover {
    background: #122e1f !important;
    border-color: #2a6a44 !important;
    box-shadow: 0 0 10px #4ade8022 !important;
}

.btn-ghost {
    background: transparent !important;
    color: #4a6080 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 4px !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    padding: 8px 14px !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}
.btn-ghost:hover {
    background: #0d1220 !important;
    color: #7a9abf !important;
    border-color: #2a3d55 !important;
}

/* ── Status ── */
.status-box textarea {
    background: #080c14 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 4px !important;
    color: #4a6080 !important;
    font-size: 0.72rem !important;
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    padding: 7px 12px !important;
    resize: none !important;
}

/* ── Inputs ── */
textarea, input[type=text] {
    background: #080c14 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 4px !important;
    color: #c0cedd !important;
    font-size: 0.82rem !important;
    transition: border-color 0.15s !important;
}
textarea:focus, input[type=text]:focus {
    border-color: #2a5080 !important;
    outline: none !important;
}
label > span {
    color: #4a6080 !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* ── Dropdown ── */
.gr-dropdown select, .wrap-inner {
    background: #080c14 !important;
    border: 1px solid #1e2d45 !important;
    color: #c0cedd !important;
    border-radius: 4px !important;
    font-size: 0.78rem !important;
}

/* ── Accordion ── */
.gr-accordion {
    background: #080c14 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 4px !important;
    margin-top: 4px !important;
}
.gr-accordion .label-wrap span {
    color: #4a6080 !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
}

/* ── Section Labels ── */
.section-label {
    color: #2e4460;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    padding: 16px 0 8px;
    border-top: 1px solid #1a2535;
    margin-top: 8px;
}

/* ── Report Output ── */
#report-output .prose {
    color: #c8d6e5 !important;
    line-height: 1.75 !important;
}
#report-output h1 {
    font-size: 1.1rem !important;
    color: #dce3ed !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    border-bottom: 1px solid #1e2d45 !important;
    padding-bottom: 12px !important;
    margin-bottom: 20px !important;
}
#report-output h2 {
    font-size: 0.9rem !important;
    color: #7ab8e8 !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-left: 2px solid #1a4a80 !important;
    padding-left: 12px !important;
    margin-top: 32px !important;
    margin-bottom: 12px !important;
}
#report-output h3 {
    font-size: 0.78rem !important;
    color: #4a6080 !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    margin-top: 18px !important;
}
#report-output li {
    color: #a8bdd0 !important;
    line-height: 1.8 !important;
    font-size: 0.88rem !important;
}
#report-output p { color: #a8bdd0 !important; font-size: 0.88rem !important; }
#report-output strong { color: #c8d6e5 !important; }
#report-output table { width: 100% !important; border-collapse: collapse !important; margin: 16px 0 !important; }
#report-output th {
    background: #0d1220 !important;
    color: #4a6080 !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 8px 14px !important;
    text-align: left !important;
    border-bottom: 1px solid #1e2d45 !important;
}
#report-output td {
    padding: 8px 14px !important;
    border-bottom: 1px solid #121825 !important;
    color: #a8bdd0 !important;
    font-size: 0.85rem !important;
}
#report-output blockquote {
    border-left: 2px solid #1a4a80 !important;
    margin: 0 !important;
    padding: 8px 16px !important;
    background: #0d1220 !important;
    border-radius: 0 4px 4px 0 !important;
}

/* ── Sources Panel ── */
.sources-panel {
    margin-top: 24px;
    border: 1px solid #1e2d45;
    border-radius: 4px;
    overflow: hidden;
    background: #080c14;
}
.sources-toggle {
    background: #0d1220;
    border: none;
    width: 100%;
    text-align: left;
    padding: 10px 16px;
    color: #4a6080;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1e2d45;
}
.sources-list {
    padding: 12px 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.source-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 6px 0;
    border-bottom: 1px solid #121825;
}
.source-item:last-child { border-bottom: none; }
.source-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: #1a4a80;
    margin-top: 6px;
    flex-shrink: 0;
}
.source-link {
    color: #5b9bd5 !important;
    font-size: 0.78rem !important;
    text-decoration: none !important;
    line-height: 1.5;
    word-break: break-all;
}
.source-link:hover { color: #7ab8e8 !important; text-decoration: underline !important; }
.source-title {
    color: #4a6080;
    font-size: 0.68rem;
    margin-top: 1px;
}
.sources-empty {
    color: #2e4460;
    font-size: 0.75rem;
    padding: 12px 0;
    text-align: center;
    font-style: italic;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #080c14; }
::-webkit-scrollbar-thumb { background: #1e2d45; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2a3d55; }
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _build_sources_html(sources: list[dict]) -> str:
    if not sources:
        return """
        <div class="sources-panel">
            <div class="sources-toggle">
                <span>Sources</span><span>0</span>
            </div>
            <div class="sources-list">
                <div class="sources-empty">No sources captured for this report.</div>
            </div>
        </div>"""

    items = ""
    for s in sources:
        title = s["title"] if s["title"] != s["url"] else ""
        title_html = f'<div class="source-title">{title}</div>' if title else ""
        items += f"""
        <div class="source-item">
            <div class="source-dot"></div>
            <div>
                <a class="source-link" href="{s['url']}" target="_blank" rel="noopener">{s['url']}</a>
                {title_html}
            </div>
        </div>"""

    return f"""
    <div class="sources-panel">
        <details>
            <summary class="sources-toggle">
                <span>Sources &amp; References</span>
                <span style="color:#2e4460">{len(sources)} links</span>
            </summary>
            <div class="sources-list">{items}</div>
        </details>
    </div>"""


# ── Pipeline ─────────────────────────────────────────────────────────────────

def run_pipeline(query=None, manual_text=None, manual_url=None):
    """Returns (report, sources_html, filepath, status)."""
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
                return "", "", "", f"Failed to fetch URL: {e}"

        research_output, sources = run_research(query=query or None, manual_content=manual_content)
        curated_report = run_curation(research_output)
        filepath = save_report(curated_report)
        sources_html = _build_sources_html(sources)

        return curated_report, sources_html, filepath, f"Saved — {filepath.split('/')[-1]}"

    except Exception as e:
        return "", "", "", f"Error: {e}"


def handle_notebooklm_upload(filepath_state):
    if not filepath_state:
        return "Run a brief first."
    return upload_report(filepath_state)


def refresh_history():
    reports = list_reports()
    names = [r["name"] for r in reports]
    return gr.Dropdown(choices=names, value=names[0] if names else None), reports


def load_selected_report(report_name, reports_cache):
    for r in reports_cache:
        if r["name"] == report_name:
            return load_report(r["path"]), ""
    return "", ""


# ── UI ────────────────────────────────────────────────────────────────────────

def build_ui():
    with gr.Blocks(title="Utility Intelligence Agent") as app:

        filepath_state = gr.State("")
        reports_cache = gr.State([])

        # Header
        gr.HTML("""
        <div id="app-header">
            <div style="width:32px;height:32px;background:#0f3460;border:1px solid #1a4a80;
                        border-radius:4px;display:flex;align-items:center;justify-content:center;
                        font-size:1rem;">⚡</div>
            <div>
                <div class="title">Utility Intelligence Agent</div>
                <div class="subtitle">Utilities &nbsp;·&nbsp; Energy &nbsp;·&nbsp; Critical Infrastructure &nbsp;·&nbsp; Cybersecurity</div>
            </div>
            <div style="margin-left:auto">
                <span class="badge">Powered by Claude</span>
            </div>
        </div>
        """)

        with gr.Row(equal_height=False):

            # ── Sidebar ──────────────────────────────────────────────────────
            with gr.Column(scale=1, elem_id="sidebar", min_width=230):

                run_btn = gr.Button(
                    "▶  Run Intelligence Brief",
                    elem_classes=["btn-primary"]
                )
                status_box = gr.Textbox(
                    value="Ready",
                    interactive=False,
                    show_label=False,
                    elem_classes=["status-box"],
                    lines=1
                )

                gr.HTML('<div class="section-label">Notebook</div>')
                notebooklm_btn = gr.Button(
                    "◆  Add to NotebookLM",
                    elem_classes=["btn-green"]
                )
                notebooklm_status = gr.Textbox(
                    interactive=False,
                    show_label=False,
                    elem_classes=["status-box"],
                    lines=1
                )

                gr.HTML('<div class="section-label">History</div>')
                history_dropdown = gr.Dropdown(
                    choices=[],
                    label="",
                    interactive=True,
                    show_label=False
                )
                load_btn = gr.Button(
                    "Load Selected Report",
                    elem_classes=["btn-ghost"]
                )

                gr.HTML('<div class="section-label">Manual Feed</div>')
                with gr.Accordion("Add custom content or URL", open=False):
                    manual_url_input = gr.Textbox(
                        label="URL",
                        placeholder="https://...",
                        lines=1
                    )
                    manual_text_input = gr.Textbox(
                        label="Paste Content",
                        placeholder="Articles, reports, raw intel...",
                        lines=4
                    )
                    custom_query_input = gr.Textbox(
                        label="Custom Focus",
                        placeholder="E.g. Focus on OT threats in Ontario...",
                        lines=2
                    )
                    manual_run_btn = gr.Button(
                        "Run with Manual Input",
                        elem_classes=["btn-primary"]
                    )

            # ── Main Panel ────────────────────────────────────────────────────
            with gr.Column(scale=4, elem_id="main-panel"):
                report_output = gr.Markdown(
                    value="> Hit **Run Intelligence Brief** to generate your first report.",
                    elem_id="report-output"
                )
                sources_output = gr.HTML(value="")

        # ── Handlers ─────────────────────────────────────────────────────────

        def auto_run():
            yield (
                gr.update(value="> Researching..."),
                gr.update(value=""),
                gr.update(value="Running research agent..."),
                gr.update(),
                gr.update()
            )
            report, sources_html, filepath, status = run_pipeline()
            reports = list_reports()
            names = [r["name"] for r in reports]
            yield (
                gr.update(value=report),
                gr.update(value=sources_html),
                gr.update(value=status),
                filepath,
                gr.update(choices=names, value=names[0] if names else None)
            )

        def manual_run(text, url, query):
            yield (
                gr.update(value="> Researching..."),
                gr.update(value=""),
                gr.update(value="Running research agent..."),
                gr.update(),
                gr.update()
            )
            report, sources_html, filepath, status = run_pipeline(
                query=query if query and query.strip() else None,
                manual_text=text,
                manual_url=url
            )
            reports = list_reports()
            names = [r["name"] for r in reports]
            yield (
                gr.update(value=report),
                gr.update(value=sources_html),
                gr.update(value=status),
                filepath,
                gr.update(choices=names, value=names[0] if names else None)
            )

        run_btn.click(
            fn=auto_run,
            outputs=[report_output, sources_output, status_box, filepath_state, history_dropdown]
        )

        manual_run_btn.click(
            fn=manual_run,
            inputs=[manual_text_input, manual_url_input, custom_query_input],
            outputs=[report_output, sources_output, status_box, filepath_state, history_dropdown]
        )

        notebooklm_btn.click(
            fn=handle_notebooklm_upload,
            inputs=[filepath_state],
            outputs=[notebooklm_status]
        )

        load_btn.click(
            fn=load_selected_report,
            inputs=[history_dropdown, reports_cache],
            outputs=[report_output, sources_output]
        )

        app.load(
            fn=refresh_history,
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
