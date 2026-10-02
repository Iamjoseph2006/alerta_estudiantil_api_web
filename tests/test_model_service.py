import math

from app.model_service import ModelService
from app.schemas import PredictionInput


def make_payload(**changes) -> PredictionInput:
    values = {
        "modalidad": "Virtual",
        "nivel_educativo_previo": "Bachillerato",
        "edad": 29,
        "intentos_previos": 0,
        "creditos_matriculados": 60,
        "dias_anticipacion_registro": 35,
        "clicks_30_dias": 398,
        "dias_activos_30": 13,
        "tareas_asignadas_30": 6,
        "tareas_entregadas_30": 3,
        "nota_promedio_30": 73.3,
        "solicito_soporte": False,
    }
    values.update(changes)
    return PredictionInput(**values)


def test_feature_engineering_reproduces_notebook_formulas():
    service = ModelService()
    features = service.build_features(make_payload())

    assert features.columns.tolist() == service.feature_columns
    assert features.loc[0, "clicks_por_dia_activo"] == 398 / 13
    assert features.loc[0, "tasa_entrega_30"] == 0.5
    assert features.loc[0, "tasa_actividad_30"] == 13 / 30
    assert features.loc[0, "log_clicks_30"] == math.log1p(398)
    assert features.loc[0, "sin_nota_30"] == 0


def test_missing_grade_is_preserved_for_pipeline_imputation():
    service = ModelService()
    features = service.build_features(make_payload(nota_promedio_30=None))

    assert math.isnan(features.loc[0, "nota_promedio_30"])
    assert features.loc[0, "sin_nota_30"] == 1


def test_prediction_has_valid_probability_and_contract():
    result = ModelService().predict(make_payload())

    assert 0 <= result["probabilidad_abandono"] <= 1
    assert 0 <= result["porcentaje_riesgo"] <= 100
    assert result["prediccion"] in {"alerta", "sin_alerta"}
    assert result["nivel_riesgo"] in {"alto", "bajo"}

