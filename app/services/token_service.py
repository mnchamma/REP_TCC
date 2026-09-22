"""JWT validation with safe, distinguishable failure reasons."""
import logging

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.config import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login", auto_error=False)


def reject(reason):
    logger.warning("authentication_failed reason=%s", reason)
    raise HTTPException(
        status_code=401, detail=reason,
        headers={"WWW-Authenticate": "Bearer", "X-Auth-Error": reason},
    )


def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        reject("missing_token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],
                             options={"require_exp": True})
    except ExpiredSignatureError:
        reject("expired_token")
    except JWTError:
        reject("invalid_token")
    username = payload.get("sub")
    if not isinstance(username, str) or not username.strip():
        reject("invalid_subject")
    return username
