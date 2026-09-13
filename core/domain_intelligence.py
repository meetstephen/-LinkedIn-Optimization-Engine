"""Domain intelligence used by every writing module.

The original app mapped every unfamiliar niche to ``startup``.  That made the
copy sound specific while often being specific to the wrong profession.  This
module uses scored, word-boundary matching, supports cross-disciplinary
niches, and returns an honest custom-domain fallback when no profile matches.

Profiles deliberately contain durable practitioner knowledge (workflows,
metrics, stakeholders and recurring tensions), not current statistics.  Fresh
facts belong in the grounded research layer or in user-supplied source notes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DomainProfile:
    key: str
    label: str
    aliases: tuple[str, ...]
    vocabulary: tuple[str, ...]
    workflows: tuple[str, ...]
    metrics: tuple[str, ...]
    stakeholders: tuple[str, ...]
    tensions: tuple[str, ...]
    proof: tuple[str, ...]
    avoid: tuple[str, ...]


def _p(key, label, aliases, vocabulary, workflows, metrics, stakeholders,
       tensions, proof, avoid) -> DomainProfile:
    return DomainProfile(
        key, label, tuple(aliases), tuple(vocabulary), tuple(workflows),
        tuple(metrics), tuple(stakeholders), tuple(tensions), tuple(proof),
        tuple(avoid),
    )


DOMAIN_PROFILES: dict[str, DomainProfile] = {
    p.key: p for p in (
        _p("legal", "Legal & Compliance", ("law", "lawyer", "legal", "litigation", "compliance", "counsel"),
           ("material breach", "indemnity", "governing law", "discovery", "regulatory exposure", "closing conditions"),
           ("matter intake", "fact pattern", "legal research", "drafting", "negotiation", "filing and enforcement"),
           ("cycle time", "outside-counsel spend", "matter outcome", "contract turnaround", "compliance exceptions"),
           ("client", "counterparty", "court", "regulator", "in-house counsel"),
           ("speed vs defensibility", "commercial intent vs legal risk", "precedent vs novel facts"),
           ("identify the clause, decision point and consequence", "distinguish law, interpretation and practical advice"),
           ("invented cases or section numbers", "absolute legal conclusions", "US law assumed for every jurisdiction")),
        _p("fintech", "Banking, Fintech & Payments", ("fintech", "banking", "payments", "finance", "microfinance", "open banking"),
           ("settlement", "reconciliation", "authorization rate", "KYC", "AML", "chargeback", "liquidity"),
           ("onboarding", "risk scoring", "payment authorization", "settlement", "reconciliation", "dispute handling"),
           ("approval rate", "fraud-loss rate", "cost per transaction", "take rate", "NPL ratio", "deposit growth"),
           ("customer", "merchant", "issuer", "acquirer", "switch", "regulator"),
           ("conversion vs fraud", "growth vs compliance", "instant UX vs settlement reality"),
           ("trace one transaction end-to-end", "show the denominator and time window behind a metric"),
           ("fabricated transaction volumes", "financial-inclusion slogans without mechanics", "treating all finance as crypto")),
        _p("insurance", "Insurance", ("insurance", "insurtech", "underwriting", "claims", "actuarial"),
           ("loss ratio", "combined ratio", "premium", "exposure", "reserve", "reinsurance"),
           ("distribution", "underwriting", "policy issuance", "premium collection", "claims adjudication", "renewal"),
           ("loss ratio", "combined ratio", "claim frequency", "claim severity", "retention", "expense ratio"),
           ("policyholder", "broker", "underwriter", "claims adjuster", "reinsurer", "regulator"),
           ("growth vs underwriting discipline", "fast claims vs fraud controls", "affordability vs adequate cover"),
           ("walk through an underwriting or claims decision", "separate insured value, limit, excess and payout"),
           ("promising coverage without policy wording", "confusing premium with insured value", "invented claim outcomes")),
        _p("technology", "Software, Product & SaaS", ("software", "saas", "product", "developer", "engineering", "technology", "platform", "api"),
           ("activation", "retention cohort", "latency", "error budget", "feature flag", "technical debt"),
           ("discovery", "prioritisation", "delivery", "instrumentation", "release", "incident review"),
           ("activation rate", "retention", "churn", "latency", "availability", "deployment frequency"),
           ("user", "buyer", "product", "engineering", "support", "security"),
           ("speed vs reliability", "customer request vs product strategy", "local optimisation vs system health"),
           ("name the user behaviour and metric that changed", "explain the technical or product mechanism"),
           ("invented A/B-test lifts", "vanity shipping updates", "calling every feature AI")),
        _p("data_ai", "Data, Analytics & AI", ("artificial intelligence", "machine learning", "data science", "analytics", "data engineering", "generative ai", " llm"),
           ("ground truth", "feature drift", "precision", "recall", "evaluation set", "lineage", "hallucination"),
           ("problem framing", "data collection", "labeling", "training", "evaluation", "deployment and monitoring"),
           ("precision", "recall", "F1", "calibration", "latency", "cost per inference", "data freshness"),
           ("domain expert", "data owner", "model builder", "reviewer", "end user", "risk team"),
           ("accuracy vs coverage", "automation vs review", "benchmark score vs production behaviour"),
           ("define the evaluation set and failure class", "show where human review remains"),
           ("benchmark claims without datasets", "AI-will-replace-everyone rhetoric", "confusing a demo with production")),
        _p("cybersecurity", "Cybersecurity & Privacy", ("cybersecurity", "information security", "infosec", "privacy", "soc", "cloud security", "zero trust"),
           ("attack surface", "threat model", "blast radius", "least privilege", "dwell time", "data classification"),
           ("asset inventory", "threat modeling", "prevention", "detection", "containment", "recovery"),
           ("MTTD", "MTTR", "patch latency", "control coverage", "false-positive rate", "phishing-report rate"),
           ("employee", "security team", "IT", "vendor", "attacker", "regulator"),
           ("friction vs control", "visibility vs privacy", "prevention vs resilience"),
           ("use an attack path or control failure", "separate likelihood, impact and residual risk"),
           ("actionable exploit detail", "fear-only selling", "claiming any control makes a system secure")),
        _p("healthcare", "Healthcare & Life Sciences", ("healthcare", "medical", "medicine", "clinical", "hospital", "pharma", "nursing", "public health"),
           ("care pathway", "triage", "contraindication", "adherence", "sensitivity", "specificity", "patient safety"),
           ("screening", "diagnosis", "treatment planning", "care delivery", "follow-up", "quality review"),
           ("wait time", "readmission", "adherence", "mortality", "length of stay", "cost per case"),
           ("patient", "caregiver", "clinician", "payer", "facility", "regulator"),
           ("access vs quality", "sensitivity vs specificity", "protocol vs individual context"),
           ("state population and outcome boundaries", "distinguish evidence, clinical judgment and lived experience"),
           ("diagnosis or treatment claims", "invented patient stories", "causal claims from weak evidence")),
        _p("marketing", "Marketing, Brand & Communications", ("marketing", "brand", "advertising", "communications", "content", "public relations", "growth marketing"),
           ("positioning", "share of voice", "creative fatigue", "incrementality", "attribution", "message-market fit"),
           ("research", "segmentation", "positioning", "creative development", "distribution", "measurement"),
           ("CAC", "conversion rate", "incremental lift", "reach", "frequency", "brand recall", "pipeline influenced"),
           ("audience", "customer", "creative team", "sales", "channel partner", "media owner"),
           ("brand vs performance", "reach vs relevance", "short-term conversion vs memory building"),
           ("connect message, channel, audience and measured behaviour", "separate correlation from incrementality"),
           ("invented campaign results", "viral as a strategy", "engagement reported without business impact")),
        _p("sales", "Sales & Revenue", ("sales", "revenue", "business development", "account executive", "commercial", "go-to-market", "gtm"),
           ("qualification", "deal velocity", "pipeline coverage", "multi-threading", "champion", "procurement"),
           ("prospecting", "discovery", "qualification", "solution mapping", "negotiation", "close and expansion"),
           ("win rate", "sales-cycle length", "ACV", "pipeline coverage", "quota attainment", "net revenue retention"),
           ("buyer", "user", "champion", "economic buyer", "procurement", "legal"),
           ("volume vs fit", "forecast confidence vs optimism", "discount vs value"),
           ("reconstruct the buyer decision and stalled stage", "show conversion between funnel stages"),
           ("fake deal values", "pressure tactics presented as universal", "pipeline advice without buyer context")),
        _p("hr", "People, HR & Talent", ("human resources", " hr ", "people operations", "talent", "recruitment", "workforce", "learning and development"),
           ("workforce planning", "time to productivity", "quality of hire", "psychological safety", "span of control", "succession"),
           ("workforce planning", "sourcing", "selection", "onboarding", "performance", "development and retention"),
           ("time to hire", "quality of hire", "regrettable attrition", "engagement", "internal mobility", "time to productivity"),
           ("candidate", "employee", "manager", "leadership", "HR", "works council or regulator"),
           ("consistency vs context", "speed vs candidate quality", "performance accountability vs safety"),
           ("name the people decision and observed behaviour", "separate sentiment from operational outcomes"),
           ("invented employee stories", "universal culture prescriptions", "legal claims across jurisdictions")),
        _p("education", "Education & Learning", ("education", "school", "university", "teacher", "learning", "edtech", "training", "academic"),
           ("learning objective", "formative assessment", "mastery", "cognitive load", "rubric", "student persistence"),
           ("needs analysis", "curriculum design", "instruction", "practice", "assessment", "feedback and iteration"),
           ("completion", "mastery", "attendance", "progression", "student-teacher ratio", "time on task"),
           ("learner", "teacher", "parent", "institution", "employer", "regulator"),
           ("access vs quality", "coverage vs mastery", "assessment performance vs durable learning"),
           ("show the learning objective, activity and evidence", "name the learner context"),
           ("guaranteed learning outcomes", "technology as pedagogy", "one-size-fits-all advice")),
        _p("real_estate", "Real Estate, Construction & Property", ("real estate", "property", "construction", "housing", "realtor", "mortgage", "architecture"),
           ("title due diligence", "cap rate", "rental yield", "vacancy", "variation order", "practical completion"),
           ("site selection", "feasibility", "design", "approvals", "construction", "leasing or sale"),
           ("yield", "vacancy", "cost per square metre", "schedule variance", "cost variance", "absorption"),
           ("buyer", "tenant", "developer", "contractor", "lender", "planning authority"),
           ("cost vs lifecycle value", "speed vs build quality", "headline yield vs vacancy and maintenance"),
           ("show assumptions in the yield or project calculation", "name the document, approval or handoff at risk"),
           ("invented prices", "guaranteed appreciation", "ignoring title and jurisdiction")),
        _p("manufacturing", "Manufacturing & Operations", ("manufacturing", "factory", "industrial", "operations", "production", "lean", "quality assurance"),
           ("throughput", "first-pass yield", "changeover", "bottleneck", "OEE", "scrap", "preventive maintenance"),
           ("demand planning", "scheduling", "material staging", "production", "quality control", "dispatch"),
           ("OEE", "cycle time", "first-pass yield", "scrap rate", "downtime", "schedule attainment"),
           ("operator", "maintenance", "quality", "planner", "supplier", "customer"),
           ("utilisation vs flow", "inventory buffer vs working capital", "speed vs quality"),
           ("trace the constraint through the line", "use before/after process measures with a time window"),
           ("invented savings", "lean slogans without process detail", "blaming operators for system design")),
        _p("supply_chain", "Supply Chain, Logistics & Procurement", ("supply chain", "logistics", "procurement", "shipping", "freight", "warehouse", "last mile", "transport"),
           ("lead time", "fill rate", "demurrage", "landed cost", "safety stock", "OTIF", "supplier concentration"),
           ("source", "order", "transport", "clearance", "receive", "store and fulfil"),
           ("OTIF", "lead time", "cost per shipment", "inventory turns", "stockout rate", "damage rate"),
           ("supplier", "buyer", "carrier", "customs", "warehouse", "customer"),
           ("resilience vs cost", "inventory availability vs cash", "speed vs consolidation"),
           ("follow one shipment or purchase order", "separate quoted price from total landed cost"),
           ("invented route savings", "generic efficiency language", "ignoring customs and handoff risk")),
        _p("agriculture", "Agriculture & Food Systems", ("agriculture", "agritech", "farming", "food production", "livestock", "crop", "agronomy"),
           ("yield per hectare", "post-harvest loss", "extension", "off-taker", "cold chain", "input quality"),
           ("input planning", "production", "harvest", "aggregation", "storage", "processing and market access"),
           ("yield", "mortality", "feed conversion", "post-harvest loss", "farmgate price", "rejection rate"),
           ("farmer", "aggregator", "off-taker", "processor", "lender", "extension officer"),
           ("yield vs input cost", "scale vs traceability", "farmgate price vs consumer affordability"),
           ("name crop, geography, season and unit economics", "trace value lost between harvest and sale"),
           ("invented yields", "farmer-as-beneficiary framing", "climate claims without location and season")),
        _p("energy", "Energy, Oil & Gas, and Utilities", ("energy", "oil", "gas", "petroleum", "utility", "power", "renewable", "solar"),
           ("capacity factor", "offtake", "curtailment", "lifting cost", "downtime", "metering", "dispatch"),
           ("resource or feedstock", "production", "transmission", "distribution", "metering", "settlement"),
           ("availability", "capacity factor", "losses", "cost per unit", "downtime", "collection efficiency"),
           ("producer", "operator", "off-taker", "community", "regulator", "customer"),
           ("reliability vs affordability", "production vs evacuation", "transition ambition vs grid reality"),
           ("trace molecules or electrons through the value chain", "state units, period and operating boundary"),
           ("invented production figures", "ESG slogans without assets and economics", "confusing capacity with generation")),
        _p("telecom", "Telecommunications", ("telecom", "telecommunications", "mobile network", "broadband", "isp", "connectivity"),
           ("ARPU", "churn", "spectrum", "backhaul", "dropped-call rate", "network availability"),
           ("coverage planning", "site acquisition", "deployment", "optimisation", "assurance", "billing and care"),
           ("ARPU", "churn", "availability", "latency", "throughput", "drop rate", "cost per site"),
           ("subscriber", "operator", "tower company", "vendor", "regulator", "content provider"),
           ("coverage vs capacity", "quality vs affordability", "capex vs customer experience"),
           ("connect a network event to customer impact", "distinguish population coverage from service quality"),
           ("invented subscriber counts", "5G hype without use case", "coverage claims without methodology")),
        _p("accounting", "Accounting, Audit & Tax", ("accounting", "audit", "tax", "bookkeeping", "controller", "cfo", "treasury"),
           ("materiality", "control deficiency", "working capital", "reconciliation", "provision", "cash conversion"),
           ("record", "reconcile", "close", "review", "report", "assure or file"),
           ("days sales outstanding", "cash conversion cycle", "close time", "error rate", "tax exposure", "working capital"),
           ("management", "board", "auditor", "tax authority", "investor", "lender"),
           ("speed vs control", "tax efficiency vs defensibility", "profit vs cash"),
           ("walk from transaction to statement or return", "state accounting basis, period and assumption"),
           ("invented tax rates", "profit and cash treated as identical", "jurisdiction-free compliance advice")),
        _p("public_sector", "Public Policy & Government", ("public policy", "government", "public sector", "civil service", "regulation", "policy", "ngo", "development"),
           ("implementation capacity", "appropriation", "service delivery", "stakeholder consultation", "compliance burden", "theory of change"),
           ("problem definition", "consultation", "design", "budgeting", "implementation", "monitoring and evaluation"),
           ("coverage", "uptake", "unit cost", "processing time", "compliance", "outcome indicator"),
           ("citizen", "ministry or agency", "legislature", "implementer", "funder", "regulated entity"),
           ("policy intent vs implementation", "coverage vs service quality", "speed vs due process"),
           ("identify instrument, implementing body and affected group", "separate outputs from outcomes"),
           ("invented policy dates", "partisan claims posed as analysis", "announcements treated as implementation")),
        _p("consulting", "Consulting & Professional Services", ("consulting", "advisory", "strategy", "professional services", "management consultant"),
           ("hypothesis", "workstream", "operating model", "decision rights", "root cause", "benefits realisation"),
           ("scope", "diagnose", "analyse", "align", "recommend", "implement and measure"),
           ("time to value", "adoption", "cost reduction", "revenue uplift", "cycle time", "benefit realised"),
           ("client sponsor", "workstream owner", "frontline team", "customer", "vendor", "board"),
           ("analysis vs adoption", "scope vs emergent reality", "executive alignment vs frontline constraints"),
           ("show the stated problem, root cause and changed decision", "use anonymised evidence supplied by the user"),
           ("invented client results", "framework name-dropping", "transformation without an operating change")),
        _p("entrepreneurship", "Entrepreneurship & Small Business", ("founder", "startup", "entrepreneur", "small business", "sme", "business owner"),
           ("runway", "gross margin", "repeat purchase", "working capital", "distribution", "founder-market fit"),
           ("problem discovery", "offer design", "customer acquisition", "delivery", "cash collection", "retention"),
           ("runway", "gross margin", "conversion", "repeat rate", "cash cycle", "customer concentration"),
           ("founder", "customer", "employee", "supplier", "investor", "regulator"),
           ("growth vs cash", "custom work vs repeatable offer", "speed vs operational control"),
           ("name the customer decision and unit economics", "distinguish revenue, margin and cash collected"),
           ("invented revenue milestones", "hustle slogans", "fundraising treated as customer value")),
    )
}


_TOKEN_RE = re.compile(r"[a-z0-9+#]+")


def _normalise(value: str) -> str:
    return " ".join(_TOKEN_RE.findall((value or "").lower()))


def _alias_score(text: str, alias: str) -> int:
    alias_n = _normalise(alias)
    if not alias_n:
        return 0
    if re.search(rf"(?<![a-z0-9]){re.escape(alias_n)}(?![a-z0-9])", text):
        return 4 + alias_n.count(" ") * 2
    return 0


def detect_domains(niche: str, *, limit: int = 2) -> list[DomainProfile]:
    """Return best matching domains, or an empty list for an unknown niche."""
    text = _normalise(niche)
    if not text:
        return []
    ranked: list[tuple[int, DomainProfile]] = []
    for profile in DOMAIN_PROFILES.values():
        score = max((_alias_score(text, a) for a in profile.aliases), default=0)
        if score:
            ranked.append((score, profile))
    ranked.sort(key=lambda item: (-item[0], item[1].label))
    return [profile for _, profile in ranked[: max(1, limit)]]


def detect_industry_key(niche: str) -> str:
    matches = detect_domains(niche, limit=1)
    return matches[0].key if matches else "custom"


def vocabulary_for(niche: str) -> tuple[str, ...]:
    out: list[str] = []
    for profile in detect_domains(niche):
        out.extend(profile.vocabulary)
        out.extend(profile.metrics)
    return tuple(dict.fromkeys(out))


def _bullets(values: Iterable[str]) -> str:
    return "\n".join(f"- {v}" for v in values)


def build_domain_block(niche: str) -> str:
    """Build durable subject-matter context without inventing current facts."""
    niche = (niche or "").strip()
    if not niche:
        return ""
    matches = detect_domains(niche)
    if not matches:
        return f"""
DOMAIN INTELLIGENCE — CUSTOM NICHE: {niche}
- Do not silently reinterpret this niche as a better-known industry.
- Use the exact niche language supplied by the user.
- Establish specificity from the user's facts or grounded research only.
- Explain the real workflow, stakeholders, trade-offs, and decision involved.
- If a necessary fact is missing, write around it or mark the uncertainty; never invent it.
"""

    sections = []
    for profile in matches:
        sections.append(f"""### {profile.label}
Practitioner language (use only where accurate): {", ".join(profile.vocabulary)}
Operational workflow: {" → ".join(profile.workflows)}
Decision metrics: {", ".join(profile.metrics)}
Stakeholders: {", ".join(profile.stakeholders)}
Recurring tensions: {"; ".join(profile.tensions)}
Credibility patterns:
{_bullets(profile.proof)}
Failure modes to avoid:
{_bullets(profile.avoid)}""")
    return """
DOMAIN INTELLIGENCE — durable practitioner context, not a source of current facts.
Use it to reason about mechanisms and trade-offs. Never turn a listed metric,
regulation, company, example or workflow into a claimed fact about the user.
Do not force jargon; explain cause and effect in plain language.

""" + "\n\n".join(sections)
