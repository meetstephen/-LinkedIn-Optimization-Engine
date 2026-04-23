"""
Engagement Toolkit — Hook generator, CTA generator, hashtag optimizer,
and posting time analyzer all in one.
"""
import streamlit as st
from utils.gemini_client import generate_text


POSTING_TIMES = {
    "North America (EST/PST)": {
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["7:00–9:00 AM EST", "12:00–1:00 PM EST", "5:00–6:00 PM EST"],
        "avoid": "Friday afternoon, Saturday, Sunday morning",
    },
    "Europe (GMT/CET)": {
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["7:00–9:00 AM CET", "12:00–2:00 PM CET", "6:00–8:00 PM CET"],
        "avoid": "Monday morning, Friday evening, weekends",
    },
    "Asia Pacific (SGT/AEST)": {
        "best_days": ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["8:00–10:00 AM SGT", "12:00–1:00 PM SGT", "7:00–9:00 PM SGT"],
        "avoid": "Monday morning, Friday afternoon",
    },
    "Middle East & Africa": {
        "best_days": ["Sunday", "Monday", "Tuesday"],
        "peak_times": ["8:00–10:00 AM GST", "1:00–3:00 PM GST"],
        "avoid": "Friday prayer times, weekends in GCC",
    },
    "Global / Mixed Audience": {
        "best_days": ["Tuesday", "Wednesday"],
        "peak_times": ["9:00 AM UTC", "1:00 PM UTC"],
        "avoid": "Weekends and major holidays",
    },
}


def build_hooks_prompt(topic: str, tone: str, count: int) -> str:
    return f"""You are the #1 LinkedIn hook writer. You've written hooks that generated millions of impressions.

Generate {count} KILLER hooks for this topic:

Topic: {topic}
Tone: {tone}

RULES FOR EACH HOOK:
- Max 2 lines (ideally 1 line)
- Must make the reader STOP scrolling
- Use at least 3 different psychological triggers across all hooks:
  (curiosity gap, shock, controversy, FOMO, confession, bold claim, question, specificity)
- No generic openers like "I'm excited to share...", "Great news!", "In today's post..."
- Each hook must be COMPLETELY different in structure

For each hook, add: 🧠 Trigger Used: [name the psychological trigger]

Number them clearly 1 through {count}.
"""


def build_cta_prompt(post_context: str, cta_goal: str) -> str:
    return f"""You are a conversion copywriting expert specializing in LinkedIn engagement.

Generate 8 powerful CTAs for this LinkedIn post context:

Post Context: {post_context}
CTA Goal: {cta_goal}

Provide 8 CTAs organized in categories:

**QUESTION CTAs (invite comments):**
1. [CTA]
2. [CTA]

**ACTION CTAs (drive behavior):**
3. [CTA]
4. [CTA]

**SHARE CTAs (drive reshares):**
5. [CTA]
6. [CTA]

**SOFT CTAs (non-pushy):**
7. [CTA]
8. [CTA]

For each, add: 🎯 Best for: [when to use this CTA]
"""


def build_hashtag_prompt(post_content: str, industry: str) -> str:
    return f"""You are a LinkedIn SEO specialist who understands hashtag strategy deeply.

Analyze this post and create an optimal hashtag strategy:

Post Content: {post_content}
Industry: {industry}

Provide a TIERED hashtag strategy:

## TIER 1 — HIGH VOLUME (1M+ followers): [3 tags]
[hashtag] — [follower count estimate] — [reach potential]

## TIER 2 — MID VOLUME (100K–1M): [3 tags]  
[hashtag] — [follower count estimate] — [why include]

## TIER 3 — NICHE/TARGETED (10K–100K): [3 tags]
[hashtag] — [follower count estimate] — [precision targeting reason]

## FINAL RECOMMENDED SET:
The optimal 5–8 hashtags to use (in order to add them):
#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7

## HASHTAG STRATEGY NOTES:
[2–3 strategic insights specific to this post]
"""


def render_engagement_toolkit():
    """Renders the Engagement Toolkit tab UI."""
    st.header("⚡ Engagement Toolkit")
    st.markdown("Your complete toolkit for maximum LinkedIn engagement: hooks, CTAs, hashtags, and timing.")

    tab1, tab2, tab3, tab4 = st.tabs(["🪝 Hook Generator", "📢 CTA Generator", "#️⃣ Hashtag Optimizer", "⏰ Posting Times"])

    # ── TAB 1: HOOKS ──────────────────────────────────────────────────────────
    with tab1:
        st.subheader("🪝 Viral Hook Generator")
        st.markdown("Generate scroll-stopping opening lines using proven psychological triggers.")

        col1, col2 = st.columns(2)
        with col1:
            hook_topic = st.text_area(
                "📌 Topic / Post Idea",
                placeholder="e.g., I spent $50K on a startup that failed in 6 months",
                height=80,
                key="hook_topic",
            )
        with col2:
            hook_tone = st.selectbox(
                "🎭 Tone",
                ["Storytelling", "Shocking", "Inspirational", "Contrarian", "Educational", "Vulnerability"],
                key="hook_tone",
            )
            hook_count = st.slider("Number of Hooks", 5, 15, 8, key="hook_count")

        if st.button("⚡ Generate Hooks", type="primary", use_container_width=True, key="gen_hooks"):
            if not hook_topic.strip():
                st.error("Please enter a topic.")
            else:
                with st.spinner("Writing your scroll-stopping hooks..."):
                    try:
                        result = generate_text(
                            build_hooks_prompt(hook_topic, hook_tone, hook_count), temperature=0.95
                        )
                        st.success("✅ Hooks generated!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ── TAB 2: CTAs ───────────────────────────────────────────────────────────
    with tab2:
        st.subheader("📢 CTA Generator")
        st.markdown("Create compelling calls-to-action that drive comments, saves, and shares.")

        col1, col2 = st.columns(2)
        with col1:
            cta_context = st.text_area(
                "📝 Post Topic/Context",
                placeholder="e.g., A post about 5 lessons from 10 years in software engineering",
                height=80,
                key="cta_context",
            )
        with col2:
            cta_goal = st.selectbox(
                "🎯 CTA Goal",
                ["Drive Comments", "Drive Shares/Reposts", "Generate DMs/Leads", "Build Community", "Get Profile Views"],
                key="cta_goal",
            )

        if st.button("⚡ Generate CTAs", type="primary", use_container_width=True, key="gen_ctas"):
            if not cta_context.strip():
                st.error("Please enter your post context.")
            else:
                with st.spinner("Crafting high-converting CTAs..."):
                    try:
                        result = generate_text(
                            build_cta_prompt(cta_context, cta_goal), temperature=0.85
                        )
                        st.success("✅ CTAs generated!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ── TAB 3: HASHTAGS ───────────────────────────────────────────────────────
    with tab3:
        st.subheader("#️⃣ Hashtag Optimizer")
        st.markdown("Get a tiered hashtag strategy for maximum reach and targeting.")

        col1, col2 = st.columns(2)
        with col1:
            ht_content = st.text_area(
                "📝 Post Content or Topic",
                placeholder="Paste your post or describe your topic...",
                height=100,
                key="ht_content",
            )
        with col2:
            ht_industry = st.text_input(
                "🏢 Industry",
                placeholder="e.g., SaaS, Healthcare, Finance",
                key="ht_industry",
            )

        if st.button("🔍 Optimize Hashtags", type="primary", use_container_width=True, key="gen_hashtags"):
            if not ht_content.strip():
                st.error("Please enter post content or a topic.")
            else:
                with st.spinner("Analyzing hashtag strategy..."):
                    try:
                        result = generate_text(
                            build_hashtag_prompt(ht_content, ht_industry or "General"), temperature=0.7
                        )
                        st.success("✅ Hashtag strategy ready!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    # ── TAB 4: POSTING TIMES ─────────────────────────────────────────────────
    with tab4:
        st.subheader("⏰ Optimal Posting Times")
        st.markdown("Know exactly when to post for your audience's timezone to maximize first-hour engagement.")

        region = st.selectbox("🌍 Your Target Audience Region", list(POSTING_TIMES.keys()))
        data = POSTING_TIMES[region]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**✅ Best Days**")
            for day in data["best_days"]:
                st.markdown(f"• {day}")

        with col2:
            st.markdown("**⏰ Peak Times**")
            for time in data["peak_times"]:
                st.markdown(f"• {time}")

        with col3:
            st.markdown("**🚫 Avoid**")
            st.markdown(data["avoid"])

        st.markdown("---")
        st.markdown("""
**💡 Pro Posting Tips:**
- **Golden hour rule**: Reply to EVERY comment within 60 minutes of posting — this signals high engagement to LinkedIn's algorithm
- **Pre-warm strategy**: Comment on 5–10 relevant posts in the 30 min before you post (activates your network)  
- **Consistency beats frequency**: 3× per week consistently > 7× per week erratically
- **First comment trick**: Post your own comment (key takeaway or question) right after you publish to seed engagement
- **Don't edit immediately**: Wait 3+ hours before editing a post — edits can reset the algorithm's distribution
        """)
