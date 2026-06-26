"""Custom Styles Module — modern dark theme for Prompt Pipeline."""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; }
html, body, .stApp { background: #0d0f1a !important; font-family: 'Inter', sans-serif; }

/* ── Hide chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2e3150; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #6c63ff; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #11131f !important;
    border-right: 1px solid #1e2138 !important;
}
.sidebar-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #4b5280;
    margin: 1.25rem 0 0.5rem;
}

/* ── Header ── */
.app-header {
    padding: 1.75rem 0 1.25rem;
    border-bottom: 1px solid #1e2138;
    margin-bottom: 1.5rem;
}
.app-header h1 {
    font-size: 1.75rem;
    font-weight: 700;
    color: #eef0f8;
    margin: 0 0 0.25rem;
    letter-spacing: -0.5px;
}
.app-header p {
    font-size: 0.85rem;
    color: #5a5f80;
    margin: 0;
}
.accent { display: inline; background: linear-gradient(90deg,#6c63ff,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }

/* ── Cards ── */
.card {
    background: #13152a;
    border: 1px solid #1e2138;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.875rem;
    transition: border-color .2s;
}
.card:hover { border-color: #6c63ff44; }
.card-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #5a5f80;
    margin-bottom: 0.5rem;
}
.char-count { font-size: 0.68rem; color: #3d4268; text-align: right; margin-top: 0.25rem; }

/* ── Stage cards ── */
.stage-card {
    background: #13152a;
    border: 1px solid #1e2138;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 0.875rem;
    transition: border-color .2s;
}
.stage-card:hover { border-color: #6c63ff44; }
.stage-card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 1rem 1.25rem;
}
.stage-num {
    width: 30px; height: 30px;
    border-radius: 9px;
    background: linear-gradient(135deg,#6c63ff,#a78bfa);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; font-weight: 700; color: #fff;
    flex-shrink: 0;
}
.stage-meta { flex: 1; min-width: 0; }
.stage-title { font-size: 0.875rem; font-weight: 600; color: #dde0f5; }
.stage-sub { font-size: 0.72rem; color: #4b5280; margin-top: 1px; }
.stage-card-body {
    border-top: 1px solid #1e2138;
    padding: 1rem 1.25rem 1.25rem;
}

/* ── Badges ── */
.badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.65rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.4px;
    flex-shrink: 0;
}
.badge-pending  { background:#1e2138; color:#5a5f80; }
.badge-running  { background:rgba(99,179,237,.12); color:#63b3ed; border:1px solid rgba(99,179,237,.2); }
.badge-success  { background:rgba(72,199,142,.12); color:#48c78e; border:1px solid rgba(72,199,142,.2); }
.badge-error    { background:rgba(252,100,100,.12); color:#fc6464; border:1px solid rgba(252,100,100,.2); }

/* ── Status / result cards ── */
.result-success {
    background: rgba(72,199,142,.07);
    border: 1px solid rgba(72,199,142,.25);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #48c78e;
    font-size: 0.85rem;
    display: flex; align-items: center; gap: 10px;
}
.result-error {
    background: rgba(252,100,100,.07);
    border: 1px solid rgba(252,100,100,.25);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #fc6464;
    font-size: 0.85rem;
    display: flex; align-items: center; gap: 10px;
}

/* ── Pretty JSON ── */
.json-block {
    background: #0a0c18;
    border: 1px solid #1e2138;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    line-height: 1.6;
    overflow-x: auto;
    margin-top: 0.75rem;
    color: #c5cae9;
}
.json-key   { color: #a78bfa; }
.json-str   { color: #79e3b1; }
.json-num   { color: #f9c74f; }
.json-bool  { color: #63b3ed; }
.json-null  { color: #fc6464; }

/* ── Markdown output ── */
.md-output { font-size: 0.875rem; color: #c5cae9; line-height: 1.7; }
.md-output h1,.md-output h2,.md-output h3 { color:#dde0f5; font-weight:600; margin:.75rem 0 .35rem; }
.md-output code { background:#0a0c18; border:1px solid #1e2138; border-radius:5px; padding:1px 6px; font-family:'JetBrains Mono',monospace; font-size:.8em; color:#a78bfa; }
.md-output pre  { background:#0a0c18; border:1px solid #1e2138; border-radius:10px; padding:.875rem 1rem; overflow-x:auto; }
.md-output pre code { background:none; border:none; padding:0; color:#79e3b1; }
.md-output blockquote { border-left:3px solid #6c63ff; margin:0; padding:.5rem 1rem; color:#7b80a0; }
.md-output table { width:100%; border-collapse:collapse; font-size:.82rem; }
.md-output th  { background:#1e2138; color:#8b8fb5; font-weight:600; padding:.5rem .75rem; text-align:left; }
.md-output td  { border-top:1px solid #1e2138; padding:.45rem .75rem; color:#b0b5d8; }

/* ── Progress bar ── */
.pipeline-progress {
    background: #1e2138;
    border-radius: 20px;
    height: 6px;
    overflow: hidden;
    margin: 0.75rem 0 1.25rem;
}
.pipeline-progress-fill {
    height: 100%;
    border-radius: 20px;
    background: linear-gradient(90deg, #6c63ff, #a78bfa);
    transition: width .4s ease;
}

/* ── Stats bar ── */
.stats-bar {
    display: flex; align-items: center; gap: 1.5rem;
    background: #13152a;
    border: 1px solid #1e2138;
    border-radius: 14px;
    padding: .875rem 1.25rem;
    margin-top: 1.25rem;
    flex-wrap: wrap;
}
.stat-item { display:flex; align-items:center; gap:8px; }
.stat-icon { font-size: 1.1rem; }
.stat-label { font-size:.65rem; font-weight:600; letter-spacing:.8px; text-transform:uppercase; color:#4b5280; }
.stat-value { font-size:.875rem; font-weight:600; color:#dde0f5; }
.stat-divider { width:1px; height:24px; background:#1e2138; }

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #0a0c18 !important;
    border: 1px solid #1e2138 !important;
    border-radius: 9px !important;
    color: #c5cae9 !important;
    font-size: 0.83rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #6c63ff !important;
    box-shadow: 0 0 0 2px rgba(108,99,255,.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 9px !important;
    font-weight: 500 !important;
    font-size: 0.83rem !important;
    transition: all .18s ease !important;
}
.stButton > button[kind="secondary"] {
    background: #1e2138 !important;
    color: #8b8fb5 !important;
    border: 1px solid #2a2d4a !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #252845 !important;
    border-color: #6c63ff !important;
    color: #dde0f5 !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg,#6c63ff,#a78bfa) !important;
    color: #fff !important;
    border: none !important;
    box-shadow: 0 4px 14px rgba(108,99,255,.35) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(108,99,255,.5) !important;
    transform: translateY(-1px);
}
.stButton > button:disabled {
    opacity: .4 !important;
    cursor: not-allowed !important;
}

/* ── Selectbox ── */
.stSelectbox [data-baseweb="select"] > div {
    background: #0a0c18 !important;
    border-color: #1e2138 !important;
    border-radius: 9px !important;
    color: #c5cae9 !important;
}

/* ── Expanders ── */
details summary {
    background: #13152a !important;
    border: 1px solid #1e2138 !important;
    border-radius: 10px !important;
    padding: .6rem 1rem !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    background: #1e2138 !important;
    border: 1px solid #2a2d4a !important;
    color: #8b8fb5 !important;
    border-radius: 9px !important;
    font-size: .82rem !important;
}
.stDownloadButton > button:hover {
    border-color: #6c63ff !important;
    color: #dde0f5 !important;
}

/* ── Spinner override ── */
.stSpinner > div { border-top-color: #6c63ff !important; }
</style>
"""


def apply_custom_styles() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def get_custom_css() -> str:
    return _CSS


def badge(status: str) -> str:
    """Return an HTML badge for the given status string."""
    labels = {
        "pending": ("⬜", "PENDING", "badge-pending"),
        "running": ("⟳", "RUNNING", "badge-running"),
        "complete": ("✓", "SUCCESS", "badge-success"),
        "success":  ("✓", "SUCCESS", "badge-success"),
        "error":    ("✕", "ERROR",   "badge-error"),
    }
    icon, text, cls = labels.get(status, ("·", status.upper(), "badge-pending"))
    return f'<span class="badge {cls}">{icon} {text}</span>'


# Keep old name for backward compat
def style_status_badge(status: str) -> str:
    return badge(status)
