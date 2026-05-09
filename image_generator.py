"""
AI Image Generator Module — Stability AI primary + Hugging Face fallback.

Imports from image_client are done lazily inside the render function using
importlib so this module never crashes at load time regardless of whether
utils.image_client prewarm has run or which version is on disk.
"""
import streamlit as st
import importlib.util
import sys
import os


def _load_image_client():
    """
    Load image_client.py safely at call time.
    Priority:
      1. Already in sys.modules as 'utils.image_client' (prewarm succeeded)
      2. Already in sys.modules as 'image_client'
      3. Direct file load from same directory as this file (always works)
    """
    for key in ("utils.image_client", "image_client"):
        if key in sys.modules:
            return sys.modules[key]

    here    = os.path.dirname(os.path.abspath(__file__))
    ic_path = os.path.join(here, "image_client.py")
    if not os.path.exists(ic_path):
        raise FileNotFoundError(
            f"image_client.py not found at {ic_path}. "
            "Make sure image_client.py is committed alongside app.py."
        )
    spec = importlib.util.spec_from_file_location("utils.image_client", ic_path)
    mod  = importlib.util.module_from_spec(spec)
    sys.modules["utils.image_client"] = mod
    sys.modules["image_client"]       = mod
    spec.loader.exec_module(mod)
    return mod


def render_image_generator():
    """Renders the AI Image Generator tab UI."""

    # Lazy safe import — works at any lifecycle point
    try:
        ic = _load_image_client()
        generate_image        = ic.generate_image
        build_image_prompt    = ic.build_image_prompt
        STYLE_PRESETS         = ic.STYLE_PRESETS
        image_bytes_to_base64 = ic.image_bytes_to_base64
    except Exception as e:
        st.error(
            f"Could not load the image generation engine: {e}\n\n"
            "Make sure `image_client.py` is committed to your GitHub repo "
            "alongside `app.py`."
        )
        return

    st.header("🎨 AI Image Generator")
    st.markdown(
        "Generate professional LinkedIn visuals powered by Stability AI (SDXL) "
        "with Hugging Face as fallback."
    )

    # ── API key status ─────────────────────────────────────────────────────
    stability_key = st.session_state.get("stability_api_key", "")
    hf_key        = st.session_state.get("hf_api_key", "")

    col_s, col_h = st.columns(2)
    with col_s:
        if stability_key:
            st.success("✅ Stability AI: Connected (Primary)")
        else:
            st.warning("⚠️ Stability AI: Not configured (add key in sidebar)")
    with col_h:
        if hf_key:
            st.success("✅ Hugging Face: Connected (Fallback)")
        else:
            st.info("ℹ️ Hugging Face: Not configured (fallback unavailable)")

    if not stability_key and not hf_key:
        st.error("❌ No image API keys configured. Add at least one in the sidebar.")
        return

    st.markdown("---")

    # ── Profile context ────────────────────────────────────────────────────
    _p          = st.session_state.get("user_profile", {})
    _industry   = _p.get("industry", "")
    _role       = _p.get("role", "")
    _audience   = _p.get("audience", "")

    # Profile banner — shows the user their images will be industry-tailored
    if _industry or _role:
        _profile_hint = " · ".join(filter(None, [_role, _industry]))
        st.info(
            f"🎯 **Profile active:** Images will be styled for **{_profile_hint}** "
            f"{'targeting ' + _audience if _audience else ''}. "
            "Style is pre-selected based on your industry."
        )

    # ── Industry → best style mapping ─────────────────────────────────────
    # Maps industry keywords to style preset keywords. Matches at runtime
    # against whatever STYLE_PRESETS keys are defined in image_client.py.
    _INDUSTRY_STYLE_MAP = {
        "tech": ["digital", "futuristic", "minimal", "abstract", "corporate"],
        "legal": ["corporate", "professional", "minimal", "clean", "formal"],
        "finance": ["corporate", "professional", "minimal", "clean", "abstract"],
        "marketing": ["creative", "vibrant", "bold", "colorful", "dynamic"],
        "healthcare": ["clean", "minimal", "professional", "calm", "soft"],
        "hr": ["warm", "people", "professional", "clean", "friendly"],
        "sales": ["bold", "dynamic", "vibrant", "energetic", "corporate"],
        "education": ["clean", "friendly", "bright", "minimal", "warm"],
        "creative": ["artistic", "vibrant", "bold", "abstract", "colorful"],
        "startup": ["modern", "bold", "dynamic", "minimal", "digital"],
        "consulting": ["professional", "corporate", "clean", "minimal", "formal"],
        "engineering": ["technical", "minimal", "clean", "digital", "abstract"],
    }

    def _best_style_for_industry(industry: str, style_keys: list) -> int:
        """Return index of the best matching style preset for the user's industry."""
        _ind_lower = industry.lower()
        _keywords  = []
        for _key, _words in _INDUSTRY_STYLE_MAP.items():
            if _key in _ind_lower:
                _keywords = _words
                break
        if not _keywords:
            return 0
        for _kw in _keywords:
            for _i, _sk in enumerate(style_keys):
                if _kw in _sk.lower():
                    return _i
        return 0

    _style_keys    = list(STYLE_PRESETS.keys())
    _style_default = _best_style_for_industry(_industry, _style_keys) if _industry else 0

    # ── Pipeline: pick the best available post content ─────────────────────
    # Priority: explicitly piped variation > last clean variation > raw last post
    _piped_content = (
        st.session_state.get("pg_var1")        # clean variation from Post Generator
        or st.session_state.get("last_generated_post", "")
    )
    # Trim to 500 chars — image_client only needs the theme, not the full post
    _piped_content = _piped_content[:500] if _piped_content else ""

    # ── Input section ──────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 2])

    with col1:
        post_content = st.text_area(
            "📝 LinkedIn Post Content",
            value=st.session_state.get("ig_post_content", _piped_content),
            placeholder=(
                "Paste your LinkedIn post here — AI extracts the key theme "
                "and builds the perfect visual prompt.\n\n"
                "Tip: Send a post directly from Post Generator using '🎨 Make Visual'."
            ),
            height=150,
            key="ig_post_content",
        )

        # Profile-enriched prompt hint
        if _industry and post_content.strip():
            _profile_suffix = (
                f", tailored for {_industry} professionals"
                + (f" targeting {_audience}" if _audience else "")
            )
            st.caption(
                f"💡 Profile context will enrich the image prompt with: "
                f"**{_profile_suffix.strip(', ')}**"
            )

    with col2:
        style = st.selectbox(
            "🎨 Visual Style",
            _style_keys,
            index=_style_default,
            help="Auto-selected based on your profile industry. Change any time.",
        )
        st.caption(f"**Style:** {STYLE_PRESETS[style][:100]}...")

        use_custom_prompt = st.checkbox("✏️ Use Custom Prompt Instead")
        custom_prompt = ""
        if use_custom_prompt:
            # Pre-seed custom prompt with profile context so the user
            # gets a relevant starting point rather than a blank box
            _custom_default = ""
            if _industry or _role:
                _custom_default = (
                    f"Professional LinkedIn visual for a {_role or _industry} "
                    f"{'in ' + _industry if _role and _industry else ''}. "
                    f"{'Audience: ' + _audience + '. ' if _audience else ''}"
                    "Style: "
                )
            custom_prompt = st.text_area(
                "Custom Prompt",
                value=_custom_default,
                placeholder="Describe your image in detail...",
                height=100,
            )

    # ── Auto-prompt preview ────────────────────────────────────────────────
    if post_content.strip() and not use_custom_prompt:
        with st.expander("👁️ Preview Auto-Generated Image Prompt", expanded=False):
            # Enrich the preview with profile context
            _enriched_content = post_content
            if _industry or _audience:
                _enriched_content += (
                    f"\n\n[Context: {_industry or ''}"
                    f"{' professional' if _industry else ''}"
                    f"{', audience: ' + _audience if _audience else ''}]"
                )
            st.code(build_image_prompt(_enriched_content, style), language="text")
            st.caption(
                "Profile context has been added to sharpen the prompt. "
                "Enable 'Use Custom Prompt' to fully override."
            )

    st.markdown("---")

    # ── Generation options ─────────────────────────────────────────────────
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    with col_opt1:
        num_images = st.selectbox("🖼️ Number of Images", [1, 2, 3], index=0)
    with col_opt2:
        quality = st.selectbox("⚙️ Quality Mode", ["Standard (Faster)", "High Quality (Slower)"])
    with col_opt3:
        steps = 20 if quality == "Standard (Faster)" else 35
        st.metric("Diffusion Steps", steps)

    generate_btn = st.button(
        "🎨 Generate LinkedIn Visual",
        type="primary",
        use_container_width=True,
        disabled=(
            not post_content.strip()
            and not (use_custom_prompt and custom_prompt.strip())
        ),
    )

    if generate_btn:
        final_content = (
            custom_prompt if (use_custom_prompt and custom_prompt.strip())
            else post_content
        )
        # Append profile context to enrich the image prompt
        if not use_custom_prompt and (_industry or _audience):
            final_content += (
                f"\n\n[Profile context: {_industry or ''}"
                f"{' professional' if _industry else ''}"
                f"{', audience: ' + _audience if _audience else ''}]"
            )
        if not final_content.strip():
            st.error("Please provide post content or a custom prompt.")
            return

        progress_bar     = st.progress(0)
        status_text      = st.empty()
        generated_images = []

        for i in range(num_images):
            status_text.text(f"Generating image {i + 1}/{num_images}…")
            progress_bar.progress(i / num_images)
            try:
                img_bytes, source, message = generate_image(
                    post_content=final_content,
                    style=style,
                    stability_key=stability_key,
                    hf_key=hf_key,
                )
                if img_bytes:
                    generated_images.append((img_bytes, source, message))
                else:
                    st.error(f"Image {i + 1} failed: {message}")
            except Exception as e:
                st.error(f"Unexpected error for image {i + 1}: {e}")

        progress_bar.progress(1.0)
        status_text.empty()
        progress_bar.empty()

        if generated_images:
            # Persist as base64 so images survive reruns without re-generating
            st.session_state["ig_generated"] = [
                {
                    "b64":     image_bytes_to_base64(img),
                    "bytes":   img,
                    "source":  src,
                    "message": msg,
                    "style":   style,
                }
                for img, src, msg in generated_images
            ]
            st.session_state["ig_style"] = style

    # ── Persistent output — always renders from session state ──────────────
    _saved = st.session_state.get("ig_generated", [])
    if _saved:
        _saved_style = st.session_state.get("ig_style", style)
        st.success(f"✅ {len(_saved)} image(s) generated!")

        if len(_saved) == 1:
            _img = _saved[0]
            st.markdown(f"**Source:** {_img['message']}")
            st.image(_img["bytes"], caption=f"LinkedIn Visual — {_saved_style}", use_column_width=True)
            st.download_button(
                "📥 Download Image",
                data=_img["bytes"],
                file_name=f"linkedin_visual_{_saved_style.replace(' ', '_').lower()}.png",
                mime="image/png",
                use_container_width=True,
                key="dl_single",
            )
        else:
            cols = st.columns(len(_saved))
            for idx, _img in enumerate(_saved):
                with cols[idx]:
                    st.markdown(f"**Image {idx + 1}**")
                    st.image(
                        _img["bytes"],
                        caption=f"Variation {idx + 1} — {_saved_style}",
                        use_column_width=True,
                    )
                    st.download_button(
                        f"📥 Download {idx + 1}",
                        data=_img["bytes"],
                        file_name=f"linkedin_visual_{idx + 1}_{_saved_style.replace(' ', '_').lower()}.png",
                        mime="image/png",
                        use_container_width=True,
                        key=f"dl_{idx}",
                    )

        # Clear button so user can start fresh
        if st.button("🔄 Generate New Images", key="ig_clear", use_container_width=False):
            del st.session_state["ig_generated"]
            st.rerun()

    st.markdown("---")
    with st.expander("💡 Tips for Better LinkedIn Visuals", expanded=False):
        st.markdown("""
**📐 Optimal LinkedIn Image Specs:**
- **Square posts**: 1200 × 1200px (1:1) — Best for feed
- **Landscape**: 1200 × 627px (1.91:1) — Standard link preview
- **Portrait**: 1080 × 1350px (4:5) — More screen space

**🎨 Design Best Practices:**
- Use **minimal text** on images (LinkedIn isn't Instagram)
- Ensure **high contrast** for accessibility
- Professional images get **3× more profile views**
- Abstract/conceptual images often outperform stock-photo style

**⚡ Prompt Tips:**
- Be specific: "flat design illustration" beats "image"
- Specify what to avoid: faces, text, clutter
- Try colour keywords: "navy blue and white", "muted earth tones"
- Composition keywords: "centered subject", "negative space"
        """)
