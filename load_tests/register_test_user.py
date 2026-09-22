"""Create an isolated benchmark account; keep credentials out of source and logs."""
import argparse
import secrets
from pathlib import Path
import requests


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True)
    args = p.parse_args()
    target = Path(__file__).resolve().parents[1] / ".env.loadtest"
    if target.exists():
        raise SystemExit("Credential file already exists; reuse the account or handle explicitly.")
    username = "locust_" + secrets.token_hex(8)
    password = secrets.token_urlsafe(32)
    r = requests.post(args.host.rstrip("/") + "/api/v1/register",
                      json=dict(username=username, password=password), timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"Registration failed: HTTP {r.status_code}")
    with target.open("x", encoding="utf-8") as f:
        f.write(f"TEST_USERNAME={username}\nTEST_PASSWORD={password}\n")
    print("Test account created; credentials saved locally in ignored .env.loadtest")


if __name__ == "__main__":
    main()
