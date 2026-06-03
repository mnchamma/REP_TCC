from app.database.postgres import engine, Base
from app.models.user import User

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()