from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as v1_router
from app.api.v2.routes import router as v2_router
from app.database.postgres import Base, engine
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.services.model_registry import registry

app = FastAPI(
    title="API do TCC - Gerenciamento e Estruturação de APIs",
    description="API REST com versionamento, autenticação JWT e persistência híbrida",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    registry()

app.include_router(v1_router, prefix="/api/v1")
app.include_router(v2_router, prefix="/api/v2")

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}

app.mount("/", StaticFiles(directory=Path(__file__).parent / "frontend", html=True), name="frontend")
