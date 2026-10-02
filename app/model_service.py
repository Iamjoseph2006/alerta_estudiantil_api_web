"""Carga del pipeline entrenado, ingeniería de variables e inferencia."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from app.schemas import PredictionInput


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "model" / "modelo_alerta_estudiantil.joblib"
DEFAULT_METADATA_PATH = Path(__file__).resolve().parent / "model" / "metadata_modelo.json"


class ModelService:
    """Encapsula el contrato entre los datos de la API y el pipeline de sklearn."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        metadata_path: str | Path | None = None,
    ) -> None:
        self.model_path = Path(
            model_path or os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH))
        )
        self.metadata_path = Path(
            metadata_path or os.getenv("MODEL_METADATA_PATH", str(DEFAULT_METADATA_PATH))
        )

        if not self.model_path.is_file():
            raise FileNotFoundError(f"No se encontró el modelo en {self.model_path}")
        if not self.metadata_path.is_file():
            raise FileNotFoundError(
                f"No se encontraron los metadatos en {self.metadata_path}"
            )

        package = joblib.load(self.model_path)
        required_keys = {"model", "feature_columns", "metadata"}
        if not isinstance(package, dict) or not required_keys.issubset(package):
            raise ValueError("El archivo del modelo no tiene el formato esperado.")

        self.pipeline = package["model"]
        self.feature_columns = list(package["feature_columns"])
        with self.metadata_path.open(encoding="utf-8") as metadata_file:
            self.metadata: dict[str, Any] = json.load(metadata_file)

        expected_columns = list(self.metadata.get("variables_modelo", []))
        if expected_columns and self.feature_columns != expected_columns:
            raise ValueError(
                "Las variables del archivo del modelo no coinciden con sus metadatos."
            )
        if not hasattr(self.pipeline, "predict_proba"):
            raise TypeError("El modelo cargado no implementa predict_proba().")

        self.threshold = float(self.metadata.get("umbral_clasificacion", 0.5))

    @staticmethod
    def api_input_fields() -> list[str]:
        return list(PredictionInput.model_fields)

    def build_features(self, payload: PredictionInput) -> pd.DataFrame:
        """Reproduce exactamente las variables derivadas del cuaderno de entrenamiento."""

        clicks_per_active_day = (
            payload.clicks_30_dias / payload.dias_activos_30
            if payload.dias_activos_30 > 0
            else 0.0
        )
        delivery_rate = (
            payload.tareas_entregadas_30 / payload.tareas_asignadas_30
        )

        row: dict[str, Any] = {
            "modalidad": payload.modalidad,
            "nivel_educativo_previo": payload.nivel_educativo_previo,
            "edad": payload.edad,
            "intentos_previos": payload.intentos_previos,
            "creditos_matriculados": payload.creditos_matriculados,
            "dias_anticipacion_registro": (
                np.nan
                if payload.dias_anticipacion_registro is None
                else payload.dias_anticipacion_registro
            ),
            "dias_activos_30": payload.dias_activos_30,
            "tareas_asignadas_30": payload.tareas_asignadas_30,
            "tareas_entregadas_30": payload.tareas_entregadas_30,
            "nota_promedio_30": (
                np.nan if payload.nota_promedio_30 is None else payload.nota_promedio_30
            ),
            "solicito_soporte": int(payload.solicito_soporte),
            "clicks_por_dia_activo": clicks_per_active_day,
            "tasa_entrega_30": delivery_rate,
            "tasa_actividad_30": payload.dias_activos_30 / 30,
            "log_clicks_30": float(np.log1p(payload.clicks_30_dias)),
            "sin_nota_30": int(payload.nota_promedio_30 is None),
        }

        missing = set(self.feature_columns) - set(row)
        if missing:
            raise ValueError(f"Faltan variables requeridas por el modelo: {sorted(missing)}")
        return pd.DataFrame([row], columns=self.feature_columns)

    def predict(self, payload: PredictionInput) -> dict[str, Any]:
        features = self.build_features(payload)
        probabilities = self.pipeline.predict_proba(features)[0]
        classes = list(self.pipeline.classes_)
        try:
            positive_index = classes.index(1)
        except ValueError as exc:
            raise ValueError("El modelo no contiene la clase positiva de abandono.") from exc

        probability = float(probabilities[positive_index])
        has_alert = probability >= self.threshold
        return {
            "probabilidad_abandono": round(probability, 6),
            "porcentaje_riesgo": round(probability * 100, 2),
            "prediccion": "alerta" if has_alert else "sin_alerta",
            "nivel_riesgo": "alto" if has_alert else "bajo",
            "umbral_clasificacion": self.threshold,
            "indicadores_derivados": {
                "clicks_por_dia_activo": round(
                    float(features.loc[0, "clicks_por_dia_activo"]), 4
                ),
                "tasa_entrega_30": round(
                    float(features.loc[0, "tasa_entrega_30"]), 4
                ),
                "tasa_actividad_30": round(
                    float(features.loc[0, "tasa_actividad_30"]), 4
                ),
                "sin_nota_30": bool(features.loc[0, "sin_nota_30"]),
            },
            "recomendacion": (
                "Priorizar una revisión académica y ofrecer acompañamiento; "
                "la predicción no debe usarse como decisión automática."
                if has_alert
                else "Mantener el seguimiento regular y actualizar la predicción con nuevos datos."
            ),
            "advertencia": self.metadata["limitacion"],
        }

    def public_model_info(self) -> dict[str, Any]:
        return {
            "nombre_modelo": self.metadata["nombre_modelo"],
            "tipo_base": self.metadata["tipo_base"],
            "ventana_observacion_dias": self.metadata[
                "ventana_observacion_dias"
            ],
            "objetivo": self.metadata["definicion_objetivo"],
            "umbral_clasificacion": self.threshold,
            "metricas_prueba": self.metadata["metricas_prueba"],
            "variables_entrada_api": self.api_input_fields(),
            "limitacion": self.metadata["limitacion"],
        }

