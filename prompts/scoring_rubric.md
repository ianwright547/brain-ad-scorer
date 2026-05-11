# Scoring Rubric Reference

This file documents the label schema Claude uses to grade ads. The full evaluation
framework lives in `hormozi_brain.md`. This file is the quick-reference for building
`scripts/label_ads.py` and understanding the features the ML model trains on.

---

## JSON Output Schema

```json
{
  "context": {
    "business_type": "info product | ecommerce | saas | services | unknown",
    "price_point": "low ticket | mid ticket | high ticket | ultra-high | unknown",
    "audience_temperature": "cold | warm | hot | unknown",
    "funnel_position": "top | middle | bottom | unknown",
    "platform": "meta | youtube | tiktok | email | landing page | unknown",
    "ad_format": "video short | video long | static image | carousel | written copy | unknown"
  },
  "quick_kill_flags": ["array of red flags, empty if none"],
  "scores": {
    "hook_power": 7,
    "offer_strength": 6,
    "persuasion_depth": 5,
    "narrative_emotion": 8,
    "structure_flow": 7,
    "cta_clarity": 6,
    "audience_targeting": 7,
    "funnel_fit": 6,
    "platform_optimization": 5,
    "overall_impact": 7
  },
  "total_score": 64,
  "verdict": "Average",
  "top_strengths": ["strength 1", "strength 2", "strength 3"],
  "top_weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "priority_fixes": ["fix 1", "fix 2", "fix 3"]
}
```

---

## The 10 Scoring Dimensions (each 1–10)

| Dimension | What it measures | 1-3 | 7-8 | 9-10 |
|---|---|---|---|---|
| `hook_power` | Does the first 1-3s stop the scroll? | Generic, no pattern interrupt | Strong, clear audience callout | Would stop anyone mid-scroll |
| `offer_strength` | Does it pass the Hormozi Value Equation? | No offer or fails on all fronts | Strong dream outcome, some proof, risk reversal | Godfather Offer — specific, stacked, guaranteed |
| `persuasion_depth` | Cialdini principles in play | 0-1 principles, poorly executed | 3-4 principles layered effectively | 5+ working in harmony |
| `narrative_emotion` | Story + identity shift | No story, feature-dumping | Clear emotional arc, identity pull | Full Epiphany Bridge narrative |
| `structure_flow` | Hook-Body-CTA clarity | No structure, rambling | Clear Hook-Body-CTA, logical flow | Perfect — every word earns its place |
| `cta_clarity` | Is the ask single, clear, and proportional? | No CTA or multiple competing CTAs | Clear, specific, funnel-aligned | Compelling with urgency + zero friction |
| `audience_targeting` | Does it speak to one specific person? | Could be for anyone | Clear callout, right language, calibrated awareness | Laser-targeted — feels made for exactly them |
| `funnel_fit` | Right message for traffic temperature? | Wrong ask for the relationship | Well-matched to funnel position | Perfect calibration |
| `platform_optimization` | Native to the platform it runs on? | Ignores platform norms | Well-optimized | Feels like it belongs in the feed |
| `overall_impact` | Expert's final verdict | Wouldn't make anyone pause | Should perform well with right audience | Potential winner that could scale |

---

## Verdict Tiers

| Total Score | Verdict | Meaning |
|---|---|---|
| 90–100 | Exceptional | Ship it. Winner potential. Minor tweaks only. |
| 75–89 | Strong | Solid, worth testing with optimizations. |
| 60–74 | Average | Will probably break even or underperform. Needs work. |
| 40–59 | Weak | Fundamental issues. Major rework needed. |
| Below 40 | Kill It | Start over. Structural failures that can't be patched. |

---

## How This Maps to the ML Model (Phase 3)

**Features (X):** `hook_power`, `offer_strength`, `persuasion_depth`, `narrative_emotion`,
`structure_flow`, `cta_clarity`, `audience_targeting`, `funnel_fit`, `platform_optimization`

**Target (y):** `overall_impact`

The model learns which dimensions, and in what combination, drive the expert's final verdict.
This is Hormozi's weighting function — not pixel analysis.

Context fields and text fields (`quick_kill_flags`, `top_strengths`, etc.) are NOT ML features.
They are used by the Streamlit app to display explanations.
