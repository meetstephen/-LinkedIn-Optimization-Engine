# ⚡ LinkedEdge — LinkedIn Optimization Engine

> **AI-powered LinkedIn growth toolkit.** 14 modules. Built for the Nigerian professional market and configurable for any audience worldwide.
>
> Every post auto-saves to a persistent Post Library. Every AI module reads your profile and writes in your voice. Production-ready Streamlit app, deploys in minutes.

---

## What's inside

| # | Module | What it does |
|---|--------|-------------|
| 1 | 🔥 **Viral Hook Analyzer** | Scores any hook 0–100 across 5 dimensions, returns 5 power rewrites + live mobile preview |
| 2 | 🚀 **Post Generator** | Two complete post variations from any topic, with story-beats input, Unicode bold/italic formatter, and live LinkedIn feed preview |
| 3 | 🔧 **Post Optimizer** | Diagnoses an existing post (hook · clarity · emotional pull · formatting · CTA), assigns a score, rewrites it with 5 explained edits |
| 4 | ♻️ **Repurposing Engine** | One idea → text post + 7-slide carousel + 5 hooks + 5 CTAs + 3 strategic comments |
| 5 | 💬 **Engagement Intelligence** | Strategic comments, DM templates, and networking responses — three generators in one |
| 6 | 🔍 **Brand Scanner** | Compares what your profile claims vs. what your content proves; scores the gap; gives a 5-day fix |
| 7 | 💼 **About Optimizer** | 3-paragraph About section rewrite + 3 headline options + before/after + key improvements |
| 8 | 🌟 **Profile Enhancer** | Full profile audit (0–100), 30-day action plan, 3 quick wins under 20 min each |
| 9 | 💡 **Content Ideas** | Up to 20 ideas across selected pillars, with hooks, hashtags, and one "post this week" pick |
| 10 | 🧠 **Strategy Insights** | Creator playbook for your archetype: hooks, post blueprints, posting rhythm, 90-day roadmap |
| 11 | 🎨 **Image Generator** | LinkedIn visuals via Stability AI SDXL (primary) → Hugging Face (fallback). Prompt auto-derived from your post |
| 12 | ⚡ **Engagement Toolkit** | Hooks, CTAs, hashtags, and WAT-aware posting times |
| 13 | 🎠 **Carousel Planner** | AI-generated slide titles + bodies + emojis with a slide-by-slide LinkedIn-style preview |
| 14 | 📚 **Post Library** | Persistent (Supabase). Search, star, filter by module, sort by score, export `.txt`/`.json`, re-import |

Plus:
- **🇳🇬 Nigerian Voice Mode** — a sidebar toggle that injects Nigerian context (CBN, NBA, naira, WAT times, geographic diversity beyond Lagos) into every prompt.
- **Tone presets** — fine-grained Nigerian voice (Legal, Fintech, Founder, Storyteller, etc.).
- **Profile-aware AI** — your role, industry, audience, voice sample feed every module's prompt.
- **Cross-module pipelines** — e.g. `Post Generator → Hook Analyzer`, `Optimizer → Image Generator`, `Repurposing → Carousel Planner`.

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

## Project layout

```
.
├── app.py                       # Main router + Home, Hook Analyzer, Library, Carousel pages
│
├── core/                        # Shared infrastructure
│   ├── ai.py                    #   Central Gemini wrapper with retry + JSON validation
│   ├── db.py                    #   Supabase persistence (lb_posts + lb_profiles)
│   └── state.py                 #   Session-state init + profile auto-load on cold start
│
├── library.py                   # Single source of truth for save-to-library
├── gemini_client.py             # Streaming Gemini wrapper used by per-module prompts
├── image_client.py              # Stability AI + Hugging Face image generation
├── industry_profiles.py         # Industry voice blocks + Nigerian tone presets
│
├── post_generator.py            # 🚀 Post Generator
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
│
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

Python 3.9+ · [Streamlit](https://streamlit.io) · [Google Gemini](https://aistudio.google.com) ·
[Stability AI SDXL](https://platform.stability.ai) · [Hugging Face](https://huggingface.co) ·
[Supabase](https://supabase.com)
