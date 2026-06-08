import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

# Configuración
st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard de Operaciones, Control de Experiencia & NPS 360°")
st.subheader("🏢 Centro de Inteligencia Operativa — Il Mercato Gentiloni")
st.markdown("---")

# Función NPS Híbrido
def calcular_nps_hibrido(df, col_nps, col_estrellas):
    if df.empty: return None
    total_respuestas, promotheus, detractores = 0, 0, 0
    for _, fila in df.iterrows():
        v = pd.to_numeric(fila.get(col_nps), errors='coerce')
        if not pd.isna(v):
            total_respuestas += 1
            if v >= 9: promotheus += 1
            elif v <= 6: detractores += 1
    return ((promotheus - detractores) / total_respuestas * 100) if total_respuestas > 0 else None

# Procesador
@st.cache_data(show_spinner=False)
def procesar_tally_csv(archivo_path):
    df = pd.read_csv(archivo_path, encoding='utf-8')
    df.columns = df.columns.str.strip()
    # Identificar columnas clave
    col_unidad = next((c for c in df.columns if 'unidad' in c.lower()), df.columns[0])
    df['Restaurante_Origen'] = df[col_unidad].astype(str).str.strip().str.upper().replace('ÁLAMO', 'ALAMO')
    col_fecha = next((c for c in df.columns if 'submitted' in c.lower() or 'fecha' in c.lower()), None)
    df['Fecha_Envio'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date if col_fecha else datetime.today().date()
    return df

# Carga de datos
todos_los_archivos = sorted([f for f in os.listdir('.') if f.lower().endswith('.csv')], reverse=True)
if not todos_los_archivos:
    st.error("No se encontró el archivo CSV.")
else:
    df_completo = procesar_tally_csv(todos_los_archivos[0])
    
    # Mapeo de columnas
    col_mesero = next((c for c in df_completo.columns if 'persona' in c.lower()), df_completo.columns[1])
    col_calif = next((c for c in df_completo.columns if 'califica' in c.lower()), None)
    col_nps_nueva = next((c for c in df_completo.columns if 'probable' in c.lower()), None)
    col_comentario = next((c for c in df_completo.columns if 'experiencia' in c.lower()), None)

    # --- BARRA LATERAL ---
    rango_actual = st.sidebar.date_input("Periodo Actual:", (datetime.today()-timedelta(days=7), datetime.today()))
    unidades = sorted(df_completo['Restaurante_Origen'].unique())
    sel_unidades = st.sidebar.multiselect("Unidades:", unidades, default=unidades)

    # --- FILTRO TRANSPARENTE (SIN DROPNA) ---
    # Este df_act cuenta EXACTAMENTE las filas que cumplan los criterios, sin descartar filas vacías.
    df_act = df_completo[
        (df_completo['Restaurante_Origen'].isin(sel_unidades)) & 
        (df_completo['Fecha_Envio'] >= rango_actual[0]) & 
        (df_completo['Fecha_Envio'] <= rango_actual[1])
    ].copy()

    # --- MÉTRICAS ---
    st.subheader("📈 Rendimiento e Indicadores Claves")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    # M1: Conteo directo de filas filtradas
    m1.metric("Total Encuestas (Envíos)", value=f"{len(df_act)} resp.")
    
    # Resto de métricas (calculadas sobre los datos filtrados)
    prom_act = df_act[col_calif].mean() if col_calif else 0
    m2.metric("Promedio Calificación", f"{prom_act:.2f} ⭐")
    m3.metric("NPS", f"{calcular_nps_hibrido(df_act, col_nps_nueva, col_calif):.1f}%")
    m4.metric("Alertas (1-2⭐)", len(df_act[df_act[col_calif] <= 2]) if col_calif else 0)
    m5.metric("Meseros Evaluados", df_act[col_mesero].nunique())

    # Registro
    st.markdown("---")
    st.dataframe(df_act, use_container_width=True)
