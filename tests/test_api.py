import io
import base64
from unittest.mock import patch

from PIL import Image
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


def png_base64(size=(1080, 1080), color=(200, 60, 60)):
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_score_returns_200_with_valid_copy(mock_claude):
    response = client.post("/score", json={"ad_copy": "Buy now and save 50%!"})
    assert response.status_code == 200
    data = response.json()
    for key in ["rf_score", "xgb_score", "claude_score", "verdict", "run_verdict",
                "scores", "context", "profitability", "text_metrics", "image_metrics",
                "cached", "quick_kill_flags", "top_strengths", "priority_fixes"]:
        assert key in data
    assert data["image_metrics"] is None
    assert data["text_metrics"]["word_count"] > 0


def test_score_returns_422_with_empty_copy():
    response = client.post("/score", json={"ad_copy": ""})
    assert response.status_code == 422


def test_score_returns_422_with_no_input_at_all():
    response = client.post("/score", json={})
    assert response.status_code == 422


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_scores_contain_all_dimension_keys(mock_claude):
    response = client.post("/score", json={"ad_copy": "Limited time offer!"})
    assert response.status_code == 200
    scores = response.json()["scores"]
    for key in DIMENSION_KEYS:
        assert key in scores, f"Missing dimension key: {key}"


@patch("app.main.call_claude_vision", return_value=MOCK_CLAUDE_RESPONSE)
def test_score_accepts_image(mock_vision):
    response = client.post("/score", json={"image_base64": png_base64()})
    assert response.status_code == 200
    data = response.json()
    assert data["image_metrics"] is not None
    assert data["image_metrics"]["format"] == "image/png"
    assert data["image_metrics"]["nearest_platform"] == "Meta feed (1:1)"
    assert data["rf_score"] > 0
    mock_vision.assert_called_once()


def test_score_rejects_invalid_image():
    bad = base64.b64encode(b"definitely not an image").decode()
    response = client.post("/score", json={"image_base64": bad})
    assert response.status_code == 422


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_second_identical_request_hits_cache(mock_claude):
    body = {"ad_copy": "A very specific ad used only by the cache test."}
    first = client.post("/score", json=body).json()
    second = client.post("/score", json=body).json()

    assert first["cached"] is False
    assert second["cached"] is True
    assert second["claude_score"] == first["claude_score"]
    mock_claude.assert_called_once()  # the second request never touched the API


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


def test_analyze_is_free_and_deterministic():
    response = client.post("/analyze", json={
        "ad_copy": "Get 50% off today — guaranteed. Book your spot now!"
    })
    assert response.status_code == 200
    metrics = response.json()["text_metrics"]
    assert "guaranteed" in metrics["power_words"]
    assert "book" in metrics["cta_verbs"]
    assert metrics["flesch_reading_ease"] is not None


@patch("app.main.call_claude", return_value=MOCK_CLAUDE_RESPONSE)
def test_history_records_scored_ads(mock_claude):
    client.post("/score", json={"ad_copy": "An ad destined for the history books."})
    response = client.get("/history")
    assert response.status_code == 200
    rows = response.json()["history"]
    assert len(rows) >= 1
    assert any("history books" in r["ad_preview"] for r in rows)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert len(data["prompt_version"]) == 12
