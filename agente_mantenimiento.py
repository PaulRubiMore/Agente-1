# =============================================================================
# AGENTE ANALISTA DE CONDICIÓN DE ACTIVOS (VERSIÓN CLOUD ROBUSTA)
# SIN SKLEARN
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np

# =============================================================================
# 1. DATASET (simulación o reemplazar por tu fuente real)
# =============================================================================

@st.cache_data
def generar_data():
    np.random.seed(42)

    n_equipos = 20
    equipos = [f"EQ_{i:03d}" for i in range(n_equipos)]

    data = []
    for eq in equipos:
        for mes in range(1, 13):
            data.append({
                "equipo": eq,
                "mes": mes,
                "fallas_mes": np.random.poisson(lam=np.random.randint(0, 5)),
                "tiempo_operacion": np.random.randint(100, 300),
                "tiempo_reparacion": np.random.randint(1, 10),
                "costo_mantenimiento": np.random.randint(1000, 10000),
                "criticidad_actual": np.random.randint(1, 5),
                "centro": f"C{np.random.randint(1,4)}",
                "area": f"A{np.random.randint(1,6)}"
            })

    return pd.DataFrame(data)

df = generar_data()

# =============================================================================
# 2. FEATURE ENGINEERING
# =============================================================================

df["mtbf"] = df["tiempo_operacion"] / (df["fallas_mes"] + 1)
df["mttr"] = df["tiempo_reparacion"]

df["frecuencia_fallas_30d"] = df["fallas_mes"]
df["frecuencia_fallas_90d"] = (
    df.groupby("equipo")["fallas_mes"]
    .rolling(3)
    .mean()
    .reset_index(0, drop=True)
)

df["costo_mantenimiento_acum"] = df.groupby("equipo")["costo_mantenimiento"].cumsum()

# =============================================================================
# 3. TENDENCIA (sin sklearn)
# =============================================================================

def calcular_tendencia(grupo):
    y = grupo["fallas_mes"].values
    x = np.arange(len(y))
    if len(y) < 2:
        return 0
    return np.polyfit(x, y, 1)[0]

tendencias = (
    df.groupby("equipo", group_keys=False)
    .apply(lambda g: calcular_tendencia(g))
    .reset_index(name="pendiente_fallas")
)

df = df.merge(tendencias, on="equipo", how="left")

# =============================================================================
# 4. DETECCIÓN DE ANOMALÍAS (Z-SCORE)
# =============================================================================

def detectar_anomalias(grupo):
    z = (grupo - grupo.mean()) / (grupo.std() + 1e-6)
    return (np.abs(z) > 2.5).astype(int)

df["flag_anomalia"] = (
    df.groupby("equipo")["frecuencia_fallas_30d"]
    .transform(detectar_anomalias)
)

# =============================================================================
# 5. CLASIFICACIÓN
# =============================================================================

def clasificar_estado(row):
    if row["flag_anomalia"] == 1 and row["pendiente_fallas"] > 0:
        return "CRITICO"
    elif row["pendiente_fallas"] > 0:
        return "DEGRADANDO"
    elif row["frecuencia_fallas_30d"] == 0:
        return "ESTABLE"
    else:
        return "NORMAL"

df["estado_activo"] = df.apply(clasificar_estado, axis=1)

# =============================================================================
# 6. SCORE DE CRITICIDAD
# =============================================================================

df["criticidad_score"] = (
    0.3 * (1 / (df["mtbf"] + 1)) +
    0.2 * df["mttr"] +
    0.2 * df["frecuencia_fallas_30d"] +
    0.2 * df["costo_mantenimiento_acum"] +
    0.1 * df["flag_anomalia"]
)

df["criticidad_score"] = (
    (df["criticidad_score"] - df["criticidad_score"].min()) /
    (df["criticidad_score"].max() - df["criticidad_score"].min())
)

# =============================================================================
# 7. FORECAST (regresión simple con numpy)
# =============================================================================

def forecast_fallas(grupo, pasos=3):
    y = grupo["fallas_mes"].values
    x = np.arange(len(y))

    if len(y) < 2:
        return [0]*pasos

    coef = np.polyfit(x, y, 1)
    future_x = np.arange(len(y), len(y)+pasos)

    return (coef[0]*future_x + coef[1]).tolist()

forecast = (
    df.groupby("equipo", group_keys=False)
    .apply(lambda g: forecast_fallas(g))
    .to_dict()
)

# =============================================================================
# 8. ALERTAS
# =============================================================================

df_alertas = df[df["estado_activo"].isin(["CRITICO", "DEGRADANDO"])]

# =============================================================================
# 9. UI STREAMLIT
# =============================================================================

st.title("Agente Analista de Condición de Activos")

st.subheader("Clasificación de Activos")
st.dataframe(df[[
    "equipo", "estado_activo", "criticidad_score",
    "centro", "area"
]].drop_duplicates())

st.subheader("Alertas")
st.dataframe(df_alertas[[
    "equipo", "estado_activo",
    "criticidad_score", "pendiente_fallas"
]])

st.subheader("Forecast de Fallas")
equipo_sel = st.selectbox("Seleccionar equipo", df["equipo"].unique())
st.write(forecast[equipo_sel])
