from datetime import datetime
from app.database.mongo import predictions_collection
from app.services.model_service import predict_house_value_v1, predict_house_value_v2

def predict_v1(user: str, features: dict):
    result = predict_house_value_v1(features)

    predictions_collection.insert_one({
        "usuario": user,
        "features": features,
        "resultado_modelo": result,
        "resultado_dolar": result * 100000,
        "versao": "v1",
        "timestamp": datetime.utcnow()
    })

    return result

def predict_v2(user: str, features: dict):
    result = predict_house_value_v2(features)

    predictions_collection.insert_one({
        "usuario": user,
        "features": features,
        "resultado_modelo": result,
        "resultado_dolar": result * 100000,
        "versao": "v2",
        "timestamp": datetime.utcnow()
    })

    return result