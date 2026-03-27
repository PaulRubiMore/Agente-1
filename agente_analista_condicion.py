# ============================================================
# AGENTE – CRITICIDAD DINÁMICA + REUBICACIÓN DE ACTIVOS
# ============================================================

import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🔄 Criticidad Dinámica y Reubicación de Activos")

# ============================================================
# GENERAR ACTIVOS
# ============================================================

def generar_activos(n):

    tipos = ["Motor", "Bomba", "Compresor"]
    centros = ["CAP1", "CAMPO2"]
    areas = ["Produccion", "Servicios", "Backup"]

    data = []

    for i in range(n):
        data.append({
            "Activo": f"{random.choice(tipos)} {i+1}",
            "Centro": random.choice(centros),
            "Area": random.choice(areas),
            "Probabilidad_Falla": random.randint(1,5),
            "Impacto_Produccion": random.randint(1,5),
            "Impacto_Costo": random.randint(1,5),
            "Redundancia": random.choice([0,1]),
            "Criticidad_Proceso": random.randint(1,5)
        })

    df = pd.DataFrame(data)
    df["Consecuencia"] = df["Impacto_Produccion"] + df["Impacto_Costo"]

    return df

# ============================================================
# FACTOR CONTEXTO
# ============================================================

def factor_contexto(centro, area, redundancia, criticidad_proceso):

    factor = 1

    # Centro
    if centro == "CAMPO2":
        factor *= 1.3

    # Área
    mapa_area = {
        "Produccion": 1.5,
        "Servicios": 1.0,
        "Backup": 0.7
    }

    factor *= mapa_area[area]

    # Redundancia
    if redundancia == 0:
        factor *= 1.4

    # Proceso
    factor *= (criticidad_proceso / 3)

    return factor

# ============================================================
# CALCULAR CRITICIDAD
# ============================================================

def calcular_criticidad(df):

    df["Factor_Contexto"] = df.apply(
        lambda x: factor_contexto(
            x["Centro"],
            x["Area"],
            x["Redundancia"],
            x["Criticidad_Proceso"]
        ), axis=1
    )

    df["Criticidad"] = (
        df["Probabilidad_Falla"] *
        df["Consecuencia"] *
        df["Factor_Contexto"]
    )

    return df

# ============================================================
# CLASIFICACIÓN
# ============================================================

def clasificar(c):
    if c >= 40:
        return "ALTA"
    elif c >= 20:
        return "MEDIA"
    else:
        return "BAJA"

# ============================================================
# SESSION STATE (para persistencia en Streamlit)
# ============================================================

if "df" not in st.session_state:
    st.session_state.df = calcular_criticidad(generar_activos(50))
    st.session_state.df["Nivel"] = st.session_state.df["Criticidad"].apply(clasificar)

df = st.session_state.df

# ============================================================
# SELECCIÓN ACTIVO
# ============================================================

activo_sel = st.selectbox("Selecciona un activo", df["Activo"])

activo = df[df["Activo"] == activo_sel].iloc[0]

# ============================================================
# ESTADO ACTUAL
# ============================================================

st.subheader("📍 Estado Actual")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Centro", activo["Centro"])
col2.metric("Área", activo["Area"])
col3.metric("Criticidad", round(activo["Criticidad"],2))
col4.metric("Nivel", activo["Nivel"])

# ============================================================
# SIMULACIÓN DE REUBICACIÓN
# ============================================================

st.subheader("🔧 Simular Reubicación")

nuevo_centro = st.selectbox("Nuevo Centro", ["CAP1", "CAMPO2"])
nueva_area = st.selectbox("Nueva Área", ["Produccion", "Servicios", "Backup"])
nueva_redundancia = st.selectbox("Redundancia", [0,1])
nuevo_proceso = st.slider("Criticidad del proceso", 1, 5, int(activo["Criticidad_Proceso"]))

# ============================================================
# CALCULO NUEVO
# ============================================================

nuevo_factor = factor_contexto(
    nuevo_centro,
    nueva_area,
    nueva_redundancia,
    nuevo_proceso
)

nueva_criticidad = (
    activo["Probabilidad_Falla"] *
    activo["Consecuencia"] *
    nuevo_factor
)

nuevo_nivel = clasificar(nueva_criticidad)

# ============================================================
# COMPARACIÓN
# ============================================================

st.subheader("📊 Comparación")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Antes")
    st.metric("Criticidad", round(activo["Criticidad"],2))
    st.metric("Nivel", activo["Nivel"])

with col2:
    st.markdown("### Después")
    st.metric("Criticidad", round(nueva_criticidad,2))
    st.metric("Nivel", nuevo_nivel)

# ============================================================
# ALERTA
# ============================================================

if nuevo_nivel != activo["Nivel"]:
    st.warning("⚠ Cambio de criticidad detectado")

# ============================================================
# APLICAR REUBICACIÓN (ACTUALIZA TAXONOMÍA)
# ============================================================

if st.button("Aplicar Reubicación"):

    idx = df[df["Activo"] == activo_sel].index[0]

    st.session_state.df.loc[idx, "Centro"] = nuevo_centro
    st.session_state.df.loc[idx, "Area"] = nueva_area
    st.session_state.df.loc[idx, "Redundancia"] = nueva_redundancia
    st.session_state.df.loc[idx, "Criticidad_Proceso"] = nuevo_proceso

    # Recalcular criticidad
    st.session_state.df = calcular_criticidad(st.session_state.df)
    st.session_state.df["Nivel"] = st.session_state.df["Criticidad"].apply(clasificar)

    st.success("✅ Activo reubicado y criticidad actualizada")

# ============================================================
# TABLA FINAL
# ============================================================

st.subheader("📋 Activos actualizados")

st.dataframe(st.session_state.df, use_container_width=True)
