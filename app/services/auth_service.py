from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.database.postgres import SessionLocal
from app.models.user import User
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username, password):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()

    if not user:
        db.close()
        return False

    if not verify_password(password, user.password):
        db.close()
        return False

    db.close()
    return {"username": user.username}

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    print("TOKEN GERADO:", token)
    print("PAYLOAD GERADO:", to_encode)
    print("SECRET_KEY USADA NA GERAÇÃO:", SECRET_KEY)
    print("ALGORITHM USADO NA GERAÇÃO:", ALGORITHM)

    return token

def create_user(username, password):
    db = SessionLocal()

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        db.close()
        return None

    hashed_password = pwd_context.hash(password)

    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()

    return {"username": new_user.username}
