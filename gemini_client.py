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

    return base

def save_to_library_db(content: str, module: str, score: int = 0, tags: list = None) -> bool:
    """
    Save a post directly to Supabase lb_posts table.
    Returns True on success, False on failure.
    All modules import this instead of writing to st.session_state directly.
    """
    import time as _time
    import json as _json

    try:
        from supabase import create_client as _cc
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            # Fallback: write to session state only
            _fallback_save(content, module, score, tags)
            return True
        client = _cc(url, key)
        uid    = st.session_state.get("user_id", "default")
        row = {
            "id":         int(_time.time() * 1000),
            "user_id":    uid,
            "content":    content.strip(),
            "module":     module,
            "score":      score,
            "tags":       _json.dumps(tags or []),
            "created_at": __import__("datetime").datetime.now().strftime("%b %d, %Y · %I:%M %p"),
            "starred":    False,
        }
        client.table("lb_posts").insert(row).execute()
        # Also update session count
        st.session_state["session_posts_generated"] = (
            st.session_state.get("session_posts_generated", 0) + 1
        )
        return True
    except Exception as _e:
        # Supabase failed — fall back to session state
        _fallback_save(content, module, score, tags)
        return False


def _fallback_save(content: str, module: str, score: int = 0, tags: list = None) -> None:
    """Write post to session_state when Supabase is unavailable."""
    import time as _time
    entry = {
        "id":         int(_time.time() * 1000),
        "content":    content.strip(),
        "module":     module,
        "score":      score,
        "tags":       tags or [],
        "created_at": __import__("datetime").datetime.now().strftime("%b %d, %Y · %I:%M %p"),
        "starred":    False,
    }
    st.session_state.setdefault("post_library", []).insert(0, entry)
    st.session_state["session_posts_generated"] = (
        st.session_state.get("session_posts_generated", 0) + 1
    )
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
    """
    Generate text using the Gemini model.

    Args:
        prompt:      The input prompt for generation.
        temperature: Creativity level (0.0 = deterministic, 1.0 = creative).
        max_tokens:  Maximum tokens in the response.
        model:       Model string — defaults to gemini-2.5-flash.

    Returns:
        Generated text string.
    """
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
