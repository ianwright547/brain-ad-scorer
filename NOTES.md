# Brain Ad Scorer — Learning Notes

Updated after every step. Use this to review what was built and why.

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
