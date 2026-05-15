from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import anthropic
import json
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

model = joblib.load(BASE_DIR / "models" / "ad_scorer.pkl")

with open(BASE_DIR / "prompts" / "hormozi_brain.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScoreRequest(BaseModel):
    ad_copy: str


@app.post("/score")
def score_ad(request: ScoreRequest):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Evaluate this ad. Return ONLY valid JSON, no other text:\n\n{request.ad_copy}"}]
    )
    raw = response.content[0].text

    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(cleaned)
    scores = data.get("scores", {})

    features = [
        scores.get("hook_power"),
        scores.get("offer_strength"),
        scores.get("persuasion_depth"),
        scores.get("narrative_emotion"),
        scores.get("structure_flow"),
        scores.get("cta_clarity"),
        scores.get("audience_targeting"),
        scores.get("funnel_fit"),
        scores.get("platform_optimization"),
    ]

    overall_impact = model.predict([features])[0]

    return {
        "overall_impact": round(float(overall_impact), 2),
        "claude_score": scores.get("overall_impact"),
        "verdict": data.get("verdict"),
        "scores": scores,
    }
