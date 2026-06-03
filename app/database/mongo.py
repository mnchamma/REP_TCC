from pymongo import MongoClient
from app.config import MONGO_URL

client = MongoClient(MONGO_URL)
db = client["tcc_db"]
predictions_collection = db["predictions"]