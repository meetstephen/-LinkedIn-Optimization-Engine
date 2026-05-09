"""
Post Optimizer Module — Rewrites and scores existing LinkedIn posts
for maximum engagement and virality potential.
"""
import streamlit as st
from utils.gemini_client import generate_text, get_profile_context


OPTIMIZATION_GOALS = {
    "Maximum Engagement":    "likes, comments, shares — the post needs emotional pull and a reason to respond",
    "Professional Authority":"clear expertise signal — confident, specific, not arrogant",
    "Lead Generation":       "attract clients or employers — show the result, not just the skill",
    "Community Building":    "get people talking — relatable friction, genuine questions",
    "Personal Branding":     "unmistakably you — a distinctive voice that people remember",
}

_BANNED = """
NEVER use: "game-changer", "dive in", "leverage", "synergy", "actionable", "thought leader",
"passionate about", "journey", "crushing it", "hustle", "disrupt", "innovative",
"cutting-edge", "best practices", "I'm excited to share", "I'm thrilled",
"in today's fast-paced world", "at the end of the day", "needless to say",
"in conclusion", "circle back", "touch base", "move the needle"
"""


def build_optimizer_prompt(original_post: str, goal: str) -> str:
    goal_desc   = OPTIMIZATION_GOALS.get(goal, goal)
    profile_ctx = get_profile_context()
    return f"""You edit LinkedIn posts the way a great editor improves a first draft — you keep the writer's voice, cut what doesn't serve the reader, and make every line do more work.{profile_ctx}

ORIGINAL POST:
\"\"\"
{original_post}
\"\"\"

GOAL: {goal} — {goal_desc}

{_BANNED}

DELIVER:

## DIAGNOSIS
Score each element (1–10) in one line each:
- Hook: X/10 — [why, specifically]
- Clarity: X/10 — [why]
- Emotional pull: X/10 — [why]
- Formatting: X/10 — [why]
- CTA: X/10 — [why]

**OVERALL: XX/100**

## WHAT'S KILLING IT
3–4 specific problems. Be direct. No softening.

## REWRITTEN VERSION
Write the full rewritten post. Keep the author's voice and story — only improve the execution.

Rules for the rewrite:
- Hook must not start with "I"
- No questions as hooks
- One idea per line, blank lines between paragraphs
- Specifics over generalities (real numbers, real details)
- One vulnerable or honest moment
- CTA is a genuine question — max one, at the end
- Under 260 words

## WHAT CHANGED & WHY
List 4–5 specific edits with the reason each one performs better.
Not "improved the hook" — say exactly what you changed it to and why that's stronger.
"""


def render_post_optimizer():
    st.header("🔧 LinkedIn Post Optimizer")
    st.markdown("Paste your existing post and get a full diagnosis + professional rewrite with engagement score.")

    original_post = st.text_area(
        "📝 Paste Your LinkedIn Post Here",
        placeholder="Paste your existing LinkedIn post here… or send one directly from the Post Generator →",
        height=200,
        key="po_content",
    )

    col1, col2 = st.columns(2)
    with col1:
        goal = st.selectbox("🎯 Optimization Goal", list(OPTIMIZATION_GOALS.keys()))
    with col2:
        st.info(f"**Goal:** {OPTIMIZATION_GOALS[goal]}")

    st.markdown("---")

    if st.button("🚀 Optimize My Post", type="primary", use_container_width=True):
        if not original_post.strip():
            st.error("Please paste a post to optimize.")
            return
        if len(original_post.strip()) < 20:
            st.warning("Post seems too short. Add more content for better optimization.")
            return

        with st.spinner("Analyzing and rewriting your post..."):
            try:
                prompt = build_optimizer_prompt(original_post, goal)
                result = generate_text(prompt, temperature=0.72)

                st.success("✅ Optimization complete!")
                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("❌ Original Post")
                    st.markdown(
                        f'<div style="background:#fff3f3;padding:1rem;border-radius:8px;border-left:4px solid #ff4444;">'
                        f'{original_post.replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.subheader("✅ After AI Analysis")
                    score_line = ""
                    for line in result.split("\n"):
                        if "OVERALL" in line.upper():
                            score_line = line
                            break
                    if score_line:
                        st.metric("Engagement Score", score_line.split(":")[-1].strip() if ":" in score_line else "—")

                st.markdown("---")
                st.markdown(result)
                st.session_state["last_generated_post"] = result

                # ── Pipeline: send optimised post onwards ──────────────────
                st.markdown("---")
                st.markdown("**Send the optimized post to:**")
                pipe1, pipe2 = st.columns(2)
                with pipe1:
                    if st.button(
                        "🔥 Check Hook in Analyzer",
                        use_container_width=True,
                        key="opt_to_hook",
                        help="Run the rewritten hook through the Viral Hook Analyzer",
                    ):
                        # Extract the rewritten post section from the result
                        _lines   = result.split("\n")
                        _in, _rw = False, []
                        for _line in _lines:
                            if "REWRITTEN VERSION" in _line.upper():
                                _in = True; continue
                            if _in and _line.startswith("##"):
                                break
                            if _in:
                                _rw.append(_line)
                        _rewritten = "\n".join(_rw).strip() or original_post
                        st.session_state["hook_analyzer_input"] = _rewritten
                        st.session_state["current_page"]        = "🔥 Viral Hook Analyzer"
                        st.rerun()
                with pipe2:
                    if st.button(
                        "📚 Save to Post Library",
                        use_container_width=True,
                        key="opt_to_library",
                        help="Save the full optimization report to your Post Library",
                    ):
                        st.session_state.setdefault("post_library", []).insert(0, {
                            "id":         int(__import__("time").time() * 1000),
                            "content":    result,
                            "module":     "🔧 Post Optimizer",
                            "score":      0,
                            "tags":       ["optimized"],
                            "created_at": __import__("datetime").datetime.now().strftime("%b %d, %Y · %I:%M %p"),
                            "starred":    False,
                        })
                        st.success("✅ Saved to Post Library!")

            except Exception as e:
                st.error(f"Optimization failed: {str(e)}")
