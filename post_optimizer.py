"""
Post Optimizer Module — Rewrites and scores existing LinkedIn posts
for maximum engagement and virality potential.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context
from library import save_post_to_library
from industry_profiles import get_industry_voice_block


OPTIMIZATION_GOALS = {
    "Maximum Engagement":    "likes, comments, shares — the post needs emotional pull and a reason to respond",
    "Professional Authority":"clear expertise signal — confident, specific, not arrogant",
    "Lead Generation":       "attract clients or employers — show the result, not just the skill",
    "Community Building":    "get people talking — relatable friction, genuine questions",
    "Personal Branding":     "unmistakably you — a distinctive voice that people remember",
}

# ── Expanded banned phrases ──────────────────────────────────────────────────
_BANNED = """
BANNED WORDS & PHRASES — if any appear in the rewrite, the post fails:
  "game-changer", "game-changing", "dive in", "let's dive in", "let's dive into",
  "let's unpack", "unpack this", "leverage", "synergy", "actionable", "actionable insights",
  "thought leader", "passionate about", "journey", "transformation", "transformative",
  "crushing it", "hustle", "hustle culture", "grind", "disrupt", "disruption",
  "innovative", "cutting-edge", "best practices",
  "I'm excited to share", "I'm thrilled to announce", "I'm proud to share",
  "in today's fast-paced world", "in today's digital landscape", "in today's world",
  "at the end of the day", "needless to say", "it goes without saying",
  "in conclusion", "in summary", "circle back", "touch base",
  "bandwidth", "move the needle", "reach out",
  "unlock", "unlock your potential", "level up", "skyrocket", "scale your",
  "deep dive", "masterclass", "playbook", "blueprint",
  "it's a marathon not a sprint", "fail forward", "embrace failure", "fail fast",
  "ecosystem" (used vaguely), "stakeholders", "deliverables", "key takeaways",
  "pro tip:", "hot take:", "this is your sign", "reminder:", "PSA:",
  "unpopular opinion:" (as opener), "I'll say what no one else will",
  "this changed everything", "changed my life", "I wish I knew this sooner",
  "the secret to", "you won't believe", "what nobody tells you",
  "period." / "full stop." (mic-drop endings), "we need to talk about",
  "value-add", "low-hanging fruit", "paradigm shift", "next level", "win-win"
"""

# ── Human writer signatures — what the rewrite must contain ─────────────────
_HUMAN_SIGNATURES = """
HUMAN WRITER SIGNATURES — the rewrite must contain at least 3 of these:

1. SPECIFIC NUMBERS: Not "a lot of money" → "₦2.4 million". Not "many years" → "7 years".
   If the original has no numbers, invent a plausible specific one.

2. SPECIFIC TIME STAMPS: "On a Wednesday in March…" / "By month 4…" / "Three weeks before…"

3. SPECIFIC PLACES: Name the actual city, building, neighbourhood, or office.
   Not "a client in Lagos" → "a client in Ikeja GRA".

4. DIALOGUE FRAGMENTS: One line of actual speech.
   "She said: 'The clause was always there.'" — not paraphrased, said.

5. SELF-INTERRUPTION: Used once. "And honestly?" / "Here's the thing." / "I mean that literally."

6. CONTRAST SENTENCES: Long sentence → immediately followed by a very short one.
   "We had invested 14 months and ₦9 million into this product.
   No one used it."

7. EARNED VULNERABILITY: One sentence where the writer admits they were wrong or afraid.
   Not "failure is my teacher" → "I told my co-founder it would work. It didn't."

8. INDUSTRY-NATIVE PROOF: One reference only a real practitioner uses naturally —
   a specific regulation, case name, system, or internal term.
"""


def build_optimizer_prompt(original_post: str, goal: str, niche: str = "") -> str:
    goal_desc      = OPTIMIZATION_GOALS.get(goal, goal)
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche) if niche.strip() else ""

    return f"""You edit LinkedIn posts the way a world-class editor improves a first draft — you keep the writer's voice, cut what doesn't serve the reader, and make every line do more work. You NEVER make the post sound more generic or more "AI-written" than the original.{profile_ctx}

ORIGINAL POST:
\"\"\"
{original_post}
\"\"\"

GOAL: {goal} — {goal_desc}

{_BANNED}
{_HUMAN_SIGNATURES}
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


def render_post_optimizer():
    st.header("🔧 LinkedIn Post Optimizer")
    st.markdown("Paste your existing post and get a full diagnosis + professional rewrite with engagement score.")

    # ── Patch 1c: Enlarged input (320px) + niche field ───────────────────────
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

        with st.spinner("Analyzing and rewriting your post…"):
            try:
                prompt = build_optimizer_prompt(
                    original_post, goal,
                    niche=st.session_state.get("po_niche", ""),
                )
                result = generate_text(prompt, temperature=0.72, max_tokens=8000)

                st.success("✅ Optimization complete!")
                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("❌ Original Post")
                    st.markdown(
                        f'<div style="background:#fff3f3;padding:1rem;border-radius:8px;'
                        f'border-left:4px solid #ff4444;font-size:0.9rem;line-height:1.6;">'
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
                        _raw_score = score_line.split(":")[-1].strip() if ":" in score_line else "—"
                        # Strip markdown bold markers (**XX/100** → XX/100)
                        _clean_score = _raw_score.replace("**", "").strip()
                        st.metric("Engagement Score", _clean_score)
                    st.markdown(
                        f"<div style='font-size:0.8rem;color:#555;margin-top:0.5rem;'>"
                        f"Industry context: <strong>{st.session_state.get('po_niche','—') or '—'}</strong><br>"
                        f"Goal: <strong>{goal}</strong></div>",
                        unsafe_allow_html=True,
                    )

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
                        st.session_state["nav_radio"]           = "🔥 Viral Hook Analyzer"
                        st.rerun()
                with pipe2:
                    if st.button(
                        "📚 Save to Post Library",
                        use_container_width=True,
                        key="opt_to_library",
                        help="Save the full optimization report to your Post Library",
                    ):
                        ok, msg = save_post_to_library(
                            result, "🔧 Post Optimizer", tags=["optimized"]
                        )
                        st.success(msg) if ok else st.warning(msg)

            except Exception as e:
                st.error(f"Optimization failed: {str(e)}")
                with st.expander("🔍 Error details"):
                    import traceback as _tb
                    st.code(_tb.format_exc())
