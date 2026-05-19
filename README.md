# Ad Profitability Scorer

## A full-stack ML app that scores marketing ads and tells you if they'll make money

You paste in ad copy, it scores the ad across 12 dimensions using an LLM, runs the scores through two ML models, does break-even math against your business numbers, and gives you a verdict: **RUN**, **FIX FIRST**, or **DON'T RUN**.

This project covers:

- Building an LLM-powered labeling pipeline (Claude API + custom persona prompt)
- Training and comparing two ML models (Random Forest vs XGBoost)
- Designing a scoring system based on real marketing frameworks (Hormozi, Cialdini, Brunson)
- Building a FastAPI backend with profitability math
- Connecting a React frontend to a Python backend
- Writing tests with mocked API calls
- Context-relative evaluation (a raw iPhone testimonial isn't scored the same as a polished video ad)

## How it works

```
You input: ad copy + business info (price, cost, budget)
                        |
                        v
         Claude API scores the ad across 12 dimensions
         (using a custom expert persona prompt)
                        |
                        v
         Two ML models predict overall impact score
         (Random Forest + XGBoost)
                        |
                        v
         Profitability math runs against your margins
         (break-even CPA, estimated cost range)
                        |
                        v
         You get back: scores, strengths, weaknesses,
         priority fixes, and a RUN / FIX / DON'T RUN verdict
```

## What the 12 scoring dimensions are

| Dimension | What it's checking |
|---|---|
| Hook Power | Does the opening stop someone from scrolling? |
| Offer Strength | Is the offer good enough?|
| Persuasion Depth | How many psychological triggers does it use? |
| Narrative & Emotion | Is there a story that makes you feel something? |
| Structure & Flow | Does it flow from hook to body to CTA? |
| CTA Clarity | Is there one clear ask? |
| Audience Targeting | Does it talk to a specific person or everyone? |
| Funnel Fit | Is the message right for cold/warm/hot traffic? |
| Platform Optimization | Does it fit the platform it runs on? |
| Conversion Likelihood | Will someone actually do something after seeing this? |
| Message-Market Match | Does it speak the language this market uses? |
| Ad Type Execution | How well does it pull off its format (UGC, testimonial, etc)? |

## Design decisions

**Why context-relative scoring?**
A scrappy iPhone testimonial and a polished 2-minute video sales letter are both valid strategies. You can't score them on the same scale. So the system detects what kind of ad it is first (niche, audience, format), then scores how well it executes that specific strategy.

**Why profitability math instead of predicting clicks?**
I don't have real ad platform data and I'm not going to fake it. Instead the system flips the question: given your margins, what does your cost-per-acquisition need to be? Given the ad quality, is that realistic?

**Why two models?**
Random Forest builds a bunch of independent decision trees and averages them. XGBoost builds trees one after another where each tree tries to fix the mistakes of the last one. Showing both lets you see where they agree and where they disagree.

**Why 12 dimensions instead of 9?**
Started with 9 that measure copy quality. Added 3 more (conversion likelihood, message-market match, ad type execution) that measure whether the ad will actually work in the real world. You can write a perfectly structured ad that still fails because it uses the wrong language for its audience.

## Model performance

Trained on 90 real ad transcripts scored by Claude. 5-fold cross-validation results:

| Model | MAE | R2 |
|---|---|---|
| Random Forest | 0.317 | 0.543 |
| XGBoost | 0.312 | 0.526 |

Both models agree with Claude's score within 1 point 100% of the time.

The R2 is moderate because the dataset is small and the scores cluster between 5 and 8. With more training data the models should improve. Right now they're useful for smoothing out noise in Claude's scoring, not for replacing it.

## How to run it locally

1. Clone the repo

```bash
git clone https://github.com/ianwright27/brain-ad-scorer.git
cd brain-ad-scorer
```

2. Set up the backend

```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # then open .env and add your Anthropic API key
uvicorn app.main:app --reload
```

3. Set up the frontend (in a separate terminal)

```bash
cd frontend
npm install
npm run dev
```

4. Open the URL that Vite prints out (usually `http://localhost:5173`)

## How to add more training data

1. Paste ad transcripts into `data/raw/real_ads.txt`, separated by `--- AD ---`
2. Run `python scripts/label_real_ads.py` to score them with Claude
3. Run `python scripts/train_model.py` to retrain the models on the new data

## How to run the tests

```bash
python -m pytest tests/ -v
```

There are 6 tests covering: response shape, input validation, all 12 dimensions present, e-commerce profitability math, lead gen profitability math, and the fallback when no business inputs are given.

## How the pipeline fits together

```
prompts/hormozi_brain.md        the expert persona prompt Claude uses to evaluate ads
                                    |
scripts/label_real_ads.py       sends ads to Claude, saves the 12-dimension scores to CSV
                                    |
scripts/train_model.py          trains Random Forest + XGBoost on the labeled data
                                    |
app/main.py                     FastAPI backend that ties it all together at runtime
                                    |
frontend/src/App.jsx            React UI where you paste ads and see results
```

## Project structure

```
app/main.py                  FastAPI backend with /score endpoint and profitability math
scripts/label_real_ads.py    sends real ads to Claude for scoring
scripts/train_model.py       trains both models, saves metrics and charts
prompts/hormozi_brain.md     the full expert persona system prompt
prompts/scoring_rubric.md    reference doc for the scoring schema
models/ad_scorer_rf.pkl      trained Random Forest model
models/ad_scorer_xgb.pkl     trained XGBoost model
data/raw/                    raw ad transcripts (input)
data/labeled/                scored training data (output from labeling)
data/processed/              metrics, feature importance charts
frontend/src/App.jsx         React frontend
tests/test_api.py            API tests with mocked Claude responses
```

## Built with

Python 3.11 · scikit-learn · XGBoost · FastAPI · Anthropic Claude API · React · Vite · pytest
