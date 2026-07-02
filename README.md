# brain-ad-scorer

Scores marketing ads before you spend money on them.

Paste ad copy or upload the creative itself. An expert-persona LLM grades it across 12
dimensions, two ML models predict overall impact from those dimensions, a hand-written
analysis engine runs deterministic checks locally, and break-even math runs against your
margins. Out comes a verdict: **RUN it**, **FIX it first**, or **DON'T RUN it**.

## Demo

[Loom walkthrough →](https://www.loom.com/share/839d9cc3fec545ada3fa94633cb772ba)

## Architecture

```
ad copy and/or image ──► FastAPI
                           │
        ┌──────────────────┼───────────────────────┐
        ▼                  ▼                       ▼
  text preflight     image inspector        SQLite cache
  (readability,      (sharpness, contrast,  (SHA-256 of input +
  lexicons, regex —  colorfulness — raw     prompt version;
  no API, <1ms)      pixels via numpy)      hit = $0, instant)
        │                  │                       │ miss
        │                  │                       ▼
        │                  │              Claude API (text or vision)
        │                  │              grades 12 expert dimensions
        │                  │                       │
        │                  │         ┌─────────────┴────────────┐
        │                  │         ▼                          ▼
        │                  │   Random Forest              XGBoost
        │                  │   (dimensions → overall impact score)
        │                  │         │                          │
        └──────────────────┴─────────┴──────────┬───────────────┘
                                                ▼
                                 break-even math vs your margins
                                                ▼
                                    RUN / FIX FIRST / DON'T RUN
```

## The interesting parts

**Hand-written text analysis, zero API.** `analysis/text_features.py` computes
Flesch-Kincaid readability from scratch (including the syllable-counting heuristic),
matches curated copywriting lexicons, and detects CTAs, specificity signals, and risk
reversal with regex. It runs in under a millisecond and costs nothing, so it works as a
pre-flight check before any money is spent on an LLM call.

**Pixel-level image analysis.** `analysis/image_features.py` takes raw image bytes and
computes brightness, RMS contrast, Laplacian-variance sharpness (the classic blur
detector), Sobel edge density, and the Hasler-Süsstrunk colorfulness metric — all with
numpy convolutions written by hand, no OpenCV. It also sniffs the file format from magic
bytes instead of trusting extensions, and checks dimensions against real platform specs.

**Content-addressed caching.** Every Claude response is cached in SQLite, keyed on
SHA-256 of the exact input plus a hash of the evaluation prompt. Identical input never
bills twice, and editing the prompt file automatically invalidates every stale entry —
there is no manual invalidation step to forget.

**ML with baselines, not vibes.** The models are evaluated against a dummy mean-predictor
(the floor) and linear regression (does the relationship even need trees?). Random Forest
wins on 5-fold cross-validation, which means the dimension weighting is genuinely
non-linear. Feature importance is measured by permutation on held-out data, not impurity.

## Model performance

12 expert-graded dimensions → `overall_impact`, trained on 30 real ad transcripts
(24 train / 6 test, 5-fold CV on the full set).

| model         | CV MAE      | CV R²        | holdout MAE | holdout R² |
|---------------|-------------|--------------|-------------|------------|
| dummy (mean)  | 1.53 ± 0.42 | −0.79 ± 0.78 | 1.28        | −0.96      |
| linear        | 0.68 ± 0.32 |  0.57 ± 0.41 | 0.32        |  0.84      |
| random forest | **0.46 ± 0.16** | **0.86 ± 0.10** | **0.31** | **0.88**   |
| xgboost       | 0.52 ± 0.05 |  0.74 ± 0.17 | 0.34        |  0.75      |

Random Forest agrees with the expert score within 1 point on 100% of held-out ads, within
0.5 points on 83%. Permutation importance says the expert's verdict is driven mostly by
`conversion_likelihood` and `audience_targeting` — hook quality matters less than ad
gurus claim, at least in this dataset.

## API

| method | route      | what it does                                                        |
|--------|-----------|----------------------------------------------------------------------|
| POST   | `/score`   | full evaluation — copy and/or base64 image, optional business economics |
| POST   | `/analyze` | deterministic text pre-flight only — free, no API call               |
| GET    | `/history` | recent evaluations from SQLite                                       |
| GET    | `/health`  | liveness + active prompt version                                     |

## Run it locally

```bash
# backend
git clone https://github.com/ianwright547/brain-ad-scorer.git
cd brain-ad-scorer
python -m venv venv
source venv/bin/activate      # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # add your Anthropic API key
uvicorn app.main:app --reload

# frontend (separate terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env.local
npm run dev
```

## Tests

33 tests: unit tests for the syllable counter, readability math, lexicon matching, image
metrics (against generated test images), cache behavior, plus API tests with the Claude
call mocked. CI runs ruff + pytest on every push.

```bash
pip install -r requirements-dev.txt
pytest
```

## Honest limitations

- 30 labeled samples is small. The metrics are real but the confidence intervals are wide
  — more labeled ads is the single highest-leverage improvement.
- The ML models are distilling Claude's own weighting function, not independent ground
  truth. The head-to-head comparison measures agreement, not ad performance. Validating
  against real CTR/CPA data is the obvious next step.
- The estimated CPA range in the profitability engine is an industry heuristic, clearly
  labeled as such — not a prediction from the model.

## Stack

Python 3.11 · FastAPI · scikit-learn · XGBoost · numpy · Pillow · SQLite · Claude API ·
React · Vite · pytest · ruff · GitHub Actions
