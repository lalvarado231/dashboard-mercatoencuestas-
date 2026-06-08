import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard Automatizado con Filtro de Fechas e Indicadores - Il Mercato")
st.markdown("---")

# 1. FUNCIÓN HÍBRIDA INTELIGENTE PARA CALCULAR EL NPS (SOPORTA HISTÓRICO Y NUEVO)
def calcular_nps_hibrido(df, col_nps, col_estrellas):
    total_respuestas = 0
    promotores = 0
    detractores = 0
    
    for _, fila in df.iterrows():
        voto_nuevo = pd.to_numeric(fila.get(col_nps), errors='coerce')
        voto_viejo = pd.to_numeric(fila.get(col_estrellas), errors='coerce')
        
        # Caso A: Tiene el formato nuevo (0 al 10)
        if not pd.isna(voto_nuevo):
            total_respuestas += 1
            if voto_nuevo >= 9:
                promotores += 1
            elif voto_nuevo <= 6:
                detractores += 1
                
        # Caso B: No tiene formato nuevo, pero tiene el histórico de 5 estrellas
        elif not pd.isna(voto_viejo):
            total_respuestas += 1
            if voto_viejo == 5:      
                promotores += 1
            elif voto_viejo == 4:    
                pass 
            else:                    
                detractores += 1

    if total_respuestas == 0:
        return None
        
    pct_promotores = (promotores / total_respuestas) * 100
    pct_detractores = (detractores / total_respuestas) * 100
    return pct_promotores - pct_detractores

# 2. PROCESADOR AUTOMÁTICO DE ARCHIVOS CRUDOS DE TALLY (CSV)
@st.cache_data(show_spinner=False)  
def procesar_tally_csv(archivo_path):
    if not os.path.exists(archivo_path):
        return None
        
    try:
        df = pd.read_csv(archivo_path, encoding='utf-8')
    except:
        try:
            df = pd.read_csv(archivo_path, encoding='latin1')
        except:
            return None
            
    # Limpieza estricta de espacios en los nombres de las columnas para evitar fallas de Tally
    df.columns = df.columns.str.strip()
    
    col_origen_unidad = "Selecciona la unidad que visitaste / Select the Il Mercato Gentiloni location you visited"
    
    if col_origen_unidad in df.columns:
        df['Restaurante_Origen'] = df[col_origen_unidad].astype(str).str.strip().str.upper()
        df['Restaurante_Origen'] = df['Restaurante_Origen'].replace({'ÁLAMO': 'ALAMO'})
        
        # Buscar dinámicamente la columna de fecha de envío
        col_fecha_tally = None
        for col in df.columns:
            if 'submitted' in col.lower() or 'fecha' in col.lower():
                col_fecha_tally = col
                break
        
        if col_fecha_tally and col_fecha_tally in df.columns:
            df['Fecha_Envio'] = pd.to_datetime(df[col_fecha_tally], errors='coerce').dt.date
        else:
            df['Fecha_Envio'] = datetime.today().date()
            
        return df.copy()
        
    return None

# 3. DETECTAR EL ARCHIVO DE TALLY
todos_los_archivos = [f for f in os.listdir('.') if f.lower().endswith('.csv')]

if len(todos_los_archivos) == 0:
    st.error("⚠️ No se encontraron archivos de Tally (.csv) en el repositorio. Por favor sube tu archivo a GitHub.")
else:
    todos_los_archivos.sort(reverse=True)
    archivo_actual = todos_los_archivos[0]

    df_raw = procesar_tally_csv(archivo_actual)
    
    if df_raw is not None:
        df_completo = df_raw.copy()
        
        col_mesero = 'Selecciona a la persona que te atendió / Select the person who assisted you'
        col_comentario = 'Cuéntanos cómo fue tu experiencia / Tell us about your visit'
        
        # Nombres exactos mapeados tras limpiar los espacios del CSV
        col_calif = 'Califica la atención recibida / How would you rate your experience?'
        col_nps_nueva = '¿Qué tan probable es que nos recomiende a un familiar, amigo o colega? /How likely are you to recommend us to a friend, family member, or colleague?'
        
        if col_calif in df_completo.columns:
            df_completo[col_calif] = pd.to_numeric(df_completo[col_calif], errors='coerce')

        # --- CONFIGURACIÓN DE FECHAS ---
        fechas_validas = df_completo['Fecha_Envio'].dropna()
        if not fechas_validas.empty:
            min_fecha = min(fechas_validas)
            max_fecha = max(fechas_validas)
            
            def_act_inicio = max_fecha - timedelta(days=6)
            def_act_fin = max_fecha
            def_ant_inicio = def_act_inicio - timedelta(days=7)
            def_ant_fin = def_act_inicio - timedelta(days=1)
        else:
            min_fecha = datetime.today().date() - timedelta(days=60)
            max_fecha = datetime.today().date()
            def
