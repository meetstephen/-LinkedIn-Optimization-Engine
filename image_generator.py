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

    col1, col2 = st.columns([3, 2])
    with col1:
        post_content = st.text_area(
            "📝 LinkedIn Post Content (for auto-prompt generation)",
            value=(
                st.session_state.get("last_generated_post", "")[:500]
                if st.session_state.get("last_generated_post") else ""
            ),
            placeholder=(
                "Paste your LinkedIn post here — AI will extract the key theme "
                "and create the perfect visual prompt.\n\n"
                "Or use 'Custom Prompt' to write your own."
            ),
            height=150,
        )

    with col2:
        style = st.selectbox(
            "🎨 Visual Style",
            list(STYLE_PRESETS.keys()),
        )
        st.caption(f"**Style:** {STYLE_PRESETS[style][:100]}...")
        use_custom_prompt = st.checkbox("✏️ Use Custom Prompt Instead")
        custom_prompt = ""
        if use_custom_prompt:
            custom_prompt = st.text_area(
                "Custom Prompt",
                placeholder="Describe your image in detail...",
                height=100,
            )

    if post_content.strip() and not use_custom_prompt:
        with st.expander("👁️ Preview Auto-Generated Image Prompt", expanded=False):
            st.code(build_image_prompt(post_content, style), language="text")
            st.caption("Enable 'Use Custom Prompt' to override.")

    st.markdown("---")

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
        if not final_content.strip():
            st.error("Please provide post content or a custom prompt.")
            return

        progress_bar     = st.progress(0)
        status_text      = st.empty()
        generated_images = []

        for i in range(num_images):
            status_text.text(f"Generating image {i+1}/{num_images}...")
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
                    st.error(f"Image {i+1} failed: {message}")
            except Exception as e:
                st.error(f"Unexpected error for image {i+1}: {e}")

        progress_bar.progress(1.0)
        status_text.empty()
        progress_bar.empty()

        if generated_images:
            st.success(f"✅ {len(generated_images)} image(s) generated!")

            if len(generated_images) == 1:
                img_bytes, _, message = generated_images[0]
                st.markdown(f"**Source:** {message}")
                st.image(img_bytes, caption=f"LinkedIn Visual — {style}", use_column_width=True)
                st.download_button(
                    "📥 Download Image",
                    data=img_bytes,
                    file_name=f"linkedin_visual_{style.replace(' ','_').lower()}.png",
                    mime="image/png",
                    use_container_width=True,
                )
            else:
                cols = st.columns(len(generated_images))
                for idx, (img_bytes, _, message) in enumerate(generated_images):
                    with cols[idx]:
                        st.markdown(f"**Image {idx+1}**")
                        st.image(img_bytes, caption=f"Variation {idx+1}", use_column_width=True)
                        st.download_button(
                            f"📥 Download {idx+1}",
                            data=img_bytes,
                            file_name=f"linkedin_visual_{idx+1}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"dl_{idx}",
                        )

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
