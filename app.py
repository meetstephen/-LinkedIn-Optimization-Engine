"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          LINKEDIN OPTIMIZATION ENGINE — Powered by Gemini AI + SDXL        ║
║  Full-stack Streamlit app for professional LinkedIn growth & content        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Modules:
  - Post Generator    : Gemini-powered viral post creation with frameworks
  - Post Optimizer    : Diagnosis + rewrite with engagement score
  - About Optimizer   : Personal brand story + keyword optimization
  - Profile Enhancer  : Beginner → PRO score and 30-day roadmap
  - Content Ideas     : Full content calendar by niche/pillar
  - Strategy Insights : Top creator tactics and growth playbooks
  - Image Generator   : Stability AI (primary) + Hugging Face (fallback)
  - Engagement Toolkit: Hooks, CTAs, hashtags, posting times

Author: LinkedIn Optimization Engine
Stack: Python · Streamlit · Gemini API · Stability AI · Hugging Face
"""

import streamlit as st
import sys
import os
import importlib.util

# ── Bulletproof module loader for Streamlit Cloud ──────────────────────────
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def load_module(module_name, relative_path):
    abs_path = os.path.join(APP_DIR, relative_path)
    spec = importlib.util.spec_from_file_location(module_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

# Pre-load utils so modules can import them
load_module("utils.gemini_client", "gemini_client.py")
load_module("utils.image_client",  "image_client.py")

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
    },
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

    /* ── Main Header ── */
    .main-header {
        background: linear-gradient(135deg, #0A66C2 0%, #004182 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(10,102,194,0.3);
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
    }
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(10,102,194,0.15);
        border-color: #0A66C2;
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
    # Keep last 20 only
    st.session_state["post_history"] = st.session_state["post_history"][:20]
    st.session_state["session_posts_generated"] += 1

# ─────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
def init_session_state():
    """Initialize all session state variables."""
    # Auto-load from environment variables / Streamlit secrets (production-ready)
    def _get_secret(env_key: str, fallback: str = "") -> str:
        """Check env vars first, then st.secrets, then fallback."""
        env_val = os.environ.get(env_key, "")
        if env_val:
            return env_val
        try:
            return st.secrets.get(env_key, fallback)
        except Exception:
            return fallback

    defaults = {
        "gemini_api_key":    _get_secret("GEMINI_API_KEY"),
        "stability_api_key": _get_secret("STABILITY_API_KEY"),
        "hf_api_key":        _get_secret("HF_API_KEY"),
        "last_generated_post": "",
        "current_page": "🏠 Home",
        # History & stats (new)
        "post_history": [],          # list of {type, content, timestamp}
        "session_posts_generated": 0,
        "session_minutes_saved": 0,
        "viral_analyzer_result": None,
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
            "🚀 Post Generator",
            "🔧 Post Optimizer",
            "💼 About Optimizer",
            "🌟 Profile Enhancer",
            "💡 Content Ideas",
            "🧠 Strategy Insights",
            "🎨 Image Generator",
            "⚡ Engagement Toolkit",
        ]
        selected_page = st.radio(
            "Navigate to",
            pages,
            index=pages.index(st.session_state.get("current_page", "🏠 Home")),
            label_visibility="collapsed",
        )
        st.session_state["current_page"] = selected_page

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
        posts_gen  = st.session_state.get("session_posts_generated", 0)
        mins_saved = posts_gen * 12   # avg 12 min saved per AI-generated post
        history_ct = len(st.session_state.get("post_history", []))
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
        <h1>🚀 LinkedIn Optimization Engine</h1>
        <p>AI-powered toolkit to transform your LinkedIn presence from beginner to thought leader</p>
    </div>
    """, unsafe_allow_html=True)

    # Stats row
    col1, col2, col3, col4 = st.columns(4)
    stats = [
        ("8", "Powerful Modules"),
        ("∞", "Post Variations"),
        ("100", "Profile Score"),
        ("3", "AI APIs"),
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

    # Feature cards grid
    st.markdown("### 🛠️ What Can You Do Today?")

    features = [
        ("🚀", "Post Generator", "Create viral posts with proven frameworks, hooks, and 2-3 variations per topic"),
        ("🔧", "Post Optimizer", "Get your existing posts diagnosed and rewritten with engagement scores"),
        ("💼", "About Optimizer", "Transform your About section into a personal brand story that gets found"),
        ("🌟", "Profile Enhancer", "Get your profile scored (0–100) and a 30-day transformation roadmap"),
        ("💡", "Content Ideas", "Generate a full content calendar with hooks, angles, and hashtags"),
        ("🧠", "Strategy Insights", "Reverse-engineered playbooks from top LinkedIn creators"),
        ("🎨", "Image Generator", "AI-generated professional visuals using SDXL and Hugging Face"),
        ("⚡", "Engagement Toolkit", "Hooks, CTAs, hashtag optimizer, and perfect posting times"),
    ]

    col_pairs = [features[i:i+4] for i in range(0, len(features), 4)]
    for row in col_pairs:
        cols = st.columns(4)
        for col, (icon, title, desc) in zip(cols, row):
            with col:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="icon">{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

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
        """)

    with step2:
        st.markdown("""
        **Step 2: Start with Your Profile** 🌟
        
        Go to **Profile Enhancer** to:
        - Get your LinkedIn profile scored
        - See exactly what's missing
        - Get a personalized 30-day roadmap
        
        Then use **About Optimizer** to transform your bio.
        """)

    with step3:
        st.markdown("""
        **Step 3: Create Consistent Content** 🚀
        
        Use **Content Ideas** to fill your content calendar, then:
        - **Post Generator** to write each post
        - **Image Generator** to create visuals
        - **Engagement Toolkit** for hooks, CTAs, hashtags
        
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
                            import json  # ← moved here, outside try block
                            try:
                                import google.generativeai as genai
                                genai.configure(api_key=st.session_state["gemini_api_key"])
                                model = genai.GenerativeModel("gemini-1.5-flash")

                                analysis_prompt = f"""You are a LinkedIn virality expert. Analyze this LinkedIn post and return ONLY a valid JSON object — no markdown, no explanation, no backticks.

POST TO ANALYZE:
\"\"\"
{post_to_analyze[:3000]}
\"\"\"

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

                        response = model.generate_content(analysis_prompt)
                        raw = response.text.strip()
                        # Strip markdown fences if present
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.startswith("json"):
                                raw = raw[4:]
                        
                        result = json.loads(raw.strip())
                        st.session_state["viral_analyzer_result"] = result
                    except json.JSONDecodeError:
                        st.error("⚠️ AI returned unexpected format. Try again.")
                        st.session_state["viral_analyzer_result"] = None
                    except Exception as e:
                        st.error(f"⚠️ Analysis failed: {str(e)[:120]}")
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
# MAIN APP ROUTER
# ─────────────────────────────────────────────
def main():
    """Main application entry point and page router."""
    init_session_state()
    selected_page = render_sidebar()

    # ── Page routing using importlib (Streamlit Cloud compatible) ─────────────
    MODULE_MAP = {
        "🏠 Home":              (None, None),
        "🚀 Post Generator":    ("modules.post_generator",   "post_generator.py",   "render_post_generator"),
        "🔧 Post Optimizer":    ("modules.post_optimizer",   "post_optimizer.py",   "render_post_optimizer"),
        "💼 About Optimizer":   ("modules.about_optimizer",  "about_optimizer.py",  "render_about_optimizer"),
        "🌟 Profile Enhancer":  ("modules.profile_enhancer", "profile_enhancer.py", "render_profile_enhancer"),
        "💡 Content Ideas":     ("modules.content_ideas",    "content_ideas.py",    "render_content_ideas"),
        "🧠 Strategy Insights": ("modules.strategy_insights","strategy_insights.py","render_strategy_insights"),
        "🎨 Image Generator":   ("modules.image_generator",  "image_generator.py",  "render_image_generator"),
        "⚡ Engagement Toolkit":("modules.engagement_toolkit","engagement_toolkit.py","render_engagement_toolkit"),
    }

    if selected_page == "🏠 Home":
        render_home()
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
