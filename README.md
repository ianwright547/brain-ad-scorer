# Brain Ad Scorer

Scores marketing ads before you spend money on them.

## Demo

[Loom walkthrough →] https://www.loom.com/share/839d9cc3fec545ada3fa94633cb772ba 

## What it does

You paste in ad copy and your business numbers (price, cost, budget). It runs the ad through a custom LLM persona built on Hormozi/Cialdini/Brunson marketing frameworks, scores it across 12 dimensions, feeds those scores into two ML models, does break-even math against your margins, and tells you: **RUN it**, **FIX it first**, or **DON'T RUN it**.

Not a vibe check — actual scoring with profitability math behind it.

## Use case

Most people burn ad spend testing copy that was never going to convert. This catches the obvious misses before you put dollars behind them. You get back dimension-level scores, specific weaknesses, priority fixes, and whether the unit economics even make sense for your offer.

## What's under the hood

- **Claude API + custom persona prompt** — built an expert evaluator persona grounded in real marketing frameworks, not generic "rate this ad" prompting
- **scikit-learn + XGBoost** — trained two models (Random Forest and XGBoost) on 90 real ad transcripts to predict overall impact from 12 dimension scores
- **FastAPI** — Python backend handling scoring, model inference, and profitability calculations
- **React + Vite** — frontend that sends ad copy and renders the full breakdown
- **Context-relative scoring** — a scrappy iPhone testimonial gets evaluated differently than a polished VSL, because they're different strategies
- **Profitability engine** — no fake click predictions, instead it flips the question: given your margins, what CPA do you need, and is this ad good enough to hit it?
- **pytest with mocked API calls** — 6 tests covering response shape, validation, dimension coverage, e-commerce math, lead gen math, and fallback behavior

## How it works

```
Ad copy + business numbers in
        ↓
Claude API scores 12 dimensions via custom persona
        ↓
Random Forest + XGBoost predict overall impact
        ↓
Profitability math runs against your margins
        ↓
Scores, weaknesses, fixes, and a verdict out
```

## Run it locally

```bash
# backend
git clone https://github.com/ianwright547/brain-ad-scorer.git
cd brain-ad-scorer
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # add your Anthropic API key
uvicorn app.main:app --reload

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open whatever URL Vite gives you (usually `http://localhost:5173`).

## Stack

Python 3.11 · scikit-learn · XGBoost · FastAPI · Claude API · React · Vite · pytest
