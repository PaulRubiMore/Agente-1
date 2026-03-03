# ============================================================
# AGENTE 1 – GENERADOR DE PLANES DE MANTENIMIENTO
# VERSIÓN STREAMLIT
# ============================================================

import streamlit as st
import pandas as pd
import random

st.set_page_config(layout="wide")

st.title("🧠 Agente Generador de Planes de Mantenimiento")

st.markdown("Simulación automática de activos y criticidad")

# ============================================================
# FUNCIÓN PARA GENERAR ACTIVOS
# ============================================================

def generar_activos(cantidad):

    tipos = ["Motor", "Bomba", "Compresor", "Ventilador", "Transformador"]
    lista_activos = []

    for i in range(cantidad):

        nombre = random.choice(tipos) + " " + str(i+1)

        probabilidad = random.randint(1, 5)
        impacto_produccion = random.randint(1, 5)
        impacto_costo = random.randint(1, 5)

        lista_activos.append({
            "Activo": nombre,
            "Probabilidad_Falla": probabilidad,
            "Impacto_Produccion": impacto_produccion,
            "Impacto_Costo": impacto_costo
        })

    return pd.DataFrame(lista_activos)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("⚙ Parámetros")

cantidad = st.sidebar.slider("Cantidad de activos", 10, 300, 50)

if st.sidebar.button("Generar Activos"):

    df = generar_activos(cantidad)

    # Cálculos
    df["Consecuencia"] = df["Impacto_Produccion"] + df["Impacto_Costo"]
    df["Criticidad"] = df["Probabilidad_Falla"] * df["Consecuencia"]

    def clasificar(criticidad):
        if criticidad >= 40:
            return "ALTA"
        elif criticidad >= 20:
            return "MEDIA"
        else:
            return "BAJA"

    df["Nivel_Criticidad"] = df["Criticidad"].apply(clasificar)

    def recomendar_plan(nivel):
        if nivel == "ALTA":
            return "Predictivo + Monitoreo"
        elif nivel == "MEDIA":
            return "Preventivo Optimizado"
        else:
            return "Correctivo Planificado"

    df["Plan_Recomendado"] = df["Nivel_Criticidad"].apply(recomendar_plan)

    # Mostrar resultados
    st.subheader("📊 Matriz de Criticidad")
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Resumen por Nivel")
    resumen = df["Nivel_Criticidad"].value_counts()
    st.bar_chart(resumen)

else:
    st.info("Seleccione la cantidad y presione 'Generar Activos'")
