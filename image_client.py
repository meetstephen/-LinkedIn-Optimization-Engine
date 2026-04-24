"""
Gemini API client wrapper for all text generation tasks.
Migrated to google-genai SDK (google.generativeai is deprecated).
Model is resolved from st.session_state["gemini_model"] so the sidebar
switcher in app.py controls every module simultaneously.
"""
from google import genai
from google.genai import types
import streamlit as st

# ── Available models ───────────────────────────────────────────────────────────
MODEL_DEFAULT = "gemini-2.5-flash"       # fast, capable — sidebar default
MODEL_LITE    = "gemini-2.5-flash-lite"  # lighter, use if flash hits quota


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
    model: str = None,
) -> str:
    """
    Generate text using the Gemini model.

    Args:
        prompt:      The input prompt for generation.
        temperature: Creativity level (0.0 = deterministic, 1.0 = creative).
        max_tokens:  Maximum tokens in the response.
        model:       Model string. If None (default), reads from
                     st.session_state["gemini_model"] so the sidebar
                     switcher controls all modules automatically.

    Returns:
        Generated text string.
    """
    # Resolve model: session state > explicit arg > hardcoded default
    if model is None:
        model = st.session_state.get("gemini_model", MODEL_DEFAULT)

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
        raise RuntimeError(f"Gemini API error ({model}): {str(e)}")
