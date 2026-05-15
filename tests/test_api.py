from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

MOCK_CLAUDE_RESPONSE = {
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
        "overall_impact": 7,
    },
    "verdict": "Average",
    "total_score": 70,
}

DIMENSION_KEYS = [
    "hook_power",
    "offer_strength",
    "persuasion_depth",
    "narrative_emotion",
    "structure_flow",
    "cta_clarity",
    "audience_targeting",
    "funnel_fit",
    "platform_optimization",
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
    assert "scores" in data


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
