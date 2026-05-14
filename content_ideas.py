"""
Content Idea Generator — Generates a full content calendar and
post ideas by niche using proven LinkedIn content pillars.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context
from industry_profiles import get_industry_voice_block


CONTENT_PILLARS = {
    "Career Growth & Lessons":          "Hard lessons, career pivots, promotions, setbacks, and growth",
    "Industry Insights & Trends":       "What's changing in your field, predictions, news analysis",
    "Personal Stories (Vulnerability)": "Failures, imposter syndrome, real struggles and how you overcame them",
    "Contrarian / Hot Takes":           "Unpopular opinions that challenge the status quo in your field",
    "How-To & Tutorials":               "Step-by-step guides, frameworks, tactics that deliver real value",
    "Social Proof & Wins":              "Milestones, results, client outcomes — authentic, not braggy",
    "Motivational / Mindset":           "Beliefs, mindset shifts, daily practices — grounded in your experience",
    "Behind the Scenes":                "Day-in-the-life, building in public, tools, processes, decisions",
    "Collaboration & Community":        "Tagging others, sharing insights from your network, Q&As",
}

_BANNED_IDEAS = """
BANNED content angles:
- "X lessons I learned from Y years in Z" (overused title structure)
- Anything starting with "I'm excited to..."
- "X things about [topic] that will change your life"
- "Journey", "game-changer", "hustle", "crush it", "level up"
- Generic inspiration without a specific story or number behind it
"""


def build_ideas_prompt(niche, role, pillars, count, timeframe):
    pillar_list    = "\n".join([f"- {p}: {CONTENT_PILLARS[p]}" for p in pillars])
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche)
    return f"""You generate LinkedIn content ideas the way a sharp editor would — specific, usable, and grounded in how real practitioners actually talk about their work.

Not generic. Not "share your journey". Real angles a real {niche} professional would actually post.{profile_ctx}
{industry_voice}

CREATOR:
- Niche: {niche}
- Background: {role}
- Posting window: {timeframe}
- Content pillars to use:
{pillar_list}

{_BANNED_IDEAS}

Generate {count} content ideas.

For each idea:

**[NUMBER]. [IDEA TITLE — 5-8 words, punchy and specific]**
Pillar: [which pillar]
Hook: [The exact first 1-2 lines to open the post. No questions. Does not start with "I". Scroll-stopping.]
Angle: [2 sentences — the specific tension to create and the insight to land on. Name any real Nigerian institution, regulation, or data point that would make this credible.]
Why it will perform: [1 specific reason tied to LinkedIn psychology — not generic]
Hashtags: [3-5 specific ones including at least 1 Nigeria-specific if Nigerian mode active]

---

After all {count} ideas, add:

**EVERGREEN PICKS (3 ideas that work any week):**
[Title + one-line reason why it stays relevant]

**POST THIS WEEK:**
[The single idea most likely to get traction RIGHT NOW in {niche}, and the specific reason why this week.]
"""


def render_content_ideas():
    st.header("💡 Content Idea Generator")
    st.markdown("Generate a full content calendar with real, usable post ideas tailored to your niche.")

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)

    with col1:
        niche = st.text_input(
            "🎯 Your Niche / Industry",
            value=st.session_state.get("ci_niche", _p.get("industry", "")),
            placeholder="e.g., Legal Practice, Fintech, Real Estate, Oil & Gas",
            key="ci_niche",
        )
        role  = st.text_input(
            "👤 Your Role / Background",
            value=st.session_state.get("ci_role", _p.get("role", "")),
            placeholder="e.g., Corporate lawyer, 8 years, Lagos-based",
            key="ci_role",
        )
        count = st.slider("📊 Number of Ideas", min_value=5, max_value=20, value=10)

    with col2:
        timeframe = st.selectbox("📅 Content Timeframe",
                                  ["1 Week", "2 Weeks", "1 Month", "3 Months (90-day plan)"])
        pillars   = st.multiselect(
            "🏛️ Content Pillars (pick up to 5)",
            list(CONTENT_PILLARS.keys()),
            default=["Career Growth & Lessons", "How-To & Tutorials", "Contrarian / Hot Takes"],
            max_selections=5,
        )

    if pillars:
        st.markdown("**Selected Pillars:**")
        for p in pillars:
            st.caption(f"• **{p}**: {CONTENT_PILLARS[p]}")

    st.markdown("---")

    if st.button("🚀 Generate Content Ideas", type="primary", use_container_width=True):
        if not niche.strip():
            st.error("Please enter your niche.")
            return
        if not pillars:
            st.error("Please select at least one content pillar.")
            return

        with st.spinner(f"Building {count} content ideas for {niche}..."):
            try:
                result = generate_text(
                    build_ideas_prompt(niche, role, pillars, count, timeframe),
                    temperature=0.88, max_tokens=8000,
                )
                st.success(f"{count} content ideas generated!")
                st.markdown("---")

                st.download_button(
                    label="📥 Download Content Calendar",
                    data=result,
                    file_name=f"content_ideas_{niche.replace(' ', '_').lower()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

                st.markdown(result)

            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
                with st.expander("Error details"):
                    import traceback as _tb
                    st.code(_tb.format_exc())
