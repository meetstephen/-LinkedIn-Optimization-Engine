"""
Content Idea Generator — Generates a full content calendar and
post ideas by niche using proven LinkedIn content pillars.
"""
import streamlit as st
from utils.gemini_client import generate_text


CONTENT_PILLARS = {
    "Career Growth & Lessons": "Hard lessons, career pivots, promotions, setbacks, and growth",
    "Industry Insights & Trends": "What's changing in your field, predictions, news analysis",
    "Personal Stories (Vulnerability)": "Failures, imposter syndrome, real struggles and how you overcame them",
    "Contrarian / Hot Takes": "Unpopular opinions that challenge the status quo",
    "How-To & Tutorials": "Step-by-step guides, frameworks, tactics that deliver value",
    "Social Proof & Wins": "Milestones, results, testimonials, transformations (authentic, not braggy)",
    "Motivational / Mindset": "Beliefs, mindset shifts, daily practices, philosophy",
    "Behind the Scenes": "Day-in-the-life, building in public, processes, tools",
    "Collaboration & Community": "Tagging others, sharing insights from your network, Q&As",
}


def build_ideas_prompt(niche: str, role: str, pillars: list, count: int, timeframe: str) -> str:
    pillar_list = "\n".join([f"- {p}: {CONTENT_PILLARS[p]}" for p in pillars])
    return f"""You are a LinkedIn content strategist who has helped over 500 creators build million-impression content machines.

TASK: Generate {count} LinkedIn post IDEAS for the following creator.

CREATOR PROFILE:
- Niche: {niche}
- Role/Background: {role}
- Content Timeframe: {timeframe}
- Chosen Content Pillars:
{pillar_list}

For EACH idea, provide:
1. 💡 **Idea Title** (5–8 words, punchy)
2. 📐 **Content Pillar**: [which pillar]
3. 🪝 **Hook** (the exact opening line — scroll-stopping, max 2 lines)
4. 📝 **Post Angle** (2–3 sentences describing the approach/angle)
5. 📊 **Viral Potential**: [High/Medium] — [1-sentence reason]
6. 🏷️ **Key Hashtags** (3–5 relevant ones)

---

BONUS AT THE END:
- 3 EVERGREEN post ideas (that work any time, any week)
- 2 TRENDING angles based on what's hot in {niche} right now
- 1 PERSONAL BRAND anchor post they should write immediately

Organize by pillar for easy content calendar planning.
Format cleanly with clear separators between ideas.
"""


def render_content_ideas():
    """Renders the Content Idea Generator tab UI."""
    st.header("💡 Content Idea Generator")
    st.markdown("Generate a full content calendar with viral post ideas tailored to your niche.")

    col1, col2 = st.columns(2)

    with col1:
        niche = st.text_input(
            "🎯 Your Niche",
            placeholder="e.g., Product Management, Data Science, Sales Leadership",
        )
        role = st.text_input(
            "👤 Your Role/Background",
            placeholder="e.g., Senior PM at a fintech startup, 5 years experience",
        )
        count = st.slider("📊 Number of Ideas to Generate", min_value=5, max_value=20, value=10)

    with col2:
        timeframe = st.selectbox(
            "📅 Content Timeframe",
            ["1 Week", "2 Weeks", "1 Month", "3 Months (90-day plan)"],
        )
        pillars = st.multiselect(
            "🏛️ Content Pillars to Focus On",
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

        with st.spinner(f"Generating {count} killer content ideas for {niche}..."):
            try:
                prompt = build_ideas_prompt(niche, role, pillars, count, timeframe)
                result = generate_text(prompt, temperature=0.9, max_tokens=3000)

                st.success(f"✅ {count} content ideas generated!")
                st.markdown("---")

                # Download as text option
                st.download_button(
                    label="📥 Download Content Calendar",
                    data=result,
                    file_name=f"linkedin_content_ideas_{niche.replace(' ','_').lower()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

                st.markdown(result)

            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
