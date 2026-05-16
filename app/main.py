from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import joblib
import anthropic
import json
import numpy as np
from dotenv import load_dotenv
import os
import time

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

rf_data = joblib.load(BASE_DIR / "models" / "ad_scorer_rf.pkl")
xgb_data = joblib.load(BASE_DIR / "models" / "ad_scorer_xgb.pkl")

# Handle both old format (bare model) and new format (dict with meta)
if isinstance(rf_data, dict):
    rf_model = rf_data["model"]
    MODEL_FEATURES = rf_data["meta"]["features"]
else:
    rf_model = rf_data
    MODEL_FEATURES = [
        'hook_power', 'offer_strength', 'persuasion_depth', 'narrative_emotion',
        'structure_flow', 'cta_clarity', 'audience_targeting', 'funnel_fit',
        'platform_optimization',
    ]

if isinstance(xgb_data, dict):
    xgb_model = xgb_data["model"]
else:
    xgb_model = xgb_data

with open(BASE_DIR / "prompts" / "hormozi_brain.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ACCESS_CODE = os.environ.get("ACCESS_CODE", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALL_SCORE_FEATURES = [
    'hook_power', 'offer_strength', 'persuasion_depth', 'narrative_emotion',
    'structure_flow', 'cta_clarity', 'audience_targeting', 'funnel_fit',
    'platform_optimization', 'conversion_likelihood', 'message_market_match',
    'ad_type_execution',
]


class ScoreRequest(BaseModel):
    ad_copy: str = Field(..., min_length=1)
    access_code: Optional[str] = Field(None, description="Access code to authorize usage")
    business_type: Optional[str] = Field(None, description="ecommerce or lead_gen")
    product_price: Optional[float] = Field(None, description="Revenue per sale/deal")
    product_cost: Optional[float] = Field(None, description="Cost per unit (ecommerce) or 0 for services")
    close_rate: Optional[float] = Field(None, description="Lead gen only: % of leads that close (0-100)")
    monthly_budget: Optional[float] = Field(None, description="Monthly ad spend budget")


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


def calculate_profitability(request: ScoreRequest, conversion_score: float):
    """Calculate break-even economics and run verdict."""
    if not request.business_type or not request.product_price:
        return None

    if request.business_type == "ecommerce":
        cost = request.product_cost or 0
        profit_per_sale = request.product_price - cost
        break_even_cpa = profit_per_sale
        metric_label = "CPA"
    else:
        close_rate = (request.close_rate or 20) / 100
        profit_per_deal = request.product_price
        break_even_cpl = profit_per_deal * close_rate
        break_even_cpa = break_even_cpl
        metric_label = "CPL"

    if break_even_cpa <= 0:
        return {
            "viable": False,
            "reason": "Negative margins — you lose money on every sale regardless of ad performance.",
            "break_even_cpa": 0,
            "metric_label": metric_label,
            "run_verdict": "DON'T RUN",
            "monthly_budget": request.monthly_budget,
        }

    # Estimate realistic CPA range based on conversion score
    # Higher conversion_likelihood = lower expected CPA
    # Base assumption: average Meta CPA for lead gen is ~$30-80, ecommerce ~$15-50
    if request.business_type == "ecommerce":
        base_cpa_low, base_cpa_high = 12, 60
    else:
        base_cpa_low, base_cpa_high = 25, 120

    # Conversion score 1-10 scales the CPA estimate
    # Score 8+ = optimistic end, Score 3- = pessimistic end
    score_factor = (10 - conversion_score) / 9  # 0 (best) to 1 (worst)
    estimated_cpa_low = base_cpa_low + (base_cpa_high - base_cpa_low) * score_factor * 0.5
    estimated_cpa_high = base_cpa_low + (base_cpa_high - base_cpa_low) * score_factor * 1.2

    viable = estimated_cpa_low < break_even_cpa
    margin_of_safety = (break_even_cpa - estimated_cpa_low) / break_even_cpa if break_even_cpa > 0 else 0

    if not viable:
        run_verdict = "DON'T RUN"
        reason = f"Estimated {metric_label} (${estimated_cpa_low:.0f}-${estimated_cpa_high:.0f}) likely exceeds your break-even of ${break_even_cpa:.0f}. The ad quality isn't strong enough to overcome tight margins."
    elif margin_of_safety < 0.2:
        run_verdict = "FIX FIRST"
        reason = f"Tight margins. Break-even {metric_label} is ${break_even_cpa:.0f}, estimated {metric_label} is ${estimated_cpa_low:.0f}-${estimated_cpa_high:.0f}. Could work but leaves little room for error. Fix the weak dimensions first."
    else:
        run_verdict = "RUN"
        reason = f"Economics work. Break-even {metric_label} is ${break_even_cpa:.0f}, estimated {metric_label} is ${estimated_cpa_low:.0f}-${estimated_cpa_high:.0f}. Good margin of safety."

    monthly_conversions = None
    if request.monthly_budget and estimated_cpa_low > 0:
        monthly_conversions = {
            "optimistic": int(request.monthly_budget / estimated_cpa_low),
            "pessimistic": int(request.monthly_budget / estimated_cpa_high) if estimated_cpa_high > 0 else 0,
        }

    return {
        "viable": viable,
        "reason": reason,
        "break_even_cpa": round(break_even_cpa, 2),
        "estimated_cpa_range": [round(estimated_cpa_low, 2), round(estimated_cpa_high, 2)],
        "metric_label": metric_label,
        "margin_of_safety": round(margin_of_safety * 100, 1),
        "run_verdict": run_verdict,
        "monthly_budget": request.monthly_budget,
        "monthly_conversions": monthly_conversions,
    }


@app.post("/score")
def score_ad(request: ScoreRequest):
    if ACCESS_CODE and request.access_code != ACCESS_CODE:
        raise HTTPException(status_code=403, detail="Invalid access code")

    data = call_claude(request.ad_copy)
    scores = data.get("scores", {})
    context = data.get("context", {})

    # Build feature vector for ML models (use only what they were trained on)
    feature_values = [scores.get(f, 5) for f in MODEL_FEATURES]

    rf_prediction = float(rf_model.predict([feature_values])[0])
    xgb_prediction = float(xgb_model.predict([feature_values])[0])

    # Profitability assessment
    conversion_score = scores.get("conversion_likelihood", scores.get("overall_impact", 5))
    profitability = calculate_profitability(request, conversion_score)

    # Determine overall run verdict
    overall_impact = scores.get("overall_impact", 5)
    if profitability:
        run_verdict = profitability["run_verdict"]
    elif overall_impact >= 7:
        run_verdict = "RUN"
    elif overall_impact >= 5:
        run_verdict = "FIX FIRST"
    else:
        run_verdict = "DON'T RUN"

    return {
        "rf_score": round(rf_prediction, 2),
        "xgb_score": round(xgb_prediction, 2),
        "claude_score": overall_impact,
        "verdict": data.get("verdict"),
        "run_verdict": run_verdict,
        "scores": scores,
        "context": context,
        "profitability": profitability,
        "quick_kill_flags": data.get("quick_kill_flags", []),
        "top_strengths": data.get("top_strengths", []),
        "top_weaknesses": data.get("top_weaknesses", []),
        "priority_fixes": data.get("priority_fixes", []),
    }
