# Brain Ad Scorer — Project Coaching Notes

This file is loaded at the start of every Claude Code session in this folder. It carries project context across sessions.

## What this project is

ML model that scores marketing ads using Alex Hormozi's frameworks, deployed as a Streamlit web app. 2-week timeline. Resume + learning project for the user (newer to ML, comfortable with code).

## Architecture — Path B (updated 2026-05-14)

```
Reference material (Hormozi books, frameworks)
        ↓
Persona prompt (prompts/hormozi_brain.md)
        ↓
Claude API grades each ad → JSON with 9 dimensions + overall_impact
        ↓
scikit-learn Random Forest trains on (9 dimensions → overall_impact)
        ↓
FastAPI backend (Python):
  - POST /score endpoint
  - receives ad copy
  - calls Claude API → gets 9 dimension scores
  - feeds scores to model → gets overall_impact prediction
  - returns full JSON response

React frontend (JavaScript):
  - text area for ad copy input
  - calls FastAPI /score endpoint
  - displays score, dimension breakdown, verdict
```

**Deploy:**
- Backend → Fly.io (free tier, deploys via `flyctl` CLI)
- Frontend → Vercel (free tier, deploys from GitHub)

**User has zero JS experience** — explain JS concepts as they come up, focus on how things connect not syntax.

**Video transcript** is a stretch feature for after core app is working.

## Coaching rules (updated 2026-05-15)

- Claude writes the code. User's job is to understand the system — how pieces connect, why decisions were made.
- Explain the *why* behind every meaningful code decision. Skip obvious syntax explanations.
- Focus on architecture and data flow over line-by-line syntax.
- Track which phase/step we're on. Resume cleanly across sessions.
- Direct/ruthless mentor feedback over validation.

## Division of labor

- **Claude writes and runs**: all code, scaffolding, installs, git.
- **User owns**: understanding how the system works, design decisions, what to build next.

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
