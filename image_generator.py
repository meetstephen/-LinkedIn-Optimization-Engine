"""
AI Image Generator Module — Stability AI primary + Hugging Face fallback.
Generates professional LinkedIn-style visuals from post content.
"""
import streamlit as st
from utils.image_client import (
    generate_image,
    build_image_prompt,
    STYLE_PRESETS,
    image_bytes_to_base64,
)
import io


def render_image_generator():
    """Renders the AI Image Generator tab UI."""
    st.header("🎨 AI Image Generator")
    st.markdown(
        "Generate professional LinkedIn visuals powered by Stability AI (SDXL) with Hugging Face as fallback."
    )

    # API Key status indicators
    stability_key = st.session_state.get("stability_api_key", "")
    hf_key = st.session_state.get("hf_api_key", "")

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
        st.error("❌ No image API keys configured. Please add at least one in the sidebar Settings.")
        return

    st.markdown("---")

    # Input section
    col1, col2 = st.columns([3, 2])

    with col1:
        post_content = st.text_area(
            "📝 LinkedIn Post Content (for auto-prompt generation)",
            value=st.session_state.get("last_generated_post", "")[:500] if st.session_state.get("last_generated_post") else "",
            placeholder="Paste your LinkedIn post here — AI will extract the key theme and create the perfect visual prompt.\n\nOr use the 'Custom Prompt' option to write your own.",
            height=150,
            help="The AI will analyze your post and generate an optimized image prompt.",
        )

    with col2:
        style = st.selectbox(
            "🎨 Visual Style",
            list(STYLE_PRESETS.keys()),
            help="Choose the aesthetic that best fits your brand and post content.",
        )
        st.caption(f"**Style details:** {STYLE_PRESETS[style][:100]}...")

        use_custom_prompt = st.checkbox("✏️ Use Custom Prompt Instead")
        if use_custom_prompt:
            custom_prompt = st.text_area(
                "Custom Prompt",
                placeholder="Describe your image in detail...\ne.g., 'A minimalist illustration of a professional climbing a data-driven mountain, flat design, blue tones'",
                height=100,
            )

    # Show auto-generated prompt preview
    if post_content.strip() and not use_custom_prompt:
        with st.expander("👁️ Preview Auto-Generated Image Prompt", expanded=False):
            preview_prompt = build_image_prompt(post_content, style)
            st.code(preview_prompt, language="text")
            st.caption("This prompt is automatically engineered for best results. You can enable 'Use Custom Prompt' to override.")

    st.markdown("---")

    # Generation options
    col_opt1, col_opt2, col_opt3 = st.columns(3)
    with col_opt1:
        num_images = st.selectbox("🖼️ Number of Images", [1, 2, 3], index=0)
    with col_opt2:
        quality = st.selectbox("⚙️ Quality Mode", ["Standard (Faster)", "High Quality (Slower)"])
    with col_opt3:
        steps = 20 if quality == "Standard (Faster)" else 35
        st.metric("Diffusion Steps", steps, help="More steps = better quality but slower")

    # Generate button
    generate_btn = st.button(
        "🎨 Generate LinkedIn Visual",
        type="primary",
        use_container_width=True,
        disabled=(not post_content.strip() and not (use_custom_prompt and custom_prompt.strip())),
    )

    if generate_btn:
        # Determine prompt source
        if use_custom_prompt and custom_prompt.strip():
            final_content = custom_prompt
            prompt_type = "custom"
        elif post_content.strip():
            final_content = post_content
            prompt_type = "auto"
        else:
            st.error("Please provide post content or a custom prompt.")
            return

        # Generate image(s)
        progress_bar = st.progress(0)
        status_text = st.empty()

        generated_images = []

        for i in range(num_images):
            status_text.text(f"Generating image {i+1}/{num_images}...")
            progress_bar.progress((i) / num_images)

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
                st.error(f"Unexpected error for image {i+1}: {str(e)}")

        progress_bar.progress(1.0)
        status_text.empty()
        progress_bar.empty()

        # Display generated images
        if generated_images:
            st.success(f"✅ {len(generated_images)} image(s) generated!")

            if len(generated_images) == 1:
                img_bytes, source, message = generated_images[0]
                st.markdown(f"**Source:** {message}")

                # Display image
                st.image(img_bytes, caption=f"LinkedIn Visual — {style}", use_column_width=True)

                # Download button
                st.download_button(
                    label="📥 Download Image",
                    data=img_bytes,
                    file_name=f"linkedin_visual_{style.replace(' ','_').lower()}.png",
                    mime="image/png",
                    use_container_width=True,
                )

            else:
                # Multiple images in grid
                cols = st.columns(len(generated_images))
                for idx, (img_bytes, source, message) in enumerate(generated_images):
                    with cols[idx]:
                        st.markdown(f"**Image {idx+1}**")
                        st.image(img_bytes, caption=f"Variation {idx+1}", use_column_width=True)
                        st.download_button(
                            label=f"📥 Download {idx+1}",
                            data=img_bytes,
                            file_name=f"linkedin_visual_{idx+1}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"dl_{idx}",
                        )

        # Tips section
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
- Match your **personal brand colors**
- Professional images get **3× more profile views**
- Abstract/conceptual images often outperform stock-photo style

**⚡ Prompt Tips for Better Results:**
- Be specific about style: "flat design illustration" > "image"
- Specify what to AVOID in your prompt (faces, text, clutter)
- Professional color keywords: "navy blue and white", "muted earth tones"
- Composition keywords: "centered subject", "rule of thirds", "negative space"
            """)
