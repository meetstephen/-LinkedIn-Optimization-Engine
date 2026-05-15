"""
About Section Optimizer — Transforms LinkedIn About sections into
powerful personal brand stories with keyword optimization.
"""
import streamlit as st
from gemini_client import generate_text, get_profile_context, save_to_library_db
from industry_profiles import get_industry_voice_block


INDUSTRY_KEYWORDS = {
    "Legal Practice (Nigeria)": "litigation, corporate law, CAMA 2020, CAC, NBA, arbitration, SAN, chambers, retainer, deed of assignment",
    "Fintech / Banking":        "fintech, payments, CBN, KYC, NIBSS, open banking, wallet, PSB, financial inclusion, API",
    "Oil & Gas":                "upstream, midstream, downstream, PIA 2021, NUPRC, NNPC, PSC, marginal field, FPSO, bpd",
    "Consulting & Strategy":    "strategy, transformation, operating model, diagnostics, change management, stakeholder, P&L",
    "Technology":               "product, engineering, SaaS, API, retention, DAU, sprint, roadmap, scale, architecture",
    "Real Estate":              "C of O, Governor's Consent, off-plan, yield, Lekki, Ikoyi, land banking, title perfection",
    "Healthcare":               "clinical, patient outcomes, NHIS, NAFDAC, MDCN, primary care, protocol, comorbidity",
    "Marketing & Media":        "brand, campaigns, APCON, ROI, earned media, share of voice, CPM, content, GTM",
    "Education & EdTech":       "learning outcomes, JAMB, WAEC, NUC, pedagogy, cohort, curriculum, EdTech",
    "HR & People Ops":          "talent, attrition, PENCOM, onboarding, NLC, employer brand, HRIS, total comp",
    "Entrepreneurship":         "founder, startup, PMF, fundraising, ARR, runway, cap table, seed, pre-seed",
    "Other":                    "professional, expertise, strategic, collaborative, impact, results, growth",
}

_BANNED_ABOUT = """
NEVER write these in the About section or any recommendations:
"passionate about", "I am a dedicated", "results-driven professional",
"thought leader", "I'm excited to", "game-changer", "journey", "synergy",
"I thrive in", "I am committed to", "dynamic", "I help people reach their potential",
"fast-paced environment", "innovative solutions", "leverage", "stakeholder",
"value-add", "I wear many hats", "seasoned professional", "extensive experience"
"""


def build_about_prompt(current_about, name, role, industry, superpowers, achievements, goal):
    keywords       = INDUSTRY_KEYWORDS.get(industry, INDUSTRY_KEYWORDS["Other"])
    profile_ctx    = get_profile_context()
    industry_voice = get_industry_voice_block(industry)
    return f"""You write LinkedIn About sections that read like a person wrote them after a long honest conversation — not like a resume, not like a brand deck. The reader should finish it knowing exactly who this person is, what they've done, and why they matter.{profile_ctx}
{industry_voice}

PERSON:
- Name: {name}
- Role: {role}
- Industry: {industry}
- Strengths: {superpowers}
- Achievements: {achievements}
- Goal: {goal}
- Keywords to weave in naturally (not stuffed): {keywords}

CURRENT ABOUT:
\"\"\"
{current_about if current_about.strip() else "Nothing written yet — build from scratch."}
\"\"\"

{_BANNED_ABOUT}

DELIVER:

## BEFORE — WHAT'S WRONG
If they have an existing About, name 3-4 specific problems. Be direct. Quote the exact line that fails.
If blank, skip this section.

## REWRITTEN ABOUT SECTION
Write a 3-paragraph About section (220-280 words):

Para 1 — The Hook:
Opens with a bold statement, specific result, or unusual truth about them.
NOT "I am a [job title]". NOT a question. NOT "Welcome to my profile."
Something that makes the right reader think "this person gets it."

Para 2 — The Story:
What they've actually done. Real numbers. Real moments. The tension they've sat in.
The thing they figured out that others haven't yet.
Ends with: "I help [specific who] [do specific what] by [specific how]."

Para 3 — The CTA:
What should happen next. A genuine invitation, not a sales pitch.
One or two lines maximum.

Style rules:
- "I" is fine — use it naturally
- Short sentences mixed with longer ones for rhythm
- Specific over general: not "many years" — say how many
- One moment of earned honesty or vulnerability per section
- Every keyword must read naturally, not forced

## KEY IMPROVEMENTS
5 specific changes and exactly why each one performs better.
Quote the original line → show the new version → explain the mechanism.

## VALUE PROPOSITION (one line)
"I help [specific who] [achieve specific what] by [specific how]"

## KEYWORDS EMBEDDED
List each keyword used and where — one line each.

## 3 HEADLINE OPTIONS
1. [Authority-focused, under 200 chars]
2. [Value-focused, under 200 chars]
3. [Outcome-focused, under 200 chars]

None should contain: "Helping", "Passionate", "Empowering", "Driving".
"""


def render_about_optimizer():
    st.header("💼 LinkedIn 'About' Section Optimizer")
    st.markdown("Transform your About section into a personal brand story that attracts the right opportunities.")

    _p = st.session_state.get("user_profile", {})

    _ind_options = list(INDUSTRY_KEYWORDS.keys())
    _prof_ind    = _p.get("industry", "").lower()
    _ind_default = next(
        (opt for opt in _ind_options if _prof_ind and _prof_ind[:6] in opt.lower()),
        "Other",
    )
    _ind_idx = _ind_options.index(_ind_default)

    col1, col2 = st.columns(2)

    with col1:
        name     = st.text_input("👤 Your Name",
                                  value=st.session_state.get("ao_name", _p.get("name", "")),
                                  placeholder="e.g., Chidi Okonkwo", key="ao_name")
        role     = st.text_input("💼 Current Role/Title",
                                  value=st.session_state.get("ao_role", _p.get("role", "")),
                                  placeholder="e.g., Senior Associate at Udo Udoma & Belo-Osagie",
                                  key="ao_role")
        industry = st.selectbox("🏭 Industry", _ind_options, index=_ind_idx)
        goal     = st.text_input("🎯 What Do You Want to Achieve?",
                                  value=st.session_state.get("ao_goal", ""),
                                  placeholder="e.g., Attract corporate mandates, build my personal brand as a lawyer",
                                  key="ao_goal")

    with col2:
        superpowers  = st.text_area("Your Top 3-5 Strengths",
                                     placeholder="e.g., Turning complex regulatory problems into clear strategy, closing high-value M&A transactions, building client trust in hostile negotiations",
                                     height=110)
        achievements = st.text_area("Your Best Achievements (with numbers)",
                                     placeholder="e.g., Led N12B acquisition of Lagos hotel portfolio, won Supreme Court appeal after 4 years of litigation, built practice from 0 to 18 clients in 2 years",
                                     height=110)

    current_about = st.text_area("📝 Current About Section (leave blank to build from scratch)",
                                  placeholder="Paste your current LinkedIn About section here...",
                                  height=140)

    st.markdown("---")

    if st.button("Optimize My About Section", type="primary", use_container_width=True):
        if not name.strip() or not role.strip():
            st.error("Please fill in at least your name and current role.")
            return
        if not superpowers.strip():
            st.error("Please share your key strengths.")
            return

        with st.spinner("Writing your About section..."):
            try:
                result = generate_text(
                    build_about_prompt(current_about, name, role, industry,
                                       superpowers, achievements, goal),
                    temperature=0.78,
                    max_tokens=8000,
                )
                st.success("About section optimized!")
                st.markdown("---")

                if current_about.strip():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Before")
                        st.markdown(
                            f'<div style="background:#fff3f3;padding:1rem;border-radius:8px;'
                            f'border-left:4px solid #ff6b6b;font-size:0.9rem;">'
                            f'{current_about.replace(chr(10), "<br>")}</div>',
                            unsafe_allow_html=True)
                    with col2:
                        st.subheader("After (Preview)")
                        lines = result.split("\n")
                        in_section, preview_lines = False, []
                        for line in lines:
                            if "REWRITTEN ABOUT" in line.upper():
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

                pipe1, pipe2 = st.columns(2)
                with pipe1:
                    st.download_button(
                        label="📥 Download About Section",
                        data=result,
                        file_name="linkedin_about_section.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
                with pipe2:
                    if st.button("📚 Save to Post Library", use_container_width=True,
                                 key="ao_save_library"):
                        ok = save_to_library_db(result, "💼 About Optimizer",
                                                tags=["about-section", industry.lower()[:20]])
                        st.success("✅ Saved to Post Library!") if ok else st.warning("⚠️ Saved in-session only")

            except Exception as e:
                st.error(f"Optimization failed: {str(e)}")
                with st.expander("Error details"):
                    import traceback as _tb
                    st.code(_tb.format_exc())
