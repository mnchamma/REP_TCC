"""Local fixture validates evidence collection; it is NOT an API performance result."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from jose import jwt


def test_locust_captures_status_timings_and_active_users(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            if self.path.endswith("/login"):
                body = {"access_token": jwt.encode({"sub": "fixture", "exp": time.time()+300}, "fixture", algorithm="HS256")}
            else:
                body = {"prediction_model": 1.5, "versao": self.path.split("/")[2]}
            data = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    env = os.environ.copy()
    env.update(TEST_USERNAME="fixture", TEST_PASSWORD="fixture", TEST_AUTH_MODE="renew",
               TEST_VERSION="v1", TEST_RAW_CSV=str(tmp_path / "requests.csv"))
    try:
        run = subprocess.run([sys.executable, "-m", "locust", "-f", "load_tests/detailed.py",
                              "--host", f"http://127.0.0.1:{server.server_port}", "--headless",
                              "--users", "1", "--spawn-rate", "1", "--run-time", "5s", "--only-summary"],
                             cwd=Path(__file__).resolve().parents[1], env=env, capture_output=True, text=True, timeout=30)
        assert run.returncode == 0, run.stderr
    finally:
        server.shutdown()
        server.server_close()
    with (tmp_path / "requests.csv").open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert any(r["name"] == "login/initial" for r in rows)
    predictions = [r for r in rows if r["name"] == "predict/v1"]
    assert predictions
    assert all(r["status"] == "200" and r["success"] == "1" for r in predictions)
    assert all(float(r["token_remaining_s"]) > 0 for r in predictions)
    assert (tmp_path / "requests.timing.json").exists()
    samples = json.loads((tmp_path / "requests.users.json").read_text())
    assert any(s["users"] == 1 for s in samples)
    assert "access_token" not in (tmp_path / "requests.csv").read_text()
