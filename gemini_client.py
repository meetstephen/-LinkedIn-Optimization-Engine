"""
Gemini API client wrapper for all text generation tasks.
Migrated to google-genai SDK (google.generativeai is deprecated).
"""
from google import genai
from google.genai import types
import streamlit as st

# ── Available models (use flash for speed/cost, pro for quality) ──
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
    max_tokens: int = 2048,
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
