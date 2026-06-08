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

# 1. FUNCIÓN HÍBRIDA INTELIGENTE PARA CALCULAR EL NPS
def calcular_nps_hibrido(df, col_nps, col_estrellas):
    if not col_nps and not col_estrellas:
        return None
    total_respuestas = 0
    promotheus = 0
    detractores = 0
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
            elif voto_viejo == 4: pass
            else: detractores += 1
    if total_respuestas == 0: return None
    return ((promotheus / total_respuestas) * 100) - ((detractores / total_respuestas) * 100)

# 2. PROCESADOR DE ARCHIVOS
@st.cache_data(show_spinner=False)
def procesar_tally_csv(archivo_path):
    if not os.path.exists(archivo_path): return None
    try: df = pd.read_csv(archivo_path, encoding='utf-8')
    except:
        try: df = pd.read_csv(archivo_path, encoding='latin1')
        except: return None
    df.columns = df.columns.str.strip()
    col_origen_unidad = next((col for col in df.columns if 'unidad' in col.lower() or 'location' in col.lower()), None)
    if col_origen_unidad:
        df['Restaurante_Origen'] = df[col_origen_unidad].astype(str).str.strip().str.upper()
        col_fecha = next((col for col in df.columns if 'submitted' in col.lower() or 'fecha' in col.lower()), None)
        df['Fecha_Envio'] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date if col_fecha else datetime.today().date()
        return df
    return None

# 3. LÓGICA PRINCIPAL
todos_los_archivos = sorted([f for f in os.listdir('.') if f.lower().endswith('.csv')], reverse=True)
if not todos_los_archivos:
    st.error("⚠️ No se encontraron archivos de Tally.")
else:
    df_completo = procesar_tally_csv(todos_los_archivos[0])
    total_absoluto = len(df_completo)
    
    # Mapeo de columnas (simplificado para estabilidad)
    col_mesero = "Selecciona a la persona que te atendió / Select the person who assisted you"
    col_calif = "Califica la atención recibida / How would you rate your experience?"
    col_nps = "¿Qué tan probable es que nos recomiende a un familiar, amigo o colega? /How likely are you to recommend us to a friend, family member, or colleague?"
    
    # Filtros laterales
    rango_actual = st.sidebar.date_input("Rango actual:", (datetime.today() - timedelta(days=7), datetime.today()))
    sel_unidades = st.sidebar.multiselect("Unidades:", df_completo['Restaurante_Origen'].unique(), default=df_completo['Restaurante_Origen'].unique())
    
    df_act = df_completo[(df_completo['Restaurante_Origen'].isin(sel_unidades)) & 
                         (df_completo['Fecha_Envio'] >= rango_actual[0]) & 
                         (df_completo['Fecha_Envio'] <= rango_actual[1])]

    # MÉTRICAS
    st.subheader("📈 Rendimiento e Indicadores")
    m1, m2, m3, m4, m5 = st.columns(5)
    
    # LA CORRECCIÓN SOLICITADA:
    m1.metric("Total Encuestas (Envíos)", value=f"{len(df_act)} envíos", delta=f"Histórico: {total_absoluto}")
    
    # (El resto de tus métricas y gráficas van aquí abajo exactamente igual)
    prom = df_act[col_calif].mean() if col_calif in df_act.columns else 0
    m2.metric("Promedio", f"{prom:.2f} ⭐")
    m3.metric("NPS", f"{calcular_nps_hibrido(df_act, col_nps, col_calif):.1f}%")
    m4.metric("Alertas (1-2⭐)", len(df_act[df_act[col_calif] <= 2]))
    m5.metric("Colaboradores", df_act[col_mesero].nunique())
