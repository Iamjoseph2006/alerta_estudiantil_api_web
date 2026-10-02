from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

VALID_PAYLOAD = {
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


def test_health_endpoint():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["modelo_cargado"] is True


def test_model_info_endpoint():
    response = client.get("/api/v1/model-info")
    data = response.json()

    assert response.status_code == 200
    assert data["nombre_modelo"] == "Regresión logística"
    assert data["ventana_observacion_dias"] == 30
    assert "clicks_30_dias" in data["variables_entrada_api"]


def test_predict_endpoint():
    response = client.post("/api/v1/predict", json=VALID_PAYLOAD)
    data = response.json()

    assert response.status_code == 200
    assert 0 <= data["probabilidad_abandono"] <= 1
    assert data["umbral_clasificacion"] == 0.5


def test_rejects_incoherent_task_counts():
    payload = {**VALID_PAYLOAD, "tareas_asignadas_30": 4, "tareas_entregadas_30": 5}
    response = client.post("/api/v1/predict", json=payload)

    assert response.status_code == 422
    assert "no pueden superar" in str(response.json())


def test_web_interface_is_served():
    response = client.get("/")

    assert response.status_code == 200
    assert "Consulta de riesgo de abandono" in response.text
    assert 'id="prediction-form"' in response.text


def test_public_api_documentation_is_hidden():
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
