"""
Post Generator Module — Generates high-performing LinkedIn posts
using proven content frameworks powered by Gemini.
"""
import html as _html
import streamlit as st
import streamlit.components.v1 as _components
from gemini_client import generate_text, get_profile_context
from industry_profiles import get_industry_voice_block
from library import save_post_to_library


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

# ── Banned phrases — injected into every generation prompt ─────────────────
_BANNED_PHRASES = """
BANNED WORDS & PHRASES — writing any of these means the post fails:
  "game-changer", "game-changing", "dive in", "let's dive in", "let's dive into",
  "let's unpack", "unpack this", "leverage", "synergy", "actionable", "actionable insights",
  "thought leader", "passionate about", "journey", "transformation", "transformative",
  "crushing it", "hustle", "hustle culture", "grind", "disrupt", "disruption",
  "innovative", "cutting-edge", "best practices",
  "I'm excited to share", "I'm thrilled to announce", "I'm proud to share",
  "in today's fast-paced world", "in today's digital landscape", "in today's world",
  "at the end of the day", "needless to say", "it goes without saying",
  "in conclusion", "in summary", "circle back", "touch base",
  "bandwidth", "move the needle", "reach out",
  "unlock", "unlock your potential", "level up", "skyrocket", "scale your",
  "deep dive", "masterclass", "playbook", "blueprint",
  "it's a marathon not a sprint", "fail forward", "embrace failure", "fail fast",
  "ecosystem" (used vaguely), "stakeholders", "deliverables", "key takeaways",
  "pro tip:", "hot take:", "this is your sign", "reminder:", "PSA:",
  "unpopular opinion:" (as opener), "I'll say what no one else will",
  "this changed everything", "changed my life", "I wish I knew this sooner",
  "the secret to", "you won't believe", "what nobody tells you",
  "period." / "full stop." (mic-drop endings), "we need to talk about",
  "value-add", "low-hanging fruit", "paradigm shift", "next level", "win-win"
"""

# ── Human writer signatures — what separates a real post from AI filler ─────
_HUMAN_SIGNATURES = """
HUMAN WRITER SIGNATURES — use at least 3 of these per post:

1. SPECIFIC NUMBERS: Not "a lot of money" → "₦2.4 million". Not "many years" → "7 years".
   Not "significant growth" → "31% in 90 days". If no real number, invent a plausible specific one.

2. SPECIFIC TIME STAMPS: "On a Wednesday in March..." / "By month 4..." /
   "Three weeks before the deadline..." — anchor the story in time.

3. SPECIFIC PLACES: Name the actual city, building, neighbourhood, court, ward, or market.
   Not "a client in Lagos" → "a client in Ikeja GRA".

4. DIALOGUE FRAGMENTS: One line of actual speech from a real moment.
   "The client said: 'We already signed it.'" — not paraphrased, said.

5. SELF-INTERRUPTION: Used once per post only.
   "And honestly?" / "Here's the thing." / "I mean that literally."

6. CONTRAST SENTENCES: After a long sentence, a very short one.
   "We had invested 14 months and ₦9 million. No one used it."

7. EARNED VULNERABILITY: One sentence admitting the writer was wrong or afraid.
   Not "failure is my teacher" → "I told my co-founder it would work. It didn't."

8. INDUSTRY-NATIVE PROOF: One reference only a real practitioner would make naturally —
   a specific regulation, case name, system, or internal term.
"""

# ── Voice rules: formatting and structure ────────────────────────────────────
_STRUCTURE_RULES = """
STRUCTURE & FORMATTING RULES:
HOOK: Never start with "I". No questions as hooks. No emojis in line 1.
  Create an information gap. Under 12 words.
BODY: One idea per line. Blank line between paragraphs. Max 3 lines per paragraph.
  No dashes as bullets. Numbered lists only when the number is in the hook.
CTA: One genuine question at the end — maximum.
  No "drop a comment below", "smash the like button", "share this if you agree".
"""


def build_post_prompt(
    topic: str,
    niche: str,
    tone: str,
    framework: str,
    audience: str,
    story_beats: str = "",
) -> str:
    tone_desc        = TONE_DESCRIPTIONS.get(tone, tone)
    framework_desc   = FRAMEWORK_DESCRIPTIONS.get(framework, framework)
    profile_ctx      = get_profile_context()
    industry_voice   = get_industry_voice_block(niche)

    beats_block = ""
    if story_beats.strip():
        beats_block = f"""
STORY BEATS — the writer has provided these raw details. Use them.
Do not ignore or paraphrase away the specifics. Build the post around these exact moments:
{story_beats.strip()}
"""

    return f"""You write LinkedIn posts for a specific type of creator: someone with real experience, real mistakes, and no need to impress anyone. Their posts feel like they came from a human being, not a content team.

You are writing for this specific person:
- Topic: {topic}
- Niche / Industry: {niche}
- Target Audience: {audience}
- Tone: {tone} — {tone_desc}
- Framework: {framework} — {framework_desc}{profile_ctx}
{beats_block}
{industry_voice}
{_BANNED_PHRASES}
{_HUMAN_SIGNATURES}
{_STRUCTURE_RULES}

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


def render_post_generator():
    st.header("🚀 LinkedIn Post Generator")
    st.markdown("Generate scroll-stopping posts using proven viral frameworks powered by Gemini AI.")

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

    if st.button("✨ Generate Post Variations", type="primary", use_container_width=True):
        _topic_val = st.session_state.get("pg_topic", "").strip()
        if not _topic_val:
            st.error("Please enter a topic before generating.")
            return
        if not st.session_state.get("pg_niche", "").strip():
            st.error("Please enter your niche/industry.")
            return

        with st.spinner("Writing your posts…"):
            try:
                import re as _re

                prompt = build_post_prompt(
                    _topic_val,
                    st.session_state.get("pg_niche", ""),
                    tone,
                    framework,
                    st.session_state.get("pg_audience", "Professionals on LinkedIn"),
                    story_beats=st.session_state.get("pg_story_beats", ""),
                )
                result = generate_text(prompt, temperature=0.88, max_tokens=8000)

                # ── Robust regex parser ────────────────────────────────────
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

                st.session_state["pg_var1"]     = var1
                st.session_state["pg_var2"]     = var2
                st.session_state["pg_analysis"] = analysis
                st.session_state["last_generated_post"] = result
                st.session_state["session_posts_generated"] = (
                    st.session_state.get("session_posts_generated", 0) + 1
                )

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
                btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns(5)

                with btn_col1:
                    if st.button("📋 Copy Post", key=f"copy_v{idx}",
                                 use_container_width=True, help="Expand to copy text"):
                        st.code(content, language=None)

                with btn_col2:
                    if st.button("🔧 Optimize", key=f"opt_v{idx}",
                                 use_container_width=True, help="Send to Post Optimizer"):
                        st.session_state["po_content_pipe"] = content  # pipe key, not widget key
                        st.session_state["_pending_nav"]    = "🔧 Post Optimizer"
                        st.rerun()

                with btn_col3:
                    if st.button("🔥 Check Hook", key=f"hook_v{idx}",
                                 use_container_width=True, help="Send to Viral Hook Analyzer"):
                        st.session_state["hook_analyzer_input"] = content
                        st.session_state["_pending_nav"] = "🔥 Viral Hook Analyzer"
                        st.rerun()

                with btn_col4:
                    if st.button("🎨 Make Visual", key=f"img_v{idx}",
                                 use_container_width=True, help="Generate a LinkedIn image"):
                        st.session_state["ig_post_content"] = content[:500]
                        st.session_state["_pending_nav"] = "🎨 Image Generator"
                        st.rerun()

                with btn_col5:
                    if st.button("📚 Save", key=f"save_v{idx}",
                                 use_container_width=True, help="Save to Post Library"):
                        ok, msg = save_post_to_library(
                            content, "🚀 Post Generator",
                            tags=["generated", f"variation-{idx}"]
                        )
                        st.success(msg) if ok else st.warning(msg)

        if analysis:
            with st.expander("📊 AI Analysis", expanded=True):
                st.markdown(analysis)
