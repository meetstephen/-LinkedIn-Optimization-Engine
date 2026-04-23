# 🚀 LinkedIn Optimization Engine

> **AI-powered LinkedIn growth toolkit** — Transform your LinkedIn presence from beginner to thought leader using Gemini AI, Stability AI (SDXL), and Hugging Face.

---

## 📸 Features Overview

| Module | Description | AI Used |
|--------|-------------|---------|
| 🚀 **Post Generator** | 2–3 viral post variations with frameworks, hooks & CTAs | Gemini 1.5 Flash |
| 🔧 **Post Optimizer** | Diagnose + rewrite existing posts with engagement score | Gemini 1.5 Flash |
| 💼 **About Optimizer** | Personal brand story + keyword optimization | Gemini 1.5 Flash |
| 🌟 **Profile Enhancer** | Profile score (0–100) + 30-day transformation roadmap | Gemini 1.5 Flash |
| 💡 **Content Ideas** | Full content calendar by niche and pillar | Gemini 1.5 Flash |
| 🧠 **Strategy Insights** | Creator playbooks, hook formulas, algorithm tactics | Gemini 1.5 Flash |
| 🎨 **Image Generator** | Professional LinkedIn visuals (SDXL → HF fallback) | Stability AI + HF |
| ⚡ **Engagement Toolkit** | Hooks, CTAs, hashtags, optimal posting times | Gemini 1.5 Flash |

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Step 1: Clone or Download

```bash
# Download the project files or clone if using git
cd linkedin_optimizer
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure API Keys

You have two options:

#### Option A: Via the App (Recommended for beginners)
Just run the app — there's a sidebar panel to enter keys directly. They're stored in session state only.

#### Option B: Via .env file
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your actual keys
```

---

## 🔑 Getting Your API Keys (All Free)

### 1. Gemini API Key (Required for all text features)
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API key"**
4. Copy your key (starts with `AIza...`)
- **Free tier**: 60 req/min, 1M tokens/day with Gemini 1.5 Flash ✅

### 2. Stability AI API Key (Primary image generation)
1. Go to [platform.stability.ai](https://platform.stability.ai)
2. Sign up / Log in
3. Go to **Account** → **API Keys** → **Create API Key**
4. Copy your key (starts with `sk-...`)
- **Free credits**: New accounts get free credits to start ✅

### 3. Hugging Face API Key (Fallback image generation)
1. Go to [huggingface.co](https://huggingface.co) and sign up
2. Go to **Settings** → **Access Tokens**
3. Click **"New token"** → Set role to **Read**
4. Copy your key (starts with `hf_...`)
- **Free tier**: Inference API calls included ✅

---

## 🚀 Running the App

```bash
# From the linkedin_optimizer directory
streamlit run app.py
```

The app will open at **http://localhost:8501**

### Optional flags:
```bash
# Run on a specific port
streamlit run app.py --server.port 8080

# Run without browser auto-opening
streamlit run app.py --server.headless true

# Allow external access (for server deployment)
streamlit run app.py --server.address 0.0.0.0
```

---

## 📁 Project Structure

```
linkedin_optimizer/
│
├── app.py                    # Main Streamlit app + page router
│
├── modules/                  # Feature modules (one per page)
│   ├── post_generator.py     # Viral post creation with frameworks
│   ├── post_optimizer.py     # Post diagnosis + rewrite + scoring
│   ├── about_optimizer.py    # About section transformation
│   ├── profile_enhancer.py   # Profile score + 30-day roadmap
│   ├── content_ideas.py      # Content calendar generator
│   ├── strategy_insights.py  # Creator playbooks + tactics
│   ├── image_generator.py    # AI visual generation (UI layer)
│   └── engagement_toolkit.py # Hooks, CTAs, hashtags, timing
│
├── utils/                    # Shared utilities
│   ├── gemini_client.py      # Gemini API wrapper
│   └── image_client.py       # Image APIs (Stability + HF fallback)
│
├── requirements.txt          # Python dependencies
├── .env.example              # API keys template
└── README.md                 # This file
```

---

## 🎨 Image Generation Architecture

```
User Input (Post Content)
        ↓
Prompt Engineering (build_image_prompt)
  - Extract key theme
  - Apply style preset (SDXL / Minimalist / Corporate / etc.)
  - Add negative prompts
        ↓
Try PRIMARY: Stability AI SDXL
  ├── Success → Return image bytes
  └── Fail (rate limit / error) ↓
        ↓
Try FALLBACK: Hugging Face Inference API
  ├── Try SDXL → Stable Diffusion 1.5 → SD 1.4 (in order)
  ├── Success → Return image bytes
  └── Fail → Return error message
```

### Style Presets Available:
- **Corporate Professional** — Business photography style
- **Modern Minimalist** — Flat illustration, clean design
- **Tech & Innovation** — Dark background, neon accents
- **Warm & Human** — Documentary-style photography
- **Infographic / Data** — Charts and visual data
- **Sketch / Illustrated** — Hand-drawn business illustrations

---

## 📐 Content Frameworks Available

### Post Generator Frameworks:
1. **Hook → Story → Insight → CTA** — Classic viral formula
2. **Problem → Agitation → Solution** — Copywriting powerhouse
3. **Listicle (Numbered Tips)** — High-share format
4. **Before → After → Bridge** — Transformation posts
5. **Contrarian Statement** — High-engagement debates
6. **Personal Story Arc** — Vulnerability-driven growth

### Creator Archetypes (Strategy Module):
- The Educator, The Storyteller, The Contrarian Thinker
- The Results Poster, The Community Builder
- The Niche Expert, The Document Builder

---

## ⚡ Key Technical Details

### Gemini Integration
```python
# Uses Gemini 1.5 Flash for speed + cost efficiency
model = genai.GenerativeModel("gemini-1.5-flash")
# Configurable temperature (0.7–0.95 depending on task)
# Max tokens: 2048–3000 per request
```

### Image Generation Fallback Logic
```python
def generate_image(post_content, style, stability_key, hf_key):
    prompt = build_image_prompt(post_content, style)     # 1. Engineer prompt
    
    if stability_key:
        img, err = generate_image_stability(prompt, ...)  # 2. Try primary
        if img: return img, "stability", "✅ Stability AI"
        st.warning(f"Stability failed: {err}, trying fallback...")
    
    if hf_key:
        img, err = generate_image_huggingface(prompt, ...) # 3. Try fallback
        if img: return img, "huggingface", "✅ HuggingFace"
    
    return None, "failed", "Both APIs failed"
```

---

## 🔧 Customization Guide

### Adding New Post Frameworks
In `modules/post_generator.py`:
```python
FRAMEWORK_DESCRIPTIONS["Your Framework Name"] = "Description of the framework"
```

### Adding New Image Styles
In `utils/image_client.py`:
```python
STYLE_PRESETS["Your Style Name"] = "detailed style description for SDXL"
```

### Adding New Niche Keywords
In `modules/about_optimizer.py`:
```python
INDUSTRY_KEYWORDS["Your Industry"] = "keyword1, keyword2, keyword3"
```

---

## 🌐 Deployment

### Streamlit Community Cloud (Free)
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Add API keys as **Secrets** in the Streamlit dashboard:
   ```toml
   GEMINI_API_KEY = "AIza..."
   STABILITY_API_KEY = "sk-..."
   HUGGING_FACE_API_KEY = "hf_..."
   ```
5. Modify `app.py` to read from `st.secrets`:
   ```python
   st.session_state["gemini_api_key"] = st.secrets.get("GEMINI_API_KEY", "")
   ```

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: google.generativeai` | Run `pip install google-generativeai` |
| Gemini API 429 error | You've hit rate limits — wait 60 seconds or upgrade plan |
| Images not generating | Check Stability AI credits, then verify HF key is set |
| `ValueError: Gemini API key not set` | Add key in sidebar **Configure API Keys** panel |
| Streamlit not found | Run `pip install streamlit` |
| App crashes on startup | Ensure Python 3.9+ with `python --version` |

---

## 📜 Legal & Ethics

- ✅ No LinkedIn scraping or data extraction
- ✅ All content is AI-generated simulation (no real profiles copied)
- ✅ Creator tactics are simulated from publicly available best practices
- ✅ Images generated are original (not scraped or watermarked content)
- ❌ Not affiliated with LinkedIn or Microsoft in any way

---

## 🤝 Contributing

Feel free to extend the app with:
- Additional post frameworks
- New image style presets
- More industry keyword sets
- Multi-language support
- Analytics dashboard

---

*Built with Streamlit · Gemini AI · Stability AI (SDXL) · Hugging Face Inference API*
