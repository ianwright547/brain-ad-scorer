"""Train and evaluate the ad-scoring models.

Four models get compared, not two. The dummy regressor (always predicts
the mean) is the floor — anything that can't beat it learned nothing.
Linear regression tests whether the dimension-to-score relationship is
just a weighted sum; the tree models only earn their complexity if they
beat it.
"""

import os
import json

import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.inspection import permutation_importance
from xgboost import XGBRegressor

SCORE_FEATURES = [
    'hook_power', 'offer_strength', 'persuasion_depth', 'narrative_emotion',
    'structure_flow', 'cta_clarity', 'audience_targeting', 'funnel_fit',
    'platform_optimization', 'conversion_likelihood', 'message_market_match',
    'ad_type_execution',
]

TARGET = 'overall_impact'

real_path = "data/labeled/real_ads_labeled.csv"
legacy_path = "data/labeled/ads_labeled.csv"

frames = []

if os.path.exists(real_path):
    real_df = pd.read_csv(real_path)
    print(f"Real ads: {len(real_df)} rows")
    frames.append(real_df)

if os.path.exists(legacy_path):
    legacy_df = pd.read_csv(legacy_path)
    # Legacy data has 9 features — fill new dimensions with NaN
    for col in SCORE_FEATURES:
        if col not in legacy_df.columns:
            legacy_df[col] = np.nan
    print(f"Legacy synthetic ads: {len(legacy_df)} rows")
    frames.append(legacy_df)

if not frames:
    print("No training data found. Run label_real_ads.py first.")
    raise SystemExit(1)

df = pd.concat(frames, ignore_index=True)
print(f"Total dataset: {len(df)} rows")

# Drop rows missing new features (legacy data without the 3 new dimensions)
df_full = df.dropna(subset=SCORE_FEATURES + [TARGET])
print(f"Rows with all 12 features: {len(df_full)}")

if len(df_full) < 20:
    print("\nNot enough data with all 12 features. Falling back to 9-feature training.")
    SCORE_FEATURES = SCORE_FEATURES[:9]
    df_full = df.dropna(subset=SCORE_FEATURES + [TARGET])
    print(f"Rows with 9 features: {len(df_full)}")

X = df_full[SCORE_FEATURES].astype(float)
y = df_full[TARGET].astype(float)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

MODELS = {
    "dummy_mean": DummyRegressor(strategy="mean"),
    "linear": LinearRegression(),
    "random_forest": RandomForestRegressor(n_estimators=100, random_state=42),
    "xgboost": XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42),
}

results = {}
predictions = {}

print("\n=== Model Comparison (5-fold CV + holdout) ===")
print(f"{'model':<15} {'CV MAE':>14} {'CV R²':>14} {'holdout MAE':>12} {'holdout R²':>11}")

for name, model in MODELS.items():
    cv_mae = -cross_val_score(model, X, y, cv=5, scoring='neg_mean_absolute_error')
    cv_r2 = cross_val_score(model, X, y, cv=5, scoring='r2')

    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    predictions[name] = pred

    holdout_mae = mean_absolute_error(y_test, pred)
    holdout_r2 = r2_score(y_test, pred)

    results[name] = {
        "cv_mae_mean": round(float(cv_mae.mean()), 3),
        "cv_mae_std": round(float(cv_mae.std()), 3),
        "cv_r2_mean": round(float(cv_r2.mean()), 3),
        "cv_r2_std": round(float(cv_r2.std()), 3),
        "holdout_mae": round(holdout_mae, 3),
        "holdout_r2": round(holdout_r2, 3),
    }

    print(f"{name:<15} {cv_mae.mean():>6.2f} ± {cv_mae.std():<5.2f} "
          f"{cv_r2.mean():>6.2f} ± {cv_r2.std():<5.2f} "
          f"{holdout_mae:>12.2f} {holdout_r2:>11.2f}")

rf = MODELS["random_forest"]
xgb = MODELS["xgboost"]
rf_pred = predictions["random_forest"]

within_1 = np.mean(np.abs(rf_pred - y_test) <= 1.0) * 100
within_05 = np.mean(np.abs(rf_pred - y_test) <= 0.5) * 100
print(f"\nRandom Forest agreed with Claude within 1 point on {within_1:.0f}% of test ads")
print(f"Random Forest agreed with Claude within 0.5 points on {within_05:.0f}% of test ads")

# Permutation importance: shuffle one feature at a time and measure how much
# the score degrades. Unlike impurity-based importance, it's computed on
# held-out data and doesn't inflate features just because trees split on
# them often.
perm = permutation_importance(rf, X_test, y_test, n_repeats=30, random_state=42,
                              scoring='neg_mean_absolute_error')
perm_series = pd.Series(perm.importances_mean, index=SCORE_FEATURES).sort_values()

print("\n=== Permutation Importance (Random Forest, holdout) ===")
for feat, imp in perm_series.sort_values(ascending=False).items():
    print(f"  {feat:<24} {imp:+.3f}")

metrics = {
    "features_used": len(SCORE_FEATURES),
    "feature_names": SCORE_FEATURES,
    "total_samples": len(df_full),
    "train_size": len(y_train),
    "test_size": len(y_test),
    "models": results,
    "agreement_within_1pt": round(within_1, 1),
    "agreement_within_0.5pt": round(within_05, 1),
    "permutation_importance": {k: round(float(v), 4) for k, v in perm_series.items()},
}
with open("data/processed/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

# --- Charts ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

perm_series.plot(kind='barh', ax=axes[0], color='#0969da')
axes[0].set_title('Permutation Importance (Random Forest)', fontsize=12, fontweight='bold')
axes[0].set_xlabel('MAE increase when shuffled')

xgb_imp = pd.Series(xgb.feature_importances_, index=SCORE_FEATURES).sort_values()
xgb_imp.plot(kind='barh', ax=axes[1], color='#cf222e')
axes[1].set_title('XGBoost — Impurity Importance', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Importance')

plt.tight_layout()
plt.savefig('data/processed/feature_importance.png', dpi=150, bbox_inches='tight')
print("\nFeature importance chart saved to data/processed/feature_importance.png")

fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))

rf_mae = results["random_forest"]["holdout_mae"]
xgb_mae = results["xgboost"]["holdout_mae"]

axes2[0].scatter(y_test, rf_pred, alpha=0.6, color='#0969da', edgecolors='white', linewidth=0.5)
axes2[0].plot([1, 10], [1, 10], '--', color='#656d76')
axes2[0].set_xlabel('Claude Score (actual)')
axes2[0].set_ylabel('Model Prediction')
axes2[0].set_title(f'Random Forest (MAE={rf_mae:.2f})', fontsize=12, fontweight='bold')

axes2[1].scatter(y_test, predictions["xgboost"], alpha=0.6, color='#cf222e', edgecolors='white', linewidth=0.5)
axes2[1].plot([1, 10], [1, 10], '--', color='#656d76')
axes2[1].set_xlabel('Claude Score (actual)')
axes2[1].set_ylabel('Model Prediction')
axes2[1].set_title(f'XGBoost (MAE={xgb_mae:.2f})', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('data/processed/model_comparison.png', dpi=150, bbox_inches='tight')
print("Model comparison chart saved to data/processed/model_comparison.png")

# Save with feature list metadata so the backend knows what to expect
model_meta = {"features": SCORE_FEATURES}
joblib.dump({"model": rf, "meta": model_meta}, 'models/ad_scorer_rf.pkl')
joblib.dump({"model": xgb, "meta": model_meta}, 'models/ad_scorer_xgb.pkl')
print("\nModels saved to models/")
print(f"Training complete. {len(SCORE_FEATURES)} features used.")
