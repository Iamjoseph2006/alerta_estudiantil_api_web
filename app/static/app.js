const form = document.querySelector("#prediction-form");
const submitButton = document.querySelector("#submit-button");
const formMessage = document.querySelector("#form-message");
const apiState = document.querySelector("#api-state");
const emptyResult = document.querySelector("#empty-result");
const predictionResult = document.querySelector("#prediction-result");

const examples = {
  low: {
    modalidad: "Semipresencial",
    nivel_educativo_previo: "Universitario",
    edad: 27,
    intentos_previos: 0,
    creditos_matriculados: 60,
    dias_anticipacion_registro: 55,
    clicks_30_dias: 900,
    dias_activos_30: 24,
    tareas_asignadas_30: 6,
    tareas_entregadas_30: 6,
    nota_promedio_30: 88,
    solicito_soporte: false,
  },
  high: {
    modalidad: "Virtual",
    nivel_educativo_previo: "Bachillerato",
    edad: 34,
    intentos_previos: 2,
    creditos_matriculados: 90,
    dias_anticipacion_registro: 5,
    clicks_30_dias: 45,
    dias_activos_30: 4,
    tareas_asignadas_30: 7,
    tareas_entregadas_30: 1,
    nota_promedio_30: 52,
    solicito_soporte: true,
  },
};

function setApiState(kind, text) {
  apiState.classList.remove("online", "offline");
  apiState.classList.add(kind);
  apiState.querySelector("span:last-child").textContent = text;
}

async function checkApi() {
  try {
    const response = await fetch("/api/v1/health", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Respuesta no disponible");
    const data = await response.json();
    setApiState("online", `API disponible · ${data.nombre_modelo}`);
  } catch (_error) {
    setApiState("offline", "API no disponible");
  }
}

function setExample(example) {
  Object.entries(example).forEach(([name, value]) => {
    const field = form.elements.namedItem(name);
    if (!field) return;
    if (field.type === "checkbox") field.checked = Boolean(value);
    else field.value = value ?? "";
  });
  hideMessage();
  form.querySelector("input, select")?.focus();
}

function optionalNumber(formData, name) {
  const value = formData.get(name);
  return value === null || value === "" ? null : Number(value);
}

function createPayload() {
  const data = new FormData(form);
  return {
    modalidad: data.get("modalidad"),
    nivel_educativo_previo: data.get("nivel_educativo_previo"),
    edad: Number(data.get("edad")),
    intentos_previos: Number(data.get("intentos_previos")),
    creditos_matriculados: Number(data.get("creditos_matriculados")),
    dias_anticipacion_registro: optionalNumber(data, "dias_anticipacion_registro"),
    clicks_30_dias: Number(data.get("clicks_30_dias")),
    dias_activos_30: Number(data.get("dias_activos_30")),
    tareas_asignadas_30: Number(data.get("tareas_asignadas_30")),
    tareas_entregadas_30: Number(data.get("tareas_entregadas_30")),
    nota_promedio_30: optionalNumber(data, "nota_promedio_30"),
    solicito_soporte: data.get("solicito_soporte") === "on",
  };
}

function showMessage(message) {
  formMessage.textContent = message;
  formMessage.hidden = false;
}

function hideMessage() {
  formMessage.hidden = true;
  formMessage.textContent = "";
}

function apiErrorMessage(data) {
  if (!Array.isArray(data?.detail)) return data?.detail || "No se pudo calcular la predicción.";
  return data.detail
    .map((item) => item.msg?.replace(/^Value error, /, "") || "Dato inválido")
    .join(" ");
}

function renderResult(data) {
  const highRisk = data.prediccion === "alerta";
  const percentage = data.porcentaje_riesgo;
  const meter = document.querySelector(".risk-meter");
  const status = document.querySelector("#result-status");

  emptyResult.hidden = true;
  predictionResult.hidden = false;
  document.querySelector("#risk-number").textContent = percentage.toLocaleString("es-EC", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  });
  document.querySelector("#risk-meter-fill").style.width = `${percentage}%`;
  meter.setAttribute("aria-valuenow", String(percentage));
  meter.classList.toggle("high", highRisk);
  status.classList.toggle("high", highRisk);
  status.textContent = highRisk ? "Alerta de seguimiento" : "Sin alerta en este momento";
  document.querySelector("#recommendation").textContent = data.recomendacion;
  document.querySelector("#delivery-rate").textContent = `${(
    data.indicadores_derivados.tasa_entrega_30 * 100
  ).toFixed(1)} %`;
  document.querySelector("#activity-rate").textContent = `${(
    data.indicadores_derivados.tasa_actividad_30 * 100
  ).toFixed(1)} %`;
  document.querySelector("#click-rate").textContent =
    data.indicadores_derivados.clicks_por_dia_activo.toLocaleString("es-EC", {
      maximumFractionDigits: 1,
    });
  document.querySelector("#model-note").textContent = data.advertencia;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideMessage();

  if (!form.reportValidity()) return;

  submitButton.disabled = true;
  submitButton.textContent = "Calculando…";
  try {
    const response = await fetch("/api/v1/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(createPayload()),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(apiErrorMessage(data));
    renderResult(data);
  } catch (error) {
    showMessage(error.message || "No fue posible conectar con la API.");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Calcular riesgo";
  }
});

document.querySelector("#example-low").addEventListener("click", () => setExample(examples.low));
document.querySelector("#example-high").addEventListener("click", () => setExample(examples.high));

checkApi();

