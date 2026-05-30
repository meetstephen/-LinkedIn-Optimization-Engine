# ⚡ LinkedEdge — LinkedIn Optimization Engine

> **AI-powered LinkedIn growth toolkit.** 17 modules. Built for the Nigerian professional market and configurable for any audience worldwide.
>
> Human-quality output powered by few-shot example calibration, voice fingerprinting, and a deterministic quality gate. Every post sounds like a real person wrote it - not AI.
>
> Every post auto-saves to a persistent Post Library. Every AI module reads your profile and writes in your voice. Production-ready Streamlit app, deploys in minutes.

---

## What's inside

| # | Module | What it does |
|---|--------|-------------|
| 1 | 🔥 **Viral Hook Analyzer** | Scores any hook 0–100 across 5 dimensions, returns 5 power rewrites + live mobile preview |
| 2 | 🚀 **Post Generator** | One focused, high-quality post per generation. Few-shot example calibration, story-beats input, engagement prediction score, Unicode formatter, live LinkedIn feed preview, **optional live-web research backing**, and direct-to-scheduler pipeline |
| 3 | 🔎 **Trend Researcher** | Goes online via Gemini's Google Search grounding to find how top-performing LinkedIn posts in your niche are written *right now* — current hooks, formats, what's getting reach — with real source links. Pipes findings straight into the Post Generator |
| 4 | 🔧 **Post Optimizer** | Diagnoses an existing post (hook · clarity · emotional pull · formatting · CTA), assigns a score, rewrites it with 5 explained edits |
| 5 | ♻️ **Repurposing Engine** | One idea → text post + 7-slide carousel + 5 hooks + 5 CTAs + 3 strategic comments |
| 6 | 💬 **Engagement Intelligence** | Strategic comments, DM templates, and networking responses — three generators in one |
| 7 | 🔍 **Brand Scanner** | Compares what your profile claims vs. what your content proves; scores the gap; gives a 5-day fix |
| 8 | 💼 **About Optimizer** | 3-paragraph About section rewrite + 3 headline options + before/after + key improvements |
| 9 | 🌟 **Profile Enhancer** | Full profile audit (0–100), 30-day action plan, 3 quick wins under 20 min each |
| 10 | 💡 **Content Ideas** | Up to 20 ideas across selected pillars, with hooks, hashtags, and one "post this week" pick. **Optional live-web research** surfaces what's trending in your niche right now |
| 11 | 🧠 **Strategy Insights** | Creator playbook for your archetype: hooks, post blueprints, posting rhythm, 90-day roadmap. **Optional live-web research** grounds it in what the algorithm rewards now |
| 12 | 🎨 **Image Generator** | LinkedIn visuals via Stability AI SDXL (primary) → Hugging Face (fallback). Prompt auto-derived from your post |
| 13 | ⚡ **Engagement Toolkit** | Hooks, CTAs, hashtags, and WAT-aware posting times |
| 14 | 🎠 **Carousel Planner** | AI-generated slide titles + bodies + emojis with a slide-by-slide LinkedIn-style preview |
| 15 | 📚 **Post Library** | Persistent (Supabase). Search, star, filter by module, sort by score, export `.txt`/`.json`, re-import. Live diagnostics tell you exactly what's wrong if it's empty. |
| 16 | 📅 **Content Scheduler** | Pin saved posts to weekday + time slots. See your full week at a glance. Export as a `.md` checklist. |
| 17 | 🎙️ **Voice Fingerprint** | Analyses your writing sample once, extracts structured DNA (sentence length, signature phrases, structure, tells), injects into every prompt for on-voice output |

Plus:
- **🇳🇬 Nigerian Voice Mode** — Nigerian warmth is baked into the core voice natively. The sidebar toggle adds deeper context (CBN, NBA, naira, WAT times, geographic diversity beyond Lagos) into every prompt.
- **Tone presets** — fine-grained Nigerian voice (Legal, Fintech, Founder, Storyteller, etc.).
- **Profile-aware AI** — your role, industry, audience, voice sample, and structured voice fingerprint feed every module's prompt.
- **Few-shot example calibration** — every module injects 2-3 real high-performing post examples into the prompt so the AI knows what "good" looks like, not just what to avoid.
- **Engagement prediction** — deterministic 0-100 score after every generation evaluating hook strength, specificity, structure variety, and emotional pull.
- **Voice quality gate** — deterministic validator catches 156+ banned phrases, weak CTAs, and structural issues before you ever see the output.
- **Cross-module pipelines** — `Post Generator → Hook Analyzer`, `Post Generator → Content Scheduler`, `Optimizer → Image Generator`, `Repurposing → Carousel Planner`, and more.

---

## Quick start (5 minutes)

### 1. Clone and install

```bash
git clone https://github.com/meetstephen/-LinkedIn-Optimization-Engine.git
cd -LinkedIn-Optimization-Engine
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get API keys (all free tiers)

| Service | Why | Where |
|---------|-----|-------|
| **Gemini** (required) | Powers every text feature | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| **Stability AI** (optional) | Primary image engine | [platform.stability.ai](https://platform.stability.ai/account/keys) |
| **Hugging Face** (optional) | Image fallback | [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| **Supabase** (optional but recommended) | Persistent library + profile | [supabase.com](https://supabase.com) |

### 3. Configure

Pick **one** of these — easiest first:

**Option A — Streamlit secrets (recommended for deployment).** Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY    = "AIza..."
STABILITY_API_KEY = "sk-..."
HF_API_KEY        = "hf_..."
SUPABASE_URL      = "https://xxxxx.supabase.co"
SUPABASE_KEY      = "<your-anon-public-key>"
```

**Option B — `.env` file** (local dev). Copy `.env.example` to `.env` and fill in your keys.

**Option C — In-app sidebar.** Run the app and paste keys into the sidebar's **Configure API Keys** panel. Session-only.

### 4. Set up Supabase (for persistent library)

If you skip this, the Post Library still works — but only for the current browser session.

1. Create a free project at [supabase.com](https://supabase.com).
2. Open **SQL Editor → New query**.
3. Paste the entire contents of [`supabase_schema.sql`](./supabase_schema.sql) and click **Run**.
4. Copy `Project URL` and the `anon public` key from **Project Settings → API** into your secrets/env (above).

### 5. Run

```bash
streamlit run app.py
```

The app opens at <http://localhost:8501>.

---

## Deploy to Streamlit Cloud (free, public URL)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Pick the repo and set the main file to `app.py`.
4. Click **Advanced settings → Secrets** and paste the same TOML block from Option A above.
5. Deploy. Done.

> **Note on the WebSocket keep-alive:** the bundled `.streamlit/config.toml` raises `maxMessageSize` to 200 MB so long Gemini streams don't disconnect. The bundled GitHub Action in `.github/workflows/keep_alive.yml` pings the deployed URL daily so Streamlit Cloud doesn't sleep the app.

---

## Multi-user mode & Admin Console

LinkedEdge ships with built-in email + password authentication. Every signed-in user has their own isolated Post Library, Profile and Schedule — backed by Supabase, persistent across reboots.

### How it works
- The login/signup gateway is shown automatically when no one is logged in.
- Passwords are hashed with **bcrypt** (12 rounds) before being stored. Plaintext passwords are never written to the database.
- The authenticated user's UUID becomes the per-row `user_id` in `lb_posts`, `lb_profiles`, `lb_schedule`. Two users with the same Gemini key still see *only their own* posts.
- Every successful login, signup, logout and failed attempt is recorded in `lb_login_events` for audit.

### Access control & key safety (read before going public)
- **Sign-in is required by default.** Set `REQUIRE_AUTH=false` in env/secrets only for a personal single-user instance or a local demo — otherwise anonymous traffic could spend your shared API quota.
- **Your server-side API keys are never exposed to visitors.** If you set `GEMINI_API_KEY` (etc.) in secrets, the sidebar keeps it hidden — it is *not* rendered into the password field (Streamlit ships widget values to the browser, so a pre-filled field could be read via devtools). Visitors see a masked notice and may type their own key to override.
- For a public launch, either accept that signed-in users share your key/quota, or ask each user to bring their own key in the sidebar.

### Beta feedback (for test groups)
- Testers can send feedback any time from the sidebar **💬 Send Beta Feedback** widget (type, message, optional star rating). Each submission is tagged with the page they were on.
- Submissions land in Supabase (`lb_feedback`) and are visible to admins in the **Admin Console → 💬 Feedback** tab, grouped by type.
- Run the latest [`supabase_schema.sql`](./supabase_schema.sql) once so the `lb_feedback` table exists — the widget degrades gracefully with a friendly message until then.

### Bootstrap your first admin
1. Set `BOOTSTRAP_ADMIN_EMAIL` in your secrets/env to the email you want to use.
2. Sign up through the app's **Sign Up** tab using that exact email.
3. The new account is automatically promoted to admin and gains the **🛡️ Admin Console** entry in the sidebar.

You can also flip `is_admin` manually from the Supabase Table Editor (`lb_users` → `is_admin = true`).

### What the Admin Console shows
- **Live tiles**: total users, active users, admins, signups today, logins today / 7-day, total posts.
- **Users tab**: searchable user list with last login, login count, post count, status. Promote / demote, deactivate / reactivate, hard-delete (with 2-click confirm). Self-actions are disabled so you can't lock yourself out.
- **Recent Activity tab**: live feed of the last 100 login / signup / logout / failed-login events, filterable by event type.

> **Disabling auth for local dev.** If neither `lb_users` nor `bcrypt` are available, the app silently falls back to the legacy single-tenant mode (one shared library keyed by `SUPABASE_URL`). Re-enable auth by running the latest `supabase_schema.sql` migration and reinstalling `requirements.txt`.

---

## Project layout

```
.
├── app.py                       # Main router + Home, Hook Analyzer, Library, Carousel pages
│
├── core/                        # Shared infrastructure
│   ├── ai.py                    #   Central Gemini wrapper with retry + JSON validation
│   ├── db.py                    #   Supabase persistence (lb_posts + lb_profiles)
│   ├── examples.py              #   Few-shot post/hook/comment examples for prompt injection
│   ├── polish.py                #   Two-pass rewrite (critique → polish) for any post
│   ├── sanitize.py              #   User-input sanitisation against prompt injection
│   ├── state.py                 #   Session-state init + profile auto-load on cold start
│   ├── validator.py             #   Deterministic voice quality gate (156+ banned phrases)
│   ├── voice.py                 #   Canonical voice system (primer, banned, signatures, structure)
│   ├── web_research.py          #   🔎 Live web research via Gemini Google Search grounding
│   └── voice_fingerprint.py     #   One-time writing-sample analysis → structured DNA
│
├── library.py                   # Single source of truth for save-to-library
├── gemini_client.py             # Streaming Gemini wrapper used by per-module prompts
├── image_client.py              # Stability AI + Hugging Face image generation
├── industry_profiles.py         # Industry voice blocks + Nigerian tone presets
│
├── post_generator.py            # 🚀 Post Generator (single-post, few-shot calibrated)
├── post_optimizer.py            # 🔧 Post Optimizer
├── about_optimizer.py           # 💼 About Optimizer
├── profile_enhancer.py          # 🌟 Profile Enhancer
├── content_ideas.py             # 💡 Content Ideas
├── strategy_insights.py         # 🧠 Strategy Insights
├── image_generator.py           # 🎨 Image Generator
├── engagement_toolkit.py        # ⚡ Engagement Toolkit
├── engagement_intelligence.py   # 💬 Engagement Intelligence
├── repurposing_engine.py        # ♻️ Repurposing Engine
├── brand_scanner.py             # 🔍 Brand Scanner
├── carousel_pdf.py              # 🎠 PDF carousel renderer (Pillow-based)
│
├── tests/                       # pytest suite (87 tests)
├── supabase_schema.sql          # One-time DB migration
├── requirements.txt
├── .env.example
├── .streamlit/config.toml       # Theme + maxMessageSize for streaming
└── .github/workflows/keep_alive.yml
```

---

## How the persistence layer works

```
┌──────────────┐  generate ─►  ┌──────────────┐
│   Module     │               │ session_state│
│  (any of 14) │               │  *_last_*    │
└──────────────┘               └──────────────┘
       │                              │
       │ save click                   │ render persistent
       ▼                              ▼
┌──────────────┐              ┌──────────────┐
│ library.py   │── Supabase ─►│  lb_posts    │
│ save_post_to │   available? │  (persistent)│
│ _library     │── no ────────►│ session post_│
└──────────────┘                │ library    │
                                │  (fallback) │
                                └──────────────┘
```

Every module follows the same contract:

```python
from library import save_post_to_library, bump_generated

# After successful generation:
bump_generated()                          # +1 to "Posts Generated"
st.session_state["mod_last_result"] = r   # survives reruns

# On save click (rendered OUTSIDE the if-button block):
ok, msg = save_post_to_library(content, "🚀 Post Generator", tags=[...])
st.success(msg) if ok else st.warning(msg)
```

This is what enables save buttons to work after generation — clicking save no longer wipes the AI output.

---

## How the voice system works

```
┌────────────────────────────────────────────────────────────────────┐
│                        core/voice.py                                │
│  HUMAN_VOICE_PRIMER (189 words) + BANNED (156 phrases)            │
│  + HUMAN_SIGNATURES (8 types) + STRUCTURE_RULES                    │
└────────────────────────────────────────────────────────────────────┘
         │                           │                    │
         ▼                           ▼                    ▼
┌─────────────────┐    ┌──────────────────┐    ┌────────────────────┐
│  core/examples  │    │ core/validator   │    │ core/voice_finger- │
│  6 post examples│    │ deterministic    │    │ print.py           │
│  8 hook examples│    │ quality gate     │    │ structured DNA     │
│  4 comment ex.  │    │ runs AFTER gen   │    │ from user's sample │
└─────────────────┘    └──────────────────┘    └────────────────────┘
         │                           │                    │
         └───────────────────────────┴────────────────────┘
                                     │
                              Every AI prompt
                           (all 16 modules use
                            the same voice)
```

The voice system has three layers:

1. **Before generation** — `core/voice.py` constants + `core/examples.py` few-shot posts inject into every prompt. The user's voice fingerprint (if set) adds per-user calibration.
2. **After generation** — `core/validator.py` runs a deterministic check: banned phrases, hook structure, CTA quality. Score 0-100.
3. **Optional polish** — `core/polish.py` sends the draft + validator report back to Gemini for a tightening pass.

---

## How live web research works (`core/web_research.py`)

The **🔎 Trend Researcher** module and the Post Generator's **Research-backed** toggle both call `core/web_research.py`, which uses **Gemini's first-party Google Search tool** (`types.Tool(google_search=...)`). The model issues real search queries, reads current results, and grounds its answer in live web content — returning a scannable brief plus **real citation links**.

The same engine now backs four touchpoints, each with an opt-in **🔎 Research-backed (live web)** toggle:

- **Post Generator** — injects current hook/format patterns before writing.
- **Content Ideas** — surfaces what's trending in your niche *this week*.
- **Strategy Insights** — grounds the playbook in what the algorithm rewards now.
- **📬 Daily Content Brief (Home)** — a button-triggered, cached-per-day panel that researches timely angles for your niche; each topic is a one-click, research-backed draft straight into the Post Generator. This is the habit loop: open the app → see what's worth posting today → write it.

```
research_linkedin_strategy(topic, niche, audience)
        │
        ├─ grounding available?  ──► generate_content(tools=[GoogleSearch])
        │                              │  → grounded brief + source links
        │                              ▼
        └─ unavailable / error ──► generate_content (no tools)
                                       → best-practice brief, grounded=False
```

Design notes:

- **No scraping, no ToS risk.** It researches public *writing about* LinkedIn best practice — never LinkedIn member data or profiles.
- **Untrusted by default.** Everything the web returns is wrapped in `<<USER_WEB_RESEARCH_…>>` delimiters via `core/sanitize.py` with a trust reminder before it touches a generation prompt, so a poisoned search result can't hijack the model.
- **Graceful fallback.** If the installed SDK or model can't ground (old SDK, transient error), the call degrades to an ungrounded best-practice brief flagged `grounded=False`, so the feature never hard-fails.
- **Cached.** The Post Generator caches research for an hour per `(topic, niche, audience)` so re-rolling the same topic doesn't fire a fresh billable search every click.

> Requires `google-genai>=1.0.0` (bundled in `requirements.txt`). Works on the free Gemini tier.

---

## Counters (Home page stats)

| Counter | When it increments |
|---------|-------------------|
| `session_posts_generated` | Once per successful AI generation in any module |
| `session_posts_saved` | Once per **save** click (from `library.save_post_to_library`) |
| `session_posts_optimized` | Once per Post Optimizer run |
| `session_repurposed` | Once per Repurposing Engine run |
| `hooks_analyzed` | Once per Viral Hook Analyzer run |

Saving a post does **not** inflate `session_posts_generated`.

---

## Customising the app

| Want to | Edit |
|---------|------|
| Add a content framework | `post_generator.py` → `FRAMEWORK_DESCRIPTIONS` |
| Add an image style | `image_client.py` → `STYLE_PRESETS` |
| Add an industry's voice block | `industry_profiles.py` → `INDUSTRY_VOICES` |
| Add a Nigerian tone preset | `industry_profiles.py` → `NIGERIAN_TONE_PRESETS` |
| Change the default Gemini model | Sidebar → **🤖 Gemini Model**, or `core/state.py` defaults |
| Add a few-shot example | `core/examples.py` → `_EXAMPLES`, `_HOOK_EXAMPLES`, or `_COMMENT_EXAMPLES` |
| Add a banned phrase | `core/voice.py` → `BANNED` constant (validator picks it up automatically) |
| Change theme colours | `.streamlit/config.toml` |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ValueError: Gemini API key not set` | Open the sidebar → **Configure API Keys** and paste your Gemini key |
| Post Library shows "📭 empty" after saving | Run `supabase_schema.sql` in your Supabase SQL editor and re-deploy |
| Library says "Saved in-session only" | Supabase keys missing or `lb_posts` table not created — see step 4 above |
| Images fail to generate | Check Stability AI credit balance, then verify the HF key is set as a fallback |
| `429 Too many requests` from Gemini | Free tier is 60 req/min; switch to Gemini 2.5 Flash-Lite in the sidebar or wait a minute |
| App disconnects mid-stream on Streamlit Cloud | Confirm `.streamlit/config.toml` is committed (raises `maxMessageSize`) |

---

## Legal / ethics

- ✅ No LinkedIn scraping, no profile harvesting
- ✅ All output is AI-generated suggestion — users review before posting
- ✅ Industry references draw on publicly known regulators and best practice
- ❌ Not affiliated with LinkedIn or Microsoft

---

## Stack

Python 3.10+ · [Streamlit](https://streamlit.io) · [Google Gemini 2.5 Flash](https://aistudio.google.com) ·
[Stability AI SDXL](https://platform.stability.ai) · [Hugging Face](https://huggingface.co) ·
[Supabase](https://supabase.com) · [Pillow](https://python-pillow.org) (carousel PDF)
