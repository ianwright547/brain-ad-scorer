from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_CLAUDE_RESPONSE = {
    "context": {
        "business_type": "services",
        "price_point": "high ticket",
        "audience_temperature": "cold",
        "funnel_position": "top",
        "platform": "meta",
        "ad_format": "video short",
        "ad_style": "direct pitch",
        "niche": "marketing agency",
    },
    "scores": {
        "hook_power": 7,
        "offer_strength": 8,
        "persuasion_depth": 6,
        "narrative_emotion": 5,
        "structure_flow": 7,
        "cta_clarity": 8,
        "audience_targeting": 9,
        "funnel_fit": 7,
        "platform_optimization": 6,
        "conversion_likelihood": 7,
        "message_market_match": 8,
        "ad_type_execution": 7,
        "overall_impact": 7,
    },
    "verdict": "Strong",
    "total_score": 92,
    "quick_kill_flags": [],
    "top_strengths": ["Strong audience callout", "Clear offer", "Good proof"],
    "top_weaknesses": ["Could use more urgency", "Narrative is thin"],
    "priority_fixes": ["Add testimonial for social proof", "Tighten the hook"],
}

DIMENSION_KEYS = [
    "hook_power", "offer_strength", "persuasion_depth", "narrative_emotion",
    "structure_flow", "cta_clarity", "audience_targeting", "funnel_fit",
    "platform_optimization", "conversion_likelihood", "message_market_match",
    "ad_type_execution",
]


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_score_returns_200_with_valid_copy(mock_claude):
    response = client.post("/score", json={"ad_copy": "Buy now and save 50%!"})
    assert response.status_code == 200
    data = response.json()
    assert "rf_score" in data
    assert "xgb_score" in data
    assert "claude_score" in data
    assert "verdict" in data
    assert "run_verdict" in data
    assert "scores" in data
    assert "context" in data
    assert "profitability" in data
    assert "quick_kill_flags" in data
    assert "top_strengths" in data
    assert "priority_fixes" in data


def test_score_returns_422_with_empty_copy():
    response = client.post("/score", json={"ad_copy": ""})
    assert response.status_code == 422


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_scores_contain_all_dimension_keys(mock_claude):
    response = client.post("/score", json={"ad_copy": "Limited time offer!"})
    assert response.status_code == 200
    scores = response.json()["scores"]
    for key in DIMENSION_KEYS:
        assert key in scores, f"Missing dimension key: {key}"


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_profitability_with_ecommerce_inputs(mock_claude):
    response = client.post("/score", json={
        "ad_copy": "Buy our product!",
        "business_type": "ecommerce",
        "product_price": 49.99,
        "product_cost": 15.00,
        "monthly_budget": 3000,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["profitability"] is not None
    assert "break_even_cpa" in data["profitability"]
    assert "run_verdict" in data["profitability"]
    assert data["profitability"]["metric_label"] == "CPA"


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_profitability_with_lead_gen_inputs(mock_claude):
    response = client.post("/score", json={
        "ad_copy": "Book a free strategy call!",
        "business_type": "lead_gen",
        "product_price": 5000,
        "close_rate": 20,
        "monthly_budget": 5000,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["profitability"] is not None
    assert data["profitability"]["metric_label"] == "CPL"
    assert data["profitability"]["break_even_cpa"] == 1000.0


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_no_profitability_without_business_inputs(mock_claude):
    response = client.post("/score", json={"ad_copy": "Just score this ad"})
    assert response.status_code == 200
    data = response.json()
    assert data["profitability"] is None
    assert data["run_verdict"] == "RUN"  # overall_impact is 7, so RUN
