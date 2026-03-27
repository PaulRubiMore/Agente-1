import streamlit as st
import pandas as pd

st.title("Agente de Mantenimiento - Órdenes y Fallas")

# =========================
# CARGA ROBUSTA DE DATOS
# =========================
def cargar_ordenes():
    archivo = st.file_uploader("Sube archivo de órdenes", type=["xlsx"])

    if archivo is not None:
        return pd.read_excel(archivo)

    # fallback si existe en repo
    try:
        return pd.read_excel("ordenes.xlsx")
    except FileNotFoundError:
        st.error("No hay archivo disponible. Sube un Excel.")
        st.stop()

ordenes = cargar_ordenes()

# =========================
# VALIDACIÓN DE ESTRUCTURA
# =========================
columnas_requeridas = ["equipo", "fecha", "tipo_ot", "falla", "tiempo_paro", "costo"]

faltantes = [col for col in columnas_requeridas if col not in ordenes.columns]

if faltantes:
    st.error(f"Faltan columnas: {faltantes}")
    st.stop()

# =========================
# LIMPIEZA
# =========================
ordenes["tipo_ot"] = ordenes["tipo_ot"].str.lower()
ordenes["fecha"] = pd.to_datetime(ordenes["fecha"], errors="coerce")

# =========================
# GENERACIÓN DE FALLAS DESDE ÓRDENES
# =========================
def calcular_fallas(df):
    df_fallas = df[df["tipo_ot"] == "correctivo"]

    resumen = df_fallas.groupby("equipo").agg({
        "falla": "count",
        "tiempo_paro": "sum",
        "costo": "sum"
    }).reset_index()

    resumen.columns = ["equipo", "num_fallas", "tiempo_total", "costo_total"]

    return resumen

resumen_fallas = calcular_fallas(ordenes)

# =========================
# CRITICIDAD SIMPLE
# =========================
def calcular_criticidad(df):
    df["criticidad"] = (
        df["num_fallas"] * 0.5 +
        df["tiempo_total"] * 0.3 +
        df["costo_total"] * 0.2
    )

    return df.sort_values(by="criticidad", ascending=False)

criticidad = calcular_criticidad(resumen_fallas)

# =========================
# OUTPUT
# =========================
st.subheader("Órdenes cargadas")
st.dataframe(ordenes)

st.subheader("Resumen de fallas por equipo")
st.dataframe(resumen_fallas)

st.subheader("Ranking de criticidad")
st.dataframe(criticidad)
