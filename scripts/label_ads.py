import anthropic
import pandas as pd
from dotenv import load_dotenv
import time
import os
import json

load_dotenv()
api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

# Load the scoring system prompt from file
with open("prompts/hormozi_brain.md", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# 90 ads spread across quality tiers to give the model full score range
QUALITY_TIERS = (
    ["weak"] * 18 +
    ["average"] * 36 +
    ["strong"] * 18 +
    ["exceptional"] * 18
)

BUSINESS_TYPES = ["fitness coaching", "SaaS", "e-commerce", "info product", "agency services"]
PLATFORMS = ["Meta (Facebook/Instagram)", "YouTube"]


def generate_ad(quality_tier, business_type, platform):
    prompt = f"""Write a {quality_tier} quality ad for a {business_type} business to run on {platform}.

Quality guidance:
- weak: generic hook, vague offer, no CTA, no social proof, feature-dumping
- average: decent hook, some offer clarity, basic CTA, minimal proof
- strong: strong hook, clear offer, compelling CTA, social proof, emotional arc
- exceptional: pattern-interrupt hook, Godfather offer, layered persuasion, full narrative arc, irresistible CTA

Return ONLY the ad copy. No explanations or labels."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def score_ad(ad_copy):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=5000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Evaluate this ad. Return ONLY valid JSON, no other text:\n\n{ad_copy}"}]
    )
    return response.content[0].text


def parse_scores(json_text):
    # Strip markdown code fences if Claude wraps the JSON
    cleaned = json_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
        scores = data.get("scores", {})
        context = data.get("context", {})
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
            "business_type": context.get("business_type"),
            "platform": context.get("platform"),
            "audience_temperature": context.get("audience_temperature"),
        }
    except json.JSONDecodeError:
        print(f"  → JSON parse failed. Raw response: {json_text[:200]}")
        return None


output_path = "data/labeled/ads_labeled.csv"

if os.path.exists(output_path):
    already_saved = len(pd.read_csv(output_path))
    print(f"Resuming from row {already_saved + 1} ({already_saved} already saved)")
else:
    already_saved = 0

saved_count = already_saved

for i, quality_tier in enumerate(QUALITY_TIERS):
    if i < already_saved:
        continue
    business_type = BUSINESS_TYPES[i % len(BUSINESS_TYPES)]
    platform = PLATFORMS[i % len(PLATFORMS)]

    print(f"[{i+1}/90] {quality_tier.upper()} — {business_type} on {platform}")

    try:
        ad_copy = generate_ad(quality_tier, business_type, platform)
        time.sleep(1)
        raw_scores = score_ad(ad_copy)
        time.sleep(1)
    except Exception as e:
        print(f"  → API error: {e}. Waiting 10s and skipping.")
        time.sleep(10)
        continue

    row = parse_scores(raw_scores)
    if row:
        row["ad_copy"] = ad_copy
        row["quality_tier"] = quality_tier

        # Save each row immediately so a crash doesn't lose progress
        df_row = pd.DataFrame([row])
        write_header = not os.path.exists(output_path)
        df_row.to_csv(output_path, mode="a", header=write_header, index=False)
        saved_count += 1
        print(f"  → overall_impact: {row['overall_impact']} | verdict: {row['verdict']}")
    else:
        print("  → Skipped (parse error)")

print(f"\nDone. {saved_count} ads saved to {output_path}")
