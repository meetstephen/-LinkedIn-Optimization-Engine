"""
Content Idea Generator — Generates a full content calendar and
post ideas by niche using proven LinkedIn content pillars.
"""
import streamlit as st
from utils.gemini_client import generate_text, get_profile_context


CONTENT_PILLARS = {
    "Career Growth & Lessons":          "Hard lessons, career pivots, promotions, setbacks, and growth",
    "Industry Insights & Trends":       "What's changing in your field, predictions, news analysis",
    "Personal Stories (Vulnerability)": "Failures, imposter syndrome, real struggles and how you overcame them",
    "Contrarian / Hot Takes":           "Unpopular opinions that challenge the status quo",
    "How-To & Tutorials":               "Step-by-step guides, frameworks, tactics that deliver value",
    "Social Proof & Wins":              "Milestones, results, testimonials, transformations (authentic, not braggy)",
    "Motivational / Mindset":           "Beliefs, mindset shifts, daily practices, philosophy",
    "Behind the Scenes":                "Day-in-the-life, building in public, processes, tools",
    "Collaboration & Community":        "Tagging others, sharing insights from your network, Q&As",
}


def build_ideas_prompt(niche, role, pillars, count, timeframe):
    pillar_list = "\n".join([f"- {p}: {CONTENT_PILLARS[p]}" for p in pillars])
    profile_ctx = get_profile_context()
    return f"""You generate LinkedIn content ideas the way a sharp editor would — specific, usable, and grounded in how real people actually talk on LinkedIn.

Not generic. Not "share your journey". Real angles a real person in {niche} would actually post about.{profile_ctx}

CREATOR:
- Niche: {niche}
- Background: {role}
- Posting window: {timeframe}
- Pillars they want to use:
{pillar_list}

Generate {count} content ideas.

BANNED angles:
- "X lessons I learned from Y years in Z"
- Anything that starts with "I'm excited to..."
- Listicles titled "X things about [topic] that will change your life"
- Anything with the word "journey", "game-changer", or "hustle"

For each idea, give:

**[NUMBER]. [IDEA TITLE — 4–7 words, punchy, specific]**
Pillar: [which pillar]
Hook: [The exact first 1–2 lines they'd use to open the post. Scroll-stopping. No questions. No "I".]
Angle: [2 sentences on how to actually write this — what tension to create, what insight to land on]
Why it will perform: [1 specific reason based on LinkedIn psychology — not generic]
Hashtags: [3–5 specific ones]

---

After all {count} ideas, add:

**EVERGREEN PICKS (3 ideas that work any week of the year):** [just title + one-line reason]

**POST THIS WEEK:** [the single idea most likely to get traction right now in {niche}, and why]
"""


def render_content_ideas():
    st.header("💡 Content Idea Generator")
    st.markdown("Generate a full content calendar with real, usable post ideas tailored to your niche.")

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)

    with col1:
        niche = st.text_input(
            "🎯 Your Niche",
            value=st.session_state.get("ci_niche", _p.get("industry", "")),
            placeholder="e.g., Product Management, Data Science, Sales Leadership",
            key="ci_niche",
        )
        role  = st.text_input(
            "👤 Your Role/Background",
            value=st.session_state.get("ci_role", _p.get("role", "")),
            placeholder="e.g., Senior PM at a fintech startup, 5 years experience",
            key="ci_role",
        )
        count = st.slider("📊 Number of Ideas", min_value=5, max_value=20, value=10)

    with col2:
        timeframe = st.selectbox("📅 Content Timeframe", ["1 Week", "2 Weeks", "1 Month", "3 Months (90-day plan)"])
        pillars   = st.multiselect("🏛️ Content Pillars",
                                    list(CONTENT_PILLARS.keys()),
                                    default=["Career Growth & Lessons", "How-To & Tutorials", "Contrarian / Hot Takes"],
                                    max_selections=5)

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
                prompt = build_ideas_prompt(niche, role, pillars, count, timeframe)
                result = generate_text(prompt, temperature=0.88, max_tokens=3000)

                st.success(f"✅ {count} content ideas generated!")
                st.markdown("---")

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
