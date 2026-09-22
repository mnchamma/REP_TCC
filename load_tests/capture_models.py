"""Capture public model provenance and predictions, excluding credentials and user data."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
from preflight import credentials

PAYLOAD = dict(MedInc=8.3252, HouseAge=41, AveRooms=6.984127, AveBedrms=1.02381,
               Population=322, AveOccup=2.555556, Latitude=37.88, Longitude=-122.23)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    username, password = credentials()
    session = requests.Session()
    r = session.post(args.host.rstrip("/") + "/api/v1/login",
                     data=dict(username=username, password=password), timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"Login failed: HTTP {r.status_code}")
    session.headers["Authorization"] = "Bearer " + r.json()["access_token"]
    evidence = dict(captured_at=datetime.now(timezone.utc).isoformat(), host=args.host, payload=PAYLOAD)
    r = session.get(args.host.rstrip("/") + "/api/v1/models", timeout=60)
    evidence["registry_status"] = r.status_code
    if r.status_code == 200:
        evidence["registry"] = r.json()
    evidence["predictions"] = {}
    for v in ["v1", "v2"]:
        r = session.post(args.host.rstrip("/") + f"/api/{v}/predict", json=PAYLOAD, timeout=60)
        evidence["predictions"][v] = {"status": r.status_code}
        if r.status_code == 200:
            evidence["predictions"][v]["value"] = r.json()["prediction_model"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(f"Evidence saved to {args.output}")


if __name__ == "__main__":
    main()
