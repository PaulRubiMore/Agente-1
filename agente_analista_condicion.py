# ============================================================
# AGENTE DE CRITICIDAD + REUBICACIÓN DE ACTIVOS
# ============================================================

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Agente de Criticidad", layout="wide")

st.title("🔧 Agente de Evaluación de Activos")

# ============================================================
# 1. DATA INICIAL (SIMULADA)
# ============================================================

data = [
    {
        "id": "10000001",
        "ubicacion": "CAP1",
        "frecuencia_fallas": 70,
        "costo_mantenimiento": 60,
        "impacto_operacional": 65,
        "criticidad": "MEDIA"
    },
    {
        "id": "10000002",
        "ubicacion": "CAP1",
        "frecuencia_fallas": 30,
        "costo_mantenimiento": 40,
        "impacto_operacional": 35,
        "criticidad": "BAJA"
    }
]

df = pd.DataFrame(data)

# ============================================================
# 2. FUNCIONES
# ============================================================

def factor_contexto(ubicacion):
    if ubicacion == "CAMPO2":
        return 1.5   # Producción
    elif ubicacion == "CAP1":
        return 0.8   # Backup
    else:
        return 1.0

def calcular_criticidad(row, nueva_ubicacion):

    base = (
        row["frecuencia_fallas"] * 0.4 +
        row["costo_mantenimiento"] * 0.3 +
        row["impacto_operacional"] * 0.3
    )

    return base * factor_contexto(nueva_ubicacion)

def clasificar(score):
    if score > 80:
        return "CRITICO"
    elif score > 50:
        return "ALTO"
    else:
        return "MEDIO"

def actualizar_taxonomia(row, nueva_ubicacion):

    row["ubicacion"] = nueva_ubicacion

    if nueva_ubicacion == "CAMPO2":
        row["centro"] = "OPERACION"
        row["area"] = "PRODUCCION"

    elif nueva_ubicacion == "CAP1":
        row["centro"] = "SOPORTE"
        row["area"] = "BACKUP"

    return row

def procesar_evento(row, nueva_ubicacion):

    ubicacion_anterior = row["ubicacion"]

    # 1. actualizar taxonomía
    row = actualizar_taxonomia(row, nueva_ubicacion)

    # 2. recalcular criticidad
    score = calcular_criticidad(row, nueva_ubicacion)
    nueva_criticidad = clasificar(score)

    # 3. detectar cambio
    cambio = nueva_criticidad != row["criticidad"]

    row["criticidad"] = nueva_criticidad
    row["score"] = round(score, 2)
    row["cambio"] = cambio
    row["ubicacion_anterior"] = ubicacion_anterior

    return row

# ============================================================
# 3. UI
# ============================================================

st.subheader("📋 Activos")

st.dataframe(df)

# Selección de activo
activo_id = st.selectbox("Selecciona un activo", df["id"])

# Nueva ubicación
nueva_ubicacion = st.selectbox(
    "Nueva ubicación",
    ["CAP1", "CAMPO2"]
)

# ============================================================
# 4. PROCESAMIENTO
# ============================================================

if st.button("Procesar cambio"):

    activo = df[df["id"] == activo_id].iloc[0].copy()

    resultado = procesar_evento(activo, nueva_ubicacion)

    st.subheader("📊 Resultado")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Antes")
        st.write("Ubicación:", resultado["ubicacion_anterior"])
        st.write("Criticidad:", activo["criticidad"])

    with col2:
        st.markdown("### Después")
        st.write("Ubicación:", resultado["ubicacion"])
        st.write("Criticidad:", resultado["criticidad"])
        st.write("Score:", resultado["score"])

    if resultado["cambio"]:
        st.warning("⚠ Cambio de criticidad detectado")

    # ========================================================
    # LOG
    # ========================================================

    log = pd.DataFrame([{
        "equipo": resultado["id"],
        "ubicacion_anterior": resultado["ubicacion_anterior"],
        "ubicacion_nueva": resultado["ubicacion"],
        "criticidad": resultado["criticidad"],
        "score": resultado["score"]
    }])

    st.subheader("🧾 Log de cambios")
    st.dataframe(log)
