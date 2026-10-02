"""Aplicación FastAPI y servidor de la interfaz web."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.model_service import ModelService
from app.schemas import (
    HealthResponse,
    ModelInfoResponse,
    PredictionInput,
    PredictionResponse,
)


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app = FastAPI(
    title="API de alerta temprana estudiantil",
    version="1.0.0",
    description=(
        "API académica que estima el riesgo de abandono posterior al día 30 "
        "a partir de información temprana del curso."
    ),
    contact={"name": "Proyecto de Minería de Datos"},
    docs_url="/docs" if os.getenv("ENABLE_API_DOCS") == "1" else None,
    redoc_url=None,
    openapi_url="/openapi.json" if os.getenv("ENABLE_API_DOCS") == "1" else None,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

model_service = ModelService()

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def web_app() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    tags=["Sistema"],
    summary="Comprobar disponibilidad",
)
def health() -> dict[str, object]:
    return {
        "estado": "ok",
        "modelo_cargado": True,
        "nombre_modelo": model_service.metadata["nombre_modelo"],
    }


@app.get(
    "/api/v1/model-info",
    response_model=ModelInfoResponse,
    tags=["Modelo"],
    summary="Consultar metadatos del modelo",
)
def model_info() -> dict[str, object]:
    return model_service.public_model_info()


@app.post(
    "/api/v1/predict",
    response_model=PredictionResponse,
    tags=["Predicción"],
    summary="Estimar el riesgo individual",
)
def predict(payload: PredictionInput) -> dict[str, object]:
    return model_service.predict(payload)
