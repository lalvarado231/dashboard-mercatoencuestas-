import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard con Doble Comparativa de Fechas - Il Mercato")
st.markdown("---")

# Meta u Objetivo del Grupo para el Semáforo de Calificaciones
META_CALIFICACION = 4.6

# 1. PROCESADOR AUTOMÁTICO DE ARCHIVOS CRUDOS DE TALLY (CSV)
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
        
        # Convertir la columna de fecha de Tally a formato de fecha real (Date)
        if 'Submitted at' in df.columns:
            df['Fecha_Envio'] = pd.to_datetime(df['Submitted at'], errors='coerce').dt.date
            
        return df.copy()
        
    return None

# 2. DETECTAR EL ARCHIVO HISTÓRICO DE TALLY
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

        # Aplicar Semáforo únicamente a la visualización y tablas específicas del final (para no romper métricas)
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
        
        # Mostrar confirmación de rangos arriba
        if len(rango_actual) == 2 and len(rango_anterior) == 2:
            st.info(f"Análisis: Periodo Actual (**{rango_actual[0].strftime('%d/%m')} al {rango_actual[1].strftime('%d/%m')}**) vs Periodo Anterior (**{rango_anterior[0].strftime('%d/%m')} al {rango_anterior[1].strftime('%d/%m')}**)")

        m1, m2, m3, m4 = st.columns(4)
        
        # Métrica 1: Volumen de Respuestas
        total_act = len(df_act)
        total_ant = len(df_ant)
        diff_total = total_act - total_ant
        m1.metric(
            label="Total Encuestas", 
            value=f"{total_act} resp.", 
            delta=f"{diff_total:+d} vs periodo ant."
        )
        
        # Métrica 2: Promedio de Estrellas Global
        prom_act, prom_ant = None, None
        if col_calif in df_act.columns and len(df_act) > 0:
            prom_act = df_act[col_calif].mean()
        if col_calif in df_ant.columns and len(df_ant) > 0:
            prom_ant = df_ant[col_calif].mean()
            
        if prom_act is not None and not pd.isna(prom_act):
            diff_prom = (prom_act - prom_ant) if (prom_ant is not None and not pd.isna(prom_ant)) else None
            m2.metric(
                label="Promedio Calificación", 
                value=f"{prom_act:.2f} ⭐", 
                delta=f"{diff_prom:+.2f} ⭐" if diff_prom is not None else None
            )
            # Semáforo visual dinámico
            if prom_act >= META_CALIFICACION:
                st.success(f"🟢 **Estatus del Periodo Evaluado: Excelente.** Promedio de {prom_act:.2f} ⭐")
            elif prom_act >= 4.3:
                st.warning(f"🟡 **Estatus del Periodo Evaluado: En Observación.** Promedio de {prom_act:.2f} ⭐")
            else:
                st.error(f"🔴 **Estatus del Periodo Evaluado: Alerta Crítica.** Promedio de {prom_act:.2f} ⭐")
        else:
            m2.metric("Promedio Calificación", "N/A")

        # Métrica 3: Alertas Críticas (1-2 ⭐)
        if col_calif in df_act.columns:
            alertas_act = len(df_act[df_act[col_calif] <= 2].dropna(subset=[col_calif]))
            alertas_ant = len(df_ant[df_ant[col_calif] <= 2].dropna(subset=[col_calif])) if len(df_ant) > 0 else 0
            diff_alertas = alertas_act - alertas_ant
            m3.metric(
                label="Alertas Críticas (1-2 ⭐)", 
                value=alertas_act, 
                delta=f"{diff_alertas:+d} quejas",
                delta_color="inverse"
            )
        else:
            m3.metric("Alertas Críticas", "0")

        # Métrica 4: Total de Personal Evaluado
        meseros_act = df_act[col_mesero].dropna().nunique() if (col_mesero in df_act.columns and len(df_act) > 0) else 0
        meseros_ant = df_ant[col_mesero].dropna().nunique() if (col_mesero in df_ant.columns and len(df_ant) > 0) else 0
        diff_meseros = meseros_act - meseros_ant
        m4.metric(
            label="Meseros Evaluados", 
            value=meseros_act, 
            delta=f"{diff_meseros:+d} integrantes"
        )

        st.markdown("---")

        # --- SECCIÓN 2: GRÁFICOS DINÁMICOS DEL PERIODO ACTUAL ---
        st.subheader("🏆 Análisis Visual del Periodo Actual Seleccionado")
        
        if len(df_act) == 0:
            st.warning("📋 No existen encuestas registradas para el Periodo Actual en los filtros seleccionados.")
        else:
            g1, g2, g3 = st.columns(3)
            
            with g1:
                st.markdown("##### 🏢 Volumen de Encuestas por Unidad")
                df_unidades = df_act['Restaurante_Origen'].value_counts().reset_index()
                df_unidades.columns = ['Unidad', 'Encuestas']
                fig_uni = px.bar(df_unidades, x='Encuestas', y='Unidad', orientation='h',
                                 color='Encuestas', color_continuous_scale='Teal', text_auto=True)
                fig_uni.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_uni, use_container_width=True)
            
            with g2:
                st.markdown("##### 🔝 Top 10 Meseros con Mayor Volumen")
                if col_mesero in df_act.columns and not df_act[col_mesero].dropna().empty:
                    top_volumen = df_act[col_mesero].value_counts().nlargest(10).reset_index()
                    top_volumen.columns = ['Mesero', 'Cantidad']
                    fig_vol = px.bar(top_volumen, x='Cantidad', y='Mesero', orientation='h', 
                                     color='Cantidad', color_continuous_scale='Blues', text_auto=True)
                    fig_vol.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_vol, use_container_width=True)
                else:
                    st.info("Sin datos de colaboradores.")
                    
            with g3:
                st.markdown("##### ⭐ Top 10 Meseros con Mejor Calificación")
                if col_mesero in df_act.columns and col_calif in df_act.columns and not df_act[col_mesero].dropna().empty:
                    conteo_votos = df_act[col_mesero].value_counts()
                    meseros_activos = conteo_votos.index
                    df_meseros_activos = df_act[df_act[col_mesero].isin(meseros_activos)]
                    
                    if not df_meseros_activos.empty:
                        top_calif = df_meseros_activos.groupby(col_mesero)[col_calif].mean().nlargest(10).reset_index()
                        top_calif.columns = ['Mesero', 'Promedio']
                        fig_cal = px.bar(top_calif, x='Promedio', y='Mesero', orientation='h',
                                         color='Promedio', color_continuous_scale='Reds', text_auto='.2f', range_x=[0,5])
                        fig_cal.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_cal, use_container_width=True)
                    else:
                        st.info("Sin promedios suficientes.")
                else:
                    st.info("Sin calificaciones disponibles.")

        # --- SECCIÓN 3: TABLA DE COMENTARIOS NEGATIVOS EN EL PERIODO ACTUAL ---
        if col_calif in df_act.columns and len(df_act) > 0:
            malos_comentarios = df_act[df_act[col_calif] <= 2].dropna(subset=[col_calif])
            if not malos_comentarios.empty:
                st.markdown("---")
                st.subheader("⚠️ Atención Inmediata: Comentarios Negativos (Periodo Actual)")
                columnas_existentes = [c for c in ['Restaurante_Origen', col_mesero, col_calif, col_comentario] if c in df_act.columns]
                st.dataframe(malos_comentarios[columnas_existentes], use_container_width=True)

        # --- SECCIÓN 4: REVISIÓN GLOBAL / AUDITORÍA DE DATOS ---
        st.markdown("---")
        st.subheader("📋 Consolidado de Datos Auditados (Filtrado por Semáforo)")
        if "🔵" not in opcion_semaforo:
            st.info(f"Filtro de Semáforo Activo: Mostrando únicamente registros en **{opcion_semaforo[2:]}** del periodo actual.")
        
        if len(df_act_visual) == 0:
            st.warning(f"No hay registros específicos que entren en la categoría {opcion_semaforo} para los días seleccionados.")
        else:
            columnas_finales = [c for c in ['Restaurante_Origen', col_mesero, col_calif, col_comentario, 'Submitted at'] if c in df_act_visual.columns]
            st.dataframe(df_act_visual[columnas_finales], use_container_width=True)
    else:
        st.error("Error al procesar la estructura del archivo. Revisa que sea el CSV correcto descargado de Tally.")
