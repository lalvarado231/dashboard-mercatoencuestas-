import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")

st.title("📊 Dashboard de Operaciones, Control de Experiencia & NPS 360°")
st.subheader("🏢 Centro de Inteligencia Operativa — Il Mercato Gentiloni")
st.markdown("---")

# Función NPS
def calcular_nps_hibrido(df, col_nps, col_estrellas):
    if df.empty: return None
    promotheus = 0
    detractores = 0
    total_validas = 0
    
    for _, fila in df.iterrows():
        voto_nuevo = pd.to_numeric(fila.get(col_nps), errors='coerce')
        voto_viejo = pd.to_numeric(fila.get(col_estrellas), errors='coerce')
        
        if not pd.isna(voto_nuevo):
            total_validas += 1
            if voto_nuevo >= 9: promotheus += 1
            elif voto_nuevo <= 6: detractores += 1
        elif not pd.isna(voto_viejo):
            total_validas += 1
            if voto_viejo == 5: promotheus += 1
            elif voto_viejo < 4: detractores += 1
            
    return ((promotheus - detractores) / total_validas * 100) if total_validas > 0 else None

# Procesar archivo
@st.cache_data(show_spinner=False)
def procesar_tally_csv(archivo_path):
    if not os.path.exists(archivo_path): return None
    df = pd.read_csv(archivo_path, encoding='latin1')
    df.columns = df.columns.str.strip()
    return df

# Carga de datos
todos_los_archivos = sorted([f for f in os.listdir('.') if f.lower().endswith('.csv')], reverse=True)
if not todos_los_archivos:
    st.error("No se encontró archivo CSV.")
else:
    df_completo = procesar_tally_csv(todos_los_archivos[0])
    
    # Identificación de columnas
    col_mesero = next((c for c in df_completo.columns if 'asistió' in c.lower() or 'assisted' in c.lower()), df_completo.columns[1])
    col_calif = next((c for c in df_completo.columns if 'califica' in c.lower() or 'rate' in c.lower()), df_completo.columns[2])
    col_nps = next((c for c in df_completo.columns if 'probable' in c.lower()), None)
    col_fecha = next((c for c in df_completo.columns if 'fecha' in c.lower() or 'submitted' in c.lower()), None)
    col_unidad = next((c for c in df_completo.columns if 'unidad' in c.lower() or 'location' in c.lower()), df_completo.columns[0])

    df_completo['Fecha_Envio'] = pd.to_datetime(df_completo[col_fecha], errors='coerce').dt.date if col_fecha else datetime.today().date()
    df_completo['Restaurante_Origen'] = df_completo[col_unidad].astype(str).str.upper()
    df_completo[col_calif] = pd.to_numeric(df_completo[col_calif], errors='coerce')
    total_absoluto = len(df_completo)

    # Sidebar
    st.sidebar.header("📅 Configuración")
    rango_act = st.sidebar.date_input("Rango Actual", value=(datetime.today()-timedelta(days=7), datetime.today()))
    unidades = sorted(df_completo['Restaurante_Origen'].unique())
    sel_unidades = st.sidebar.multiselect("Unidades", unidades, default=unidades)
    sel_calificaciones = st.sidebar.multiselect("Filtro Estrellas", [1,2,3,4,5], default=[1,2,3,4,5])

    # Filtrado
    df_base = df_completo[df_completo['Restaurante_Origen'].isin(sel_unidades)]
    df_act = df_base[(df_base['Fecha_Envio'] >= rango_act[0]) & (df_base['Fecha_Envio'] <= rango_act[1])]
    
    # MÉTRICAS
    m1, m2, m3, m4 = st.columns(4)
    
    # AQUÍ ESTÁ LA CORRECCIÓN: Contamos filas totales para que dé 166
    m1.metric("Total Encuestas (Envíos)", value=f"{len(df_act)} envíos", delta=f"Histórico: {total_absoluto}")
    
    prom = df_act[col_calif].mean()
    m2.metric("Promedio", f"{prom:.2f} ⭐" if not pd.isna(prom) else "N/A")
    
    nps = calcular_nps_hibrido(df_act, col_nps, col_calif)
    m3.metric("NPS", f"{nps:.1f}%" if nps is not None else "N/A")
    
    alertas = len(df_act[df_act[col_calif] <= 2])
    m4.metric("Alertas (1-2 ⭐)", alertas)

    # Gráficas
    df_filtrado = df_act[df_act[col_calif].isin(sel_calificaciones)]
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Volumen por Unidad")
        st.bar_chart(df_filtrado['Restaurante_Origen'].value_counts())
    
    with c2:
        st.subheader("Registro Detallado")
        st.dataframe(df_filtrado)
