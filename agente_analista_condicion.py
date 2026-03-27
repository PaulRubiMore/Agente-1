# ============================================================
# SIMULADOR DE TRASLADO DE ACTIVOS + CRITICIDAD DINÁMICA
# ============================================================

import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")
st.title("🔄 Simulación de Criticidad por Traslado de Activos")

# ============================================================
# GENERAR ACTIVOS
# ============================================================

def generar_activos(n):

    tipos = ["Motor", "Bomba", "Compresor"]
    areas = ["Produccion", "Servicios", "Backup"]

    data = []

    for i in range(n):
        data.append({
            "Activo": f"{random.choice(tipos)} {i+1}",
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

def factor_contexto(area, redundancia, criticidad_proceso):

    factor = 1

    if area == "Produccion":
        factor *= 1.5
    elif area == "Backup":
        factor *= 0.7

    if redundancia == 0:
        factor *= 1.4

    factor *= (criticidad_proceso / 3)

    return factor

# ============================================================
# CALCULO CRITICIDAD
# ============================================================

def calcular_criticidad(df):

    df["Factor_Contexto"] = df.apply(
        lambda x: factor_contexto(
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
# RECOMENDACIÓN
# ============================================================

def clasificar(c):
    if c >= 40:
        return "ALTA"
    elif c >= 20:
        return "MEDIA"
    else:
        return "BAJA"

def plan(nivel):
    if nivel == "ALTA":
        return "Predictivo"
    elif nivel == "MEDIA":
        return "Preventivo"
    else:
        return "Correctivo"

# ============================================================
# APP
# ============================================================

df = generar_activos(50)
df = calcular_criticidad(df)

df["Nivel"] = df["Criticidad"].apply(clasificar)
df["Plan"] = df["Nivel"].apply(plan)

# -------------------------------
# SELECCIÓN ACTIVO
# -------------------------------

activo_sel = st.selectbox("Selecciona un activo", df["Activo"])

activo = df[df["Activo"] == activo_sel].iloc[0]

st.subheader("📍 Estado Actual")

col1, col2, col3 = st.columns(3)

col1.metric("Área", activo["Area"])
col2.metric("Criticidad", round(activo["Criticidad"],2))
col3.metric("Nivel", activo["Nivel"])

# -------------------------------
# SIMULACIÓN CAMBIO
# -------------------------------

st.subheader("🔧 Simular traslado / cambio")

nueva_area = st.selectbox("Nueva Área", ["Produccion", "Servicios", "Backup"])
nueva_redundancia = st.selectbox("Redundancia", [0,1])
nuevo_proceso = st.slider("Criticidad del proceso", 1, 5, int(activo["Criticidad_Proceso"]))

# -------------------------------
# CALCULO NUEVO
# -------------------------------

nuevo_factor = factor_contexto(nueva_area, nueva_redundancia, nuevo_proceso)

nueva_criticidad = (
    activo["Probabilidad_Falla"] *
    activo["Consecuencia"] *
    nuevo_factor
)

nuevo_nivel = clasificar(nueva_criticidad)
nuevo_plan = plan(nuevo_nivel)

# -------------------------------
# RESULTADO
# -------------------------------

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

# -------------------------------
# ALERTA
# -------------------------------

if nuevo_nivel != activo["Nivel"]:
    st.warning("⚠ Cambio de criticidad detectado → se debe actualizar estrategia de mantenimiento")

# -------------------------------
# PLAN
# -------------------------------

st.subheader("🧠 Plan Recomendado")

st.write("ANTES:", activo["Plan"])
st.write("DESPUÉS:", nuevo_plan)

# -------------------------------
# TABLA COMPLETA
# -------------------------------

st.subheader("📋 Todos los activos")

st.dataframe(df, use_container_width=True)
