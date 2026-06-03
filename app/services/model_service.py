from pathlib import Path
import joblib
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "trained_models"

model_v1 = joblib.load(MODELS_DIR / "california_model_v1.joblib")
model_v2 = joblib.load(MODELS_DIR / "california_model_v2.joblib")

FEATURE_ORDER = [
    "MedInc",
    "HouseAge",
    "AveRooms",
    "AveBedrms",
    "Population",
    "AveOccup",
    "Latitude",
    "Longitude",
]

def prepare_features(data: dict) -> pd.DataFrame:
    row = [[data[feature] for feature in FEATURE_ORDER]]
    return pd.DataFrame(row, columns=FEATURE_ORDER)

def predict_house_value_v1(data: dict) -> float:
    x = prepare_features(data)
    prediction = model_v1.predict(x)[0]
    return float(prediction)

def predict_house_value_v2(data: dict) -> float:
    x = prepare_features(data)
    prediction = model_v2.predict(x)[0]
    return float(prediction)