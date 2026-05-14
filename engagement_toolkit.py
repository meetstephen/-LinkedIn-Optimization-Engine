"""
Engagement Toolkit — Hook generator, CTA generator, hashtag optimizer,
and posting time analyzer all in one.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context
from industry_profiles import get_industry_voice_block


POSTING_TIMES = {
    "🇳🇬 Nigeria / West Africa (WAT)": {
        "best_days":  ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["7:00–9:00 AM WAT", "12:00–2:00 PM WAT", "6:00–8:00 PM WAT"],
        "avoid":      "Monday mornings, Friday after 3pm, Saturday & Sunday",
        "note":       "WAT = UTC+1. Most Nigerian LinkedIn users are on mobile — hook must work on a small screen.",
    },
    "North America (EST/PST)": {
        "best_days":  ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["7:00–9:00 AM EST", "12:00–1:00 PM EST", "5:00–6:00 PM EST"],
        "avoid":      "Friday afternoon, Saturday, Sunday morning",
        "note":       "",
    },
    "Europe (GMT/CET)": {
        "best_days":  ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["7:00–9:00 AM CET", "12:00–2:00 PM CET", "6:00–8:00 PM CET"],
        "avoid":      "Monday morning, Friday evening, weekends",
        "note":       "",
    },
    "Asia Pacific (SGT/AEST)": {
        "best_days":  ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["8:00–10:00 AM SGT", "12:00–1:00 PM SGT", "7:00–9:00 PM SGT"],
        "avoid":      "Monday morning, Friday afternoon",
        "note":       "",
    },
    "Global / Mixed Audience": {
        "best_days":  ["Tuesday", "Wednesday"],
        "peak_times": ["9:00 AM UTC", "1:00 PM UTC"],
        "avoid":      "Weekends and major holidays",
        "note":       "",
    },
}

_BANNED = """
BANNED WORDS & PHRASES — if any appear in output, the response fails:
  "game-changer", "dive in", "let's dive in", "let's unpack", "leverage", "synergy",
  "actionable", "thought leader", "passionate about", "journey", "crushing it",
  "hustle", "disrupt", "innovative", "cutting-edge", "best practices",
  "I'm excited to share", "I'm thrilled", "in today's fast-paced world",
  "at the end of the day", "needless to say", "in conclusion", "circle back",
  "touch base", "move the needle", "unlock", "level up", "deep dive",
  "masterclass", "playbook", "paradigm shift", "pro tip:", "hot take:",
  "this is your sign", "unpopular opinion:" (as opener), "period." (mic-drop ending),
  "we need to talk about", "value-add", "low-hanging fruit", "win-win"
"""


def build_hooks_prompt(topic, tone, count, niche=""):
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche) if niche.strip() else ""
    return f"""You write LinkedIn hooks the way a great headline writer works — every word earns its place, and the reader has no choice but to keep reading.{profile_ctx}
{industry_voice}
Write {count} hooks for this topic: {topic}
Tone: {tone}

{_BANNED}

Hook rules — non-negotiable:
- Never open with "I" as the first word
- No questions — statements outperform questions every time on LinkedIn
- Max 12 words per hook ideally, 15 absolute maximum
- Each hook must use a DIFFERENT psychological trigger
- No emojis in the hook line itself
- Use specifics: real numbers, real places, real moments — not vague gestures

Psychological triggers to distribute across the {count} hooks:
  curiosity gap, specific number, confession, bold claim, direct address,
  before/after contrast, shock stat, story opening, counterintuitive truth,
  named-person authority ("Warren Buffett does X. Most people do Y.")

For each hook, on a new line add:
🧠 Trigger: [name] | Why it stops scrolling: [one specific sentence — name the mechanism]

Number them 1 through {count}. No preamble.
"""


def build_cta_prompt(post_context, cta_goal, niche=""):
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(niche) if niche.strip() else ""
    return f"""You write CTAs for LinkedIn posts that feel like a natural end to the conversation — not a sales pitch, not a desperate ask. The best CTAs make the reader think they thought of the response themselves.{profile_ctx}
{industry_voice}
Post context: {post_context}
Goal: {cta_goal}

{_BANNED}

Additional CTA rules:
- No "drop a comment below" — they know how comments work
- No "hit the like button" or "smash that follow"
- No "I'd love to hear your thoughts" — weak and predictable
- Every CTA should feel like something a real person would actually say at the end of a conversation

Write 8 CTAs across 4 categories:

**QUESTION CTAs** (invite real responses — genuinely curious, not fake):
1. [CTA]
2. [CTA]

**ACTION CTAs** (get them to do one specific thing):
3. [CTA]
4. [CTA]

**SHARE CTAs** (give them a reason to repost — not "please share"):
5. [CTA]
6. [CTA]

**SOFT CTAs** (low commitment, high warmth — for community-building posts):
7. [CTA]
8. [CTA]

After each: 🎯 Use when: [one-line context for when this CTA works best]
"""


def build_hashtag_prompt(post_content, industry):
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(industry) if industry.strip() else ""
    ng_context     = "\nNigerian context: include Nigeria-specific hashtags where relevant (e.g. #NigeriaLinkedIn #LagosBusinesses #NaijaTwitter #MadeInNigeria #AfricanBusiness)." if st.session_state.get("nigerian_mode") else ""
    return f"""You know how LinkedIn hashtags actually work — not in theory, in practice. Most people either use 30 generic ones or none at all. You find the specific combination that puts a post in front of the right people.{profile_ctx}
{industry_voice}
Post: {post_content}
Industry: {industry}{ng_context}

Give me a 3-tier hashtag strategy:

## TIER 1 — BROAD (1M+ followers)
3 tags. High reach, high competition. Include only if the post topic is genuinely broad.
[hashtag] — [estimated followers] — [why include despite competition]

## TIER 2 — MID-RANGE (100K–1M)
3 tags. The sweet spot for most posts.
[hashtag] — [estimated followers] — [why this specific tag for this specific post]

## TIER 3 — NICHE (10K–100K)
3 tags. Smaller reach, higher engagement rate. Often the best performing tier.
[hashtag] — [estimated followers] — [the specific audience this reaches]

## COPY THESE (paste directly into LinkedIn after your post):
#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8 #tag9

## 2 MISTAKES MOST PEOPLE MAKE WITH HASHTAGS IN {industry.upper() or "YOUR INDUSTRY"}
Specific to this post — not generic hashtag advice.
"""


def render_engagement_toolkit():
    st.header("⚡ Engagement Toolkit")
    st.markdown("Hooks, CTAs, hashtags, and timing — everything you need to maximise reach on every post.")

    tab1, tab2, tab3, tab4 = st.tabs(["🪝 Hook Generator", "📢 CTA Generator", "#️⃣ Hashtag Optimizer", "⏰ Posting Times"])

    with tab1:
        st.subheader("🪝 Viral Hook Generator")
        st.markdown("The hook is 90% of your reach. Get multiple options across different psychological triggers.")

        col1, col2 = st.columns(2)
        with col1:
            hook_topic = st.text_area("📌 Topic / Post Idea",
                                       placeholder="e.g., I lost a ₦4M client because of one clause I didn't check",
                                       height=120, key="hook_topic")
            hook_niche = st.text_input("🏭 Your Industry (optional)",
                                        placeholder="e.g., Legal Practice, Fintech, Real Estate",
                                        key="hook_niche",
                                        help="Unlocks industry-specific hook archetypes")
        with col2:
            hook_tone  = st.selectbox("🎭 Tone",
                                       ["Storytelling", "Shocking", "Inspirational", "Contrarian", "Educational", "Vulnerability"],
                                       key="hook_tone")
            hook_count = st.slider("Number of Hooks", 5, 15, 8, key="hook_count")

        if st.button("⚡ Generate Hooks", type="primary", use_container_width=True, key="gen_hooks"):
            if not hook_topic.strip():
                st.error("Please enter a topic.")
            else:
                with st.spinner("Writing your hooks…"):
                    try:
                        result = generate_text(
                            build_hooks_prompt(hook_topic, hook_tone, hook_count,
                                               niche=st.session_state.get("hook_niche", "")),
                            temperature=0.92,
                            max_tokens=6000,
                        )
                        st.success("✅ Hooks generated!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with tab2:
        st.subheader("📢 CTA Generator")
        st.markdown("The CTA decides whether your post stays read or gets shared.")

        col1, col2 = st.columns(2)
        with col1:
            cta_context = st.text_area("📝 Post Topic/Context",
                                        placeholder="e.g., A post about 5 lessons from 10 years in legal practice in Lagos",
                                        height=100, key="cta_context")
            cta_niche   = st.text_input("🏭 Your Industry (optional)",
                                         placeholder="e.g., Legal Practice, Fintech",
                                         key="cta_niche")
        with col2:
            cta_goal    = st.selectbox("🎯 CTA Goal",
                                        ["Drive Comments", "Drive Shares/Reposts", "Generate DMs/Leads",
                                         "Build Community", "Get Profile Views"],
                                        key="cta_goal")

        if st.button("⚡ Generate CTAs", type="primary", use_container_width=True, key="gen_ctas"):
            if not cta_context.strip():
                st.error("Please enter your post context.")
            else:
                with st.spinner("Writing CTAs…"):
                    try:
                        result = generate_text(
                            build_cta_prompt(cta_context, cta_goal,
                                             niche=st.session_state.get("cta_niche", "")),
                            temperature=0.82,
                            max_tokens=6000,
                        )
                        st.success("✅ CTAs generated!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with tab3:
        st.subheader("#️⃣ Hashtag Optimizer")
        st.markdown("Get a 3-tier hashtag strategy that balances reach and targeting.")

        col1, col2 = st.columns(2)
        with col1:
            ht_content  = st.text_area("📝 Post Content or Topic",
                                        placeholder="Paste your post or describe your topic…",
                                        height=120, key="ht_content")
        with col2:
            ht_industry = st.text_input("🏢 Industry",
                                         placeholder="e.g., Legal Practice, Fintech, Real Estate",
                                         key="ht_industry")

        if st.button("🔍 Optimize Hashtags", type="primary", use_container_width=True, key="gen_hashtags"):
            if not ht_content.strip():
                st.error("Please enter post content or a topic.")
            else:
                with st.spinner("Building hashtag strategy…"):
                    try:
                        result = generate_text(
                            build_hashtag_prompt(ht_content, ht_industry or "General"),
                            temperature=0.7,
                            max_tokens=4000,
                        )
                        st.success("✅ Hashtag strategy ready!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with tab4:
        st.subheader("⏰ Optimal Posting Times")
        st.markdown("When you post matters almost as much as what you post. First-hour engagement is everything.")

        region = st.selectbox("🌍 Your Target Audience Region", list(POSTING_TIMES.keys()),
                               index=0)  # WAT is now first
        data   = POSTING_TIMES[region]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**✅ Best Days**")
            for day in data["best_days"]:
                st.markdown(f"• {day}")
        with col2:
            st.markdown("**⏰ Peak Times**")
            for t in data["peak_times"]:
                st.markdown(f"• {t}")
        with col3:
            st.markdown("**🚫 Avoid**")
            st.markdown(data["avoid"])

        if data.get("note"):
            st.info(f"💡 {data['note']}")

        st.markdown("---")
        st.markdown("""
**💡 Rules that actually move the needle:**
- **Golden hour**: Reply to every comment within 60 minutes of posting — this is LinkedIn's primary engagement signal
- **Pre-warm**: Comment meaningfully on 5–10 posts in the 30 min before you post
- **Consistency beats frequency**: 3× per week every week > 7× some weeks and 0× others
- **First comment**: Post your own comment right after publishing (a question or key takeaway) to seed engagement
- **Don't edit early**: Wait 3+ hours before making any edits — early edits can suppress distribution
- **🇳🇬 Nigerian note**: Most Nigerian LinkedIn users scroll between 7–9am WAT commuting and 8–10pm WAT at home — mobile-first hooks matter more than anywhere else
        """)
