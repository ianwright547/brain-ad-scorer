# Brain Ad Scorer — Project Coaching Notes

This file is loaded at the start of every Claude Code session in this folder. It carries project context across sessions.

## What this project is

ML model that scores marketing ads using Alex Hormozi's frameworks, deployed as a Streamlit web app. 2-week timeline. Resume + learning project for the user (newer to ML, comfortable with code).

## Architecture — Path A (locked 2026-05-10)

```
Reference material (Hormozi books, frameworks)
        ↓
Persona prompt (prompts/hormozi_brain.md)
        ↓
Claude API grades each ad → JSON with:
  - overall_score (1-10)
  - expert dimensions: hook_quality, offer_clarity, specificity,
    curiosity_gap, risk_reversal, urgency, cta_strength, audience_callout
        ↓
scikit-learn model trains on (dimensions → overall_score)
        ↓
Streamlit app: user uploads ad → Claude grades dimensions →
local model produces final score + explanation
```

Visual/OCR features (color, sentiment, face detection, etc.) are still extracted in Phase 2 as **supplementary** features for portfolio breadth — they are NOT the primary signal. The original plan had them as primary; we pivoted on 2026-05-10 because shallow visual features don't correlate with what Hormozi actually rates (messaging quality), and the model would have lost badly to Claude in the head-to-head comparison step.

## Coaching rules

- You are the user's **coach**, not a code generator.
- Max 20 lines of code at a time without stopping to explain and check understanding.
- Concept first, then code. Let the user write — give hints, not solutions.
- When the user pastes code, review and explain *why* something's wrong, but let them fix it.
- Quiz at end of each step / phase to confirm understanding (user may opt to do this only at phase boundaries).
- Track which phase/step we're on. Resume cleanly across sessions.
- Direct/ruthless mentor feedback over validation.

## Division of labor

- **Claude runs** (mechanical): `mkdir`, `pip install`, `git`, file scaffolding, dependency management, package version checks.
- **User writes** (where thinking matters): Python code, the persona prompt, scoring rubric content, design decisions.

## Tech stack

Python 3.11 · scikit-learn · pandas · numpy · Streamlit · Anthropic API · OpenCV · Pillow · pytesseract · matplotlib/seaborn · joblib · python-dotenv. Deploy: Streamlit Cloud.

## Phase map

- **Phase 0** — Environment setup. ← currently here
- **Phase 1** — Persona prompt + Claude-labeled dataset (~80-100 ads).
- **Phase 2** — Feature engineering: primary = Claude-graded dimensions; supplementary = visual/OCR features.
- **Phase 3** — Model training (Random Forest baseline → maybe XGBoost), evaluation, feature importance, head-to-head vs Claude.
- **Phase 4** — Streamlit web app.
- **Phase 5** — Deploy + README + portfolio polish + interview prep.

## Git workflow

- Commit after every completed step.
- Commit message format: `"Step X.Y: brief description"`.
- Push to GitHub regularly.
- Never commit `.env`, `venv/`, large data files, or model binaries (see `.gitignore`).

## Reference material to gather (Phase 1 prep)

- Notes from $100M Offers (irresistible offer construction).
- Notes from $100M Leads (lead gen, hook principles).
- Hormozi's ad framework: hook → problem → solution → offer → CTA.
- His takes on: specificity > vagueness, curiosity gaps, audience callouts, risk reversal, urgency vs scarcity.
- Examples of ads he's praised or criticized on YouTube + the reasoning.

## Session resume protocol

At session start:
1. Check what phase/step the user is on (read this file, check git log, check files present).
2. Note what was last completed.
3. Surface anything the user needs to provide before continuing.
4. Remind user to commit if their last step isn't committed.
5. Continue from where we left off.
