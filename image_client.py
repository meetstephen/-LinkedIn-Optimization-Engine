"""
Image generation client with Stability AI as primary and Hugging Face as fallback.
Handles prompt engineering, API calls, base64 encoding, and graceful fallback.
"""
import requests
import base64
import io
import streamlit as st
from typing import Optional, Tuple
import time


# ─────────────────────────────────────────────
# PROMPT ENGINEERING
# ─────────────────────────────────────────────

STYLE_PRESETS = {
    "Corporate Professional": (
        "corporate professional photography style, clean office background, "
        "business attire, soft lighting, LinkedIn profile aesthetic, "
        "high resolution, photorealistic"
    ),
    "Modern Minimalist": (
        "minimalist design, flat illustration, clean white background, "
        "simple geometric shapes, modern color palette (blue, white, grey), "
        "professional infographic style, vector art"
    ),
    "Tech & Innovation": (
        "futuristic technology illustration, dark background with neon blue accents, "
        "digital network visualization, circuit patterns, modern tech aesthetic, "
        "professional and sleek"
    ),
    "Warm & Human": (
        "warm photography, natural light, candid professional moment, "
        "authentic human connection, storytelling visual, soft warm tones, "
        "documentary style photography"
    ),
    "Infographic / Data": (
        "clean infographic design, data visualization, charts and graphs, "
        "professional color scheme, white background, business report style, "
        "flat design icons, readable typography"
    ),
    "Sketch / Illustrated": (
        "hand-drawn sketch illustration, business concept drawing, "
        "black and white with subtle color accents, whiteboard drawing style, "
        "clean lines, professional illustration"
    ),
}


def build_image_prompt(post_content: str, style: str = "Modern Minimalist") -> str:
    """
    Converts LinkedIn post content into an optimized image generation prompt.
    
    Args:
        post_content: The LinkedIn post text to visualize.
        style: The visual style preset name.
    
    Returns:
        Engineered prompt string optimized for image generation.
    """
    # Truncate post for prompt safety
    excerpt = post_content[:300].strip()
    style_desc = STYLE_PRESETS.get(style, STYLE_PRESETS["Modern Minimalist"])

    prompt = (
        f"Professional LinkedIn visual for the following concept: {excerpt}. "
        f"Style: {style_desc}. "
        "Social media optimized, 1:1 aspect ratio, no text overlays, "
        "brand-safe, clean composition, high quality render. "
        "Avoid: faces, logos, explicit content, cluttered layouts."
    )
    return prompt


# ─────────────────────────────────────────────
# PRIMARY: STABILITY AI
# ─────────────────────────────────────────────

def generate_image_stability(
    prompt: str,
    api_key: str,
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Generate image using Stability AI SDXL API.
    
    Returns:
        (image_bytes, error_message)
    """
    if not api_key:
        return None, "Stability AI API key not provided."

    # Try SDXL first, fall back to SD 1.6
    endpoints = [
        ("stable-diffusion-xl-1024-v1-0", 1024, 1024),
        ("stable-diffusion-v1-6", 512, 512),
    ]

    for engine_id, w, h in endpoints:
        url = f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "text_prompts": [
                {"text": prompt, "weight": 1.0},
                {"text": "blurry, low quality, distorted, watermark, text, faces, nsfw", "weight": -1.0},
            ],
            "cfg_scale": 7,
            "height": h,
            "width": w,
            "steps": steps,
            "samples": 1,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                image_b64 = data["artifacts"][0]["base64"]
                image_bytes = base64.b64decode(image_b64)
                return image_bytes, None
            elif response.status_code == 404:
                # Engine not found, try next
                continue
            else:
                error = response.json().get("message", f"HTTP {response.status_code}")
                return None, f"Stability AI error: {error}"
        except requests.exceptions.Timeout:
            return None, "Stability AI request timed out."
        except Exception as e:
            return None, f"Stability AI exception: {str(e)}"

    return None, "All Stability AI engines unavailable."


# ─────────────────────────────────────────────
# FALLBACK: HUGGING FACE
# ─────────────────────────────────────────────

HF_MODELS = [
    "stabilityai/stable-diffusion-xl-base-1.0",
    "runwayml/stable-diffusion-v1-5",
    "CompVis/stable-diffusion-v1-4",
]


def generate_image_huggingface(
    prompt: str,
    api_key: str,
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Generate image using Hugging Face Inference API (fallback).
    
    Returns:
        (image_bytes, error_message)
    """
    if not api_key:
        return None, "Hugging Face API key not provided."

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": "blurry, low quality, distorted, watermark, nsfw",
            "num_inference_steps": 25,
            "guidance_scale": 7.5,
        },
        "options": {"wait_for_model": True},
    }

    for model in HF_MODELS:
        url = f"https://api-inference.huggingface.co/models/{model}"
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            if response.status_code == 200:
                # HF returns raw image bytes
                content_type = response.headers.get("content-type", "")
                if "image" in content_type:
                    return response.content, None
                else:
                    # Some models return JSON with base64
                    try:
                        data = response.json()
                        if isinstance(data, list) and len(data) > 0:
                            img_b64 = data[0].get("generated_image", "")
                            if img_b64:
                                return base64.b64decode(img_b64), None
                    except Exception:
                        pass
                    continue
            elif response.status_code == 503:
                # Model loading, wait and retry once
                time.sleep(10)
                retry = requests.post(url, json=payload, headers=headers, timeout=120)
                if retry.status_code == 200 and "image" in retry.headers.get("content-type", ""):
                    return retry.content, None
                continue
            else:
                continue
        except requests.exceptions.Timeout:
            continue
        except Exception:
            continue

    return None, "All Hugging Face models failed or unavailable."


# ─────────────────────────────────────────────
# MAIN ENTRY POINT: generate_image()
# ─────────────────────────────────────────────

def generate_image(
    post_content: str,
    style: str = "Modern Minimalist",
    stability_key: Optional[str] = None,
    hf_key: Optional[str] = None,
) -> Tuple[Optional[bytes], str, str]:
    """
    Main image generation function with automatic fallback.
    
    Flow:
        1. Build optimized prompt from post content + style
        2. Try Stability AI (primary)
        3. If fails → Try Hugging Face (fallback)
        4. Return image bytes, source used, and status message
    
    Returns:
        (image_bytes, source, status_message)
        source: "stability" | "huggingface" | "failed"
    """
    if not post_content.strip():
        return None, "failed", "Post content is empty. Please generate a post first."

    prompt = build_image_prompt(post_content, style)

    # ── ATTEMPT 1: Stability AI ──
    if stability_key:
        img_bytes, err = generate_image_stability(prompt, stability_key)
        if img_bytes:
            return img_bytes, "stability", "✅ Generated with Stability AI (SDXL)"
        else:
            st.warning(f"Stability AI failed: {err}. Switching to Hugging Face...")

    # ── ATTEMPT 2: Hugging Face ──
    if hf_key:
        img_bytes, err = generate_image_huggingface(prompt, hf_key)
        if img_bytes:
            return img_bytes, "huggingface", "✅ Generated with Hugging Face (fallback)"
        else:
            return None, "failed", f"Both APIs failed. Last error: {err}"

    return None, "failed", "No API keys provided. Please add Stability AI or Hugging Face API key in the sidebar."


def image_bytes_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to base64 string for display."""
    return base64.b64encode(image_bytes).decode("utf-8")
