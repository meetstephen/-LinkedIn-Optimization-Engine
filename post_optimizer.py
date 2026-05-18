"""
Post Optimizer Module — Diagnoses and rewrites existing LinkedIn posts
for maximum engagement and virality potential.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context, stream_text
from library import save_post_to_library, bump_optimized
from industry_profiles import get_industry_voice_block
from core.voice import (
    HUMAN_VOICE_PRIMER, BANNED, HUMAN_SIGNATURES,
)


OPTIMIZATION_GOALS = {
    "Maximum Engagement":    "likes, comments, shares — the post needs emotional pull and a reason to respond",
    "Professional Authority":"clear expertise signal — confident, specific, not arrogant",
    "Lead Generation":       "attract clients or employers — show the result, not just the skill",
    "Community Building":    "get people talking — relatable friction, genuine questions",
    "Personal Branding":     "unmistakably you — a distinctive voice that people remember",
}


def build_optimizer_prompt(original_post: str, goal: str, niche: str = "") -> str:
    goal_desc      = OPTIMIZATION_GOALS.get(goal, goal)
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche) if niche.strip() else ""

    return f"""{HUMAN_VOICE_PRIMER}

You are working as a world-class editor improving a first draft. Keep the writer's voice. Cut what doesn't serve the reader. Make every line do more work. Never make the post sound more generic or more "AI-written" than the original.{profile_ctx}

ORIGINAL POST:
\"\"\"
{original_post}
\"\"\"

GOAL: {goal} — {goal_desc}

{BANNED}
{HUMAN_SIGNATURES}
{industry_voice}

DELIVER EXACTLY THIS STRUCTURE:

## DIAGNOSIS
Score each element (1–10) with one specific sentence explaining the score:
- Hook: X/10 — [name the exact technique used or missed]
- Clarity: X/10 — [name the specific confusing moment, or what makes it clear]
- Emotional pull: X/10 — [name the exact line that creates or kills emotion]
- Formatting: X/10 — [name the specific formatting problem or strength]
- CTA: X/10 — [quote the CTA and say precisely why it works or doesn't]

**OVERALL: XX/100**

## WHAT'S KILLING IT
3–4 specific problems. Be direct. No softening. Name the exact line or word.
Not "the hook is weak" — say "the opening line 'I have been thinking about...' kills momentum before it starts."

## REWRITTEN VERSION
Write the full rewritten post. Keep the author's voice and story — only improve the execution.

Rewrite rules:
- Hook must not start with "I"
- No questions as hooks
- One idea per line, blank line between paragraphs
- Specifics over generalities (real numbers, real details)
- One vulnerable or honest moment (earned, not performative)
- One industry-native proof point
- CTA is a genuine question — max one, at the very end
- Under 260 words

## WHAT CHANGED & WHY
List exactly 5 edits. For each one:
- Quote the original line
- Show what it was changed to
- Explain in one sentence why the change performs better

Not "improved the hook" — say exactly what you changed it from and to, and why that's stronger.
"""


def _extract_rewritten(result: str) -> str:
    """Pull the REWRITTEN VERSION section out of an optimizer result."""
    lines, in_block, out = result.split("\n"), False, []
    for line in lines:
        if "REWRITTEN VERSION" in line.upper():
            in_block = True
            continue
        if in_block and line.startswith("##"):
            break
        if in_block:
            out.append(line)
    return "\n".join(out).strip()


def _extract_score(result: str) -> str:
    """Find the OVERALL: XX/100 line and return the score string."""
    for line in result.split("\n"):
        if "OVERALL" in line.upper():
            raw = line.split(":")[-1].strip() if ":" in line else "—"
            return raw.replace("**", "").strip()
    return "—"


def render_post_optimizer():
    st.header("🔧 LinkedIn Post Optimizer")
    st.markdown("Paste your existing post and get a full diagnosis + professional rewrite with engagement score.")

    # ── Pipeline-fed content from Post Generator ─────────────────────────────
    _piped_content = st.session_state.pop("po_content_pipe", None)
    _handoff_note  = st.session_state.pop("po_handoff_note", None)
    if _piped_content:
        # Use a separate state key to seed the widget without value+key conflict
        st.session_state["po_content"] = _piped_content
        if _handoff_note:
            st.success(f"✅ Received: **{_handoff_note}** — pre-filled below. Pick a goal and hit Optimize.")
        else:
            st.success("✅ Post received from Post Generator — pre-filled below.")

    original_post = st.text_area(
        "📝 Paste Your LinkedIn Post Here",
        placeholder=(
            "Paste your existing LinkedIn post here…\n\n"
            "The more complete the post, the more specific the diagnosis. "
            "Even rough drafts work — the AI will show you exactly what to fix."
        ),
        height=320,
        key="po_content",
    )

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        goal = st.selectbox("🎯 Optimization Goal", list(OPTIMIZATION_GOALS.keys()))
    with col2:
        niche = st.text_input(
            "🏭 Your Industry (optional)",
            placeholder="e.g., Legal Practice, Fintech, Real Estate",
            key="po_niche",
            help="Unlocks industry-specific vocabulary, proof patterns and hook archetypes in the rewrite.",
        )
    with col3:
        st.info(f"**Goal:** {OPTIMIZATION_GOALS[goal]}")

    st.markdown("---")

    if st.button("🚀 Optimize My Post", type="primary", use_container_width=True):
        if not original_post.strip():
            st.error("Please paste a post to optimize.")
            return
        if len(original_post.strip()) < 20:
            st.warning("Post seems too short. Add more content for better optimization.")
            return

        st.info("⚡ Streaming analysis — results appear as they're written…")
        _stream_box = st.empty()
        try:
            prompt = build_optimizer_prompt(
                original_post, goal,
                niche=st.session_state.get("po_niche", ""),
            )
            with _stream_box.container():
                result = st.write_stream(
                    stream_text(prompt, temperature=0.72, max_tokens=8000)
                )
            # Clear the raw stream — the formatted report below is the single source of truth
            _stream_box.empty()

            # Persist the result so save buttons / pipelines survive reruns
            st.session_state["po_last_result"]   = result
            st.session_state["po_last_original"] = original_post
            st.session_state["po_last_goal"]     = goal
            st.session_state["po_last_niche"]    = st.session_state.get("po_niche", "")
            st.session_state["last_generated_post"] = result
            bump_optimized()

        except Exception as e:
            st.error(f"Optimization failed: {str(e)}")
            with st.expander("🔍 Error details"):
                import traceback as _tb
                st.code(_tb.format_exc())
            return

    # ── Render last result + actions (always renders when result exists) ───
    result = st.session_state.get("po_last_result", "")
    if not result:
        return

    last_original = st.session_state.get("po_last_original", "")
    last_goal     = st.session_state.get("po_last_goal", goal)
    last_niche    = st.session_state.get("po_last_niche", "")

    st.success("✅ Optimization complete.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("❌ Original Post")
        st.markdown(
            f'<div style="background:#fff3f3;padding:1rem;border-radius:8px;'
            f'border-left:4px solid #ff4444;font-size:0.9rem;line-height:1.6;">'
            f'{last_original.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.subheader("✅ After AI Analysis")
        st.metric("Engagement Score", _extract_score(result))
        st.markdown(
            f"<div style='font-size:0.8rem;color:#555;margin-top:0.5rem;'>"
            f"Industry: <strong>{last_niche or '—'}</strong><br>"
            f"Goal: <strong>{last_goal}</strong></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    with st.expander("📄 Full Optimization Report", expanded=True):
        st.markdown(result)

    st.markdown("---")
    st.markdown("**Send the optimized post to:**")
    pipe1, pipe2, pipe3 = st.columns(3)
    with pipe1:
        if st.button("🔥 Check Hook in Analyzer", use_container_width=True,
                     key="opt_to_hook",
                     help="Run the rewritten hook through the Viral Hook Analyzer"):
            rewritten = _extract_rewritten(result) or last_original
            st.session_state["hook_analyzer_input"] = rewritten
            st.session_state["_pending_nav"] = "🔥 Viral Hook Analyzer"
            st.rerun()
    with pipe2:
        if st.button("🎨 Make Visual", use_container_width=True,
                     key="opt_to_image",
                     help="Generate a LinkedIn image for this post"):
            rewritten = _extract_rewritten(result) or last_original
            st.session_state["ig_post_content"] = rewritten[:500]
            st.session_state["_pending_nav"] = "🎨 Image Generator"
            st.rerun()
    with pipe3:
        if st.button("📚 Save to Post Library", use_container_width=True,
                     key="opt_to_library",
                     help="Save the full optimization report to your Post Library"):
            ok, msg = save_post_to_library(
                result, "🔧 Post Optimizer",
                tags=["optimized", last_goal.lower().replace(" ", "-")],
            )
            st.success(msg) if ok else st.warning(msg)

    if st.button("🔄 Start a fresh optimization", key="po_reset"):
        for k in ("po_last_result", "po_last_original", "po_last_goal", "po_last_niche"):
            st.session_state.pop(k, None)
        st.rerun()
