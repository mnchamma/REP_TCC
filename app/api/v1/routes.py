from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.services.auth_service import authenticate_user, create_access_token
from app.services.ml_services import predict_v1
from app.schemas.user_schema import UserCreate, UserResponse
from app.services.auth_service import create_user
from app.schemas.predict_schema import HouseFeatures
from app.services.token_service import get_current_user
from app.services.model_registry import registry

router = APIRouter()

@router.get("/models")
def models(user: str = Depends(get_current_user)):
    return registry()

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate):
    user = create_user(user_data.username, user_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    return {
        "message": "Usuário criado com sucesso",
        "username": user["username"]
    }

@router.get("/")
def root():
    return {"message": "API v1 funcionando 🚀"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas",
                            headers={"WWW-Authenticate": "Bearer", "X-Auth-Error": "invalid_credentials"})

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/predict")
def predict(features: HouseFeatures, user: str = Depends(get_current_user)):
    result = predict_v1(user, features.dict())

    return {
        "prediction_model": result,
        "prediction_dollars": result * 100000,
        "usuario": user,
        "versao": "v1"
    }
