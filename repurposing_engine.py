"""
Repurposing Engine — Transform one idea into a full content suite.

One topic → text post + carousel slides + 5 hook variations +
            5 CTA options + 3 comment prompts.

This is how serious creators operate: one idea, maximum reach.
"""
import streamlit as st
from gemini_client import get_profile_context, stream_text, generate_text
from industry_profiles import get_industry_voice_block
from library import save_post_to_library, bump_generated
from core.voice import HUMAN_VOICE_PRIMER, BANNED, HUMAN_SIGNATURES, STRUCTURE_RULES


def build_repurpose_prompt(idea: str, niche: str, audience: str, formats: list) -> str:
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche)
    formats_str    = ", ".join(formats)

    NL = chr(10)

    # Build the requested-format sections separately so f-string expressions
    # never need to contain quote/backslash escapes (Python 3.9 / 3.10 friendly).
    section_text = ""
    if "Text Post" in formats:
        section_text += (
            f"{NL}---TEXT POST---{NL}"
            "Write one complete LinkedIn post (300-500 words). Opens with a hook "
            "that does NOT start with \"I\". One idea per line. Blank lines between "
            "paragraphs. Ends with one genuine question CTA."
        )
    if "Carousel Slides" in formats:
        section_text += (
            f"{NL}---CAROUSEL SLIDES---{NL}"
            "Write 7 carousel slides. Each slide: one emoji, one title (max 8 words), "
            "one body (max 35 words). Format: SLIDE N | emoji | TITLE | body. "
            "First slide = bold hook claim. Last slide = CTA with clear next step."
        )
    if "Hook Variations" in formats:
        section_text += (
            f"{NL}---HOOK VARIATIONS---{NL}"
            "Write 5 completely different hooks for this idea. Each hook max 15 words. "
            "Never starts with \"I\". No questions. Each uses a different psychological "
            "trigger: curiosity gap, bold claim, confession, shock stat, direct address. "
            "Label: HOOK 1, HOOK 2, etc. After each: Trigger used + one sentence why it works."
        )
    if "CTA Options" in formats:
        section_text += (
            f"{NL}---CTA OPTIONS---{NL}"
            "Write 5 CTAs for this topic. Mix: question CTA, action CTA, share CTA, "
            "soft CTA, DM CTA. Label CTA 1-5. After each: best used when: [one line]."
        )
    if "Comment Prompts" in formats:
        section_text += (
            f"{NL}---COMMENT PROMPTS---{NL}"
            "Write 3 strategic comments for this topic — designed to be left on "
            "other peoples posts to drive profile visits. Each 2-3 sentences. "
            "Adds a real insight. Ends with a soft hook back to this topic. "
            "Label COMMENT 1-3."
        )

    return f"""{HUMAN_VOICE_PRIMER}

You are working as a content strategist who repurposes one strong idea into multiple formats without losing authenticity. Same voice across every format. Same human warmth. No brand-deck energy.
{profile_ctx}
{industry_voice}

CORE IDEA / TOPIC:
\"\"\"{idea}\"\"\"

TARGET AUDIENCE: {audience}
NICHE: {niche}
FORMATS REQUESTED: {formats_str}

{BANNED}
{HUMAN_SIGNATURES}
{STRUCTURE_RULES}

Produce ONLY the requested formats below. Label each section clearly. Each format must sound like the same person wrote it — same voice, same specificity, same point of view.
{section_text}
"""


def render_repurposing_engine():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">Content Operating System</div>
        <h1>♻️ LinkedIn Repurposing Engine</h1>
        <p>One idea → full content suite. Text post, carousel, hooks, CTAs, and comment prompts — all in one generation.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Education strip ───────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("**💡 Why Repurpose?**\n\nTop LinkedIn creators don't write 5 posts a week. They write 1 idea and distribute it across 5 formats. Carousels get 3× reach. Comments drive profile visits. Hooks boost first-hour engagement.")
    with c2:
        st.warning("**⚡ How It Works**\n\nPaste your idea below — raw notes, a drafted post, even just a few bullet points. Select which formats you need. Generate. Everything comes out ready to copy.")
    with c3:
        st.success("**🇳🇬 Nigerian Context**\n\nAll output uses Nigerian business context — naira figures, local institutions, WAT posting times — when Nigerian Voice Mode is active in the sidebar.")

    st.markdown("---")

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns([1.2, 0.8])
    with col1:
        idea = st.text_area(
            "💡 Your Core Idea",
            value=st.session_state.get("re_idea", ""),
            placeholder=(
                "Raw notes are fine — the AI will shape them.\n\n"
                "e.g.: 'Most Nigerian founders don't know their CAC until month 9. "
                "By then it's too late. I learnt this after burning ₦4M in ads with no tracking.'"
            ),
            height=180,
            key="re_idea",
        )
        niche = st.text_input(
            "🏭 Your Industry",
            value=st.session_state.get("re_niche", _p.get("industry", "")),
            placeholder="e.g., Fintech, Legal Practice, Real Estate",
            key="re_niche",
        )
        audience = st.text_input(
            "👥 Target Audience",
            value=st.session_state.get("re_audience", _p.get("audience", "")),
            placeholder="e.g., Nigerian founders, Lagos lawyers, HR managers",
            key="re_audience",
        )

    with col2:
        st.markdown("**📦 Select Formats to Generate**")
        fmt_text     = st.checkbox("📝 Text Post",       value=True,  key="re_fmt_text")
        fmt_carousel = st.checkbox("🎠 Carousel Slides", value=True,  key="re_fmt_carousel")
        fmt_hooks    = st.checkbox("🪝 Hook Variations", value=True,  key="re_fmt_hooks")
        fmt_ctas     = st.checkbox("📢 CTA Options",     value=False, key="re_fmt_ctas")
        fmt_comments = st.checkbox("💬 Comment Prompts", value=False, key="re_fmt_comments")

        st.markdown("---")
        st.markdown("**💡 Pro Tips**")
        st.caption("• Text Post + Hooks = minimum viable suite")
        st.caption("• Add Carousel for 3× reach on the same idea")
        st.caption("• Comment Prompts = passive traffic from others' posts")
        st.caption("• Select all 5 for a full week of content from one idea")

    st.markdown("---")

    formats = []
    if fmt_text:     formats.append("Text Post")
    if fmt_carousel: formats.append("Carousel Slides")
    if fmt_hooks:    formats.append("Hook Variations")
    if fmt_ctas:     formats.append("CTA Options")
    if fmt_comments: formats.append("Comment Prompts")

    if not formats:
        st.warning("Select at least one format above.")
        return

    if st.button(
        f"♻️ Generate {len(formats)} Format{'s' if len(formats) > 1 else ''}",
        type="primary",
        use_container_width=True,
        disabled=not idea.strip(),
    ):
        if not idea.strip():
            st.error("Please enter your core idea.")
            return

        st.info(f"⚡ Generating {len(formats)} formats — output streams in real time…")

        _stream_box = st.empty()
        try:
            prompt = build_repurpose_prompt(
                idea,
                niche or "Professional",
                audience or "Professionals on LinkedIn",
                formats,
            )
            with _stream_box.container():
                result = st.write_stream(
                    stream_text(prompt, temperature=0.85, max_tokens=10000)
                )
            # Clear the raw stream — the formatted per-format expanders below render it cleanly
            _stream_box.empty()
            st.session_state["re_last_result"]  = result
            st.session_state["re_last_formats"] = list(formats)
            st.session_state["session_repurposed"] = (
                st.session_state.get("session_repurposed", 0) + 1
            )
            bump_generated()

        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            with st.expander("🔍 Error details"):
                import traceback as _tb
                st.code(_tb.format_exc())
            return

    # ── Result panel — survives reruns and save clicks ─────────────────────
    result = st.session_state.get("re_last_result", "")
    if not result:
        return

    last_formats = st.session_state.get("re_last_formats", formats)

    st.markdown("---")
    st.markdown("### ✅ Your Content Suite")

    import re as _re

    def _extract_section(label: str) -> str:
        m = _re.search(
            rf"---{label}---\s*(.*?)(?=---[A-Z\s]+---|$)",
            result, _re.DOTALL | _re.IGNORECASE
        )
        return m.group(1).strip() if m else ""

    sections = {
        "Text Post":       ("📝", "🚀 Post Generator"),
        "Carousel Slides": ("🎠", "🎠 Carousel Planner"),
        "Hook Variations": ("🪝", "🔥 Viral Hook Analyzer"),
        "CTA Options":     ("📢", None),
        "Comment Prompts": ("💬", None),
    }

    for fmt_name, (icon, dest_page) in sections.items():
        if fmt_name not in last_formats:
            continue
        content = _extract_section(fmt_name.upper())
        if not content:
            continue

        with st.expander(f"{icon} {fmt_name}", expanded=True):
            st.markdown(content)

            btn_cols = st.columns([1, 1, 2])
            with btn_cols[0]:
                if st.button(f"📚 Save", key=f"re_save_{fmt_name}",
                             use_container_width=True):
                    ok, msg = save_post_to_library(
                        content, f"♻️ Repurposing — {fmt_name}",
                        tags=["repurposed", fmt_name.lower().replace(" ", "-")]
                    )
                    st.success(msg) if ok else st.warning(msg)

            with btn_cols[1]:
                if dest_page:
                    if st.button(f"→ {dest_page.split()[1]}", key=f"re_nav_{fmt_name}",
                                 use_container_width=True,
                                 help=f"Send to {dest_page}"):
                        if dest_page == "🔧 Post Optimizer":
                            st.session_state["po_content_pipe"] = content
                        elif dest_page == "🔥 Viral Hook Analyzer":
                            st.session_state["hook_analyzer_input"] = content[:500]
                        st.session_state["_pending_nav"] = dest_page
                        st.rerun()

    # ── Save / download / reset for the full suite ────────────────────────
    st.markdown("---")
    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        if st.button("📚 Save Full Suite to Library",
                     type="primary", use_container_width=True,
                     key="re_save_all"):
            ok, msg = save_post_to_library(
                result, "♻️ Repurposing Engine",
                tags=["repurposed", "full-suite"]
            )
            st.success(msg) if ok else st.warning(msg)
    with bcol2:
        st.download_button(
            "📥 Download Full Suite (.txt)",
            data=result,
            file_name=f"content_suite_{st.session_state.get('re_niche','').replace(' ','_').lower() or 'linkedin'}.txt",
            mime="text/plain",
            use_container_width=True,
            key="re_download",
        )
    with bcol3:
        if st.button("🔄 Generate a new suite", use_container_width=True, key="re_reset"):
            for k in ("re_last_result", "re_last_formats"):
                st.session_state.pop(k, None)
            st.rerun()
