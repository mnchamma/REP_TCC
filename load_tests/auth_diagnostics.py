"""Cloud authentication probes. Token is private; evidence contains only safe metadata."""
import argparse
import base64
import json
import time
from pathlib import Path
import requests
from preflight import credentials


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True)
    p.add_argument("--phase", choices=["start", "finish"], required=True)
    p.add_argument("--directory", type=Path, required=True)
    args = p.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    private = args.directory / "private-token.json"
    evidence_file = args.directory / "auth-evidence.json"
    host = args.host.rstrip("/")
    user, password = credentials()

    def login():
        r = requests.post(host + "/api/v1/login", data={"username": user, "password": password}, timeout=60)
        if r.status_code != 200:
            raise SystemExit(f"Login failed: HTTP {r.status_code}")
        return r.json()["access_token"]

    def probe(token, label):
        headers = {"Authorization": "Bearer " + token} if token else {}
        r = requests.get(host + "/api/v1/models", headers=headers, timeout=60)
        return dict(label=label, at=time.time(), status=r.status_code,
                    auth_error=r.headers.get("X-Auth-Error", ""))

    if args.phase == "start":
        if private.exists() or evidence_file.exists():
            raise SystemExit("Use a fresh directory to preserve existing evidence")
        token = login()
        segment = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)))
        private.write_text(json.dumps({"token": token}), encoding="utf-8")
        evidence = dict(host=host, started_at=time.time(), expires_at=claims["exp"], probes=[
            probe(token, "valid_initial"), probe(None, "missing_token"), probe("malformed", "malformed_token")])
    else:
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
        if time.time() <= evidence["expires_at"] + 2:
            raise SystemExit("Token has not expired yet; do not infer expiry failure")
        if evidence["host"] != host:
            raise SystemExit("Host changed")
        token = json.loads(private.read_text(encoding="utf-8"))["token"]
        evidence["probes"].extend([probe(token, "expired_original"), probe(login(), "valid_after_new_login")])
        evidence["finished_at"] = time.time()
        private.unlink()
    evidence_file.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
