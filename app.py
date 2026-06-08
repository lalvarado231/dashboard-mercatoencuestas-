import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard con Doble Comparativa y NPS - Il Mercato")
st.markdown("---")

# Meta u Objetivo del Grupo para el Semáforo de Calificaciones
META_CALIFICACION = 4.6

# 1. FUNCIÓN INTELIGENTE PARA CALCULAR EL NPS OFICIAL (-100 a +100)
def calcular_nps(df, columna_nps):
    if columna_nps not in df.columns or len(df) == 0:
        return None
    
    # Asegurar que los valores sean numéricos
    valores = pd.to_numeric(df[columna_nps], errors='coerce').dropna()
    total_respuestas = len(valores)
    
    if total_respuestas == 0:
        return None
        
    promotores = len(valores[valores >= 9])
    detractores = len(valores[valores <= 6])
    
    pct_promotores = (promotores / total_respuestas) * 100
    pct_detractores = (detractores / total_respuestas) * 100
    
    nps_score = pct_promotores - pct_detractores
    return nps_score

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
            
    col_origen_unidad = "Selecciona la unidad que visitaste / Select the Il Mercato Gentiloni location you visited"
    
    if col_origen_unidad in df.columns:
        df['Restaurante_Origen'] = df[col_origen_unidad].astype(str).str.strip().str.upper()
        df['Restaurante_Origen'] = df['Restaurante_Origen'].replace({'ÁLAMO': 'ALAMO'})
        
        # Encontrar dinámicamente la columna de fecha de envío en Tally (evita errores de mayúsculas/minúsculas)
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

# 3. DETECTAR EL ARCHIVO HISTÓRICO DE TALLY
todos_los_archivos = [f for f in os.listdir('.') if f.lower().endswith('.csv')]

if len(todos_los_archivos) == 0:
    st.error("⚠️ No se encontraron archivos de Tally (.csv) en el repositorio. Por favor sube tu archivo histórico de Tally a GitHub.")
else:
    # Seleccionar el archivo principal (el primero disponible)
    todos_los_archivos.sort(reverse=True)
    archivo_actual = todos_los_archivos[0]

    # Cargar Datos Base Completos
    df_raw = procesar_tally_csv(archivo_actual)
    
    if df_raw is not None:
        df_completo = df_raw.copy()
        
        col_mesero = 'Selecciona a la persona que te atendió / Select the person who assisted you'
        col_calif = 'Califica la atención recibida / How would you rate your experience?'
        col_comentario = 'Cuéntanos cómo fue tu experiencia / Tell us about your visit'
        
        # Buscador automático para la columna de NPS
        col_nps = None
        for col in df_completo.columns:
            if 'recomiende' in col.lower() or 'likely are you to recommend' in col.lower() or 'nps' in col.lower():
                col_nps = col
                break
        
        if col_calif in df_completo.columns:
            df_completo[col_calif] = pd.to_numeric(df_completo[col_calif], errors='coerce')

        # --- CONFIGURACIÓN DE FECHAS BASE EN EL ARCHIVO ---
        fechas_validas = df_completo['Fecha_Envio'].dropna()
        if not fechas_validas.empty:
            min_fecha = min(fechas_validas)
            max_fecha = max(fechas_validas)
            
            # Valores por defecto periodo actual (últimos 7 días)
            def_act_inicio = max_fecha - timedelta(days=6)
            def_act_fin = max_fecha
            
            # Valores por defecto periodo anterior (los 7 días previos a los de arriba)
            def_ant_inicio = def_act_inicio - timedelta(days=7)
            def_ant_fin = def_act_inicio - timedelta(days=1)
        else:
            min_fecha = datetime.today().date() - timedelta(days=60)
            max_fecha = datetime.today().date()
            def_act_inicio, def_act_fin = min_fecha + timedelta(days=30), max_fecha
            def_ant_inicio, def_ant_fin = min_fecha, min_fecha + timedelta(days=29)

        # --- BARRA LATERAL: DOBLE CALENDARIO DE RANGOS ---
        st.sidebar.header("📅 1. Periodo Actual (Evaluado)")
        rango_actual = st.sidebar.date_input(
            "Selecciona rango actual:",
            value=(def_act_inicio, def_act_fin),
            min_value=min_fecha,
            max_value=max_fecha,
            key="actual_range"
        )
        
        st.sidebar.markdown("---")
        st.sidebar.header("⏳ 2. Periodo Anterior (Comparativo)")
        rango_anterior = st.sidebar.date_input(
            "Selecciona rango a comparar:",
            value=(def_ant_inicio, def_ant_fin),
            min_value=min_fecha,
            max_value=max_fecha,
            key="anterior_range"
        )

        # Filtro de Unidades
        st.sidebar.markdown("---")
        st.sidebar.header("🏢 Filtro de Unidades")
        unidades = sorted([u for u in df_completo['Restaurante_Origen'].unique() if u != 'NAN'])
        sel_unidades = st.sidebar.multiselect("Selecciona Unidades:", unidades, default=unidades)

        # Filtro de Semáforo
        st.sidebar.markdown("---")
        st.sidebar.header("🚦 Filtro por Semáforo")
        opcion_semaforo = st.sidebar.radio(
            "Estatus a auditar (Afecta lista y tablas):",
            ["🔵 Mostrar Todo", "🟢 Cumplen Meta (>= 4.6 ⭐)", "🟡 En Observación (4.3 - 4.5 ⭐)", "🔴 Alerta Crítica (<= 4.2 ⭐)"],
            index=0
        )

        # --- PROCESAMIENTO Y FILTRADO DE LOS DOS PERIODOS ---
        # Filtro por unidad base común
        df_base_unidades = df_completo[df_completo['Restaurante_Origen'].isin(sel_unidades)].copy()

        # Separar Periodo Actual
        df_act = pd.DataFrame()
        if isinstance(rango_actual, tuple) and len(rango_actual) == 2:
            act_i, act_f = rango_actual
            df_act = df_base_unidades[(df_base_unidades['Fecha_Envio'] >= act_i) & (df_base_unidades['Fecha_Envio'] <= act_f)].copy()

        # Separar Periodo Anterior
        df_ant = pd.DataFrame()
        if isinstance(rango_anterior, tuple) and len(rango_anterior) == 2:
            ant_i, ant_f = rango_anterior
            df_ant = df_base_unidades[(df_base_unidades['Fecha_Envio'] >= ant_i) & (df_base_unidades['Fecha_Envio'] <= ant_f)].copy()

        # Aplicar Semáforo únicamente a la visualización y tablas específicas del final
        df_act_visual = df_act.copy()
        if col_calif in df_act_visual.columns:
            if "🟢" in opcion_semaforo:
                df_act_visual = df_act_visual[df_act_visual[col_calif] >= META_CALIFICACION].copy()
            elif "🟡" in opcion_semaforo:
                df_act_visual = df_act_visual[(df_act_visual[col_calif] >= 4.3) & (df_act_visual[col_calif] < META_CALIFICACION)].copy()
            elif "🔴" in opcion_semaforo:
                df_act_visual = df_act_visual[df_act_visual[col_calif] <= 4.2].copy()

        # --- SECCIÓN 1: MÉTRICAS COMPARATIVAS INTELIGENTES (DELTAS) ---
        st.subheader("📈 Comparativa de Rendimiento Operativo")
        
        if len(rango_actual) == 2 and len(rango_anterior) == 2:
            st.info(f"Análisis: Periodo Actual (**{rango_actual[0].strftime('%d/%m')} al {rango_actual[1].strftime('%d/%m')}**) vs Periodo Anterior (**{rango_anterior[0].strftime('%d/%m')} al {rango_anterior[1].strftime('%d/%m')}**)")

        m1, m2, m3, m4, m5 = st.columns(5)
        
        # Métrica 1: Volumen de Respuestas
        total_act = len(df_act)
        total_ant = len(df_ant)
        diff_total = total_act - total_ant
        m1.metric(label="Total Encuestas", value=f"{total_act} resp.", delta=f"{diff_total:+d} vs periodo ant.")
        
        # Métrica 2: Promedio de Estrellas Global
        prom_act, prom_ant = None, None
        if col_calif in df_act.columns and len(df_act) > 0:
            prom_act = df_act[col_calif].mean()
        if col_calif in df_ant.columns and len(df_ant) > 0:
            prom_ant = df_ant[col_calif].mean()
            
        if prom_act is not None and not pd.isna(prom_act):
            diff_prom = (prom_act - prom_ant) if (prom_ant is not None and not pd.isna(prom_ant)) else None
            m2.metric(label="Promedio Calificación", value=f"{prom_act:.2f} ⭐", delta=f"{diff_prom:+.2f} ⭐" if diff_prom is not None else None)
        else:
            m2.metric("Promedio Calificación", "N/A")

        # Métrica 3: ÍNDICE NPS DINÁMICO
        nps_act = calcular_nps(df_act, col_nps) if col_nps else None
        nps_ant = calcular_nps(df_ant, col_nps) if col_nps else None
        
        if nps_act is not None:
            diff_nps = (nps_act - nps_ant) if nps_ant is not None else None
            m3.metric(label="Índice NPS (Lealtad)", value=f"{nps_act:.1f}%", delta=f"{diff_nps:+.1f}% vs periodo ant." if diff_nps is not None else None)
        else:
            m3.metric("Índice NPS (Lealtad)", "N/A (Falta columna en Tally)")

        # Métrica 4: Alertas Críticas (1-2 ⭐)
        if col_calif in df_act.columns:
            alertas_act = len(df_act[df_act[col_calif] <= 2].dropna(subset=[col_calif]))
            alertas_ant = len(df_ant[df_ant[col_calif] <= 2].dropna(subset=[col_calif])) if len(df_ant) > 0 else 0
            diff_alertas = alertas_act - alertas_ant
            m4.metric(label="Alertas Críticas (1-2 ⭐)", value=alertas_act, delta=f"{diff_alertas:+d} quejas", delta_color="inverse")
        else:
            m4.metric("Alertas Críticas", "0")

        # Métrica 5: Total de Personal Evaluado
        meseros_act = df_act[col_mesero].dropna().nunique() if (col_mesero in df_act.columns and len(df_act) > 0) else 0
        meseros_ant = df_ant[col_mesero].dropna().nunique() if (col_mesero in df_ant.columns and len(df_ant) > 0) else 0
        diff_meseros = meseros_act - meseros_ant
        m5.metric(label="Meseros Evaluados", value=meseros_act, delta=f"{diff_meseros:+d} integrantes")

        # Semáforo de Texto General
        if prom_act is not None and not pd.isna(prom_act):
            if prom_act >= META_CALIFICACION:
                st.success(f"🟢 **Estatus del Periodo Evaluado: Excelente.** Promedio de {prom_act:.2f} ⭐")
            elif prom_act >=
