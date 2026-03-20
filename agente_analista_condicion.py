# ============================================================
# AGENTE 2 – ANALISTA DE CONDICIÓN DE ACTIVOS (VERSIÓN REALISTA)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.title("🧠 AGENTE 2 – Analista de Condición de Activos")

# ============================================================
# 1️⃣ MAESTRO DE EQUIPOS (IDs REALES)
# ============================================================

equipos = pd.DataFrame({
    "ID": [
        10000000,10000001,10000002,10000003,10000004,10000005,
        10000006,10000007,10000008,10000009,10000010,10000011,
        10000012,10000013,10000014,10000015,10000016,10000017,
        10000018,10000019,10000020,10000021,10000022,10000023,
        10000024,10000025,10000026,10000027,10000028
    ],
    "Nombre": [
        "BRAZO DE CARGUE","BRAZO DE CARGUE","BRAZO DE CARGUE","BRAZO DE CARGUE","BRAZO DE CARGUE","BRAZO DE CARGUE",
        "CARGADERO CRUDO VEHICULOS 1","CARGADERO CRUDO VEHICULOS 2",
        "56ABR1 ANILLO BOQUILLAS ROCIADOR","56ABR2 ANILLO BOQUILLAS ROCIADOR","56ABR3 ANILLO BOQUILLAS ROCIADOR",
        "56ABR4 ANILLO BOQUILLAS ROCIADOR","56ABR5 ANILLO BOQUILLAS ROCIADOR","56ABR9 ANILLO BOQUILLAS ROCIADOR",
        "56ABR8 ANILLO BOQUILLAS ROCIADOR",
        "56CE01 CAMARA ESPUMA","56CE02 CAMARA ESPUMA","56CE03 CAMARA ESPUMA",
        "56CE04 CAMARA ESPUMA","56CE05 CAMARA ESPUMA","56CE06 CAMARA ESPUMA",
        "CAMARA ESPUMA","CAMARA ESPUMA",
        "56HF001 MONITOR HIDRANTE","56HF002 MONITOR HIDRANTE","56HF003 MONITOR HIDRANTE",
        "56HF004 MONITOR HIDRANTE","56HF005 MONITOR HIDRANTE","56HF006 MONITOR HIDRANTE"
    ]
})

# Clasificación por tipo
equipos["Tipo"] = equipos["Nombre"].apply(lambda x: 
    "BRAZO" if "BRAZO" in x else
    "ROCIADOR" if "ABR" in x else
    "ESPUMA" if "CE" in x else
    "HIDRANTE" if "HF" in x else
    "OTRO"
)

# ============================================================
# 2️⃣ SELECCIÓN DE ACTIVO
# ============================================================

activo = st.selectbox(
    "Seleccionar Activo",
    equipos["ID"],
    format_func=lambda x: f"{x} - {equipos.loc[equipos['ID']==x, 'Nombre'].values[0]}"
)

info_activo = equipos[equipos["ID"] == activo].iloc[0]

st.markdown(f"**Tipo:** {info_activo['Tipo']}")

# ============================================================
# 3️⃣ GENERACIÓN DE DATOS (SIMULACIÓN DIFERENCIADA)
# ============================================================

def generar_datos_activo(id_activo, tipo):

    fechas = pd.date_range(end=datetime.today(), periods=180)

    np.random.seed(id_activo % 1000)

    # Parámetros por tipo
    if tipo == "BRAZO":
        base_vib, base_temp = 4.5, 70
    elif tipo == "ROCIADOR":
        base_vib, base_temp = 3.5, 60
    elif tipo == "ESPUMA":
        base_vib, base_temp = 3.0, 55
    elif tipo == "HIDRANTE":
        base_vib, base_temp = 2.5, 50
    else:
        base_vib, base_temp = 4.0, 65

    vibracion = np.random.normal(base_vib, 0.5, len(fechas))
    temperatura = np.random.normal(base_temp, 3, len(fechas))

    # Degradación
    vibracion += np.linspace(0, np.random.uniform(1,3), len(fechas))
    temperatura += np.linspace(0, np.random.uniform(2,6), len(fechas))

    # Fallas
    fallas = np.random.choice([0,1], size=len(fechas), p=[0.92,0.08])

    return pd.DataFrame({
        "Fecha": fechas,
        "Vibracion": vibracion,
        "Temperatura": temperatura,
        "Falla": fallas
    })

df = generar_datos_activo(activo, info_activo["Tipo"])

# ============================================================
# 4️⃣ DETECCIÓN DE ANOMALÍAS
# ============================================================

df["Z_Vibracion"] = (df["Vibracion"] - df["Vibracion"].mean()) / df["Vibracion"].std()
df["Anomalia"] = df["Z_Vibracion"].abs() > 2

# ============================================================
# 5️⃣ MTBF
# ============================================================

fechas_falla = df[df["Falla"] == 1]["Fecha"]

if len(fechas_falla) > 1:
    mtbf = fechas_falla.diff().dropna().mean().days
else:
    mtbf = 0

# ============================================================
# 6️⃣ CLASIFICACIÓN
# ============================================================

total_fallas = df["Falla"].sum()
anomalias = df["Anomalia"].sum()

if total_fallas < 5 and anomalias < 5:
    estado = "🟢 Estable"
elif total_fallas < 10:
    estado = "🟡 En Observación"
elif total_fallas < 20:
    estado = "🟠 Degradándose"
else:
    estado = "🔴 Crítico"

# ============================================================
# 7️⃣ DASHBOARD
# ============================================================

col1, col2, col3 = st.columns(3)

col1.metric("Total Fallas", int(total_fallas))
col2.metric("Anomalías", int(anomalias))
col3.metric("MTBF (días)", int(mtbf))

st.subheader("Estado del Activo")
st.markdown(f"## {estado}")

# ============================================================
# 8️⃣ GRÁFICAS
# ============================================================

fig1 = px.line(df, x="Fecha", y="Vibracion", title="Vibración")
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.line(df, x="Fecha", y="Temperatura", title="Temperatura")
st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# 9️⃣ ALERTAS
# ============================================================

st.subheader("🚨 Alertas")

if anomalias > 10:
    st.error("Alta cantidad de anomalías. Revisar inmediatamente.")
elif anomalias > 5:
    st.warning("Comportamiento inestable.")
else:
    st.success("Operación normal.")

# ============================================================
# 🔟 PREDICCIÓN DE FALLA
# ============================================================

tendencia = np.polyfit(range(len(df)), df["Vibracion"], 1)[0]

if tendencia > 0.01:
    st.warning("📈 Tendencia creciente de vibración.")
else:
    st.success("📊 Sin tendencia crítica.")
