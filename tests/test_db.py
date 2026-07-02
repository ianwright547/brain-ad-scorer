from app import db


def test_cache_roundtrip(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)

    key = db.make_cache_key(b"some ad copy", "v1")
    assert db.cache_get(key, path) is None

    response = {"scores": {"overall_impact": 7}, "verdict": "Strong"}
    db.cache_put(key, response, path)
    assert db.cache_get(key, path) == response


def test_cache_key_changes_with_prompt_version():
    payload = b"identical ad copy"
    assert db.make_cache_key(payload, "v1") != db.make_cache_key(payload, "v2")


def test_cache_key_changes_with_payload():
    assert db.make_cache_key(b"ad one", "v1") != db.make_cache_key(b"ad two", "v1")


def test_history_records_and_orders(tmp_path):
    path = tmp_path / "test.db"
    db.init_db(path)

    db.history_add("text", "first ad", {"claude_score": 6, "rf_score": 6.1, "xgb_score": 5.9},
                   "FIX FIRST", cached=False, db_path=path)
    db.history_add("image", "[image only]", {"claude_score": 8, "rf_score": 7.8, "xgb_score": 8.2},
                   "RUN", cached=True, db_path=path)

    rows = db.history_list(limit=10, db_path=path)
    assert len(rows) == 2
    assert rows[0]["input_type"] == "image"  # newest first
    assert rows[0]["cached"] == 1
    assert rows[1]["ad_preview"] == "first ad"
    assert rows[1]["run_verdict"] == "FIX FIRST"
