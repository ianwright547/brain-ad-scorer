import anthropic
import pandas as pd
from dotenv import load_dotenv
import time
import os
import json

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

with open("prompts/hormozi_brain.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()


def score_ad(ad_copy):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Evaluate this ad. Return ONLY valid JSON, no other text:\n\n{ad_copy}"}]
    )
    return response.content[0].text


def parse_scores(json_text):
    cleaned = json_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
        scores = data.get("scores", {})
        return {
            "hook_power": scores.get("hook_power"),
            "offer_strength": scores.get("offer_strength"),
            "persuasion_depth": scores.get("persuasion_depth"),
            "narrative_emotion": scores.get("narrative_emotion"),
            "structure_flow": scores.get("structure_flow"),
            "cta_clarity": scores.get("cta_clarity"),
            "audience_targeting": scores.get("audience_targeting"),
            "funnel_fit": scores.get("funnel_fit"),
            "platform_optimization": scores.get("platform_optimization"),
            "overall_impact": scores.get("overall_impact"),
            "total_score": data.get("total_score"),
            "verdict": data.get("verdict"),
        }
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

output_path = "data/labeled/ads_labeled.csv"
existing = pd.read_csv(output_path) if os.path.exists(output_path) else pd.DataFrame()
print(f"Existing dataset: {len(existing)} rows")

scored = 0
for i, ad_copy in enumerate(ads):
    print(f"[{i+1}/{len(ads)}] Scoring ({len(ad_copy)} chars)...")

    try:
        raw_scores = score_ad(ad_copy)
        time.sleep(1)
    except Exception as e:
        print(f"  API error: {e}. Skipping.")
        continue

    row = parse_scores(raw_scores)
    if row:
        row["ad_copy"] = ad_copy
        row["quality_tier"] = "real"
        row["business_type"] = ""
        row["platform"] = ""
        row["audience_temperature"] = ""

        df_row = pd.DataFrame([row])
        df_row.to_csv(output_path, mode="a", header=False, index=False)
        scored += 1
        print(f"  overall_impact: {row['overall_impact']} | verdict: {row['verdict']}")
    else:
        print(f"  Skipped (parse error)")

print(f"\nDone. {scored} real ads scored and appended to {output_path}")
print(f"Total dataset: {len(existing) + scored} rows")
print("\nNext step: run scripts/train_model.py to retrain with the new data.")
