"""
hook_lab.py — 🧪 Hook Lab (premium)

Give it a topic; it writes a batch of scroll-stopping LinkedIn hooks using a
spread of proven opening patterns, then scores every one with the SAME
deterministic voice validator the rest of the app uses (core.validator) and
ranks them best-first. One click sends the winning hook into the Post
Generator as the opener.

Why it's different from the Viral Hook Analyzer:
  • Analyzer: you paste ONE hook → it diagnoses + rewrites it.
  • Hook Lab: you give a TOPIC → it generates MANY hooks, scores + ranks them.
    Ideation vs. diagnosis.

Design notes:
  • Generation is a single Gemini call returning "PATTERN :: HOOK" lines, parsed
    defensively (never crashes on malformed output).
  • Scoring is deterministic (validate_hook), so ranking is stable and on-brand
    — no extra AI calls, no inflated self-scores.
  • Optional live-web research backing reuses core.web_research, cached 1h.
"""
from __future__ import annotations

import streamlit as st

from gemini_client import generate_text, get_profile_context
from industry_profiles import get_industry_voice_block
from core.voice import HUMAN_VOICE_PRIMER, BANNED
from core import validator as _validator
from core import web_research as _web_research


# The proven opening patterns we ask the model to spread across. Kept here (not
# in the prompt only) so the UI can explain what each one is.
HOOK_PATTERNS = [
    "Contrarian",      # challenges a widely-held belief
    "Specific Number", # a concrete, surprising stat or figure
    "Mid-Scene",       # drops the reader into a moment, mid-action
    "Confession",      # an honest admission with stakes
    "Bold Claim",      # a strong, defensible assertion
    "Curiosity Gap",   # opens a loop the reader must close
    "Cost / Loss",     # what it cost — money, time, a deal
    "Before / After",  # a sharp transformation in one line
]


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_hook_research(topic: str, niche: str, audience: str, api_key: str) -> dict:
    """Cached live-web research on winning hook patterns for the niche (1h TTL)."""
    return dict(_web_research.research_linkedin_strategy(
        topic, niche, audience,
        api_key=api_key, model=_web_research.RESEARCH_MODEL_DEFAULT,
    ))


def build_hooks_prompt(
    topic: str,
    niche: str,
    audience: str,
    count: int = 8,
    research: str = "",
) -> str:
    """Compose the hook-generation prompt. Output is one 'PATTERN :: HOOK' per line."""
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche)
    pattern_list   = ", ".join(HOOK_PATTERNS[:count])

    return f"""{HUMAN_VOICE_PRIMER}

You are a LinkedIn hook specialist. Write {count} DISTINCT opening lines (hooks)
for a post on this topic. Each hook must be able to stand alone as line 1 of a
post and make a real person stop scrolling.

TOPIC: {topic}
NICHE / INDUSTRY: {niche}
AUDIENCE: {audience}{profile_ctx}
{industry_voice}
{research}
Use a DIFFERENT pattern for each hook. Spread across these patterns: {pattern_list}.

HARD RULES:
- One line each. Under 200 characters so it's fully visible before "see more".
- Specific and concrete — real numbers, real moments, real stakes. No vague setup.
- Do NOT open a hook with the word "I".
- Statements beat questions — avoid question hooks.
- Sound like a sharp human wrote it, never like AI.
{BANNED}

OUTPUT FORMAT — return ONLY {count} lines, nothing else, exactly:
PATTERN :: HOOK
(where PATTERN is the pattern name and HOOK is the opening line)

Example line:
Cost / Loss :: We lost a 40-million-naira account because I sent one Slack message at 9pm."""


def parse_hooks(raw: str) -> list[dict]:
    """
    Parse 'PATTERN :: HOOK' lines into [{pattern, hook}], defensively.

    Tolerates missing patterns, markdown bullets, numbering, and stray prose.
    Never raises.
    """
    import re
    out: list[dict] = []
    seen: set[str] = set()
    lines = [ln.strip() for ln in (raw or "").splitlines() if ln.strip()]

    # If the model followed the "PATTERN :: HOOK" format for any line, trust the
    # format and drop everything without a delimiter (preamble, prose, "Here are
    # your hooks:", trailing notes). Only fall back to loose parsing when the
    # model ignored the format entirely.
    has_delim = any("::" in ln for ln in lines)

    for s in lines:
        # strip list markers / numbering
        s = re.sub(r"^[\-\*•]\s*", "", s)
        s = re.sub(r"^\d+[.)]\s*", "", s)
        s = s.replace("**", "").strip()

        pattern, hook = "", ""
        if "::" in s:
            left, right = s.split("::", 1)
            pattern, hook = left.strip(), right.strip()
        elif has_delim:
            continue  # delimited mode — skip non-delimited noise lines
        else:
            hook = s  # loose fallback: whole line is the hook

        # Drop quotes wrapping the hook
        hook = hook.strip().strip('"“”').strip()
        if len(hook) < 12 or len(hook) > 280:
            continue
        key = hook.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"pattern": pattern or "Hook", "hook": hook})
    return out


def score_and_rank(hooks: list[dict]) -> list[dict]:
    """Attach a deterministic validator score + grade to each hook; sort best-first."""
    scored: list[dict] = []
    for h in hooks:
        rep = _validator.validate_hook(h["hook"])
        scored.append({
            **h,
            "score": rep.score,
            "grade": rep.grade,
            "issues": [i.message for i in rep.issues],
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def _score_color(score: int) -> str:
    if score >= 90: return "#00875A"
    if score >= 75: return "#0A66C2"
    if score >= 60: return "#B7791F"
    return "#C0392B"


# ─────────────────────────────────────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_hook_lab():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">Premium · Generate · Score · Rank</div>
        <h1>🧪 Hook Lab</h1>
        <p>Give it a topic. Get a batch of scroll-stopping hooks — each scored and ranked, best first.</p>
    </div>
    """, unsafe_allow_html=True)

    _p = st.session_state.get("user_profile", {})
    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        st.warning("⚠️ Add your Gemini API key in the sidebar to use Hook Lab.")

    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_area(
            "📌 What's the post about?",
            value=st.session_state.get("hl_topic", ""),
            placeholder="e.g., why we stopped doing daily standups, a deal that fell through, a pricing change…",
            height=120,
            key="hl_topic",
        )
        niche = st.text_input(
            "🎯 Niche / industry",
            value=st.session_state.get("hl_niche", _p.get("industry", "")),
            placeholder="e.g., Fintech, Legal Practice, B2B SaaS",
            key="hl_niche",
        )
    with col2:
        audience = st.text_input(
            "👥 Audience",
            value=st.session_state.get("hl_audience", _p.get("audience", "") or "Professionals on LinkedIn"),
            key="hl_audience",
        )
        count = st.slider("How many hooks?", 4, 8, 8, key="hl_count")
        research_on = st.checkbox(
            "🔎 Research-backed (live web)",
            value=st.session_state.get("hl_research_on", False),
            help="Pull current winning hook patterns for your niche from the web before generating.",
            key="hl_research_on",
        )

    if st.button("🧪 Generate & rank hooks", type="primary",
                 use_container_width=True, disabled=not api_key, key="hl_generate"):
        if not (topic or "").strip():
            st.error("Tell me what the post is about first.")
        else:
            _research_block = ""
            _research_result = None
            if research_on:
                with st.spinner("🔎 Researching winning hooks in your niche…"):
                    try:
                        _research_result = _cached_hook_research(
                            topic.strip(), niche.strip(), audience.strip(), api_key,
                        )
                        if not (_research_result and _research_result.get("ok")):
                            try:
                                _cached_hook_research.clear()
                            except Exception:
                                pass
                        _research_block = _web_research.research_block(_research_result)
                    except Exception:
                        _research_result, _research_block = None, ""
            st.session_state["hl_research_result"] = _research_result

            with st.spinner("🧪 Writing and scoring hooks…"):
                try:
                    raw = generate_text(
                        build_hooks_prompt(topic.strip(), niche.strip(),
                                           audience.strip(), count, _research_block),
                        temperature=0.95,
                        max_tokens=2000,
                        model=st.session_state.get("gemini_model", "gemini-2.5-flash"),
                    )
                    hooks = score_and_rank(parse_hooks(raw))
                except Exception as e:
                    hooks = []
                    st.error(f"Couldn't generate hooks: {str(e)[:160]}")
            st.session_state["hl_hooks"] = hooks
            st.session_state["hl_for_topic"] = topic.strip()

    # ── Results ───────────────────────────────────────────────────────────
    hooks = st.session_state.get("hl_hooks")
    if hooks:
        st.markdown("---")
        st.markdown(f"### 🏆 {len(hooks)} hooks, ranked")

        _research_result = st.session_state.get("hl_research_result")
        if _research_result and _research_result.get("ok"):
            _badge = "🔎 Live web research" if _research_result.get("grounded") else "🔎 Best-practice research"
            with st.expander(f"{_badge} used for these hooks", expanded=False):
                st.markdown(_research_result.get("summary", ""))
                _web_research.render_sources(_research_result)

        import html as _h
        for i, h in enumerate(hooks):
            color = _score_color(h["score"])
            pattern = _h.escape(h["pattern"])
            hook_txt = _h.escape(h["hook"])
            rank_medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            st.markdown(
                f"""
                <div style="display:flex;gap:0.8rem;align-items:flex-start;
                            padding:0.85rem 1rem;margin:0.5rem 0;background:#fff;
                            border:1px solid #E1E9F5;border-left:5px solid {color};
                            border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
                    <div style="font-size:1.1rem;min-width:34px;text-align:center;">{rank_medal}</div>
                    <div style="flex:1;">
                        <div style="color:#1a1a1a;font-size:1rem;font-weight:600;line-height:1.45;">{hook_txt}</div>
                        <div style="margin-top:0.35rem;">
                            <span style="background:{color}1A;color:{color};font-size:0.72rem;
                                         font-weight:700;padding:2px 9px;border-radius:99px;">
                                {h['score']}/100 · {h['pattern'] and pattern}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("✍️ Write a post with this hook", key=f"hl_use_{i}",
                         use_container_width=True):
                st.session_state["pg_topic"] = st.session_state.get("hl_for_topic", "")
                st.session_state["pg_niche"] = niche.strip()
                st.session_state["pg_audience"] = audience.strip() or "Professionals on LinkedIn"
                st.session_state["pg_story_beats"] = (
                    f"Open with a hook in the spirit of this (rework it, don't copy verbatim): "
                    f"\"{h['hook']}\""
                )
                st.session_state["_pending_nav"] = "🚀 Post Generator"
                st.toast("Hook sent to the Post Generator", icon="✍️")
                st.rerun()

        # Copy-friendly plain list
        with st.expander("📋 Copy-friendly list", expanded=False):
            st.code("\n".join(f"{h['score']:>3}  {h['hook']}" for h in hooks), language=None)
