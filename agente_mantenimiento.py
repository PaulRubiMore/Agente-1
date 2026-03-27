# =============================================================================
# AGENTE ANALISTA DE CONDICIÓN DE ACTIVOS
# =============================================================================
# Requisitos:
# pip install pandas numpy scikit-learn

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans

# =============================================================================
# 1. DATASET SIMULADO (puedes reemplazar por tu fuente real)
# =============================================================================

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

df = pd.DataFrame(data)

# =============================================================================
# 2. FEATURE ENGINEERING
# =============================================================================

# MTBF y MTTR
df["mtbf"] = df["tiempo_operacion"] / (df["fallas_mes"] + 1)
df["mttr"] = df["tiempo_reparacion"]

# Frecuencias
df["frecuencia_fallas_30d"] = df["fallas_mes"]
df["frecuencia_fallas_90d"] = df.groupby("equipo")["fallas_mes"].rolling(3).mean().reset_index(0,drop=True)

# Costos acumulados
df["costo_mantenimiento_acum"] = df.groupby("equipo")["costo_mantenimiento"].cumsum()

# =============================================================================
# 3. TENDENCIA DE FALLAS
# =============================================================================

def calcular_tendencia(grupo):
    y = grupo["fallas_mes"].values
    X = np.arange(len(y)).reshape(-1,1)
    if len(y) < 2:
        return 0
    return LinearRegression().fit(X, y).coef_[0]

tendencias = df.groupby("equipo").apply(calcular_tendencia).reset_index()
tendencias.columns = ["equipo", "pendiente_fallas"]

df = df.merge(tendencias, on="equipo", how="left")

# =============================================================================
# 4. DETECCIÓN DE ANOMALÍAS
# =============================================================================

features_model = [
    "mtbf",
    "mttr",
    "frecuencia_fallas_30d",
    "costo_mantenimiento_acum",
    "pendiente_fallas"
]

X = df[features_model].fillna(0)

model_anom = IsolationForest(contamination=0.05, random_state=42)
df["anomalia"] = model_anom.fit_predict(X)
df["flag_anomalia"] = (df["anomalia"] == -1).astype(int)

# =============================================================================
# 5. CLASIFICACIÓN DE ESTADO
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
# 6. SCORE DE CRITICIDAD DINÁMICA
# =============================================================================

df["criticidad_score"] = (
    0.3 * (1 / (df["mtbf"] + 1)) +
    0.2 * df["mttr"] +
    0.2 * df["frecuencia_fallas_30d"] +
    0.2 * df["costo_mantenimiento_acum"] +
    0.1 * df["flag_anomalia"]
)

# Normalización
df["criticidad_score"] = (df["criticidad_score"] - df["criticidad_score"].min()) / (
    df["criticidad_score"].max() - df["criticidad_score"].min()
)

# =============================================================================
# 7. CLUSTER DE COMPORTAMIENTO (OPCIONAL)
# =============================================================================

kmeans = KMeans(n_clusters=4, random_state=42)
df["cluster"] = kmeans.fit_predict(X)

# =============================================================================
# 8. FORECAST DE FALLAS
# =============================================================================

def forecast_fallas(grupo, pasos=3):
    y = grupo["fallas_mes"].values
    X = np.arange(len(y)).reshape(-1,1)

    if len(y) < 2:
        return [0]*pasos

    model = LinearRegression().fit(X, y)
    future_X = np.arange(len(y), len(y)+pasos).reshape(-1,1)

    return model.predict(future_X).tolist()

forecast = df.groupby("equipo").apply(forecast_fallas).to_dict()

# =============================================================================
# 9. ALERTAS
# =============================================================================

df_alertas = df[df["estado_activo"].isin(["CRITICO", "DEGRADANDO"])]

alertas = df_alertas[[
    "equipo",
    "estado_activo",
    "criticidad_score",
    "pendiente_fallas",
    "centro",
    "area"
]]

# =============================================================================
# 10. OUTPUT FINAL
# =============================================================================

output = {
    "alertas": alertas.to_dict(orient="records"),
    "clasificacion_activos": df[[
        "equipo",
        "estado_activo",
        "criticidad_score",
        "cluster",
        "centro",
        "area"
    ]].drop_duplicates().to_dict(orient="records"),
    "forecast": forecast
}

# =============================================================================
# 11. EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    print("=== ALERTAS ===")
    print(pd.DataFrame(output["alertas"]).head())

    print("\n=== CLASIFICACIÓN ===")
    print(pd.DataFrame(output["clasificacion_activos"]).head())

    print("\n=== FORECAST (ejemplo) ===")
    for k, v in list(output["forecast"].items())[:3]:
        print(k, "->", v)
