"""
Post Generator Module — Generates high-performing LinkedIn posts
using proven content frameworks powered by Gemini.
"""
import html as _html
import streamlit as st
import streamlit.components.v1 as _components
from gemini_client import generate_text, get_profile_context, stream_text
from industry_profiles import get_industry_voice_block
from library import save_post_to_library, bump_generated
from core.voice import (
    HUMAN_VOICE_PRIMER, BANNED, HUMAN_SIGNATURES, STRUCTURE_RULES,
    story_beats_block, STORY_BEATS_PLACEHOLDER,
)
from core import validator as _validator
from core import polish as _polish
from core.debug import stash_prompt, render_prompt_debug


# ── Re-roll knobs ────────────────────────────────────────────────────────────
# Hitting "Generate" twice in a row used to produce nearly-identical output
# because the temperature was pinned at 0.88. We track how many times the
# user has re-rolled the SAME (topic, niche, tone, framework) signature and
# escalate temperature each time. The signature resets the moment any of
# those four fields change so a fresh topic always starts from a calm 0.88.
_REGEN_TEMPS = [0.88, 0.95, 1.05, 1.15, 1.20]   # caps at 1.20 — beyond is gibberish
_DIFFERENT_ANGLE_TEMP = 1.00                    # warmer than first run, cooler than 3rd


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

def build_post_prompt(
    topic: str,
    niche: str,
    tone: str,
    framework: str,
    audience: str,
    story_beats: str = "",
    *,
    different_angle: bool = False,
    avoid_framework: str = "",
) -> str:
    """
    Compose the full Post Generator prompt.

    Parameters
    ----------
    different_angle : bool, default False
        When True, instruct the model to take a deliberately different angle
        from the previous generation — different opener, different structure,
        different emotional register. Used by the "🎲 Different Angle" button.
    avoid_framework : str
        Name of a framework the model should NOT default to (typically the
        framework used on the previous click). Lets the user keep generating
        until something genuinely distinct lands.
    """
    tone_desc        = TONE_DESCRIPTIONS.get(tone, tone)
    framework_desc   = FRAMEWORK_DESCRIPTIONS.get(framework, framework)
    profile_ctx      = get_profile_context()
    industry_voice   = get_industry_voice_block(niche)

    beats_block = story_beats_block(story_beats)

    # ── Anti-repetition cue — only injected when the caller asks for it
    # so a fresh topic gets a clean prompt without the "different from last
    # time" instruction polluting the model's planning.
    repetition_cue = ""
    if different_angle:
        repetition_cue = (
            "\n\n🎲 DIFFERENT ANGLE MODE — the user already saw one version of "
            "this post and wants something genuinely different. Do NOT reuse "
            "the same opening line type, the same structure, or the same "
            "emotional register as a typical first attempt. Pick the angle a "
            "different writer would have picked."
        )
    if avoid_framework and avoid_framework != framework:
        repetition_cue += (
            f"\n\nAvoid leaning on the **{avoid_framework}** framework — that "
            f"was the previous attempt's default. Use **{framework}** as the "
            f"primary structure here."
        )

    return f"""{HUMAN_VOICE_PRIMER}

You are writing for this specific person:
- Topic: {topic}
- Niche / Industry: {niche}
- Target Audience: {audience}
- Tone: {tone} — {tone_desc}
- Framework: {framework} — {framework_desc}{profile_ctx}
{beats_block}
{industry_voice}
{BANNED}
{HUMAN_SIGNATURES}
{STRUCTURE_RULES}{repetition_cue}

Write 2 COMPLETELY DIFFERENT post variations. Same message. Different angle. Different structure. Different hook.

CRITICAL — the two posts must differ in:
  • Hook type (bold claim vs. story opening vs. counterintuitive fact)
  • Structure (numbered list vs. narrative paragraphs vs. contrast format)
  • Emotional register (analytical vs. vulnerable vs. provocative)

OUTPUT FORMAT — use exactly this. Nothing before, nothing after:

---VARIATION 1---
[The post. No label, no intro, no "Here is variation 1:". Just the post.]

---VARIATION 2---
[The post. Structurally different from V1 — not just the same post reworded.]

---ANALYSIS---
Hook strength: [Strong/Medium/Weak] — [one specific reason, name the technique used]
Which to post: [1 or 2] — [one specific reason tied to the audience]
What to A/B test next time: [one specific, testable variable]

LinkedIn post length guide:
- Short post (high impact): 150-300 words — use for bold claims, confessions, contrast posts
- Medium post (storytelling): 300-500 words — use for narrative, before/after, lesson posts
- Long post (authority): 500-700 words — use for how-to, frameworks, detailed case studies
LinkedIn supports up to 3,000 characters (~500 words). Use as much space as the story needs.
Never pad. Never cut a story short because you're running out of room.
Every line must move the reader forward — but don't truncate the narrative to hit an arbitrary limit.
"""


def _next_framework(current: str) -> str:
    """
    Pick a framework that is *visibly* different from ``current`` so the
    "Different Angle" button actually changes the structure of the output.

    Strategy: walk the FRAMEWORK_DESCRIPTIONS dict and pick the next entry
    after the current one (wrapping around). Ordered list rather than random
    so successive clicks rotate through every framework deterministically —
    the user can keep clicking until something lands without re-seeing the
    same framework twice in a row.
    """
    keys = list(FRAMEWORK_DESCRIPTIONS.keys())
    if not keys:
        return current
    if current not in keys:
        return keys[0]
    idx = (keys.index(current) + 1) % len(keys)
    return keys[idx]


def _generation_signature(topic: str, niche: str, tone: str, framework: str) -> str:
    """
    Stable signature for "this is the same generation request as last time."
    When the signature changes (e.g. user edits the topic) we reset the regen
    counter so the next click starts at temperature 0.88 again.
    """
    import hashlib
    raw = "|".join([topic.strip(), niche.strip(), tone.strip(), framework.strip()])
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def render_post_generator():
    st.markdown("""
    <div class="main-header">
        <div class="v-badge">Scroll-Stopping Posts on Demand</div>
        <h1>🚀 LinkedIn Post Generator</h1>
        <p>Generate scroll-stopping posts using proven viral frameworks powered by Gemini AI.</p>
    </div>
    """, unsafe_allow_html=True)

    _p = st.session_state.get("user_profile", {})

    col1, col2 = st.columns(2)

    with col1:
        topic = st.text_area(
            "📌 Topic / Main Idea *",
            placeholder=(
                "Be specific — the more detail here, the better the output.\n\n"
                "e.g., 'I lost a ₦4M client because of one clause I didn't read in the contract. "
                "Here's what happened and what I do differently now.'"
            ),
            height=160,
            key="pg_topic",
        )
        niche = st.text_input(
            "🎯 Your Niche / Industry",
            value=st.session_state.get("pg_niche", _p.get("industry", "")),
            placeholder="e.g., Legal Practice, Fintech, Real Estate, Consulting",
            key="pg_niche",
        )
        audience = st.text_input(
            "👥 Target Audience",
            value=st.session_state.get("pg_audience", _p.get("audience", "") or "Professionals on LinkedIn"),
            placeholder="e.g., Nigerian founders, Lagos lawyers, HR managers",
            key="pg_audience",
        )

    with col2:
        tone = st.selectbox("🎭 Tone", list(TONE_DESCRIPTIONS.keys()))
        framework = st.selectbox("📐 Content Framework", list(FRAMEWORK_DESCRIPTIONS.keys()))
        st.info(f"**Framework:** {FRAMEWORK_DESCRIPTIONS[framework]}")

    # ── Story Beats — the specificity engine ─────────────────────────────────
    with st.expander("✍️ Story Beats — Optional, but this is what separates great posts from generic ones", expanded=False):
        st.markdown(
            "Drop raw details here: names (anonymised), numbers, dates, exact quotes, "
            "what went wrong, what you felt, what you learnt. "
            "The AI builds the post around these exact moments — this is the single biggest "
            "lever for making output sound like **you**, not a bot."
        )
        story_beats = st.text_area(
            "Raw story details",
            placeholder=(
                "e.g.:\n"
                "- Client was a Lagos construction firm, ₦80M contract\n"
                "- I spotted the error on a Tuesday at 11pm\n"
                "- My senior partner had reviewed the same doc and missed it too\n"
                "- We filed an emergency injunction at the Federal High Court Lagos next morning\n"
                "- Key lesson: check the arbitration clause — not just whether it exists, "
                "but which seat and governing law"
            ),
            height=160,
            key="pg_story_beats",
        )

    st.markdown("---")

    # ── Action row: main Generate button + Different-Angle re-roll ───────────
    # The two buttons are siblings, not nested, so a re-roll never re-runs the
    # primary click handler. ``st.button(...)`` returns True only on the click
    # that triggered this rerun — using each return value to gate behaviour.
    _gen_col, _angle_col = st.columns([2, 1])
    with _gen_col:
        _generate_clicked = st.button(
            "✨ Generate Post Variations",
            type="primary",
            use_container_width=True,
            key="pg_generate_btn",
        )
    with _angle_col:
        _has_prior = bool(st.session_state.get("pg_var1") or st.session_state.get("pg_var2"))
        _different_angle_clicked = st.button(
            "🎲 Different Angle",
            use_container_width=True,
            disabled=not _has_prior,
            help=(
                "Pick a different framework than the one you just used and "
                "force the model to take a structurally different angle. "
                "Generate at least once first."
                if not _has_prior else
                "Re-rolls with a different framework and a fresh angle so you "
                "don't get the same post twice."
            ),
            key="pg_different_angle_btn",
        )

    if _generate_clicked or _different_angle_clicked:
        _topic_val = st.session_state.get("pg_topic", "").strip()
        if not _topic_val:
            st.error("Please enter a topic before generating.")
            return
        if not st.session_state.get("pg_niche", "").strip():
            st.error("Please enter your niche/industry.")
            return

        # ── Decide WHICH framework + temperature to use this run ─────────────
        # On a normal "Generate" click we use the user's selected framework.
        # On "Different Angle" we deliberately rotate to the next framework and
        # also flip the prompt's "different_angle" flag so the model knows the
        # previous attempt is on the user's screen.
        if _different_angle_clicked:
            _last_framework = st.session_state.get("pg_last_framework", framework)
            _active_framework = _next_framework(_last_framework)
            _temperature      = _DIFFERENT_ANGLE_TEMP
            _different_angle  = True
            _avoid_framework  = _last_framework
        else:
            # Re-roll escalation: same signature → step up; new signature → reset.
            _signature  = _generation_signature(
                _topic_val,
                st.session_state.get("pg_niche", ""),
                tone, framework,
            )
            _prev_sig   = st.session_state.get("pg_last_signature", "")
            _regen_idx  = st.session_state.get("pg_regen_count", 0) if _signature == _prev_sig else 0
            _temperature = _REGEN_TEMPS[min(_regen_idx, len(_REGEN_TEMPS) - 1)]

            _active_framework = framework
            # On a fresh signature (first click for this topic) we don't want
            # the model thinking about a "previous angle" that didn't exist.
            _different_angle  = (_regen_idx > 0)
            _avoid_framework  = ""

            # Bump for next time
            st.session_state["pg_regen_count"]   = _regen_idx + 1
            st.session_state["pg_last_signature"] = _signature

        st.info(
            f"⚡ Streaming output — your post appears as it's written… "
            f"(framework: **{_active_framework}**, "
            f"temperature: **{_temperature:.2f}**)"
        )
        _stream_box = st.empty()
        try:
            import re as _re

            prompt = build_post_prompt(
                _topic_val,
                st.session_state.get("pg_niche", ""),
                tone,
                _active_framework,
                st.session_state.get("pg_audience", "Professionals on LinkedIn"),
                story_beats=st.session_state.get("pg_story_beats", ""),
                different_angle=_different_angle,
                avoid_framework=_avoid_framework,
            )

            # Stash for the debug expander before streaming so the user can
            # inspect even when generation errors mid-stream.
            stash_prompt(
                "post_generator", prompt,
                meta={
                    "model":           st.session_state.get("gemini_model", "gemini-2.5-flash"),
                    "temperature":     _temperature,
                    "framework":       _active_framework,
                    "tone":            tone,
                    "different_angle": _different_angle,
                    "avoid":           _avoid_framework or "—",
                },
            )

            # Stream into a placeholder — st.write_stream returns full text
            with _stream_box.container():
                result = st.write_stream(
                    stream_text(prompt, temperature=_temperature, max_tokens=8000)
                )

            # Parse the streamed result
            def _extract(pattern: str) -> str:
                m = _re.search(pattern, result, _re.DOTALL | _re.IGNORECASE)
                return m.group(1).strip() if m else ""

            var1     = _extract(r"-+\s*VARIATION\s*1\s*-+(.*?)(?=-+\s*VARIATION\s*2|-+\s*ANALYSIS|$)")
            var2     = _extract(r"-+\s*VARIATION\s*2\s*-+(.*?)(?=-+\s*ANALYSIS|$)")
            analysis = _extract(r"-+\s*ANALYSIS\s*-+(.*?)$")

            if not var1 and not var2:
                var1 = _extract(r"(?:variation\s*1[:\s]*)(.*?)(?=variation\s*2|analysis|$)")
                var2 = _extract(r"(?:variation\s*2[:\s]*)(.*?)(?=analysis|$)")

            if not var1 and result.strip():
                var1 = result.strip()

            # Clear the raw stream box — formatted cards render below
            _stream_box.empty()

            st.session_state["pg_var1"]     = var1
            st.session_state["pg_var2"]     = var2
            st.session_state["pg_analysis"] = analysis
            st.session_state["last_generated_post"] = result
            # Remember which framework was actually used so the next "Different
            # Angle" click rotates AWAY from it, not the user's currently
            # selected option.
            st.session_state["pg_last_framework"] = _active_framework
            # Bump generation counter exactly once per successful generation
            bump_generated()

        except Exception as e:
            st.error(f"Generation failed: {str(e)}")
            with st.expander("🔍 Error details"):
                import traceback as _tb
                st.code(_tb.format_exc())

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

                # ── Voice Validator badge — runs on every render ──────────
                _vs_report = _validator.validate_post(content)
                _validator.render_voice_score(_vs_report, key=f"vs_v{idx}")

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

                # ── Polish (two-pass) ──────────────────────────────────────
                _polish_key = f"pg_polished_v{idx}"
                _polish_report_key = f"pg_polish_report_v{idx}"
                _polished = st.session_state.get(_polish_key, "")

                p_col1, p_col2 = st.columns([1, 3])
                with p_col1:
                    if st.button(
                        "✨ Polish",
                        key=f"polish_v{idx}",
                        use_container_width=True,
                        help="Run a second pass: critique against voice rules, then rewrite. Costs ~2× tokens.",
                    ):
                        try:
                            with st.spinner("Polishing — second pass running…"):
                                gen, _orig_report = _polish.polish_stream(
                                    content,
                                    profile_ctx=get_profile_context(),
                                    industry_voice=get_industry_voice_block(
                                        st.session_state.get("pg_niche", "")
                                    ),
                                )
                                # Drain the generator into a single string
                                polished_text = "".join(list(gen))
                            st.session_state[_polish_key] = polished_text.strip()
                            st.session_state[_polish_report_key] = _orig_report
                            st.rerun()
                        except Exception as _e:
                            st.error(f"Polish failed: {_e}")
                with p_col2:
                    if _polished:
                        st.caption("✨ Polished version generated below")

                if _polished:
                    st.markdown("**✨ Polished version**")
                    st.markdown(
                        f"<div style='background:#F0FFF4;padding:1rem;border-radius:8px;"
                        f"border-left:4px solid #00c851;font-size:0.9rem;line-height:1.6;"
                        f"white-space:pre-wrap;'>{_html.escape(_polished)}</div>",
                        unsafe_allow_html=True,
                    )
                    _polished_report = _validator.validate_post(_polished)
                    _validator.render_voice_score(_polished_report, key=f"vs_polished_v{idx}")
                    pp_col1, pp_col2 = st.columns(2)
                    with pp_col1:
                        if st.button("📚 Save polished",
                                     key=f"save_polished_v{idx}",
                                     use_container_width=True):
                            ok, msg = save_post_to_library(
                                _polished, "🚀 Post Generator (Polished)",
                                tags=["generated", f"variation-{idx}", "polished"],
                            )
                            st.success(msg) if ok else st.warning(msg)
                    with pp_col2:
                        if st.button("✕ Discard polish",
                                     key=f"discard_polished_v{idx}",
                                     use_container_width=True):
                            st.session_state.pop(_polish_key, None)
                            st.session_state.pop(_polish_report_key, None)
                            st.rerun()

                # ── Pipeline buttons ───────────────────────────────────────
                # Labels kept short so all 5 buttons stay readable on tablets.
                # Each button's full intent lives in its `help` tooltip.
                st.markdown("**Send this post to:**")
                btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns(5)

                with btn_col1:
                    if st.button("📋 Copy", key=f"copy_v{idx}",
                                 use_container_width=True,
                                 help="Reveal the post text in a code box for one-click copy"):
                        st.code(content, language=None)

                with btn_col2:
                    if st.button("🔧 Optimize", key=f"opt_v{idx}",
                                 use_container_width=True,
                                 help="Open Post Optimizer with this post pre-filled"):
                        st.session_state["po_content_pipe"] = content  # pipe key, not widget key
                        st.session_state["po_handoff_note"] = (
                            f"Variation {idx} from Post Generator"
                        )
                        st.session_state["_pending_nav"]    = "🔧 Post Optimizer"
                        st.toast(f"Variation {idx} sent to Post Optimizer", icon="🔧")
                        st.rerun()

                with btn_col3:
                    if st.button("🔥 Hook", key=f"hook_v{idx}",
                                 use_container_width=True,
                                 help="Send to the Viral Hook Analyzer to score & rewrite the opening"):
                        st.session_state["hook_analyzer_input"] = content
                        st.session_state["_pending_nav"] = "🔥 Viral Hook Analyzer"
                        st.rerun()

                with btn_col4:
                    if st.button("🎨 Visual", key=f"img_v{idx}",
                                 use_container_width=True,
                                 help="Generate a LinkedIn image for this post"):
                        st.session_state["ig_post_content"] = content[:500]
                        st.session_state["_pending_nav"] = "🎨 Image Generator"
                        st.rerun()

                with btn_col5:
                    if st.button("📚 Save", key=f"save_v{idx}",
                                 use_container_width=True,
                                 help="Save this post to your Library"):
                        ok, msg = save_post_to_library(
                            content, "🚀 Post Generator",
                            tags=["generated", f"variation-{idx}"]
                        )
                        st.success(msg) if ok else st.warning(msg)

        if analysis:
            with st.expander("📊 AI Analysis", expanded=True):
                st.markdown(analysis)

        # ── Prompt debug expander — collapsed by default. Lets the user see
        # exactly what context Gemini got, so "why is the output ignoring my
        # industry?" becomes a self-serve diagnosis instead of a support
        # ticket. The expander silently no-ops when no prompt has been
        # stashed (e.g. on first page load).
        render_prompt_debug("post_generator")
