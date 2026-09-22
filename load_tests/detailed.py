"""Single-process experiments. Original locustfile.py is preserved as evidence."""
import base64
import csv
import json
import os
import random
import time
import uuid
from pathlib import Path
import gevent

from locust import HttpUser, between, events, task
from locust.exception import StopUser

PAYLOAD = dict(MedInc=8.3252, HouseAge=41.0, AveRooms=6.984127,
               AveBedrms=1.02381, Population=322.0, AveOccup=2.555556,
               Latitude=37.88, Longitude=-122.23)
MODE = os.getenv("TEST_AUTH_MODE", "renew")
VERSION = os.getenv("TEST_VERSION", "mixed")
if MODE not in {"renew", "no_renew", "legacy"}:
    raise ValueError("TEST_AUTH_MODE must be renew, no_renew or legacy")
if VERSION not in {"v1", "v2", "mixed"}:
    raise ValueError("TEST_VERSION must be v1, v2 or mixed")
raw_file = None
raw_writer = None
started_at = None
sampler = None
active_counts = []


def sample_users(environment):
    while True:
        active_counts.append({"time": time.time(), "users": environment.runner.user_count})
        gevent.sleep(1)


@events.test_start.add_listener
def open_raw(environment, **kwargs):
    global raw_file, raw_writer, started_at, sampler, active_counts
    started_at = time.time()
    active_counts = []
    sampler = gevent.spawn(sample_users, environment)
    path = Path(os.environ.get("TEST_RAW_CSV", "load_tests/results/requests.csv"))
    path.parent.mkdir(parents=True, exist_ok=True)
    raw_file = path.open("w", newline="", encoding="utf-8")
    raw_writer = csv.DictWriter(raw_file, fieldnames=[
        "finished_at", "name", "response_ms", "status", "success", "reason",
        "user_id", "token_age_s", "token_remaining_s", "request_id",
    ])
    raw_writer.writeheader()
    path.with_suffix(".timing.json").write_text(json.dumps({"started_at": started_at}), encoding="utf-8")


@events.request.add_listener
def record_request(name, response_time, response=None, exception=None, context=None, **kwargs):
    if raw_writer is None:
        return
    ctx = context or {}
    status = response.status_code if response is not None else 0
    reason = response.headers.get("X-Auth-Error", "") if response is not None else ""
    if not reason and exception:
        # Do not persist arbitrary exception messages, URLs, bodies or credentials.
        reason = type(exception).__name__
    raw_writer.writerow(dict(
        finished_at=time.time(), name=name, response_ms=response_time,
        status=status, success=int(exception is None and 200 <= status < 300),
        reason=reason, user_id=ctx.get("user_id", ""),
        token_age_s=ctx.get("token_age_s", ""),
        token_remaining_s=ctx.get("token_remaining_s", ""),
        request_id=ctx.get("request_id", ""),
    ))


@events.test_stop.add_listener
def close_raw(environment, **kwargs):
    global raw_file, raw_writer
    if sampler:
        sampler.kill()
    if raw_file:
        Path(raw_file.name).with_suffix(".users.json").write_text(json.dumps(active_counts), encoding="utf-8")
        raw_file.close()
    raw_file = raw_writer = None


class APIUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.user_id = uuid.uuid4().hex
        self.token = None
        self.acquired = None
        self.expires = 0
        if not self.login("initial") and MODE != "legacy":
            # Stopping reduces effective concurrency: runner/analysis must flag it.
            raise StopUser()

    def login(self, phase):
        with self.client.post(
            "/api/v1/login", data={"username": os.environ["TEST_USERNAME"],
                                   "password": os.environ["TEST_PASSWORD"]},
            name=f"login/{phase}", timeout=60, catch_response=True,
            context={"user_id": self.user_id},
        ) as response:
            if response.status_code != 200:
                response.failure(f"login_http_{response.status_code}")
                return False
            try:
                token = response.json()["access_token"]
                payload = token.split(".")[1]
                claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
                expires = float(claims["exp"])
                if expires <= time.time():
                    raise ValueError("expired")
            except (ValueError, KeyError, IndexError, TypeError):
                response.failure("invalid_login_response")
                return False
            # Decode only to schedule renewal; server performs signature validation.
            self.token, self.expires, self.acquired = token, expires, time.time()
            return True

    @task
    def predict(self):
        if MODE == "renew" and time.time() >= self.expires - 30:
            if not self.login("renewal"):
                raise StopUser()
        version = random.choice(["v1", "v2"]) if VERSION == "mixed" else VERSION
        now = time.time()
        request_id = uuid.uuid4().hex
        headers = {"X-Request-ID": request_id}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        context = dict(user_id=self.user_id, request_id=request_id,
                       token_age_s=now - self.acquired if self.acquired else "",
                       token_remaining_s=self.expires - now if self.token else "")
        with self.client.post(
            f"/api/{version}/predict", json=PAYLOAD, headers=headers,
            name=f"predict/{version}", timeout=60, catch_response=True, context=context,
        ) as response:
            if response.status_code == 200:
                try:
                    body = response.json()
                    if body["versao"] != version or not isinstance(body["prediction_model"], (int, float)):
                        raise ValueError("contract")
                except (ValueError, KeyError, TypeError):
                    response.failure("invalid_prediction_response")
            elif response.status_code == 401:
                response.failure("authentication_401")
                # Keep the failure in statistics. Never retry/mask this prediction.
                if MODE == "renew":
                    self.expires = 0
