"""
Post Optimizer Module — Rewrites and scores existing LinkedIn posts
for maximum engagement and virality potential.
"""
import streamlit as st
from utils.gemini_client import generate_text


OPTIMIZATION_GOALS = {
    "Maximum Engagement": "optimize for likes, comments, and shares — prioritize emotional resonance",
    "Professional Authority": "position as thought leader — credibility and expertise signaling",
    "Lead Generation": "attract potential clients/employers — clear value demonstration",
    "Community Building": "spark conversations — questions, relatable content",
    "Personal Branding": "build distinctive voice — authentic, memorable, consistent",
}


def build_optimizer_prompt(original_post: str, goal: str) -> str:
    goal_desc = OPTIMIZATION_GOALS.get(goal, goal)
    return f"""You are a LinkedIn content strategist who has helped 100+ creators grow from 1K to 100K+ followers.

TASK: Analyze and completely optimize the following LinkedIn post.

ORIGINAL POST:
\"\"\"
{original_post}
\"\"\"

OPTIMIZATION GOAL: {goal} — {goal_desc}

DELIVER THE FOLLOWING:

## 🔍 DIAGNOSTIC ANALYSIS
Rate each element (1–10) with a brief reason:
- Hook Strength: X/10 — [reason]
- Clarity: X/10 — [reason]  
- Emotional Impact: X/10 — [reason]
- Formatting: X/10 — [reason]
- CTA Effectiveness: X/10 — [reason]
- Hashtag Quality: X/10 — [reason]

**OVERALL ENGAGEMENT SCORE: XX/100**

## ⚠️ KEY ISSUES FOUND
List 3–5 specific problems with the original post (be direct and specific).

## ✅ OPTIMIZED VERSION
Rewrite the complete post with:
- Stronger hook (scroll-stopping first line)
- Better formatting (short lines, white space)
- Clearer message and storytelling
- Stronger CTA
- Better hashtags
(Keep the author's voice but dramatically improve execution)

## 📈 IMPROVEMENTS MADE
List exactly what you changed and why each change increases engagement.

## 💡 PRO TIPS
2–3 additional power moves the author can use going forward.
"""


def render_post_optimizer():
    """Renders the Post Optimizer tab UI."""
    st.header("🔧 LinkedIn Post Optimizer")
    st.markdown("Paste your existing post and get a full diagnosis + professional rewrite with engagement score.")

    original_post = st.text_area(
        "📝 Paste Your LinkedIn Post Here",
        placeholder="Paste your existing LinkedIn post here...\n\nExcited to announce that I just completed a certification in...",
        height=200,
    )

    col1, col2 = st.columns(2)
    with col1:
        goal = st.selectbox("🎯 Optimization Goal", list(OPTIMIZATION_GOALS.keys()))
    with col2:
        st.info(f"**Goal:** {OPTIMIZATION_GOALS[goal]}")

    st.markdown("---")

    if st.button("🚀 Optimize My Post", type="primary", use_container_width=True):
        if not original_post.strip():
            st.error("Please paste a post to optimize.")
            return
        if len(original_post.strip()) < 20:
            st.warning("Post seems too short. Add more content for better optimization.")
            return

        with st.spinner("Analyzing and rewriting your post..."):
            try:
                prompt = build_optimizer_prompt(original_post, goal)
                result = generate_text(prompt, temperature=0.7)

                st.success("✅ Optimization complete!")
                st.markdown("---")

                # Side by side comparison
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("❌ Original Post")
                    st.markdown(
                        f'<div style="background:#fff3f3;padding:1rem;border-radius:8px;border-left:4px solid #ff4444;">'
                        f'{original_post.replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True,
                    )

                with col2:
                    st.subheader("✅ After AI Analysis")
                    # Extract score for highlight
                    score_line = ""
                    for line in result.split("\n"):
                        if "OVERALL ENGAGEMENT SCORE" in line.upper():
                            score_line = line
                            break
                    if score_line:
                        st.metric("Engagement Score", score_line.split(":")[-1].strip() if ":" in score_line else "—")

                st.markdown("---")
                st.markdown(result)

                # Save optimized post
                st.session_state["last_generated_post"] = result

            except Exception as e:
                st.error(f"Optimization failed: {str(e)}")
