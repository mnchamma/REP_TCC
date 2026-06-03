from app.database.postgres import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

hashed_password = pwd_context.hash("1234")

user = User(username="admin", password=hashed_password)

db.add(user)
db.commit()
db.close()