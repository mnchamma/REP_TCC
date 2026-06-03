from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from app.services.auth_service import authenticate_user, create_access_token
from app.services.ml_services import predict_v1
from app.config import SECRET_KEY, ALGORITHM
from app.schemas.user_schema import UserCreate, UserResponse
from app.services.auth_service import create_user
from app.schemas.predict_schema import HouseFeatures

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

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
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme)):
    print("TOKEN RECEBIDO:", token)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("PAYLOAD DECODIFICADO:", payload)

        username = payload.get("sub")
        if username is None:
            print("ERRO: campo 'sub' não encontrado no payload")
            raise HTTPException(status_code=401, detail="Token inválido")

        return username

    except JWTError as e:
        print("ERRO JWT:", str(e))
        print("SECRET_KEY USADA NA VALIDAÇÃO:", SECRET_KEY)
        print("ALGORITHM USADO NA VALIDAÇÃO:", ALGORITHM)
        raise HTTPException(status_code=401, detail="Token inválido")

@router.post("/predict")
def predict(features: HouseFeatures, user: str = Depends(get_current_user)):
    result = predict_v1(user, features.dict())

    return {
        "prediction_model": result,
        "prediction_dollars": result * 100000,
        "usuario": user,
        "versao": "v1"
    }