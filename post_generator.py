"""
Post Generator Module — Generates high-performing LinkedIn posts
using proven content frameworks powered by Gemini.
"""
import streamlit as st
from utils.gemini_client import generate_text, get_profile_context


TONE_DESCRIPTIONS = {
    "Inspirational":   "hopeful, grounded — a mentor talking to someone earlier in their journey",
    "Educational":     "clear, direct, generous — the smartest person in the room who never makes you feel dumb",
    "Storytelling":    "narrative-first, specific details, real tension — not a TED talk, a conversation",
    "Contrarian":      "calm confidence, not rage-bait — challenges assumptions without being arrogant",
    "Data-Driven":     "precise, crisp, lets the numbers do the talking — no fluff around the stats",
    "Conversational":  "like texting a smart friend — lowercase where natural, short sentences, real thoughts",
    "Motivational":    "honest energy, not toxic positivity — acknowledges the hard part before the push",
}

FRAMEWORK_DESCRIPTIONS = {
    "Hook → Story → Insight → CTA":  "Open mid-scene, tell what happened, extract the lesson, end with a question",
    "Problem → Agitation → Solution": "Name the pain clearly, make it feel real, offer a specific way out",
    "Listicle (Numbered Tips)":        "A number in the hook, tight actionable points, no padding",
    "Before → After → Bridge":        "Where you were, where you got to, the exact step that bridged the gap",
    "Contrarian Statement":            "One uncomfortable truth, defend it calmly, invite the pushback",
    "Personal Story Arc":              "Specific moment → what you felt → what you did → what you now know",
}

# Global voice rules injected into every post generation prompt
_VOICE_RULES = """
VOICE & STYLE RULES — follow these without exception:

1. BANNED WORDS & PHRASES — never write these:
   "game-changer", "game-changing", "dive in", "let's dive into", "in today's fast-paced world",
   "I'm excited to share", "I'm thrilled to announce", "leverage", "synergy", "actionable insights",
   "thought leader", "passionate about", "journey", "transformation", "crushing it",
   "hustle", "disrupt", "innovative", "cutting-edge", "best practices", "circle back",
   "touch base", "bandwidth", "move the needle", "at the end of the day", "it goes without saying",
   "needless to say", "in conclusion", "in summary", "I hope this finds you well"

2. HOOK RULES:
   - Never open with "I" as the first word
   - No questions as the hook (weak — everyone does it)
   - No emojis in the hook line
   - Must create a gap — reader has to keep going to close it
   - Under 12 words ideally

3. FORMATTING:
   - One idea per line
   - Blank line between every paragraph
   - Max 3 lines per paragraph
   - Never use bullet points with dashes (—) inside the post body
   - Numbered lists only when the number is part of the hook

4. SOUND HUMAN:
   - Incomplete sentences are fine if they hit harder that way
   - Use specifics: not "a lot of money" but "$47,000"
   - Not "many years" but "11 years"
   - Tension before resolution — don't rush to the lesson
   - One vulnerability moment per post minimum
   - Write like you're talking to one specific person, not an audience

5. CTA:
   - One question at the end, max
   - Must be genuinely curious, not a fake question
   - No "drop a comment below" or "hit the like button"
"""


def build_post_prompt(topic: str, niche: str, tone: str, framework: str, audience: str) -> str:
    tone_desc      = TONE_DESCRIPTIONS.get(tone, tone)
    framework_desc = FRAMEWORK_DESCRIPTIONS.get(framework, framework)
    profile_ctx    = get_profile_context()

    return f"""You write LinkedIn posts for a specific type of creator: someone who has real experience, has made real mistakes, and doesn't need to impress anyone. Their posts feel like they came from a person, not a content team.

WHAT YOU'RE WRITING:
- Topic: {topic}
- Niche: {niche}
- Audience: {audience}
- Tone: {tone} — {tone_desc}
- Framework: {framework} — {framework_desc}{profile_ctx}

Write 2 completely different post variations on this topic. Same message, different angle, different structure.

{_VOICE_RULES}

OUTPUT FORMAT — use exactly this, nothing else:

---VARIATION 1---
[The post. No label, no intro, just the post itself.]

---VARIATION 2---
[The post. Completely different structure from V1.]

---ANALYSIS---
Hook strength: [Strong/Medium/Weak] — [one specific sentence on why]
Which to post: [1 or 2] — [one specific sentence on why]
What to A/B test next time: [one specific thing]

Keep each post under 280 words. Every line should earn its place.
"""


def render_post_generator():
    st.header("🚀 LinkedIn Post Generator")
    st.markdown("Generate scroll-stopping posts using proven viral frameworks powered by Gemini AI.")

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_area(
            "📌 Topic / Main Idea",
            placeholder="e.g., 'I failed my first startup and learned these 3 lessons'",
            height=80,
        )
        niche = st.text_input(
            "🎯 Your Niche / Industry",
            value=st.session_state.get("pg_niche", _p.get("industry", "")),
            placeholder="e.g., Tech, Marketing, Finance, HR, Coaching",
            key="pg_niche",
        )
        audience = st.text_input(
            "👥 Target Audience",
            value=st.session_state.get("pg_audience", _p.get("audience", "") or "Professionals on LinkedIn"),
            placeholder="e.g., Early-career professionals, CTOs, Entrepreneurs",
            key="pg_audience",
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

        with st.spinner("Writing your posts..."):
            try:
                prompt = build_post_prompt(topic, niche, tone, framework, audience)
                result = generate_text(prompt, temperature=0.88)

                # Parse and persist variations so pipeline buttons survive reruns
                var1 = var2 = analysis = ""
                parts = result.split("---")
                for part in parts:
                    part = part.strip()
                    if part.startswith("VARIATION 1"):
                        var1 = part.replace("VARIATION 1", "").strip()
                    elif part.startswith("VARIATION 2"):
                        var2 = part.replace("VARIATION 2", "").strip()
                    elif part.startswith("ANALYSIS"):
                        analysis = part.replace("ANALYSIS", "").strip()

                st.session_state["pg_var1"]     = var1
                st.session_state["pg_var2"]     = var2
                st.session_state["pg_analysis"] = analysis
                st.session_state["last_generated_post"] = result

            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

    # ── Persistent output — renders after generation and survives button reruns ──
    var1     = st.session_state.get("pg_var1", "")
    var2     = st.session_state.get("pg_var2", "")
    analysis = st.session_state.get("pg_analysis", "")

    if var1 or var2:
        st.success("✅ Posts generated!")
        st.markdown("---")
        st.subheader("📝 Your Post Variations")

        for idx, (label, content) in enumerate(
            [("Variation 1", var1), ("Variation 2", var2)], start=1
        ):
            if not content:
                continue
            with st.expander(f"📄 {label}", expanded=True):
                st.markdown(content)

                # Character count warning
                char_count = len(content)
                char_color = "#00c851" if char_count <= 3000 else "#e63946"
                st.markdown(
                    f"<div style='font-size:0.75rem;color:{char_color};text-align:right;'>"
                    f"{char_count:,} / 3,000 chars</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("**Send this post to:**")
                btn_col1, btn_col2, btn_col3 = st.columns(3)

                with btn_col1:
                    if st.button(
                        "📋 Copy Post",
                        key=f"copy_v{idx}",
                        use_container_width=True,
                        help="Expand to copy the text",
                    ):
                        st.code(content, language=None)

                with btn_col2:
                    if st.button(
                        "🔧 Optimize This Post",
                        key=f"opt_v{idx}",
                        use_container_width=True,
                        help="Send directly to Post Optimizer",
                    ):
                        st.session_state["po_content"]   = content
                        st.session_state["current_page"] = "🔧 Post Optimizer"
                        st.rerun()

                with btn_col3:
                    if st.button(
                        "🔥 Check Hook",
                        key=f"hook_v{idx}",
                        use_container_width=True,
                        help="Send directly to Viral Hook Analyzer",
                    ):
                        st.session_state["hook_analyzer_input"] = content
                        st.session_state["current_page"]        = "🔥 Viral Hook Analyzer"
                        st.rerun()

        if analysis:
            with st.expander("📊 AI Analysis", expanded=True):
                st.markdown(analysis)
