import os
import json
import time
import base64
import hashlib
from pathlib import Path
from typing import Optional

import joblib
import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app import db
from analysis.text_features import analyze_text
from analysis.image_features import analyze_image, sniff_format

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

xgb_model = xgb_data["model"] if isinstance(xgb_data, dict) else xgb_data

with open(BASE_DIR / "prompts" / "hormozi_brain.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# Cache entries are keyed on input + prompt version, so editing the prompt
# file automatically invalidates every previous evaluation.
PROMPT_VERSION = hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:12]

ACCESS_CODE = os.environ.get("ACCESS_CODE", "")

if os.environ.get("SCORER_DB"):
    db.DB_PATH = Path(os.environ["SCORER_DB"])
db.init_db()

_client = None


def get_client():
    """Create the Anthropic client on first use, not at import time.

    Tests and CI run with no API key — they mock the Claude call — and the
    app should still boot for endpoints that never touch the API.
    """
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


app = FastAPI(title="Brain Ad Scorer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScoreRequest(BaseModel):
    ad_copy: Optional[str] = Field(None, min_length=1)
    image_base64: Optional[str] = Field(None, description="Base64-encoded ad creative")
    access_code: Optional[str] = Field(None, description="Access code to authorize usage")
    business_type: Optional[str] = Field(None, description="ecommerce or lead_gen")
    product_price: Optional[float] = Field(None, description="Revenue per sale/deal")
    product_cost: Optional[float] = Field(None, description="Cost per unit (ecommerce) or 0 for services")
    close_rate: Optional[float] = Field(None, description="Lead gen only: % of leads that close (0-100)")
    monthly_budget: Optional[float] = Field(None, description="Monthly ad spend budget")


class AnalyzeRequest(BaseModel):
    ad_copy: str = Field(..., min_length=1)


def parse_claude_json(raw):
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


def call_claude(ad_copy, retries=2):
    for attempt in range(retries + 1):
        try:
            response = get_client().messages.create(
                model="claude-sonnet-4-6",
                max_tokens=5000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": f"Evaluate this ad. Return ONLY valid JSON, no other text:\n\n{ad_copy}"}],
            )
            return parse_claude_json(response.content[0].text)
        except HTTPException:
            raise
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            raise ValueError(f"Claude returned invalid response after {retries + 1} attempts: {e}")


def call_claude_vision(image_bytes, media_type, extra_copy=None, retries=2):
    """Score an ad creative (image) instead of a transcript.

    Same persona, same JSON schema — the image is sent as a base64 content
    block alongside the instruction, so all 12 dimensions get scored on the
    visual creative itself.
    """
    instruction = "Evaluate this ad creative. Return ONLY valid JSON, no other text."
    if extra_copy:
        instruction += f"\n\nThe ad's accompanying copy:\n\n{extra_copy}"

    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64.b64encode(image_bytes).decode(),
            },
        },
        {"type": "text", "text": instruction},
    ]

    for attempt in range(retries + 1):
        try:
            response = get_client().messages.create(
                model="claude-sonnet-4-6",
                max_tokens=5000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content}],
            )
            return parse_claude_json(response.content[0].text)
        except HTTPException:
            raise
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
                continue
            raise ValueError(f"Claude returned invalid response after {retries + 1} attempts: {e}")


# Industry-heuristic CPA ranges (low, high) in USD used to sanity-check
# margins. These are assumptions, not predictions — the honest version of
# "what does a Meta conversion typically cost" without pretending the model
# can forecast CPA from copy alone.
CPA_RANGES = {"ecommerce": (12, 60), "lead_gen": (25, 120)}


def calculate_profitability(request: ScoreRequest, conversion_score: float):
    """Calculate break-even economics and run verdict."""
    if not request.business_type or not request.product_price:
        return None

    if request.business_type == "ecommerce":
        cost = request.product_cost or 0
        break_even_cpa = request.product_price - cost
        metric_label = "CPA"
    else:
        close_rate = (request.close_rate or 20) / 100
        break_even_cpa = request.product_price * close_rate
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

    base_cpa_low, base_cpa_high = CPA_RANGES.get(request.business_type, CPA_RANGES["lead_gen"])

    # Conversion score 1-10 scales the CPA estimate:
    # score 8+ lands near the optimistic end, 3 and below near the pessimistic end.
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


@app.get("/health")
def health():
    return {"status": "ok", "prompt_version": PROMPT_VERSION, "model_features": len(MODEL_FEATURES)}


@app.post("/analyze")
def analyze_ad(request: AnalyzeRequest):
    """Free deterministic pre-flight check — no API call, no cost."""
    return {"text_metrics": analyze_text(request.ad_copy)}


@app.get("/history")
def get_history(limit: int = 20):
    return {"history": db.history_list(min(limit, 100))}


@app.post("/score")
def score_ad(request: ScoreRequest):
    if ACCESS_CODE and request.access_code != ACCESS_CODE:
        raise HTTPException(status_code=403, detail="Invalid access code")

    if not request.ad_copy and not request.image_base64:
        raise HTTPException(status_code=422, detail="Provide ad_copy, image_base64, or both")

    # Local analysis runs first — it's free and never blocks on the API.
    text_metrics = analyze_text(request.ad_copy) if request.ad_copy else None

    image_metrics = None
    image_bytes = None
    media_type = None
    if request.image_base64:
        try:
            image_bytes = base64.b64decode(request.image_base64)
            image_metrics = analyze_image(image_bytes)
            media_type = sniff_format(image_bytes)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # Cache lookup: hash of the exact input plus prompt version.
    payload = image_bytes if image_bytes else request.ad_copy.encode()
    if image_bytes and request.ad_copy:
        payload = image_bytes + request.ad_copy.encode()
    cache_key = db.make_cache_key(payload, PROMPT_VERSION)

    data = db.cache_get(cache_key)
    cached = data is not None
    if not cached:
        if image_bytes:
            data = call_claude_vision(image_bytes, media_type, extra_copy=request.ad_copy)
        else:
            data = call_claude(request.ad_copy)
        db.cache_put(cache_key, data)

    scores = data.get("scores", {})
    context = data.get("context", {})

    # Build feature vector for ML models (use only what they were trained on)
    feature_values = [scores.get(f, 5) for f in MODEL_FEATURES]

    rf_prediction = float(rf_model.predict([feature_values])[0])
    xgb_prediction = float(xgb_model.predict([feature_values])[0])

    conversion_score = scores.get("conversion_likelihood", scores.get("overall_impact", 5))
    profitability = calculate_profitability(request, conversion_score)

    overall_impact = scores.get("overall_impact", 5)
    if profitability:
        run_verdict = profitability["run_verdict"]
    elif overall_impact >= 7:
        run_verdict = "RUN"
    elif overall_impact >= 5:
        run_verdict = "FIX FIRST"
    else:
        run_verdict = "DON'T RUN"

    result = {
        "rf_score": round(rf_prediction, 2),
        "xgb_score": round(xgb_prediction, 2),
        "claude_score": overall_impact,
        "verdict": data.get("verdict"),
        "run_verdict": run_verdict,
        "scores": scores,
        "context": context,
        "profitability": profitability,
        "text_metrics": text_metrics,
        "image_metrics": image_metrics,
        "cached": cached,
        "quick_kill_flags": data.get("quick_kill_flags", []),
        "top_strengths": data.get("top_strengths", []),
        "top_weaknesses": data.get("top_weaknesses", []),
        "priority_fixes": data.get("priority_fixes", []),
    }

    preview = (request.ad_copy or "")[:120] or "[image only]"
    input_type = "image" if image_bytes else "text"
    db.history_add(input_type, preview, result, run_verdict, cached)

    return result
