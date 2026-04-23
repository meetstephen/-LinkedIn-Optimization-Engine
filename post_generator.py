"""
Post Generator Module — Generates high-performing LinkedIn posts
using proven content frameworks powered by Gemini.
"""
import streamlit as st
from utils.gemini_client import generate_text


# ─── Tone descriptions ───────────────────────────────────────────────────────
TONE_DESCRIPTIONS = {
    "Inspirational": "motivational, uplifting, empowering — like a coach speaking to professionals",
    "Educational": "informative, structured, teaching-oriented — like a subject matter expert sharing wisdom",
    "Storytelling": "narrative-driven, personal, relatable — like sharing a real experience",
    "Contrarian": "thought-provoking, challenges assumptions — like a bold LinkedIn thought leader",
    "Data-Driven": "analytical, evidence-based, specific numbers and facts — like a researcher",
    "Conversational": "casual, authentic, approachable — like talking to a friend at a networking event",
    "Motivational": "high-energy, action-oriented, pushing people to take steps",
}

FRAMEWORK_DESCRIPTIONS = {
    "Hook → Story → Insight → CTA": "Start with a bold hook, tell a brief story, share the key insight, close with CTA",
    "Problem → Agitation → Solution": "Present a problem, amplify its pain, provide your unique solution",
    "Listicle (Numbered Tips)": "X things I learned / X mistakes I made / X tools that changed my work",
    "Before → After → Bridge": "Describe the before state, the after state, and how to bridge the gap",
    "Contrarian Statement": "State an unpopular opinion, defend it with evidence, invite debate",
    "Personal Story Arc": "Vulnerability → Struggle → Lesson → Takeaway",
}


def build_post_prompt(topic: str, niche: str, tone: str, framework: str, audience: str) -> str:
    tone_desc = TONE_DESCRIPTIONS.get(tone, tone)
    framework_desc = FRAMEWORK_DESCRIPTIONS.get(framework, framework)

    return f"""You are a top LinkedIn creator with 500K+ followers. Your posts consistently go viral because of your ability to craft engaging, human-centered content.

TASK: Write 2 high-performing LinkedIn post VARIATIONS on the following:

Topic: {topic}
Niche/Industry: {niche}
Target Audience: {audience}
Tone: {tone} — {tone_desc}
Framework: {framework} — {framework_desc}

STRICT FORMATTING RULES FOR EACH VARIATION:
1. START with a powerful, scroll-stopping HOOK (1–2 lines max, no emojis in hook)
2. Body: Short paragraphs (1–3 lines each). Use line breaks generously.
3. Include a personal insight or contrarian angle
4. Use 2–3 relevant emojis sparingly (not in hook)
5. End with a compelling CTA (question or action)
6. Add 5–8 relevant hashtags at the bottom
7. Keep total post under 300 words
8. Avoid corporate speak, jargon, or generic advice

OUTPUT FORMAT:
---VARIATION 1---
[Hook]

[Body with short paragraphs]

[CTA]

[Hashtags]

---VARIATION 2---
[Hook]

[Body with short paragraphs]

[CTA]

[Hashtags]

---ANALYSIS---
Hook strength: [Strong/Medium/Weak] — [brief reason]
Engagement prediction: [High/Medium/Low] — [brief reason]
Best variation: [1 or 2] — [brief reason]
"""


def render_post_generator():
    """Renders the Post Generator tab UI."""
    st.header("🚀 LinkedIn Post Generator")
    st.markdown("Generate scroll-stopping posts using proven viral frameworks powered by Gemini AI.")

    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_area(
            "📌 Topic / Main Idea",
            placeholder="e.g., 'I failed my first startup and learned these 3 lessons'",
            height=80,
        )
        niche = st.text_input(
            "🎯 Your Niche / Industry",
            placeholder="e.g., Tech, Marketing, Finance, HR, Coaching",
        )
        audience = st.text_input(
            "👥 Target Audience",
            placeholder="e.g., Early-career professionals, CTOs, Entrepreneurs",
            value="Professionals on LinkedIn",
        )

    with col2:
        tone = st.selectbox("🎭 Tone", list(TONE_DESCRIPTIONS.keys()))
        framework = st.selectbox("📐 Content Framework", list(FRAMEWORK_DESCRIPTIONS.keys()))

        st.info(f"**Framework:** {FRAMEWORK_DESCRIPTIONS[framework]}")

    st.markdown("---")

    if st.button("✨ Generate Post Variations", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a topic before generating.")
            return
        if not niche.strip():
            st.error("Please enter your niche/industry.")
            return

        with st.spinner("Crafting your viral LinkedIn posts..."):
            try:
                prompt = build_post_prompt(topic, niche, tone, framework, audience)
                result = generate_text(prompt, temperature=0.85)

                st.success("✅ Posts generated!")
                st.markdown("---")
                st.subheader("📝 Your Post Variations")

                # Display in expandable sections
                parts = result.split("---")
                for part in parts:
                    part = part.strip()
                    if part.startswith("VARIATION 1"):
                        with st.expander("📄 Variation 1", expanded=True):
                            content = part.replace("VARIATION 1", "").strip()
                            st.markdown(content)
                            if st.button("📋 Copy Variation 1", key="copy_v1"):
                                st.code(content)
                    elif part.startswith("VARIATION 2"):
                        with st.expander("📄 Variation 2", expanded=True):
                            content = part.replace("VARIATION 2", "").strip()
                            st.markdown(content)
                            if st.button("📋 Copy Variation 2", key="copy_v2"):
                                st.code(content)
                    elif part.startswith("ANALYSIS"):
                        with st.expander("📊 AI Analysis", expanded=True):
                            st.markdown(part.replace("ANALYSIS", "").strip())

                # Save last post to session for image generation
                st.session_state["last_generated_post"] = result

            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
