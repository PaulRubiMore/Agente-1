import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

# -----------------------------
# UTILIDADES
# -----------------------------
def normalizar(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-9)

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def calcular_features(ordenes, fallas, condicion):
    
    # Frecuencia de falla
    freq_falla = fallas.groupby("id_activo").size().rename("frecuencia_falla")
    
    # MTTR
    mttr = ordenes.groupby("id_activo")["duracion"].mean().rename("mttr")
    
    # Costos
    costo = ordenes.groupby("id_activo")["costo"].sum().rename("costo_total")
    
    # Tendencia de condición
    tendencias = []
    
    for activo, df in condicion.groupby("id_activo"):
        df = df.sort_values("fecha")
        if len(df) > 2:
            X = np.arange(len(df)).reshape(-1,1)
            y = df["valor"].values
            modelo = LinearRegression().fit(X, y)
            tendencias.append((activo, modelo.coef_[0], np.std(y)))
    
    tendencia_df = pd.DataFrame(tendencias, columns=["id_activo", "tendencia", "volatilidad"])
    tendencia_df = tendencia_df.set_index("id_activo")
    
    # Merge
    features = pd.concat([freq_falla, mttr, costo, tendencia_df], axis=1).fillna(0)
    
    return features

# -----------------------------
# CRITICIDAD
# -----------------------------
def calcular_criticidad(features):
    
    features["criticidad"] = (
        0.35 * normalizar(features["frecuencia_falla"]) +
        0.25 * normalizar(features["mttr"]) +
        0.20 * normalizar(features["costo_total"]) +
        0.20 * normalizar(features["tendencia"])
    )
    
    return features

# -----------------------------
# ANOMALÍAS
# -----------------------------
def detectar_anomalias(condicion):
    
    resultados = []
    
    for activo, df in condicion.groupby("id_activo"):
        if len(df) < 10:
            continue
        
        modelo = IsolationForest(contamination=0.05)
        df["anomaly"] = modelo.fit_predict(df[["valor"]])
        
        df["anomaly"] = df["anomaly"].apply(lambda x: 1 if x == -1 else 0)
        
        resultados.append(df)
    
    return pd.concat(resultados)

# -----------------------------
# PRONÓSTICO SIMPLE
# -----------------------------
def pronostico(condicion, pasos=5):
    
    forecasts = []
    
    for activo, df in condicion.groupby("id_activo"):
        df = df.sort_values("fecha")
        
        if len(df) < 5:
            continue
        
        X = np.arange(len(df)).reshape(-1,1)
        y = df["valor"].values
        
        modelo = LinearRegression().fit(X, y)
        
        futuros = np.arange(len(df), len(df)+pasos).reshape(-1,1)
        pred = modelo.predict(futuros)
        
        forecasts.append({
            "id_activo": activo,
            "predicciones": pred.tolist()
        })
    
    return pd.DataFrame(forecasts)

# -----------------------------
# AGENTE PRINCIPAL
# -----------------------------
class AgenteCondicionActivos:
    
    def __init__(self):
        pass
    
    def ejecutar(self, activos, ordenes, fallas, condicion):
        
        features = calcular_features(ordenes, fallas, condicion)
        features = calcular_criticidad(features)
        
        anomalías = detectar_anomalias(condicion)
        pronos = pronostico(condicion)
        
        return {
            "features": features,
            "anomalias": anomalías,
            "pronosticos": pronos
        }
