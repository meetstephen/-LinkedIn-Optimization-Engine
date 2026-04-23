"""
Creator Strategy Insights — Simulates top LinkedIn creator tactics,
hook formulas, post structures, and engagement frameworks.
"""
import streamlit as st
from utils.gemini_client import generate_text


CREATOR_ARCHETYPES = {
    "The Educator": "Breaks down complex topics into digestible frameworks. Known for carousels, step-by-step guides, and 'what they don't teach you' posts.",
    "The Storyteller": "Masters vulnerability and personal narrative. Uses emotional arcs, cliffhangers in hooks, and relatable human moments.",
    "The Contrarian Thinker": "Challenges conventional wisdom. Posts controversial takes, defends with data, sparks massive comment threads.",
    "The Results Poster": "Shows before/after, shares numbers, proof-of-concept posts. Attracts clients and employers with demonstrated outcomes.",
    "The Community Builder": "Engages others, reposts with commentary, Q&A threads, collaborative posts. Wins through relationship capital.",
    "The Niche Expert": "Hyper-specific advice for a defined audience. Known as THE go-to person for one topic.",
    "The Document Builder": "Builds in public — shares the journey, the failures, the weekly updates. Audiences become invested in their story.",
}

HOOK_FORMULAS = [
    "Shock Statistic: '[Surprising number] of [audience] don't know [key insight]'",
    "Confession: 'I was [wrong/embarrassed/scared] about [topic]. Here's what I discovered.'",
    "Unpopular Opinion: 'Hot take: [Contrarian belief that challenges status quo]'",
    "Curiosity Gap: '[Do/Don't] [common action] until you read this.'",
    "Before/After: 'X months ago, I [was struggling with Y]. Today [dramatic outcome].'",
    "Direct Address: 'If you're a [specific role] and you're doing [specific thing], stop.'",
    "Question: 'Why do [impressive people] all seem to [do surprising thing]?'",
    "Story Opening: '[Day/time]. I was [doing something]. Then [unexpected thing happened].'",
    "Bold Claim: '[Topic] changed how I think about [bigger concept]. Here's how:'",
    "List Tease: 'X things I wish someone told me about [topic] when I started:'",
]


def build_strategy_prompt(creator_type: str, niche: str, goal: str) -> str:
    archetype_desc = CREATOR_ARCHETYPES.get(creator_type, "")
    hooks_formatted = "\n".join([f"{i+1}. {h}" for i, h in enumerate(HOOK_FORMULAS)])
    return f"""You are a LinkedIn growth strategist who has studied the top 1% of LinkedIn creators and reverse-engineered their exact playbooks.

TASK: Create a complete LinkedIn Creator Strategy Playbook for this creator.

CREATOR PROFILE:
- Creator Archetype: {creator_type} — {archetype_desc}
- Niche/Industry: {niche}
- Primary Goal: {goal}

DELIVER A COMPLETE STRATEGY PLAYBOOK:

## 🧬 YOUR CREATOR DNA
Based on the {creator_type} archetype, here's how to manifest this on LinkedIn:
[Deep explanation with specific tactics, examples, and why this archetype wins in {niche}]

## 🪝 HOOK FORMULA MASTERCLASS
The 5 best hook formulas for {creator_type} in {niche}:

For each formula, provide:
- Formula name
- Template
- Example for {niche}
- Why it works psychologically
- When to use it

Reference these proven hooks for inspiration:
{hooks_formatted}

## 📐 POST ARCHITECTURE BLUEPRINTS
3 proven post structures for maximum {niche} engagement:

Blueprint 1: [Name]
- Line 1: [what to write]
- Lines 2–5: [what to write]
[etc. — full blueprint with instructions]

Blueprint 2: [Name] [full blueprint]
Blueprint 3: [Name] [full blueprint]

## 🔥 ENGAGEMENT MULTIPLICATION TACTICS
10 specific tactics to 10x comments and shares:
1. [Tactic + exact implementation]
[...]

## ⏰ OPTIMAL POSTING STRATEGY
- Best days for {niche} audience: [specific days with reasoning]
- Best times: [specific times with timezone context]
- Posting frequency: [specific recommendation]
- Content mix ratio: [X% stories, Y% education, Z% engagement posts]

## 🌱 ALGORITHM GROWTH FORMULA
How to hack LinkedIn's algorithm for {creator_type} creators:
[Specific, tactical instructions covering: early engagement window, comment strategy, network seeding, content repurposing]

## 📈 90-DAY GROWTH ROADMAP
Month 1 — Foundation: [key actions]
Month 2 — Momentum: [key actions]  
Month 3 — Authority: [key actions]

Milestone checkpoints and what metrics to track at each stage.

## 💬 COMMENT STRATEGY (Hidden Growth Lever)
[Complete playbook on using comments to grow faster than posting — the underrated secret of top creators]

## 🏆 CREATOR CASE STUDY
Simulate a success story: Describe how a fictional {creator_type} creator in {niche} went from 0 to 10K followers in 90 days using these exact tactics. Include their content strategy, breakthrough post type, and turning point moment.
"""


def render_strategy_insights():
    """Renders the Creator Strategy Insights tab UI."""
    st.header("🧠 Creator Strategy Insights")
    st.markdown("Reverse-engineered playbooks from top LinkedIn creators — personalized to your archetype and niche.")

    # Creator archetype display
    with st.expander("🎭 Learn About Creator Archetypes", expanded=False):
        for archetype, desc in CREATOR_ARCHETYPES.items():
            st.markdown(f"**{archetype}**: {desc}")

    col1, col2 = st.columns(2)

    with col1:
        creator_type = st.selectbox(
            "🎭 Your Creator Archetype",
            list(CREATOR_ARCHETYPES.keys()),
            help="Choose the style that resonates most with you",
        )
        niche = st.text_input(
            "🎯 Your Niche",
            placeholder="e.g., B2B SaaS, Career Coaching, Data Engineering",
        )

    with col2:
        goal = st.selectbox(
            "🎯 Primary Growth Goal",
            [
                "Grow to 5K followers in 90 days",
                "Establish myself as a thought leader",
                "Attract premium clients / consulting work",
                "Get recruited by top companies",
                "Build an audience for my product/course",
                "Become the go-to expert in my niche",
            ],
        )
        st.info(f"**Your Archetype:** {CREATOR_ARCHETYPES[creator_type]}")

    st.markdown("---")

    # Quick reference: Hook formulas
    with st.expander("🪝 Quick Reference: 10 Proven Hook Formulas", expanded=False):
        for formula in HOOK_FORMULAS:
            st.markdown(f"• {formula}")

    if st.button("🚀 Generate My Strategy Playbook", type="primary", use_container_width=True):
        if not niche.strip():
            st.error("Please enter your niche.")
            return

        with st.spinner("Building your personalized creator playbook..."):
            try:
                prompt = build_strategy_prompt(creator_type, niche, goal)
                result = generate_text(prompt, temperature=0.8, max_tokens=3000)

                st.success("✅ Strategy playbook generated!")
                st.markdown("---")

                # Download option
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
