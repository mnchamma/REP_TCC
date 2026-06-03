from fastapi import APIRouter, Depends
from app.services.ml_services import predict_v2
from app.api.v1.routes import get_current_user
from app.schemas.predict_schema import HouseFeatures

router = APIRouter()

@router.post("/predict")
def predict(features: HouseFeatures, user: str = Depends(get_current_user)):
    result = predict_v2(user, features.dict())

    return {
        "prediction_model": result,
        "prediction_dollars": result * 100000,
        "usuario": user,
        "versao": "v2"
    }