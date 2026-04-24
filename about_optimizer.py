"""
About Section Optimizer — Transforms LinkedIn About sections into
powerful personal brand stories with keyword optimization.
"""
import streamlit as st
from utils.gemini_client import generate_text


INDUSTRY_KEYWORDS = {
    "Technology":       "software, engineering, AI, machine learning, cloud, agile, innovation, scalable",
    "Marketing":        "growth, demand generation, brand, GTM, campaigns, ROI, digital, SEO, conversion",
    "Finance":          "financial analysis, portfolio, risk, investment, forecasting, revenue, compliance",
    "Healthcare":       "patient care, clinical, healthcare systems, evidence-based, outcomes, research",
    "Consulting":       "strategy, transformation, stakeholder, client success, frameworks, implementation",
    "Sales":            "pipeline, quota, enterprise, SaaS, CRM, hunter, relationships, ARR, closing",
    "HR & People Ops":  "talent, culture, DEI, performance, employee experience, org design, HRIS",
    "Entrepreneurship": "founder, startup, scaling, product-market fit, fundraising, vision, growth",
    "Education":        "curriculum, pedagogy, student outcomes, EdTech, facilitation, mentorship",
    "Creative":         "design, UX, branding, storytelling, visual, creative direction, content strategy",
    "Other":            "professional, expertise, results-driven, strategic, collaborative, impact",
}


def build_about_prompt(current_about, name, role, industry, superpowers, achievements, goal):
    keywords = INDUSTRY_KEYWORDS.get(industry, INDUSTRY_KEYWORDS["Other"])
    return f"""You write LinkedIn About sections that read like a person wrote them at midnight after a long honest conversation — not like a resume, not like a brand deck.

PERSON:
- Name: {name}
- Role: {role}
- Industry: {industry}
- Strengths: {superpowers}
- Achievements: {achievements}
- Goal: {goal}
- Keywords to weave in naturally: {keywords}

CURRENT ABOUT:
\"\"\"
{current_about if current_about.strip() else "Nothing written yet — build from scratch."}
\"\"\"

NEVER write:
"passionate about", "I am a dedicated", "results-driven professional", "leverage",
"thought leader", "I'm excited to", "game-changer", "journey", "synergy",
"I thrive in", "I am committed to", "dynamic", "I help people reach their potential",
"fast-paced environment", "innovative solutions"

DELIVER:

## BEFORE — WHAT'S WRONG
If they have an existing About, name 3–4 specific problems with it. Be honest.
If it's blank, skip this section.

## REWRITTEN ABOUT SECTION
Write a 3-paragraph About section (220–280 words) that:

Para 1 — The Hook:
Opens with a bold statement, specific result, or unusual truth about them.
NOT "I am a [job title]". NOT a question.
Something that makes the right reader think "this person gets it."

Para 2 — The Story:
What they've actually done. Real numbers. Real names if possible.
The tension they've sat in. The thing they figured out that others haven't.
Ends with their clear value: "I help [who] do [specific thing] by [specific how]."

Para 3 — The CTA:
What should happen next? A genuine invitation, not a sales pitch.
One line, maybe two.

Style rules:
- "I" is fine — use it
- Short sentences mix with longer ones for rhythm
- Specific over general always (not "many years" — say how many)
- One moment of honesty or vulnerability

## KEY IMPROVEMENTS
5 specific things you changed and exactly why each one performs better.

## VALUE PROPOSITION (one line)
"I help [specific who] [achieve specific what] by [specific how]"

## KEYWORDS EMBEDDED
List which keywords you used and where — one line each.

## 3 HEADLINE OPTIONS
One authority-focused, one value-focused, one outcome-focused.
Each under 200 characters.
"""


def render_about_optimizer():
    st.header("💼 LinkedIn 'About' Section Optimizer")
    st.markdown("Transform your About section into a personal brand story that attracts the right opportunities.")

    col1, col2 = st.columns(2)

    with col1:
        name      = st.text_input("👤 Your Name", placeholder="e.g., Sarah Johnson")
        role      = st.text_input("💼 Current Role/Title", placeholder="e.g., Senior Product Manager at Fintech Co.")
        industry  = st.selectbox("🏢 Industry", list(INDUSTRY_KEYWORDS.keys()))
        goal      = st.text_input("🎯 What Do You Want to Achieve?",
                                   placeholder="e.g., Land a VP role, attract clients, build my personal brand")

    with col2:
        superpowers  = st.text_area("⚡ Your Top 3–5 Strengths",
                                     placeholder="e.g., Turning complex data into clear decisions, building high-performing teams, scaling B2B SaaS from 0 to $10M ARR",
                                     height=100)
        achievements = st.text_area("🏆 Your Best Achievements (with numbers)",
                                     placeholder="e.g., Grew team from 5 to 40 engineers, launched product used by 2M+ users, reduced churn by 35%",
                                     height=100)

    current_about = st.text_area("📝 Current About Section (leave blank to create from scratch)",
                                  placeholder="Paste your current LinkedIn About section here...",
                                  height=120)

    st.markdown("---")

    if st.button("✨ Optimize My About Section", type="primary", use_container_width=True):
        if not name.strip() or not role.strip():
            st.error("Please fill in at least your name and current role.")
            return
        if not superpowers.strip():
            st.error("Please share your key strengths so we can highlight them.")
            return

        with st.spinner("Writing your About section..."):
            try:
                prompt = build_about_prompt(current_about, name, role, industry,
                                            superpowers, achievements, goal)
                result = generate_text(prompt, temperature=0.78)

                st.success("✅ About section optimized!")
                st.markdown("---")

                if current_about.strip():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📋 Before")
                        st.markdown(
                            f'<div style="background:#fff3f3;padding:1rem;border-radius:8px;'
                            f'border-left:4px solid #ff6b6b;font-size:0.9rem;">'
                            f'{current_about.replace(chr(10), "<br>")}</div>',
                            unsafe_allow_html=True)
                    with col2:
                        st.subheader("✨ After (Preview)")
                        lines = result.split("\n")
                        in_section, preview_lines = False, []
                        for line in lines:
                            if "REWRITTEN ABOUT" in line:
                                in_section = True; continue
                            if in_section and line.startswith("##"):
                                break
                            if in_section:
                                preview_lines.append(line)
                        preview = "\n".join(preview_lines).strip()
                        st.markdown(
                            f'<div style="background:#f0fff4;padding:1rem;border-radius:8px;'
                            f'border-left:4px solid #00c851;font-size:0.9rem;">'
                            f'{preview.replace(chr(10), "<br>") if preview else "See full results below"}</div>',
                            unsafe_allow_html=True)

                st.markdown("---")
                st.markdown(result)

            except Exception as e:
                st.error(f"Optimization failed: {str(e)}")
