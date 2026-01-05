# ml/model.py

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.utils.class_weight import compute_class_weight
import pandas as pd


class UserNotificationModel:
    def __init__(self):
        self.pipeline = None

    def train(self, dataset):
        X_dict = [x for x, y in dataset]
        y = [y for x, y in dataset]

        X = pd.DataFrame(X_dict)

        cat_features = ["app"]
        num_features = ["hour", "has_urgent", "has_promo"]

        preprocessor = ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features),
            ("num", "passthrough", num_features),
        ])

        clf = LogisticRegression(
            max_iter=500,
            multi_class="auto",
            class_weight="balanced",
        )

        self.pipeline = Pipeline([
            ("prep", preprocessor),
            ("clf", clf),
        ])

        self.pipeline.fit(X, y)

    def predict(self, features):
        return int(self.pipeline.predict([features])[0])

    def save(self, path):
        joblib.dump(self.pipeline, path)

    def load(self, path):
        self.pipeline = joblib.load(path)
