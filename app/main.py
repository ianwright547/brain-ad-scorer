from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import anthropic
import json
import numpy as np
from dotenv import load_dotenv
import os
import time

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

rf_model = joblib.load(BASE_DIR / "models" / "ad_scorer_rf.pkl")
xgb_model = joblib.load(BASE_DIR / "models" / "ad_scorer_xgb.pkl")

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

FEATURES = [
    'hook_power', 'offer_strength', 'persuasion_depth', 'narrative_emotion',
    'structure_flow', 'cta_clarity', 'audience_targeting', 'funnel_fit',
    'platform_optimization',
]


class ScoreRequest(BaseModel):
    ad_copy: str = Field(..., min_length=1)


def call_claude(ad_copy, retries=2):
    for attempt in range(retries + 1):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=5000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Evaluate this ad. Return ONLY valid JSON, no other text:\n\n{ad_copy}"}]
            )
            raw = response.content[0].text
            cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return json.loads(cleaned)
        except (json.JSONDecodeError, Exception) as e:
            if attempt < retries:
                time.sleep(1)
                continue
            raise ValueError(f"Claude returned invalid response after {retries + 1} attempts: {e}")


@app.post("/score")
def score_ad(request: ScoreRequest):
    data = call_claude(request.ad_copy)
    scores = data.get("scores", {})

    feature_values = [scores.get(f, 5) for f in FEATURES]

    rf_prediction = float(rf_model.predict([feature_values])[0])
    xgb_prediction = float(xgb_model.predict([feature_values])[0])

    return {
        "rf_score": round(rf_prediction, 2),
        "xgb_score": round(xgb_prediction, 2),
        "claude_score": scores.get("overall_impact"),
        "verdict": data.get("verdict"),
        "scores": scores,
    }
