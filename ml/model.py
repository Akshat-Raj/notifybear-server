# ml/model.py

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
import pandas as pd
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import StringTensorType, Int64TensorType, FloatTensorType
import onnx


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
    
    def save_onnx(self, path="model.onnx"):
        initial_types = [
            ("app", StringTensorType([None, 1])),
            ("hour", Int64TensorType([None, 1])),
            ("has_urgent", Int64TensorType([None, 1])),
            ("has_promo", Int64TensorType([None, 1])),
        ]

        onnx_model = convert_sklearn(self.pipeline, initial_types=initial_types)
        with open(path, "wb") as f:
            f.write(onnx_model.SerializeToString())
