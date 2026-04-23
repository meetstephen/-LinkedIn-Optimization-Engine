"""
Gemini API client wrapper for all text generation tasks.
"""
import google.generativeai as genai
import streamlit as st
from typing import Optional


def get_gemini_client():
    """Initialize and return Gemini client using API key from session state."""
    api_key = st.session_state.get("gemini_api_key", "")
    if not api_key:
        raise ValueError("Gemini API key not set. Please enter your API key in the sidebar.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def generate_text(prompt: str, temperature: float = 0.8, max_tokens: int = 2048) -> str:
    """
    Generate text using the Gemini model.
    
    Args:
        prompt: The input prompt for generation.
        temperature: Creativity level (0.0 = deterministic, 1.0 = creative).
        max_tokens: Maximum tokens in the response.
    
    Returns:
        Generated text string.
    """
    try:
        model = get_gemini_client()
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text
    except ValueError as e:
        raise e
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {str(e)}")
