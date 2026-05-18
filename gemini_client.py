"""
Gemini API client wrapper for all text generation tasks.
Migrated to google-genai SDK (google.generativeai is deprecated).
"""
from google import genai
from google.genai import types
import streamlit as st


def get_profile_context() -> str:
    """
    Returns a formatted profile context string for injection into any AI prompt.
    Reads from st.session_state['user_profile'] — available across all Streamlit modules.
    When Nigerian Voice Mode is active, appends the full Nigerian professional context block.
    Returns an empty string when no profile is configured (safe to concatenate).
    """
    p = st.session_state.get("user_profile", {})
    parts = []
    if p.get("name"):            parts.append(f"- Name: {p['name']}")
    if p.get("headline"):        parts.append(f"- LinkedIn Headline: {p['headline']}")
    if p.get("role"):            parts.append(f"- Current Role: {p['role']}")
    if p.get("industry"):        parts.append(f"- Industry / Niche: {p['industry']}")
    if p.get("audience"):        parts.append(f"- Target Audience: {p['audience']}")
    if p.get("content_pillars"): parts.append(f"- Content Pillars: {', '.join(p['content_pillars'])}")
    if p.get("tone"):            parts.append(f"- Preferred Writing Tone: {p['tone']}")
    if p.get("voice_sample"):
        parts.append(
            f"- Writing Voice Sample (match this style as closely as possible):\n"
            f"\"\"\"\n{p['voice_sample'][:400].strip()}\n\"\"\""
        )

    # ── Voice Fingerprint — structured analysis of the user's writing.
    # When present, this gives Gemini explicit per-user voice rules
    # (avg sentence length, signature phrases, structure, tells) instead of
    # just the raw 400-char sample. Output dramatically more on-voice.
    _fp = p.get("voice_fingerprint") or {}
    if _fp:
        try:
            from core.voice_fingerprint import fingerprint_block as _fp_block
            _fp_text = _fp_block(_fp)
            if _fp_text:
                parts.append(_fp_text)
        except Exception:
            pass

    if not parts:
        return ""

    base = (
        "\n\nUSER PROFILE — tailor ALL output specifically and concretely to this person. "
        "Use their exact industry, role, and audience in every example, hook, and suggestion. "
        "Never give generic advice — make it feel written for them specifically:\n"
        + "\n".join(parts)
    )

    # ── Nigerian Professional Voice Mode ─────────────────────────────────────
    if st.session_state.get("nigerian_mode", False):
        base += """

NIGERIAN PROFESSIONAL VOICE MODE — ACTIVE. Apply ALL of the following:

CULTURAL TONE: Warm, confident, community-oriented. Nigerian professionals value earned
  respect, resilience narratives, and collective uplift — not just personal wins.
  Nigeria is not Lagos. Acknowledge practitioners across Abuja, Port Harcourt, Enugu,
  Kano, Ibadan, Owerri, Kaduna, Benin City — not just the Southwest.

LOCAL CONTEXT: Reference Nigerian business realities naturally — naira pricing,
  infrastructure challenges (power, roads) nationwide, fintech disruption
  (Flutterwave, Paystack, Moniepoint), mobile-first user behaviour, federal/state
  government dynamics, and the diversity of the Nigerian economy beyond oil.

INSTITUTIONS TO DRAW FROM: CBN, CAC, NBA (Nigerian Bar Association), EFCC, FIRS,
  NAFDAC, NCC, SEC Nigeria, NUPRC, NHIS/NHIA, NUC, JAMB, PENCOM, NIM, ICAN, CIBN.

GEOGRAPHIC DIVERSITY: Use examples from across Nigeria — not just Lagos.
  Abuja (government, policy, consulting), Port Harcourt (oil & gas, maritime),
  Kano (manufacturing, agriculture, trade), Enugu (coal belt, judiciary, academia),
  Ibadan (education, agribusiness), Owerri (commerce, diaspora investment).

LANGUAGE FLAVOUR: Posts should feel written by a Nigerian professional — not a
  Silicon Valley content team. Occasional Pidgin phrasing is acceptable where
  culturally natural (e.g. "e no easy" in a story hook, "we move" as a CTA)
  but keep it professional overall. The app serves non-Nigerians too — keep
  Pidgin light enough that any African professional can follow the post.

POSTING TIMES: Always give time advice in WAT (West Africa Time, UTC+1).
  Best windows: Tue & Thu 7–9am WAT, Wed 12–2pm WAT, Fri 6–8pm WAT.

AVOID: Silicon Valley jargon, dollar-centric examples as primary reference,
  treating Nigeria as synonymous with Lagos, assuming all users are in the Southwest."""

        # ── Nigerian Tone Preset (fine-grained voice within Nigerian mode) ────
        _ng_tone = st.session_state.get("nigerian_tone_preset", "")
        if _ng_tone:
            try:
                from industry_profiles import get_nigerian_tone_block
                _tone_block = get_nigerian_tone_block(_ng_tone)
                if _tone_block:
                    base += _tone_block
            except Exception:
                pass

    return base



MODEL_DEFAULT = "gemini-2.5-flash"
MODEL_LITE    = "gemini-2.0-flash-lite"


def get_gemini_client() -> genai.Client:
    """Initialize and return Gemini client using API key from session state."""
    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        raise ValueError(
            "Gemini API key not set. Please enter your API key in the sidebar."
        )
    return genai.Client(api_key=api_key)


def generate_text(
    prompt: str,
    temperature: float = 0.8,
    max_tokens: int = 8000,
    model: str = MODEL_DEFAULT,
) -> str:
    """Generate text and return the full response string."""
    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        return response.text

    except ValueError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {str(e)}")


def stream_text(
    prompt: str,
    temperature: float = 0.8,
    max_tokens: int = 8000,
    model: str = MODEL_DEFAULT,
):
    """
    Stream text generation from Gemini — yields text chunks as they arrive.

    Usage in Streamlit:
        result = st.write_stream(stream_text(prompt))
        # result contains the full text after streaming completes

    Falls back to generate_text() if streaming fails.
    """
    try:
        client = get_gemini_client()
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        ):
            if chunk.text:
                yield chunk.text
    except Exception as e:
        # Streaming failed — yield the full response in one chunk
        try:
            yield generate_text(prompt, temperature, max_tokens, model)
        except Exception as e2:
            raise RuntimeError(f"Gemini streaming error: {str(e)} | Fallback error: {str(e2)}")
