"""
Creator Strategy Insights — Simulates top LinkedIn creator tactics,
hook formulas, post structures, and engagement frameworks.
"""
import streamlit as st
from utils.gemini_client import generate_text


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
    "Unpopular Opinion: 'Hot take: [Contrarian belief that challenges status quo]'",
    "Curiosity Gap: '[Do/Don't] [common action] until you read this.'",
    "Before/After: 'X months ago, I [was struggling with Y]. Today [dramatic outcome].'",
    "Direct Address: 'If you're a [specific role] and you're doing [specific thing], stop.'",
    "Story Opening: '[Day/time]. I was [doing something]. Then [unexpected thing happened].'",
    "Bold Claim: '[Topic] changed how I think about [bigger concept]. Here's how:'",
    "List Tease: 'X things I wish someone told me about [topic] when I started:'",
]


def build_strategy_prompt(creator_type, niche, goal):
    archetype_desc = CREATOR_ARCHETYPES.get(creator_type, "")
    hooks_formatted = "\n".join([f"{i+1}. {h}" for i, h in enumerate(HOOK_FORMULAS)])
    return f"""You study what actually works on LinkedIn — not the theory, the real patterns. You've watched thousands of posts succeed and fail. You know the difference between a creator who posts and one who grows.

Build a strategy playbook for this creator:

- Archetype: {creator_type} — {archetype_desc}
- Niche: {niche}
- Goal: {goal}

Write this like you're a mentor who's seen it work, not a consultant filling a template.
No buzzwords. No padding. Every line should be something they can act on today.

NEVER use: "leverage", "synergy", "game-changer", "thought leader", "content machine",
"actionable insights", "crush it", "go viral", "algorithm hack"

---

## YOUR CREATOR DNA
What makes the {creator_type} archetype work — and specifically how it plays in {niche}.
The one thing this archetype must never do. The one thing they must always do.
3–4 paragraphs, specific to their niche.

## THE 5 HOOKS THAT WILL ACTUALLY WORK FOR YOU
Pick the 5 best hook formulas for a {creator_type} in {niche}.
For each:
- Template
- Real example written for {niche} (not a placeholder — an actual hook ready to use)
- The psychology behind why it stops scrolling

Reference these formulas as inspiration:
{hooks_formatted}

## 3 POST BLUEPRINTS
Three repeatable structures that consistently perform for this archetype.
For each blueprint:
- Name it something memorable
- Show the structure line by line (e.g., "Line 1: X. Lines 2-4: Y. Line 5: Z.")
- Write a real example for {niche}

## 10 ENGAGEMENT TACTICS
Not generic tips. Specific moves.
Each one: what to do + when to do it + what result to expect.

## POSTING RHYTHM
- Best days for {niche} audience (with a reason, not just the days)
- Best times (with timezone context)
- How many times per week — and why that number
- Content mix: what % of posts should be each type

## THE ALGORITHM IN PLAIN ENGLISH
What LinkedIn actually rewards for {creator_type} creators right now.
What most creators in {niche} get wrong about distribution.
How to use the first 60 minutes after posting.

## 90-DAY ROADMAP
Month 1 — Foundation: 3–4 specific things to do, not categories
Month 2 — Momentum: what should be different by now, 3–4 actions
Month 3 — Authority: what "made it" looks like, 3–4 actions

One metric to track per month.

## THE COMMENT STRATEGY
Most people ignore this. It's how creators actually grow.
Exactly how to use commenting to build faster than posting alone.

## REAL-WORLD CASE STUDY
Create a specific fictional creator in {niche} who is a {creator_type}.
Walk through their first 90 days: their first 5 post topics, the post that broke through, the turning point, where they were at day 90.
Make it feel real — specific numbers, specific moments.
"""


def render_strategy_insights():
    st.header("🧠 Creator Strategy Insights")
    st.markdown("A real playbook based on what actually works — not what sounds good in theory.")

    with st.expander("🎭 Learn About Creator Archetypes", expanded=False):
        for archetype, desc in CREATOR_ARCHETYPES.items():
            st.markdown(f"**{archetype}**: {desc}")

    col1, col2 = st.columns(2)

    with col1:
        creator_type = st.selectbox("🎭 Your Creator Archetype", list(CREATOR_ARCHETYPES.keys()),
                                     help="Choose the style that feels most like you")
        niche = st.text_input("🎯 Your Niche", placeholder="e.g., B2B SaaS, Career Coaching, Data Engineering")

    with col2:
        goal = st.selectbox("🎯 Primary Growth Goal", [
            "Grow to 5K followers in 90 days",
            "Establish myself as a thought leader",
            "Attract premium clients / consulting work",
            "Get recruited by top companies",
            "Build an audience for my product/course",
            "Become the go-to expert in my niche",
        ])
        st.info(f"**Your Archetype:** {CREATOR_ARCHETYPES[creator_type]}")

    st.markdown("---")

    with st.expander("🪝 Quick Reference: 9 Proven Hook Formulas", expanded=False):
        for formula in HOOK_FORMULAS:
            st.markdown(f"• {formula}")

    if st.button("🚀 Generate My Strategy Playbook", type="primary", use_container_width=True):
        if not niche.strip():
            st.error("Please enter your niche.")
            return

        with st.spinner("Building your playbook..."):
            try:
                prompt = build_strategy_prompt(creator_type, niche, goal)
                result = generate_text(prompt, temperature=0.8, max_tokens=3000)

                st.success("✅ Strategy playbook generated!")
                st.markdown("---")

                st.download_button(
                    label="📥 Download Strategy Playbook",
                    data=result,
                    file_name=f"linkedin_strategy_{creator_type.replace(' ','_').lower()}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

                st.markdown(result)

            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
