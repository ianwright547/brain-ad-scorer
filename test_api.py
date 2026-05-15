import requests

ad = """Hook: Most PI firms won't grow in 2026 because Google Ads stops working when you try to scale.
Problem: Google brings high-intent leads, but you've hit the ceiling.
You can't just spend more without your cost per case jumping from $3,000 to $6,000+.
You're maxed out. You need more cases but Google can't deliver them without destroying your margins.
Solution: We'll beat your Google Ads campaign in the next 30 days. We give you a second pipeline of high-intent MVA cases for under $1,500 per signed case—not-at-fault, police report verified, under 12 months old. Keep your Google running. Add this on top.
Social Proof: Within 2 weeks of launching our campaign for one of our clients, they were able to sign a case valued at over $200k.
CTA: Click Learn More to see if your area is available and learn our exact pre-qualification process."""

response = requests.post("http://127.0.0.1:8000/score", json={"ad_copy": ad})
import json
print(json.dumps(response.json(), indent=2))
