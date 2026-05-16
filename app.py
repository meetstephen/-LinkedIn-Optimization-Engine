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
    # Register core.db into sys.modules so library.py can reach it
    if _CORE_AVAILABLE and "core.db" not in sys.modules:
        try:
            from core import db as _cdb
            sys.modules["core.db"] = _cdb
        except Exception:
            pass

    for mod_name, rel_path in [
        ("gemini_client",    "gemini_client.py"),
        ("industry_profiles","industry_profiles.py"),
        ("library",          "library.py"),
        # legacy aliases kept for any old import paths
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
    page_title="LinkedEdge",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "LinkedEdge — AI-powered LinkedIn growth toolkit by LinkedIn Optimization Engine",
    }
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Professional dark-accent LinkedIn theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Root & Global ── */
    :root {
        --linkedin-blue: #0A66C2;
        --linkedin-dark: #004182;
        --linkedin-light: #EAF4FF;
        --accent-green: #00c851;
        --accent-orange: #FF6B35;
        --text-muted: #666;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A66C2 0%, #004182 100%);
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 3px 0;
        display: block;
        transition: all 0.2s ease;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.25);
        transform: translateX(4px);
    }
    /* ── Sidebar inputs & selects — keep legible on blue background ── */
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stTextInput input::placeholder,
    [data-testid="stSidebar"] .stTextArea textarea,
    [data-testid="stSidebar"] .stTextArea textarea::placeholder {
        color: #1a1a1a !important;
        background: rgba(255,255,255,0.95) !important;
    }
    [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] div {
        color: #1a1a1a !important;
        background: rgba(255,255,255,0.95) !important;
    }

    /* ── Main Header ── */
    .main-header {
        background: linear-gradient(135deg, #0A66C2 0%, #004182 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(10,102,194,0.3);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: "";
        position: absolute;
        top: -60px; right: -60px;
        width: 200px; height: 200px;
        border-radius: 50%;
        background: rgba(255,255,255,0.05);
        pointer-events: none;
    }
    .main-header .v-badge {
        display: inline-block;
        background: rgba(255,255,255,0.18);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 0.6rem;
    }
    .main-header h1 {
        color: white !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }
    .main-header p {
        color: rgba(255,255,255,0.85) !important;
        font-size: 1.05rem !important;
        margin: 0.5rem 0 0 !important;
    }

    /* ── Feature Cards ── */
    .feature-card {
        background: white;
        border: 1px solid #E1E9F5;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        height: 100%;
        position: relative;
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(10,102,194,0.15);
        border-color: #0A66C2;
    }
    .feature-card .new-badge {
        position: absolute;
        top: 10px; right: 10px;
        background: #FF6B35;
        color: white;
        font-size: 0.6rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 2px 7px;
        border-radius: 10px;
    }
    .feature-card .icon {
        font-size: 2.5rem;
        margin-bottom: 0.75rem;
    }
    .feature-card h3 {
        color: #0A66C2;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
    }
    .feature-card p {
        color: #555;
        font-size: 0.88rem;
        margin: 0;
    }

    /* ── Hook Analyzer — mobile preview card ── */
    .hook-preview-card {
        background: white;
        border: 1px solid #E1E9F5;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .hook-preview-header {
        display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
    }
    .hook-preview-avatar {
        width: 40px; height: 40px; border-radius: 50%;
        background: linear-gradient(135deg, #0A66C2, #004182);
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 800; font-size: 1rem; flex-shrink: 0;
    }
    .hook-preview-name  { font-weight: 600; font-size: 0.88rem; color: #191919; }
    .hook-preview-title { font-size: 0.75rem; color: #666; }
    .hook-preview-text  { font-size: 0.88rem; color: #191919; line-height: 1.55; }
    .hook-see-more      { color: #0A66C2; font-size: 0.85rem; font-weight: 600; cursor: pointer; }

    /* ── Post Library cards ── */
    .post-card {
        background: white;
        border: 1px solid #E1E9F5;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        transition: box-shadow 0.2s;
    }
    .post-card:hover { box-shadow: 0 6px 20px rgba(10,102,194,0.12); }
    .post-card-meta {
        font-size: 0.72rem; color: #888;
        margin-bottom: 0.5rem;
        display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
    }
    .post-card-meta .tag {
        background: #EAF4FF; color: #0A66C2;
        padding: 2px 8px; border-radius: 10px; font-weight: 600;
    }
    .post-card-body {
        font-size: 0.88rem; color: #333;
        line-height: 1.55; white-space: pre-wrap;
    }

    /* ── Resume session banner ── */
    .resume-banner {
        background: linear-gradient(135deg, #e8f4ff 0%, #d0eaff 100%);
        border: 1px solid #b3d4f0;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        display: flex; align-items: center; gap: 1rem;
    }
    .resume-banner .rb-icon { font-size: 2rem; }
    .resume-banner h4 { color: #0A66C2; margin: 0; font-size: 0.95rem; font-weight: 700; }
    .resume-banner p  { color: #444; margin: 2px 0 0; font-size: 0.82rem; }

    /* ── Stat Cards ── */
    .stat-card {
        background: linear-gradient(135deg, #0A66C2, #004182);
        color: white;
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
    }
    .stat-card .number {
        font-size: 2rem;
        font-weight: 800;
    }
    .stat-card .label {
        font-size: 0.8rem;
        opacity: 0.85;
    }

    /* ── Section Headers ── */
    h1, h2, h3 { 
        color: #0A66C2 !important; 
    }
    
    /* ── Buttons ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0A66C2, #004182);
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(10,102,194,0.3);
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(10,102,194,0.4);
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        border: 1px solid #E1E9F5 !important;
        border-radius: 10px !important;
    }

    /* ── Input fields ── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1.5px solid #C7D9F5;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0A66C2;
        box-shadow: 0 0 0 2px rgba(10,102,194,0.15);
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: #F0F7FF;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #D0E8FF;
    }

    /* ── Success/Warning/Error boxes ── */
    .stSuccess, .stInfo, .stWarning, .stError {
        border-radius: 10px;
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #888;
        font-size: 0.8rem;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    }

    /* ── Hide only footer and hamburger menu — sidebar untouched ── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Viral Analyzer Score Bars ── */
    .score-bar-wrap {
        margin: 0.6rem 0;
    }
    .score-bar-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 3px;
    }
    .score-bar-bg {
        background: #E1E9F5;
        border-radius: 99px;
        height: 10px;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 99px;
        transition: width 0.8s ease;
    }
    .viral-panel {
        background: #F8FBFF;
        border: 1.5px solid #C7D9F5;
        border-radius: 14px;
        padding: 1.5rem;
        margin-top: 1rem;
    }
    .viral-score-circle {
        width: 90px; height: 90px;
        border-radius: 50%;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        font-weight: 800; color: white;
        margin: 0 auto 1rem auto;
        font-size: 1.8rem;
        box-shadow: 0 4px 16px rgba(10,102,194,0.3);
    }
    .copy-btn-wrap {
        display: flex;
        gap: 8px;
        margin-top: 0.5rem;
    }
    /* ── Quick action badge ── */
    .badge-new {
        background: #FF6B35;
        color: white;
        font-size: 0.65rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 99px;
        vertical-align: middle;
        margin-left: 6px;
        letter-spacing: 0.5px;
    }

    /* ── Tab styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #EAF4FF;
        border-bottom: 3px solid #0A66C2;
    }

    /* ══════════════════════════════════════════════════════════════
       TEXT VISIBILITY FIX — force dark text on all main-area whites
       The sidebar's "* { color: white !important }" can bleed into
       Streamlit's shared component layer, making text invisible on
       white/light tiles. Every rule below locks dark text on the
       main content pane only.
    ══════════════════════════════════════════════════════════════ */

    /* ── Global main area text ── */
    .main .block-container,
    .main .block-container p,
    .main .block-container span,
    .main .block-container li,
    .main .block-container label,
    .main .block-container div,
    section[data-testid="stMain"] p,
    section[data-testid="stMain"] span,
    section[data-testid="stMain"] label,
    section[data-testid="stMain"] li,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] strong,
    [data-testid="stMarkdownContainer"] em,
    [data-testid="stMarkdownContainer"] td,
    [data-testid="stMarkdownContainer"] th {
        color: #1a1a1a !important;
    }

    /* ── Headings in main area ── */
    section[data-testid="stMain"] h1,
    section[data-testid="stMain"] h2,
    section[data-testid="stMain"] h3,
    section[data-testid="stMain"] h4,
    section[data-testid="stMain"] h5,
    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4 {
        color: #0A66C2 !important;
    }

    /* ── Metric tiles ── */
    [data-testid="stMetric"] {
        background: #F0F7FF !important;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #D0E8FF;
    }
    [data-testid="stMetric"] label,
    [data-testid="stMetric"] [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricLabel"] span {
        color: #444 !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div,
    [data-testid="stMetricValue"] span {
        color: #0A66C2 !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] span {
        color: #444 !important;
    }

    /* ── Expander header & body ── */
    [data-testid="stExpander"] {
        border: 1px solid #E1E9F5 !important;
        border-radius: 10px !important;
        background: #ffffff !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary svg {
        color: #1a1a1a !important;
    }
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] strong {
        color: #1a1a1a !important;
    }

    /* ── Alert / info / success / warning / error boxes ── */
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span,
    [data-testid="stAlert"] li,
    [data-testid="stAlert"] strong,
    [data-testid="stNotification"] p,
    [data-testid="stNotification"] span,
    .stAlert p, .stAlert span, .stAlert li,
    .element-container .stSuccess p,
    .element-container .stInfo p,
    .element-container .stWarning p,
    .element-container .stError p {
        color: #1a1a1a !important;
    }

    /* ── Input fields — text typed by user ── */
    .stTextInput > div > div > input {
        color: #1a1a1a !important;
        background: #ffffff !important;
        border-radius: 8px;
        border: 1.5px solid #C7D9F5;
    }
    .stTextArea > div > div > textarea {
        color: #1a1a1a !important;
        background: #ffffff !important;
        border-radius: 8px;
        border: 1.5px solid #C7D9F5;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #0A66C2 !important;
        box-shadow: 0 0 0 2px rgba(10,102,194,0.15);
    }

    /* ── Selectbox / dropdown ── */
    [data-testid="stSelectbox"] div[data-baseweb="select"] div,
    [data-testid="stSelectbox"] div[data-baseweb="select"] span,
    [data-testid="stSelectbox"] > label,
    [data-testid="stSelectbox"] > label p {
        color: #1a1a1a !important;
    }

    /* ── Radio buttons ── */
    [data-testid="stRadio"] > label,
    [data-testid="stRadio"] > label p,
    [data-testid="stRadio"] div[role="radiogroup"] label,
    [data-testid="stRadio"] div[role="radiogroup"] p,
    [data-testid="stRadio"] div[role="radiogroup"] span {
        color: #1a1a1a !important;
    }

    /* ── Checkbox ── */
    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] label p,
    [data-testid="stCheckbox"] label span {
        color: #1a1a1a !important;
    }

    /* ── Slider labels ── */
    [data-testid="stSlider"] label,
    [data-testid="stSlider"] label p,
    [data-testid="stSlider"] div[data-testid="stTickBarMin"],
    [data-testid="stSlider"] div[data-testid="stTickBarMax"] {
        color: #1a1a1a !important;
    }

    /* ── Number input ── */
    [data-testid="stNumberInput"] label,
    [data-testid="stNumberInput"] label p,
    [data-testid="stNumberInput"] input {
        color: #1a1a1a !important;
    }

    /* ── Multiselect ── */
    [data-testid="stMultiSelect"] label,
    [data-testid="stMultiSelect"] label p,
    [data-testid="stMultiSelect"] div[data-baseweb="tag"] span,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] div {
        color: #1a1a1a !important;
    }

    /* ── Dataframe / table ── */
    [data-testid="stDataFrame"] td,
    [data-testid="stDataFrame"] th,
    [data-testid="stTable"] td,
    [data-testid="stTable"] th {
        color: #1a1a1a !important;
        background: #ffffff !important;
    }

    /* ── Caption / small text ── */
    [data-testid="stCaptionContainer"] p,
    .stCaption p {
        color: #555 !important;
    }

    /* ── Tab labels ── */
    .stTabs [data-baseweb="tab"] p,
    .stTabs [data-baseweb="tab"] span {
        color: #1a1a1a !important;
    }
    .stTabs [aria-selected="true"] p,
    .stTabs [aria-selected="true"] span {
        color: #0A66C2 !important;
        font-weight: 700 !important;
    }

    /* ── Download button ── */
    [data-testid="stDownloadButton"] button p,
    [data-testid="stDownloadButton"] button span {
        color: #1a1a1a !important;
    }

    /* ── Code blocks ── */
    [data-testid="stCode"] code,
    .stCode code,
    pre, pre span, pre code {
        color: #1a1a1a !important;
        background: #f5f7fa !important;
    }

    /* ── Sidebar — keep white text, override everything above ── */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] li {
        color: white !important;
    }

    /* ── WAT window: re-override sidebar white-text rule with dark colours ── */
    /* These must come AFTER the sidebar rule to win the specificity battle    */
    [data-testid="stSidebar"] .wat-window {
        background: #1A3A5C !important;
        border-color: rgba(255,255,255,0.15) !important;
    }
    [data-testid="stSidebar"] .wat-window .slot {
        border-bottom-color: rgba(255,255,255,0.1) !important;
    }
    [data-testid="stSidebar"] .wat-window .slot .day {
        color: #7DD3FC !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .wat-window .slot .time-range {
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.78rem !important;
    }
    [data-testid="stSidebar"] .wat-window .slot .reach-badge {
        background: rgba(125,211,252,0.15) !important;
        color: #7DD3FC !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .wat-window .slot .reach-badge.hot {
        background: rgba(255,107,53,0.2) !important;
        color: #FFB347 !important;
    }

    /* ══════════════════════════════════════════════
       MOBILE RESPONSIVENESS — stack columns on small screens
    ══════════════════════════════════════════════ */
    @media (max-width: 768px) {
        /* Stack Streamlit columns vertically on mobile */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        [data-testid="column"] {
            width: 100% !important;
            flex: 0 0 100% !important;
            min-width: 100% !important;
        }
        /* Shrink the hero heading on mobile */
        .main-header h1 { font-size: 1.5rem !important; }
        .main-header p  { font-size: 0.9rem !important; }
        /* Tighten padding on mobile */
        .main-header { padding: 1.2rem !important; }
        .block-container { padding: 0.8rem !important; }
        /* Carousel slides stack nicely */
        .carousel-slide { margin-bottom: 1rem; }
        /* Dimension score cards on mobile */
        .viral-panel { padding: 0.9rem; }
    }

    /* ── WAT Clock / Posting Time Badge ── */
    .wat-badge {
        background: linear-gradient(135deg, #004182, #0A66C2);
        color: white;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        font-size: 0.82rem;
        margin-top: 0.5rem;
        text-align: center;
    }
    .wat-badge .wat-time {
        font-size: 1.4rem;
        font-weight: 900;
        letter-spacing: 1px;
    }
    .wat-badge .wat-label {
        font-size: 0.65rem;
        opacity: 0.75;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .wat-window {
        background: #F8FBFF;
        border: 1.5px solid #C7D9F5;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .wat-window .slot {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 0;
        border-bottom: 1px solid #E1E9F5;
        font-size: 0.85rem;
    }
    .wat-window .slot:last-child { border-bottom: none; }
    .wat-window .slot .day { font-weight: 700; color: #0A66C2; }
    .wat-window .slot .time-range { color: #444; }
    .wat-window .slot .reach-badge {
        background: #EAF4FF; color: #0A66C2;
        padding: 2px 8px; border-radius: 8px;
        font-size: 0.72rem; font-weight: 700;
    }
    .wat-window .slot .reach-badge.hot {
        background: #FFF0EA; color: #FF6B35;
    }

    /* ── Onboarding Wizard ── */
    .onboarding-wrap {
        background: linear-gradient(135deg, #EAF4FF 0%, #F0F7FF 100%);
        border: 2px solid #B3D4F0;
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 2rem;
    }
    .onboarding-step {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        padding: 1rem 0;
        border-bottom: 1px solid #D0E8FF;
    }
    .onboarding-step:last-child { border-bottom: none; padding-bottom: 0; }
    .step-circle {
        width: 36px; height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0A66C2, #004182);
        color: white;
        font-weight: 900;
        font-size: 1rem;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 2px 8px rgba(10,102,194,0.3);
    }
    .step-circle.done { background: linear-gradient(135deg, #00c851, #009d3e); }
    .step-body h4 { margin: 0 0 4px; color: #0A66C2; font-size: 0.95rem; }
    .step-body p  { margin: 0; color: #555; font-size: 0.82rem; }

    /* ── Nigerian Mode Badge ── */
    .ng-badge {
        display: inline-flex; align-items: center; gap: 5px;
        background: rgba(0,200,81,0.12);
        border: 1px solid rgba(0,200,81,0.35);
        color: #009d3e;
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }

    /* ══════════════════════════════════════════════
       CAROUSEL PLANNER
    ══════════════════════════════════════════════ */
    .carousel-slide-preview {
        background: white;
        border: 2px solid #0A66C2;
        border-radius: 14px;
        width: 100%;
        aspect-ratio: 1 / 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(10,102,194,0.12);
        position: relative;
        overflow: hidden;
    }
    .carousel-slide-preview .slide-number {
        position: absolute;
        top: 10px; right: 14px;
        font-size: 0.7rem;
        color: #aaa;
        font-weight: 700;
    }
    .carousel-slide-preview .slide-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0A66C2;
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }
    .carousel-slide-preview .slide-body {
        font-size: 0.82rem;
        color: #333;
        line-height: 1.5;
    }
    .carousel-slide-preview .slide-swipe {
        position: absolute;
        bottom: 10px;
        font-size: 0.68rem;
        color: #aaa;
        letter-spacing: 0.5px;
    }
    .carousel-nav-dots {
        display: flex;
        justify-content: center;
        gap: 6px;
        margin: 0.5rem 0;
    }
    .carousel-nav-dots .dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #C7D9F5;
    }
    .carousel-nav-dots .dot.active {
        background: #0A66C2;
        width: 20px;
        border-radius: 4px;
    }
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


def inject_profile_context() -> str:
    """
    Returns a formatted profile block to inject into any AI prompt.
    When the user has filled their profile, every module's AI output becomes
    personalised to their role, industry, audience, and voice automatically.
    Returns an empty string when no profile data exists (safe to concatenate).
    """
    p = st.session_state.get("user_profile", {})
    parts = []
    if p.get("name"):            parts.append(f"- Name: {p['name']}")
    if p.get("headline"):        parts.append(f"- LinkedIn Headline: {p['headline']}")
    if p.get("role"):            parts.append(f"- Current Role / Position: {p['role']}")
    if p.get("industry"):        parts.append(f"- Industry / Niche: {p['industry']}")
    if p.get("audience"):        parts.append(f"- Target Audience: {p['audience']}")
    if p.get("content_pillars"): parts.append(f"- Content Pillars: {', '.join(p['content_pillars'])}")
    if p.get("tone"):            parts.append(f"- Preferred Writing Tone: {p['tone']}")
    if p.get("voice_sample"):    parts.append(
        f"- Writing Voice Sample (match this style closely):\n\"\"\"\n{p['voice_sample'][:400].strip()}\n\"\"\""
    )
    if not parts:
        return ""

    base = (
        "\n\nUSER PROFILE — tailor ALL output specifically and concretely to this person. "
        "Use their industry, role, and audience in every example and suggestion:\n"
        + "\n".join(parts)
    )

    # ── Nigerian Professional Voice Mode ──────────────────────────────────────
    if st.session_state.get("nigerian_mode", False):
        base += """

NIGERIAN PROFESSIONAL VOICE MODE — ACTIVE:
You are writing for a Nigerian LinkedIn professional audience. Apply ALL of the following:

1. CULTURAL TONE: Warm, confident, community-oriented. Nigerian professionals value earned respect,
   resilience narratives, and collective uplift — not just personal wins.
2. LOCAL CONTEXT: Reference Nigerian business realities naturally — NAIRA pricing, Lagos traffic
   hustle, Abuja government contracting dynamics, power supply constraints, fintech disruption
   (e.g. Flutterwave, Paystack, Moniepoint), and telco penetration.
3. NIGERIAN INDUSTRIES: Ground examples in: fintech/banking, legal practice, oil & gas,
   agribusiness, real estate, healthcare, education-tech, government/civil service, media.
4. INSTITUTIONS: Reference where relevant — NCC, CBN, CAC, NBA (Nigerian Bar Association),
   SEC, NAFDAC, EFCC, Lagos State Government, federal MDAs.
5. UNIVERSITIES & CREDENTIALS: Mention Nigerian universities (UNILAG, OAU, Unilorin, ABSU)
   and professional certifications (ICAN, CIBN, NIM, CISA-NG, SAN) where fitting.
6. LANGUAGE FLAVOUR: Posts should FEEL written by a Nigerian professional — not a Silicon Valley
   content team. Use occasional Pidgin-inflected phrasing where culturally appropriate (e.g.
   "e no easy" in a story hook, "we move" as a CTA) — but keep it professional overall.
7. WAT TIME AWARENESS: Posting time advice must be in West Africa Time (WAT, UTC+1).
   Best windows for Nigerian LinkedIn: Tue & Thu 7-9am WAT, Wed 12-2pm WAT, Fri 6-8pm WAT.
8. AVOID: Silicon Valley jargon ("disrupting", "10x your growth"), dollar-centric examples,
   US-centric statistics or cultural references as primary examples."""

    return base


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
        # ── Persistent user profile — feeds every AI module ────────────────
        "user_profile": {
            "name": "",
            "headline": "",
            "role": "",
            "industry": "",
            "audience": "",
            "content_pillars": [],
            "tone": "Professional & Authoritative",
            "voice_sample": "",
        },
        # ── New v2.1 state ──────────────────────────────────────────────────
        "nigerian_mode":       True,   # ON by default for Nigerian audience
        "onboarding_complete": False,  # show 3-step wizard until dismissed
        "carousel_slides":     [],     # [{title, body, emoji}]
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
        <div style="text-align:center;padding:1.2rem 0.5rem 0.8rem;">
            <div style="display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;border-radius:14px;background:linear-gradient(135deg,rgba(255,255,255,0.28),rgba(255,255,255,0.10));border:1.5px solid rgba(255,255,255,0.3);font-size:1.8rem;margin-bottom:0.7rem;box-shadow:0 4px 16px rgba(0,0,0,0.15);">⚡</div>
            <div style="font-size:1.7rem;font-weight:900;letter-spacing:-0.5px;color:white;line-height:1;text-shadow:0 2px 8px rgba(0,0,0,0.2);">Linked<span style="color:#7DD3FC;text-shadow:0 0 20px rgba(125,211,252,0.5);">Edge</span></div>
            <div style="margin-top:5px;font-size:0.67rem;font-weight:600;letter-spacing:0.8px;text-transform:uppercase;color:rgba(255,255,255,0.6);">LinkedIn Optimization Engine</div>
            <div style="display:inline-block;margin-top:10px;background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:20px;padding:3px 12px;font-size:0.65rem;color:rgba(255,255,255,0.8);letter-spacing:0.3px;">AI-Powered · Production Ready</div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.15);margin:0 0 0.6rem 0;">
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("**📍 Navigation**")
        pages = [
            "🏠 Home",
            "🔥 Viral Hook Analyzer",
            "🚀 Post Generator",
            "🔧 Post Optimizer",
            "💼 About Optimizer",
            "🌟 Profile Enhancer",
            "💡 Content Ideas",
            "🧠 Strategy Insights",
            "🎨 Image Generator",
            "⚡ Engagement Toolkit",
            "🎠 Carousel Planner",
            "📚 Post Library",
        ]
        selected_page = st.radio(
            "Navigate to",
            pages,
            index=pages.index(st.session_state.get("current_page", "🏠 Home"))
                  if st.session_state.get("current_page", "🏠 Home") in pages else 0,
            label_visibility="collapsed",
            key="nav_radio",
        )
        st.session_state["current_page"] = selected_page

        st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        # ── User Profile — context for every AI module ────────────────────
        st.markdown("**👤 Your Profile**")
        _p = st.session_state.get("user_profile", {})
        _profile_complete = bool(_p.get("role") and _p.get("industry"))
        _badge = "✅ Profile Set" if _profile_complete else "⚙️ Set Up Profile"
        with st.expander(_badge, expanded=not _profile_complete):
            _name = st.text_input(
                "Your Name", value=_p.get("name", ""),
                placeholder="e.g. Stephen Chukwu", key="sp_name",
            )
            _headline = st.text_input(
                "LinkedIn Headline", value=_p.get("headline", ""),
                placeholder="e.g. AI Builder | Legal Tech Founder", key="sp_headline",
            )
            _role = st.text_input(
                "Current Role *", value=_p.get("role", ""),
                placeholder="e.g. Product Manager at Fintech", key="sp_role",
            )
            # ── Nigerian Industry Quickfill ────────────────────────────────
            NG_INDUSTRIES = [
                "Legal Practice (Nigeria)", "Fintech / Banking", "Oil & Gas",
                "Agribusiness", "Real Estate", "Healthcare", "EdTech",
                "Government / Civil Service", "Media & Communications", "Consulting",
            ]
            st.caption("🇳🇬 Quick-fill your industry:")
            _qf_cols = st.columns(2)
            for _qi, _qind in enumerate(NG_INDUSTRIES[:8]):
                with _qf_cols[_qi % 2]:
                    if st.button(_qind, key=f"qf_{_qi}", use_container_width=True):
                        st.session_state["_qf_industry"] = _qind
                        st.rerun()
            # Apply quickfill if triggered
            _qf_val = st.session_state.pop("_qf_industry", None)
            _industry_default = _qf_val if _qf_val else _p.get("industry", "")
            _industry = st.text_input(
                "Industry / Niche *", value=_industry_default,
                placeholder="e.g. Legal Tech, SaaS, Finance", key="sp_industry",
            )
            _audience = st.text_input(
                "Target Audience", value=_p.get("audience", ""),
                placeholder="e.g. Nigerian lawyers, startup founders", key="sp_audience",
            )
            _pillars_raw = st.text_input(
                "Content Pillars (comma-separated)",
                value=", ".join(_p.get("content_pillars", [])),
                placeholder="e.g. Leadership, AI, Career", key="sp_pillars",
            )
            _tone_opts = [
                "Professional & Authoritative", "Conversational & Warm",
                "Bold & Provocative", "Story-Driven", "Data-Led",
            ]
            _tone = st.selectbox(
                "Preferred Tone", _tone_opts,
                index=_tone_opts.index(_p.get("tone", "Professional & Authoritative"))
                      if _p.get("tone") in _tone_opts else 0,
                key="sp_tone",
            )
            _voice = st.text_area(
                "Voice Sample (optional)",
                value=_p.get("voice_sample", ""), height=70,
                placeholder="Paste 1-2 of your own LinkedIn posts — AI will match your authentic writing style...",
                key="sp_voice",
            )
            st.caption("* Required for personalised AI output")
            if st.button("💾 Save Profile", key="sp_save", use_container_width=True):
                _new_profile = {
                    "name":            _name.strip(),
                    "headline":        _headline.strip(),
                    "role":            _role.strip(),
                    "industry":        _industry.strip(),
                    "audience":        _audience.strip(),
                    "content_pillars": [x.strip() for x in _pillars_raw.split(",") if x.strip()],
                    "tone":            _tone,
                    "voice_sample":    _voice.strip(),
                }
                st.session_state["user_profile"] = _new_profile
                st.session_state["_profile_loaded"] = False  # force reload on next boot
                # Persist to Supabase so profile survives refresh & reboot
                _save_ok = False
                _save_err = ""
                try:
                    if _CORE_AVAILABLE:
                        _db.save_profile(
                            _new_profile,
                            onboarding_complete=st.session_state.get("onboarding_complete", False),
                            nigerian_mode=st.session_state.get("nigerian_mode", True),
                        )
                        _save_ok = True
                except Exception as _e:
                    _save_err = str(_e)

                if _save_ok:
                    st.success("✅ Profile saved — will persist across reboots.")
                elif _CORE_AVAILABLE:
                    st.error(f"⚠️ Saved in-session but Supabase failed: {_save_err}\n\nCheck your Supabase secrets and run the SQL migration if you haven't.")
                else:
                    st.info("💡 Saved in-session. Add Supabase credentials to persist across reboots.")
        if _profile_complete:
            _role_short = _p.get("role", "")[:32]
            _ind_short  = _p.get("industry", "")[:24]
            st.markdown(
                f"<div style='font-size:0.7rem;color:rgba(255,255,255,0.72);margin-top:-4px;margin-bottom:4px;'>"
                f"{'👤 ' + _p['name'] + ' · ' if _p.get('name') else ''}{_role_short}"
                f"{'<br>🏭 ' + _ind_short if _ind_short else ''}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        # ── 🇳🇬 Nigerian Professional Voice Mode ─────────────────────────
        st.markdown("**🇳🇬 Nigerian Voice Mode**")
        _ng_prev = st.session_state.get("nigerian_mode", True)
        _ng_on = st.toggle(
            "Activate Nigerian Context",
            value=_ng_prev,
            key="ng_mode_toggle",
            help="Makes all AI output sound like it was written by a Nigerian professional — Lagos culture, naira context, local institutions, WAT posting times.",
        )
        st.session_state["nigerian_mode"] = _ng_on
        # Only persist when value actually changed — avoids a Supabase write on every rerun
        if _ng_on != _ng_prev and _CORE_AVAILABLE and st.session_state.get("user_profile", {}).get("role"):
            try:
                _db.save_profile(
                    st.session_state["user_profile"],
                    onboarding_complete=st.session_state.get("onboarding_complete", False),
                    nigerian_mode=_ng_on,
                )
            except Exception:
                pass
        if _ng_on:
            st.markdown(
                "<div style='font-size:0.7rem;color:rgba(255,255,255,0.75);margin-top:-4px;'>"
                "🟢 Active — AI uses Lagos business culture, WAT times & Nigerian context"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='font-size:0.7rem;color:rgba(255,255,255,0.55);margin-top:-4px;'>"
                "⚪ Off — Generic global English mode"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr style='border-color:rgba(255,255,255,0.2);'>", unsafe_allow_html=True)

        # ── ⏰ WAT Posting Schedule ────────────────────────────────────────
        st.markdown("**⏰ Best Time to Post (WAT)**")
        from datetime import timezone, timedelta
        _wat_now = datetime.now(timezone(timedelta(hours=1)))
        _wat_str = _wat_now.strftime("%I:%M %p")
        _wat_day = _wat_now.strftime("%A")
        st.markdown(
            f"<div class='wat-badge'>"
            f"<div class='wat-label'>Current WAT Time</div>"
            f"<div class='wat-time'>{_wat_str}</div>"
            f"<div class='wat-label'>{_wat_day}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        _WAT_SLOTS = [
            ("Tue & Thu", "7:00 – 9:00 AM", "🔥 Peak"),
            ("Wednesday", "12:00 – 2:00 PM", "🔥 Peak"),
            ("Mon & Fri", "8:00 – 10:00 AM", "Good"),
            ("Friday",    "6:00 – 8:00 PM",  "Good"),
            ("Weekend",   "10:00 AM – 12 PM", "Moderate"),
        ]
        _slot_html = "".join(
            f"<div class='slot'><span class='day'>{d}</span>"
            f"<span class='time-range'>{t}</span>"
            f"<span class='reach-badge{' hot' if 'Peak' in r else ''}'>{r}</span></div>"
            for d, t, r in _WAT_SLOTS
        )
        st.markdown(
            f"<div class='wat-window'>{_slot_html}</div>",
            unsafe_allow_html=True,
        )
        st.caption("⏰ All times in West Africa Time (WAT, UTC+1)")

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
    _ng_active = st.session_state.get("nigerian_mode", False)
    _ng_suffix  = " — 🇳🇬 Nigerian Voice Active" if _ng_active else ""
    st.markdown(f"""
    <div class="main-header">
        <div class="v-badge">v2.1 · Production Ready{_ng_suffix}</div>
        <div style="font-size:3rem;font-weight:900;letter-spacing:-1px;color:white;line-height:1.05;margin:0.4rem 0 0.1rem;text-shadow:0 2px 12px rgba(0,0,0,0.2);">
            ⚡ Linked<span style="color:#7DD3FC;text-shadow:0 0 30px rgba(125,211,252,0.6);">Edge</span>
        </div>
        <div style="font-size:0.82rem;font-weight:600;letter-spacing:1.8px;text-transform:uppercase;color:rgba(255,255,255,0.55);margin-bottom:0.5rem;">LinkedIn Optimization Engine</div>
        <p>AI-powered toolkit to transform your LinkedIn presence from beginner to thought leader</p>
    </div>
    """, unsafe_allow_html=True)

    # ── 3-Step Onboarding Wizard (shown until dismissed) ─────────────────
    if not st.session_state.get("onboarding_complete", False):
        _p_ob = st.session_state.get("user_profile", {})
        _step1_done = bool(_p_ob.get("role") and _p_ob.get("industry"))
        _step2_done = st.session_state.get("session_posts_generated", 0) > 0
        _step3_done = st.session_state.get("hooks_analyzed", 0) > 0

        def _step_circle(done: bool, num: int) -> str:
            cls = "done" if done else ""
            icon = "✓" if done else str(num)
            return f"<div class='step-circle {cls}'>{icon}</div>"

        st.markdown(f"""
        <div class="onboarding-wrap">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem;">
                <div>
                    <h3 style="margin:0;color:#0A66C2;">👋 Welcome to LinkedEdge</h3>
                    <p style="margin:4px 0 0;color:#555;font-size:0.85rem;">
                        Complete these 3 steps to unlock personalised AI output for your profile.
                    </p>
                </div>
            </div>
            <div class="onboarding-step">
                {_step_circle(_step1_done, 1)}
                <div class="step-body">
                    <h4>{'✅ ' if _step1_done else ''}Set Up Your Profile</h4>
                    <p>Open the sidebar → <strong>Your Profile</strong>. Add your role, industry and audience.
                    Every AI module will instantly personalise output to you.</p>
                </div>
            </div>
            <div class="onboarding-step">
                {_step_circle(_step2_done, 2)}
                <div class="step-body">
                    <h4>{'✅ ' if _step2_done else ''}Generate Your First Post</h4>
                    <p>Go to <strong>🚀 Post Generator</strong> and create your first AI-powered LinkedIn post.
                    It auto-saves to your Post Library.</p>
                </div>
            </div>
            <div class="onboarding-step">
                {_step_circle(_step3_done, 3)}
                <div class="step-body">
                    <h4>{'✅ ' if _step3_done else ''}Analyse Your Hook</h4>
                    <p>Go to <strong>🔥 Viral Hook Analyzer</strong>. 90% of LinkedIn reach is won or lost
                    in your first 2 lines. Score and rewrite yours.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if _step1_done and _step2_done and _step3_done:
            if st.button("🎉 All steps done! Dismiss onboarding", type="primary", key="dismiss_onboarding"):
                st.session_state["onboarding_complete"] = True
                # Persist so it never shows again after reboot
                try:
                    if _CORE_AVAILABLE:
                        _db.save_profile(
                            st.session_state.get("user_profile", {}),
                            onboarding_complete=True,
                            nigerian_mode=st.session_state.get("nigerian_mode", True),
                        )
                except Exception:
                    pass
                st.rerun()
        else:
            st.caption("Complete all 3 steps to dismiss this guide. You can always find it by refreshing the page.")

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

    # Stats row — responsive HTML grid (safe on mobile, no st.columns collapse)
    st.markdown("""
<style>
.stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-bottom:1.2rem;}
@media(max-width:768px){.stat-grid{grid-template-columns:repeat(2,1fr);}}
</style>
<div class="stat-grid">
    <div class="stat-card"><div class="number">11</div><div class="label">Powerful Modules</div></div>
    <div class="stat-card"><div class="number">∞</div><div class="label">Post Variations</div></div>
    <div class="stat-card"><div class="number">100</div><div class="label">Profile Score</div></div>
    <div class="stat-card"><div class="number">3</div><div class="label">AI APIs</div></div>
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
        ("\u26a1", "Engagement Toolkit",      "Hooks, CTAs, hashtag optimizer, and WAT-aware posting times", False),
        ("\U0001f3a0", "Carousel Planner",    "Slide-by-slide text planner for LinkedIn carousels — 3&times; more reach than text posts", True),
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
.fc-card{background:#fff;border:1px solid #E1E9F5;border-radius:12px;padding:1.4rem 1rem;
         text-align:center;position:relative;box-shadow:0 2px 8px rgba(0,0,0,.06);
         transition:transform .2s,box-shadow .2s,border-color .2s;}
.fc-card:hover{transform:translateY(-4px);box-shadow:0 8px 24px rgba(10,102,194,.15);border-color:#0A66C2;}
.fc-new{position:absolute;top:10px;right:10px;background:#FF6B35;color:#fff;
        font-size:.6rem;font-weight:800;text-transform:uppercase;letter-spacing:.5px;
        padding:2px 7px;border-radius:10px;}
.fc-icon{font-size:2.2rem;margin-bottom:.5rem;display:block;}
.fc-title{color:#0A66C2;font-weight:700;margin:0 0 .4rem;font-size:.92rem;}
.fc-desc{color:#555;font-size:.82rem;margin:0;line-height:1.4;}
</style>
<div class="fc-grid">""" + _card_html + """</div>
""", unsafe_allow_html=True)


    # Getting started guide — responsive HTML grid (no st.columns collapse on mobile)
    st.markdown("---")
    st.markdown("### 🏁 Getting Started in 3 Steps")
    st.markdown("""
<style>
.gs-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.5rem;}
@media(max-width:768px){.gs-grid{grid-template-columns:1fr;}}
.gs-card{background:#F8FBFF;border:1.5px solid #C7D9F5;border-radius:12px;padding:1.4rem;}
.gs-card h4{color:#0A66C2;margin:0 0 0.5rem;font-size:0.95rem;}
.gs-card p,.gs-card li{color:#444;font-size:0.83rem;line-height:1.6;}
</style>
<div class="gs-grid">
<div class="gs-card">
  <h4>Step 1: Configure API Keys 🔑</h4>
  <p>Open the sidebar → <strong>Configure API Keys</strong>:</p>
  <ul>
    <li><strong>Gemini API</strong> (required): Free at aistudio.google.com</li>
    <li><strong>Stability AI</strong> (images): platform.stability.ai</li>
    <li><strong>Hugging Face</strong> (fallback): huggingface.co</li>
  </ul>
  <p><em>Pro tip: set GEMINI_API_KEY as an env variable — it loads automatically.</em></p>
</div>
<div class="gs-card">
  <h4>Step 2: Analyse Your Hooks 🔥</h4>
  <p>Start with <strong>Viral Hook Analyzer</strong>:</p>
  <ul>
    <li>Paste any post you've written</li>
    <li>Get a live hook score (0–100) across 5 dimensions</li>
    <li>Receive 5 power-rewritten alternatives</li>
    <li>Preview exactly how it looks on mobile</li>
  </ul>
  <p><em>90% of LinkedIn reach is won or lost in the first 2 lines.</em></p>
</div>
<div class="gs-card">
  <h4>Step 3: Create Consistent Content 🚀</h4>
  <p>Use <strong>Content Ideas</strong> to fill your calendar, then:</p>
  <ul>
    <li><strong>Post Generator</strong> to write each post</li>
    <li><strong>Carousel Planner</strong> for 3× reach slides</li>
    <li><strong>Engagement Toolkit</strong> for hooks, CTAs, hashtags</li>
    <li><strong>Post Library</strong> — everything auto-saved</li>
  </ul>
  <p>Post consistently <strong>3× per week</strong> for best results!</p>
</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.info("👈 **Select a module from the sidebar to get started.** Your profile is now active — every module uses it to personalise AI output for your role and industry.")

    # ── LinkedIn Health Dashboard ──────────────────────────────────────────
    st.markdown("### 📊 Your LinkedIn Health Dashboard")

    _p          = st.session_state.get("user_profile", {})
    _profile_ok = bool(_p.get("role") and _p.get("industry"))
    _posts_gen  = st.session_state.get("session_posts_generated", 0)
    _hooks_done = st.session_state.get("hooks_analyzed", 0)
    _lib_count  = (
        _db.get_stats()["total"] if _CORE_AVAILABLE
        else len(st.session_state.get("post_library", []))
    )
    _hook_result    = st.session_state.get("hook_analysis_result")
    _avg_hook_score = _hook_result.get("overall_score", 0) if _hook_result else 0

    # Weighted health score
    _health = (
        (25 if _profile_ok else 0)
        + min(_hooks_done * 10, 20)
        + min(_posts_gen * 5, 20)
        + min(_lib_count * 2, 15)
        + (20 if _avg_hook_score >= 70 else 10 if _avg_hook_score >= 40 else 0)
    )
    _h_color = "#00c851" if _health >= 70 else "#FF6B35" if _health >= 40 else "#e63946"
    _h_label = "🔥 Strong Presence" if _health >= 70 else "👍 Building Up" if _health >= 40 else "🚀 Just Getting Started"

    _hd1, _hd2, _hd3 = st.columns([0.22, 0.38, 0.40])

    with _hd1:
        st.markdown(f"""
        <div style="background:white;border:2px solid {_h_color};border-radius:16px;
                    padding:1.5rem 1rem;text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.06);">
            <div style="font-size:3rem;font-weight:900;color:{_h_color};line-height:1;">{_health}</div>
            <div style="font-size:0.7rem;color:#888;margin-top:4px;">out of 100</div>
            <div style="font-size:0.85rem;font-weight:700;color:{_h_color};margin-top:8px;">{_h_label}</div>
            <div style="font-size:0.68rem;color:#aaa;margin-top:4px;">LinkedIn Health Score</div>
        </div>
        """, unsafe_allow_html=True)

    with _hd2:
        st.markdown("**Profile Checklist**")
        _checks = [
            ("👤 Profile configured",   _profile_ok),
            ("🔥 Hook analyzed",        _hooks_done > 0),
            ("🚀 Posts generated",      _posts_gen > 0),
            ("📚 Library started",      _lib_count > 0),
            ("⚡ Hook quality ≥ 70",    _avg_hook_score >= 70),
        ]
        for _lbl, _done in _checks:
            st.markdown(f"{'✅' if _done else '⬜'} {_lbl}")

    with _hd3:
        st.markdown("**🎯 Your Top Actions**")
        _actions = []
        if not _profile_ok:
            _actions.append(("🔴", "**Complete your profile** in the sidebar — all AI output immediately improves"))
        if _hooks_done == 0:
            _actions.append(("🟠", "Run **Viral Hook Analyzer** on your best post to find what's working"))
        if _posts_gen == 0:
            _actions.append(("🟠", "Use **Post Generator** to create your first AI-powered LinkedIn post"))
        if _avg_hook_score > 0 and _avg_hook_score < 60:
            _actions.append(("🟡", "Hook scored below 60 — try one of the 5 power rewrites from the analyzer"))
        if not _actions:
            _actions.append(("🟢", "You're on track! Keep posting consistently — **3× per week** is the LinkedIn sweet spot"))
            _actions.append(("🟢", "Use **Content Ideas** to fill your next 30 days of content in one click"))
        for _dot, _action in _actions[:3]:
            st.markdown(f"{_dot} {_action}")

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

    # ── Hook Formula Bank ─────────────────────────────────────────────────────
    with st.expander("📖 Hook Formula Bank — 20 proven templates (click any to load into editor)"):
        _HOOK_BANK = {
            "🪤 Curiosity Gap": [
                "Nobody talks about [X]. Here's what they're missing:",
                "Most people think [common belief]. They're completely wrong.",
                "I spent [X years] doing [Y] before I discovered this:",
                "What [industry] won't tell you about [topic]:",
            ],
            "📊 Data & Stats": [
                "[X]% of [target audience] fail at [Y]. Here's why:",
                "I analyzed [X] [posts/profiles/companies]. This pattern shows up every time:",
                "In [timeframe], I went from [bad state] to [good state]. The numbers:",
            ],
            "📖 Story Opening": [
                "At [age], I [did something bold]. Nobody believed me.",
                "[Year]. I had [nothing/everything]. Then [event] changed everything.",
                "My [boss/mentor/client] told me I'd never [achieve X]. I proved them wrong.",
            ],
            "💥 Bold Claim": [
                "[Popular advice] is terrible advice. Here's what actually works:",
                "Stop doing [common thing]. It's silently killing your [career/results].",
                "The [industry] is lying to you about [topic]. Here's the truth:",
            ],
            "❓ Question Hook": [
                "What would you do if [challenging scenario]? Most people pick the wrong answer.",
                "Can you spot the mistake in this [post/resume/strategy]?",
                "How do the top [1%/performers] actually [achieve goal]? (Hint: not what you think.)",
            ],
        }
        for _cat, _templates in _HOOK_BANK.items():
            st.markdown(f"**{_cat}**")
            for _tmpl in _templates:
                _tc, _bc = st.columns([0.85, 0.15])
                with _tc:
                    st.markdown(
                        f"<div style='font-size:0.83rem;color:#444;padding:3px 0;'>{_tmpl}</div>",
                        unsafe_allow_html=True,
                    )
                with _bc:
                    if st.button("Use ↗", key=f"hb_{abs(hash(_tmpl))}", help="Load into editor"):
                        st.session_state["hook_analyzer_input"] = _tmpl
                        st.rerun()
            st.markdown("<div style='margin-bottom:0.3rem;'></div>", unsafe_allow_html=True)

    # ── Input + Live Preview ────────────────────────────────────────────────
    if not st.session_state.get("gemini_api_key"):
        st.error("🔑 **Gemini API key required.** Add it in the sidebar to unlock Hook Analysis.")
        st.stop()

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
            _profile_ctx = inject_profile_context()
            prompt = f"""You are a world-class LinkedIn content strategist. Analyze the hook/opening of this post.{_profile_ctx}

HOOK (first 210 chars — what LinkedIn shows before '…see more'):
\"\"\"{user_text[:210].strip()}\"\"\"

FULL POST (context only):
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

    # ── Export & Backup — always visible, not conditional on posts existing ──
    with st.expander("📤 Export & Backup", expanded=False):
        _ex_tabs = st.tabs(["⬇️ Export Posts", "🔄 Import / Restore"])
        with _ex_tabs[0]:
            if filtered:
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
                st.caption(f"Exporting {len(filtered)} post(s) matching current filters.")
            else:
                st.info("No posts to export yet. Generate some posts first!")
        with _ex_tabs[1]:
            st.info(
                "**Restore from a previous .json export:**\n\n"
                "Paste the contents of your downloaded `.json` file below and click **Import**."
            )
            _import_text = st.text_area("Paste JSON here", height=120, key="lib_import_json",
                                        placeholder='[{"content": "...", "module": "...", ...}, ...]')
            if st.button("📥 Import Posts", key="lib_import_btn", use_container_width=True):
                try:
                    _imported = json.loads(_import_text.strip())
                    if not isinstance(_imported, list):
                        st.error("Invalid format — expected a JSON array.")
                    else:
                        _count = 0
                        for _item in _imported:
                            _content = _item.get("content", "").strip()
                            _module  = _item.get("module", "Imported")
                            if _content:
                                save_to_library(_content, _module,
                                                score=_item.get("score", 0),
                                                tags=_item.get("tags", []))
                                _count += 1
                        st.success(f"✅ Imported {_count} post(s) successfully!")
                        st.rerun()
                except json.JSONDecodeError:
                    st.error("⚠️ Could not parse JSON. Make sure you pasted a valid .json export.")

    st.markdown("---")

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
# 🎠 CAROUSEL PLANNER — Slide-by-slide text planner
#
# LinkedIn carousels (PDFs) get 3× more reach than text posts.
# This module lets users plan each slide's title + body, preview
# them in a LinkedIn-style card, and generate AI-written content.
# ─────────────────────────────────────────────
def render_carousel_planner():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">3× More Reach Than Text Posts</div>
        <h1>🎠 LinkedIn Carousel Planner</h1>
        <p>Plan your carousel slide-by-slide, preview each frame, and generate AI copy — ready to turn into a PDF</p>
    </div>
    """, unsafe_allow_html=True)

    # Education strip
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**📊 Why Carousels?**\n\nLinkedIn carousels (multi-image PDFs) generate 3× more impressions than plain text. Each swipe is a dwell signal that the algorithm loves.")
    with c2:
        st.warning("**🎯 Best Carousel Structure**\n\nSlide 1: Bold hook claim. Slides 2–8: One insight each. Final slide: CTA + your offer. 6–10 slides is the sweet spot.")
    with c3:
        st.success("**🇳🇬 Nigerian Carousel Themes That Work**\n\nLegal rights explainers, fintech guides, hustle-to-success stories, 'X things I learnt' frameworks, and sector breakdowns.")

    st.markdown("---")

    if not st.session_state.get("gemini_api_key"):
        st.error("🔑 **Gemini API key required.** Add it in the sidebar to enable AI slide generation.")
        st.stop()

    # ── AI Topic Generator ────────────────────────────────────────────────
    with st.expander("🤖 Generate Carousel with AI", expanded=True):
        ai_topic = st.text_input(
            "Carousel topic",
            placeholder="e.g. '5 rights every Nigerian employee must know' or 'How Paystack changed Nigerian fintech'",
            key="carousel_ai_topic",
        )
        ai_slides_count = st.slider("Number of slides", 4, 12, 7, key="carousel_slide_count")
        ai_col1, ai_col2 = st.columns(2)
        with ai_col1:
            carousel_tone = st.selectbox(
                "Tone", ["Educational & Clear", "Inspirational", "Bold & Direct",
                         "Story-Driven", "Data-Led"], key="carousel_tone"
            )
        with ai_col2:
            carousel_cta = st.text_input(
                "CTA (last slide)", placeholder="e.g. Follow me for more | DM me 'LEGAL' for a free consult",
                key="carousel_cta"
            )

        if st.button("🤖 Generate Carousel Slides", type="primary",
                     disabled=not bool(ai_topic.strip()), key="carousel_gen_btn", use_container_width=True):
            _profile_ctx = inject_profile_context()
            prompt = f"""You are a world-class LinkedIn carousel content strategist.{_profile_ctx}

Create a {ai_slides_count}-slide LinkedIn carousel on: "{ai_topic}"
Tone: {carousel_tone}
Final slide CTA: {carousel_cta or 'Follow me for more insights like this.'}

Return ONLY a JSON array — no markdown, no backticks, no preamble:
[
  {{"slide": 1, "emoji": "🎯", "title": "<hook title ≤8 words>", "body": "<body text ≤40 words — punchy, single idea>"}},
  ...
  {{"slide": {ai_slides_count}, "emoji": "👇", "title": "<CTA title>", "body": "<CTA body with the specified CTA>"}}
]

Rules:
- Slide 1: Bold hook claim or curiosity-gap statement that makes people swipe
- Middle slides: ONE clear insight per slide — no padding
- Each title ≤8 words, each body ≤40 words
- Body text should feel written by a human professional, not a bot
- Last slide: compelling CTA with clear next action"""

            with st.spinner("🎠 Building your carousel…"):
                try:
                    if _CORE_AVAILABLE:
                        slides_data = _ai.generate_json(
                            prompt,
                            st.session_state["gemini_api_key"],
                            model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                            temperature=0.7,
                            max_tokens=2000,
                        )
                        if isinstance(slides_data, dict):
                            slides_data = list(slides_data.values())[0]
                    else:
                        from google import genai as _genai
                        from google.genai import types as _gtypes
                        _c = _genai.Client(api_key=st.session_state["gemini_api_key"])
                        _res = _c.models.generate_content(
                            model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                            contents=prompt,
                            config=_gtypes.GenerateContentConfig(temperature=0.7, max_output_tokens=2000),
                        )
                        raw = _res.text.strip()
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.startswith("json"): raw = raw[4:]
                        slides_data = json.loads(raw.strip())

                    if isinstance(slides_data, list) and slides_data:
                        st.session_state["carousel_slides"] = [
                            {
                                "title": s.get("title", f"Slide {s.get('slide', i+1)}"),
                                "body":  s.get("body", ""),
                                "emoji": s.get("emoji", "📌"),
                            }
                            for i, s in enumerate(slides_data)
                        ]
                        st.success(f"✅ {len(slides_data)} slides generated! Scroll down to preview and edit.")
                        st.rerun()
                    else:
                        st.error("⚠️ AI returned an unexpected format. Try again.")
                except Exception:
                    st.error("⚠️ Generation failed. Please try again.")
                    with st.expander("🔍 Details"):
                        st.code(traceback.format_exc())

    # ── Manual Slide Editor ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✏️ Slide Editor & Preview")

    slides = st.session_state.get("carousel_slides", [])

    # Add / remove buttons
    ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1, 1, 2])
    with ctrl_c1:
        if st.button("➕ Add Slide", key="carousel_add", use_container_width=True):
            st.session_state["carousel_slides"].append(
                {"title": f"Slide {len(slides)+1}", "body": "", "emoji": "📌"}
            )
            st.rerun()
    with ctrl_c2:
        if slides and st.button("➖ Remove Last", key="carousel_del", use_container_width=True):
            st.session_state["carousel_slides"].pop()
            st.rerun()
    with ctrl_c3:
        if slides:
            # Export all slides as plain text
            _export_text = "\n\n".join(
                f"── SLIDE {i+1} ──\n{s['emoji']} {s['title']}\n\n{s['body']}"
                for i, s in enumerate(slides)
            )
            st.download_button(
                "⬇️ Export All Slides (.txt)",
                data=_export_text,
                file_name=f"carousel_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="carousel_export",
            )

    if not slides:
        st.markdown("""
        <div style="text-align:center; padding:3rem 1rem; color:#aaa;
                    border:2px dashed #D0E8FF; border-radius:12px; margin-top:1rem;">
            <div style="font-size:2.5rem;">🎠</div>
            <div style="font-weight:600; color:#888; margin-top:0.5rem;">No slides yet</div>
            <div style="font-size:0.8rem; margin-top:0.3rem;">Use AI to generate or click ➕ Add Slide to start manually</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # Navigation dot indicator
    _dot_html = "".join(
        f"<div class='dot{'  active' if i == 0 else ''}'></div>" for i in range(len(slides))
    )
    st.markdown(
        f"<div class='carousel-nav-dots'>{_dot_html}</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"📎 {len(slides)} slides — swipe indicator shown above")

    # ── Slide cards: editor on left, preview on right ─────────────────────
    for i, slide in enumerate(slides):
        st.markdown(f"<div style='margin-top:1.2rem;'>", unsafe_allow_html=True)
        ed_col, pv_col = st.columns([1.1, 0.9])

        with ed_col:
            st.markdown(f"**Slide {i+1}**")
            new_emoji = st.text_input(
                "Emoji", value=slide.get("emoji", "📌"),
                key=f"cs_emoji_{i}", max_chars=4,
            )
            new_title = st.text_input(
                "Title (≤8 words)", value=slide.get("title", ""),
                placeholder=f"Slide {i+1} headline…", key=f"cs_title_{i}",
            )
            new_body = st.text_area(
                "Body (≤40 words)", value=slide.get("body", ""),
                height=100, placeholder="One clear insight per slide…",
                key=f"cs_body_{i}",
            )
            # Persist edits back to session state immediately
            st.session_state["carousel_slides"][i] = {
                "emoji": new_emoji, "title": new_title, "body": new_body
            }
            _body_words = len(new_body.split()) if new_body.strip() else 0
            if _body_words > 40:
                st.warning(f"⚠️ {_body_words} words — aim for ≤40 for best readability")
            else:
                st.caption(f"✅ {_body_words}/40 words")

        with pv_col:
            st.markdown("**Preview**")
            _swipe_hint = "Swipe →" if i < len(slides) - 1 else "Last slide"
            st.markdown(f"""
            <div class="carousel-slide-preview">
                <div class="slide-number">{i+1} / {len(slides)}</div>
                <div style="font-size:2rem;margin-bottom:0.4rem;">{new_emoji or '📌'}</div>
                <div class="slide-title">{new_title or 'Your title here'}</div>
                <div class="slide-body">{(new_body or 'Your insight here…').replace(chr(10), '<br>')}</div>
                <div class="slide-swipe">{_swipe_hint}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"💾 Save Slide {i+1} to Library", key=f"carousel_save_{i}"):
                _slide_content = f"[Carousel Slide {i+1}/{len(slides)}]\n\n{new_emoji} {new_title}\n\n{new_body}"
                save_to_library(_slide_content, "🎠 Carousel Planner",
                                tags=["carousel", f"slide-{i+1}"])
                st.success("✅ Saved to Post Library!")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:0.8rem 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

    # Save all slides at once
    st.markdown("---")
    if st.button("💾 Save Full Carousel to Post Library", type="primary",
                 use_container_width=True, key="carousel_save_all"):
        full_text = f"[LinkedIn Carousel — {len(slides)} slides]\n\n" + "\n\n".join(
            f"── Slide {i+1} ──\n{s['emoji']} {s['title']}\n\n{s['body']}"
            for i, s in enumerate(slides)
        )
        save_to_library(full_text, "🎠 Carousel Planner",
                        tags=["carousel", "full-carousel"])
        st.success(f"✅ Full {len(slides)}-slide carousel saved to Post Library!")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div class="footer">
        Built with ❤️ using Streamlit · Gemini AI · Stability AI (SDXL) · Hugging Face<br>
        <em>Not affiliated with LinkedIn. No scraping. All content is AI-generated.</em>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN APP ROUTER
# ─────────────────────────────────────────────
def main():
    """Main application entry point and page router."""

    # ── WebSocket keepalive ───────────────────────────────────────────────────
    # Streamlit 1.57 sanitises st.markdown scripts. The correct fix for
    # "keepalive ping timeout" on Streamlit Cloud is a .streamlit/config.toml:
    #   [server]
    #   maxUploadSize = 200
    # AND keeping renders frequent. We trigger a lightweight dummy read of
    # session state every run (Streamlit already does this; the real fix is
    # config.toml — see sidebar tips).
    # We still write a hidden div so user activity resets the 30s timer:
    st.markdown(
        "<div style='display:none' aria-hidden='true'>♻</div>",
        unsafe_allow_html=True,
    )

    # Warm up shared utility modules (safe here — Streamlit runtime is active)
    _prewarm_utils()
    init_session_state()
    # ── Cross-module navigation ───────────────────────────────────────────────
    # Pipeline buttons set st.session_state["_pending_nav"] = "🔧 Post Optimizer"
    # We honour it here BEFORE the radio renders so the correct page shows.
    _pending = st.session_state.pop("_pending_nav", None)
    if _pending and _pending in pages:
        st.session_state["current_page"] = _pending

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
    elif selected_page == "🎠 Carousel Planner":
        render_carousel_planner()
    elif selected_page == "📚 Post Library":
        render_post_library()
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
