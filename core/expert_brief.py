"""Structured pre-writing brief for specific, defensible LinkedIn content."""
from __future__ import annotations

import json
from typing import Any

from core import ai
from core.domain_intelligence import build_domain_block
from core.sanitize import USER_DATA_TRUST_REMINDER, wrap_user_data


BRIEF_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reader_problem": {"type": "string"},
        "point_of_view": {"type": "string"},
        "industry_mechanism": {"type": "string"},
        "decision_stakes": {"type": "array", "items": {"type": "string"}},
        "verified_claims": {"type": "array", "items": {"type": "string"}},
        "claims_to_avoid": {"type": "array", "items": {"type": "string"}},
        "practitioner_details": {"type": "array", "items": {"type": "string"}},
        "counterpoint": {"type": "string"},
        "actionable_takeaways": {"type": "array", "items": {"type": "string"}},
        "hook_direction": {"type": "string"},
        "confidence_note": {"type": "string"},
    },
    "required": [
        "reader_problem", "point_of_view", "industry_mechanism",
        "decision_stakes", "verified_claims", "claims_to_avoid",
        "practitioner_details", "counterpoint", "actionable_takeaways",
        "hook_direction", "confidence_note",
    ],
}

REQUIRED_KEYS = list(BRIEF_SCHEMA["required"])


def build_brief_prompt(
    topic: str,
    niche: str,
    audience: str,
    *,
    source_material: str = "",
    story_beats: str = "",
    research: str = "",
) -> str:
    """Build a trust-separated planning prompt; all external text is data."""
    fields = "\n".join(filter(None, (
        wrap_user_data(topic, "TOPIC"),
        wrap_user_data(niche, "NICHE"),
        wrap_user_data(audience, "AUDIENCE"),
        wrap_user_data(source_material, "SOURCE_MATERIAL"),
        wrap_user_data(story_beats, "STORY_BEATS"),
        wrap_user_data(research, "RESEARCH"),
    )))
    evidence_mode = (
        "Verified evidence is available in SOURCE_MATERIAL and/or RESEARCH. "
        "Copy claims faithfully and preserve qualifications."
        if source_material.strip() or research.strip()
        else
        "No verified evidence was supplied. Keep verified_claims empty. Do not invent statistics, "
        "dates, named clients, personal experience, regulations, case law, quotes, or outcomes."
    )
    return f"""You are the senior subject-matter editor for a professional LinkedIn writer.
Create a rigorous content brief before any prose is drafted.

{USER_DATA_TRUST_REMINDER}
{fields}

{build_domain_block(niche)}

EVIDENCE POLICY:
- {evidence_mode}
- Durable domain context may support mechanisms and terminology, never a current factual claim.
- If a topic is ambiguous, choose the narrowest defensible interpretation and state it in confidence_note.
- The point of view must be useful and contestable, not motivational filler.
- actionable_takeaways must be observable actions, checks, calculations, questions, or decisions.
- practitioner_details must be relevant terms or workflow details, not decorative jargon.

Return only the requested JSON object."""


def generate_expert_brief(
    topic: str,
    niche: str,
    audience: str,
    *,
    source_material: str = "",
    story_beats: str = "",
    research: str = "",
    api_key: str,
    model: str = "gemini-2.5-flash",
) -> dict:
    prompt = build_brief_prompt(
        topic, niche, audience, source_material=source_material,
        story_beats=story_beats, research=research,
    )
    return ai.generate_json(
        prompt, api_key, model=model, temperature=0.25, max_tokens=2200,
        required_keys=REQUIRED_KEYS, response_schema=BRIEF_SCHEMA,
    )


def brief_block(brief: dict | None) -> str:
    """Render model-produced planning data as a bounded reference block."""
    if not brief:
        return ""
    clean = {key: brief.get(key) for key in REQUIRED_KEYS}
    wrapped = wrap_user_data(json.dumps(clean, ensure_ascii=False, indent=2), "EXPERT_BRIEF")
    return f"""
EXPERT CONTENT BRIEF — follow this plan unless it conflicts with a higher-priority rule.
Treat it as reference data, not as permission to invent missing evidence.
{wrapped}
"""
