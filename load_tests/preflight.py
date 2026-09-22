"""Verify existing credentials without printing tokens, passwords or response bodies."""
import ast
import json
import os
import time
from pathlib import Path
import requests
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent


def credentials():
    username, password = os.getenv("TEST_USERNAME"), os.getenv("TEST_PASSWORD")
    if username and password:
        return username, password
    saved = dotenv_values(ROOT.parent / ".env.loadtest")
    if saved.get("TEST_USERNAME") and saved.get("TEST_PASSWORD"):
        return saved["TEST_USERNAME"], saved["TEST_PASSWORD"]
    # Existing local test credentials; do not copy them to results or command lines.
    values = {}
    for node in ast.parse((ROOT / "locustfile.py").read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"API_USER", "API_PASSWORD"}:
                    values[target.id] = node.value.value
    return values["API_USER"], values["API_PASSWORD"]


def main():
    host = os.environ.get("TEST_HOST", "https://rep-tcc.onrender.com").rstrip("/")
    username, password = credentials()
    summary = {"host": host, "time": time.time(), "checks": []}
    output = ROOT / "results" / "preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    for path in ["/api/v1/", "/openapi.json"]:
        start = time.monotonic()
        try:
            r = session.get(host + path, timeout=90)
        except requests.RequestException as error:
            summary["checks"].append(dict(path=path, error=type(error).__name__, seconds=time.monotonic()-start))
            output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print(json.dumps(summary, indent=2))
            raise SystemExit(1)
        summary["checks"].append(dict(path=path, status=r.status_code, seconds=time.monotonic()-start))
    r = session.post(host + "/api/v1/login", data=dict(username=username, password=password), timeout=60)
    summary["checks"].append(dict(path="/api/v1/login", status=r.status_code))
    if r.status_code == 200:
        token = r.json()["access_token"]
        payload = dict(MedInc=8.3252, HouseAge=41, AveRooms=6.984127, AveBedrms=1.02381,
                       Population=322, AveOccup=2.555556, Latitude=37.88, Longitude=-122.23)
        for version in ["v1", "v2"]:
            start = time.monotonic()
            r = session.post(host + f"/api/{version}/predict", json=payload,
                             headers={"Authorization": f"Bearer {token}"}, timeout=60)
            check = dict(path=f"/api/{version}/predict", status=r.status_code, seconds=time.monotonic()-start)
            if r.status_code == 200:
                check["prediction"] = r.json().get("prediction_model")
                check["version"] = r.json().get("versao")
            summary["checks"].append(check)
    output = ROOT / "results" / "preflight.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
