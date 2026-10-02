# API e interfaz web de alerta temprana estudiantil

Segunda etapa del proyecto de Minería de Datos. El proyecto carga el pipeline final de **regresión logística**, expone una API REST con FastAPI y sirve una página web que consume esa misma API.

> Alcance académico: el modelo fue entrenado con una base simulada reproducible inspirada en OULAD. Su resultado sirve para demostrar el flujo técnico y orientar apoyo humano; no debe emplearse para sancionar estudiantes ni tomar decisiones automáticas.

## Estructura

```text
alerta_estudiantil_api_web/
├── app/
│   ├── main.py                 # Rutas FastAPI y archivos estáticos
│   ├── model_service.py        # Carga, transformación y predicción
│   ├── schemas.py              # Validaciones de entrada y salida
│   ├── model/                  # Pipeline y metadatos exportados del Colab
│   └── static/                 # Aplicación web (HTML, CSS y JavaScript)
├── tests/                      # Pruebas del modelo y de los endpoints
├── Dockerfile
├── requirements.txt
└── README.md
```

## Ejecución local

Se recomienda Python 3.12.

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Linux o macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Después de iniciar el servidor:

- Aplicación web: <http://127.0.0.1:8000>

La documentación automática no se muestra al usuario final. Para habilitarla temporalmente durante una revisión técnica:

```powershell
$env:ENABLE_API_DOCS="1"
python -m uvicorn app.main:app --reload
```

## Endpoints

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/api/v1/health` | Confirma que la API y el modelo están disponibles. |
| `GET` | `/api/v1/model-info` | Devuelve alcance, variables y métricas del modelo. |
| `POST` | `/api/v1/predict` | Calcula la probabilidad individual de abandono. |

Ejemplo de petición:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
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
    "solicito_soporte": false
  }'
```

La API calcula internamente las cinco variables derivadas usadas durante el entrenamiento: clics por día activo, tasa de entrega, tasa de actividad, logaritmo de clics y ausencia de nota. El consumidor no puede alterar manualmente esas variables.

## Validaciones principales

- Solo se aceptan las categorías conocidas por el modelo.
- Las variables se limitan a los rangos observados durante el entrenamiento para evitar extrapolaciones silenciosas.
- Los días activos deben encontrarse entre 0 y 30.
- Las tareas entregadas no pueden superar a las asignadas.
- No puede registrarse actividad si los días activos son cero.
- La nota se limita a 0–100 y puede enviarse como `null`.
- Los campos adicionales se rechazan para evitar errores silenciosos.

## Pruebas

Con el entorno virtual activado:

```bash
python -m pytest -q
```

Las pruebas verifican la ingeniería de variables, la inferencia, el rango de la probabilidad, la validación de datos, los endpoints y la entrega de la interfaz web.

## Ejecución con Docker

```bash
docker build -t alerta-estudiantil .
docker run --rm -p 8000:8000 alerta-estudiantil
```

## Configuración opcional

- `MODEL_PATH`: ruta a otro archivo `.joblib` con el mismo contrato.
- `MODEL_METADATA_PATH`: ruta al JSON de metadatos correspondiente.
- `ALLOWED_ORIGINS`: orígenes permitidos, separados por comas, si otro frontend consume la API.

Si se reemplaza el modelo, deben conservarse las claves `model`, `feature_columns` y `metadata` dentro del archivo exportado, además del orden exacto de variables descrito en `metadata_modelo.json`.
