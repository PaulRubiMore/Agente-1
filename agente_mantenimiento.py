import pandas as pd
import numpy as np
import streamlit as st

# =========================================================
# UTILIDADES
# =========================================================
def normalizar(s):
    return (s - s.min()) / (s.max() - s.min() + 1e-9)


def limpiar_columnas(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(".", "", regex=False)
    )
    return df


# =========================================================
# CARGA DE DATOS (CORREGIDO STREAMLIT CLOUD)
# =========================================================
def cargar_ordenes():
    archivo = st.file_uploader("Subir archivo IWAN (Órdenes SAP)", type=["xlsx"])

    if archivo is not None:
        df = pd.read_excel(archivo, engine="openpyxl")
        return df
    else:
        st.warning("Sube el archivo de órdenes SAP")
        st.stop()


# =========================================================
# TRANSFORMACIÓN
# =========================================================
def transformar_ordenes(df):

    df = limpiar_columnas(df)

    columnas_clave = {
        "orden": "orden",
        "aviso": "aviso",
        "equipo": "id_activo",
        "ubicación_técnica": "ubicacion",
        "clase_de_orden": "tipo_orden",
        "prioridad": "prioridad",
        "total_general_(real)": "horas_real",
        "tota_general_(plan)": "horas_plan",
        "fecha_de_inicio_extrema": "fecha_inicio",
        "fecha_real_de_fin_de_la_orden": "fecha_fin"
    }

    # Validación de columnas existentes
    columnas_validas = [col for col in columnas_clave.keys() if col in df.columns]

    df = df[columnas_validas].rename(
        columns={k: v for k, v in columnas_clave.items() if k in columnas_validas}
    )

    return df


# =========================================================
# FEATURE ENGINEERING
# =========================================================
def generar_features(df):

    # Convertir numéricos
    df["horas_real"] = pd.to_numeric(df["horas_real"], errors="coerce").fillna(0)
    df["horas_plan"] = pd.to_numeric(df["horas_plan"], errors="coerce").fillna(0)

    # Clasificación de falla (correctivo)
    df["es_falla"] = (
        (df["tipo_orden"] == "PM02") &
        (df["aviso"].notna())
    ).astype(int)

    # Frecuencia de falla
    freq_falla = df.groupby("id_activo")["es_falla"].sum()

    # MTTR
    mttr = df.groupby("id_activo")["horas_real"].mean()

    # Carga de trabajo
    carga = df.groupby("id_activo")["horas_real"].sum()

    # Desviación
    df["desviacion"] = df["horas_real"] - df["horas_plan"]
    desviacion = df.groupby("id_activo")["desviacion"].mean()

    features = pd.concat([
        freq_falla.rename("frecuencia_falla"),
        mttr.rename("mttr"),
        carga.rename("carga_trabajo"),
        desviacion.rename("desviacion")
    ], axis=1).fillna(0)

    return features


# =========================================================
# CRITICIDAD
# =========================================================
def calcular_criticidad(features):

    features["criticidad"] = (
        0.4 * normalizar(features["frecuencia_falla"]) +
        0.3 * normalizar(features["mttr"]) +
        0.2 * normalizar(features["carga_trabajo"]) +
        0.1 * normalizar(abs(features["desviacion"]))
    )

    return features.sort_values("criticidad", ascending=False)


# =========================================================
# AGENTE
# =========================================================
class AgenteCondicionActivos:

    def ejecutar(self, df):

        df = transformar_ordenes(df)

        features = generar_features(df)

        criticidad = calcular_criticidad(features)

        return criticidad


# =========================================================
# STREAMLIT APP
# =========================================================
st.title("Agente Analista de Condición de Activos")

df = cargar_ordenes()

agente = AgenteCondicionActivos()
resultado = agente.ejecutar(df)

st.subheader("Clasificación de criticidad de activos")
st.dataframe(resultado)

st.download_button(
    "Descargar resultados",
    resultado.to_csv(index=True),
    "criticidad_activos.csv",
    "text/csv"
)
