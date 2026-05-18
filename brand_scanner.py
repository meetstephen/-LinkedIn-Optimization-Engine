"""
Brand Consistency Scanner — Compares what your profile says
versus what your content says, and scores the gap.

"Your profile says X but your posts say Y" — this catches it.
"""
import streamlit as st
from gemini_client import get_profile_context, stream_text
from library import save_post_to_library


def build_scanner_prompt(
    headline: str, about: str, recent_posts: str,
    claimed_niche: str, claimed_audience: str,
) -> str:
    profile_ctx = get_profile_context()
    return f"""You are a brand strategist who analyses LinkedIn profiles the way a
talent scout or investor does — looking for consistency, clarity, and authenticity.
You're famous for finding the gap between what someone claims to be and what their
content actually demonstrates.{profile_ctx}

PROFILE DATA:
Headline: {headline}
About Section: {about or 'Not provided'}
Claimed Niche: {claimed_niche or 'Not specified'}
Claimed Target Audience: {claimed_audience or 'Not specified'}

RECENT POSTS / CONTENT SAMPLES:
\"\"\"{recent_posts}\"\"\"

Analyse the consistency between their profile positioning and their actual content.
Be direct. Be specific. Quote the exact lines that create the gaps.

---

## BRAND CONSISTENCY SCORE: XX/100

| Dimension | Score | Finding |
|-----------|-------|---------|
| Headline ↔ Content alignment | X/20 | [specific finding] |
| Niche clarity | X/20 | [specific finding] |
| Audience targeting | X/20 | [specific finding] |
| Tone consistency | X/20 | [specific finding] |
| Authority signals | X/20 | [specific finding] |

**OVERALL: XX/100 — [Fragmented / Inconsistent / Developing / Consistent / Authoritative]**

## THE CORE GAP
One paragraph. Name the single most damaging inconsistency.
Quote the profile line. Quote the content that contradicts it.
Say exactly what a visitor thinks when they notice it.

## WHAT YOUR PROFILE PROMISES
List 3-4 things your headline/about section signals about you.

## WHAT YOUR CONTENT DELIVERS
List 3-4 things your recent posts actually demonstrate.

## THE GAPS (in order of damage)
For each gap:
❌ Profile says: "[exact quote]"
📝 Content shows: "[what the posts actually demonstrate]"
💥 Reader confusion: "[what a visitor thinks when they see this]"
✅ Fix: "[one specific, actionable change]"

## WHAT'S WORKING (keep this)
2-3 things that ARE consistent and should be preserved.

## YOUR UNIFIED BRAND STATEMENT
Write a one-sentence brand statement that is ACTUALLY true based on both
the profile AND the content combined:
"[Name] helps [specific who] [do specific what] by [specific how] — as seen in [specific content proof]."

## 5-DAY REALIGNMENT PLAN
Day 1: [exact profile change — which section, what to add/remove]
Day 2: [exact content change — what type of post, what angle]
Day 3: [exact engagement change — where to show up, what to say]
Day 4: [exact storytelling fix — which story to tell that bridges the gap]
Day 5: [exact audit — what to check and what to cut]
"""


def render_brand_scanner():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">What Your Profile Says vs What You Post</div>
        <h1>🔍 Brand Consistency Scanner</h1>
        <p>Scores the gap between your LinkedIn profile and your content. Most people have one. Almost no tool catches it.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(3)
    with col1:
        st.info("**The Problem**\n\nYour headline says 'Fintech Strategist' but your posts are all about personal development. A visitor notices in 8 seconds. They leave.")
    with col2:
        st.warning("**What This Does**\n\nCompares your profile positioning against your recent content. Scores 5 dimensions. Names the exact gap. Gives a 5-day fix.")
    with col3:
        st.success("**The Result**\n\nA unified brand statement that's true based on BOTH your profile and content — not just what you hope people think.")

    st.markdown("---")

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)
    with col1:
        headline = st.text_input(
            "📌 Your LinkedIn Headline",
            value=st.session_state.get("bs_headline", _p.get("headline", "")),
            placeholder="e.g., Corporate Lawyer | SAN | CAMA 2020 Specialist",
            key="bs_headline",
        )
        claimed_niche = st.text_input(
            "🎯 What niche do you claim to be in?",
            value=st.session_state.get("bs_niche", _p.get("industry", "")),
            placeholder="e.g., Nigerian Corporate Law, B2B Fintech",
            key="bs_niche",
        )
        claimed_audience = st.text_input(
            "👥 Who do you claim to serve?",
            value=st.session_state.get("bs_audience", _p.get("audience", "")),
            placeholder="e.g., Nigerian founders, Mid-size law firms",
            key="bs_audience",
        )
        about = st.text_area(
            "📝 Your LinkedIn About Section",
            placeholder="Paste your About section here (or the first 300 words)…",
            height=140,
            key="bs_about",
        )

    with col2:
        recent_posts = st.text_area(
            "📋 Paste 3-5 Recent Posts",
            placeholder=(
                "Paste your recent LinkedIn posts here, separated by --- \n\n"
                "The more content you paste, the more accurate the analysis.\n\n"
                "Even rough drafts or post ideas count."
            ),
            height=340,
            key="bs_posts",
        )

    st.markdown("---")

    if st.button(
        "🔍 Scan My Brand Consistency",
        type="primary",
        use_container_width=True,
        disabled=not (headline.strip() and recent_posts.strip()),
    ):
        if not headline.strip():
            st.error("Please enter your headline.")
            return
        if not recent_posts.strip():
            st.error("Please paste at least one recent post.")
            return

        st.info("⚡ Scanning your brand — analysis streams in real time…")
        try:
            result = st.write_stream(stream_text(
                build_scanner_prompt(
                    headline, about, recent_posts,
                    claimed_niche, claimed_audience,
                ),
                temperature=0.7, max_tokens=6000,
            ))
            st.session_state["bs_last_result"] = result
        except Exception as e:
            st.error(f"Scan failed: {str(e)}")
            with st.expander("🔍 Error details"):
                import traceback as _tb
                st.code(_tb.format_exc())
            return

    # ── Result panel — survives reruns ─────────────────────────────────────
    result = st.session_state.get("bs_last_result", "")
    if not result:
        return

    st.success("Brand scan complete.")
    st.markdown("---")
    with st.expander("📄 Full Brand Report", expanded=True):
        st.markdown(result)

    col_save, col_dl, col_reset = st.columns(3)
    with col_save:
        if st.button("📚 Save to Post Library", use_container_width=True,
                     key="bs_save"):
            ok, msg = save_post_to_library(
                result, "🔍 Brand Scanner",
                tags=["brand-audit", "consistency"]
            )
            st.success(msg) if ok else st.warning(msg)
    with col_dl:
        st.download_button(
            "📥 Download Brand Report",
            data=result,
            file_name="brand_consistency_report.txt",
            mime="text/plain",
            use_container_width=True,
            key="bs_dl",
        )
    with col_reset:
        if st.button("🔄 Run a fresh scan", use_container_width=True, key="bs_reset"):
            st.session_state.pop("bs_last_result", None)
            st.rerun()
