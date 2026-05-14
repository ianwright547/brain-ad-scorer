import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import joblib

df = pd.read_csv("data/labeled/ads_labeled.csv")
features = ['hook_power', 'offer_strength', 'persuasion_depth', 'narrative_emotion',
              'structure_flow', 'cta_clarity', 'audience_targeting', 'funnel_fit',
              'platform_optimization']
x = df[features]
y = df['overall_impact']

X_train, X_test, y_train, y_test = train_test_split(x,y,test_size=0.2,random_state=42)

model = RandomForestRegressor(n_estimators=100,random_state=42)
model.fit(X_train,y_train)

from sklearn.metrics import mean_absolute_error, r2_score

y_pred = model.predict(X_test)
mae = mean_absolute_error(y_test,y_pred)
r2 = r2_score(y_test,y_pred)

print(f"MAE: {mae:.2f}")
print(f"R2: {r2:.2f}")

importances = pd.Series(model.feature_importances_, index=features)
importances.sort_values().plot(kind='barh')
plt.title('Feature Importance')
plt.tight_layout()
plt.savefig('data/processed/feature_importance.png')
plt.show()

joblib.dump(model, 'models/ad_scorer.pkl')
print("Model saved to models/ad_scorer.pkl")
