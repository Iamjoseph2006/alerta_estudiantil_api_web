# Proyecto de Minería de Datos: alerta temprana de abandono estudiantil

Proyecto académico de la asignatura **Minería de Datos** orientado a construir un flujo completo de análisis, modelado y despliegue para estimar el riesgo de abandono estudiantil después de los primeros 30 días de actividad académica.

**Autor:** José Jhair Hernández Tseremp

> **Alcance académico:** el modelo fue entrenado con una base simulada reproducible inspirada en OULAD. El sistema demuestra el proceso técnico completo y puede orientar acciones de acompañamiento humano. No debe utilizarse para sancionar estudiantes ni para tomar decisiones automáticas sin validación externa.

## Flujo del proyecto

El repositorio integra las etapas principales del trabajo:

1. generación y exploración de la base de datos;
2. limpieza y transformación;
3. creación de variables derivadas;
4. comparación de técnicas de minería de datos;
5. selección y exportación del modelo final;
6. integración del modelo en una API REST con FastAPI;
7. desarrollo de una WebAPP que consume la API;
8. validación mediante pruebas automatizadas.

El cuaderno final compara **Regresión Logística, Árbol de Decisión y Bosque Aleatorio**. El modelo seleccionado es **Regresión Logística** y utiliza un umbral de clasificación de 0,50.

## Datos

La base final contiene **2.000 estudiantes** y fue generada de forma simulada y reproducible tomando como referencia variables demográficas, académicas y de interacción presentes en OULAD.

La predicción utiliza información disponible durante los primeros **30 días** y la variable objetivo representa el abandono posterior a ese periodo.

El archivo procesado se encuentra en:

```text
data/base_estudiantes_simulada_limpia.csv
```

## Resultados del modelo final

Métricas obtenidas sobre el conjunto de prueba:

| Métrica | Resultado |
|---|---:|
| Accuracy | 0.6950 |
| Precision | 0.5202 |
| Recall | 0.6977 |
| F1-score | 0.5960 |
| ROC-AUC | 0.7724 |

Estas métricas corresponden al modelo final de **Regresión Logística** almacenado en `app/model/modelo_alerta_estudiantil.joblib`.

## Estructura

```text
alerta_estudiantil_api_web/
├── data/
│   └── base_estudiantes_simulada_limpia.csv
├── notebooks/
│   └── Guia_Practica_Mineria_Datos_Modelo_Final.ipynb
├── app/
│   ├── __init__.py
│   ├── main.py                 # Rutas FastAPI y archivos estáticos
│   ├── model_service.py        # Carga, transformación y predicción
│   ├── schemas.py              # Validaciones de entrada y salida
│   ├── model/
│   │   ├── modelo_alerta_estudiantil.joblib
│   │   └── metadata_modelo.json
│   └── static/
│       ├── index.html          # Interfaz principal
│       ├── app.js              # Consumo de la API
│       └── styles.css          # Estilos de la WebAPP
├── tests/
│   ├── test_api.py
│   └── test_model_service.py
├── Dockerfile
├── requirements.txt
├── .gitignore
├── .dockerignore
└── README.md
```

## Cuaderno de Minería de Datos

El archivo:

```text
notebooks/Guia_Practica_Mineria_Datos_Modelo_Final.ipynb
```

documenta la definición del problema, generación de datos, análisis exploratorio, tratamiento de calidad de datos, ingeniería de variables, clustering, comparación de modelos, validación cruzada, evaluación final y exportación del modelo.

Entre las variables derivadas utilizadas se encuentran:

- clics por día activo;
- tasa de entrega;
- tasa de actividad;
- logaritmo de clics;
- indicador de ausencia de nota.

## Ejecución local

Se recomienda **Python 3.12**.

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

- WebAPP: <http://127.0.0.1:8000>

La documentación automática de FastAPI puede habilitarse temporalmente durante una revisión técnica.

### Windows PowerShell

```powershell
$env:ENABLE_API_DOCS="1"
python -m uvicorn app.main:app --reload
```

## Endpoints

| Método | Ruta | Función |
|---|---|---|
| `GET` | `/api/v1/health` | Confirma que la API y el modelo están disponibles. |
| `GET` | `/api/v1/model-info` | Devuelve información, variables y métricas del modelo. |
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

La API calcula internamente las cinco variables derivadas empleadas durante el entrenamiento, por lo que el consumidor no puede modificarlas manualmente.

## Validaciones principales

- Solo se aceptan categorías conocidas por el modelo.
- Las variables se restringen a los rangos observados durante el entrenamiento.
- Los días activos deben encontrarse entre 0 y 30.
- Las tareas entregadas no pueden superar a las tareas asignadas.
- No puede registrarse actividad cuando los días activos son cero.
- La nota se limita al rango 0–100 y puede enviarse como `null`.
- Los campos adicionales se rechazan para evitar errores silenciosos.

## Pruebas

Con el entorno virtual activado:

```bash
python -m pytest -q
```

Las pruebas verifican la ingeniería de variables, inferencia del modelo, rango de probabilidad, validación de datos, endpoints y entrega de la interfaz web.

## Ejecución con Docker

```bash
docker build -t alerta-estudiantil .
docker run --rm -p 8000:8000 alerta-estudiantil
```

## Configuración opcional

- `MODEL_PATH`: ruta a otro archivo `.joblib` con el mismo contrato.
- `MODEL_METADATA_PATH`: ruta al archivo JSON de metadatos correspondiente.
- `ALLOWED_ORIGINS`: orígenes permitidos, separados por comas, si otro frontend consume la API.

Si se reemplaza el modelo, deben conservarse las claves `model`, `feature_columns` y `metadata` dentro del archivo exportado, además del orden exacto de variables descrito en `metadata_modelo.json`.

## Referencias de apoyo

El proyecto toma como referencia conceptual el **Open University Learning Analytics Dataset (OULAD)** y literatura sobre modelos predictivos de abandono y éxito académico. Las referencias completas se documentan en el cuaderno y en el informe final de la práctica.
