"""
Profile Enhancer Module — Transforms beginner LinkedIn profiles into
PRO-level profiles with a comprehensive score and action plan.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context, save_to_library_db
from industry_profiles import get_industry_voice_block


_BANNED_PROFILE = """
NEVER write these phrases anywhere in the output:
"passionate about", "results-driven professional", "thought leader", "leverage",
"synergy", "game-changer", "I thrive in fast-paced environments",
"dynamic professional", "I am committed to excellence", "seasoned professional",
"I bring X years of experience", "I help people reach their potential",
"innovative solutions", "value-add", "stakeholder", "circle back",
"I wear many hats", "extensive experience", "proven track record",
"motivated self-starter", "detail-oriented"
"""


def build_profile_prompt(profile_data):
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(profile_data.get("industry", ""))
    return f"""You review LinkedIn profiles the way a hiring manager or premium client does — quickly, honestly, looking for specific signals of credibility, clarity, and character. You give real feedback, not padded encouragement.{profile_ctx}
{industry_voice}

PROFILE BEING REVIEWED:
- Name: {profile_data['name']}
- Headline: {profile_data['headline']}
- Industry: {profile_data['industry']}
- Experience: {profile_data['experience_years']}
- About: {profile_data['about'] or 'None provided'}
- Photo: {profile_data['has_photo']}
- Banner: {profile_data['has_banner']}
- Connections: {profile_data['connections']}
- Featured Section: {profile_data['has_featured']}
- Skills: {profile_data['skills']}
- Recommendations: {profile_data['recommendations']}
- Goal: {profile_data['goal']}
- Achievements: {profile_data['achievements']}

{_BANNED_PROFILE}

---

## PROFILE SCORE: XX/100

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
One honest sentence naming the single biggest thing holding this profile back right now.

## HEADLINE REWRITE
Current: "{profile_data['headline']}"
What specifically is wrong (name the exact word or phrase that fails — not "it's too generic"):

3 rewrites for a {profile_data['industry']} professional:
1. [Authority — what you do + who for + one specific result, under 200 chars]
2. [Value — the transformation you create, under 200 chars]
3. [Personality — more voice, less job description, under 200 chars]

Never use: "Helping", "Passionate", "Empowering", "Driving results" in any headline option.

## PROFILE PHOTO & BANNER
Photo ({profile_data['has_photo']}): Specific advice for {profile_data['industry']} — lighting, background, expression, framing.
Banner ({profile_data['has_banner']}): Exactly what to put on it (size: 1584x396px, tool: Canva), message it must land in 2 seconds.

## EXPERIENCE SECTION
Show the difference with real examples from {profile_data['industry']}:
Bad: [generic example from their field]
Good: [specific result-driven rewrite with real numbers]

Write 2 example rewrites specific to {profile_data['industry']} and {profile_data['experience_years']} experience.

## SKILLS STRATEGY
Current: "{profile_data['skills'] or 'None listed'}"
Which to keep, cut, and add.
The 5 most-searched skills in {profile_data['industry']} right now.
One tactic to get endorsements without asking awkwardly.

## RECOMMENDATIONS
Current count: {profile_data['recommendations']}
Who to ask, how to ask (short message template), what to offer in return.
Realistic timeline to reach 5 quality recommendations.

## FEATURED SECTION
5 specific content types for a {profile_data['industry']} professional with goal: "{profile_data['goal']}".
Not categories — exact asset type + one sentence on why it works for this person.

## 30-DAY ACTION PLAN
Specific actions, not categories.

Week 1 (Days 1-7) — Profile Foundation:
- Day 1: [exact action — time estimate]
- Day 2: [exact action]
- Day 3: [exact action]
- Days 4-7: [batched actions]

Week 2 (Days 8-14) — Content: 4-5 specific actions
Week 3 (Days 15-21) — Network: 4-5 specific actions
Week 4 (Days 22-30) — Authority: 4-5 specific actions

## 3 QUICK WINS — DO THESE TODAY
Each under 20 minutes, each with an immediate measurable impact.
1. [Exact action] — Why it matters: [one specific sentence with expected result]
2. [Exact action] — Why it matters: [one specific sentence]
3. [Exact action] — Why it matters: [one specific sentence]
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
                                  placeholder="e.g., Corporate Lawyer | 12 years | SAN",
                                  key="pe_headline")
        industry = st.text_input("🏭 Industry / Field",
                                  value=st.session_state.get("pe_industry", _p.get("industry", "")),
                                  placeholder="e.g., Legal Practice, Fintech, Oil & Gas",
                                  key="pe_industry")
        experience_years = st.selectbox("📅 Years of Experience",
                                         ["0-1 year (Student/New Grad)", "1-3 years", "3-7 years",
                                          "7-15 years", "15+ years"])
        connections = st.selectbox("🔗 LinkedIn Connections",
                                    ["< 100", "100-500", "500-1000", "1000-5000", "5000+"])
        goal = st.text_input("🎯 Primary Goal",
                              value=st.session_state.get("pe_goal", ""),
                              placeholder="e.g., Attract corporate clients, get appointed SAN, grow consultancy",
                              key="pe_goal")

    with col2:
        achievements  = st.text_area("🏆 Top 3 Career Achievements (with numbers)",
                                      placeholder="e.g., Won Supreme Court case worth N2.4B, built team of 12 associates",
                                      height=100)
        skills        = st.text_area("🛠️ Current Skills Listed on Profile",
                                      placeholder="e.g., Commercial Litigation, Corporate Law, Arbitration, CAMA 2020",
                                      height=80)
        about_preview = st.text_area("📝 Current About Section (first 200 chars is fine)",
                                      placeholder="Paste the beginning of your About section...",
                                      height=80)

        col_a, col_b = st.columns(2)
        with col_a:
            has_photo    = st.checkbox("Has Profile Photo", value=True)
            has_banner   = st.checkbox("Has Banner/Cover Image", value=False)
            has_featured = st.checkbox("Has Featured Section", value=False)
        with col_b:
            recommendations = st.number_input("# of Recommendations",
                                               min_value=0, max_value=50, value=0)

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
            "has_photo":    "Yes" if has_photo    else "No",
            "has_banner":   "Yes" if has_banner   else "No",
            "has_featured": "Yes" if has_featured else "No",
            "recommendations": recommendations,
        }

        with st.spinner("Scoring your profile and building your plan..."):
            try:
                result = generate_text(
                    build_profile_prompt(profile_data),
                    temperature=0.72, max_tokens=8000,
                )
                st.success("Profile analysis complete!")
                st.markdown("---")
                st.markdown(result)

                if st.button("📚 Save Analysis to Post Library", use_container_width=True,
                             key="pe_save_library"):
                    ok = save_to_library_db(result, "🌟 Profile Enhancer",
                                            tags=["profile-analysis", industry.lower()[:20]])
                    st.success("✅ Saved to Post Library!") if ok else st.warning("⚠️ Saved in-session only")

            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                with st.expander("Error details"):
                    import traceback as _tb
                    st.code(_tb.format_exc())
