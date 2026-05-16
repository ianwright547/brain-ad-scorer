import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
import json
import os

SCORE_FEATURES = [
    'hook_power', 'offer_strength', 'persuasion_depth', 'narrative_emotion',
    'structure_flow', 'cta_clarity', 'audience_targeting', 'funnel_fit',
    'platform_optimization', 'conversion_likelihood', 'message_market_match',
    'ad_type_execution',
]

TARGET = 'overall_impact'

# Load real ads (new format with 12 features + context)
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
    exit()

df = pd.concat(frames, ignore_index=True)
print(f"Total dataset: {len(df)} rows")

# Drop rows missing new features (legacy data without the 3 new dimensions)
df_full = df.dropna(subset=SCORE_FEATURES + [TARGET])
print(f"Rows with all 12 features: {len(df_full)}")

if len(df_full) < 20:
    print("\nNot enough data with all 12 features. Falling back to 9-feature training.")
    SCORE_FEATURES = [
        'hook_power', 'offer_strength', 'persuasion_depth', 'narrative_emotion',
        'structure_flow', 'cta_clarity', 'audience_targeting', 'funnel_fit',
        'platform_optimization',
    ]
    df_full = df.dropna(subset=SCORE_FEATURES + [TARGET])
    print(f"Rows with 9 features: {len(df_full)}")

X = df_full[SCORE_FEATURES].astype(float)
y = df_full[TARGET].astype(float)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

xgb = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=4, random_state=42)
xgb.fit(X_train, y_train)

# --- 5-Fold Cross-Validation ---
print("\n=== 5-Fold Cross-Validation ===")

rf_cv_mae = cross_val_score(rf, X, y, cv=5, scoring='neg_mean_absolute_error')
rf_cv_r2 = cross_val_score(rf, X, y, cv=5, scoring='r2')
xgb_cv_mae = cross_val_score(xgb, X, y, cv=5, scoring='neg_mean_absolute_error')
xgb_cv_r2 = cross_val_score(xgb, X, y, cv=5, scoring='r2')

rf_cv_mae_vals = -rf_cv_mae
xgb_cv_mae_vals = -xgb_cv_mae

print(f"Random Forest  — CV MAE: {rf_cv_mae_vals.mean():.2f} +/- {rf_cv_mae_vals.std():.2f}, CV R²: {rf_cv_r2.mean():.2f} +/- {rf_cv_r2.std():.2f}")
print(f"XGBoost        — CV MAE: {xgb_cv_mae_vals.mean():.2f} +/- {xgb_cv_mae_vals.std():.2f}, CV R²: {xgb_cv_r2.mean():.2f} +/- {xgb_cv_r2.std():.2f}")
print()

# --- Holdout Set Evaluation ---
rf_pred = rf.predict(X_test)
xgb_pred = xgb.predict(X_test)

rf_mae = mean_absolute_error(y_test, rf_pred)
rf_r2 = r2_score(y_test, rf_pred)
xgb_mae = mean_absolute_error(y_test, xgb_pred)
xgb_r2 = r2_score(y_test, xgb_pred)

print("=== Holdout Set Comparison ===")
print(f"Random Forest  — MAE: {rf_mae:.2f}, R²: {rf_r2:.2f}")
print(f"XGBoost        — MAE: {xgb_mae:.2f}, R²: {xgb_r2:.2f}")

within_1 = np.mean(np.abs(rf_pred - y_test) <= 1.0) * 100
within_05 = np.mean(np.abs(rf_pred - y_test) <= 0.5) * 100
print(f"\nRandom Forest agreed with Claude within 1 point on {within_1:.0f}% of test ads")
print(f"Random Forest agreed with Claude within 0.5 points on {within_05:.0f}% of test ads")

metrics = {
    "features_used": len(SCORE_FEATURES),
    "feature_names": SCORE_FEATURES,
    "total_samples": len(df_full),
    "random_forest": {"mae": round(rf_mae, 3), "r2": round(rf_r2, 3)},
    "xgboost": {"mae": round(xgb_mae, 3), "r2": round(xgb_r2, 3)},
    "cross_validation": {
        "folds": 5,
        "random_forest": {
            "mae_mean": round(float(rf_cv_mae_vals.mean()), 3),
            "mae_std": round(float(rf_cv_mae_vals.std()), 3),
            "r2_mean": round(float(rf_cv_r2.mean()), 3),
            "r2_std": round(float(rf_cv_r2.std()), 3),
        },
        "xgboost": {
            "mae_mean": round(float(xgb_cv_mae_vals.mean()), 3),
            "mae_std": round(float(xgb_cv_mae_vals.std()), 3),
            "r2_mean": round(float(xgb_cv_r2.mean()), 3),
            "r2_std": round(float(xgb_cv_r2.std()), 3),
        },
    },
    "agreement_within_1pt": round(within_1, 1),
    "agreement_within_0.5pt": round(within_05, 1),
    "test_size": len(y_test),
    "train_size": len(y_train),
}
with open("data/processed/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

rf_imp = pd.Series(rf.feature_importances_, index=SCORE_FEATURES).sort_values()
rf_imp.plot(kind='barh', ax=axes[0], color='#0969da')
axes[0].set_title('Random Forest — Feature Importance', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Importance')

xgb_imp = pd.Series(xgb.feature_importances_, index=SCORE_FEATURES).sort_values()
xgb_imp.plot(kind='barh', ax=axes[1], color='#cf222e')
axes[1].set_title('XGBoost — Feature Importance', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Importance')

plt.tight_layout()
plt.savefig('data/processed/feature_importance.png', dpi=150, bbox_inches='tight')
print("\nFeature importance chart saved to data/processed/feature_importance.png")

fig2, axes2 = plt.subplots(1, 2, figsize=(12, 5))

axes2[0].scatter(y_test, rf_pred, alpha=0.6, color='#0969da', edgecolors='white', linewidth=0.5)
axes2[0].plot([1, 10], [1, 10], '--', color='#656d76')
axes2[0].set_xlabel('Claude Score (actual)')
axes2[0].set_ylabel('Model Prediction')
axes2[0].set_title(f'Random Forest (MAE={rf_mae:.2f})', fontsize=12, fontweight='bold')

axes2[1].scatter(y_test, xgb_pred, alpha=0.6, color='#cf222e', edgecolors='white', linewidth=0.5)
axes2[1].plot([1, 10], [1, 10], '--', color='#656d76')
axes2[1].set_xlabel('Claude Score (actual)')
axes2[1].set_ylabel('Model Prediction')
axes2[1].set_title(f'XGBoost (MAE={xgb_mae:.2f})', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('data/processed/model_comparison.png', dpi=150, bbox_inches='tight')
print("Model comparison chart saved to data/processed/model_comparison.png")

# Save with feature list metadata so backend knows what to expect
model_meta = {"features": SCORE_FEATURES}
joblib.dump({"model": rf, "meta": model_meta}, 'models/ad_scorer_rf.pkl')
joblib.dump({"model": xgb, "meta": model_meta}, 'models/ad_scorer_xgb.pkl')
print("\nModels saved to models/")
print(f"Training complete. {len(SCORE_FEATURES)} features used.")
