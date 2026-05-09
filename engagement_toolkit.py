"""
Engagement Toolkit — Hook generator, CTA generator, hashtag optimizer,
and posting time analyzer all in one.
"""
import streamlit as st
from utils.gemini_client import generate_text, get_profile_context


POSTING_TIMES = {
    "North America (EST/PST)": {
        "best_days":  ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["7:00–9:00 AM EST", "12:00–1:00 PM EST", "5:00–6:00 PM EST"],
        "avoid":      "Friday afternoon, Saturday, Sunday morning",
    },
    "Europe (GMT/CET)": {
        "best_days":  ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["7:00–9:00 AM CET", "12:00–2:00 PM CET", "6:00–8:00 PM CET"],
        "avoid":      "Monday morning, Friday evening, weekends",
    },
    "Asia Pacific (SGT/AEST)": {
        "best_days":  ["Tuesday", "Wednesday", "Thursday"],
        "peak_times": ["8:00–10:00 AM SGT", "12:00–1:00 PM SGT", "7:00–9:00 PM SGT"],
        "avoid":      "Monday morning, Friday afternoon",
    },
    "Middle East & Africa": {
        "best_days":  ["Sunday", "Monday", "Tuesday"],
        "peak_times": ["8:00–10:00 AM GST", "1:00–3:00 PM GST"],
        "avoid":      "Friday prayer times, weekends in GCC",
    },
    "Global / Mixed Audience": {
        "best_days":  ["Tuesday", "Wednesday"],
        "peak_times": ["9:00 AM UTC", "1:00 PM UTC"],
        "avoid":      "Weekends and major holidays",
    },
}

_BANNED = """
NEVER use: "game-changer", "dive in", "leverage", "synergy", "I'm excited",
"thought leader", "passionate", "journey", "hustle", "crush it", "in today's world"
"""


def build_hooks_prompt(topic, tone, count):
    profile_ctx = get_profile_context()
    return f"""You write LinkedIn hooks the way a great headline writer works — every word earns its place, and the reader has no choice but to keep reading.{profile_ctx}

Write {count} hooks for this topic: {topic}
Tone: {tone}

{_BANNED}

Rules:
- Never open with "I" as the first word
- No hooks that are questions — statements outperform questions every time
- Max 12 words per hook ideally, never more than 15
- Each hook must use a different psychological trigger
- No emojis in the hook

Triggers to use across the {count} hooks (mix them):
curiosity gap, specific number, confession, bold claim, direct address, before/after, contrast, shock stat, story opening

For each hook, on a new line add:
🧠 Trigger: [name] | Why it works: [one sentence]

Number them 1 through {count}.
"""


def build_cta_prompt(post_context, cta_goal):
    profile_ctx = get_profile_context()
    return f"""You write CTAs for LinkedIn posts that feel like a natural end to the conversation — not a sales pitch, not a desperate ask.{profile_ctx}

Post context: {post_context}
Goal: {cta_goal}

{_BANNED}

Write 8 CTAs across 4 categories:

**QUESTION CTAs** (invite real responses — not fake curiosity):
1. [CTA]
2. [CTA]

**ACTION CTAs** (get them to do something specific):
3. [CTA]
4. [CTA]

**SHARE CTAs** (give them a reason to repost — not "please share"):
5. [CTA]
6. [CTA]

**SOFT CTAs** (low commitment, high warmth):
7. [CTA]
8. [CTA]

After each: 🎯 Use when: [one-line context]

Rules:
- No "drop a comment below" — it's 2024, they know how comments work
- No "hit the like button" or "smash that follow"
- Every CTA should feel like something a real person would actually say
"""


def build_hashtag_prompt(post_content, industry):
    profile_ctx = get_profile_context()
    return f"""You know how LinkedIn hashtags actually work — not in theory, in practice. Most people either use 30 generic ones or none at all. You find the specific combination that puts a post in front of the right people.{profile_ctx}

Post: {post_content}
Industry: {industry}

Give me a 3-tier hashtag strategy:

## TIER 1 — BROAD (1M+ followers)
3 tags. These reach the most people but competition is high.
[hashtag] — [estimated followers] — [why include despite high competition]

## TIER 2 — MID-RANGE (100K–1M)
3 tags. The sweet spot for most posts.
[hashtag] — [estimated followers] — [why this specific tag for this post]

## TIER 3 — NICHE (10K–100K)
3 tags. Smaller reach but highly targeted — often drives better engagement rate.
[hashtag] — [estimated followers] — [the specific audience this reaches]

## USE THESE (in this order):
#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8

## 2 THINGS MOST PEOPLE GET WRONG
[Specific to this post and industry — not generic hashtag advice]
"""


def render_engagement_toolkit():
    st.header("⚡ Engagement Toolkit")
    st.markdown("Hooks, CTAs, hashtags, and timing — everything you need to maximise reach on every post.")

    tab1, tab2, tab3, tab4 = st.tabs(["🪝 Hook Generator", "📢 CTA Generator", "#️⃣ Hashtag Optimizer", "⏰ Posting Times"])

    with tab1:
        st.subheader("🪝 Viral Hook Generator")
        st.markdown("The hook is 90% of your reach. Get {count} options across different psychological triggers.")

        col1, col2 = st.columns(2)
        with col1:
            hook_topic = st.text_area("📌 Topic / Post Idea",
                                       placeholder="e.g., I spent $50K on a startup that failed in 6 months",
                                       height=80, key="hook_topic")
        with col2:
            hook_tone  = st.selectbox("🎭 Tone",
                                       ["Storytelling", "Shocking", "Inspirational", "Contrarian", "Educational", "Vulnerability"],
                                       key="hook_tone")
            hook_count = st.slider("Number of Hooks", 5, 15, 8, key="hook_count")

        if st.button("⚡ Generate Hooks", type="primary", use_container_width=True, key="gen_hooks"):
            if not hook_topic.strip():
                st.error("Please enter a topic.")
            else:
                with st.spinner("Writing your hooks..."):
                    try:
                        result = generate_text(build_hooks_prompt(hook_topic, hook_tone, hook_count), temperature=0.92)
                        st.success("✅ Hooks generated!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with tab2:
        st.subheader("📢 CTA Generator")
        st.markdown("The CTA decides whether your post stays read or gets shared. Make it count.")

        col1, col2 = st.columns(2)
        with col1:
            cta_context = st.text_area("📝 Post Topic/Context",
                                        placeholder="e.g., A post about 5 lessons from 10 years in software engineering",
                                        height=80, key="cta_context")
        with col2:
            cta_goal    = st.selectbox("🎯 CTA Goal",
                                        ["Drive Comments", "Drive Shares/Reposts", "Generate DMs/Leads",
                                         "Build Community", "Get Profile Views"],
                                        key="cta_goal")

        if st.button("⚡ Generate CTAs", type="primary", use_container_width=True, key="gen_ctas"):
            if not cta_context.strip():
                st.error("Please enter your post context.")
            else:
                with st.spinner("Writing CTAs..."):
                    try:
                        result = generate_text(build_cta_prompt(cta_context, cta_goal), temperature=0.82)
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
                                        placeholder="Paste your post or describe your topic...",
                                        height=100, key="ht_content")
        with col2:
            ht_industry = st.text_input("🏢 Industry", placeholder="e.g., SaaS, Healthcare, Finance",
                                         key="ht_industry")

        if st.button("🔍 Optimize Hashtags", type="primary", use_container_width=True, key="gen_hashtags"):
            if not ht_content.strip():
                st.error("Please enter post content or a topic.")
            else:
                with st.spinner("Building hashtag strategy..."):
                    try:
                        result = generate_text(build_hashtag_prompt(ht_content, ht_industry or "General"), temperature=0.7)
                        st.success("✅ Hashtag strategy ready!")
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

    with tab4:
        st.subheader("⏰ Optimal Posting Times")
        st.markdown("When you post matters almost as much as what you post. First-hour engagement is everything.")

        region = st.selectbox("🌍 Your Target Audience Region", list(POSTING_TIMES.keys()))
        data   = POSTING_TIMES[region]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**✅ Best Days**")
            for day in data["best_days"]:
                st.markdown(f"• {day}")
        with col2:
            st.markdown("**⏰ Peak Times**")
            for time in data["peak_times"]:
                st.markdown(f"• {time}")
        with col3:
            st.markdown("**🚫 Avoid**")
            st.markdown(data["avoid"])

        st.markdown("---")
        st.markdown("""
**💡 The rules that actually move the needle:**
- **Golden hour**: Reply to every comment within 60 minutes of posting — this is LinkedIn's engagement signal
- **Pre-warm**: Comment meaningfully on 5–10 posts in the 30 min before you post
- **Consistency beats frequency**: 3× per week every week > 7× some weeks and 0× others
- **First comment**: Post your own comment right after publishing (a question or key takeaway) to seed engagement
- **Don't edit early**: Wait 3+ hours before making any edits — early edits can reset distribution
        """)
