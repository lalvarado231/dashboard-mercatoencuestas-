import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")

# Título
st.title("📊 Dashboard de Operaciones, Control de Experiencia & NPS 360°")
st.subheader("🏢 Centro de Inteligencia Operativa — Il Mercato Gentiloni")
st.markdown("---")

# 1. FUNCIÓN HÍBRIDA NPS
def calcular_nps_hibrido(df, col_nps, col_estrellas):
    if not col_nps and not col_estrellas: return None
    total_respuestas, promotheus, detractores = 0, 0, 0
    for _, fila in df.iterrows():
        voto_nuevo = pd.to_numeric(fila.get(col_nps), errors='coerce') if col_nps else None
        voto_viejo = pd.to_numeric(fila.get(col_estrellas), errors='coerce') if col_estrellas else None
        if voto_nuevo is not None and not pd.isna(voto_nuevo):
            total_respuestas += 1
            if voto_nuevo >= 9: promotheus += 1
            elif voto_nuevo <= 6: detractores += 1
        elif voto_viejo is not None and not pd.isna(voto_viejo):
            total_respuestas += 1
            if voto_viejo == 5: promotheus += 1
            elif voto_viejo != 4: detractores += 1
    return ((promotheus - detractores) / total_respuestas * 100) if total_respuestas > 0 else None

# 2. PROCESADOR DE ARCHIVOS
@st.cache_data
def procesar_tally_csv(archivo_path):
    df = pd.read_csv(archivo_path)
    df.columns = df.columns.str.strip()
    return df

# 3. LÓGICA DE DATOS
archivos = sorted([f for f in os.listdir('.') if f.lower().endswith('.csv')], reverse=True)
if archivos:
    df_completo = procesar_tally_csv(archivos[0])
    total_absoluto = len(df_completo)
    
    # Filtros
    rango = st.sidebar.date_input("Periodo:", (datetime.today()-timedelta(days=7), datetime.today()))
    unidades = st.sidebar.multiselect("Unidades:", df_completo.iloc[:,0].unique(), default=df_completo.iloc[:,0].unique())
    
    # Filtrado básico (ajusta los nombres de columnas según tu archivo)
    df_act = df_completo[df_completo.iloc[:,0].isin(unidades)]
    
    # --- MÉTRICAS ---
    st.subheader("📈 Rendimiento e Indicadores Claves del Periodo")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    # ESTA ES LA ÚNICA LÍNEA QUE CAMBIA:
    m1.metric("Total Encuestas (Envíos)", value=f"{len(df_act)} envíos", delta=f"Histórico: {total_absoluto}")
    
    # (Aquí mantienes el resto de tus m2, m3, m4, m5 como los tenías originalmente)
