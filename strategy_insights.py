"""
Creator Strategy Insights — Simulates top LinkedIn creator tactics,
hook formulas, post structures, and engagement frameworks.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context, stream_text
from library import save_post_to_library
from industry_profiles import get_industry_voice_block
from core.voice import HUMAN_VOICE_PRIMER, BANNED, HUMAN_SIGNATURES
from core import web_research as _web_research


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_strategy_research(archetype: str, niche: str, goal: str, api_key: str) -> dict:
    """Cached live-web research on what's working for an archetype/niche (1h TTL)."""
    return dict(_web_research.research_creator_strategy(
        archetype, niche, goal,
        api_key=api_key, model=_web_research.RESEARCH_MODEL_DEFAULT,
    ))


CREATOR_ARCHETYPES = {
    "The Educator":           "Breaks down complex topics into digestible frameworks. Known for carousels, step-by-step guides, and 'what they don't teach you' posts.",
    "The Storyteller":        "Masters vulnerability and personal narrative. Uses emotional arcs, cliffhangers in hooks, and relatable human moments.",
    "The Contrarian Thinker": "Challenges conventional wisdom. Posts controversial takes, defends with data, sparks massive comment threads.",
    "The Results Poster":     "Shows before/after, shares numbers, proof-of-concept posts. Attracts clients and employers with demonstrated outcomes.",
    "The Community Builder":  "Engages others, reposts with commentary, Q&A threads, collaborative posts. Wins through relationship capital.",
    "The Niche Expert":       "Hyper-specific advice for a defined audience. Known as THE go-to person for one topic.",
    "The Document Builder":   "Builds in public — shares the journey, the failures, the weekly updates. Audiences become invested in their story.",
}

HOOK_FORMULAS = [
    "Shock Statistic: '[Surprising number] of [audience] don't know [key insight]'",
    "Confession: 'I was [wrong/embarrassed/scared] about [topic]. Here's what I discovered.'",
    "Contrarian Claim: '[Common belief everyone holds]. It's wrong. Here's what actually happens.'",
    "Curiosity Gap: '[Thing] looks like [X]. It's actually [Y]. Here's why that matters.'",
    "Before/After: '[Time period] ago, I [was struggling with Y]. Today [specific dramatic outcome].'",
    "Direct Address: 'If you're a [specific role] doing [specific thing], stop. Read this first.'",
    "Story Opening: '[Day/time]. I was [doing something specific]. Then [unexpected thing happened].'",
    "Bold Claim: '[Number] [units] later, I can say this with certainty: [counterintuitive truth].'",
    "List Tease: '[Number] things I wish someone told me about [topic] before I spent [cost/time]:'",
]

_BANNED_STRATEGY = """
ADDITIONAL BANNED STRATEGY-SPECIFIC PHRASES:
"content machine", "go viral", "algorithm hack", "viral formula",
"algorithm cheat code"
"""


def build_strategy_prompt(creator_type, niche, goal, research=""):
    archetype_desc  = CREATOR_ARCHETYPES.get(creator_type, "")
    hooks_formatted = "\n".join([f"{i+1}. {h}" for i, h in enumerate(HOOK_FORMULAS)])
    profile_ctx     = get_profile_context()
    industry_voice  = get_industry_voice_block(niche)
    return f"""{HUMAN_VOICE_PRIMER}

You study what actually works on LinkedIn — not the theory, the real patterns. You've watched thousands of posts succeed and fail. You know the difference between a creator who posts and one who grows.

Build a strategy playbook for this creator:{profile_ctx}
{industry_voice}
{research}
- Archetype: {creator_type} — {archetype_desc}
- Niche: {niche}
- Goal: {goal}

Write this like you're a mentor who has seen it work, not a consultant filling a template.
Every line should be something they can act on today.

{BANNED}
{_BANNED_STRATEGY}
{HUMAN_SIGNATURES}

---

## YOUR CREATOR DNA
What makes the {creator_type} archetype work — and specifically how it plays in {niche}.
The one thing this archetype must NEVER do. The one thing they must ALWAYS do.
3-4 paragraphs, specific to their niche. Real examples, not general principles.

## THE 5 HOOKS THAT WILL ACTUALLY WORK FOR YOU
Pick the 5 best hook formulas for a {creator_type} in {niche}.
For each hook:
- Template (adapted for their niche)
- A ready-to-use example written specifically for {niche} — not a placeholder
- The psychological mechanism: why this one stops the scroll

Reference these formulas as raw material:
{hooks_formatted}

## 3 REPEATABLE POST BLUEPRINTS
Three structures that consistently perform for this archetype in {niche}.
For each blueprint:
- A memorable name
- The structure line by line (e.g., "Line 1: hook. Lines 2-4: tension. Line 5-7: insight. Final line: CTA.")
- A complete written example for {niche}

## 10 ENGAGEMENT TACTICS
Not generic tips. Specific moves with timing and expected outcome.
Each one: what to do + when + what result to expect + why it works.

## POSTING RHYTHM
- Best days for {niche} audience — with a specific reason, not just the days
- Best times in WAT (West Africa Time, UTC+1) if Nigerian audience, or relevant timezone
- How many times per week — and exactly why that number
- Content mix: what percentage of posts should be each type

## THE ALGORITHM IN PLAIN ENGLISH
What LinkedIn actually rewards for {creator_type} creators right now.
What most {niche} creators get wrong about distribution.
How to use the first 60 minutes after posting — specifically.

## 90-DAY ROADMAP
Month 1 — Foundation: 3-4 specific actions (not categories)
Month 2 — Momentum: what should be measurably different, 3-4 specific actions
Month 3 — Authority: what success looks like with a real metric, 3-4 actions

One metric to track per month.

## THE COMMENT STRATEGY
This is how creators actually grow faster than posting alone.
Exactly which accounts to comment on, what kind of comments land, and when to do it.

## REAL-WORLD CASE STUDY
Create a specific fictional creator in {niche} who is a {creator_type}.
Walk through their first 90 days:
- Their first 5 post topics (actual titles)
- The post that broke through (what it was and why it worked)
- The turning point (day and what changed)
- Where they were at day 90 (specific follower count, engagement rate, one tangible outcome)

Make it feel real — specific numbers, specific moments.
"""


def render_strategy_insights():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">What Actually Works</div>
        <h1>🧠 Creator Strategy Insights</h1>
        <p>A real playbook based on what actually works — not what sounds good in theory.</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🎭 Learn About Creator Archetypes", expanded=False):
        for archetype, desc in CREATOR_ARCHETYPES.items():
            st.markdown(f"**{archetype}**: {desc}")

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)

    with col1:
        creator_type = st.selectbox("🎭 Your Creator Archetype", list(CREATOR_ARCHETYPES.keys()),
                                     help="Choose the style that feels most natural to you")
        niche = st.text_input(
            "🎯 Your Niche",
            value=st.session_state.get("si_niche", _p.get("industry", "")),
            placeholder="e.g., Legal Practice, Fintech, Real Estate, Consulting",
            key="si_niche",
        )

    with col2:
        goal = st.selectbox("🎯 Primary Growth Goal", [
            "Grow to 5K followers in 90 days",
            "Establish myself as a niche authority",
            "Attract premium clients / consulting mandates",
            "Get recruited by top companies or firms",
            "Build an audience for my product or service",
            "Become the go-to expert in my field",
        ])
        st.info(f"**Archetype:** {CREATOR_ARCHETYPES[creator_type]}")
        research_on = st.checkbox(
            "🔎 Research-backed (live web)",
            value=st.session_state.get("si_research_on", False),
            help="Search the web for how this archetype is currently growing in your niche, plus the latest on what the algorithm rewards.",
            key="si_research_on",
        )

    st.markdown("---")

    with st.expander("🪝 Quick Reference: 9 Proven Hook Formulas", expanded=False):
        for formula in HOOK_FORMULAS:
            st.markdown(f"• {formula}")

    if st.button("🚀 Generate My Strategy Playbook", type="primary", use_container_width=True):
        if not niche.strip():
            st.error("Please enter your niche.")
            return

        try:
            # ── Optional live web research ──────────────────────────────
            _research_block = ""
            _research_result = None
            if st.session_state.get("si_research_on", False):
                _api_key = st.session_state.get("gemini_api_key", "")
                with st.spinner("🔎 Researching what's working for your archetype now…"):
                    try:
                        _research_result = _cached_strategy_research(
                            creator_type, niche, goal, _api_key,
                        )
                        if not (_research_result and _research_result.get("ok")):
                            try:
                                _cached_strategy_research.clear()
                            except Exception:
                                pass
                        _research_block = _web_research.research_block(_research_result)
                    except Exception:
                        _research_result, _research_block = None, ""
                st.session_state["si_research_result"] = _research_result
            else:
                st.session_state.pop("si_research_result", None)

            st.info("⚡ Generating your playbook — streams in real time…")
            _stream_box = st.empty()
            with _stream_box.container():
                result = st.write_stream(stream_text(
                    build_strategy_prompt(creator_type, niche, goal,
                                          research=_research_block),
                    temperature=0.8, max_tokens=8000,
                ))
            _stream_box.empty()
            st.session_state["si_last_result"]    = result
            st.session_state["si_last_creator"]   = creator_type
            st.session_state["si_last_niche"]     = niche
        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            with st.expander("Error details"):
                import traceback as _tb
                st.code(_tb.format_exc())
            return

    # ── Result panel — survives reruns ─────────────────────────────────────
    result = st.session_state.get("si_last_result", "")
    if not result:
        return

    _ct = st.session_state.get("si_last_creator", creator_type)
    _ni = st.session_state.get("si_last_niche", niche)

    st.success("Strategy playbook generated.")
    st.markdown("---")

    # ── Live research brief (only when research-backed) ─────────────────
    _research_result = st.session_state.get("si_research_result")
    if _research_result and _research_result.get("ok"):
        _badge = "🔎 Live web research" if _research_result.get("grounded") else "🔎 Best-practice research"
        with st.expander(f"{_badge} used for this playbook", expanded=False):
            st.markdown(_research_result.get("summary", ""))
            _web_research.render_sources(_research_result)

    with st.expander("📄 Full Strategy Playbook", expanded=True):
        st.markdown(result)

    dl_col, sv_col, rs_col = st.columns(3)
    with dl_col:
        st.download_button(
            label="📥 Download Playbook",
            data=result,
            file_name=f"linkedin_strategy_{_ct.replace(' ', '_').lower()}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with sv_col:
        if st.button("📚 Save to Post Library", use_container_width=True,
                     key="si_save_library"):
            ok, msg = save_post_to_library(result, "🧠 Strategy Insights",
                                           tags=["strategy", _ct.lower().replace(" ", "-")])
            st.success(msg) if ok else st.warning(msg)
    with rs_col:
        if st.button("🔄 New playbook", use_container_width=True, key="si_reset"):
            for k in ("si_last_result", "si_last_creator", "si_last_niche"):
                st.session_state.pop(k, None)
            st.rerun()
