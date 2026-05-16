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
    "ad_format": "video short | video long | static image | carousel | written copy | unknown",
    "ad_style": "direct pitch | testimonial | ugc | narrative | teaser | educational | unknown",
    "niche": "string - specific industry/market"
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
    "conversion_likelihood": 7,
    "message_market_match": 7,
    "ad_type_execution": 7,
    "overall_impact": 7
  },
  "total_score": 87,
  "verdict": "Strong",
  "top_strengths": ["strength 1", "strength 2", "strength 3"],
  "top_weaknesses": ["weakness 1", "weakness 2", "weakness 3"],
  "priority_fixes": ["fix 1", "fix 2", "fix 3"]
}
```

---

## The 13 Scoring Dimensions (each 1-10)

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
| `conversion_likelihood` | Will someone actually act after seeing this? | No momentum toward action | Good friction-to-trust ratio, clear next step | Viewer feels compelled to act immediately |
| `message_market_match` | Does messaging hit what this market actually cares about? | Generic/wrong language for the niche | Speaks the market's language, hits real triggers | Insider-level resonance — audience feels deeply understood |
| `ad_type_execution` | How well does it execute its chosen format? | Poor execution of the format it chose | Solid execution within its style | Masterful — best-in-class for this ad type |
| `overall_impact` | Expert's final verdict | Wouldn't make anyone pause | Should perform well with right audience | Potential winner that could scale |

---

## CRITICAL: Context-Relative Scoring

All dimensions are scored RELATIVE to the ad's context and job:
- A raw UGC testimonial is NOT penalized for lacking polished structure
- A 15-second retargeting teaser is NOT penalized for missing proof stacking
- A $47 product ad is NOT held to the same narrative depth standard as a $10k coaching offer
- A testimonial ad is scored on how authentic and specific it feels, not on CTA structure

The question is always: "How well does this ad do ITS job, for ITS audience, in ITS context?"

---

## Verdict Tiers (based on total_score out of 130)

| Total Score | Verdict | Meaning |
|---|---|---|
| 117-130 | Exceptional | Ship it. Winner potential. Minor tweaks only. |
| 98-116 | Strong | Solid, worth testing with optimizations. |
| 78-97 | Average | Will probably break even or underperform. Needs work. |
| 52-77 | Weak | Fundamental issues. Major rework needed. |
| Below 52 | Kill It | Start over. Structural failures that can't be patched. |

---

## How This Maps to the ML Model

**Features (X):** `hook_power`, `offer_strength`, `persuasion_depth`, `narrative_emotion`,
`structure_flow`, `cta_clarity`, `audience_targeting`, `funnel_fit`, `platform_optimization`,
`conversion_likelihood`, `message_market_match`, `ad_type_execution`

**Target (y):** `overall_impact`

The model learns which dimensions, and in what combination, drive the expert's final verdict.

Context fields (`business_type`, `niche`, `ad_style`, etc.) are used for display and
profitability analysis but not as ML features (too few samples for categorical encoding to help).

Text fields (`quick_kill_flags`, `top_strengths`, etc.) are displayed in the app for actionable feedback.
