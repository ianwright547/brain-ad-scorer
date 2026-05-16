import anthropic
import pandas as pd
from dotenv import load_dotenv
import time
import os
import json
import re

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

with open("prompts/hormozi_brain.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

FEATURES = [
    "hook_power", "offer_strength", "persuasion_depth", "narrative_emotion",
    "structure_flow", "cta_clarity", "audience_targeting", "funnel_fit",
    "platform_optimization", "conversion_likelihood", "message_market_match",
    "ad_type_execution", "overall_impact",
]

CONTEXT_FIELDS = [
    "business_type", "price_point", "audience_temperature",
    "funnel_position", "platform", "ad_format", "ad_style", "niche",
]


def strip_timestamps(text):
    """Remove timestamp lines like '00:00 - 00:05' from transcripts."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\d{2}:\d{2}\s*-\s*\d{2}:\d{2}$", stripped):
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def score_ad(ad_copy):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Evaluate this ad transcript. Return ONLY valid JSON, no other text:\n\n{ad_copy}"
        }]
    )
    return response.content[0].text


def parse_scores(json_text):
    cleaned = json_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
        scores = data.get("scores", {})
        context = data.get("context", {})

        row = {}
        for f in FEATURES:
            row[f] = scores.get(f)
        for f in CONTEXT_FIELDS:
            row[f] = context.get(f, "unknown")

        row["total_score"] = data.get("total_score")
        row["verdict"] = data.get("verdict")
        row["quick_kill_flags"] = json.dumps(data.get("quick_kill_flags", []))
        row["top_strengths"] = json.dumps(data.get("top_strengths", []))
        row["top_weaknesses"] = json.dumps(data.get("top_weaknesses", []))
        row["priority_fixes"] = json.dumps(data.get("priority_fixes", []))

        return row
    except json.JSONDecodeError:
        print(f"  JSON parse failed. Raw: {json_text[:200]}")
        return None


with open("data/raw/real_ads.txt", "r", encoding="utf-8") as f:
    raw = f.read()

ads = [ad.strip() for ad in raw.split("--- AD ---") if ad.strip()]
ads = [ad for ad in ads if not ad.startswith("PASTE YOUR")]

if not ads:
    print("No real ads found. Open data/raw/real_ads.txt and paste your ads separated by --- AD ---")
    exit()

print(f"Found {len(ads)} real ads to score.\n")

output_path = "data/labeled/real_ads_labeled.csv"

if os.path.exists(output_path):
    existing = pd.read_csv(output_path)
    print(f"Existing labeled real ads: {len(existing)} rows")
    start_from = len(existing)
else:
    existing = pd.DataFrame()
    start_from = 0

if start_from >= len(ads):
    print("All ads already labeled. Delete the CSV to re-label.")
    exit()

print(f"Starting from ad #{start_from + 1}\n")

scored = 0
for i, ad_copy in enumerate(ads[start_from:], start=start_from):
    clean_copy = strip_timestamps(ad_copy)
    print(f"[{i+1}/{len(ads)}] Scoring ({len(clean_copy)} chars)...")

    try:
        raw_scores = score_ad(clean_copy)
        time.sleep(1.5)
    except Exception as e:
        print(f"  API error: {e}. Skipping.")
        continue

    row = parse_scores(raw_scores)
    if row:
        row["ad_copy"] = clean_copy
        row["quality_tier"] = "real"

        df_row = pd.DataFrame([row])
        if scored == 0 and start_from == 0:
            df_row.to_csv(output_path, mode="w", header=True, index=False)
        else:
            df_row.to_csv(output_path, mode="a", header=False, index=False)
        scored += 1
        print(f"  overall_impact: {row['overall_impact']} | verdict: {row['verdict']} | niche: {row.get('niche', '?')}")
    else:
        print(f"  Skipped (parse error)")

print(f"\nDone. {scored} real ads scored and saved to {output_path}")
print(f"Total real ads labeled: {start_from + scored}")
