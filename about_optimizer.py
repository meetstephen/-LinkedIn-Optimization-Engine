"""
About Section Optimizer — Transforms LinkedIn About sections into
powerful personal brand stories with keyword optimization.
"""
import streamlit as st
from utils.gemini_client import generate_text


INDUSTRY_KEYWORDS = {
    "Technology": "software, engineering, AI, machine learning, cloud, agile, innovation, scalable",
    "Marketing": "growth, demand generation, brand, GTM, campaigns, ROI, digital, SEO, conversion",
    "Finance": "financial analysis, portfolio, risk, investment, forecasting, revenue, compliance",
    "Healthcare": "patient care, clinical, healthcare systems, evidence-based, outcomes, research",
    "Consulting": "strategy, transformation, stakeholder, client success, frameworks, implementation",
    "Sales": "pipeline, quota, enterprise, SaaS, CRM, hunter, relationships, ARR, closing",
    "HR & People Ops": "talent, culture, DEI, performance, employee experience, org design, HRIS",
    "Entrepreneurship": "founder, startup, scaling, product-market fit, fundraising, vision, growth",
    "Education": "curriculum, pedagogy, student outcomes, EdTech, facilitation, mentorship",
    "Creative": "design, UX, branding, storytelling, visual, creative direction, content strategy",
    "Other": "professional, expertise, results-driven, strategic, collaborative, impact",
}


def build_about_prompt(current_about: str, name: str, role: str, industry: str,
                        superpowers: str, achievements: str, goal: str) -> str:
    keywords = INDUSTRY_KEYWORDS.get(industry, INDUSTRY_KEYWORDS["Other"])
    return f"""You are a world-class LinkedIn personal brand strategist and copywriter.

TASK: Transform this LinkedIn "About" section into a compelling personal brand story.

PERSON'S INFO:
- Name: {name}
- Current Role: {role}
- Industry: {industry}
- Key Strengths/Superpowers: {superpowers}
- Top Achievements: {achievements}
- Career Goal/What They Want: {goal}
- Industry Keywords to Weave In: {keywords}

CURRENT ABOUT SECTION:
\"\"\"
{current_about if current_about.strip() else "No About section written yet — create one from scratch."}
\"\"\"

DELIVER:

## 📊 BEFORE ANALYSIS
If there's an existing About section, diagnose its weaknesses (3–5 issues).
If it's blank, note that you'll build from scratch.

## ✨ OPTIMIZED ABOUT SECTION
Write a 3-paragraph (250–300 word) About section that:
1. Opens with a POWERFUL hook (not "I am a..." — instead, start with a result, belief, or bold statement)
2. Tells a compelling career narrative with personality
3. Demonstrates clear VALUE PROPOSITION ("I help [who] achieve [what] through [how]")
4. Weaves in 5–7 relevant keywords naturally (for LinkedIn search)
5. Ends with a specific CTA (what should viewers do next?)
6. Uses "I" language — personal, not corporate
7. Shows personality, not just accomplishments

## 🔑 KEY IMPROVEMENTS MADE
List 5 specific improvements with the reason each one increases profile effectiveness.

## 🎯 VALUE PROPOSITION
Write their core value proposition in 1 sentence:
"I help [target audience] [achieve specific outcome] by [your unique approach]"

## 🔍 KEYWORDS EMBEDDED
List the keywords you wove in and WHY each matters for LinkedIn search.

## 📣 HEADLINE BONUS
Suggest 3 optimized LinkedIn headlines that complement this About section.
"""


def render_about_optimizer():
    """Renders the About Section Optimizer UI."""
    st.header("💼 LinkedIn 'About' Section Optimizer")
    st.markdown("Transform your About section into a powerful personal brand story that attracts opportunities.")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("👤 Your Name", placeholder="e.g., Sarah Johnson")
        role = st.text_input("💼 Current Role/Title", placeholder="e.g., Senior Product Manager at Fintech Co.")
        industry = st.selectbox("🏢 Industry", list(INDUSTRY_KEYWORDS.keys()))
        goal = st.text_input(
            "🎯 What Do You Want to Achieve?",
            placeholder="e.g., Land a VP role, attract clients, build my personal brand",
        )

    with col2:
        superpowers = st.text_area(
            "⚡ Your Top 3–5 Strengths / Superpowers",
            placeholder="e.g., Turning complex data into clear decisions, building high-performing teams, scaling B2B SaaS from 0 to $10M ARR",
            height=100,
        )
        achievements = st.text_area(
            "🏆 Your Best Achievements (with numbers if possible)",
            placeholder="e.g., Grew team from 5 to 40 engineers, launched product used by 2M+ users, reduced churn by 35%",
            height=100,
        )

    current_about = st.text_area(
        "📝 Current About Section (leave blank to create from scratch)",
        placeholder="Paste your current LinkedIn About section here...",
        height=120,
    )

    st.markdown("---")

    if st.button("✨ Optimize My About Section", type="primary", use_container_width=True):
        if not name.strip() or not role.strip():
            st.error("Please fill in at least your name and current role.")
            return
        if not superpowers.strip():
            st.error("Please share your key strengths so we can highlight them.")
            return

        with st.spinner("Crafting your personal brand story..."):
            try:
                prompt = build_about_prompt(
                    current_about, name, role, industry,
                    superpowers, achievements, goal
                )
                result = generate_text(prompt, temperature=0.75)

                st.success("✅ About section optimized!")
                st.markdown("---")

                # Before/After if original exists
                if current_about.strip():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📋 Before")
                        st.markdown(
                            f'<div style="background:#fff3f3;padding:1rem;border-radius:8px;'
                            f'border-left:4px solid #ff6b6b;font-size:0.9rem;">'
                            f'{current_about.replace(chr(10), "<br>")}</div>',
                            unsafe_allow_html=True,
                        )
                    with col2:
                        st.subheader("✨ After (Preview)")
                        # Extract just the optimized section for preview
                        lines = result.split("\n")
                        in_section = False
                        preview_lines = []
                        for line in lines:
                            if "OPTIMIZED ABOUT SECTION" in line:
                                in_section = True
                                continue
                            if in_section and line.startswith("##"):
                                break
                            if in_section:
                                preview_lines.append(line)
                        preview = "\n".join(preview_lines).strip()
                        st.markdown(
                            f'<div style="background:#f0fff4;padding:1rem;border-radius:8px;'
                            f'border-left:4px solid #00c851;font-size:0.9rem;">'
                            f'{preview.replace(chr(10), "<br>") if preview else "See full results below"}</div>',
                            unsafe_allow_html=True,
                        )

                st.markdown("---")
                st.markdown(result)

            except Exception as e:
                st.error(f"Optimization failed: {str(e)}")
