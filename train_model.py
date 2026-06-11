# =============================================================
#  train_model.py  —  Trains 3 classifiers and saves them
#  Run this once: python train_model.py
#  Requires: training_data.csv (run generate_data.py first)
#  Outputs:  model.pkl
# =============================================================

import csv
import pickle
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


# ── Load data ─────────────────────────────────────────────────

prompts   = []
intents   = []
sizes     = []
materials = []

with open('training_data.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        prompts.append(row['prompt'])
        intents.append(row['intent'])
        sizes.append(row['size'])
        materials.append(row['material'])

print(f"Loaded {len(prompts)} examples.")

# ── Train / test split ────────────────────────────────────────

X_train, X_test, \
yi_train, yi_test, \
ys_train, ys_test, \
ym_train, ym_test = train_test_split(
    prompts, intents, sizes, materials,
    test_size=0.15, random_state=42
)


# ── Helper: build a TF-IDF + Logistic Regression pipeline ────

def build_pipeline():
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer    = 'word',
            ngram_range = (1, 2),   # unigrams + bigrams
            lowercase   = True,
            max_features= 5000,
        )),
        ('clf', LogisticRegression(
            max_iter = 500,
            C        = 1.0,
            solver   = 'lbfgs',
            
        )),
    ])


# ── Train intent classifier ───────────────────────────────────

print("\nTraining intent classifier...")
intent_model = build_pipeline()
intent_model.fit(X_train, yi_train)
intent_acc = accuracy_score(yi_test, intent_model.predict(X_test))
print(f"  Intent accuracy:   {intent_acc * 100:.1f}%")


# ── Train size classifier ─────────────────────────────────────

print("Training size classifier...")
size_model = build_pipeline()
size_model.fit(X_train, ys_train)
size_acc = accuracy_score(ys_test, size_model.predict(X_test))
print(f"  Size accuracy:     {size_acc * 100:.1f}%")


# ── Train material classifier ─────────────────────────────────

print("Training material classifier...")
material_model = build_pipeline()
material_model.fit(X_train, ym_train)
mat_acc = accuracy_score(ym_test, material_model.predict(X_test))
print(f"  Material accuracy: {mat_acc * 100:.1f}%")


# ── Save all 3 models together ────────────────────────────────

bundle = {
    'intent':   intent_model,
    'size':     size_model,
    'material': material_model,
}

with open('model.pkl', 'wb') as f:
    pickle.dump(bundle, f)

print("\nAll 3 models saved to model.pkl")
print(f"Overall average accuracy: {(intent_acc + size_acc + mat_acc) / 3 * 100:.1f}%")
print("\nYou can now run python main.py — the AI will use the trained model.")
