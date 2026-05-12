"""
utils/industry_profiles.py — Industry Voice DNA for LinkedBoost AI.

Injected into every post generation and optimization prompt to make
AI output sound like it was written by an actual practitioner in that
field — not a generic content bot.

Each profile defines:
  label           — display name
  vocabulary      — words/phrases real practitioners use
  proof_patterns  — how credibility is demonstrated in that industry
  hook_archetypes — hook formulas that land with that audience
  avoid           — what sounds fake/amateur/out-of-touch
  rhythm          — sentence cadence and structural notes
  nigerian_ctx    — Nigeria-specific institutions, regulations, dynamics

Usage:
  from utils.industry_profiles import get_industry_voice_block
  context = get_industry_voice_block(niche_string)
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# INDUSTRY VOICE PROFILES
# ─────────────────────────────────────────────────────────────────────────────

INDUSTRY_VOICE_PROFILES: dict[str, dict] = {

    # ── 1. LEGAL PRACTICE ────────────────────────────────────────────────────
    "legal": {
        "label": "Legal Practice",
        "vocabulary": [
            "locus standi", "fiduciary duty", "precedent", "interlocutory injunction",
            "ex parte", "brief", "retainer", "tortious liability", "caveat emptor",
            "deed of assignment", "undertaking", "without prejudice",
        ],
        "proof_patterns": [
            "Cite a specific case outcome — anonymised but real ('my client's entire shareholding was set aside because of one clause')",
            "Reference Nigerian legislation by exact name: CAMA 2020, Evidence Act Cap E14, Arbitration and Conciliation Act, Cybercrime Act 2015",
            "Name the specific court and what it decided — not 'a court ruled' but 'the Court of Appeal, Lagos Division held that...'",
            "Use a real regulatory body: CAC (Corporate Affairs Commission), SCUML, FIRS, EFCC, NBA, FIDA",
        ],
        "hook_archetypes": [
            "The clause that cost my client ₦12 million. (Two sentences. It was in the boilerplate.)",
            "3 contracts Nigerian founders sign without reading. All 3 will haunt them.",
            "Lagos lawyers will argue about this. Good — it means the point is worth making.",
            "A client called me at 11pm. The acquisition had just closed. The problem had been there since page 4.",
        ],
        "avoid": [
            "American case citations as the primary example (cite Nigerian/Commonwealth cases)",
            "Disclaimers on every sentence ('this is not legal advice')",
            "Treating the reader as legally ignorant",
            "Dense blocks of legalese — if you wouldn't say it in a client meeting, don't write it",
        ],
        "rhythm": (
            "Confident, precise, occasionally dry. Short declarative sentences carry the authority. "
            "Numbered lists for multi-part legal points. One moment of practitioner-level candour per post — "
            "the thing only someone who has actually been in that courtroom would say."
        ),
        "nigerian_ctx": (
            "Institutions: NBA (Nigerian Bar Association), FIDA, NEC, SAN (Senior Advocate of Nigeria), "
            "NJC (National Judicial Council), ICPC, EFCC, SCUML. "
            "Courts: Supreme Court of Nigeria, Court of Appeal, Federal High Court, State High Courts, NIC. "
            "Key legislation: CAMA 2020, AMCON Act, PIA 2021, FIRS Act, Cybercrime Act, Violence Against Persons Act. "
            "Nigerian Bar culture: mandatory CLE hours, silk appointments, Bench-Bar relations."
        ),
    },

    # ── 2. FINTECH / BANKING / FINANCE ───────────────────────────────────────
    "fintech": {
        "label": "Fintech & Financial Services",
        "vocabulary": [
            "float management", "interchange", "chargeback rate", "KYC/AML",
            "BVN", "NIN", "USSD", "tier-1 capital", "NPL ratio",
            "open banking", "settlement window", "payment gateway", "PSB",
            "NIBSS", "NIPS", "wallet float",
        ],
        "proof_patterns": [
            "Cite CBN circulars, NDIC guidelines, or SEC rules by reference number (e.g., 'CBN's January 2024 circular on open banking')",
            "Use specific transaction volumes in naira — not 'we processed a lot' but '₦4.7 billion in Q3'",
            "Compare to an African fintech benchmark: M-Pesa, MTN MoMo, Airtel Money — Nigerians know these",
            "Reference specific Nigerian fintech milestones: Flutterwave, Paystack, Moniepoint, Interswitch, Opay",
        ],
        "hook_archetypes": [
            "Paystack processed ₦1 trillion before most Nigerian banks had an API.",
            "CBN's new circular just changed the maths for every fintech in Nigeria. Here's what it means.",
            "4 things Nigerian fintechs get wrong about KYC — and the one that gets them shut down.",
            "Our chargeback rate hit 3.2% in month 5. Here's the exact thing we fixed.",
        ],
        "avoid": [
            "Blockchain buzzwords used vaguely ('Web3 will save African finance')",
            "Generic 'financial inclusion' sermons without data",
            "Dollar-centric examples as the primary reference — naira-first",
            "Treating CBN regulation as always the villain — nuance matters",
        ],
        "rhythm": (
            "Data-forward and direct. Short punchy claim, then the specific number that proves it. "
            "Slightly more casual than traditional banking. Practitioners in this space are fast-moving — "
            "match that energy. One moment of hard-won insight per post."
        ),
        "nigerian_ctx": (
            "Regulators: CBN, SEC Nigeria, NDIC, NAICOM, PENCOM. "
            "Key players: Flutterwave, Paystack, Moniepoint, Opay, Kuda, Carbon, PalmPay, Interswitch, Remita. "
            "Infrastructure: NIBSS, NIP (NIBSS Instant Payments), NAPS, RTGS. "
            "Licences: Payment Service Bank (PSB), Switching licence, Mobile Money Operator (MMO). "
            "Context: cashless policy, eNaira, BVN linkage mandates, agent banking growth."
        ),
    },

    # ── 3. OIL, GAS & ENERGY ─────────────────────────────────────────────────
    "oil_gas": {
        "label": "Oil, Gas & Energy",
        "vocabulary": [
            "upstream", "midstream", "downstream", "production sharing contract (PSC)",
            "joint venture (JV)", "barrels per day (bpd)", "FPSO", "gas-to-power",
            "marginal field", "gas flaring", "shut-in", "lifting", "OPEC quota",
            "IOC", "indigenous operator",
        ],
        "proof_patterns": [
            "Name specific Nigerian fields or blocks: Agbami, Egina, Bonga, OML 130, Afam",
            "Reference the Petroleum Industry Act 2021 (PIA) and its specific provisions by section",
            "Cite production figures in bpd — not 'Nigeria produces oil' but 'Nigeria's Q1 2024 output averaged 1.28 mbpd'",
            "Reference NUPRC (formerly DPR) regulations or NNPC/NNPC Limited's specific decisions",
        ],
        "hook_archetypes": [
            "Nigeria flares enough gas daily to power Lagos for a week. We've been doing this for 60 years.",
            "The PIA 2021 changed the operating model. Most operators are still running the 2010 playbook.",
            "3 marginal field lessons I learnt the hard way — from 8 years based in Port Harcourt.",
            "An IOC just divested another OML. Here's what that actually means for indigenous operators.",
        ],
        "avoid": [
            "Generic climate hand-wringing without operational specifics",
            "Treating the reader as ignorant of the industry's complexity",
            "'Drill baby drill' energy — the sector is more nuanced than cheerleading or criticism",
            "Ignoring gas-to-power and energy transition context as if it doesn't exist",
        ],
        "rhythm": (
            "Technical authority, accessible to an intelligent non-specialist. Specific field names, "
            "bpd figures, and regulatory references. Personal story when available (time in Port Harcourt, "
            "Warri, Abuja). Short sentences for the punchline. Numbered lists for technical breakdowns."
        ),
        "nigerian_ctx": (
            "Regulators: NUPRC (Nigerian Upstream Petroleum Regulatory Commission), NMDPRA (downstream), "
            "NPPEF, NBET, NDDC. Key entities: NNPC Limited, Shell, TotalEnergies, Eni, ExxonMobil Nigeria, "
            "Seplat Energy, Oando, Heirs Energy. Key legislation: PIA 2021, NOGICD Act. "
            "Geography: Niger Delta, Port Harcourt, Warri, Bonny. Floating storage: FPSO Agbami, FPSO Egina."
        ),
    },

    # ── 4. CONSULTING & STRATEGY ──────────────────────────────────────────────
    "consulting": {
        "label": "Consulting & Strategy",
        "vocabulary": [
            "diagnostic", "hypothesis-driven", "operating model", "workstream",
            "executive alignment", "change management", "MECE", "root cause",
            "value chain", "cost structure", "engagement", "client-facing",
            "structured thinking", "issue tree",
        ],
        "proof_patterns": [
            "Anonymised client case with a specific, verifiable result: 'a mid-size Lagos manufacturer cut overhead by 31% in 11 weeks'",
            "The counter-intuitive insight: 'The problem stated was X. The actual problem was always Y' — and prove it",
            "Reference an industry or sector data point that reframes the conventional wisdom",
            "Contrast what a textbook framework says vs what actually happened on the ground in Nigeria",
        ],
        "hook_archetypes": [
            "The CEO knew the problem. His senior team knew the solution. Nobody had told each other.",
            "I've done 40+ business diagnostics. The real problem is almost never the stated problem.",
            "3 things McKinsey decks always get wrong about Nigerian SMEs.",
            "We saved a client ₦180 million. They almost didn't hire us because our proposal was 4 pages.",
        ],
        "avoid": [
            "Consulting jargon used unironically ('we leveraged our synergies to deliver key deliverables')",
            "Name-dropping firm pedigree instead of insight",
            "Vague 'transformation' language without a before/after and a specific number",
            "Treating Nigerian business context as a variation of Western case studies",
        ],
        "rhythm": (
            "Structured but story-first. The insight is earned through narrative, not stated upfront. "
            "Use the 'here's what I expected vs what I actually found' tension. "
            "Short sentences for the key reveal. Don't bury the insight in paragraph 4."
        ),
        "nigerian_ctx": (
            "Nigerian business context: family-owned conglomerates, FMCGs, public sector MDAs, "
            "infrastructure projects, financial services firms. Key dynamics: informal decision-making, "
            "government contracting, regulatory uncertainty, FX exposure, talent flight. "
            "Local consultancy landscape: PwC Nigeria, KPMG Nigeria, Deloitte Nigeria, EY Nigeria, "
            "Andersen, Ernst & Young. Indigenous firms: Chapel Hill Denham, Coronation Research."
        ),
    },

    # ── 5. TECHNOLOGY / PRODUCT / SAAS ───────────────────────────────────────
    "tech": {
        "label": "Technology & Product",
        "vocabulary": [
            "product-market fit", "DAU/MAU", "retention curve", "churn rate",
            "LTV/CAC", "north star metric", "feature flag", "sprint", "backlog",
            "regression", "API", "webhook", "onboarding funnel", "activation rate",
        ],
        "proof_patterns": [
            "Specific before/after metric: 'retention went from 18% to 41% after we removed the welcome email sequence'",
            "A/B test result with specific lift: 'Variant B converted 2.3× better — because of one word change in the CTA'",
            "Anonymised user quote that reveals the real insight: 'A user told us: I only open the app when I remember it's there'",
            "Time-boxed milestone: 'By month 3 we had 800 users and ₦0 in revenue. Month 7 changed everything'",
        ],
        "hook_archetypes": [
            "We launched. 0 signups in week 1. Here's what we actually learnt — not the inspirational version.",
            "Our retention doubled after we deleted a feature. The feature users had asked for.",
            "The metric we optimised for 6 months was lying to us the entire time.",
            "Nigerian users don't behave the way Y Combinator batch decks assume they will.",
        ],
        "avoid": [
            "'We're building the Stripe/Airbnb of Africa' framing (exhausted)",
            "Silicon Valley metric benchmarks applied directly to Nigerian/African markets",
            "Twitter/X bravado — 'just shipped', 'we're hiring 10x engineers'",
            "Generic startup inspiration without a single specific number or decision",
        ],
        "rhythm": (
            "Analytical and specific. One data point, one story, one insight per post. "
            "Self-aware and occasionally self-deprecating — the posts that perform best in tech "
            "are honest about what didn't work. Short punchy insight sentences after longer context."
        ),
        "nigerian_ctx": (
            "Ecosystem: CcHub (Yaba), Founders Factory Africa, Techstars Lagos, Ventures Platform, "
            "Microtraction, LoftyInc, GreenHouse Capital. Key exits/raises: Flutterwave, Andela, "
            "Paystack (Stripe acquisition), Mono, Curacel, Eden. NITDA, NCC regulatory context. "
            "Market realities: intermittent power, USSD-first users, low card penetration outside Lagos/Abuja."
        ),
    },

    # ── 6. REAL ESTATE & PROPERTY ────────────────────────────────────────────
    "real_estate": {
        "label": "Real Estate & Property",
        "vocabulary": [
            "C of O (Certificate of Occupancy)", "Governor's Consent", "Deed of Assignment",
            "off-plan", "land banking", "gross rental yield", "cap rate",
            "JV development", "off-taker", "title perfection",
            "Survey Plan", "registered title", "Right of Occupancy",
        ],
        "proof_patterns": [
            "Specific location + price comparison: 'A 4-bedroom in Ikoyi is ₦400M. The same layout in Lekki Phase 1 is ₦180M. Here's why'",
            "Title document walkthrough: explain exactly which title documents to verify and what each one proves",
            "Yield calculation shown: 'Purchase price ₦85M, annual rent ₦4.2M — gross yield 4.9%. Here's why that's acceptable for this location'",
            "A deal that went wrong: what the buyer missed in due diligence and what it cost them",
        ],
        "hook_archetypes": [
            "I bought land in Epe in 2019. The people who laughed are now asking for my agent's number.",
            "4 title documents Lagos buyers never verify. One of them will cost you everything.",
            "The Ibeju-Lekki corridor looks like speculation. Here's the infrastructure data that says otherwise.",
            "A client bought a property worth ₦120M. The title was worthless. Here's how it happened.",
        ],
        "avoid": [
            "Instagram real estate energy: 'invest now! limited slots!! DM me!!!'",
            "Vague ROI promises without a specific calculation",
            "Hiding the risks — sophisticated property buyers know there are always risks",
            "Treating all Nigerian markets as Lagos-only",
        ],
        "rhythm": (
            "Numbers-heavy and trust-building. Specific locations, prices, yield calculations, dates. "
            "Transparency about risk builds more credibility than pure optimism. "
            "One story of what can go wrong per week earns more trust than 10 success stories."
        ),
        "nigerian_ctx": (
            "Title documents: C of O, Governor's Consent, Deed of Assignment, Survey Plan, Gazette. "
            "Registries: Lagos Land Registry, Abuja AGIS (Geographic Information Systems). "
            "Markets: Ikoyi, VI (Victoria Island), Lekki (Phase 1, Chevron, Ikota), "
            "Ajah, Ibeju-Lekki, Banana Island, Maitama (Abuja), Asokoro, Wuse 2. "
            "Developments: Eko Atlantic, Alaro City, Lekki Free Trade Zone corridor."
        ),
    },

    # ── 7. HEALTHCARE & MEDICINE ──────────────────────────────────────────────
    "healthcare": {
        "label": "Healthcare & Medicine",
        "vocabulary": [
            "differential diagnosis", "clinical presentation", "comorbidity",
            "drug formulary", "referral pathway", "case management", "NHIS",
            "primary care", "tertiary care", "etiology", "protocol",
            "LUTH", "UCH", "MDCN", "NAFDAC",
        ],
        "proof_patterns": [
            "Anonymised patient case: 'A 52-year-old woman had been to 4 hospitals before we saw her. Here's what was missed'",
            "Nigerian disease burden statistics: hypertension prevalence, malaria incidence, maternal mortality rates — cite the specific figure",
            "Reference NHIS policy changes or FMOH guidelines by name and what they mean practically",
            "Compare Nigerian health infrastructure to a specific benchmark — not to shame, but to locate the gap precisely",
        ],
        "hook_archetypes": [
            "My patient had been told she was fine. Four times. By four different hospitals.",
            "Hypertension kills more Nigerians silently than any disease in the headlines. Here are the numbers.",
            "3 things I've learnt in 10 years of emergency medicine in Lagos that no textbook teaches.",
            "Nigerian doctors are leaving. The real reason isn't what you think it is.",
        ],
        "avoid": [
            "Condescending health tips ('drink 8 glasses of water daily!')",
            "Scare tactics without constructive next steps",
            "Making patients feel guilty for not knowing medical information",
            "Overmedicalisng — not every post needs to be a clinical lecture",
        ],
        "rhythm": (
            "Empathetic authority. Story of a specific patient (thoroughly anonymised) followed by the systemic insight. "
            "One piece of data about Nigerian health outcomes per post. "
            "Never talks down. Assumes the reader is intelligent but not medically trained."
        ),
        "nigerian_ctx": (
            "Institutions: LUTH (Lagos University Teaching Hospital), UCH (University College Hospital Ibadan), "
            "ABUTH, UNTH, NIMR. Regulators: MDCN (Medical and Dental Council), PCN, NAFDAC, NHIS/NHIA. "
            "Context: brain drain, japa syndrome among doctors and nurses, NHIA reforms, "
            "malaria burden, hypertension epidemic, maternal and child health statistics."
        ),
    },

    # ── 8. MARKETING, MEDIA & PR ─────────────────────────────────────────────
    "marketing": {
        "label": "Marketing, Media & PR",
        "vocabulary": [
            "share of voice (SOV)", "earned media", "above-the-line (ATL)", "below-the-line (BTL)",
            "GRP (Gross Rating Point)", "CPM", "conversion funnel", "brand equity",
            "NPS", "content velocity", "media mix", "brand lift",
            "reach and frequency", "APCON", "ARCON",
        ],
        "proof_patterns": [
            "Specific campaign result with a number: 'We hit 14 million impressions at ₦1.2 CPM — here's the creative decision that did it'",
            "Before/after brand metric: 'Brand recall moved from 23% to 41% in 8 weeks. This is the only thing we changed'",
            "A campaign failure with the real reason: 'The brief was right. The insight was wrong. Here's why'",
            "Reference a real Nigerian brand campaign and what it got right or wrong — GTBank, MTN, Guinness, Dangote Cement",
        ],
        "hook_archetypes": [
            "The billboard campaign that went viral for exactly the wrong reason. Here's what the brief said.",
            "Our biggest campaign flop taught me more than the ₦50M win that followed it.",
            "3 Nigerian brands that are quietly killing it on LinkedIn. And the one thing they all do.",
            "Clients keep asking for 'virality'. Here's what they actually need instead.",
        ],
        "avoid": [
            "'Content is king' — it's 2025, not 2012",
            "Vanity metric worship: impressions without conversion context",
            "Generic social media tips that apply to any industry in any country",
            "American/UK campaign references as the primary example — Nigerian campaigns first",
        ],
        "rhythm": (
            "Punchy and creative. Specific real campaigns by name when possible. "
            "Numbers when available — don't float around creative territory without grounding it in results. "
            "Occasional wit. Storytelling-first, data-second."
        ),
        "nigerian_ctx": (
            "Regulators: APCON (Advertising Practitioners Council of Nigeria), ARCON, NBC. "
            "Agencies: Noah's Ark, DDB Lagos, Insight Redefini, X3M Ideas, Wunderman Thompson Nigeria. "
            "Key brands for examples: GTBank, MTN Nigeria, Airtel Nigeria, Guinness Nigeria, "
            "Dangote, Indomie, Chi Limited, Jumia. Media: TVC, Channels TV, Punch, Guardian, "
            "BellaNaija, TechCabal, Nairametrics."
        ),
    },

    # ── 9. EDUCATION & EDTECH ─────────────────────────────────────────────────
    "education": {
        "label": "Education & EdTech",
        "vocabulary": [
            "learning outcomes", "pedagogy", "curriculum", "cohort completion rate",
            "blended learning", "JAMB", "WAEC", "NECO", "NUC accreditation",
            "TETFUND", "Unity schools", "academic calendar", "matriculation",
        ],
        "proof_patterns": [
            "Specific student outcome: 'A student who failed JAMB twice — here's exactly what we changed in week 3'",
            "Completion rate or test score data: 'Cohort 4 had a 78% WAEC B3-or-above rate. Cohort 1 was 34%'",
            "Reference JAMB statistics or NUC accreditation data by year and specific figure",
            "A systemic constraint named precisely: 'ASUU strikes cost Nigerian undergraduates 30 months of academic time between 2020 and 2023'",
        ],
        "hook_archetypes": [
            "Nigerian students don't have a knowledge problem. They have an access problem.",
            "I've taught 2,000 students in 6 years. The ones who succeed share exactly one habit.",
            "JAMB 2024 results revealed something that educators are not talking about.",
            "The school had 1,400 students and 3 working toilets. We focused on the wrong problem first.",
        ],
        "avoid": [
            "'Education will save Africa' without operational specifics",
            "Condescending to students or parents",
            "Ignoring the systemic constraints that shape Nigerian education outcomes",
            "Comparing Nigerian students unfavourably to Western counterparts without context",
        ],
        "rhythm": (
            "Nurturing but direct. Story of one specific student — not a demographic — then the systemic insight. "
            "Balances hope with clear-eyed honesty about what the system does and doesn't provide. "
            "Data about Nigerian education outcomes earns credibility fast in this space."
        ),
        "nigerian_ctx": (
            "Exams: JAMB (UTME/DE), WAEC, NECO, NABTEB, Cambridge A-Level. "
            "Bodies: NUC (National Universities Commission), NBTE, NCCE, TETFUND. "
            "Institutions: Unity schools (Government Colleges), state schools, private schools, "
            "federal universities, polytechnics, monotechnics. "
            "Context: ASUU strikes, private university boom, EdTech players (uLesson, Gradely, PrepClass). "
            "Brain drain: 60%+ of Nigerian medical graduates now working outside Nigeria."
        ),
    },

    # ── 10. HR, TALENT & PEOPLE OPS ──────────────────────────────────────────
    "hr": {
        "label": "HR, Talent & People Operations",
        "vocabulary": [
            "attrition rate", "employer brand", "onboarding", "performance management cycle",
            "succession planning", "total compensation", "HRIS", "employee NPS",
            "talent acquisition", "PILON", "exit interview", "retention rate",
            "Jobberman", "Workpay", "PENCOM",
        ],
        "proof_patterns": [
            "Specific retention/attrition number: 'We lost 6 people in 30 days. Exit interviews told us the same thing in 5 different words'",
            "Compensation benchmark with source: 'Jobberman's 2024 salary survey shows mid-level product managers in Lagos earning ₦1.8M–₦3.2M monthly'",
            "A hiring mistake — specific, anonymised, honest about what went wrong in the process",
            "Policy change + measurable outcome: 'We moved to 4-day experimental weeks in Q3. Attrition dropped 18% the following quarter'",
        ],
        "hook_archetypes": [
            "We lost 6 people in one month. Exit interviews said the same thing 6 different ways.",
            "Nigerian companies keep posting the same job description. Talent has noticed — and stopped applying.",
            "3 HR metrics Lagos startups don't track — until the resignation letters start coming.",
            "Our best hire never sent a CV. Here's how we found her.",
        ],
        "avoid": [
            "'Our people are our greatest asset' — meaningless without evidence",
            "Corporate HR speak that sounds like a policy document",
            "Victim-blaming employees for attrition instead of examining systemic causes",
            "Treating japa (brain drain) as a loyalty failure rather than a structural issue",
        ],
        "rhythm": (
            "Data-backed empathy. Specific attrition/retention numbers. "
            "Honest about what companies get wrong — including the writer's own organisation. "
            "One vulnerable hiring mistake per post earns more credibility than 5 success stories."
        ),
        "nigerian_ctx": (
            "Labour law: Labour Act Cap L1, National Minimum Wage Act, PENCOM regulations. "
            "Bodies: NLC (Nigeria Labour Congress), TUC, NIM (Nigerian Institute of Management). "
            "Salary data: Jobberman, BudgIT salary surveys. Benefits context: HMO (NHIA), "
            "pension (PENCOM mandatory 8%+10%), transport/housing allowances. "
            "Market context: japa syndrome, tech sector talent wars, gig economy growth, "
            "cost-of-living crisis impact on total comp expectations."
        ),
    },

    # ── 11. STARTUP & ENTREPRENEURSHIP (catch-all) ───────────────────────────
    "startup": {
        "label": "Startup & Entrepreneurship",
        "vocabulary": [
            "burn rate", "runway", "cap table", "term sheet",
            "pre-seed", "seed round", "Series A", "MVP",
            "unit economics", "ARR", "MRR", "churn",
            "product-market fit", "investor deck", "angel round",
        ],
        "proof_patterns": [
            "Specific revenue milestone in naira: 'Month 1: ₦0. Month 8: ₦4.2M MRR. Here's the one decision that changed the trajectory'",
            "Fundraising reality: 'We pitched 47 investors. 45 passed. Here's what the 2 who said yes saw that the others missed'",
            "Team growth with a real tension: 'Hiring our 8th person broke something. Fixing it took longer than building the product'",
            "A pivot — specific, with before and after numbers, and honest about what triggered it",
        ],
        "hook_archetypes": [
            "We had ₦0 in revenue at month 6. Here's what changed everything — not the inspiration version.",
            "47 investors passed on us. The 48th said yes. I now know exactly why.",
            "We were growing 40% month-on-month. Then we hired the wrong person for one role.",
            "Nigerian VCs kept saying 'the market isn't ready'. Our customers didn't agree.",
        ],
        "avoid": [
            "Hustle porn: 'sleep is for the weak', '18-hour days', toxic grind culture",
            "Toxic positivity: 'failure is just feedback!' without the actual story of what failed",
            "Vague success stories: 'we scaled the business' — scale to what, from what, in how long?",
            "American VC Twitter energy transplanted uncritically into the Nigerian context",
        ],
        "rhythm": (
            "Honest and specific. Number + story + insight per post. "
            "Self-aware about the failures — the best startup posts in Nigeria in 2025 are the ones "
            "that don't pretend the founder had everything figured out. Short sentences for the key reveal."
        ),
        "nigerian_ctx": (
            "Ecosystem: CcHub, Techstars Lagos, Ventures Platform, Microtraction, LoftyInc, "
            "GreenHouse Capital, Founders Factory Africa, Ingressive for Good. "
            "Notable exits/raises: Flutterwave ($3B valuation), Paystack (Stripe acquisition), "
            "Andela, Wave, Mono, Curacel, Eden Life. "
            "Funding realities: limited Series A+ capital in Nigeria, angel drought, "
            "FX risks for USD-denominated funds, regulatory uncertainty for startups."
        ),
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# DETECTION & INJECTION
# ─────────────────────────────────────────────────────────────────────────────

_MATCH_MAP: list[tuple[list[str], str]] = [
    (
        ["legal", "law", "lawyer", "barrister", "attorney", "solicitor",
         "litigation", "nba ", "nba,", "san ", "court", "chambers", "counsel"],
        "legal",
    ),
    (
        ["fintech", "banking", "finance", "payments", "investment",
         "capital market", "cbn", "ican", "cibn", "insurance", "microfinance"],
        "fintech",
    ),
    (
        ["oil", "gas", "energy", "petroleum", "upstream", "downstream",
         "nnpc", "dpr", "nuprc", "refinery", "psc", "fpso", "marginal field"],
        "oil_gas",
    ),
    (
        ["consulting", "strategy", "management consult", "advisory",
         "mckinsey", "pwc", "kpmg", "deloitte", "ey ", "andersen"],
        "consulting",
    ),
    (
        ["tech", "saas", "software", "product manager", "developer",
         "engineer", "startup", "app", "platform", "api", "product"],
        "tech",
    ),
    (
        ["real estate", "property", "realtor", "housing", "construction",
         "land", "mortgage", "c of o", "landlord", "tenant"],
        "real_estate",
    ),
    (
        ["health", "medical", "medicine", "doctor", "hospital", "clinical",
         "nhis", "pharmacist", "nursing", "physician", "surgeon"],
        "healthcare",
    ),
    (
        ["marketing", "media", "advertising", "pr ", "public relation",
         "brand", "content market", "digital market", "apcon", "arcon"],
        "marketing",
    ),
    (
        ["education", "edtech", "teaching", "school", "university",
         "learning", "jamb", "waec", "nuc", "academic", "tutor"],
        "education",
    ),
    (
        ["hr", "human resource", "talent", "recruitment", "people ops",
         "hiring", "workforce", "hris", "payroll"],
        "hr",
    ),
]


def detect_industry(niche_or_industry: str) -> str:
    """
    Match a free-text niche/industry string to an INDUSTRY_VOICE_PROFILES key.
    Returns 'startup' as the catch-all if no specific match is found.
    """
    text = niche_or_industry.lower()
    for keywords, key in _MATCH_MAP:
        if any(kw in text for kw in keywords):
            return key
    return "startup"


def get_industry_voice_block(niche_or_industry: str) -> str:
    """
    Returns a formatted prompt block injecting industry-specific writing DNA.
    Pass the result directly into your prompt string.
    Returns an empty string if niche_or_industry is blank.
    """
    if not niche_or_industry.strip():
        return ""

    key     = detect_industry(niche_or_industry)
    profile = INDUSTRY_VOICE_PROFILES[key]

    vocab        = ", ".join(profile["vocabulary"][:8])
    proof_lines  = "\n   ".join(f"• {p}" for p in profile["proof_patterns"])
    hook_lines   = "\n   ".join(f"• {h}" for h in profile["hook_archetypes"])
    avoid_lines  = "\n   ".join(f"• {a}" for a in profile["avoid"])

    return f"""
INDUSTRY VOICE DNA — writing as a {profile['label']} professional:

Vocabulary practitioners actually use (weave in naturally, not all at once):
  {vocab}

Proof patterns — use AT LEAST ONE of these to signal real-world credibility:
   {proof_lines}

Hook archetypes that land with this audience (use as inspiration, not template):
   {hook_lines}

What sounds fake or amateur in this industry (avoid entirely):
   {avoid_lines}

Sentence rhythm: {profile['rhythm']}

Nigerian professional context to draw from naturally:
  {profile['nigerian_ctx']}
"""
