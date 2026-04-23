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
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "gemini_api_key": "",
        "stability_api_key": "",
        "hf_api_key": "",
        "last_generated_post": "",
        "current_page": "🏠 Home",
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
    # Quick start CTA
    st.info("👈 **Select a module from the sidebar** to get started. Recommended first step: **Profile Enhancer** to see your current score!")

    # Footer
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
    if selected_page == "🏠 Home":
        render_home()

    elif selected_page == "🚀 Post Generator":
        mod = load_module("modules.post_generator", "post_generator.py")
        mod.render_post_generator()

    elif selected_page == "🔧 Post Optimizer":
        mod = load_module("modules.post_optimizer", "post_optimizer.py")
        mod.render_post_optimizer()

    elif selected_page == "💼 About Optimizer":
        mod = load_module("modules.about_optimizer", "about_optimizer.py")
        mod.render_about_optimizer()

    elif selected_page == "🌟 Profile Enhancer":
        mod = load_module("modules.profile_enhancer", "profile_enhancer.py")
        mod.render_profile_enhancer()

    elif selected_page == "💡 Content Ideas":
        mod = load_module("modules.content_ideas", "content_ideas.py")
        mod.render_content_ideas()

    elif selected_page == "🧠 Strategy Insights":
        mod = load_module("modules.strategy_insights", "strategy_insights.py")
        mod.render_strategy_insights()

    elif selected_page == "🎨 Image Generator":
        mod = load_module("modules.image_generator", "image_generator.py")
        mod.render_image_generator()

    elif selected_page == "⚡ Engagement Toolkit":
        mod = load_module("modules.engagement_toolkit", "engagement_toolkit.py")
        mod.render_engagement_toolkit()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()
