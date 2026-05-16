# Ad Profitability Scorer

Scores ad copy across 12 persuasion/conversion dimensions using an LLM evaluator, calculates profitability against your unit economics, and returns a RUN / FIX FIRST / DON'T RUN verdict.

## Architecture

```
User inputs:
  ├── Ad copy / video transcript
  ├── Business type (e-commerce or lead gen)
  └── Unit economics (price, cost, close rate, ad budget)
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  Claude API + expert persona prompt         │
  │  → detects context (niche, audience, style) │
  │  → scores 12 dimensions (context-relative)  │
  │  → returns strengths, weaknesses, fixes     │
  └─────────────────────────────────────────────┘
        │
        ├─► Random Forest model ──► prediction
        ├─► XGBoost model ────────► prediction
        │
        ├─► Break-even math (CPA/CPL calculation)
        ├─► Profitability assessment
        │
        └─► Final verdict: RUN / FIX FIRST / DON'T RUN
```

**Frontend** — React (Vite), deployed on Vercel
**Backend** — FastAPI, deployed on Render
**Models** — scikit-learn `RandomForestRegressor` + `XGBRegressor`

## What Makes This Different

**Context-relative scoring.** A raw UGC testimonial isn't penalized for lacking polished structure — if raw authenticity IS the strategy, it's scored on how well it executes that strategy. A $47 product ad isn't held to the same narrative standard as a $10k coaching offer. The system detects the ad's context (niche, audience temperature, ad style, funnel position) and evaluates relative to its job.

**Profitability layer.** Input your unit economics and the system calculates whether the ad can realistically be profitable — not just whether the copy is "good." Break-even CPA, estimated acquisition cost range, margin of safety, and monthly conversion projections.

**Actionable output.** Not just a score — red flags, top strengths, specific weaknesses, and priority fixes tied to frameworks (Hormozi, Cialdini, Brunson, Suby).

## Scoring Dimensions

| Dimension | What it measures |
|---|---|
| Hook Power | Does the opening stop the scroll? |
| Offer Strength | Dream outcome vs. time/effort/risk (Hormozi Value Equation) |
| Persuasion Depth | Layered psychological triggers (Cialdini) |
| Narrative & Emotion | Story arc and identity shift (Brunson Epiphany Bridge) |
| Structure & Flow | Hook → Body → CTA through-line |
| CTA Clarity | Specific, single, proportional ask |
| Audience Targeting | Speaks to one person, not everyone |
| Funnel Fit | Message matched to traffic temperature |
| Platform Optimization | Native to the ad platform's behavior |
| Conversion Likelihood | Will someone actually act after seeing this? |
| Message-Market Match | Does messaging hit what this market cares about? |
| Ad Type Execution | How well does it execute its chosen format? |

## Design Decisions

**Why context-relative scoring?**
A scrappy iPhone testimonial and a polished 2-minute VSL can both perform well — for different audiences, offers, and funnel stages. Scoring them on the same absolute scale produces meaningless comparisons. The system detects context first, then evaluates execution quality within that context.

**Why profitability math instead of CTR prediction?**
We don't have real ad platform metrics and don't pretend to. Instead, we flip the question: given your margins, what CPA do you NEED? Given the ad's conversion quality score, is that CPA realistic? This is honest and actually useful — it's what a media buyer thinks about before launching.

**Why 12 dimensions instead of 9?**
The original 9 dimensions measure copy quality. The 3 new dimensions (`conversion_likelihood`, `message_market_match`, `ad_type_execution`) measure whether the ad will actually WORK in context. An ad can score 9/10 on structure and still fail because it uses the wrong language for its market.

**Why two ML models?**
Random Forest averages independent decision trees; XGBoost builds trees sequentially where each corrects the previous one's errors. Showing both demonstrates model comparison methodology and surfaces where they agree or diverge.

## How the Pipeline Works

1. **Persona prompt** (`prompts/hormozi_brain.md`) — expert-level ad evaluation encoding frameworks from Hormozi, Cialdini, Brunson, Suby, and Robinson.
2. **Label generation** (`scripts/label_real_ads.py`) — sends real ad transcripts to Claude for context-aware scoring across all 12 dimensions.
3. **Model training** (`scripts/train_model.py`) — trains both RF and XGBoost on `(12 dimensions → overall_impact)`. Outputs metrics, feature importance, and comparison charts.
4. **Inference** (`app/main.py`) — FastAPI receives ad copy + business inputs, calls Claude for scores, feeds to models, calculates profitability, returns full analysis with run verdict.

## Running Locally

```bash
git clone https://github.com/<your-username>/brain-ad-scorer.git
cd brain-ad-scorer

# Backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Labeling Real Ads

1. Paste video transcripts into `data/raw/real_ads.txt` separated by `--- AD ---`
2. Run `python scripts/label_real_ads.py` — scores each ad and saves to `data/labeled/real_ads_labeled.csv`
3. Run `python scripts/train_model.py` — retrains models on the new data

## Testing

```bash
python -m pytest tests/ -v
```

6 tests covering: valid response shape, input validation, dimension completeness, e-commerce profitability math, lead gen profitability math, and no-inputs fallback.

## Tech Stack

Python 3.11 · scikit-learn · XGBoost · FastAPI · Anthropic Claude API · React · Vite · pytest

## Project Structure

```
app/
  main.py              # FastAPI backend — /score endpoint, profitability math, retry logic
scripts/
  label_real_ads.py    # Context-aware labeling pipeline for real ad transcripts
  train_model.py       # Trains RF + XGBoost on 12 features, generates metrics + charts
prompts/
  hormozi_brain.md     # Expert persona system prompt (context-relative scoring)
  scoring_rubric.md    # Scoring schema reference
models/
  ad_scorer_rf.pkl     # Trained Random Forest
  ad_scorer_xgb.pkl    # Trained XGBoost
data/
  raw/                 # Real ad transcripts (input)
  labeled/             # Scored training data (output)
  processed/           # Metrics JSON, feature importance + comparison charts
frontend/
  src/App.jsx          # React UI — business inputs, verdict, profitability, dimensions
tests/
  test_api.py          # API endpoint tests with mocked Claude
```
