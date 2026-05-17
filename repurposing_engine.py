"""
Repurposing Engine — Transform one idea into a full content suite.

One topic → text post + carousel slides + 5 hook variations +
            5 CTA options + 3 comment prompts.

This is how serious creators operate: one idea, maximum reach.
"""
import streamlit as st
from gemini_client import get_profile_context, stream_text, generate_text
from industry_profiles import get_industry_voice_block
from library import save_post_to_library

_BANNED = """
BANNED: "game-changer", "dive in", "leverage", "synergy", "actionable",
"thought leader", "passionate about", "journey", "hustle", "disrupt",
"innovative", "I'm excited to share", "in today's fast-paced world",
"at the end of the day", "circle back", "move the needle", "unlock",
"level up", "deep dive", "playbook", "paradigm shift", "win-win"
"""


def build_repurpose_prompt(idea: str, niche: str, audience: str, formats: list) -> str:
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche)
    formats_str    = ", ".join(formats)

    return f"""You are a world-class LinkedIn content strategist who specialises in
repurposing one strong idea into multiple content formats without losing authenticity.
{profile_ctx}
{industry_voice}

CORE IDEA / TOPIC:
\"\"\"{idea}\"\"\"

TARGET AUDIENCE: {audience}
NICHE: {niche}
FORMATS REQUESTED: {formats_str}

{_BANNED}

Produce ONLY the requested formats below. Label each section clearly.

{('---TEXT POST---' + chr(10) + 'Write one complete LinkedIn post (300-500 words). Opens with a hook that does NOT start with "I". One idea per line. Blank lines between paragraphs. Ends with one genuine question CTA.' if 'Text Post' in formats else '')}

{('---CAROUSEL SLIDES---' + chr(10) + 'Write 7 carousel slides. Each slide: one emoji, one title (max 8 words), one body (max 35 words). Format: SLIDE N | emoji | TITLE | body. First slide = bold hook claim. Last slide = CTA with clear next step.' if 'Carousel Slides' in formats else '')}

{('---HOOK VARIATIONS---' + chr(10) + 'Write 5 completely different hooks for this idea. Each hook max 15 words. Never starts with "I". No questions. Each uses a different psychological trigger: curiosity gap, bold claim, confession, shock stat, direct address. Label: HOOK 1, HOOK 2, etc. After each: Trigger used + one sentence why it works.' if 'Hook Variations' in formats else '')}

{('---CTA OPTIONS---' + chr(10) + 'Write 5 CTAs for this topic. Mix: question CTA, action CTA, share CTA, soft CTA, DM CTA. Label CTA 1-5. After each: best used when: [one line].' if 'CTA Options' in formats else '')}

{('---COMMENT PROMPTS---' + chr(10) + 'Write 3 strategic comments for this topic — designed to be left on other people\'s posts to drive profile visits. Each 2-3 sentences. Adds a real insight. Ends with a soft hook back to this topic. Label COMMENT 1-3.' if 'Comment Prompts' in formats else '')}
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

        try:
            prompt = build_repurpose_prompt(
                idea,
                niche or "Professional",
                audience or "Professionals on LinkedIn",
                formats,
            )
            result = st.write_stream(
                stream_text(prompt, temperature=0.85, max_tokens=10000)
            )
            st.session_state["re_last_result"] = result

        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            with st.expander("🔍 Error details"):
                import traceback as _tb
                st.code(_tb.format_exc())
            return

        # ── Parsed output display ─────────────────────────────────────────────
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
            "Text Post":       ("📝", "re_fmt_text",     "🚀 Post Generator"),
            "Carousel Slides": ("🎠", "re_fmt_carousel", "🎠 Carousel Planner"),
            "Hook Variations": ("🪝", "re_fmt_hooks",    "🔥 Viral Hook Analyzer"),
            "CTA Options":     ("📢", "re_fmt_ctas",     None),
            "Comment Prompts": ("💬", "re_fmt_comments", None),
        }

        for fmt_name, (icon, fmt_key, dest_page) in sections.items():
            if not st.session_state.get(fmt_key):
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

        # ── Save all at once ──────────────────────────────────────────────────
        st.markdown("---")
        if st.button("📚 Save Full Content Suite to Library",
                     type="primary", use_container_width=True,
                     key="re_save_all"):
            ok, msg = save_post_to_library(
                result, "♻️ Repurposing Engine",
                tags=["repurposed", "full-suite"]
            )
            st.success(msg) if ok else st.warning(msg)

        # ── Download ──────────────────────────────────────────────────────────
        st.download_button(
            "📥 Download Full Suite (.txt)",
            data=result,
            file_name=f"content_suite_{st.session_state.get('re_niche','').replace(' ','_').lower()}.txt",
            mime="text/plain",
            use_container_width=True,
            key="re_download",
        )
