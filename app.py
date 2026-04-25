"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          LINKEDIN OPTIMIZATION ENGINE — Powered by Gemini AI + SDXL        ║
║  Full-stack Streamlit app for professional LinkedIn growth & content        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Modules:
  - Post Generator     : Gemini-powered viral post creation with frameworks
  - Post Optimizer     : Diagnosis + rewrite with engagement score
  - About Optimizer    : Personal brand story + keyword optimization
  - Profile Enhancer   : Beginner → PRO score and 30-day roadmap
  - Content Ideas      : Full content calendar by niche/pillar
  - Strategy Insights  : Top creator tactics and growth playbooks
  - Image Generator    : Stability AI (primary) + Hugging Face (fallback)
  - Engagement Toolkit : Hooks, CTAs, hashtags, posting times
  ── v2.0 ADDITIONS ──────────────────────────────────────────────────────────
  - 🔥 Viral Hook Analyzer : Score, diagnose & rewrite hooks — 5 power rewrites
                             + live mobile feed preview (LinkedIn's #1 growth lever)
  - 📚 Post Library        : Auto-saved post history — search, star, filter, export

Author : LinkedIn Optimization Engine
Stack  : Python · Streamlit · Gemini 2.5 Flash · Stability AI · Hugging Face
Version: 2.0 — Production-Ready
"""

import streamlit as st
import sys
import os
import importlib.util
import json
import re
import time
import traceback
from datetime import datetime

# ── Resolve app directory (works locally & on Streamlit Cloud) ─────────────
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Ensure core/ is importable regardless of working directory ──────────────
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# ── Core modules (graceful fallback so app.py still imports even if missing) ─
try:
    from core import db as _db          # DB persistence
    from core import ai as _ai          # Central AI client
    from core import state as _state    # State helpers
    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# MODULE LOADER — dict-based cache so each .py file is compiled exactly once
# per server process.  Using a plain dict instead of @st.cache_resource avoids
# the crash that happens when cache_resource is called before Streamlit's
# runtime is fully initialised (i.e. at module-import time).
# ─────────────────────────────────────────────────────────────────────────────
_MODULE_CACHE: dict = {}


def load_module(module_name: str, relative_path: str):
    """
    Load a Python module from *relative_path* (relative to APP_DIR).
    The result is cached in _MODULE_CACHE so subsequent calls are free.
    Raises FileNotFoundError if the file does not exist.
    """
    if module_name in _MODULE_CACHE:
        return _MODULE_CACHE[module_name]

    abs_path = os.path.join(APP_DIR, relative_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(
            f"Module file not found: {relative_path}\n"
            f"Expected at: {abs_path}"
        )

    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    _MODULE_CACHE[module_name] = mod
    return mod


def _prewarm_utils() -> None:
    """
    Eagerly load shared utility modules so sub-modules can `import` them.
    Called inside main() — i.e. during a live Streamlit request, never at
    import time — so missing files surface as a friendly UI error, not a
    server crash.
    """
    for mod_name, rel_path in [
        ("utils.gemini_client", "gemini_client.py"),
        ("utils.image_client",  "image_client.py"),
    ]:
        try:
            load_module(mod_name, rel_path)
        except FileNotFoundError:
            pass  # sub-modules will surface their own import errors

# ─────────────────────────────────────────────
# PAGE CONFIGURATION — Must be first Streamlit call
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="LinkedIn Optimization Engine",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "LinkedIn Optimization Engine — AI-powered LinkedIn growth toolkit",
    }
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Professional dark-accent LinkedIn theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════════
   LINKEDIN ENGINE — CSS v3.0
   Strategy: target elements precisely. No wildcard !important rules.
   Sidebar text → white via explicit selectors.
   Main area → let Streamlit's native dark text show through.
   Only custom HTML components need explicit colour declarations.
═══════════════════════════════════════════════════════════════════ */

/* ── Design tokens ─────────────────────────────────────────────── */
:root {
    --blue:        #0A66C2;
    --blue-dark:   #004182;
    --blue-light:  #EAF4FF;
    --blue-mid:    #C7D9F5;
    --green:       #00875A;
    --orange:      #E86A2C;
    --text-dark:   #111827;
    --text-mid:    #374151;
    --text-muted:  #6B7280;
    --bg-card:     #FFFFFF;
    --bg-subtle:   #F8FAFF;
    --border:      #E1E9F5;
    --shadow-sm:   0 1px 4px rgba(0,0,0,.07);
    --shadow-md:   0 4px 16px rgba(10,102,194,.12);
    --shadow-lg:   0 8px 32px rgba(10,102,194,.18);
    --radius-sm:   8px;
    --radius-md:   12px;
    --radius-lg:   16px;
}

/* ── App background ─────────────────────────────────────────────── */
.stApp {
    background: #F3F6FB;
}
.block-container {
    padding-top: 1.5rem !important;
    max-width: 1100px !important;
}

/* ══════════════════════════════════════════════════════════════════
   SIDEBAR — scoped white text WITHOUT wildcard *
══════════════════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: linear-gradient(175deg, #0A66C2 0%, #003D82 100%);
    border-right: none;
}

/* Text nodes */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4,
[data-testid="stSidebar"] span:not([data-baseweb]),
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] li,
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] em,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown span,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: rgba(255,255,255,0.92) !important;
}

/* Radio nav items */
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.08);
    border-radius: var(--radius-sm);
    padding: 7px 11px;
    margin: 2px 0;
    display: block;
    transition: background 0.18s, transform 0.18s;
    cursor: pointer;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.18);
    transform: translateX(3px);
    border-color: rgba(255,255,255,0.2);
}
[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
[data-testid="stSidebar"] .stRadio label:has(input:checked) {
    background: rgba(255,255,255,0.22);
    border-color: rgba(255,255,255,0.35);
    font-weight: 600;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label p,
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] label span {
    color: white !important;
}

/* Sidebar API key inputs — need dark text on white bg */
[data-testid="stSidebar"] .stTextInput input {
    color: #111827 !important;
    background: rgba(255,255,255,0.96) !important;
    border: 1.5px solid rgba(255,255,255,0.3) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder {
    color: #9CA3AF !important;
}
[data-testid="stSidebar"] .stTextInput > label p {
    color: rgba(255,255,255,0.85) !important;
}

/* Sidebar selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.96) !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div[class] {
    color: #111827 !important;
}

/* Sidebar expander */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
[data-testid="stSidebar"] [data-testid="stExpander"] summary span,
[data-testid="stSidebar"] [data-testid="stExpander"] summary svg {
    color: white !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.18) !important;
}

/* ══════════════════════════════════════════════════════════════════
   MAIN AREA — light, clean base; no blanket overrides
══════════════════════════════════════════════════════════════════ */

/* Headings */
.stApp section[data-testid="stMain"] h1,
.stApp section[data-testid="stMain"] h2,
.stApp section[data-testid="stMain"] h3 {
    color: var(--blue) !important;
    font-weight: 700;
}
.stApp section[data-testid="stMain"] h4,
.stApp section[data-testid="stMain"] h5 {
    color: var(--text-dark) !important;
}

/* ── Metric tiles ────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    padding: 1.1rem 1rem !important;
    box-shadow: var(--shadow-sm) !important;
    transition: box-shadow 0.2s;
}
[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-md) !important;
}
[data-testid="stMetricLabel"] p,
[data-testid="stMetricLabel"] span {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
[data-testid="stMetricValue"] div,
[data-testid="stMetricValue"] span {
    color: var(--blue) !important;
    font-weight: 800 !important;
    font-size: 1.7rem !important;
}

/* ── Input fields ────────────────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #FFFFFF !important;
    color: var(--text-dark) !important;
    border: 1.5px solid var(--blue-mid) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.92rem !important;
    transition: border-color 0.18s, box-shadow 0.18s;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 3px rgba(10,102,194,0.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: #9CA3AF !important;
}
.stTextInput > label p,
.stTextArea > label p {
    color: var(--text-mid) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

/* ── Selectbox ───────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > label p {
    color: var(--text-mid) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #FFFFFF !important;
    border: 1.5px solid var(--blue-mid) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-dark) !important;
}
[data-testid="stSelectbox"] [data-baseweb="select"] span {
    color: var(--text-dark) !important;
}

/* ── Radio (main area) ───────────────────────────────────────────── */
[data-testid="stRadio"] > label p {
    color: var(--text-mid) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}
[data-testid="stRadio"] div[role="radiogroup"] label p,
[data-testid="stRadio"] div[role="radiogroup"] label span {
    color: var(--text-dark) !important;
}

/* ── Checkbox ────────────────────────────────────────────────────── */
[data-testid="stCheckbox"] label p,
[data-testid="stCheckbox"] label span {
    color: var(--text-dark) !important;
}

/* ── Slider ──────────────────────────────────────────────────────── */
[data-testid="stSlider"] > label p {
    color: var(--text-mid) !important;
    font-weight: 600 !important;
}

/* ── Multiselect ─────────────────────────────────────────────────── */
[data-testid="stMultiSelect"] > label p {
    color: var(--text-mid) !important;
    font-weight: 600 !important;
}
[data-testid="stMultiSelect"] [data-baseweb="tag"] span {
    color: white !important;
}

/* ── Tabs ────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg-subtle);
    border-radius: var(--radius-md);
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-sm);
    padding: 8px 18px;
    border: none !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span {
    color: var(--text-muted) !important;
    font-weight: 600;
    font-size: 0.88rem;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    box-shadow: var(--shadow-sm) !important;
}
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span {
    color: var(--blue) !important;
    font-weight: 700 !important;
}

/* ── Expanders ───────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: var(--text-dark) !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] summary svg {
    color: var(--blue) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.18s ease !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-dark) !important;
}
.stButton > button:hover {
    border-color: var(--blue) !important;
    color: var(--blue) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md) !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #0A66C2, #004182) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 3px 10px rgba(10,102,194,0.3) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 6px 18px rgba(10,102,194,0.4) !important;
    color: white !important;
    transform: translateY(-2px);
}

/* ── Download button ─────────────────────────────────────────────── */
[data-testid="stDownloadButton"] button {
    color: var(--blue) !important;
    border-color: var(--blue) !important;
    font-weight: 600 !important;
}
[data-testid="stDownloadButton"] button p,
[data-testid="stDownloadButton"] button span {
    color: var(--blue) !important;
}

/* ── Alerts / notifications ──────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] li,
[data-testid="stAlert"] strong {
    color: var(--text-dark) !important;
}

/* ── Caption ─────────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-size: 0.8rem !important;
}

/* ── Code blocks ─────────────────────────────────────────────────── */
[data-testid="stCode"],
pre, pre code {
    background: #F1F5F9 !important;
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
}
[data-testid="stCode"] code,
pre code, pre span {
    color: #1E293B !important;
}

/* ── Spinner ─────────────────────────────────────────────────────── */
[data-testid="stSpinner"] p {
    color: var(--text-mid) !important;
}

/* ══════════════════════════════════════════════════════════════════
   CUSTOM COMPONENTS
══════════════════════════════════════════════════════════════════ */

/* ── Page header banner ──────────────────────────────────────────── */
.main-header {
    background: linear-gradient(135deg, #0A66C2 0%, #003D82 100%);
    padding: 2.2rem 2rem;
    border-radius: var(--radius-lg);
    margin-bottom: 1.8rem;
    text-align: center;
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: "";
    position: absolute;
    top: -50px; right: -50px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: rgba(255,255,255,0.06);
    pointer-events: none;
}
.main-header::after {
    content: "";
    position: absolute;
    bottom: -40px; left: -40px;
    width: 140px; height: 140px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
    pointer-events: none;
}
.main-header .v-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.95);
    font-size: 0.67rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    padding: 3px 12px;
    border-radius: 20px;
    margin-bottom: 0.7rem;
    border: 1px solid rgba(255,255,255,0.2);
}
.main-header h1 {
    color: white !important;
    font-size: 2rem !important;
    font-weight: 800 !important;
    margin: 0 !important;
    text-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
.main-header p {
    color: rgba(255,255,255,0.82) !important;
    font-size: 1rem !important;
    margin: 0.5rem 0 0 !important;
}

/* ── Feature cards (home grid) ───────────────────────────────────── */
.feature-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.5rem 1.2rem;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    box-shadow: var(--shadow-sm);
    height: 100%;
    position: relative;
}
.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
    border-color: var(--blue);
}
.feature-card .new-badge {
    position: absolute;
    top: 10px; right: 10px;
    background: var(--orange);
    color: white;
    font-size: 0.58rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 2px 7px;
    border-radius: 10px;
}
.feature-card .icon { font-size: 2.4rem; margin-bottom: 0.6rem; }
.feature-card h3   { color: var(--blue) !important; font-weight: 700; margin: 0 0 0.4rem 0; font-size: 0.95rem; }
.feature-card p    { color: var(--text-muted) !important; font-size: 0.82rem; margin: 0; line-height: 1.45; }

/* ── Post cards (library) ────────────────────────────────────────── */
.post-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.6rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s, border-color 0.2s;
}
.post-card:hover {
    box-shadow: var(--shadow-md);
    border-color: #C7D9F5;
}
.post-card-meta {
    font-size: 0.72rem;
    color: var(--text-muted) !important;
    margin-bottom: 0.55rem;
    display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
}
.post-card-meta .tag {
    background: var(--blue-light);
    color: var(--blue) !important;
    padding: 2px 8px; border-radius: 10px; font-weight: 700;
}
.post-card-body {
    font-size: 0.88rem;
    color: var(--text-dark) !important;
    line-height: 1.6;
    white-space: pre-wrap;
}

/* ── Stat cards ──────────────────────────────────────────────────── */
.stat-card {
    background: linear-gradient(135deg, #0A66C2, #003D82);
    color: white;
    padding: 1.2rem;
    border-radius: var(--radius-md);
    text-align: center;
    box-shadow: 0 4px 16px rgba(10,102,194,0.25);
}
.stat-card .number { font-size: 2rem; font-weight: 800; color: white !important; }
.stat-card .label  { font-size: 0.78rem; opacity: 0.82; color: white !important; }

/* ── Resume session banner ───────────────────────────────────────── */
.resume-banner {
    background: linear-gradient(135deg, #EAF4FF 0%, #D6EAFF 100%);
    border: 1px solid #B3D4F0;
    border-radius: var(--radius-md);
    padding: 1rem 1.4rem;
    margin-bottom: 1.4rem;
    display: flex; align-items: center; gap: 1rem;
}
.resume-banner .rb-icon { font-size: 1.8rem; }
.resume-banner h4 { color: var(--blue) !important; margin: 0; font-size: 0.93rem; font-weight: 700; }
.resume-banner p  { color: var(--text-mid) !important; margin: 2px 0 0; font-size: 0.8rem; }

/* ── Viral analyzer panels ───────────────────────────────────────── */
.viral-panel {
    background: var(--bg-subtle);
    border: 1.5px solid var(--blue-mid);
    border-radius: var(--radius-md);
    padding: 1.4rem;
    margin-top: 0.8rem;
}
.viral-score-circle {
    width: 88px; height: 88px;
    border-radius: 50%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-weight: 800; color: white !important;
    margin: 0 auto 0.8rem auto;
    font-size: 1.7rem;
    box-shadow: 0 4px 16px rgba(10,102,194,0.3);
}
.score-bar-wrap { margin: 0.5rem 0; }
.score-bar-label {
    display: flex; justify-content: space-between;
    font-size: 0.8rem; font-weight: 600;
    color: var(--text-mid) !important;
    margin-bottom: 3px;
}
.score-bar-bg {
    background: #E1E9F5;
    border-radius: 99px; height: 9px; overflow: hidden;
}
.score-bar-fill {
    height: 100%; border-radius: 99px;
    transition: width 0.7s ease;
}

/* ── Hook preview card (mobile mockup) ───────────────────────────── */
.hook-preview-card {
    background: white;
    border: 1px solid #E1E9F5;
    border-radius: var(--radius-md);
    padding: 1.1rem;
    box-shadow: var(--shadow-sm);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.hook-preview-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.hook-preview-avatar {
    width: 40px; height: 40px; border-radius: 50%;
    background: linear-gradient(135deg, #0A66C2, #003D82);
    display: flex; align-items: center; justify-content: center;
    color: white !important; font-weight: 800; font-size: 1rem; flex-shrink: 0;
}
.hook-preview-name  { font-weight: 700; font-size: 0.87rem; color: #111 !important; }
.hook-preview-title { font-size: 0.73rem; color: #555 !important; }
.hook-preview-text  { font-size: 0.87rem; color: #111 !important; line-height: 1.55; }
.hook-see-more      { color: var(--blue) !important; font-size: 0.84rem; font-weight: 600; cursor: pointer; }

/* ── Badge ───────────────────────────────────────────────────────── */
.badge-new {
    background: var(--orange);
    color: white;
    font-size: 0.63rem; font-weight: 700;
    padding: 2px 7px; border-radius: 99px;
    vertical-align: middle; margin-left: 6px; letter-spacing: 0.5px;
}

/* ── Footer ──────────────────────────────────────────────────────── */
.footer {
    text-align: center; padding: 2rem 0;
    color: var(--text-muted) !important;
    font-size: 0.78rem;
    border-top: 1px solid var(--border);
    margin-top: 3rem;
}

/* ── Hide Streamlit chrome ───────────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# UTILITY — One-click clipboard copy
# ─────────────────────────────────────────────
def copy_to_clipboard_button(text: str, label: str = "📋 Copy to Clipboard", key: str = "copy"):
    """Renders a button that copies `text` to the user's clipboard via JS."""
    escaped = text.replace("`", "\\`").replace("$", "\\$")
    copy_js = f"""
    <script>
    function copyText_{key}() {{
        navigator.clipboard.writeText(`{escaped}`).then(() => {{
            const btn = document.getElementById('copybtn_{key}');
            const orig = btn.innerText;
            btn.innerText = '✅ Copied!';
            btn.style.background = '#00c851';
            setTimeout(() => {{ btn.innerText = orig; btn.style.background = ''; }}, 2000);
        }});
    }}
    </script>
    <button id="copybtn_{key}"
        onclick="copyText_{key}()"
        style="
            background: linear-gradient(135deg,#0A66C2,#004182);
            color:white; border:none; border-radius:8px;
            padding:8px 18px; font-size:0.85rem; font-weight:600;
            cursor:pointer; transition:all 0.2s ease;
            box-shadow:0 2px 8px rgba(10,102,194,0.25);
        ">{label}</button>
    """
    st.markdown(copy_js, unsafe_allow_html=True)


def save_to_history(post_type: str, content: str):
    """Adds a generated post to session history and bumps stats."""
    import datetime
    record = {
        "type": post_type,
        "content": content,
        "timestamp": datetime.datetime.now().strftime("%H:%M"),
    }
    st.session_state["post_history"].insert(0, record)


def save_to_library(content: str, module: str, score: int = 0, tags: list = None):
    """Save a post to the Post Library (DB-backed) and bump session counters."""
    if _CORE_AVAILABLE:
        _db.save_post(content, module, score=score, tags=tags or [])
    else:
        # Legacy in-memory fallback (no persistence)
        entry = {
            "id": int(time.time() * 1000),
            "content": content.strip(),
            "module": module,
            "score": score,
            "tags": tags or [],
            "created_at": datetime.now().strftime("%b %d, %Y · %I:%M %p"),
            "starred": False,
        }
        st.session_state.setdefault("post_library", []).insert(0, entry)

    st.session_state["session_posts_generated"] = (
        st.session_state.get("session_posts_generated", 0) + 1
    )
    save_to_history(module, content)


# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
def init_session_state():
    """Initialize all session state variables."""
    if _CORE_AVAILABLE:
        _state.init_session_state()
        return

    # ── Fallback (core/ not found) ─────────────────────────────────────────
    def _get_secret(env_key: str, fallback: str = "") -> str:
        val = os.environ.get(env_key, "")
        if val:
            return val
        try:
            return st.secrets.get(env_key, fallback)
        except Exception:
            return fallback

    defaults = {
        "gemini_api_key":    _get_secret("GEMINI_API_KEY"),
        "stability_api_key": _get_secret("STABILITY_API_KEY"),
        "hf_api_key":        _get_secret("HF_API_KEY"),
        "gemini_model":      "gemini-2.5-flash",
        "last_generated_post": "",
        "current_page": "🏠 Home",
        "post_history": [],
        "post_library": [],
        "session_posts_generated": 0,
        "session_minutes_saved": 0,
        "hooks_analyzed": 0,
        "viral_analyzer_result": None,
        "hook_analysis_result": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ─────────────────────────────────────────────
# SIDEBAR — Navigation + API Keys
# ─────────────────────────────────────────────
def render_sidebar():
    """Renders the sidebar with navigation and API key configuration."""
    with st.sidebar:
        # Logo & Title
        st.markdown("""
        <div style="text-align:center; padding: 1rem 0;">
            <div style="font-size:3rem;">🚀</div>
            <h2 style="color:white!important; margin:0; font-size:1.2rem; font-weight:800;">
                LinkedIn Engine
            </h2>
            <p style="color:rgba(255,255,255,0.7)!important; font-size:0.75rem; margin:4px 0 0 0;">
                AI-Powered Optimization
            </p>
        </div>
        <hr style="border-color:rgba(255,255,255,0.2); margin:0.5rem 0;">
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("**📍 Navigation**")
        pages = [
            "🏠 Home",
            "🔥 Viral Hook Analyzer",    # NEW — dedicated full-featured hook tool
            "🚀 Post Generator",
            "🔧 Post Optimizer",
            "💼 About Optimizer",
            "🌟 Profile Enhancer",
            "💡 Content Ideas",
            "🧠 Strategy Insights",
            "🎨 Image Generator",
            "⚡ Engagement Toolkit",
            "📚 Post Library",           # auto-saved posts with search/export
            "🗄️ Data Manager",           # backup export & restore
        ]
        selected_page = st.radio(
            "Navigate to",
            pages,
            index=pages.index(st.session_state.get("current_page", "🏠 Home")),
            label_visibility="collapsed",
        )
        st.session_state["current_page"] = selected_page

        st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        # ── Gemini Model Switcher ─────────────────────────────────────────
        st.markdown("**🤖 Gemini Model**")

        GEMINI_MODELS = {
            "gemini-2.5-flash":      ("⚡ Gemini 2.5 Flash",      "Fast · Best for most tasks"),
            "gemini-2.5-flash-lite": ("🪶 Gemini 2.5 Flash-Lite", "Lightweight · Use if Flash errors"),
        }

        current_model = st.session_state.get("gemini_model", "gemini-2.5-flash")
        # Build display list in a fixed order
        model_keys   = list(GEMINI_MODELS.keys())
        model_labels = [GEMINI_MODELS[k][0] for k in model_keys]
        current_idx  = model_keys.index(current_model) if current_model in model_keys else 0

        chosen_label = st.radio(
            "Select Gemini model",
            model_labels,
            index=current_idx,
            label_visibility="collapsed",
            key="gemini_model_radio",
        )
        chosen_key = model_keys[model_labels.index(chosen_label)]
        if chosen_key != st.session_state["gemini_model"]:
            st.session_state["gemini_model"] = chosen_key
            # Clear cached AI results so they re-run with the new model
            st.session_state["viral_analyzer_result"] = None
            st.session_state["hook_analysis_result"]  = None

        _, sub = GEMINI_MODELS[st.session_state["gemini_model"]]
        st.markdown(
            f"<div style='font-size:0.72rem; color:rgba(255,255,255,0.65); "
            f"margin-top:-6px; margin-bottom:6px;'>{sub}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        # ── API Keys Section ──
        st.markdown("**🔑 API Configuration**")

        with st.expander("⚙️ Configure API Keys", expanded=not bool(st.session_state["gemini_api_key"])):
            # Gemini
            gemini_key = st.text_input(
                "🤖 Gemini API Key",
                value=st.session_state["gemini_api_key"],
                type="password",
                placeholder="AIza...",
                help="Get from: aistudio.google.com",
            )
            if gemini_key != st.session_state["gemini_api_key"]:
                st.session_state["gemini_api_key"] = gemini_key

            # Stability AI
            stability_key = st.text_input(
                "🎨 Stability AI Key",
                value=st.session_state["stability_api_key"],
                type="password",
                placeholder="sk-...",
                help="Get from: platform.stability.ai",
            )
            if stability_key != st.session_state["stability_api_key"]:
                st.session_state["stability_api_key"] = stability_key

            # Hugging Face
            hf_key = st.text_input(
                "🤗 Hugging Face Key",
                value=st.session_state["hf_api_key"],
                type="password",
                placeholder="hf_...",
                help="Get from: huggingface.co/settings/tokens",
            )
            if hf_key != st.session_state["hf_api_key"]:
                st.session_state["hf_api_key"] = hf_key

        # API Status indicators
        st.markdown("**📊 API Status**")
        gemini_ok = bool(st.session_state["gemini_api_key"])
        stability_ok = bool(st.session_state["stability_api_key"])
        hf_ok = bool(st.session_state["hf_api_key"])

        st.markdown(
            f"{'✅' if gemini_ok else '❌'} Gemini AI (Text) {'— Active' if gemini_ok else '— Not set'}"
        )
        st.markdown(
            f"{'✅' if stability_ok else '⚪'} Stability AI (Images) {'— Active' if stability_ok else '— Not set'}"
        )
        st.markdown(
            f"{'✅' if hf_ok else '⚪'} Hugging Face (Fallback) {'— Active' if hf_ok else '— Not set'}"
        )

        if not gemini_ok:
            st.warning("⚠️ Add Gemini API key to unlock all text features!")

        st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        # Tips
        st.markdown("""
        <div style="font-size:0.75rem; color:rgba(255,255,255,0.7);">
        💡 <strong>Quick Tips:</strong><br>
        • Gemini API: <a href="https://aistudio.google.com" target="_blank" style="color:#90CAF9;">aistudio.google.com</a><br>
        • Stability AI: <a href="https://platform.stability.ai" target="_blank" style="color:#90CAF9;">platform.stability.ai</a><br>
        • HuggingFace: <a href="https://huggingface.co/settings/tokens" target="_blank" style="color:#90CAF9;">huggingface.co</a>
        </div>
        """, unsafe_allow_html=True)

        # ── Session Stats ──────────────────────────────────
        st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)
        posts_gen   = st.session_state.get("session_posts_generated", 0)
        mins_saved  = posts_gen * 12   # avg 12 min saved per AI-generated post
        history_ct  = (_db.get_stats()["total"] if _CORE_AVAILABLE
                       else len(st.session_state.get("post_library", [])))
        hooks_done  = st.session_state.get("hooks_analyzed", 0)
        st.markdown(f"""
        <div style="font-size:0.78rem; color:rgba(255,255,255,0.85); text-align:center;">
            <div style="display:flex; justify-content:space-around; margin-top:0.4rem;">
                <div>
                    <div style="font-size:1.4rem; font-weight:800;">{posts_gen}</div>
                    <div style="opacity:0.75; font-size:0.7rem;">Posts Made</div>
                </div>
                <div>
                    <div style="font-size:1.4rem; font-weight:800;">{mins_saved}</div>
                    <div style="opacity:0.75; font-size:0.7rem;">Mins Saved</div>
                </div>
                <div>
                    <div style="font-size:1.4rem; font-weight:800;">{history_ct}</div>
                    <div style="opacity:0.75; font-size:0.7rem;">Saved Posts</div>
                </div>
            </div>
            <div style="margin-top:0.5rem; opacity:0.8; font-size:0.72rem;">
                🔥 {hooks_done} hook{'s' if hooks_done != 1 else ''} analyzed this session
            </div>
        </div>
        """, unsafe_allow_html=True)

    return selected_page


# ─────────────────────────────────────────────
# HOME PAGE
# ─────────────────────────────────────────────
def render_home():
    """Renders the home/landing page."""
    # Hero section
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">v2.0 · Production Ready</div>
        <h1>🚀 LinkedIn Optimization Engine</h1>
        <p>AI-powered toolkit to transform your LinkedIn presence from beginner to thought leader</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Resume session banner (shown only when library has posts) ─────────
    library = st.session_state.get("post_library", [])
    if library:
        last = library[0]
        st.markdown(f"""
        <div class="resume-banner">
            <div class="rb-icon">📖</div>
            <div>
                <h4>Resume where you left off</h4>
                <p>You have <strong>{len(library)} post{'s' if len(library) > 1 else ''}</strong>
                 saved this session — latest from <strong>{last['module']}</strong>
                 at {last['created_at']}.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    stats = [
        ("10", "Powerful Modules"),
        ("∞",  "Post Variations"),
        ("100","Profile Score"),
        ("3",  "AI APIs"),
    ]
    for col, (number, label) in zip([col1, col2, col3, col4], stats):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="number">{number}</div>
                <div class="label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Feature cards ── rendered in ONE st.markdown() call via CSS grid.
    # Calling st.markdown(unsafe_allow_html=True) per st.columns() cell causes
    # Streamlit's markdown parser to escape subsequent cards as raw code blocks.
    # A single HTML/CSS-grid call is the reliable production fix.

    features = [
        ("\U0001f525", "Viral Hook Analyzer", "Score your hook across 5 dimensions, get 5 power rewrites + live mobile preview", True),
        ("\U0001f680", "Post Generator",      "Create viral posts with proven frameworks, hooks, and 2&ndash;3 variations per topic", False),
        ("\U0001f527", "Post Optimizer",      "Get your existing posts diagnosed and rewritten with engagement scores", False),
        ("\U0001f4bc", "About Optimizer",     "Transform your About section into a personal brand story that gets found", False),
        ("\U0001f31f", "Profile Enhancer",    "Get your profile scored (0&ndash;100) and a 30-day transformation roadmap", False),
        ("\U0001f4a1", "Content Ideas",       "Generate a full content calendar with hooks, angles, and hashtags", False),
        ("\U0001f9e0", "Strategy Insights",   "Reverse-engineered playbooks from top LinkedIn creators", False),
        ("\U0001f3a8", "Image Generator",     "AI-generated professional visuals using SDXL and Hugging Face", False),
        ("\u26a1", "Engagement Toolkit",      "Hooks, CTAs, hashtag optimizer, and perfect posting times", False),
        ("\U0001f4da", "Post Library",        "Every generated post auto-saved &mdash; search, star, filter, and export", True),
    ]

    _card_html = ""
    for _icon, _title, _desc, _is_new in features:
        _badge = '<span class="fc-new">NEW</span>' if _is_new else ""
        _card_html += (
            f'<div class="fc-card">{_badge}'
            f'<div class="fc-icon">{_icon}</div>'
            f'<p class="fc-title">{_title}</p>'
            f'<p class="fc-desc">{_desc}</p></div>'
        )

    st.markdown("""
<style>
.fc-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.5rem;}
@media(max-width:900px){.fc-grid{grid-template-columns:repeat(2,1fr);}}
@media(max-width:500px){.fc-grid{grid-template-columns:1fr;}}
.fc-card{background:#FFFFFF;border:1px solid #E1E9F5;border-radius:12px;padding:1.4rem 1rem;
         text-align:center;position:relative;box-shadow:0 1px 4px rgba(0,0,0,.07);
         transition:transform .2s,box-shadow .2s,border-color .2s;}
.fc-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(10,102,194,.15);border-color:#0A66C2;}
.fc-new{position:absolute;top:10px;right:10px;background:#E86A2C;color:#fff;
        font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.5px;
        padding:2px 7px;border-radius:10px;}
.fc-icon{font-size:2.2rem;margin-bottom:.5rem;display:block;}
.fc-title{color:#0A66C2 !important;font-weight:700;margin:0 0 .4rem;font-size:.92rem;}
.fc-desc{color:#374151 !important;font-size:.82rem;margin:0;line-height:1.4;}
</style>
<div class="fc-grid">""" + _card_html + """</div>
""", unsafe_allow_html=True)


    # Getting started guide
    st.markdown("---")
    st.markdown("### 🏁 Getting Started in 3 Steps")

    step1, step2, step3 = st.columns(3)
    with step1:
        st.markdown("""
        **Step 1: Configure API Keys** 🔑
        
        Open the sidebar → **Configure API Keys**:
        - **Gemini API** (required for all text features): Free at [aistudio.google.com](https://aistudio.google.com)
        - **Stability AI** (for image generation): Free tier at [platform.stability.ai](https://platform.stability.ai)
        - **Hugging Face** (fallback images): Free at [huggingface.co](https://huggingface.co/settings/tokens)

        *Pro tip: set `GEMINI_API_KEY` as an env variable and it loads automatically.*
        """)

    with step2:
        st.markdown("""
        **Step 2: Analyze Your Hooks** 🔥

        Start with **Viral Hook Analyzer** (new!):
        - Paste any post you've written
        - Get a live hook score (0–100) across 5 dimensions
        - Receive 5 power-rewritten alternatives
        - Preview exactly how it looks on mobile

        *90% of LinkedIn reach is won or lost in the first 2 lines.*
        """)

    with step3:
        st.markdown("""
        **Step 3: Create Consistent Content** 🚀
        
        Use **Content Ideas** to fill your content calendar, then:
        - **Post Generator** to write each post
        - **Image Generator** to create visuals
        - **Engagement Toolkit** for hooks, CTAs, hashtags
        - **Post Library** → everything auto-saved for you
        
        Post consistently 3× per week for best results!
        """)

    st.markdown("---")
    st.info("👈 **Select a module from the sidebar** to get started. Or try the **Viral Analyzer** below — paste any LinkedIn post for an instant AI score!")

    # ════════════════════════════════════════════════════════
    # 🔥 WOW FEATURE: LinkedIn Viral Post Analyzer
    # ════════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex; align-items:center; margin-bottom:0.5rem;">
        <span style="font-size:1.5rem; margin-right:0.5rem;">🔥</span>
        <h2 style="margin:0;">Viral Post Analyzer</h2>
        <span class="badge-new">NEW</span>
    </div>
    <p style="color:#555; margin-bottom:1rem; font-size:0.93rem;">
        Paste any LinkedIn post — yours or a top creator's — and get an instant AI-powered virality breakdown
        across 5 dimensions. Understand <em>exactly</em> why posts go viral.
    </p>
    """, unsafe_allow_html=True)

    analyze_col, result_col = st.columns([1, 1], gap="large")

    with analyze_col:
        post_to_analyze = st.text_area(
            "Paste a LinkedIn post here",
            height=220,
            placeholder="Paste any LinkedIn post to analyze...\n\nExample:\n'I got rejected by 12 companies before landing my dream job.\nHere's what I learned:\n...'",
            key="viral_analyzer_input",
        )

        char_count = len(post_to_analyze)
        char_color = "#08df5e" if char_count <= 3000 else "#F31A0E"
        st.markdown(
            f"<div style='font-size:0.75rem; color:{char_color}; text-align:right;'>"
            f"{char_count:,} / 3,000 chars</div>",
            unsafe_allow_html=True,
        )

        analyze_btn = st.button(
            "🔥 Analyze Virality",
            type="primary",
            disabled=not bool(st.session_state.get("gemini_api_key")),
            key="viral_analyze_btn",
        )
        if not st.session_state.get("gemini_api_key"):
            st.caption("⚠️ Add your Gemini API key in the sidebar to enable this.")

    with result_col:
        if analyze_btn and post_to_analyze.strip():
            if len(post_to_analyze.strip()) < 30:
                st.warning("Post is too short to analyze. Please paste a real LinkedIn post.")
            else:
                with st.spinner("🤖 Scoring your post with AI..."):
                    analysis_prompt = f"""You are a LinkedIn virality expert. Analyze this LinkedIn post and return ONLY a valid JSON object — no markdown, no explanation, no backticks.

POST TO ANALYZE:
\"\"\"{post_to_analyze[:3000]}\"\"\"

Return this exact JSON structure:
{{
  "overall_score": <integer 0-100>,
  "verdict": "<one punchy sentence verdict, max 15 words>",
  "dimensions": {{
    "hook_power": {{"score": <0-100>, "comment": "<max 20 words>"}},
    "storytelling": {{"score": <0-100>, "comment": "<max 20 words>"}},
    "cta_strength": {{"score": <0-100>, "comment": "<max 20 words>"}},
    "formatting": {{"score": <0-100>, "comment": "<max 20 words>"}},
    "emotional_pull": {{"score": <0-100>, "comment": "<max 20 words>"}}
  }},
  "top_strength": "<what is working best, max 25 words>",
  "top_fix": "<the single most impactful change to make, max 25 words>",
  "improved_hook": "<rewrite only the first 1-2 lines to be more viral, max 30 words>"
}}"""
                    try:
                        if _CORE_AVAILABLE:
                            result = _ai.generate_json(
                                analysis_prompt,
                                st.session_state["gemini_api_key"],
                                model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                                temperature=0.4,
                                max_tokens=1024,
                                required_keys=["overall_score", "dimensions"],
                            )
                        else:
                            from google import genai as _genai
                            from google.genai import types as _gtypes
                            _c  = _genai.Client(api_key=st.session_state["gemini_api_key"])
                            _r  = _c.models.generate_content(
                                model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                                contents=analysis_prompt,
                                config=_gtypes.GenerateContentConfig(temperature=0.4, max_output_tokens=1024),
                            )
                            raw = _r.text.strip()
                            if raw.startswith("```"):
                                raw = raw.split("```")[1]
                                if raw.startswith("json"):
                                    raw = raw[4:]
                            result = json.loads(raw.strip())
                        st.session_state["viral_analyzer_result"] = result
                    except Exception:
                        st.error("⚠️ Something went wrong. Please try again.")
                        with st.expander("🔍 Details (for debugging)"):
                            st.code(traceback.format_exc())
                        st.session_state["viral_analyzer_result"] = None

        

        # ── Render results ──────────────────────────────────
        result = st.session_state.get("viral_analyzer_result")
        if result:
            score = result.get("overall_score", 0)
            # Color: red < 40, orange < 65, green >= 65
            if score >= 65:
                score_color = "linear-gradient(135deg,#00c851,#007a32)"
                score_label = "🚀 High Viral Potential"
            elif score >= 40:
                score_color = "linear-gradient(135deg,#FF6B35,#cc4a00)"
                score_label = "⚠️ Moderate Potential"
            else:
                score_color = "linear-gradient(135deg,#FF3B30,#990000)"
                score_label = "❌ Low Viral Potential"

            st.markdown(f"""
            <div class="viral-panel">
                <div class="viral-score-circle" style="background:{score_color};">
                    {score}
                    <div style="font-size:0.55rem; font-weight:600; opacity:0.9; margin-top:-4px;">/ 100</div>
                </div>
                <div style="text-align:center; font-weight:700; color:#0A66C2; margin-bottom:1rem;">{score_label}</div>
                <div style="font-style:italic; color:#444; text-align:center; font-size:0.9rem; margin-bottom:1.2rem;">
                    "{result.get('verdict', '')}"
                </div>
            """, unsafe_allow_html=True)

            dim_labels = {
                "hook_power":    ("🎣 Hook Power",     "#05396C"),
                "storytelling":  ("📖 Storytelling",   "#4D0988"),
                "cta_strength":  ("📣 CTA Strength",   "#067934"),
                "formatting":    ("🗂️ Formatting",     "#7A2607"),
                "emotional_pull":("❤️ Emotional Pull", "#800830"),
            }

            dims = result.get("dimensions", {})
            for dim_key, (dim_name, bar_color) in dim_labels.items():
                dim_data = dims.get(dim_key, {})
                s = dim_data.get("score", 0)
                comment = dim_data.get("comment", "")
                st.markdown(f"""
                <div class="score-bar-wrap">
                    <div class="score-bar-label">
                        <span>{dim_name}</span>
                        <span style="color:{bar_color}; font-weight:800;">{s}/100</span>
                    </div>
                    <div class="score-bar-bg">
                        <div class="score-bar-fill" style="width:{s}%; background:{bar_color};"></div>
                    </div>
                    <div style="font-size:0.74rem; color:#666; margin-top:2px;">{comment}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

            # Strength / Fix / Improved Hook
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.success(f"✅ **What's working:** {result.get('top_strength', '')}")
            with c2:
                st.warning(f"🔧 **Top fix:** {result.get('top_fix', '')}")

            improved_hook = result.get("improved_hook", "")
            if improved_hook:
                st.markdown("**✨ AI-Improved Opening Hook:**")
                st.info(f'*"{improved_hook}"*')
                copy_to_clipboard_button(improved_hook, "📋 Copy Improved Hook", key="hook_copy")

        elif not analyze_btn:
            st.markdown("""
            <div style="text-align:center; padding:3rem 1rem; color:#aaa; border:2px dashed #D0E8FF; border-radius:12px; margin-top:0.5rem;">
                <div style="font-size:2.5rem;">📊</div>
                <div style="font-weight:600; color:#888; margin-top:0.5rem;">Your viral score will appear here</div>
                <div style="font-size:0.8rem; margin-top:0.3rem;">Paste a post and click Analyze</div>
            </div>
            """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        Built with ❤️ using Streamlit · Gemini AI · Stability AI (SDXL) · Hugging Face<br>
        <em>Not affiliated with LinkedIn. No scraping. All content is AI-generated.</em>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 🔥 VIRAL HOOK ANALYZER — Dedicated Page
#
# LinkedIn reality: posts truncate at ~210 chars in the feed.
# Only the hook shows before "…see more". If it doesn't grab,
# nobody reads — no matter how good the rest is.
# This tool is the #1 request in every LinkedIn creator community.
# ─────────────────────────────────────────────
def render_viral_hook_analyzer():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">LinkedIn Creator Secret Weapon</div>
        <h1>🔥 Viral Hook Analyzer</h1>
        <p>Score, diagnose & rewrite your hook — because 90% of your reach is won in the first 2 lines</p>
    </div>
    """, unsafe_allow_html=True)

    # Education cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**📱 The LinkedIn Feed Problem**\n\nOnly ~210 characters show before '…see more'. If your hook doesn't grab in 2 seconds, nobody reads — regardless of how good the rest is.")
    with c2:
        st.warning("**🧠 What Makes a Hook Viral?**\n\nTop hooks trigger: *Curiosity* (open a loop), *Emotion* (fear/hope/awe), *Specificity* (numbers & names), *Bold Claim* (challenge beliefs), or *Story Opening* (mid-action pull).")
    with c3:
        st.success("**📈 The ROI**\n\nCreators who rewrote their hooks using this framework report 3–10× more impressions on the same content. The algorithm rewards 'see more' clicks.")

    st.markdown("---")

    if not st.session_state.get("gemini_api_key"):
        st.error("🔑 **Gemini API key required.** Add it in the sidebar to unlock Hook Analysis.")
        st.stop()

    # ── Input + Live Preview ────────────────────────────────────────────────
    col_input, col_preview = st.columns([1.1, 0.9])

    with col_input:
        st.markdown("### ✏️ Your Post (or just the hook)")
        user_text = st.text_area(
            "Paste your LinkedIn post or hook here",
            height=180,
            placeholder=(
                "Example:\n"
                "I got fired at 32.\n"
                "No savings. No plan. No idea what to do next.\n\n"
                "Here's how that became the best thing that ever happened to me..."
            ),
            label_visibility="collapsed",
            key="hook_analyzer_input",
        )

        char_count    = len(user_text)
        is_truncated  = char_count > 210

        if char_count == 0:
            st.caption("0 / 210 chars visible in feed")
        elif char_count <= 210:
            st.success(f"✅ {char_count} / 210 chars — full post visible without 'see more'")
        else:
            st.warning(f"✂️ {char_count} chars total — LinkedIn shows first 210 then '…see more'. Hook ends at char 210.")

        tone_col, name_col = st.columns(2)
        with tone_col:
            tone = st.selectbox(
                "Rewrite tone",
                ["Professional & Authoritative", "Conversational & Warm",
                 "Bold & Provocative", "Story-Driven", "Data-Led"],
                key="hook_tone",
            )
        with name_col:
            author_name = st.text_input("Your name (for preview)", placeholder="Alex Johnson",
                                        value="You", key="hook_author")

        analyze_btn = st.button(
            "🔥 Analyze & Rewrite Hook", type="primary",
            use_container_width=True,
            disabled=not bool(user_text.strip()),
            key="hook_analyze_btn",
        )

    with col_preview:
        st.markdown("### 📱 Mobile Feed Preview")
        preview_text = user_text[:210] if user_text else "Your post will appear here…"
        initial      = (author_name[0] if author_name else "Y").upper()
        see_more_tag = '<span class="hook-see-more">…see more</span>' if is_truncated else ""

        st.markdown(f"""
        <div class="hook-preview-card">
            <div class="hook-preview-header">
                <div class="hook-preview-avatar">{initial}</div>
                <div>
                    <div class="hook-preview-name">{author_name or 'You'}</div>
                    <div class="hook-preview-title">Your LinkedIn Headline · 2nd • Just now</div>
                </div>
            </div>
            <div class="hook-preview-text">
                {preview_text.replace(chr(10), "<br>")}{see_more_tag}
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("👆 Exactly what appears in the LinkedIn mobile feed before '…see more'")

    # ── AI Analysis ─────────────────────────────────────────────────────────
    if analyze_btn and user_text.strip():
        with st.spinner("🔥 Analyzing across 5 LinkedIn dimensions…"):
            prompt = f"""You are a world-class LinkedIn content strategist. Analyze the hook/opening of this post.

HOOK (first 210 chars):
\"\"\"{user_text[:210].strip()}\"\"\"

FULL POST (context):
\"\"\"{user_text}\"\"\"

Return ONLY a JSON object — no markdown, no backticks, no preamble:
{{
  "overall_score": <0-100 integer>,
  "scores": {{
    "curiosity_gap":     <0-20>,
    "emotional_trigger": <0-20>,
    "specificity":       <0-20>,
    "bold_claim":        <0-20>,
    "readability":       <0-20>
  }},
  "verdict": "<2-sentence honest verdict>",
  "strengths":  ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "rewrites": [
    {{"label": "Curiosity Gap",  "hook": "<rewrite using curiosity-gap technique, ≤210 chars>"}},
    {{"label": "Story Opening",  "hook": "<rewrite starting mid-action, ≤210 chars>"}},
    {{"label": "Bold Claim",     "hook": "<rewrite with a provocative statement, ≤210 chars>"}},
    {{"label": "Data-Led",       "hook": "<rewrite with a striking stat or number, ≤210 chars>"}},
    {{"label": "{tone}",         "hook": "<rewrite in the requested tone, ≤210 chars>"}}
  ],
  "best_posting_time": "<recommended day & time>",
  "predicted_ctr": "<estimated see-more CTR vs average>"
}}

Rules: every rewrite ≤210 chars, distinctly different techniques, genuinely viral-worthy."""

            try:
                if _CORE_AVAILABLE:
                    data = _ai.generate_json(
                        prompt,
                        st.session_state["gemini_api_key"],
                        model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                        temperature=0.5,
                        max_tokens=1500,
                        required_keys=["overall_score", "scores", "rewrites"],
                    )
                else:
                    from google import genai as _genai
                    from google.genai import types as _gtypes
                    _c   = _genai.Client(api_key=st.session_state["gemini_api_key"])
                    _res = _c.models.generate_content(
                        model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                        contents=prompt,
                        config=_gtypes.GenerateContentConfig(temperature=0.5, max_output_tokens=1500),
                    )
                    raw = _res.text.strip()
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    data = json.loads(raw.strip())
                st.session_state["hook_analysis_result"] = data
                st.session_state["hooks_analyzed"] = st.session_state.get("hooks_analyzed", 0) + 1
            except Exception:
                st.error("⚠️ Something went wrong. Please try again.")
                with st.expander("🔍 Details (for debugging)"):
                    st.code(traceback.format_exc())
                st.session_state["hook_analysis_result"] = None

    # ── Results ─────────────────────────────────────────────────────────────
    result = st.session_state.get("hook_analysis_result")
    if result:
        st.markdown("---")
        st.markdown("## 📊 Hook Analysis Report")

        score = result.get("overall_score", 0)
        if score >= 75:
            score_color = "#00c851"; score_label = "🔥 Viral Potential"
        elif score >= 55:
            score_color = "#FF6B35"; score_label = "👍 Good Hook"
        elif score >= 35:
            score_color = "#f0a500"; score_label = "⚠️ Needs Work"
        else:
            score_color = "#e63946"; score_label = "🚨 Major Rewrite"

        sc1, sc2 = st.columns([0.3, 0.7])
        with sc1:
            st.markdown(f"""
            <div style="text-align:center; padding:1.5rem; background:white;
                        border:2px solid {score_color}; border-radius:16px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.06);">
                <div style="font-size:3.5rem; font-weight:900; color:{score_color}; line-height:1;">{score}</div>
                <div style="font-size:0.72rem; color:#888; margin-top:4px;">out of 100</div>
                <div style="font-size:0.95rem; font-weight:700; color:{score_color}; margin-top:8px;">{score_label}</div>
            </div>
            """, unsafe_allow_html=True)
        with sc2:
            st.markdown(f"**Verdict:** {result.get('verdict', '')}")
            for s in result.get("strengths", []):
                st.success(f"✅ {s}")
            for w in result.get("weaknesses", []):
                st.warning(f"⚠️ {w}")

        # Dimension breakdown
        st.markdown("### 🎯 5-Dimension Breakdown")
        dim_meta = {
            "curiosity_gap":     ("🪤 Curiosity Gap",     "Opens a loop the reader must close?"),
            "emotional_trigger": ("❤️ Emotional Trigger", "Fear, hope, awe, or pride?"),
            "specificity":       ("🎯 Specificity",        "Numbers, names & concrete detail?"),
            "bold_claim":        ("💥 Bold Claim",         "Challenges a belief or surprises?"),
            "readability":       ("📖 Readability",        "Short sentences? Easy to scan?"),
        }
        scores = result.get("scores", {})
        dcols  = st.columns(5)
        for col, (key, (label, tip)) in zip(dcols, dim_meta.items()):
            val = scores.get(key, 0)
            pct = (val / 20) * 100
            bar_col = "#00c851" if pct >= 70 else ("#FF6B35" if pct >= 40 else "#e63946")
            with col:
                st.markdown(f"""
                <div style="background:white; border:1px solid #E1E9F5; border-radius:10px;
                            padding:0.9rem; text-align:center; box-shadow:0 2px 6px rgba(0,0,0,0.05);">
                    <div style="font-size:0.78rem; font-weight:700; color:#333; margin-bottom:6px;">{label}</div>
                    <div style="font-size:1.6rem; font-weight:900; color:{bar_col};">{val}/20</div>
                    <div class="score-bar-bg" style="margin:6px 0 4px;">
                        <div class="score-bar-fill" style="width:{pct}%; background:{bar_col};"></div>
                    </div>
                    <div style="font-size:0.67rem; color:#999;">{tip}</div>
                </div>
                """, unsafe_allow_html=True)

        pm1, pm2 = st.columns(2)
        with pm1:
            st.metric("🕐 Best Posting Time", result.get("best_posting_time", "—"))
        with pm2:
            st.metric("👆 Predicted 'See More' CTR", result.get("predicted_ctr", "—"))

        # 5 Power Rewrites
        st.markdown("---")
        st.markdown("### ✍️ 5 Power-Rewritten Hooks")
        st.caption("Each uses a different proven technique. Pick your favorite and swap your hook.")

        rewrites = result.get("rewrites", [])
        for i, rw in enumerate(rewrites):
            label_rw  = rw.get("label", f"Rewrite {i+1}")
            hook_text = rw.get("hook", "")
            rw_chars  = len(hook_text)
            fits      = "✅" if rw_chars <= 210 else "⚠️ slightly over"

            with st.expander(f"**{i+1}. {label_rw}** — {rw_chars} chars {fits}", expanded=(i == 0)):
                rw_c1, rw_c2 = st.columns([0.55, 0.45])
                with rw_c1:
                    st.markdown(f"> {hook_text.replace(chr(10), '  \n> ')}")
                    copy_to_clipboard_button(hook_text, f"📋 Copy Rewrite {i+1}", key=f"hook_rw_copy_{i}")
                with rw_c2:
                    rw_init = (author_name[0] if author_name else "Y").upper()
                    st.markdown(f"""
                    <div class="hook-preview-card" style="font-size:0.82rem;">
                        <div class="hook-preview-header">
                            <div class="hook-preview-avatar" style="width:32px;height:32px;font-size:0.82rem;">{rw_init}</div>
                            <div>
                                <div class="hook-preview-name" style="font-size:0.8rem;">{author_name}</div>
                                <div class="hook-preview-title" style="font-size:0.68rem;">Your Headline · Just now</div>
                            </div>
                        </div>
                        <div class="hook-preview-text" style="font-size:0.82rem;">
                            {hook_text.replace(chr(10), "<br>")}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                if st.button(f"💾 Save to Post Library", key=f"save_hook_rw_{i}"):
                    save_to_library(hook_text, "🔥 Hook Analyzer",
                                    tags=["hook", label_rw.lower().replace(" ", "-")])
                    st.success("✅ Saved to Post Library!")

        st.markdown("---")
        if st.button("💾 Save Full Analysis Summary to Library", type="primary", key="save_hook_full"):
            summary = (
                f"[Hook Score: {score}/100 — {score_label}]\n\n"
                f"Original Hook:\n{user_text[:210]}\n\n"
                f"Best Rewrite ({rewrites[0]['label'] if rewrites else ''}):\n"
                f"{rewrites[0]['hook'] if rewrites else ''}"
            )
            save_to_library(summary, "🔥 Hook Analyzer", score=score, tags=["analysis", "hook"])
            st.success("✅ Analysis saved to Post Library!")

    elif not analyze_btn:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem; color:#aaa;
                    border:2px dashed #D0E8FF; border-radius:12px; margin-top:1rem;">
            <div style="font-size:2.5rem;">🔥</div>
            <div style="font-weight:600; color:#888; margin-top:0.5rem;">Your hook analysis will appear here</div>
            <div style="font-size:0.8rem; margin-top:0.3rem;">Paste a post and click Analyze</div>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        Built with ❤️ using Streamlit · Gemini AI · Stability AI (SDXL) · Hugging Face<br>
        <em>Not affiliated with LinkedIn. No scraping. All content is AI-generated.</em>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 📚 POST LIBRARY — Dedicated Page (DB-backed)
# ─────────────────────────────────────────────
def render_post_library():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">Persistent · Filterable · Exportable</div>
        <h1>📚 Post Library</h1>
        <p>Every post you generate is automatically saved here — star, filter, and export in bulk</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Controls ──────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([1.2, 1, 0.8])
    with ctrl1:
        search = st.text_input("🔍 Search posts", placeholder="Type to filter…", key="lib_search")
    with ctrl2:
        # Build module list from DB (or fallback session)
        if _CORE_AVAILABLE:
            all_posts_for_modules = _db.get_posts()
        else:
            all_posts_for_modules = st.session_state.get("post_library", [])
        modules = ["All Modules"] + sorted({p["module"] for p in all_posts_for_modules})
        filter_module = st.selectbox("Filter by module", modules, key="lib_filter")
    with ctrl3:
        sort_label = st.selectbox(
            "Sort by",
            ["Newest first", "Oldest first", "Highest score", "Starred"],
            key="lib_sort",
        )

    sort_map = {
        "Newest first":  "newest",
        "Oldest first":  "oldest",
        "Highest score": "score",
        "Starred":       "starred",
    }

    # ── Fetch posts ───────────────────────────────────────────────────────────
    if _CORE_AVAILABLE:
        try:
            filtered = _db.get_posts(
                search=search,
                module=filter_module,
                sort=sort_map[sort_label],
            )
            stats = _db.get_stats()
            total_count = stats["total"]
        except Exception:
            st.error("⚠️ Could not load Post Library.")
            with st.expander("🔍 Details (for debugging)"):
                st.code(traceback.format_exc())
            return
    else:
        # Legacy session-state fallback
        library  = st.session_state.get("post_library", [])
        filtered = library.copy()
        if search:
            filtered = [p for p in filtered if search.lower() in p["content"].lower()]
        if filter_module != "All Modules":
            filtered = [p for p in filtered if p["module"] == filter_module]
        if sort_label == "Oldest first":
            filtered = list(reversed(filtered))
        elif sort_label == "Highest score":
            filtered = sorted(filtered, key=lambda x: x.get("score", 0), reverse=True)
        elif sort_label == "Starred":
            filtered = [p for p in filtered if p.get("starred")]
        total_count = len(library)
        scored = [p for p in library if p.get("score", 0) > 0]
        top_mod = (max({p["module"] for p in library},
                       key=lambda m: sum(1 for p in library if p["module"] == m)).split()[-1]
                   if library else "—")
        stats = {
            "total":      total_count,
            "starred":    sum(1 for p in library if p.get("starred")),
            "avg_score":  (sum(p["score"] for p in scored) // len(scored)) if scored else 0,
            "top_module": top_mod,
        }

    if total_count == 0:
        st.info(
            "📭 **Your library is empty.** Generate a post in any module and it will appear here "
            "automatically. Start with 🔥 **Viral Hook Analyzer** or 🚀 **Post Generator**."
        )
        return

    # ── Stats row ─────────────────────────────────────────────────────────────
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st.metric("📝 Total Posts", stats["total"])
    with sc2:
        st.metric("⭐ Starred", stats["starred"])
    with sc3:
        avg = stats["avg_score"]
        st.metric("📊 Avg Hook Score", f"{avg}/100" if avg else "N/A")
    with sc4:
        st.metric("🏆 Most Used", stats["top_module"])

    st.markdown(f"**Showing {len(filtered)} of {total_count} posts**")
    st.markdown("---")

    # ── Bulk export ───────────────────────────────────────────────────────────
    with st.expander("📤 Export Options"):
        ex1, ex2 = st.columns(2)
        all_text = ("\n\n" + "═" * 60 + "\n\n").join(
            f"[{p['created_at']}] {p['module']}\n\n{p['content']}" for p in filtered
        )
        with ex1:
            st.download_button(
                "⬇️ Download as .txt", data=all_text,
                file_name=f"linkedin_posts_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain", use_container_width=True,
            )
        with ex2:
            st.download_button(
                "⬇️ Download as .json", data=json.dumps(filtered, indent=2),
                file_name=f"linkedin_posts_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json", use_container_width=True,
            )

    if not filtered:
        st.warning("No posts match your filters.")
        return

    # ── Pagination (50 per page) ───────────────────────────────────────────────
    PAGE_SIZE = 50
    total_pages = max(1, (len(filtered) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = st.session_state.get("lib_page", 1)
    page = max(1, min(page, total_pages))

    if total_pages > 1:
        pg_cols = st.columns([1, 2, 1])
        with pg_cols[0]:
            if st.button("◀ Prev", disabled=(page == 1), key="lib_prev"):
                st.session_state["lib_page"] = page - 1
                st.rerun()
        with pg_cols[1]:
            st.markdown(
                f"<div style='text-align:center; padding:0.3rem; color:#555;'>Page {page} / {total_pages}</div>",
                unsafe_allow_html=True,
            )
        with pg_cols[2]:
            if st.button("Next ▶", disabled=(page == total_pages), key="lib_next"):
                st.session_state["lib_page"] = page + 1
                st.rerun()

    page_posts = filtered[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

    # ── Post cards ────────────────────────────────────────────────────────────
    for post in page_posts:
        score    = post.get("score", 0)
        starred  = post.get("starred", False)
        tags     = post.get("tags", [])
        tag_html = " ".join(f'<span class="tag">{t}</span>' for t in tags)
        score_str = f"🔥 {score}/100" if score > 0 else ""

        st.markdown(f"""
        <div class="post-card">
            <div class="post-card-meta">
                <span class="tag">{post['module']}</span>
                {tag_html}
                <span>{post['created_at']}</span>
                {'<span>⭐ Starred</span>' if starred else ''}
                {'<span style="color:#00c851;font-weight:700;">' + score_str + '</span>' if score_str else ''}
            </div>
            <div class="post-card-body">{post['content'][:380]}{'…' if len(post['content']) > 380 else ''}</div>
        </div>
        """, unsafe_allow_html=True)

        act1, act2, act3, act4, act5 = st.columns([1, 1, 1, 1, 0.4])
        with act1:
            copy_to_clipboard_button(post["content"], "📋 Copy", key=f"lib_cp_{post['id']}")
        with act2:
            star_label = "⭐ Unstar" if starred else "☆ Star"
            if st.button(star_label, key=f"lib_star_{post['id']}"):
                if _CORE_AVAILABLE:
                    _db.toggle_star(post["id"])
                else:
                    for item in st.session_state["post_library"]:
                        if item["id"] == post["id"]:
                            item["starred"] = not item["starred"]
                st.rerun()
        with act3:
            if st.button("🔥 Analyze Hook", key=f"lib_hook_{post['id']}"):
                st.session_state["hook_analyzer_input"] = post["content"]
                st.session_state["current_page"] = "🔥 Viral Hook Analyzer"
                st.rerun()
        with act4:
            st.download_button(
                "⬇️ Save", data=post["content"],
                file_name=f"post_{post['id']}.txt", mime="text/plain",
                key=f"lib_dl_{post['id']}",
            )
        with act5:
            if st.button("🗑️", key=f"lib_del_{post['id']}", help="Delete this post"):
                if _CORE_AVAILABLE:
                    _db.delete_post(post["id"])
                    # Sync session counter
                    st.session_state["session_posts_generated"] = max(
                        0, st.session_state.get("session_posts_generated", 1) - 1
                    )
                else:
                    st.session_state["post_library"] = [
                        p for p in st.session_state["post_library"] if p["id"] != post["id"]
                    ]
                st.rerun()

        st.markdown("<hr style='margin:0.4rem 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN APP ROUTER
# ─────────────────────────────────────────────
def main():
    """Main application entry point and page router."""
    # Warm up shared utility modules (safe here — Streamlit runtime is active)
    _prewarm_utils()
    init_session_state()
    selected_page = render_sidebar()

    # ── Page routing ──────────────────────────────────────────────────────────
    MODULE_MAP = {
        "🚀 Post Generator":    ("modules.post_generator",    "post_generator.py",    "render_post_generator"),
        "🔧 Post Optimizer":    ("modules.post_optimizer",    "post_optimizer.py",    "render_post_optimizer"),
        "💼 About Optimizer":   ("modules.about_optimizer",   "about_optimizer.py",   "render_about_optimizer"),
        "🌟 Profile Enhancer":  ("modules.profile_enhancer",  "profile_enhancer.py",  "render_profile_enhancer"),
        "💡 Content Ideas":     ("modules.content_ideas",     "content_ideas.py",     "render_content_ideas"),
        "🧠 Strategy Insights": ("modules.strategy_insights", "strategy_insights.py", "render_strategy_insights"),
        "🎨 Image Generator":   ("modules.image_generator",   "image_generator.py",   "render_image_generator"),
        "⚡ Engagement Toolkit":("modules.engagement_toolkit","engagement_toolkit.py","render_engagement_toolkit"),
    }

    if selected_page == "🏠 Home":
        render_home()
    elif selected_page == "🔥 Viral Hook Analyzer":
        render_viral_hook_analyzer()
    elif selected_page == "📚 Post Library":
        render_post_library()
    elif selected_page == "🗄️ Data Manager":
        try:
            dm = load_module("data_manager", "data_manager.py")
            dm.render_data_manager()
        except FileNotFoundError:
            st.error("⚠️ `data_manager.py` not found. Make sure it exists in your project root.")
        except Exception:
            st.error("⚠️ Something went wrong loading the Data Manager.")
            with st.expander("🔍 Details"):
                st.code(traceback.format_exc())
    elif selected_page in MODULE_MAP:
        mod_name, mod_file, render_fn = MODULE_MAP[selected_page]
        try:
            mod = load_module(mod_name, mod_file)
            getattr(mod, render_fn)()
        except FileNotFoundError:
            st.error(f"⚠️ Module file `{mod_file}` not found. Make sure it exists in your project root.")
            st.info("👈 Return to **Home** from the sidebar while you fix this.")
        except AttributeError:
            st.error(f"⚠️ `{render_fn}()` function not found in `{mod_file}`.")
        except Exception as e:
            st.error(f"⚠️ Failed to load **{selected_page}**: {e}")
            with st.expander("🔍 Full error details"):
                import traceback
                st.code(traceback.format_exc(), language="python")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()
