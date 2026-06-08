import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard Unificado con Histórico y NPS - Il Mercato")
st.markdown("---")

# Meta u Objetivo del Grupo para el Semáforo de Calificaciones
META_CALIFICACION = 4.6

# 1. FUNCIÓN HÍBRIDA INTELIGENTE PARA CALCULAR EL NPS (SOPORTA 1-5 Y 0-10)
def calcular_nps_hibrido(df, col_nps_nueva, col_estrellas_vieja):
    total_respuestas = 0
    promotores = 0
    detractores = 0
    
    # Recorrer fila por fila para rescatar el histórico de forma justa
    for _, fila in df.iterrows():
        voto_nuevo = pd.to_numeric(fila.get(col_nps_nueva), errors='coerce')
        voto_viejo = pd.to_numeric(fila.get(col_estrellas_vieja), errors='coerce')
        
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
            if voto_viejo == 5:      # 5 estrellas equivale a un Promotor (9-10)
                promotores += 1
            elif voto_viejo == 4:    # 4 estrellas equivale a un Pasivo (7-8)
                pass 
            else:                    # 1, 2 o 3 estrellas equivale a un Detractor (0-6)
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

# 3. DETECTAR EL ARCHIVO HISTÓRICO DE TALLY
todos_los_archivos = [f for f in os.listdir('.') if f.lower().endswith('.csv')]

if len(todos_los_archivos) == 0:
    st.error("⚠️ No se encontraron archivos de Tally (.csv) en el repositorio. Por favor sube tu archivo completo a GitHub.")
else:
    todos_los_archivos.sort(reverse=True)
    archivo_actual = todos_los_archivos[0]

    df_raw = procesar_tally_csv(archivo_actual)
    
    if df_raw is not None:
        df_completo = df_raw.copy()
        
        col_mesero = 'Selecciona a la persona que te atendió / Select the person who assisted you'
        col_calif = 'Califica la atención recibida / How would you rate your experience?'
        col_comentario = 'Cuéntanos cómo fue tu experiencia / Tell us about your visit'
        
        # Mapeo dinámico de las dos columnas de Tally (La vieja y la nueva de escala lineal)
        col_nps_nueva = None
        col_estrellas_vieja = col_calif # La de estrellas coincide con la calificación de atención recibida
        
        for col in df_completo.columns:
            col_min = col.lower()
            # Identificar la nueva columna lineal que creaste del 0 al 10
            if ('recomiend' in col_min or 'recommend' in col_min or 'probable' in col_min) and col != col_calif:
                col_nps_nueva = col
                break
        
        if col_calif in df_completo.columns:
            df_completo[col_calif] = pd.to_numeric(df_completo[col_calif], errors='coerce')

        # --- CONFIGURACIÓN DE FECHAS BASE EN EL ARCHIVO ---
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

        st.sidebar.markdown("---")
        st.sidebar.header("🏢 Filtro de Unidades")
        unidades = sorted([u for u in df_completo['Restaurante_Origen'].unique() if u != 'NAN'])
        sel_unidades = st.sidebar.multiselect("Selecciona Unidades:", unidades, default=unidades)

        st.sidebar.markdown("---")
        st.sidebar.header("🚦 Filtro por Semáforo")
        opcion_semaforo = st.sidebar.radio(
            "Estatus a auditar (Afecta lista y tablas):",
            ["🔵 Mostrar Todo", "🟢 Cumplen Meta (>= 4.6 ⭐)", "🟡 En Observación (4.3 - 4.5 ⭐)", "🔴 Alerta Crítica (<= 4.2 ⭐)"],
            index=0
        )

        df_base_unidades = df_completo[df_completo['Restaurante_Origen'].isin(sel_unidades)].copy()

        df_act = pd.DataFrame()
        if isinstance(rango_actual, tuple) and len(rango_actual) == 2:
            act_i, act_f = rango_actual
            df_act = df_base_unidades[(df_base_unidades['Fecha_Envio'] >= act_i) & (df_base_unidades['Fecha_Envio'] <= act_f)].copy()

        df_ant = pd.DataFrame()
        if isinstance(rango_anterior, tuple) and len(rango_anterior) == 2:
            ant_i, ant_f = rango_anterior
            df_ant = df_base_unidades[(df_base_unidades['Fecha_Envio'] >= ant_i) & (df_base_unidades['Fecha_Envio'] <= ant_f)].copy()

        df_act_visual = df_act.copy()
        if col_calif in df_act_visual.columns:
            if "🟢" in opcion_semaforo:
                df_act_visual = df_act_visual[df_act_visual[col_calif] >= META_CALIFICACION].copy()
            elif "🟡" in opcion_semaforo:
                df_act_visual = df_act_visual[(df_act_visual[col_calif] >= 4.3) & (df_act_visual[col_calif] < META_CALIFICACION)].copy()
            elif "🔴" in opcion_semaforo:
                df_act_visual = df_act_visual[df_act_visual[col_calif] <= 4.2].copy()

        # --- SECCIÓN 1: MÉTRICAS COMPARATIVAS INTELIGENTES ---
        st.subheader("📈 Comparativa de Rendimiento Operativo")
        
        if len(rango_actual) == 2 and len(rango_anterior) == 2:
            st.info(f"Análisis: Periodo Actual (**{rango_actual[0].strftime('%d/%m')} al {rango_actual[1].strftime('%d/%m')}**) vs Periodo Anterior (**{rango_anterior[0].strftime('%d/%m')} al {rango_anterior[1].strftime('%d/%m')}**)")

        m1, m2, m3, m4, m5 = st.columns(5)
        
        total_act = len(df_act)
        total_ant = len(df_ant)
        diff_total = total_act - total_ant
        m1.metric(label="Total Encuestas", value=f"{total_act} resp.", delta=f"{diff_total:+d} vs periodo ant.")
        
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

        # CÁLCULO UNIFICADO DEL NPS
        nps_act = calcular_nps_hibrido(df_act, col_nps_nueva, col_estrellas_vieja)
        nps_ant = calcular_nps_hibrido(df_ant, col_nps_nueva, col_estrellas_vieja)
        
        if nps_act is not None:
            diff_nps = (nps_act - nps_ant) if nps_ant is not None else None
            m3.metric(label="Índice NPS (Lealtad)", value=f"{nps_act:.1f}%", delta=f"{diff_nps:+.1f}% vs periodo ant." if diff_nps is not None else None)
        else:
            m3.metric("Índice NPS (Lealtad)", "Esperando Datos")

        if col_calif in df_act.columns:
            alertas_act = len(df_act[df_act[col_calif] <= 2].dropna(subset=[col_calif]))
            alertas_ant = len(df_ant[df_ant[col_calif] <= 2].dropna(subset=[col_calif])) if len(df_ant) > 0 else 0
            diff_alertas = alertas_act - alertas_ant
            m4.metric(label="Alertas Críticas (1-2 ⭐)", value=alertas_act, delta=f"{diff_alertas:+d} quejas", delta_color="inverse")
        else:
            m4.metric("Alertas Críticas", "0")

        meseros_act = df_act[col_mesero].dropna().nunique() if (col_mesero in df_act.columns and len(df_act) > 0) else 0
        meseros_ant = df_ant[col_mesero].dropna().nunique() if (col_mesero in df_ant.columns and len(df_ant) > 0) else 0
        diff_meseros = meseros_act - meseros_ant
        m5.metric(label="Meseros Evaluados", value=meseros_act, delta=f"{diff_meseros:+d} integrantes")

        if prom_act is not None and not pd.isna(prom_act):
            if prom_act >= META_CALIFICACION:
                st.success(f"🟢 **Estatus del Periodo Evaluado: Excelente.** Promedio de {prom_act:.2f} ⭐")
            elif prom_act >= 4.3:
                st.warning(f"🟡 **Estatus del Periodo Evaluado: En Observación.** Promedio de {prom_act:.2f} ⭐")
            else:
                st.error(f"🔴 **Estatus del Periodo Evaluado: Alerta Crítica.** Promedio de {prom_act:.2f} ⭐")

        st.markdown("---")
        st.subheader("🏆 Análisis Visual del Periodo Actual Seleccionado")
        
        if len(df_act) == 0:
            st.warning("📋 No existen encuestas registradas para el Periodo Actual.")
        else:
            g1, g2, g3 = st.columns(3)
            
            with g1:
                st.markdown("##### 🏢 Volumen de Encuestas por Unidad")
                df_unidades = df_act['Restaurante_Origen'].value_counts().reset_index()
                df_unidades.columns = ['Unidad', 'Encuestas']
                fig_uni = px.bar(df_unidades, x='Encuestas', y='Unidad', orientation='h', color='Encuestas', color_continuous_scale='Teal', text_auto=True)
                fig_uni.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_uni, use_container_width=True)
            
            with g2:
                st.markdown("##### 🔝 Top 10 Meseros con Mayor Volumen")
                if col_mesero in df_act.columns and not df_act[col_mesero].dropna().empty:
                    top_volumen = df_act[col_mesero].value_counts().nlargest(10).reset_index()
                    top_volumen.columns = ['Mesero', 'Cantidad']
                    fig_vol = px.bar(top_volumen, x='Cantidad', y='Mesero', orientation='h', color='Cantidad', color_continuous_scale='Blues', text_auto=True)
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
                        fig_cal = px.bar(top_calif, x='Promedio', y='Mesero', orientation='h', color='Promedio', color_continuous_scale='Reds', text_auto='.2f', range_x=[0,5])
                        fig_cal.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_cal, use_container_width=True)
                    else:
                        st.info("Sin promedios suficientes.")
                else:
                    st.info("Sin calificaciones disponibles.")

        if col_calif in df_act.columns and len(df_act) > 0:
            malos_comentarios = df_act[df_act[col_calif] <= 2].dropna(subset=[col_calif])
            if not malos_comentarios.empty:
                st.markdown("---")
                st.subheader("⚠️ Atención Inmediata: Comentarios Negativos")
                columnas_existentes = [c for c in ['Restaurante_Origen', col_mesero, col_calif, col_comentario] if c in df_act.columns]
                st.dataframe(malos_comentarios[columnas_existentes], use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Consolidado de Datos Auditados (Filtrado por Semáforo)")
        
        if len(df_act_visual) == 0:
            st.warning("No hay registros específicos para mostrar con los filtros seleccionados.")
        else:
            columnas_finales_validas = []
            columnas_deseadas = ['Restaurante_Origen', col_mesero, col_calif, col_comentario, 'Fecha_Envio']
            
            for c in columnas_deseadas:
                if c and c in df_act_visual.columns:
                    columnas_finales_validas.append(c)
                    
            if col_nps_nueva and col_nps_nueva in df_act_visual.columns:
                columnas_finales_validas.append(col_nps_nueva)
                    
            st.dataframe(df_act_visual[columnas_finales_validas], use_container_width=True)
