"""
Engagement Intelligence — Strategic comments, DM follow-ups,
networking responses, and lead-conversion messages.

Real LinkedIn growth happens in the comments section.
"""
import streamlit as st
from gemini_client import get_profile_context, stream_text
from industry_profiles import get_industry_voice_block
from library import save_post_to_library

_BANNED = """
BANNED: "game-changer", "leverage", "synergy", "thought leader", "I'm excited",
"hustle", "disrupt", "innovative", "circle back", "touch base", "move the needle",
"let's connect!", "great post!", "so true!", "love this!", "absolutely!", "100%!"
"""


def build_comment_prompt(post_text: str, goal: str, niche: str) -> str:
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche)
    return f"""You write LinkedIn comments that stop people mid-scroll — not "great post!" filler but
comments that add a genuine insight, establish the commenter's authority, and make the post author
want to visit their profile.{profile_ctx}
{industry_voice}

POST BEING COMMENTED ON:
\"\"\"{post_text}\"\"\"

GOAL: {goal}
NICHE: {niche}

{_BANNED}

Write 5 strategic comments. Each comment:
- Adds ONE genuine insight the original post didn't cover
- 2-4 sentences maximum
- Never starts with "Great post", "Love this", "So true", or any empty affirmation
- Ends with either a genuine question OR a soft reference to your own experience
- Reads like it came from a real practitioner, not a bot

COMMENT 1 — [Authority Add: add a specific fact, stat, or experience that builds on the post]
COMMENT 2 — [Respectful Challenge: a polite counter-angle or nuance the post missed]
COMMENT 3 — [Story Micro: one specific sentence from your own experience that relates]
COMMENT 4 — [Question Add: a genuine question that deepens the conversation]
COMMENT 5 — [Value Bridge: connects this post's topic to your own niche specifically]

After each comment:
📌 Best used when: [one line on timing/context]
🎯 Likely result: [one line on expected engagement]
"""


def build_dm_prompt(context: str, dm_type: str, niche: str) -> str:
    profile_ctx = get_profile_context()
    return f"""You write LinkedIn DMs that feel like a message from a thoughtful professional —
not a sales pitch, not a connection request spam, not a cold outreach template.{profile_ctx}

CONTEXT: {context}
DM TYPE: {dm_type}
NICHE: {niche}

{_BANNED}

Write 3 DM variations for this situation. Each:
- Under 80 words (short DMs get read; long DMs get ignored)
- First sentence references something specific (their post, their profile, shared context)
- Clear but low-pressure ask or offer
- Never "I wanted to reach out", "I hope this finds you well", "quick question"
- Signed with first name only

DM 1 — [Warm, conversational tone]
DM 2 — [Direct, value-first tone]
DM 3 — [Question-led, curiosity tone]

After each:
✅ When to use: [one line]
⚡ Subject line if sending as InMail: [under 8 words]
"""


def build_networking_prompt(situation: str, niche: str) -> str:
    profile_ctx = get_profile_context()
    return f"""You write LinkedIn connection messages and follow-up responses that convert strangers
into genuine professional relationships — not just connection count inflators.{profile_ctx}

SITUATION: {situation}
NICHE: {niche}

{_BANNED}

Write:

CONNECTION REQUEST NOTE (under 300 characters):
[Specific to this situation — no generic "I'd love to connect" templates]

FOLLOW-UP AFTER ACCEPTANCE (under 100 words):
[Adds value immediately — share a resource, insight, or genuine compliment on their work]

REPLY TO SOMEONE WHO COMMENTED ON YOUR POST (under 60 words):
[Acknowledges their comment specifically, extends the conversation, subtly invites further dialogue]

REPLY TO A CONNECTION REQUEST FROM A STRANGER (under 80 words):
[Warm but qualifying — find out why they connected before pitching anything]
"""


def render_engagement_intelligence():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">Where Real LinkedIn Growth Happens</div>
        <h1>💬 Engagement Intelligence</h1>
        <p>Strategic comments, DMs, networking responses, and lead-conversion messages — crafted for your industry.</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(
        "**90% of LinkedIn creators only post.** The top 10% post AND engage strategically in comments. "
        "Every comment on the right post is a profile visit. Every profile visit is a potential follower, client, or collaborator."
    )

    _p = st.session_state.get("user_profile", {})
    _niche = _p.get("industry", "")

    tab1, tab2, tab3 = st.tabs([
        "💬 Strategic Comments",
        "📨 DM Templates",
        "🤝 Networking Responses",
    ])

    # ── Tab 1: Strategic Comments ─────────────────────────────────────────────
    with tab1:
        st.subheader("💬 Strategic Comment Generator")
        st.markdown(
            "Paste a post you want to comment on. Get 5 comments that "
            "add value, establish authority, and drive profile visits."
        )

        post_text = st.text_area(
            "📋 Paste the LinkedIn post you want to comment on",
            placeholder="Paste the full post text here…",
            height=180,
            key="ei_post_text",
        )
        col1, col2 = st.columns(2)
        with col1:
            comment_goal = st.selectbox(
                "🎯 Comment Goal",
                [
                    "Build authority in my niche",
                    "Drive profile visits",
                    "Start a genuine conversation",
                    "Showcase specific expertise",
                    "Position for a soft pitch",
                ],
                key="ei_comment_goal",
            )
        with col2:
            comment_niche = st.text_input(
                "🏭 Your Industry",
                value=_niche,
                placeholder="e.g., Legal Practice, Fintech",
                key="ei_comment_niche",
            )

        if st.button("💬 Generate Strategic Comments", type="primary",
                     use_container_width=True, key="ei_gen_comments",
                     disabled=not post_text.strip()):
            try:
                st.info("⚡ Generating comments…")
                result = st.write_stream(stream_text(
                    build_comment_prompt(post_text, comment_goal,
                                         comment_niche or "Professional"),
                    temperature=0.85, max_tokens=4000,
                ))
                st.session_state["ei_comments_result"] = result
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

        # Persistent result + save block
        _r = st.session_state.get("ei_comments_result", "")
        if _r:
            st.markdown("---")
            with st.expander("📄 Generated Comments", expanded=True):
                st.markdown(_r)
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("📚 Save to Library", key="ei_save_comments",
                             use_container_width=True):
                    ok, msg = save_post_to_library(
                        _r, "💬 Engagement Intelligence",
                        tags=["comments", "engagement"]
                    )
                    st.success(msg) if ok else st.warning(msg)
            with sc2:
                if st.button("🔄 Clear", key="ei_reset_comments",
                             use_container_width=True):
                    st.session_state.pop("ei_comments_result", None)
                    st.rerun()

    # ── Tab 2: DM Templates ───────────────────────────────────────────────────
    with tab2:
        st.subheader("📨 DM Template Generator")
        st.markdown(
            "Short DMs get read. Long DMs get ignored. "
            "Generate 3 variations under 80 words each."
        )

        dm_context = st.text_area(
            "📋 Context for this DM",
            placeholder=(
                "e.g., 'They posted about struggling with CAMA compliance. "
                "I'm a corporate lawyer. I want to offer a free 15-minute call.'"
            ),
            height=120,
            key="ei_dm_context",
        )
        col1, col2 = st.columns(2)
        with col1:
            dm_type = st.selectbox(
                "📨 DM Type",
                [
                    "Cold outreach (never met)",
                    "After they commented on my post",
                    "After I commented on their post",
                    "Following up after connecting",
                    "Lead conversion (interested prospect)",
                    "Collaboration proposal",
                ],
                key="ei_dm_type",
            )
        with col2:
            dm_niche = st.text_input(
                "🏭 Your Industry",
                value=_niche,
                placeholder="e.g., Legal Practice, Fintech",
                key="ei_dm_niche",
            )

        if st.button("📨 Generate DM Templates", type="primary",
                     use_container_width=True, key="ei_gen_dms",
                     disabled=not dm_context.strip()):
            try:
                st.info("⚡ Writing your DMs…")
                result = st.write_stream(stream_text(
                    build_dm_prompt(dm_context, dm_type,
                                    dm_niche or "Professional"),
                    temperature=0.82, max_tokens=3000,
                ))
                st.session_state["ei_dms_result"] = result
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

        _r = st.session_state.get("ei_dms_result", "")
        if _r:
            st.markdown("---")
            with st.expander("📄 Generated DMs", expanded=True):
                st.markdown(_r)
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("📚 Save to Library", key="ei_save_dms",
                             use_container_width=True):
                    ok, msg = save_post_to_library(
                        _r, "💬 Engagement Intelligence",
                        tags=["dm", "outreach"]
                    )
                    st.success(msg) if ok else st.warning(msg)
            with sc2:
                if st.button("🔄 Clear", key="ei_reset_dms",
                             use_container_width=True):
                    st.session_state.pop("ei_dms_result", None)
                    st.rerun()

    # ── Tab 3: Networking Responses ───────────────────────────────────────────
    with tab3:
        st.subheader("🤝 Networking Response Generator")
        st.markdown(
            "Connection requests, follow-ups, post replies. "
            "Templates that sound like you wrote them, not a bot."
        )

        net_situation = st.text_area(
            "📋 Describe the situation",
            placeholder=(
                "e.g., 'A senior fintech PM just accepted my connection request. "
                "I want to start a conversation without pitching anything immediately.'"
            ),
            height=120,
            key="ei_net_situation",
        )
        net_niche = st.text_input(
            "🏭 Your Industry",
            value=_niche,
            placeholder="e.g., Legal Practice, Fintech",
            key="ei_net_niche",
        )

        if st.button("🤝 Generate Networking Templates", type="primary",
                     use_container_width=True, key="ei_gen_net",
                     disabled=not net_situation.strip()):
            try:
                st.info("⚡ Writing your responses…")
                result = st.write_stream(stream_text(
                    build_networking_prompt(
                        net_situation, net_niche or "Professional"
                    ),
                    temperature=0.8, max_tokens=3000,
                ))
                st.session_state["ei_net_result"] = result
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

        _r = st.session_state.get("ei_net_result", "")
        if _r:
            st.markdown("---")
            with st.expander("📄 Generated Templates", expanded=True):
                st.markdown(_r)
            sc1, sc2 = st.columns(2)
            with sc1:
                if st.button("📚 Save to Library", key="ei_save_net",
                             use_container_width=True):
                    ok, msg = save_post_to_library(
                        _r, "💬 Engagement Intelligence",
                        tags=["networking", "connection"]
                    )
                    st.success(msg) if ok else st.warning(msg)
            with sc2:
                if st.button("🔄 Clear", key="ei_reset_net",
                             use_container_width=True):
                    st.session_state.pop("ei_net_result", None)
                    st.rerun()
