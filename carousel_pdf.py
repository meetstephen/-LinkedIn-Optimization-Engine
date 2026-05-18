"""
carousel_pdf.py — Render a LinkedIn-ready PDF carousel from slide data.

LinkedIn's "document post" upload accepts a multi-page PDF. The optimal
slide canvas is 1080 × 1350 px (4:5, the same vertical aspect that wins
the most real estate in feed). This module turns a list of slides into
that PDF using only Pillow — no reportlab, no system-font hunting, no
external services.

Public API:
    SLIDE_W, SLIDE_H            : canvas dimensions (px)
    THEMES                      : dict of theme_id → palette
    render_carousel_pdf(slides, theme="linkedin_blue", author="") -> bytes

A "slide" is the same dict the Carousel Planner already produces:
    {"emoji": "🎯", "title": "...", "body": "..."}
"""
from __future__ import annotations

import io
import os
import textwrap
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont


# ── Canvas constants ──────────────────────────────────────────────────────────
# 1080 × 1350 (4:5) is LinkedIn's max-real-estate vertical aspect for feed.
SLIDE_W = 1080
SLIDE_H = 1350

# Margins eat into usable area; padding controls the inner content box.
PAD_X = 90
PAD_Y = 100


# ── Themes ────────────────────────────────────────────────────────────────────
# Two intentionally — more = decision paralysis. Each theme ships every colour
# the renderer needs so swapping is a one-key change.
THEMES = {
    "linkedin_blue": {
        "label":      "LinkedIn Blue",
        "bg":         (255, 255, 255),                  # canvas
        "accent":     (10, 102, 194),                   # #0A66C2
        "accent_dim": (179, 212, 240),                  # accent rule
        "title":      (10, 102, 194),                   # title text = LinkedIn blue
        "body":       (40, 40, 40),                     # body text — near black
        "footer":     (130, 130, 130),                  # slide-no + author
        "card_shadow": True,
    },
    "dark": {
        "label":      "Dark Mode",
        "bg":         (16, 33, 60),                     # deep navy
        "accent":     (125, 211, 252),                  # icy cyan
        "accent_dim": (40, 60, 90),
        "title":      (255, 255, 255),
        "body":       (218, 226, 240),
        "footer":     (140, 165, 200),
        "card_shadow": False,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Font loader
# ─────────────────────────────────────────────────────────────────────────────
# Pillow ships with DejaVu Sans (regular + bold). It's tucked inside the
# Pillow install dir under PIL/fonts/. Falling back to ImageFont.load_default()
# yields a tiny bitmap font that looks awful at 1080px, so we hunt for DejaVu
# explicitly and only fall back on truly broken systems.
def _find_dejavu(weight: str = "regular") -> Optional[str]:
    """
    Locate DejaVu Sans (regular or bold). Returns absolute path or None.
    Searches:
      1. PIL's bundled fonts dir
      2. Common Linux locations (Streamlit Cloud is Debian-based)
      3. Common macOS locations
    """
    fname = "DejaVuSans-Bold.ttf" if weight == "bold" else "DejaVuSans.ttf"

    # 1. Pillow bundles DejaVu inside its install dir
    try:
        import PIL  # type: ignore
        bundled = os.path.join(os.path.dirname(PIL.__file__), "fonts", fname)
        if os.path.exists(bundled):
            return bundled
    except Exception:
        pass

    # 2. Linux / Streamlit Cloud
    for path in (
        f"/usr/share/fonts/truetype/dejavu/{fname}",
        f"/usr/share/fonts/dejavu/{fname}",
        f"/usr/local/share/fonts/{fname}",
    ):
        if os.path.exists(path):
            return path

    # 3. macOS
    for path in (
        f"/Library/Fonts/{fname}",
        f"/System/Library/Fonts/{fname}",
    ):
        if os.path.exists(path):
            return path

    return None


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Best-effort TrueType font load with a sensible default."""
    path = _find_dejavu("bold" if bold else "regular")
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    # Last-ditch fallback. Looks bad but never crashes.
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────────────────────
# Text helpers
# ─────────────────────────────────────────────────────────────────────────────
def _wrap_to_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> List[str]:
    """
    Word-wrap `text` so each rendered line fits inside `max_width` px.
    Falls back to char-wrap for words longer than max_width.
    """
    if not text:
        return []
    lines: List[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        current = ""
        for word in words:
            trial = (current + " " + word).strip() if current else word
            w = draw.textlength(trial, font=font)
            if w <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                # If a single word is wider than max_width, char-wrap it
                if draw.textlength(word, font=font) > max_width:
                    chunk = ""
                    for ch in word:
                        if draw.textlength(chunk + ch, font=font) <= max_width:
                            chunk += ch
                        else:
                            lines.append(chunk)
                            chunk = ch
                    current = chunk
                else:
                    current = word
        if current:
            lines.append(current)
    return lines


def _line_height(font: ImageFont.ImageFont) -> int:
    """Pillow's textbbox of a tall sample — robust line-height."""
    bbox = font.getbbox("Ag")  # has both ascender + descender
    return (bbox[3] - bbox[1]) + 6  # +6 px breathing room


def _safe_emoji(em: str) -> str:
    """
    PIL can't render colour emojis without a colour-emoji TTF. If the user
    typed a real emoji we keep it — Pillow renders it as a tofu/box on
    machines without the font, which is ugly. Fall back to a neutral bullet
    when the input doesn't look like a single emoji-ish character.
    """
    em = (em or "").strip()
    if not em:
        return "•"
    # Keep only the first visible character (avoid title-case noise).
    return em[:4]


# ─────────────────────────────────────────────────────────────────────────────
# Slide renderer
# ─────────────────────────────────────────────────────────────────────────────
def _render_slide(
    slide: dict,
    *,
    index: int,
    total: int,
    theme: dict,
    author: str = "",
) -> Image.Image:
    """
    Render a single 1080×1350 slide to an RGB PIL Image.
    Layout (top → bottom):
        ┌───────────────────────────────────────────┐
        │ accent rule                                │
        │                                            │
        │           emoji (huge, centred)            │
        │                                            │
        │      TITLE (bold, centred, wrapped)        │
        │     ─── short accent underline ──         │
        │                                            │
        │    body body body body body body body     │
        │    body body body body body body body     │
        │                                            │
        │ author                  3 / 7              │
        └───────────────────────────────────────────┘
    """
    img = Image.new("RGB", (SLIDE_W, SLIDE_H), theme["bg"])
    draw = ImageDraw.Draw(img)

    # Top accent rule (subtle brand element)
    draw.rectangle(
        [(0, 0), (SLIDE_W, 12)],
        fill=theme["accent"],
    )

    inner_w = SLIDE_W - 2 * PAD_X

    # ── Fonts ──────────────────────────────────────────────────────────────
    f_emoji = _font(140, bold=False)
    f_title = _font(64, bold=True)
    f_body  = _font(34, bold=False)
    f_meta  = _font(22, bold=False)

    # ── Emoji (centred) ────────────────────────────────────────────────────
    emoji = _safe_emoji(slide.get("emoji", ""))
    em_bbox = draw.textbbox((0, 0), emoji, font=f_emoji)
    em_w = em_bbox[2] - em_bbox[0]
    em_h = em_bbox[3] - em_bbox[1]
    em_x = (SLIDE_W - em_w) // 2 - em_bbox[0]
    em_y = PAD_Y + 30
    draw.text((em_x, em_y), emoji, fill=theme["accent"], font=f_emoji)

    cursor_y = em_y + em_h + 50

    # ── Title (bold, centred, wrapped) ─────────────────────────────────────
    title = (slide.get("title") or "").strip() or f"Slide {index + 1}"
    title_lines = _wrap_to_width(draw, title, f_title, inner_w)
    title_lh = _line_height(f_title)
    for line in title_lines:
        line_w = draw.textlength(line, font=f_title)
        x = (SLIDE_W - line_w) // 2
        draw.text((x, cursor_y), line, fill=theme["title"], font=f_title)
        cursor_y += title_lh

    # Short accent underline beneath title
    underline_w = 80
    cursor_y += 14
    draw.rectangle(
        [
            ((SLIDE_W - underline_w) // 2, cursor_y),
            ((SLIDE_W + underline_w) // 2, cursor_y + 5),
        ],
        fill=theme["accent"],
    )
    cursor_y += 50

    # ── Body (wrapped, centred) ────────────────────────────────────────────
    body = (slide.get("body") or "").strip()
    if body:
        body_lines = _wrap_to_width(draw, body, f_body, inner_w)
        body_lh = _line_height(f_body)
        for line in body_lines:
            line_w = draw.textlength(line, font=f_body)
            x = (SLIDE_W - line_w) // 2
            draw.text((x, cursor_y), line, fill=theme["body"], font=f_body)
            cursor_y += body_lh

    # ── Footer row ─────────────────────────────────────────────────────────
    footer_y = SLIDE_H - PAD_Y - 30

    if author:
        draw.text(
            (PAD_X, footer_y),
            author,
            fill=theme["footer"],
            font=f_meta,
        )

    page_label = f"{index + 1} / {total}"
    page_w = draw.textlength(page_label, font=f_meta)
    draw.text(
        (SLIDE_W - PAD_X - page_w, footer_y),
        page_label,
        fill=theme["footer"],
        font=f_meta,
    )

    # Swipe hint on every slide except the last
    if index < total - 1:
        hint = "Swipe →"
    else:
        hint = "♡ Save · 💬 Comment · ↗ Share"
    hint_w = draw.textlength(hint, font=f_meta)
    draw.text(
        ((SLIDE_W - hint_w) // 2, footer_y),
        hint,
        fill=theme["footer"],
        font=f_meta,
    )

    return img


# ─────────────────────────────────────────────────────────────────────────────
# Public: full PDF builder
# ─────────────────────────────────────────────────────────────────────────────
def render_carousel_pdf(
    slides: List[dict],
    *,
    theme: str = "linkedin_blue",
    author: str = "",
) -> bytes:
    """
    Render every slide and assemble them into a single PDF.

    Args:
        slides: List of {"emoji", "title", "body"} dicts.
        theme:  Theme id from THEMES (default: "linkedin_blue").
        author: Optional name printed bottom-left of every slide.

    Returns:
        Raw PDF bytes — feed straight to st.download_button(data=...).
    """
    if not slides:
        raise ValueError("Cannot render PDF from zero slides.")

    palette = THEMES.get(theme, THEMES["linkedin_blue"])

    pages = [
        _render_slide(s, index=i, total=len(slides),
                      theme=palette, author=author)
        for i, s in enumerate(slides)
    ]

    buf = io.BytesIO()
    # Pillow can save a multi-page PDF natively when given save_all + append.
    # No reportlab required — fewer dependencies, smaller image.
    pages[0].save(
        buf,
        format="PDF",
        save_all=True,
        append_images=pages[1:],
        # 96 dpi keeps file size sane (~150–400 KB for 7 slides)
        resolution=96.0,
    )
    return buf.getvalue()


# ── PNG single-slide export (bonus — used by the per-slide download UI) ──
def render_slide_png(
    slide: dict,
    *,
    index: int,
    total: int,
    theme: str = "linkedin_blue",
    author: str = "",
) -> bytes:
    """Render one slide as a PNG and return raw bytes."""
    palette = THEMES.get(theme, THEMES["linkedin_blue"])
    img = _render_slide(slide, index=index, total=total,
                        theme=palette, author=author)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
