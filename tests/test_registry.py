import hashlib
from app.services.model_registry import MODELS, registry


def test_registry_matches_shipped_artifacts():
    result = registry()
    assert set(result["models"]) == {"v1", "v2"}
    for version, model in result["models"].items():
        assert model["sha256"] == hashlib.sha256((MODELS / model["artifact"]).read_bytes()).hexdigest()
        assert model["endpoint"] == f"/api/{version}/predict"
        assert not str(MODELS) in str(model)
