import os
import time

os.environ["SECRET_KEY"] = "test-only-key-not-a-production-secret"

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from jose import jwt
from app.services import token_service

app = FastAPI()


@app.get("/protected")
def protected(user=Depends(token_service.get_current_user)):
    return {"user": user}


client = TestClient(app)


def signed(**overrides):
    claims = {"sub": "tester", "exp": int(time.time()) + 60}
    claims.update(overrides)
    return jwt.encode(claims, token_service.SECRET_KEY, algorithm="HS256")


@pytest.mark.parametrize("token,reason", [
    (None, "missing_token"),
    ("broken", "invalid_token"),
    (signed(exp=int(time.time()) - 10), "expired_token"),
    (signed(sub=""), "invalid_subject"),
    (jwt.encode({"sub": "tester"}, token_service.SECRET_KEY, algorithm="HS256"), "invalid_token"),
    (jwt.encode({"sub": "tester", "exp": int(time.time()) + 60}, "wrong-key", algorithm="HS256"), "invalid_token"),
])
def test_rejection_reason(token, reason):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert response.headers["x-auth-error"] == reason
    assert response.headers["www-authenticate"] == "Bearer"


def test_valid_token_and_no_sensitive_log(caplog):
    token = signed()
    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"user": "tester"}
    assert token not in caplog.text
    assert token_service.SECRET_KEY not in caplog.text
