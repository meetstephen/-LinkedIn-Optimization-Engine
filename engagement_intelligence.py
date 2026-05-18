"""
Engagement Intelligence — Strategic comments, DM follow-ups,
networking responses, and lead-conversion messages.

Real LinkedIn growth happens in the comments section.
"""
import streamlit as st
from gemini_client import get_profile_context, stream_text
from industry_profiles import get_industry_voice_block
from library import save_post_to_library
from core.voice import HUMAN_VOICE_PRIMER, SHORT_PRIMER, BANNED


def build_comment_prompt(post_text: str, goal: str, niche: str) -> str:
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche)

    return f"""{HUMAN_VOICE_PRIMER}

You are writing LinkedIn comments that stop people mid-scroll — not "great post!" filler but comments that add a genuine insight, establish the commenter's authority, and make the post author want to visit their profile.{profile_ctx}
{industry_voice}

THE POST BEING COMMENTED ON:
\"\"\"
{post_text}
\"\"\"

COMMENTER'S GOAL: {goal}
COMMENTER'S NICHE: {niche}

{BANNED}

Additional rules specific to comments:
- "great post!", "love this!", "so true!", "absolutely!", "100%!" — banned
- "Thanks for sharing this!" — banned
- Pure agreement without adding anything — banned

────────────────────────────────────────────────
STEP 1 — INTERNAL ANALYSIS (do not include in output)
Before writing anything, identify silently:
  a) The post's CORE CLAIM (one sentence — what is the author actually arguing?)
  b) The post's SPECIFIC DETAILS (numbers, names, places, moments worth referencing)
  c) The post's UNDERLYING ASSUMPTION (what does the author take for granted?)
  d) The post's GAP (what specific angle or nuance did the author leave out?)

This step is your private working — never write it in the response.

STEP 2 — ALIGNMENT CHECK
Every single comment you write must satisfy ALL of these:
  ✅ Quote or directly reference at least one specific detail from the post (a number, phrase, name, claim)
  ✅ Build on the author's exact thesis — not a tangentially related topic
  ✅ Match the post's emotional register (don't crack jokes on a serious post; don't get heavy on a lighthearted one)
  ✅ Sound like a peer of the author, not a fan or a student
  ✅ Read like one specific human typed it — not a template

If a comment doesn't pass this check, rewrite it before showing it.

────────────────────────────────────────────────
STEP 3 — OUTPUT (this is what gets shown)

Write 5 strategic comments. Each comment:
- 2-4 sentences maximum
- Never starts with "Great post", "Love this", "So true", or any empty affirmation
- Never starts with the commenter's name or "I" (start with the substance)
- References something specific from the post in the FIRST sentence
- Ends with either a genuine question OR a soft reference to the commenter's own experience
- Reads like it came from a real practitioner, not a bot

For each comment, deliver this format exactly:

────────────────────────────────
**COMMENT 1 — Authority Add**
[The actual comment, 2-4 sentences, that adds a specific fact, stat, or experience that builds on the post's exact claim.]

📎 Anchored to: "[the specific phrase, claim, or number from the post this comment locks onto]"
🧠 What it adds: [one line — the new value this comment brings to the thread]
🎯 Likely result: [one line — expected reply behaviour from the author]

────────────────────────────────
**COMMENT 2 — Respectful Challenge**
[A polite counter-angle or nuance the post missed. Must sound like collegial disagreement, not a takedown.]

📎 Anchored to: "[the specific assumption from the post being challenged]"
🧠 What it adds: [the nuance being introduced]
🎯 Likely result: [expected behaviour]

────────────────────────────────
**COMMENT 3 — Story Micro**
[One specific sentence from your own experience that mirrors or extends the post's situation. Concrete details: names a place, a number, a moment.]

📎 Anchored to: "[which part of the post this story echoes]"
🧠 What it adds: [the personal proof being offered]
🎯 Likely result: [expected behaviour]

────────────────────────────────
**COMMENT 4 — Question Add**
[A genuine question that deepens the conversation. Not "what do you think?" — a question that opens a specific second layer the author didn't address.]

📎 Anchored to: "[the specific claim or detail the question deepens]"
🧠 What it adds: [the new angle the question invites]
🎯 Likely result: [expected behaviour]

────────────────────────────────
**COMMENT 5 — Value Bridge**
[Connects the post's topic to the commenter's specific niche ({niche}) without making it about them. Must feel earned, not pivot-and-pitch.]

📎 Anchored to: "[the bridge point — what part of the post connects to the commenter's niche]"
🧠 What it adds: [the cross-domain insight]
🎯 Likely result: [expected behaviour]
────────────────────────────────

After all 5 comments, add this final block:

**📊 ALIGNMENT REPORT**
Post's core claim: [one sentence — what the author actually argued]
Post's emotional register: [analytical / vulnerable / contrarian / celebratory / instructive]
The single best comment for this specific goal ({goal}): [Comment N — one-line reason]
"""


def build_dm_prompt(context: str, dm_type: str, niche: str) -> str:
    profile_ctx = get_profile_context()
    return f"""{SHORT_PRIMER}

You are writing LinkedIn DMs that feel like a message from a thoughtful professional — not a sales pitch, not a connection request spam, not a cold outreach template.{profile_ctx}

CONTEXT: {context}
DM TYPE: {dm_type}
NICHE: {niche}

{BANNED}

Additional DM-specific rules:
- "I wanted to reach out" — banned
- "I hope this finds you well" — banned
- "quick question" — banned (it's never quick and they know it)
- No fake-warmth openers ("Hope you're having an amazing week!")

Write 3 DM variations for this situation. Each:
- Under 80 words (short DMs get read; long DMs get ignored)
- First sentence references something specific (their post, their profile, shared context)
- Clear but low-pressure ask or offer
- Signed with first name only

────────────────────────────────
**DM 1 — Warm, conversational tone**
[The DM]

✅ When to use: [one line]
⚡ Subject line if sending as InMail: [under 8 words]

────────────────────────────────
**DM 2 — Direct, value-first tone**
[The DM]

✅ When to use: [one line]
⚡ Subject line if sending as InMail: [under 8 words]

────────────────────────────────
**DM 3 — Question-led, curiosity tone**
[The DM]

✅ When to use: [one line]
⚡ Subject line if sending as InMail: [under 8 words]
"""


def build_networking_prompt(situation: str, niche: str) -> str:
    profile_ctx = get_profile_context()
    return f"""{SHORT_PRIMER}

You are writing LinkedIn connection messages and follow-up responses that turn strangers into genuine professional relationships — not connection-count inflators.{profile_ctx}

SITUATION: {situation}
NICHE: {niche}

{BANNED}

Write the four pieces below. Each must sound like a specific human wrote it for this specific situation — not a template.

**CONNECTION REQUEST NOTE** (under 300 characters):
[Specific to this situation — no generic "I'd love to connect" templates.]

**FOLLOW-UP AFTER ACCEPTANCE** (under 100 words):
[Adds value immediately — a resource, an insight, or genuine engagement with their work. Not a pitch.]

**REPLY TO SOMEONE WHO COMMENTED ON YOUR POST** (under 60 words):
[Acknowledges their comment specifically — quote one phrase from it — extends the conversation, subtly invites further dialogue.]

**REPLY TO A CONNECTION REQUEST FROM A STRANGER** (under 80 words):
[Warm but qualifying — find out why they connected before pitching anything.]
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
            "stay locked to the author's actual thesis, add value, and drive profile visits."
        )

        post_text = st.text_area(
            "📋 Paste the LinkedIn post you want to comment on",
            placeholder=(
                "Paste the FULL post text here — the more complete the post, "
                "the more accurately the comments will align with the author's thesis."
            ),
            height=200,
            key="ei_post_text",
        )

        # Live alignment hint
        if post_text.strip():
            _wc = len(post_text.split())
            if _wc < 30:
                st.warning(
                    f"⚠️ Only {_wc} words — comments may misalign. Paste at least 50–80 words "
                    "of the original post for accurate anchoring."
                )
            else:
                st.caption(f"✅ {_wc} words — enough context for accurate comment alignment.")

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
            if len(post_text.strip()) < 40:
                st.error(
                    "Please paste more of the post (at least ~40 characters). "
                    "Without enough context, the comments won't align properly with the author's thesis."
                )
            else:
                try:
                    st.info("⚡ Reading the post and generating aligned comments…")
                    _stream_box = st.empty()
                    with _stream_box.container():
                        result = st.write_stream(stream_text(
                            build_comment_prompt(post_text, comment_goal,
                                                 comment_niche or "Professional"),
                            temperature=0.78, max_tokens=4500,
                        ))
                    _stream_box.empty()
                    st.session_state["ei_comments_result"] = result
                except Exception as e:
                    st.error(f"Generation failed: {str(e)}")

        # Persistent result + save block
        _r = st.session_state.get("ei_comments_result", "")
        if _r:
            st.markdown("---")
            with st.expander("📄 Generated Comments — each anchored to a specific line in the post", expanded=True):
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
                _stream_box = st.empty()
                with _stream_box.container():
                    result = st.write_stream(stream_text(
                        build_dm_prompt(dm_context, dm_type,
                                        dm_niche or "Professional"),
                        temperature=0.82, max_tokens=3000,
                    ))
                _stream_box.empty()
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
                _stream_box = st.empty()
                with _stream_box.container():
                    result = st.write_stream(stream_text(
                        build_networking_prompt(
                            net_situation, net_niche or "Professional"
                        ),
                        temperature=0.8, max_tokens=3000,
                    ))
                _stream_box.empty()
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
