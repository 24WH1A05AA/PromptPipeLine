"""
app.py — Streamlit frontend for Prompt Pipeline.

Transforms raw bug reports into structured developer reports through
a 3-stage LLM prompt chain (Understand → Analyze → Generate).
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st

from pipeline import run_pipeline, run_preset_pipeline
from presets import list_presets, get_input_fields, get_stage_metadata
from styles import apply_custom_styles, badge
from llm import AuthenticationError, LLMError, NetworkError, RateLimitError
from llm import TimeoutError as LLMTimeoutError
from stage1 import Stage1ValidationError
from stage2 import Stage2ValidationError
from stage3 import Stage3ValidationError

# ── Page config (must be first Streamlit call) ──
st.set_page_config(page_title="Prompt Pipeline", page_icon="🧠", layout="wide")
apply_custom_styles()

# ── Constants ──

MODELS: list[str] = [
    "openai/gpt-4o-mini",                # recommended — fast & cheap
    "google/gemma-4-31b-it:free",        # free tier — Gemma 4 31B
    "openai/gpt-4o",
    "openai/gpt-3.5-turbo",
    "anthropic/claude-3-haiku",
    "anthropic/claude-3-sonnet",
    "google/gemini-pro",
    "mistralai/mistral-large",
]

# Three distinct sample bug reports covering different error categories
SAMPLES: list[Dict[str, str]] = [
    {
        "label": "🔤 Unicode Encode Error",
        "bug": (
            "When saving a file with a Unicode filename (e.g. résumé.pdf) the application "
            "crashes with a UnicodeEncodeError. Happens on Windows 10 inside the 'Save As' "
            "dialog when the file writing module tries to encode the filename."
        ),
        "trace": (
            "Traceback (most recent call last):\n"
            "  File \"app.py\", line 142, in save_file\n"
            "    with open(filename, 'w') as f:\n"
            "  File \"encodings/cp1252.py\", line 19, in encode\n"
            "UnicodeEncodeError: 'charmap' codec can't encode character '\\xe9' "
            "in position 5: character maps to <undefined>"
        ),
        "env": "OS: Windows 10 Pro 22H2 | Python 3.11.4 | Default encoding: cp1252",
    },
    {
        "label": "🗄️ Database Connection Timeout",
        "bug": (
            "The application intermittently raises a sqlalchemy.exc.OperationalError "
            "during peak traffic hours when acquiring a database connection. The error "
            "suggests the connection pool is exhausted. Users see a 500 error page."
        ),
        "trace": (
            "Traceback (most recent call last):\n"
            "  File \"api/routes.py\", line 88, in get_user\n"
            "    session = db.get_session()\n"
            "  File \"db/pool.py\", line 34, in get_session\n"
            "    return engine.connect()\n"
            "sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) "
            "FATAL: remaining connection slots are reserved for non-replication "
            "superuser connections"
        ),
        "env": (
            "OS: Ubuntu 22.04 | Python 3.11.2 | SQLAlchemy 2.0.20 | "
            "PostgreSQL 15.3 | pool_size=5 | max_overflow=10"
        ),
    },
    {
        "label": "🔑 JWT Token KeyError",
        "bug": (
            "After deploying the new auth middleware, all authenticated API requests "
            "return HTTP 500. The error occurs when the JWT decoder tries to read the "
            "'sub' claim from the token payload. Tokens issued before the deployment "
            "work fine; only newly issued tokens are affected."
        ),
        "trace": (
            "Traceback (most recent call last):\n"
            "  File \"middleware/auth.py\", line 57, in verify_token\n"
            "    user_id = payload['sub']\n"
            "KeyError: 'sub'\n\n"
            "During handling of the above exception, another exception occurred:\n"
            "  File \"middleware/auth.py\", line 62, in verify_token\n"
            "    raise AuthError('Invalid token claims', 401)"
        ),
        "env": (
            "OS: Ubuntu 22.04 | Python 3.11.5 | PyJWT 2.8.0 | "
            "FastAPI 0.103.1 | Deployed: 2024-01-15"
        ),
    },
]


# ── Session state ──

def _init_state() -> None:
    """Initialise all session-state keys with safe defaults."""
    defaults: Dict[str, Any] = {
        "preset":    "bug_triage",
        "field_1":   "",
        "field_2":   "",
        "field_3":   "",
        "model":     MODELS[0],
        "results":   None,
        "status":    "idle",
        "error_msg": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── HTML helpers ──

def _colorize_json(obj: Any, depth: int = 0) -> str:
    """Recursively produce syntax-highlighted JSON HTML (no external deps)."""
    pad = "&nbsp;" * (depth * 2)
    inner = "&nbsp;" * ((depth + 1) * 2)

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        rows = [
            f"{inner}<span class='json-key'>\"{k}\"</span>: {_colorize_json(v, depth+1)}"
            for k, v in obj.items()
        ]
        return "{\n" + ",\n".join(rows) + f"\n{pad}}}"
    if isinstance(obj, list):
        if not obj:
            return "[]"
        rows = [f"{inner}{_colorize_json(v, depth+1)}" for v in obj]
        return "[\n" + ",\n".join(rows) + f"\n{pad}]"
    if isinstance(obj, bool):
        return f"<span class='json-bool'>{'true' if obj else 'false'}</span>"
    if obj is None:
        return "<span class='json-null'>null</span>"
    if isinstance(obj, (int, float)):
        return f"<span class='json-num'>{obj}</span>"
    escaped = str(obj).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<span class='json-str'>\"{escaped}\"</span>"


def _json_block(data: Dict[str, Any]) -> str:
    return f'<div class="json-block">{_colorize_json(data)}</div>'


def _progress_bar(pct: int) -> str:
    return (
        f'<div class="pipeline-progress">'
        f'<div class="pipeline-progress-fill" style="width:{pct}%"></div>'
        f'</div>'
    )


def _has_long_text(data: Dict[str, Any]) -> bool:
    return any(isinstance(v, str) and len(v) > 120 for v in data.values())


# ── Sidebar ──

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div style="font-size:1.15rem;font-weight:700;color:#eef0f8;margin-bottom:.2rem;">'
            '🧠 Prompt Pipeline</div>'
            '<div style="font-size:.72rem;color:#4b5280;margin-bottom:1.25rem;">'
            'Multi-stage AI Bug Analysis</div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-label">Model</div>', unsafe_allow_html=True)
        st.session_state.model = st.selectbox(
            "model", MODELS,
            index=MODELS.index(st.session_state.model)
                  if st.session_state.model in MODELS else 0,
            label_visibility="collapsed",
        )

        st.markdown('<div class="sidebar-label">Pipeline Stages</div>', unsafe_allow_html=True)
        for num, title, tech in [
            ("1", "Understand & Extract", "Role Prompting"),
            ("2", "Analyze & Reason",    "Chain-of-Thought"),
            ("3", "Generate Report",     "Goal-Oriented Prompting"),
        ]:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:.45rem 0;'
                f'border-bottom:1px solid #1e2138;">'
                f'<div class="stage-num" style="width:22px;height:22px;font-size:.65rem;">{num}</div>'
                f'<div><div style="font-size:.78rem;font-weight:600;color:#c5cae9;">{title}</div>'
                f'<div style="font-size:.65rem;color:#4b5280;">{tech}</div></div></div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="sidebar-label" style="margin-top:1.25rem;">Pipeline Status</div>',
                    unsafe_allow_html=True)
        dot = {"idle": "#4b5280", "running": "#63b3ed",
               "success": "#48c78e", "error": "#fc6464"}.get(st.session_state.status, "#4b5280")
        label = {"idle": "Idle — awaiting input", "running": "Running…",
                 "success": "Complete", "error": "Failed"}.get(st.session_state.status, "—")
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;font-size:.8rem;color:{dot};">'
            f'<div style="width:8px;height:8px;border-radius:50%;background:{dot};'
            f'box-shadow:0 0 6px {dot};"></div>{label}</div>',
            unsafe_allow_html=True,
        )


# ── Stage output card ──

def _render_stage(
    num: int,
    title: str,
    technique: str,
    data: Optional[Dict[str, Any]],
    status: str,
) -> None:
    """Render a single stage result card with badge, JSON viewer, and markdown fields."""
    bdg = badge(status)
    st.markdown(
        f'<div class="stage-card">'
        f'<div class="stage-card-header">'
        f'<div class="stage-num">{num}</div>'
        f'<div class="stage-meta">'
        f'<div class="stage-title">Stage {num} — {title}</div>'
        f'<div class="stage-sub">{technique}</div></div>'
        f'{bdg}</div>'
        # Inline JSON for short-value dicts
        + (_json_block(data) if data and not _has_long_text(data) else "")
        + '</div>',
        unsafe_allow_html=True,
    )

    # Long text fields rendered as native Streamlit markdown
    if data and _has_long_text(data):
        meta = {k: v for k, v in data.items() if not (isinstance(v, str) and len(v) > 120)}
        long_fields = {k: v for k, v in data.items() if isinstance(v, str) and len(v) > 120}

        if meta:
            st.markdown(_json_block(meta), unsafe_allow_html=True)
        for key, val in long_fields.items():
            st.markdown(
                f'<div class="card-label" style="margin:.75rem 0 .35rem;">{key}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(val)  # native markdown rendering


# ── Execution summary ──

def _render_summary(results: Dict[str, Any]) -> None:
    """Render the execution summary stats bar and download button."""
    elapsed = results.get("execution_time", "—")
    model_short = st.session_state.model.split("/")[-1]
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    st.markdown(
        f'<div class="stats-bar">'
        f'<div class="stat-item"><span class="stat-icon">⏱</span>'
        f'<div><div class="stat-label">Execution Time</div>'
        f'<div class="stat-value">{elapsed}s</div></div></div>'
        f'<div class="stat-divider"></div>'
        f'<div class="stat-item"><span class="stat-icon">✅</span>'
        f'<div><div class="stat-label">Stages</div>'
        f'<div class="stat-value">3 / 3 complete</div></div></div>'
        f'<div class="stat-divider"></div>'
        f'<div class="stat-item"><span class="stat-icon">🤖</span>'
        f'<div><div class="stat-label">Model</div>'
        f'<div class="stat-value" style="font-size:.75rem;">{model_short}</div></div></div>'
        f'<div class="stat-divider"></div>'
        f'<div class="stat-item"><span class="stat-icon">🕐</span>'
        f'<div><div class="stat-label">Timestamp</div>'
        f'<div class="stat-value" style="font-size:.72rem;">{ts}</div></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Download report
    report = {
        "metadata": {
            "preset":         st.session_state.preset,
            "model":          st.session_state.model,
            "execution_time": elapsed,
            "timestamp":      datetime.utcnow().isoformat(),
        },
        "input": {
            "field_1": st.session_state.field_1,
            "field_2": st.session_state.field_2,
            "field_3": st.session_state.field_3,
        },
        "stage1": results.get("stage1", {}),
        "stage2": results.get("stage2", {}),
        "stage3": results.get("stage3", {}),
    }
    filename = f"pipeline_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button(
        label="📥 Download Full Report (JSON)",
        data=json.dumps(report, indent=2),
        file_name=filename,
        mime="application/json",
        use_container_width=True,
        help="Download the complete pipeline output including all three stage results.",
    )


# ── Pipeline execution ──

_PIPELINE_ERRORS = (
    Stage1ValidationError, Stage2ValidationError, Stage3ValidationError,
    AuthenticationError, RateLimitError, LLMTimeoutError, NetworkError, LLMError,
)

# Maps exception type to a user-friendly prefix for the error card
_ERROR_LABELS: Dict[type, str] = {
    AuthenticationError: "🔑 Authentication failed",
    RateLimitError:      "⏳ Rate limit exceeded",
    LLMTimeoutError:     "⌛ Request timed out",
    NetworkError:        "🌐 Network error",
    Stage1ValidationError: "⚠️ Stage 1 validation failed",
    Stage2ValidationError: "⚠️ Stage 2 validation failed",
    Stage3ValidationError: "⚠️ Stage 3 validation failed",
    LLMError:            "❌ LLM error",
}


def _execute_pipeline() -> None:
    """Run the pipeline, storing results or an error message in session state."""
    st.session_state.status = "running"
    st.session_state.results = None
    st.session_state.error_msg = ""

    preset_key = st.session_state.preset

    try:
        if preset_key == "bug_triage":
            # Use the original specialised pipeline for bug triage
            results = run_pipeline(
                bug_report=st.session_state.field_1,
                stack_trace=st.session_state.field_2,
                environment=st.session_state.field_3,
                model=st.session_state.model,
            )
        else:
            # Use the generic preset-based runner
            field_values = {
                "field_1": st.session_state.field_1,
                "field_2": st.session_state.field_2,
                "field_3": st.session_state.field_3,
            }
            results = run_preset_pipeline(
                preset_key=preset_key,
                field_values=field_values,
                model=st.session_state.model,
            )
        st.session_state.results = results
        st.session_state.status = "success"

    except _PIPELINE_ERRORS as exc:
        label = _ERROR_LABELS.get(type(exc), "❌ Pipeline error")
        st.session_state.error_msg = f"{label}: {exc}"
        st.session_state.status = "error"

    except Exception as exc:
        st.session_state.error_msg = f"❌ Unexpected error: {exc}"
        st.session_state.status = "error"


# ── Main ──

def main() -> None:
    _init_state()
    _render_sidebar()

    # Header
    st.markdown(
        '<div class="app-header">'
        '<h1>🧠 <span class="accent">Prompt Pipeline</span></h1>'
        '<p>Chain specialised AI prompts to analyse, reason, and generate '
        'structured outputs — choose a pipeline below.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Preset selector ──
    presets_list = list_presets()
    preset_options = {p["label"]: p["key"] for p in presets_list}
    current_label = next(
        (p["label"] for p in presets_list if p["key"] == st.session_state.preset),
        presets_list[0]["label"],
    )
    chosen_label = st.selectbox(
        "Pipeline Preset",
        options=list(preset_options.keys()),
        index=list(preset_options.keys()).index(current_label),
        label_visibility="collapsed",
    )
    new_preset = preset_options[chosen_label]
    if new_preset != st.session_state.preset:
        st.session_state.preset = new_preset
        st.session_state.field_1 = ""
        st.session_state.field_2 = ""
        st.session_state.field_3 = ""
        st.session_state.results = None
        st.session_state.status = "idle"
        st.rerun()

    # Show preset description
    current_preset_info = next(p for p in presets_list if p["key"] == st.session_state.preset)
    st.markdown(
        f'<div style="color:#8b8fa3;font-size:.85rem;margin-bottom:1rem;">'
        f'{current_preset_info["icon"]} {current_preset_info["description"]}</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([5, 7], gap="large")

    # ── Left column: dynamic inputs ──
    with left:
        fields = get_input_fields(st.session_state.preset)
        for fld in fields:
            key = fld["key"]
            st.markdown(f'<div class="card-label">{fld["label"]}</div>', unsafe_allow_html=True)
            val = st.text_area(
                key,
                value=st.session_state.get(key, ""),
                placeholder=fld["placeholder"],
                height=fld["height"],
                label_visibility="collapsed",
            )
            st.session_state[key] = val
            st.markdown(f'<div class="char-count">{len(val)} chars</div>', unsafe_allow_html=True)

        # Action buttons
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("🗑 Clear", use_container_width=True):
                for fld in fields:
                    st.session_state[fld["key"]] = ""
                st.session_state.results = None
                st.session_state.status = "idle"
                st.rerun()
        with c2:
            can_run = all(
                st.session_state.get(fld["key"], "").strip()
                for fld in fields
            )
            if st.button("▶ Run Pipeline", type="primary",
                         use_container_width=True, disabled=not can_run):
                with st.spinner("Running pipeline — this may take 10–30 seconds…"):
                    _execute_pipeline()
                st.rerun()

        if not can_run:
            st.caption("⚠️ Fill in all input fields to enable the pipeline.")

    # ── Right column: outputs ──
    with right:
        status  = st.session_state.status
        results = st.session_state.results

        pct = {"success": 100, "error": 0, "running": 50}.get(status, 0)
        st.markdown(_progress_bar(pct), unsafe_allow_html=True)

        if status == "success" and results:
            t = results.get("execution_time", "—")
            st.markdown(
                f'<div class="result-success">✅ &nbsp;'
                f'<strong>All 3 stages completed successfully</strong> '
                f'— pipeline finished in <strong>{t}s</strong></div>',
                unsafe_allow_html=True,
            )
        elif status == "error":
            st.markdown(
                f'<div class="result-error">❌ &nbsp;{st.session_state.error_msg}</div>',
                unsafe_allow_html=True,
            )
        elif status == "idle":
            st.markdown(
                '<div style="color:#4b5280;font-size:.83rem;padding:.5rem 0;">'
                'Stage results will appear here after you run the pipeline.</div>',
                unsafe_allow_html=True,
            )

        # Dynamic stage metadata from preset
        stage_meta = get_stage_metadata(st.session_state.preset)
        for sm in stage_meta:
            num = int(sm["num"])
            key = f"stage{num}"
            data = results.get(key) if results else None
            if status == "idle":
                s = "pending"
            elif status == "error" and not data:
                s = "error"
            elif data:
                s = "complete"
            else:
                s = "pending"
            _render_stage(num, sm["title"], sm["technique"], data, s)

        if status == "success" and results:
            _render_summary(results)


if __name__ == "__main__":
    main()
