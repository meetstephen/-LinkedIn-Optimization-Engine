"""Deterministic domain-depth and factual-risk checks for generated posts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.domain_intelligence import vocabulary_for


_GENERIC = (
    "in today's fast-paced world", "ever-evolving landscape", "game changer",
    "unlock your potential", "the future is here", "embrace the journey",
    "it is important to note", "whether you're a seasoned professional",
    "navigate the complexities", "delve into", "valuable insights",
)
_EXPERIENCE = re.compile(
    r"\b(my client|our client|we processed|we shipped|we increased|we reduced|"
    r"my patient|our users|our revenue|our team achieved|i advised|i represented)\b",
    re.IGNORECASE,
)
_PRECISE = re.compile(
    r"(?:[$£€₦]\s?\d|\b\d+(?:\.\d+)?\s?(?:%|million|billion|trillion|x\b|×|days?\b|weeks?\b|months?\b|years?\b))",
    re.IGNORECASE,
)
_MECHANISM = re.compile(
    r"\b(because|which meant|therefore|so that|led to|caused|resulted in|"
    r"trade-?off|constraint|bottleneck|failure mode|decision|changed when)\b",
    re.IGNORECASE,
)
_ACTION = re.compile(
    r"\b(check|measure|compare|review|calculate|map|audit|test|track|remove|"
    r"ask|document|verify|prioriti[sz]e|start with|look for)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class QualityIssue:
    code: str
    message: str
    severity: str = "medium"


@dataclass
class DomainQualityReport:
    score: int
    specificity: int
    mechanism: int
    credibility: int
    actionability: int
    issues: list[QualityIssue] = field(default_factory=list)
    matched_terms: list[str] = field(default_factory=list)

    @property
    def needs_revision(self) -> bool:
        return self.score < 72 or any(i.severity == "critical" for i in self.issues)


def _normalised_evidence(*parts: str) -> str:
    return "\n".join((p or "").lower() for p in parts if p)


def assess_post(
    post: str,
    *,
    niche: str = "",
    audience: str = "",
    supplied_facts: str = "",
    research: str = "",
) -> DomainQualityReport:
    """Score domain depth and flag claims not traceable to supplied context."""
    text = (post or "").strip()
    if not text:
        return DomainQualityReport(0, 0, 0, 0, 0, [QualityIssue("empty", "The draft is empty.", "critical")])

    lower = text.lower()
    terms = [t for t in vocabulary_for(niche) if t.lower() in lower]
    unique_terms = list(dict.fromkeys(terms))
    specific_entities = re.findall(r"\b[A-Z][A-Za-z0-9&.-]{2,}\b", text)
    specificity = min(100, 25 + len(unique_terms) * 12 + min(len(specific_entities), 4) * 5)
    mechanism_hits = len(_MECHANISM.findall(text))
    mechanism = min(100, 20 + mechanism_hits * 18)
    action_hits = len(set(m.lower() for m in _ACTION.findall(text)))
    actionability = min(100, 20 + action_hits * 16)
    credibility = 85
    issues: list[QualityIssue] = []

    generic_hits = [p for p in _GENERIC if p in lower]
    if generic_hits:
        specificity = max(0, specificity - 12 * len(generic_hits))
        issues.append(QualityIssue("generic_language", f"Generic phrasing detected: {', '.join(generic_hits[:3])}."))
    if len(unique_terms) < 2 and niche:
        issues.append(QualityIssue("thin_domain_signal", "The draft does not demonstrate enough practitioner-level domain knowledge."))
    if mechanism_hits < 2:
        issues.append(QualityIssue("thin_mechanism", "The draft states conclusions without explaining enough cause, workflow, or trade-off."))
    if action_hits < 2:
        issues.append(QualityIssue("thin_actionability", "The reader gets too few concrete actions or decision checks."))

    evidence = _normalised_evidence(supplied_facts, research)
    if _EXPERIENCE.search(text) and not supplied_facts.strip():
        credibility -= 45
        issues.append(QualityIssue(
            "invented_experience",
            "The draft speaks as if the author personally handled a client, patient, product, or result that the user did not supply.",
            "critical",
        ))

    unsupported: list[str] = []
    for match in _PRECISE.finditer(text):
        claim = match.group(0).strip()
        if claim.lower() not in evidence:
            unsupported.append(claim)
    if unsupported:
        credibility -= min(55, 14 * len(set(unsupported)))
        issues.append(QualityIssue(
            "unsupported_precision",
            "Precise claims are not traceable to user facts or research: " + ", ".join(list(dict.fromkeys(unsupported))[:5]),
            "critical",
        ))

    if audience and not any(token in lower for token in re.findall(r"[a-z]{4,}", audience.lower())[:6]):
        issues.append(QualityIssue("audience_fit", "The intended audience is not recognisable in the problem, stakes, or advice."))

    credibility = max(0, min(100, credibility))
    score = round(specificity * .30 + mechanism * .25 + credibility * .30 + actionability * .15)
    return DomainQualityReport(
        score=max(0, min(100, score)), specificity=specificity,
        mechanism=mechanism, credibility=credibility,
        actionability=actionability, issues=issues, matched_terms=unique_terms,
    )


def revision_block(report: DomainQualityReport) -> str:
    if not report.issues:
        return ""
    lines = [
        "DOMAIN QUALITY REVIEW — revise the draft to fix every item:",
        *(f"- [{issue.severity.upper()}] {issue.message}" for issue in report.issues),
        "Preserve the user's voice and true details. Do not solve a missing-facts problem by inventing facts.",
    ]
    return "\n".join(lines)
