"""
Run this script ONCE after retraining your fertilizer model.
It saves the LabelEncoder and column order needed by the Flask backend.

Place this file next to your Fertlizer_prediction.ipynb and run it
in the same environment where you trained the model.
"""

import pandas as pd
import pickle
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# ── 1. Load data (same as your notebook) ──────────────────────────────────────
df = pd.read_csv("Crop and fertilizer dataset (1).csv")

X = df.drop(["Fertilizer", "Link"], axis=1)
X = pd.get_dummies(X)

le = LabelEncoder()
y = le.fit_transform(df["Fertilizer"])

# ── 2. Train model ─────────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# ── 3. Save ALL three artifacts ────────────────────────────────────────────────
with open("fertilizer_recommendation.pkl", "wb") as f:
    pickle.dump(model, f)

with open("fertilizer_le.pkl", "wb") as f:
    pickle.dump(le, f)

with open("fertilizer_columns.pkl", "wb") as f:
    pickle.dump(list(X.columns), f)

print("✅ Saved: fertilizer_recommendation.pkl")
print("✅ Saved: fertilizer_le.pkl")
print("✅ Saved: fertilizer_columns.pkl")
print(f"\nColumns ({len(X.columns)}):")
for c in X.columns:
    print(" ", c)