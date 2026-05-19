"""
Content Idea Generator — Generates a full content calendar and
post ideas by niche using proven LinkedIn content pillars.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context, stream_text
from library import save_post_to_library
from industry_profiles import get_industry_voice_block
from core.voice import HUMAN_VOICE_PRIMER, BANNED, HUMAN_SIGNATURES


CONTENT_PILLARS = {
    "Career Growth & Lessons":          "Hard lessons, career pivots, promotions, setbacks, and growth",
    "Industry Insights & Trends":       "What's changing in your field, predictions, news analysis",
    "Personal Stories (Vulnerability)": "Failures, imposter syndrome, real struggles and how you overcame them",
    "Contrarian / Hot Takes":           "Unpopular opinions that challenge the status quo in your field",
    "How-To & Tutorials":               "Step-by-step guides, frameworks, tactics that deliver real value",
    "Social Proof & Wins":              "Milestones, results, client outcomes — authentic, not braggy",
    "Motivational / Mindset":           "Beliefs, mindset shifts, daily practices — grounded in your experience",
    "Behind the Scenes":                "Day-in-the-life, building in public, tools, processes, decisions",
    "Collaboration & Community":        "Tagging others, sharing insights from your network, Q&As",
}

_BANNED_IDEAS = """
ADDITIONAL BANNED CONTENT ANGLES (on top of the global voice rules):
- "X lessons I learned from Y years in Z" (overused title structure)
- Anything starting with "I'm excited to..."
- "X things about [topic] that will change your life"
- Generic inspiration without a specific story or number behind it

BANNED PHRASES IN THE 'WHY IT WILL PERFORM' LINE — these patterns make the
output read like marketing copy. Cut every one of them:
- "offers a tangible lesson" / "offers a painful lesson"
- "challenges a common, entrenched mindset"
- "speaks directly to" (used as filler)
- "appeals to both X and Y audiences"
- "demystifies" anything
- "cuts through generic talk" / "cuts through the noise"
- "sparking a thoughtful discussion"
- "resonates with professionals at all levels"
- "connects with the universal struggle of X"
- "addresses a common pain point"

A 'why this works' line should sound like the writer's gut-check, not a pitch
deck. Two specific reasons in plain language. No marketing register.
"""


def _hashtag_block(use_nigerian_context: bool) -> str:
    """
    Build the hashtag instruction block. Hashtags on LinkedIn 2024-2026 carry
    almost no algorithmic weight — most strong creators use 0–3, never 5+.
    Long PascalCase chains read like dated SEO and signal 'this is AI output'.
    """
    base = (
        "TAGS — keep it light. LinkedIn no longer rewards long hashtag chains; "
        "0–3 tags is the modern norm. Top creators often skip them entirely.\n"
        "  - Output 2 tags maximum, lowercase by default (e.g. #legaltech, "
        "#contractlaw). Skip if nothing genuinely fits the post.\n"
        "  - No PascalCase stuffing like #LegalTechNigeriaForFounders. That "
        "reads like SEO from 2018.\n"
        "  - Never include more than one location/region tag.\n"
        "  - If a tag is generic (#leadership, #linkedin, #networking), drop "
        "it — it does nothing for the post."
    )
    if use_nigerian_context:
        base += (
            "\n  - At most ONE Nigeria-relevant tag where it actually fits "
            "(e.g. #lagostech, #nigerianlawyers). Don't force it."
        )
    return base


def build_ideas_prompt(niche, role, pillars, count, timeframe):
    pillar_list    = "\n".join([f"- {p}: {CONTENT_PILLARS[p]}" for p in pillars])
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche)

    # Hashtag rules — sane defaults regardless of mode, plus one extra line
    # of permission for Nigerian tags when the user has Nigerian Mode on.
    import streamlit as _st
    _ng_on = bool(_st.session_state.get("nigerian_mode", False))
    hashtag_rules = _hashtag_block(_ng_on)

    return f"""{HUMAN_VOICE_PRIMER}

You are working as a sharp editor generating LinkedIn content ideas — specific, usable, and grounded in how real practitioners in {niche} actually talk about their work.

Not generic. Not "share your journey". Real angles a real {niche} professional would actually post.{profile_ctx}
{industry_voice}

CREATOR:
- Niche: {niche}
- Background: {role}
- Posting window: {timeframe}
- Content pillars to use:
{pillar_list}

{BANNED}
{_BANNED_IDEAS}
{HUMAN_SIGNATURES}

Generate {count} content ideas.

CRITICAL — ANTI-TEMPLATE RULES (most important instruction in this prompt):

The {count} ideas must NOT all use the same micro-structure. If every entry
opens with a "[time], a [role] called me…" hook, or every "angle" line ends
with a generalised lesson, the output reads like a robot. Vary aggressively.

Distribute these opening types across the {count} ideas (use each at least
once if {count} >= 5):
  • Mid-scene story opener ("9pm Monday. The founder hadn't slept.")
  • Bold statement opener ("Most M&A due diligence in Lagos is theatre.")
  • Specific number opener ("18 hidden liens. One AI tool. Six minutes.")
  • Confession opener ("Almost declined the talk. Wasn't sure I was qualified.")
  • Contrarian claim opener ("The senior at NBA got it wrong.")
  • Direct address opener ("If you're a founder reviewing your own SaaS terms, stop.")

For each idea, output EXACTLY this format:

**[NUMBER]. [IDEA TITLE — 5-8 words, punchy, no colons unless needed]**
Pillar: [which pillar from the list]
Hook: [The exact 1-2 lines that open the post. No questions. Doesn't start with "I". Sounds like a person talking, not a press release.]
Angle: [2-3 sentences in plain conversational English. Name the specific tension. Use a real number, place, or institution. Use contractions naturally. NO "this highlights / this underscores / this is a testament to" framing.]
Why it works: [One short sentence — sounds like the writer's gut-check, not marketing copy. Plain language, max 18 words.]
Tags: [Apply the rules below. If no good tag fits, write "Tags: skip".]

{hashtag_rules}

---

After all {count} ideas, add:

**EVERGREEN PICKS (3 ideas that work any week):**
[Title + one short reason in plain English — no marketing voice]

**POST THIS WEEK:**
[The single idea most likely to land RIGHT NOW in {niche}, and the specific reason why this week. Two sentences max. Sound like a friend texting a recommendation, not a content strategist filing a report.]
"""


def render_content_ideas():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">Never Run Out of Ideas Again</div>
        <h1>💡 Content Idea Generator</h1>
        <p>Generate a full content calendar with real, usable post ideas tailored to your niche.</p>
    </div>
    """, unsafe_allow_html=True)

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)

    with col1:
        niche = st.text_input(
            "🎯 Your Niche / Industry",
            value=st.session_state.get("ci_niche", _p.get("industry", "")),
            placeholder="e.g., Legal Practice, Fintech, Real Estate, Oil & Gas",
            key="ci_niche",
        )
        role  = st.text_input(
            "👤 Your Role / Background",
            value=st.session_state.get("ci_role", _p.get("role", "")),
            placeholder="e.g., Corporate lawyer, 8 years, Lagos-based",
            key="ci_role",
        )
        count = st.slider("📊 Number of Ideas", min_value=5, max_value=20, value=10)

    with col2:
        timeframe = st.selectbox("📅 Content Timeframe",
                                  ["1 Week", "2 Weeks", "1 Month", "3 Months (90-day plan)"])
        pillars   = st.multiselect(
            "🏛️ Content Pillars (pick up to 5)",
            list(CONTENT_PILLARS.keys()),
            default=["Career Growth & Lessons", "How-To & Tutorials", "Contrarian / Hot Takes"],
            max_selections=5,
        )

    if pillars:
        st.markdown("**Selected Pillars:**")
        for p in pillars:
            st.caption(f"• **{p}**: {CONTENT_PILLARS[p]}")

    st.markdown("---")

    if st.button("🚀 Generate Content Ideas", type="primary", use_container_width=True):
        if not niche.strip():
            st.error("Please enter your niche.")
            return
        if not pillars:
            st.error("Please select at least one content pillar.")
            return

        try:
            st.info("⚡ Generating content ideas — streams in real time…")
            _stream_box = st.empty()
            with _stream_box.container():
                result = st.write_stream(stream_text(
                    build_ideas_prompt(niche, role, pillars, count, timeframe),
                    temperature=0.95, max_tokens=8000,
                ))
            _stream_box.empty()
            st.session_state["ci_last_result"] = result
            st.session_state["ci_last_niche"]  = niche
            st.session_state["ci_last_count"]  = count
        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            with st.expander("Error details"):
                import traceback as _tb
                st.code(_tb.format_exc())
            return

    # ── Result panel — survives reruns ─────────────────────────────────────
    result = st.session_state.get("ci_last_result", "")
    if not result:
        return

    _ni = st.session_state.get("ci_last_niche", niche)
    _ct = st.session_state.get("ci_last_count", count)

    st.success(f"{_ct} content ideas generated.")
    st.markdown("---")
    with st.expander("📄 Full Content Calendar", expanded=True):
        st.markdown(result)

    dl_col, sv_col, rs_col = st.columns(3)
    with dl_col:
        st.download_button(
            label="📥 Download Calendar",
            data=result,
            file_name=f"content_ideas_{_ni.replace(' ', '_').lower()}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with sv_col:
        if st.button("📚 Save to Post Library", use_container_width=True,
                     key="ci_save_library"):
            ok, msg = save_post_to_library(result, "💡 Content Ideas",
                                           tags=["content-calendar", _ni.lower()[:20]])
            st.success(msg) if ok else st.warning(msg)
    with rs_col:
        if st.button("🔄 New ideas", use_container_width=True, key="ci_reset"):
            for k in ("ci_last_result", "ci_last_niche", "ci_last_count"):
                st.session_state.pop(k, None)
            st.rerun()
