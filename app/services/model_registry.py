"""Read-only provenance of the exact artifacts included in this deployment."""
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

MODELS = Path(__file__).resolve().parents[2] / "trained_models"


@lru_cache(maxsize=1)
def registry():
    metadata = json.loads((MODELS / "model_metadata.json").read_text(encoding="utf-8"))
    return {
        "deployment_commit": os.getenv("RENDER_GIT_COMMIT", "local"),
        "created_at": metadata["created_at"],
        "target": metadata["target"],
        "features": metadata["feature_names"],
        "models": {
            version: {
                "name": details["name"],
                "artifact": f"california_model_{version}.joblib",
                "sha256": hashlib.sha256((MODELS / f"california_model_{version}.joblib").read_bytes()).hexdigest(),
                "predictive_metrics": details["metrics"],
                "endpoint": f"/api/{version}/predict",
            }
            for version, details in metadata["models"].items()
        },
    }
