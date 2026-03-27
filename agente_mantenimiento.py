import pandas as pd
import numpy as np

# -----------------------------
# UTILIDADES
# -----------------------------
def normalizar(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-9)

# -----------------------------
# PREPARAR DATOS SAP
# -----------------------------
def preparar_ordenes(df):
    
    df = df.rename(columns={
        "Equipo": "id_activo",
        "Fecha de inicio extrema": "fecha_inicio",
        "Fecha real de fin de la orden": "fecha_fin",
        "Clase de orden": "tipo_mtto",
        "Texto breve": "descripcion",
        "Total general (real)": "costo",
        "Trabajo real": "duracion"
    })
    
    df["fecha_inicio"] = pd.to_datetime(df["fecha_inicio"])
    df["fecha_fin"] = pd.to_datetime(df["fecha_fin"], errors="coerce")
    
    # calcular duración si no viene
    df["duracion"] = np.where(
        df["duracion"] > 0,
        df["duracion"],
        (df["fecha_fin"] - df["fecha_inicio"]).dt.total_seconds() / 3600
    )
    
    return df


def preparar_fallas_desde_avisos(df):
    
    df = df.rename(columns={
        "Equipo": "id_activo",
        "Inicio de avería": "fecha",
        "Fin de avería": "fin_falla",
        "Duración de parada": "duracion_falla",
        "Descripción": "modo_falla",
        "Prioridad": "prioridad"
    })
    
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["fin_falla"] = pd.to_datetime(df["fin_falla"], errors="coerce")
    
    return df[[
        "id_activo",
        "fecha",
        "fin_falla",
        "duracion_falla",
        "modo_falla",
        "prioridad"
    ]]

# -----------------------------
# CLASIFICACIÓN DE FALLAS (opcional)
# -----------------------------
def clasificar_modo_falla(texto):
    
    texto = str(texto).lower()
    
    if "comunicacion" in texto:
        return "comunicaciones"
    elif "electrico" in texto:
        return "electrico"
    elif "mecanico" in texto:
        return "mecanico"
    elif "instrument" in texto:
        return "instrumentacion"
    
    return "otros"

# -----------------------------
# FEATURE ENGINEERING
# -----------------------------
def calcular_features(ordenes, fallas):
    
    # -----------------
    # FALLAS
    # -----------------
    freq_falla = fallas.groupby("id_activo").size().rename("frecuencia_falla")
    
    # MTBF
    mtbf_list = []
    for activo, df in fallas.groupby("id_activo"):
        df = df.sort_values("fecha")
        if len(df) > 1:
            diffs = df["fecha"].diff().dt.total_seconds() / 3600
            mtbf_list.append((activo, diffs.mean()))
    
    mtbf = pd.DataFrame(mtbf_list, columns=["id_activo", "mtbf"]).set_index("id_activo")
    
    # impacto (downtime)
    impacto = fallas.groupby("id_activo")["duracion_falla"].mean().rename("impacto")
    
    # tiempo desde última falla
    ultima_falla = fallas.groupby("id_activo")["fecha"].max()
    ahora = pd.Timestamp.now()
    
    t_ultima = (ahora - ultima_falla).dt.total_seconds() / 3600
    t_ultima = t_ultima.rename("t_ultima_falla")
    
    # -----------------
    # ORDENES
    # -----------------
    mttr = ordenes.groupby("id_activo")["duracion"].mean().rename("mttr")
    costo = ordenes.groupby("id_activo")["costo"].sum().rename("costo_total")
    
    # -----------------
    # MERGE
    # -----------------
    features = pd.concat([
        freq_falla,
        mtbf,
        impacto,
        t_ultima,
        mttr,
        costo
    ], axis=1).fillna(0)
    
    return features

# -----------------------------
# CRITICIDAD
# -----------------------------
def calcular_criticidad(features):
    
    features["criticidad"] = (
        0.30 * normalizar(features["frecuencia_falla"]) +
        0.20 * normalizar(features["impacto"]) +
        0.15 * normalizar(features["mttr"]) +
        0.15 * normalizar(features["costo_total"]) +
        0.20 * (1 - normalizar(features["t_ultima_falla"]))
    )
    
    return features

# -----------------------------
# ALERTAS
# -----------------------------
def generar_alertas(features):
    
    alertas = []
    
    for activo, row in features.iterrows():
        
        if row["frecuencia_falla"] > features["frecuencia_falla"].quantile(0.75):
            alertas.append((activo, "Alta frecuencia de fallas"))
        
        if row["impacto"] > features["impacto"].quantile(0.75):
            alertas.append((activo, "Alto impacto operativo"))
        
        if row["mttr"] > features["mttr"].quantile(0.75):
            alertas.append((activo, "Alto tiempo de reparación"))
        
        if row["t_ultima_falla"] < 24:
            alertas.append((activo, "Falla reciente"))
    
    return pd.DataFrame(alertas, columns=["id_activo", "alerta"])

# -----------------------------
# AGENTE PRINCIPAL
# -----------------------------
class AgenteCondicionActivos:
    
    def ejecutar(self, ordenes_df, avisos_df):
        
        # preparar datos
        ordenes = preparar_ordenes(ordenes_df)
        fallas = preparar_fallas_desde_avisos(avisos_df)
        
        # clasificar modos de falla
        fallas["categoria_falla"] = fallas["modo_falla"].apply(clasificar_modo_falla)
        
        # features
        features = calcular_features(ordenes, fallas)
        features = calcular_criticidad(features)
        
        # alertas
        alertas = generar_alertas(features)
        
        return {
            "features": features.sort_values("criticidad", ascending=False),
            "alertas": alertas,
            "fallas": fallas
        }


# -----------------------------
# EJECUCIÓN
# -----------------------------
if __name__ == "__main__":
    
    ordenes = pd.read_excel("ordenes.xlsx")
    avisos = pd.read_excel("avisos.xlsx")
    
    agente = AgenteCondicionActivos()
    
    resultado = agente.ejecutar(ordenes, avisos)
    
    print("\n=== TOP ACTIVOS CRÍTICOS ===")
    print(resultado["features"].head())
    
    print("\n=== ALERTAS ===")
    print(resultado["alertas"].head())
