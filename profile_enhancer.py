"""
Profile Enhancer Module — Transforms beginner LinkedIn profiles into
PRO-level profiles with a comprehensive score and action plan.
"""
import streamlit as st
from utils.gemini_client import generate_text


def build_profile_prompt(profile_data: dict) -> str:
    return f"""You are a LinkedIn profile optimization expert who has reviewed 10,000+ profiles and helped professionals land roles at FAANG, Big 4, and top startups.

TASK: Review this LinkedIn profile and provide a complete Beginner → PRO transformation plan.

PROFILE DATA PROVIDED:
- Name: {profile_data['name']}
- Current Headline: {profile_data['headline']}
- Industry: {profile_data['industry']}
- Years of Experience: {profile_data['experience_years']}
- Current About: {profile_data['about'] or 'Not written'}
- Profile Photo: {profile_data['has_photo']}
- Banner Image: {profile_data['has_banner']}
- Number of Connections: {profile_data['connections']}
- Featured Section: {profile_data['has_featured']}
- Skills Listed: {profile_data['skills']}
- Recommendations: {profile_data['recommendations']}
- Goal: {profile_data['goal']}
- Top Achievements: {profile_data['achievements']}

DELIVER THE FOLLOWING COMPLETE ASSESSMENT:

## 🎯 PROFILE SCORE: XX/100

Break down the score by section:
| Section | Score | Max | Status |
|---------|-------|-----|--------|
| Headline | X | 15 | [🔴 Needs Work / 🟡 OK / 🟢 Strong] |
| About Section | X | 20 | [...] |
| Profile Photo | X | 10 | [...] |
| Banner Image | X | 10 | [...] |
| Experience Section | X | 20 | [...] |
| Skills & Endorsements | X | 10 | [...] |
| Recommendations | X | 10 | [...] |
| Engagement & Activity | X | 5 | [...] |

**TOTAL: XX/100 — [Beginner / Intermediate / Advanced / PRO]**

## 💡 HEADLINE TRANSFORMATION
Current: "{profile_data['headline']}"

❌ What's wrong with it:
[Specific issues]

✅ 3 Optimized Headline Options:
1. [Option 1 — Authority-focused]
2. [Option 2 — Value-focused]
3. [Option 3 — Result-focused]

**Formula used:** [Role] + [Who You Help] + [Key Result/Differentiator]

## 📸 PROFILE PHOTO STRATEGY
Current status: {profile_data['has_photo']}
[Specific tips: lighting, background, expression, framing, attire for their industry]

## 🖼️ BANNER IMAGE BLUEPRINT  
Current status: {profile_data['has_banner']}
[Exact specifications: size, what to include, tools to use (Canva, etc.), color psychology]

## 💼 EXPERIENCE SECTION REWRITE FORMULA
Transform job descriptions from:
❌ Responsibility-based: "Responsible for managing a team..."
✅ Achievement-based: "Led a team of X → delivered Y → resulting in Z% improvement"

Provide 2–3 example rewrites relevant to their industry.

## 🧠 SKILLS STRATEGY
Current skills: {profile_data['skills']}

[Recommend top 10 skills for their role/industry, explain which get most search traffic, endorsement strategy]

## ⭐ RECOMMENDATIONS PLAYBOOK
Current count: {profile_data['recommendations']}
[Step-by-step strategy to get 5+ quality recommendations within 30 days]

## 📌 FEATURED SECTION IDEAS
[5 specific content pieces they should feature based on their industry and goal]

## 🗓️ 30-DAY TRANSFORMATION ROADMAP
Week 1 — Foundation (Days 1–7):
- Day 1: [specific action]
- Day 2: [specific action]
[etc.]

Week 2 — Content (Days 8–14): [actions]
Week 3 — Network (Days 15–21): [actions]
Week 4 — Authority (Days 22–30): [actions]

## 🚀 TOP 3 QUICK WINS (Do These TODAY)
1. [Action] — Expected impact: [outcome]
2. [Action] — Expected impact: [outcome]
3. [Action] — Expected impact: [outcome]
"""


def render_profile_enhancer():
    """Renders the Profile Enhancer tab UI."""
    st.header("🌟 Profile Enhancer: Beginner → PRO")
    st.markdown("Get your complete LinkedIn profile score and a personalized transformation roadmap.")

    # Profile data collection
    st.subheader("📋 Enter Your Profile Details")

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("👤 Full Name", placeholder="Your full name")
        headline = st.text_input(
            "📌 Current Headline",
            placeholder="e.g., Software Engineer at Company | Python | ML",
        )
        industry = st.text_input("🏢 Industry/Field", placeholder="e.g., SaaS, Finance, Marketing")
        experience_years = st.selectbox(
            "📅 Years of Experience",
            ["0–1 year (Student/New Grad)", "1–3 years", "3–7 years", "7–15 years", "15+ years"],
        )
        connections = st.selectbox(
            "🔗 LinkedIn Connections",
            ["< 100", "100–500", "500–1000", "1000–5000", "5000+"],
        )
        goal = st.text_input(
            "🎯 Primary Goal",
            placeholder="e.g., Get hired at FAANG, grow my consulting business, become a speaker",
        )

    with col2:
        achievements = st.text_area(
            "🏆 Top 3 Career Achievements",
            placeholder="e.g., Built product with 500K users, Increased sales by 40%, Led team of 15 engineers",
            height=80,
        )
        skills = st.text_area(
            "🛠️ Current Skills Listed",
            placeholder="e.g., Python, Project Management, Machine Learning, Leadership",
            height=80,
        )
        about_preview = st.text_area(
            "📝 Current About Section (first 200 chars is fine)",
            placeholder="Paste beginning of your About section...",
            height=80,
        )

        col_a, col_b = st.columns(2)
        with col_a:
            has_photo = st.checkbox("✅ Has Profile Photo", value=True)
            has_banner = st.checkbox("✅ Has Banner/Cover Image", value=False)
            has_featured = st.checkbox("✅ Has Featured Section", value=False)
        with col_b:
            recommendations = st.number_input("⭐ # of Recommendations", min_value=0, max_value=50, value=0)

    st.markdown("---")

    if st.button("🎯 Analyze My Profile & Get Score", type="primary", use_container_width=True):
        if not name.strip() or not headline.strip():
            st.error("Please enter at least your name and current headline.")
            return

        profile_data = {
            "name": name,
            "headline": headline,
            "industry": industry,
            "experience_years": experience_years,
            "connections": connections,
            "goal": goal,
            "achievements": achievements,
            "skills": skills,
            "about": about_preview,
            "has_photo": "Yes ✅" if has_photo else "No ❌",
            "has_banner": "Yes ✅" if has_banner else "No ❌",
            "has_featured": "Yes ✅" if has_featured else "No ❌",
            "recommendations": recommendations,
        }

        with st.spinner("Analyzing your profile and building your PRO transformation plan..."):
            try:
                prompt = build_profile_prompt(profile_data)
                result = generate_text(prompt, temperature=0.7, max_tokens=3000)

                st.success("✅ Profile analysis complete!")
                st.markdown("---")
                st.markdown(result)

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
