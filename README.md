# ML Ad Scorer

Scores ad copy across 9 persuasion dimensions using an LLM evaluator, then compares predictions from two ML models (Random Forest, XGBoost) against the LLM's own score.

## Architecture

```
Ad copy (user input)
  │
  ├─► Claude API + expert persona prompt
  │     → scores 9 dimensions (hook power, offer strength, etc.)
  │
  ├─► Random Forest model ──► prediction
  ├─► XGBoost model ────────► prediction
  │
  └─► Returns all three: RF prediction, XGBoost prediction, Claude raw score
```

**Frontend** — React (Vite), deployed on Vercel  
**Backend** — FastAPI, deployed on Render  
**Models** — scikit-learn `RandomForestRegressor` + `XGBRegressor`, trained on 90 LLM-labeled ads

## Model Performance

| Metric | Random Forest | XGBoost |
|---|---|---|
| MAE | 0.17 | 0.16 |
| R² | 0.99 | 0.99 |
| Within 1 pt of Claude | 100% | — |
| Within 0.5 pt of Claude | 89% | — |

Evaluated on a held-out test set of 18 ads (20% split, `random_state=42`).

![Feature Importance](data/processed/feature_importance.png)

![Model vs Claude Comparison](data/processed/model_comparison.png)

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

## Design Decisions

**Why LLM-extracted features instead of visual/NLP features?**  
The original plan was to train on surface-level features: word count, sentiment, color brightness. We scrapped it because the scoring framework evaluates *messaging quality* — hook strength, offer clarity, specificity. A bright CTA button doesn't make an ad good. Training on pixel-level features would teach the model to find noise, not expertise. Using the LLM to extract expert-graded dimensions gives the model features that actually correlate with ad quality as defined by the framework.

**Why two API calls during labeling instead of one?**  
One call where Claude generates and scores its own ad introduces self-rating bias — it rates its own output too favorably. Two calls (generate, then score separately) create cleaner separation. The scoring call uses a fixed persona prompt and evaluates the ad cold, the same way it would evaluate a real ad.

**Why regression instead of classification?**  
Bucketing scores into Low/Medium/High throws away signal. A 4.8 and a 6.9 both become "Medium" and the model can never recover that distinction. Regression preserves the full continuous score range.

**Why two models?**  
Random Forest and XGBoost learn differently. RF averages independent decision trees; XGBoost builds trees sequentially where each corrects the previous one's errors. Showing both predictions demonstrates model comparison methodology and lets the user see where they agree or diverge on a given ad.

## How the Pipeline Works

1. **Persona prompt** (`prompts/hormozi_brain.md`) — encodes expert-level ad evaluation criteria from Hormozi, Cialdini, Brunson, and direct response frameworks.
2. **Label generation** (`scripts/label_ads.py`) — two-call architecture: Claude generates synthetic ads at varying quality levels, then a separate Claude call scores each one.
3. **Model training** (`scripts/train_model.py`) — trains both Random Forest and XGBoost on `(9 dimensions → overall_impact)`. Outputs metrics, feature importance charts, and model comparison visualizations.
4. **Inference** (`app/main.py`) — FastAPI receives ad copy, calls Claude for dimension scores, feeds them to both models, returns all three scores with retry logic.

## Running Locally

```bash
git clone https://github.com/<your-username>/ml-ad-scorer.git
cd ml-ad-scorer

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

## Tech Stack

Python 3.11 · scikit-learn · XGBoost · FastAPI · Anthropic Claude API · React · Vite

## Project Structure

```
app/
  main.py              # FastAPI backend — /score endpoint, retry logic
scripts/
  label_ads.py         # Two-call labeling pipeline (generate + score)
  train_model.py       # Trains RF + XGBoost, generates metrics + charts
prompts/
  hormozi_brain.md     # Expert persona system prompt
  scoring_rubric.md    # Scoring schema reference
models/
  ad_scorer_rf.pkl     # Trained Random Forest
  ad_scorer_xgb.pkl   # Trained XGBoost
data/
  labeled/             # LLM-labeled training data (90 ads)
  processed/           # Metrics JSON, feature importance + comparison charts
frontend/
  src/App.jsx          # React UI — input, three-score display, dimension bars
```
