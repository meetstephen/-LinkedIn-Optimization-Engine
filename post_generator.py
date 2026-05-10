"""
Post Generator Module — Generates high-performing LinkedIn posts
using proven content frameworks powered by Gemini.
"""
import html as _html
import streamlit as st
import streamlit.components.v1 as _components
from utils.gemini_client import generate_text, get_profile_context


# ── Unicode formatting helpers ─────────────────────────────────────────────
# LinkedIn strips all markdown. These convert text to Unicode Mathematical
# characters that survive copy-paste directly into a LinkedIn post.

def _to_bold(text: str) -> str:
    """Sans-Serif Bold: 𝗔𝗕𝗖 / 𝗮𝗯𝗰 / 𝟬𝟭𝟮"""
    out = []
    for ch in text:
        if   'A' <= ch <= 'Z': out.append(chr(0x1D5D4 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z': out.append(chr(0x1D5EE + ord(ch) - ord('a')))
        elif '0' <= ch <= '9': out.append(chr(0x1D7EC + ord(ch) - ord('0')))
        else:                  out.append(ch)
    return ''.join(out)


def _to_italic(text: str) -> str:
    """Sans-Serif Italic: 𝘈𝘉𝘊 / 𝘢𝘣𝘤"""
    out = []
    for ch in text:
        if   'A' <= ch <= 'Z': out.append(chr(0x1D608 + ord(ch) - ord('A')))
        elif 'a' <= ch <= 'z': out.append(chr(0x1D622 + ord(ch) - ord('a')))
        else:                  out.append(ch)
    return ''.join(out)


def _strip_fmt(text: str) -> str:
    """Remove Unicode bold/italic — restore plain ASCII."""
    out = []
    for ch in text:
        cp = ord(ch)
        if   0x1D5D4 <= cp <= 0x1D5ED: out.append(chr(ord('A') + cp - 0x1D5D4))
        elif 0x1D5EE <= cp <= 0x1D607: out.append(chr(ord('a') + cp - 0x1D5EE))
        elif 0x1D7EC <= cp <= 0x1D7F5: out.append(chr(ord('0') + cp - 0x1D7EC))
        elif 0x1D608 <= cp <= 0x1D621: out.append(chr(ord('A') + cp - 0x1D608))
        elif 0x1D622 <= cp <= 0x1D63B: out.append(chr(ord('a') + cp - 0x1D622))
        else:                          out.append(ch)
    return ''.join(out)


# ── LinkedIn preview renderer ──────────────────────────────────────────────
_SEE_MORE_CHARS = 210   # LinkedIn's approximate desktop feed cutoff

def _linkedin_preview_html(content: str, name: str, role: str) -> str:
    """
    Returns a self-contained HTML string that renders a realistic LinkedIn
    feed card — with the 210-char 'see more' cutoff clearly visualised.
    """
    total_chars = len(content)
    hook_visible = total_chars <= _SEE_MORE_CHARS

    # Split at cutoff, respecting word boundaries
    if hook_visible:
        visible_raw = content
        hidden_raw  = ""
    else:
        cut = content.rfind(' ', 0, _SEE_MORE_CHARS)
        cut = cut if cut > 0 else _SEE_MORE_CHARS
        visible_raw = content[:cut]
        hidden_raw  = content[cut:]

    def _fmt(text: str) -> str:
        """Escape HTML and convert newlines to <br>."""
        return _html.escape(text).replace('\n', '<br>')

    visible_html = _fmt(visible_raw)
    hidden_html  = _fmt(hidden_raw)

    # Char counter colour
    if total_chars > 3000:
        bar_color  = "#e63946"
        bar_label  = f"⚠️ {total_chars:,} / 3,000 — TOO LONG"
    elif total_chars > 2500:
        bar_color  = "#FF6B35"
        bar_label  = f"🟡 {total_chars:,} / 3,000 chars"
    else:
        bar_color  = "#00c851"
        bar_label  = f"✅ {total_chars:,} / 3,000 chars"

    bar_pct = min(total_chars / 3000 * 100, 100)

    # Hook badge
    if hook_visible:
        hook_badge = (
            '<span style="background:#d4edda;color:#155724;padding:3px 8px;'
            'border-radius:12px;font-size:11px;font-weight:600;">'
            '✅ Hook fully visible before "see more"</span>'
        )
    else:
        hook_badge = (
            '<span style="background:#fff3cd;color:#856404;padding:3px 8px;'
            'border-radius:12px;font-size:11px;font-weight:600;">'
            f'⚠️ Hook cut at {_SEE_MORE_CHARS} chars — shorten it for more impact</span>'
        )

    # Avatar initial
    initial = (name[0].upper() if name else "U")

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          background: #f3f2ef; padding: 12px; }}
  .card {{
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    overflow: hidden;
    max-width: 560px;
    margin: 0 auto;
    box-shadow: 0 1px 3px rgba(0,0,0,.08);
  }}
  .header {{
    display: flex; align-items: flex-start; gap: 10px;
    padding: 12px 16px 8px;
  }}
  .avatar {{
    width: 48px; height: 48px; border-radius: 50%;
    background: linear-gradient(135deg,#0A66C2,#004182);
    display: flex; align-items: center; justify-content: center;
    color: white; font-weight: 700; font-size: 20px;
    flex-shrink: 0;
  }}
  .meta {{ flex: 1; }}
  .name  {{ font-weight: 600; font-size: 14px; color: #191919; }}
  .conn  {{ color: #0A66C2; font-weight: 400; font-size: 13px; }}
  .role  {{ font-size: 12px; color: #666; margin-top: 1px; }}
  .time  {{ font-size: 12px; color: #666; margin-top: 1px; }}
  .body  {{ padding: 4px 16px 12px; font-size: 14px; line-height: 1.6; color: #191919; }}
  .cutoff-line {{
    display: block; margin: 6px 0 4px;
    border: none; border-top: 2px dashed #FF6B35;
    position: relative;
  }}
  .cutoff-label {{
    font-size: 10px; color: #FF6B35; font-weight: 700;
    letter-spacing: .5px; text-transform: uppercase;
    display: block; text-align: center; margin-bottom: 4px;
  }}
  .see-more {{ color: #0A66C2; font-weight: 600; cursor: pointer; font-size: 14px; }}
  .hidden-text {{ color: #555; }}
  .reactions {{
    border-top: 1px solid #e0e0e0;
    padding: 6px 16px;
    display: flex; gap: 4px; align-items: center;
    font-size: 12px; color: #666;
  }}
  .counter-bar-bg {{
    height: 4px; background: #eee; border-radius: 2px; margin: 6px 16px 0;
  }}
  .counter-bar-fill {{
    height: 4px; border-radius: 2px;
    background: {bar_color}; width: {bar_pct:.1f}%;
  }}
  .counter-label {{
    font-size: 11px; color: {bar_color}; font-weight: 600;
    text-align: right; padding: 2px 16px 8px;
  }}
  .badge-row {{ padding: 6px 16px 10px; }}
  .more-btn {{
    background: none; border: 1px solid #0A66C2; color: #0A66C2;
    border-radius: 4px; padding: 5px 16px; font-size: 14px;
    font-weight: 600; cursor: pointer; margin: 6px 16px 12px; display: block;
  }}
</style>
</head>
<body>
<div class="card">

  <!-- Header -->
  <div class="header">
    <div class="avatar">{initial}</div>
    <div class="meta">
      <div class="name">{_html.escape(name or "Your Name")} <span class="conn">• 1st</span></div>
      <div class="role">{_html.escape(role or "Your Role · Your Company")}</div>
      <div class="time">Just now · 🌐</div>
    </div>
    <div style="font-size:20px;color:#666;cursor:pointer;margin-left:auto;">···</div>
  </div>

  <!-- Character bar -->
  <div class="counter-bar-bg"><div class="counter-bar-fill"></div></div>
  <div class="counter-label">{bar_label}</div>

  <!-- Hook badge -->
  <div class="badge-row">{hook_badge}</div>

  <!-- Post body -->
  <div class="body">
    <span id="visible">{visible_html}</span>
    {'<hr class="cutoff-line"><span class="cutoff-label">── "see more" cutoff ──</span>' if not hook_visible else ''}
    {'<span class="hidden-text">' + hidden_html + '</span>' if hidden_html else ''}
    {'' if hook_visible else ''}
  </div>

  <!-- Fake "Follow" + reactions -->
  <div class="reactions">
    👍 ❤️ 💡 &nbsp;
    <span>Be the first to react</span>
    <span style="margin-left:auto;">· 0 comments</span>
  </div>

</div>
</body>
</html>
"""


TONE_DESCRIPTIONS = {
    "Inspirational":   "hopeful, grounded — a mentor talking to someone earlier in their journey",
    "Educational":     "clear, direct, generous — the smartest person in the room who never makes you feel dumb",
    "Storytelling":    "narrative-first, specific details, real tension — not a TED talk, a conversation",
    "Contrarian":      "calm confidence, not rage-bait — challenges assumptions without being arrogant",
    "Data-Driven":     "precise, crisp, lets the numbers do the talking — no fluff around the stats",
    "Conversational":  "like texting a smart friend — lowercase where natural, short sentences, real thoughts",
    "Motivational":    "honest energy, not toxic positivity — acknowledges the hard part before the push",
}

FRAMEWORK_DESCRIPTIONS = {
    "Hook → Story → Insight → CTA":  "Open mid-scene, tell what happened, extract the lesson, end with a question",
    "Problem → Agitation → Solution": "Name the pain clearly, make it feel real, offer a specific way out",
    "Listicle (Numbered Tips)":        "A number in the hook, tight actionable points, no padding",
    "Before → After → Bridge":        "Where you were, where you got to, the exact step that bridged the gap",
    "Contrarian Statement":            "One uncomfortable truth, defend it calmly, invite the pushback",
    "Personal Story Arc":              "Specific moment → what you felt → what you did → what you now know",
}

# Global voice rules injected into every post generation prompt
_VOICE_RULES = """
VOICE & STYLE RULES — follow these without exception:

1. BANNED WORDS & PHRASES — never write these:
   "game-changer", "game-changing", "dive in", "let's dive into", "in today's fast-paced world",
   "I'm excited to share", "I'm thrilled to announce", "leverage", "synergy", "actionable insights",
   "thought leader", "passionate about", "journey", "transformation", "crushing it",
   "hustle", "disrupt", "innovative", "cutting-edge", "best practices", "circle back",
   "touch base", "bandwidth", "move the needle", "at the end of the day", "it goes without saying",
   "needless to say", "in conclusion", "in summary", "I hope this finds you well"

2. HOOK RULES:
   - Never open with "I" as the first word
   - No questions as the hook (weak — everyone does it)
   - No emojis in the hook line
   - Must create a gap — reader has to keep going to close it
   - Under 12 words ideally

3. FORMATTING:
   - One idea per line
   - Blank line between every paragraph
   - Max 3 lines per paragraph
   - Never use bullet points with dashes (—) inside the post body
   - Numbered lists only when the number is part of the hook

4. SOUND HUMAN:
   - Incomplete sentences are fine if they hit harder that way
   - Use specifics: not "a lot of money" but "$47,000"
   - Not "many years" but "11 years"
   - Tension before resolution — don't rush to the lesson
   - One vulnerability moment per post minimum
   - Write like you're talking to one specific person, not an audience

5. CTA:
   - One question at the end, max
   - Must be genuinely curious, not a fake question
   - No "drop a comment below" or "hit the like button"
"""


def build_post_prompt(topic: str, niche: str, tone: str, framework: str, audience: str) -> str:
    tone_desc      = TONE_DESCRIPTIONS.get(tone, tone)
    framework_desc = FRAMEWORK_DESCRIPTIONS.get(framework, framework)
    profile_ctx    = get_profile_context()

    return f"""You write LinkedIn posts for a specific type of creator: someone who has real experience, has made real mistakes, and doesn't need to impress anyone. Their posts feel like they came from a person, not a content team.

WHAT YOU'RE WRITING:
- Topic: {topic}
- Niche: {niche}
- Audience: {audience}
- Tone: {tone} — {tone_desc}
- Framework: {framework} — {framework_desc}{profile_ctx}

Write 2 completely different post variations on this topic. Same message, different angle, different structure.

{_VOICE_RULES}

OUTPUT FORMAT — use exactly this, nothing else:

---VARIATION 1---
[The post. No label, no intro, just the post itself.]

---VARIATION 2---
[The post. Completely different structure from V1.]

---ANALYSIS---
Hook strength: [Strong/Medium/Weak] — [one specific sentence on why]
Which to post: [1 or 2] — [one specific sentence on why]
What to A/B test next time: [one specific thing]

Keep each post under 280 words. Every line should earn its place.
"""


def render_post_generator():
    st.header("🚀 LinkedIn Post Generator")
    st.markdown("Generate scroll-stopping posts using proven viral frameworks powered by Gemini AI.")

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_area(
            "📌 Topic / Main Idea",
            placeholder="e.g., 'I failed my first startup and learned these 3 lessons'",
            height=80,
        )
        niche = st.text_input(
            "🎯 Your Niche / Industry",
            value=st.session_state.get("pg_niche", _p.get("industry", "")),
            placeholder="e.g., Tech, Marketing, Finance, HR, Coaching",
            key="pg_niche",
        )
        audience = st.text_input(
            "👥 Target Audience",
            value=st.session_state.get("pg_audience", _p.get("audience", "") or "Professionals on LinkedIn"),
            placeholder="e.g., Early-career professionals, CTOs, Entrepreneurs",
            key="pg_audience",
        )

    with col2:
        tone = st.selectbox("🎭 Tone", list(TONE_DESCRIPTIONS.keys()))
        framework = st.selectbox("📐 Content Framework", list(FRAMEWORK_DESCRIPTIONS.keys()))
        st.info(f"**Framework:** {FRAMEWORK_DESCRIPTIONS[framework]}")

    st.markdown("---")

    if st.button("✨ Generate Post Variations", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a topic before generating.")
            return
        if not niche.strip():
            st.error("Please enter your niche/industry.")
            return

        with st.spinner("Writing your posts..."):
            try:
                prompt = build_post_prompt(topic, niche, tone, framework, audience)
                result = generate_text(prompt, temperature=0.88)

                # Parse and persist variations so pipeline buttons survive reruns
                var1 = var2 = analysis = ""
                parts = result.split("---")
                for part in parts:
                    part = part.strip()
                    if part.startswith("VARIATION 1"):
                        var1 = part.replace("VARIATION 1", "").strip()
                    elif part.startswith("VARIATION 2"):
                        var2 = part.replace("VARIATION 2", "").strip()
                    elif part.startswith("ANALYSIS"):
                        analysis = part.replace("ANALYSIS", "").strip()

                st.session_state["pg_var1"]     = var1
                st.session_state["pg_var2"]     = var2
                st.session_state["pg_analysis"] = analysis
                st.session_state["last_generated_post"] = result

            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

    # ── Persistent output — renders after generation and survives button reruns ──
    var1     = st.session_state.get("pg_var1", "")
    var2     = st.session_state.get("pg_var2", "")
    analysis = st.session_state.get("pg_analysis", "")

    if var1 or var2:
        st.success("✅ Posts generated!")
        st.markdown("---")
        st.subheader("📝 Your Post Variations")

        for idx, (label, content) in enumerate(
            [("Variation 1", var1), ("Variation 2", var2)], start=1
        ):
            if not content:
                continue
            with st.expander(f"📄 {label}", expanded=True):

                # ── Tabs: Raw text / Preview / Formatter ──────────────────
                _tab_raw, _tab_prev, _tab_fmt = st.tabs([
                    "📝 Post Text",
                    "📱 LinkedIn Preview",
                    "✏️ Unicode Formatter",
                ])

                with _tab_raw:
                    st.markdown(content)
                    _cc = len(content)
                    _cc_color = "#00c851" if _cc <= 3000 else "#e63946"
                    st.markdown(
                        f"<div style='font-size:0.75rem;color:{_cc_color};text-align:right;'>"
                        f"{_cc:,} / 3,000 chars</div>",
                        unsafe_allow_html=True,
                    )

                with _tab_prev:
                    _prf  = st.session_state.get("user_profile", {})
                    _name = _prf.get("name", "")
                    _role = _prf.get("role", "") or _prf.get("headline", "")
                    _html_card = _linkedin_preview_html(content, _name, _role)
                    _components.html(_html_card, height=520, scrolling=True)

                with _tab_fmt:
                    st.markdown(
                        "LinkedIn strips all markdown. These **Unicode characters** "
                        "survive copy-paste and render bold/italic directly in the feed."
                    )
                    st.markdown("---")

                    _fmt_scope = st.radio(
                        "Apply formatting to:",
                        ["Full post", "First line (hook) only", "Custom text"],
                        horizontal=True,
                        key=f"fmt_scope_{idx}",
                    )

                    if _fmt_scope == "Custom text":
                        _custom_input = st.text_input(
                            "Type the word or phrase to format",
                            placeholder="e.g., 3 things I wish I knew",
                            key=f"fmt_custom_{idx}",
                        )
                        _fmt_source = _custom_input
                    elif _fmt_scope == "First line (hook) only":
                        _fmt_source = content.split('\n')[0].strip()
                        st.caption(f"Hook detected: *\"{_fmt_source[:80]}{'…' if len(_fmt_source) > 80 else ''}\"*")
                    else:
                        _fmt_source = content

                    _fc1, _fc2, _fc3 = st.columns(3)
                    with _fc1:
                        _do_bold   = st.button("𝗕 Bold",   key=f"bold_{idx}",   use_container_width=True)
                    with _fc2:
                        _do_italic = st.button("𝘐 Italic", key=f"italic_{idx}", use_container_width=True)
                    with _fc3:
                        _do_clear  = st.button("✕ Clear",  key=f"clear_{idx}",  use_container_width=True)

                    _fmt_result_key = f"fmt_result_{idx}"
                    if _do_bold   and _fmt_source: st.session_state[_fmt_result_key] = _to_bold(_fmt_source)
                    if _do_italic and _fmt_source: st.session_state[_fmt_result_key] = _to_italic(_fmt_source)
                    if _do_clear  and _fmt_source: st.session_state[_fmt_result_key] = _strip_fmt(_fmt_source)

                    _result = st.session_state.get(_fmt_result_key, "")
                    if _result:
                        st.markdown("**Result — copy and paste directly into LinkedIn:**")
                        st.code(_result, language=None)
                        st.caption(
                            "✅ These characters work on LinkedIn desktop & mobile. "
                            "Don't use normal **bold** markdown — LinkedIn will strip it."
                        )
                    else:
                        st.info("Select a scope, then click Bold or Italic to see the result.")

                # ── Pipeline buttons ───────────────────────────────────────
                st.markdown("**Send this post to:**")
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

                with btn_col1:
                    if st.button("📋 Copy Post", key=f"copy_v{idx}",
                                 use_container_width=True, help="Expand to copy text"):
                        st.code(content, language=None)

                with btn_col2:
                    if st.button("🔧 Optimize", key=f"opt_v{idx}",
                                 use_container_width=True, help="Send to Post Optimizer"):
                        st.session_state["po_content"]   = content
                        st.session_state["current_page"] = "🔧 Post Optimizer"
                        st.rerun()

                with btn_col3:
                    if st.button("🔥 Check Hook", key=f"hook_v{idx}",
                                 use_container_width=True, help="Send to Viral Hook Analyzer"):
                        st.session_state["hook_analyzer_input"] = content
                        st.session_state["current_page"]        = "🔥 Viral Hook Analyzer"
                        st.rerun()

                with btn_col4:
                    if st.button("🎨 Make Visual", key=f"img_v{idx}",
                                 use_container_width=True, help="Generate a LinkedIn image"):
                        st.session_state["ig_post_content"] = content[:500]
                        st.session_state["current_page"]    = "🎨 Image Generator"
                        st.rerun()

        if analysis:
            with st.expander("📊 AI Analysis", expanded=True):
                st.markdown(analysis)
