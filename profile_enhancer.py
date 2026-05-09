"""
Profile Enhancer Module — Transforms beginner LinkedIn profiles into
PRO-level profiles with a comprehensive score and action plan.
"""
import streamlit as st
from utils.gemini_client import generate_text, get_profile_context


def build_profile_prompt(profile_data):
    profile_ctx = get_profile_context()
    return f"""You review LinkedIn profiles the way a hiring manager or premium client does — quickly, honestly, and looking for specific signals. You've seen what works and what kills opportunities.

Review this profile and give an honest, specific improvement plan.{profile_ctx}

PROFILE:
- Name: {profile_data['name']}
- Headline: {profile_data['headline']}
- Industry: {profile_data['industry']}
- Experience: {profile_data['experience_years']}
- About: {profile_data['about'] or 'None'}
- Photo: {profile_data['has_photo']}
- Banner: {profile_data['has_banner']}
- Connections: {profile_data['connections']}
- Featured Section: {profile_data['has_featured']}
- Skills: {profile_data['skills']}
- Recommendations: {profile_data['recommendations']}
- Goal: {profile_data['goal']}
- Achievements: {profile_data['achievements']}

NEVER use: "passionate about", "results-driven professional", "thought leader",
"leverage", "synergy", "game-changer", "I thrive in fast-paced environments",
"dynamic professional", "I am committed to excellence"

---

## PROFILE SCORE: XX/100

Score each section in a table:
| Section | Score | Max | Status |
|---------|-------|-----|--------|
| Headline | X | 15 | [🔴 Needs Work / 🟡 OK / 🟢 Strong] |
| About Section | X | 20 | [...] |
| Profile Photo | X | 10 | [...] |
| Banner Image | X | 10 | [...] |
| Experience Section | X | 20 | [...] |
| Skills & Endorsements | X | 10 | [...] |
| Recommendations | X | 10 | [...] |
| Activity & Content | X | 5 | [...] |

**TOTAL: XX/100 — [Beginner / Intermediate / Advanced / PRO]**
One honest sentence on what's holding them back most.

## HEADLINE REWRITE
Current: "{profile_data['headline']}"

What's wrong with it (specific — not "it's too generic"):

3 rewritten options:
1. [Authority angle — what you do + who you do it for + one specific result]
2. [Value angle — the transformation you create]
3. [Personality angle — more voice, less job description]

All under 200 characters.

## PROFILE PHOTO
Current: {profile_data['has_photo']}
Specific advice for their industry: lighting, background, expression, framing, what to avoid.

## BANNER IMAGE
Current: {profile_data['has_banner']}
Exactly what to put on it, what size, what tool to use (Canva is fine), what message it should send in 2 seconds.

## EXPERIENCE SECTION
The difference between what most people write and what works:

❌ How most people write it: "Responsible for managing a team and delivering projects"
✅ How it should read: "Led a team of [X] → shipped [specific thing] → drove [specific result with number]"

Write 2–3 example rewrites specific to their industry and role.

## SKILLS STRATEGY
Current: {profile_data['skills']}

Which of these to keep, which to cut, and what to add.
The 5 skills most searched for in their field right now.
How to get endorsements without begging.

## RECOMMENDATIONS
Current count: {profile_data['recommendations']}
Step-by-step: who to ask, exactly how to ask them, what to say, what to offer in return.
Timeline to get 5 quality recommendations.

## FEATURED SECTION
5 specific things to put here based on their industry and goal.
Not "case studies" — actual specific content types with a sentence on why each one works.

## 30-DAY PLAN
Be specific. Not "improve your About section" — say what to write.

Week 1 (Days 1–7):
- Day 1: [exact action]
- Day 2: [exact action]
- Day 3: [exact action]
- Days 4–7: [batched actions]

Week 2 — Content (Days 8–14): [4–5 specific actions]
Week 3 — Network (Days 15–21): [4–5 specific actions]
Week 4 — Authority (Days 22–30): [4–5 specific actions]

## 3 QUICK WINS — DO THESE TODAY
Each one takes under 20 minutes and will immediately improve how the profile reads.
1. [Action] — Why it matters: [one specific sentence]
2. [Action] — Why it matters: [one specific sentence]
3. [Action] — Why it matters: [one specific sentence]
"""


def render_profile_enhancer():
    st.header("🌟 Profile Enhancer: Beginner → PRO")
    st.markdown("Get your LinkedIn profile scored honestly — and a specific plan to fix what's holding you back.")

    _p = st.session_state.get("user_profile", {})

    st.subheader("📋 Enter Your Profile Details")

    col1, col2 = st.columns(2)
    with col1:
        name     = st.text_input("👤 Full Name",
                                  value=st.session_state.get("pe_name", _p.get("name", "")),
                                  placeholder="Your full name", key="pe_name")
        headline = st.text_input("📌 Current Headline",
                                  value=st.session_state.get("pe_headline", _p.get("headline", "")),
                                  placeholder="e.g., Software Engineer at Company | Python | ML",
                                  key="pe_headline")
        industry = st.text_input("🏢 Industry/Field",
                                  value=st.session_state.get("pe_industry", _p.get("industry", "")),
                                  placeholder="e.g., SaaS, Finance, Marketing", key="pe_industry")
        experience_years = st.selectbox("📅 Years of Experience",
                                         ["0–1 year (Student/New Grad)", "1–3 years", "3–7 years",
                                          "7–15 years", "15+ years"])
        connections = st.selectbox("🔗 LinkedIn Connections",
                                    ["< 100", "100–500", "500–1000", "1000–5000", "5000+"])
        goal = st.text_input("🎯 Primary Goal",
                              value=st.session_state.get("pe_goal", ""),
                              placeholder="e.g., Get hired at FAANG, grow my consulting business, become a speaker",
                              key="pe_goal")

    with col2:
        achievements  = st.text_area("🏆 Top 3 Career Achievements",
                                      placeholder="e.g., Built product with 500K users, increased sales by 40%, led team of 15 engineers",
                                      height=80)
        skills        = st.text_area("🛠️ Current Skills Listed",
                                      placeholder="e.g., Python, Project Management, Machine Learning, Leadership",
                                      height=80)
        about_preview = st.text_area("📝 Current About Section (first 200 chars is fine)",
                                      placeholder="Paste beginning of your About section...",
                                      height=80)

        col_a, col_b = st.columns(2)
        with col_a:
            has_photo    = st.checkbox("✅ Has Profile Photo", value=True)
            has_banner   = st.checkbox("✅ Has Banner/Cover Image", value=False)
            has_featured = st.checkbox("✅ Has Featured Section", value=False)
        with col_b:
            recommendations = st.number_input("⭐ # of Recommendations", min_value=0, max_value=50, value=0)

    st.markdown("---")

    if st.button("🎯 Analyze My Profile & Get Score", type="primary", use_container_width=True):
        if not name.strip() or not headline.strip():
            st.error("Please enter at least your name and current headline.")
            return

        profile_data = {
            "name": name, "headline": headline, "industry": industry,
            "experience_years": experience_years, "connections": connections,
            "goal": goal, "achievements": achievements, "skills": skills,
            "about": about_preview,
            "has_photo":    "Yes ✅" if has_photo    else "No ❌",
            "has_banner":   "Yes ✅" if has_banner   else "No ❌",
            "has_featured": "Yes ✅" if has_featured else "No ❌",
            "recommendations": recommendations,
        }

        with st.spinner("Scoring your profile and building your plan..."):
            try:
                prompt = build_profile_prompt(profile_data)
                result = generate_text(prompt, temperature=0.72, max_tokens=3000)

                st.success("✅ Profile analysis complete!")
                st.markdown("---")
                st.markdown(result)

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
