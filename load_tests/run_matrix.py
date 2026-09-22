"""Reproducible sequential experiments; never puts credentials in CLI arguments."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

from preflight import credentials

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--users", nargs="+", type=int, default=[1, 10, 50])
    parser.add_argument("--versions", nargs="+", choices=["v1", "v2", "mixed"], default=["v1", "v2", "mixed"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seconds", type=int, default=360)
    parser.add_argument("--warmup", type=int, default=60)
    parser.add_argument("--auth", choices=["renew", "no_renew", "legacy"], default="renew")
    parser.add_argument("--label", required=True, help="e.g. baseline-9b2f7f8 or revised-commit")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.seconds <= args.warmup or min(args.users) < 1 or args.repeats < 1:
        parser.error("Require seconds > warmup, users >= 1, repeats >= 1")
    username, password = credentials()
    batch = ROOT / "load_tests" / "results" / (time.strftime("%Y%m%d-%H%M%S") + "-" + args.label)
    batch.mkdir(parents=True, exist_ok=False)
    scenarios = [(users, version, repeat) for repeat in range(1, args.repeats+1)
                 for users in args.users for version in args.versions]
    random.Random(args.seed).shuffle(scenarios)
    for users, version, repeat in scenarios:
        out = batch / f"{version}-{users}u-r{repeat}"
        out.mkdir()
        env = os.environ.copy()
        env.update(TEST_USERNAME=username, TEST_PASSWORD=password, TEST_VERSION=version,
                   TEST_AUTH_MODE=args.auth, TEST_RAW_CSV=str(out / "requests.csv"))
        command = [sys.executable, "-m", "locust", "-f", "load_tests/detailed.py",
                   "--host", args.host, "--headless", "--users", str(users),
                   "--spawn-rate", "1", "--run-time", f"{args.seconds}s",
                   "--stop-timeout", "65", "--csv", str(out / "locust"),
                   "--csv-full-history", "--html", str(out / "report.html"), "--only-summary"]
        manifest = dict(vars(args), users=users, version=version, repeat=repeat,
                        started_at=time.time(), python=platform.python_version(),
                        locust=importlib.metadata.version("locust"),
                        client_platform=platform.platform(), spawn_rate=1,
                        wait_seconds=[1, 3], timeout_seconds=60,
                        harness_sha256=hashlib.sha256((ROOT / "load_tests/detailed.py").read_bytes()).hexdigest(),
                        local_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip())
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Running {out.name}: {args.seconds}s", flush=True)
        with (out / "console.log").open("w", encoding="utf-8") as log:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
        manifest.update(ended_at=time.time(), exit_code=result.returncode)
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Completed {out.name}, exit={result.returncode}", flush=True)
        if not (out / "requests.csv").exists():
            raise RuntimeError(f"No requests.csv. Inspect {out / 'console.log'}")
    print(batch)


if __name__ == "__main__":
    main()
