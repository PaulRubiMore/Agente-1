# ============================================================
# AGENTE 1 – GENERADOR AUTOMÁTICO DE ACTIVOS
# ============================================================

import pandas as pd
import random

# ============================================================
# 1️⃣ FUNCIÓN PARA CREAR ACTIVOS ALEATORIOS
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
# 2️⃣ GENERAR 50 ACTIVOS (PUEDES CAMBIAR EL NÚMERO)
# ============================================================

df = generar_activos(50)

# ============================================================
# 3️⃣ CALCULAR CONSECUENCIA Y CRITICIDAD
# ============================================================

df["Consecuencia"] = df["Impacto_Produccion"] + df["Impacto_Costo"]
df["Criticidad"] = df["Probabilidad_Falla"] * df["Consecuencia"]

# ============================================================
# 4️⃣ CLASIFICACIÓN AUTOMÁTICA
# ============================================================

def clasificar(criticidad):
    if criticidad >= 40:
        return "ALTA"
    elif criticidad >= 20:
        return "MEDIA"
    else:
        return "BAJA"

df["Nivel_Criticidad"] = df["Criticidad"].apply(clasificar)

# ============================================================
# 5️⃣ RECOMENDACIÓN DE PLAN
# ============================================================

def recomendar_plan(nivel):
    if nivel == "ALTA":
        return "Predictivo + Monitoreo"
    elif nivel == "MEDIA":
        return "Preventivo Optimizado"
    else:
        return "Correctivo Planificado"

df["Plan_Recomendado"] = df["Nivel_Criticidad"].apply(recomendar_plan)

# ============================================================
# 6️⃣ MOSTRAR RESULTADO
# ============================================================

print("\n📊 MATRIZ DE CRITICIDAD GENERADA\n")
print(df.head())  # solo muestra los primeros 5

print("\n🔢 RESUMEN POR NIVEL DE CRITICIDAD\n")
print(df["Nivel_Criticidad"].value_counts())
