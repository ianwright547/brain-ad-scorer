# Brain Ad Scorer

ML model that scores marketing ads using Alex Hormozi's frameworks, deployed as a Streamlit web app.

> Status: Work in progress — 2-week portfolio build.

## How it works

1. A persona prompt encodes how Hormozi evaluates ads (hooks, offers, specificity, curiosity gaps, etc.).
2. The Claude API uses that persona to grade each ad on structured **expert dimensions** (`hook_quality`, `offer_clarity`, `specificity`, `curiosity_gap`, `risk_reversal`, `urgency`, `cta_strength`, `audience_callout`) plus an overall score.
3. A scikit-learn model is trained on `(expert dimensions → overall score)` — learning the expert's weighting function.
4. The Streamlit app takes a new ad, calls Claude to grade its dimensions, then runs the local model to produce a final score with explanation.

## Tech stack
Python 3.11 · scikit-learn · pandas · Streamlit · Anthropic API · OpenCV · Pillow

## Running locally
```bash
git clone <repo>
cd brain-ad-scorer
python -m venv venv
.\venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env      # then add your Anthropic API key
streamlit run app/streamlit_app.py
```

_(Full docs — architecture diagram, demo link, learnings — will be added as the project progresses.)_
