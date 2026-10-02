"""Esquemas públicos de entrada y salida de la API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PredictionInput(BaseModel):
    """Variables observables durante los primeros 30 días del curso."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
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
            ]
        },
    )

    modalidad: Literal["Semipresencial", "Virtual"] = Field(
        description="Modalidad en la que cursa el estudiante."
    )
    nivel_educativo_previo: Literal[
        "Bachillerato", "Técnico", "Universitario"
    ] = Field(description="Máximo nivel educativo completado antes del curso.")
    edad: int = Field(
        ge=18,
        le=54,
        description="Edad en años, limitada al rango observado al entrenar.",
    )
    intentos_previos: int = Field(
        ge=0,
        le=3,
        description="Número de intentos previos, dentro del rango de entrenamiento.",
    )
    creditos_matriculados: Literal[30, 60, 90, 120] = Field(
        description="Carga académica matriculada."
    )
    dias_anticipacion_registro: float | None = Field(
        default=None,
        ge=-20,
        le=100,
        description=(
            "Días entre el registro y el inicio del curso; puede omitirse si no consta."
        ),
    )
    clicks_30_dias: int = Field(
        ge=0,
        le=8_676,
        description="Interacciones registradas, dentro del rango de entrenamiento.",
    )
    dias_activos_30: int = Field(
        ge=0, le=30, description="Días con al menos una interacción durante la ventana."
    )
    tareas_asignadas_30: int = Field(
        ge=4,
        le=8,
        description="Tareas asignadas en los primeros 30 días.",
    )
    tareas_entregadas_30: int = Field(
        ge=0, le=8, description="Tareas entregadas en los primeros 30 días."
    )
    nota_promedio_30: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Promedio de calificaciones; nulo cuando todavía no existe nota.",
    )
    solicito_soporte: bool = Field(
        default=False, description="Indica si el estudiante solicitó soporte."
    )

    @model_validator(mode="after")
    def validar_coherencia(self) -> "PredictionInput":
        if self.tareas_entregadas_30 > self.tareas_asignadas_30:
            raise ValueError(
                "Las tareas entregadas no pueden superar las tareas asignadas."
            )
        if self.dias_activos_30 == 0 and self.clicks_30_dias > 0:
            raise ValueError(
                "No puede haber clics si el número de días activos es cero."
            )
        return self


class DerivedIndicators(BaseModel):
    clicks_por_dia_activo: float
    tasa_entrega_30: float
    tasa_actividad_30: float
    sin_nota_30: bool


class PredictionResponse(BaseModel):
    probabilidad_abandono: float = Field(ge=0, le=1)
    porcentaje_riesgo: float = Field(ge=0, le=100)
    prediccion: Literal["alerta", "sin_alerta"]
    nivel_riesgo: Literal["alto", "bajo"]
    umbral_clasificacion: float
    indicadores_derivados: DerivedIndicators
    recomendacion: str
    advertencia: str


class HealthResponse(BaseModel):
    estado: Literal["ok"]
    modelo_cargado: bool
    nombre_modelo: str


class ModelInfoResponse(BaseModel):
    nombre_modelo: str
    tipo_base: str
    ventana_observacion_dias: int
    objetivo: str
    umbral_clasificacion: float
    metricas_prueba: dict[str, float | str]
    variables_entrada_api: list[str]
    limitacion: str
