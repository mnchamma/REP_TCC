from pathlib import Path
from datetime import datetime
import json

import joblib
import pandas as pd

from sklearn.datasets import fetch_california_housing
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "trained_models"
MODELS_DIR.mkdir(exist_ok=True)


def evaluate_model(model, x_test, y_test):
    predictions = model.predict(x_test)

    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = mse ** 0.5
    r2 = r2_score(y_test, predictions)

    return {
        "mae": round(float(mae), 6),
        "mse": round(float(mse), 6),
        "rmse": round(float(rmse), 6),
        "r2": round(float(r2), 6),
    }


def main():
    # 1. Carregar dataset
    dataset = fetch_california_housing(as_frame=True)
    df = dataset.frame.copy()

    # 2. Separar features e target
    x = df.drop(columns=["MedHouseVal"])
    y = df["MedHouseVal"]

    feature_names = list(x.columns)

    # 3. Separar treino e teste
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42
    )
    # 3.1 Normalizar
    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)

    # 4. Treinar modelo v1
    model_v1 = LinearRegression()
    model_v1.fit(x_train, y_train)

    # 5. Treinar modelo v2
    model_v2 = RandomForestRegressor(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model_v2.fit(x_train, y_train)

    # 6. Avaliar modelos
    metrics_v1 = evaluate_model(model_v1, x_test, y_test)
    metrics_v2 = evaluate_model(model_v2, x_test, y_test)

    # 7. Salvar modelos
    model_v1_path = MODELS_DIR / "california_model_v1.joblib"
    model_v2_path = MODELS_DIR / "california_model_v2.joblib"

    joblib.dump(model_v1, model_v1_path)
    joblib.dump(model_v2, model_v2_path)

    # 8. Salvar metadados
    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "target": "MedHouseVal",
        "feature_names": feature_names,
        "models": {
            "v1": {
                "name": "LinearRegression",
                "path": str(model_v1_path),
                "metrics": metrics_v1,
            },
            "v2": {
                "name": "RandomForestRegressor",
                "path": str(model_v2_path),
                "metrics": metrics_v2,
            },
        },
    }

    metadata_path = MODELS_DIR / "model_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    # 9. Mostrar resumo
    print("\n=== MODELO V1 ===")
    print("Nome:", metadata["models"]["v1"]["name"])
    print("Caminho:", model_v1_path)
    print("Métricas:", metrics_v1)

    print("\n=== MODELO V2 ===")
    print("Nome:", metadata["models"]["v2"]["name"])
    print("Caminho:", model_v2_path)
    print("Métricas:", metrics_v2)

    print("\n=== FEATURES ESPERADAS ===")
    print(feature_names)

    print("\nMetadados salvos em:", metadata_path)


if __name__ == "__main__":
    main()