# Brain Ad Scorer — Learning Notes

Updated after every step. Use this to review what was built and why.

---

## Phase 1: Brain Profile + Data (in progress)

### Steps 1.1 + 1.2 — Reference Material + Expert Persona Prompt ✅

**What we built:**
- `prompts/hormozi_brain.md` — the full "Master Ad Evaluation Engine" system prompt. Built on frameworks from Hormozi, Cialdini, Brunson, Suby, and Robinson. Includes a 10-step inference chain, detailed layer-by-layer analysis, a failure taxonomy of 24 ad-killers, and a scoring rubric. This becomes the system prompt for the Claude API labeling calls.
- `prompts/scoring_rubric.md` — quick-reference schema showing the exact JSON Claude returns per ad, what each dimension means, and how they map to ML features.

**What a persona prompt is:**
A system prompt tells Claude "who it is" before it sees any user message. Instead of Claude responding as a general assistant, it responds as a direct response marketing strategist who has internalized these specific frameworks. The quality of the labels depends entirely on how well-designed this prompt is — garbage in, garbage out.

**The 10 scoring dimensions (our ML features):**
```
hook_power         → Does the first 3 seconds stop the scroll?
offer_strength     → Hormozi Value Equation: dream outcome × proof / time × effort
persuasion_depth   → How many Cialdini principles are layered?
narrative_emotion  → Is there a story + identity shift (Brunson Epiphany Bridge)?
structure_flow     → Hook-Body-CTA: is there a single clear through-line?
cta_clarity        → Is the ask specific, single, and proportional to funnel stage?
audience_targeting → Does it speak to one person, or everyone (= no one)?
funnel_fit         → Right message for the traffic temperature (cold/warm/hot)?
platform_optimization → Is it native to Meta/YouTube/TikTok behavior?
overall_impact     → Expert's final verdict (this is our ML target variable)
```

**Why we use these instead of visual features:**
The original plan was to extract color brightness, word count, sentiment, etc. and predict a score from those. We scrapped it because Hormozi rates messaging quality — not pixel aesthetics. A bright red button doesn't make an ad good. The hook text does. These 10 dimensions capture the actual decision-making criteria.

---

### Step 1.3 — Regression vs Classification ✅

**Decision: Regression.** The model predicts `overall_impact` as a float (1.0–10.0).

**Why not classification?**
Bucketing scores (Low/Medium/High) loses information. A 4.8 and a 6.9 both become "Medium" — the model can never recover that distinction. Regression preserves every point Claude scored.

**The interview answer:** "I framed it as regression because the target variable is a continuous expert score. Classification would have required me to invent arbitrary buckets and throw away signal."

**Class balance in regression:** Even in regression, you need score *range coverage* in your training data. If every ad scores 6–8, the model learns to predict ~7 for everything. You need weak ads (2–4), average (5–7), strong (7–8), and exceptional (9–10) so the model learns the full relationship.

---

### Step 1.4 — Synthetic Data Generation ✅

**What is synthetic data?**
Data that an AI generates rather than data collected from the real world. Valid when: (a) you can't easily collect real data, and (b) the generator understands the domain well enough to produce realistic examples.

Here, Claude generates ad copy at different quality levels — then a separate Claude call scores it. The dataset is artificial but the scoring is grounded in real frameworks (Hormozi, Cialdini, Brunson).

**Why two API calls instead of one?**
- One call = Claude generates AND scores its own output → bias (rates itself too high) and confusion (two jobs in one prompt = worse at both)
- Two calls = generate first, score second → cleaner separation, more honest scores

**The interview answer:** "I used synthetic data because sourcing and labeling 90 real ads would have taken weeks. Claude generates ads at specified quality levels, then a separate Claude call scores them using the expert framework as a system prompt. Two calls prevents the model from rating its own output."

---

### Step 1.5 — label_ads.py ✅

**What the script does:**
1. Loops 90 times
2. Call 1 → Claude writes ad copy (quality tier + business type + platform specified)
3. Call 2 → Claude scores the ad using the Hormozi framework → returns JSON
4. Parses the JSON into a flat row of numbers
5. Saves all rows to `data/labeled/ads_labeled.csv`

**Key concepts in the script:**

**System prompt vs user message:**
- System prompt = Claude's identity/instructions ("you are an expert ad evaluator, return only JSON...")
- User message = the actual ad copy being evaluated
- The system prompt stays the same for all 90 scoring calls. Only the ad copy changes.

**Why `time.sleep(1)`?**
APIs have rate limits — max requests per minute. Firing 180 calls with no pause gets you rejected. One second between calls keeps you under the limit.

**Why parse JSON?**
Claude returns text. We need numbers. `json.loads()` converts the text `{"hook_power": 7}` into a Python dictionary you can actually do math on. The ML model trains on numbers, not strings.

**What goes into the CSV:**
- 9 dimension scores (features / X)
- `overall_impact` (target / y)
- `ad_copy` (text — not a feature, used for app display)
- `quality_tier`, `business_type`, `platform`, `verdict` (metadata)

**The interview answer:** "The labeling script makes two API calls per ad — one to generate, one to score. It saves 90 rows to a CSV where each row has 9 expert-graded dimension scores as features and overall_impact as the target. That CSV is what the ML model trains on."

---

### The Big Picture So Far

```
PDF framework (Hormozi/Cialdini/Brunson)
        ↓
System prompt in Claude (hormozi_brain.md)
        ↓
label_ads.py: generate 90 ads → score each → CSV
        ↓
data/labeled/ads_labeled.csv
        ↓ (Phase 3)
scikit-learn trains on (9 dimensions → overall_impact)
        ↓ (Phase 4)
Streamlit app: user pastes ad → Claude scores dimensions → model predicts impact
```

**Why this is a strong portfolio project:**
Most ML projects use pre-built datasets from Kaggle. This one has a custom labeled dataset built with a real expert framework, a clear business use case, and a head-to-head model vs. Claude comparison. That's a story, not just code.

---

## Phase 0: Environment Setup ✅

### What this phase was about
Before writing any ML code, we needed a clean, reproducible workspace. Like mise en place in cooking — everything in its place before you start.

---

### Step 0.2 — Folder Structure
Created 9 folders inside `brain-ad-scorer/`.

The folders tell the data flow story:
```
data/raw/ → (Claude labels) → data/labeled/ → (features) → data/processed/ → (training) → models/ → (loaded by) → app/
```
Anyone cloning this repo can understand the pipeline just from the folder names. That's intentional.

---

### Step 0.3 — Virtual Environment + Dependencies
Created `venv/` and installed 13 packages.

**Virtual environment**: a sandboxed Python installation scoped to this project. Without one, all your projects share the same packages and eventually versions collide. `requirements.txt` is the recipe — anyone who clones the repo can recreate your environment with one command.

**Key packages and why:**
| Package | What it does |
|---|---|
| `pandas` | Spreadsheet-style data manipulation in Python |
| `numpy` | Numerical arrays + math that pandas runs on |
| `scikit-learn` | The ML library — train, test, evaluate models |
| `joblib` | Save/load trained models to disk |
| `anthropic` | Official Claude API SDK — calls Claude to label ads |
| `python-dotenv` | Loads `.env` so API keys don't end up in code |
| `streamlit` | Turns Python scripts into web apps |
| `opencv-python` + `Pillow` | Image loading and visual feature extraction |
| `pytesseract` | OCR — extract text from ad images |
| `textblob` | Simple NLP (sentiment analysis) |
| `matplotlib` + `seaborn` | Charts and visualizations for the README |

---

### Step 0.4 — Git + GitHub
Initialized a git repo and pushed to GitHub.

**Key concepts:**

**.gitignore** — a list of files git should *never* track. Most important entry: `.env` (your API key). If an API key lands in a public GitHub repo, automated bots scrape it within minutes. And git history is permanent — even if you delete the file later, the key is still in history.

**.env vs .env.example** — `.env` holds your real key (gitignored, never committed). `.env.example` is a template committed to the repo showing what env vars are needed, with placeholders. Standard pattern for any project with secrets.

**CLAUDE.md** — loaded by Claude Code at the start of every session in this folder. Lets future sessions resume without re-explaining the project.

**Why git history matters for a portfolio**: commit history shows employers you work like a professional — incremental progress, clear messages, no "final_FINAL_v3.py" files.

---

### Architecture Decision: Why Path A

**Original plan**: Train an ML model on visual features (color brightness, word count, sentiment) → predict a Hormozi-style score.

**The problem**: Hormozi rates ads on *messaging quality* — hook strength, offer clarity, specificity. A bright image or a red CTA button doesn't make an ad good. Training on those features would teach the model to find noise, not expertise. It would lose badly to Claude in the head-to-head comparison step, and the resume story falls apart.

**Path A (what we're actually doing)**: Claude grades each ad on specific *expert dimensions*:
- `hook_quality` — does the opening grab attention?
- `offer_clarity` — is it obvious what you're getting?
- `specificity` — concrete details vs vague claims
- `curiosity_gap` — does it make you want to know more?
- `risk_reversal` — money-back guarantee, free trial, etc.
- `urgency` — reason to act now
- `cta_strength` — is the call to action clear and compelling?
- `audience_callout` — does it speak directly to a specific person?

Plus an `overall_score` (1–10).

The ML model trains on those 8 dimensions → overall score. It learns *Hormozi's weighting function* — which dimensions matter most and how they combine. That's the actual insight, not surface-level pixel analysis.

---

## Phase 1: Persona Prompt + Labeled Dataset — NEXT

We'll build the Hormozi persona prompt and use it to label 80–100 real ads.

**What you'll learn:**
- How to design a persona prompt that makes Claude think like an expert
- How the Anthropic API works (sending images, getting structured JSON back)
- What a training dataset looks like and why label quality is the foundation of the whole project

**What you need to bring:** Your knowledge of Hormozi's frameworks — from his books, YouTube, anything you've read or watched. We'll structure it together.
