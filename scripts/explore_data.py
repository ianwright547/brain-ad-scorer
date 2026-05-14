import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/labeled/ads_labeled.csv")
print(df.shape)
print(df.head())
print(df.describe())
df['overall_impact'].hist(bins=9)
plt.title('Distribution of Overall Impact Scores')
plt.xlabel('Score')
plt.ylabel('Count')
plt.savefig('data/processed/score_distribution.png')
plt.show()