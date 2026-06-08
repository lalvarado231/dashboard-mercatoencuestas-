import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard Automatizado con Filtro de Fechas - Il Mercato")
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
        
        # Convertir la columna de fecha de Tally a un formato de fecha real de Python
        if 'Submitted at' in df.columns:
            df['Fecha_Envio'] = pd.to_datetime(df['Submitted at'], errors='coerce').dt.date
            
        return df.copy()
        
    return None

# 2. DETECTAR TODOS LOS ARCHIVOS CSV DE TALLY EN EL REPOSITORIO
todos_los_archivos = [f for f in os.listdir('.') if f.lower().endswith('.csv')]

if len(todos_los_archivos) == 0:
    st.error("⚠️ No se encontraron archivos de Tally (.csv) en el repositorio. Por favor sube el archivo descargado de Tally directamente a GitHub.")
else:
    # --- BARRA LATERAL: CONTROL DE ARCHIVOS Y FILTROS ---
    st.sidebar.header("📂 Origen de Datos")
    todos_los_archivos.sort(reverse=True)
    
    archivo_actual = st.sidebar.selectbox(
        "📄 Selecciona la Base de Datos (CSV):", 
        todos_los_archivos, 
        index=0
    )

    # Cargar Datos Base
    df_raw = procesar_tally_csv(archivo_actual)
    
    if df_raw is not None:
        df_completo = df_raw.copy()
        
        col_mesero = 'Selecciona a la persona que te atendió / Select the person who assisted you'
        col_calif = 'Califica la atención recibida / How would you rate your experience?'
        col_comentario = 'Cuéntanos cómo fue una experiencia / Tell us about your visit'
        if col_comentario not in df_completo.columns:
            # Por si varía un caracter en la pregunta
            col_comentario = 'Cuéntanos cómo fue tu experiencia / Tell us about your visit'

        if col_calif in df_completo.columns:
            df_completo[col_calif] = pd.to_numeric(df_completo[col_calif], errors='coerce')

        # --- SECCIÓN DE CALENDARIO (RANGO DE FECHAS) ---
        st.sidebar.markdown("---")
        st.sidebar.header("📅 Rango de Evaluación (Semana)")
        
        # Obtener las fechas disponibles en el archivo para guiar al usuario
        fechas_validas = df_completo['Fecha_Envio'].dropna()
        if not fechas_validas.empty:
            min_fecha = min(fechas_validas)
            max_fecha = max(fechas_validas)
            # Por defecto, sugerir los últimos 7 días registrados en la base
            def_inicio = max_fecha - timedelta(days=6)
            def_fin = max_fecha
        else:
            min_fecha = datetime.today().date() - timedelta(days=30)
            max_fecha = datetime.today().date()
            def_inicio = min_fecha
            def_fin = max_fecha

        # Calendario doble (Permite seleccionar Fecha Inicio y Fecha Fin)
        rango_fechas = st.sidebar.date_input(
            "Selecciona los días a evaluar:",
            value=(def_inicio, def_fin),
            min_value=min_fecha,
            max_value=max_fecha
        )

        # Filtro 1: Unidades / Sucursales
        st.sidebar.markdown("---")
        st.sidebar.header("🏢 Filtro de Unidades")
        unidades = sorted([u for u in df_completo['Restaurante_Origen'].unique() if u != 'NAN'])
        sel_unidades = st.sidebar.multiselect("Selecciona Unidades:", unidades, default=unidades)

        # Filtro 2: Semáforo
        st.sidebar.markdown("---")
        st.sidebar.header("🚦 Filtro por Semáforo")
        opcion_semaforo = st.sidebar.radio(
            "Estatus a auditar:",
            [
                "🔵 Mostrar Todo",
                "🟢 Cumplen Meta (>= 4.6 ⭐)",
                "🟡 En Observación (4.3 - 4.5 ⭐)",
                "🔴 Alerta Crítica (<= 4.2 ⭐)"
            ],
            index=0
        )

        # --- APLICAR TODOS LOS FILTROS EN CASCADA ---
        # 1. Filtro por Unidad
        df_filtrado = df_completo[df_completo['Restaurante_Origen'].isin(sel_unidades)].copy()
        
        # 2. Filtro por Rango de Fechas del Calendario
        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            fecha_i, fecha_f = rango_fechas
            df_filtrado = df_filtrado[(df_filtrado['Fecha_Envio'] >= fecha_i) & (df_filtrado['Fecha_Envio'] <= fecha_f)].copy()
            st.sidebar.success(f"📅 Evaluando del {fecha_i.strftime('%d/%m')} al {fecha_f.strftime('%d/%m')}")

        # 3. Filtro por Semáforo de Calificaciones
        if col_calif in df_filtrado.columns:
            if "🟢" in opcion_semaforo:
                df_filtrado = df_filtrado[df_filtrado[col_calif] >= META_CALIFICACION].copy()
            elif "🟡" in opcion_semaforo:
                df_filtrado = df_filtrado[(df_filtrado[col_calif] >= 4.3) & (df_filtrado[col_calif] < META_CALIFICACION)].copy()
            elif "🔴" in opcion_semaforo:
                df_filtrado = df_filtrado[df_filtrado[col_calif] <= 4.2].copy()

        # --- SECCIÓN DE TÍTULOS E INDICADORES ---
        st.subheader("📈 Rendimiento e Indicadores Claves del Periodo")
        if "🔵" not in opcion_semaforo:
            st.info(f"Filtro Activo: Mostrando únicamente registros en **{opcion_semaforo[2:]}**")

        m1, m2, m3, m4 = st.columns(4)
        
        # Métrica 1: Volumen en las fechas elegidas
        total_act = len(df_filtrado)
        m1.metric(label="Total Encuestas en Rango", value=f"{total_act} respuestas")
        
        # Métrica 2: Promedio de Estrellas en las fechas elegidas
        if col_calif in df_filtrado.columns:
            prom_act = df_filtrado[col_calif].mean()
            if not pd.isna(prom_act):
                m2.metric(label="Promedio Calificación", value=f"{prom_act:.2f} ⭐")
                if prom_act >= META_CALIFICACION:
                    st.success(f"🟢 **Semáforo del Periodo: Excelente.** ({prom_act:.2f} ⭐)")
                elif prom_act >= 4.3:
                    st.warning(f"🟡 **Semáforo del Periodo: En Observación.** ({prom_act:.2f} ⭐)")
                else:
                    st.error(f"🔴 **Semáforo del Periodo: Alerta Crítica.** ({prom_act:.2f} ⭐)")
            else:
                m2.metric("Promedio Calificación", "N/A")
        else:
            m2.metric("Promedio Calificación", "Falta columna")

        # Métrica 3: Quejas Graves (1-2 ⭐)
        if col_calif in df_filtrado.columns:
            alertas_act = len(df_filtrado[df_filtrado[col_calif] <= 2].dropna(subset=[col_calif]))
            m3.metric(label="Alertas Críticas (1-2 ⭐)", value=alertas_act)
        else:
            m3.metric("Alertas Críticas", "0")

        # Métrica 4: Total de Personal Evaluado en esas fechas
        meseros_act = df_filtrado[col_mesero].dropna().nunique() if (col_mesero in df_filtrado.columns and len(df_filtrado) > 0) else 0
        m4.metric(label="Meseros Evaluados", value=meseros_act)

        st.markdown("---")

        # --- SECCIÓN 2: GRÁFICOS DINÁMICOS ---
        st.subheader("🏆 Análisis Visual del Periodo Seleccionado")
        
        if len(df_filtrado) == 0:
            st.warning("📋 No existen encuestas registradas para el rango de fechas o filtros seleccionados.")
        else:
            g1, g2, g3 = st.columns(3)
            
            with g1:
                st.markdown("##### 🏢 Volumen de Encuestas por Unidad")
                df_unidades = df_filtrado['Restaurante_Origen'].value_counts().reset_index()
                df_unidades.columns = ['Unidad', 'Encuestas']
                fig_uni = px.bar(df_unidades, x='Encuestas', y='Unidad', orientation='h',
                                 color='Encuestas', color_continuous_scale='Teal', text_auto=True)
                fig_uni.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_uni, use_container_width=True)
            
            with g2:
                st.markdown("##### 🔝 Top 10 Meseros con Mayor Volumen")
                if col_mesero in df_filtrado.columns and not df_filtrado[col_mesero].dropna().empty:
                    top_volumen = df_filtrado[col_mesero].value_counts().nlargest(10).reset_index()
                    top_volumen.columns = ['Mesero', 'Cantidad']
                    fig_vol = px.bar(top_volumen, x='Cantidad', y='Mesero', orientation='h', 
                                     color='Cantidad', color_continuous_scale='Blues', text_auto=True)
                    fig_vol.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_vol, use_container_width=True)
                else:
                    st.info("Sin datos de colaboradores en este rango.")
                    
            with g3:
                st.markdown("##### ⭐ Top 10 Meseros con Mejor Calificación")
                if col_mesero in df_filtrado.columns and col_calif in df_filtrado.columns and not df_filtrado[col_mesero].dropna().empty:
                    conteo_votos = df_filtrado[col_mesero].value_counts()
                    meseros_activos = conteo_votos.index
                    df_meseros_activos = df_filtrado[df_filtrado[col_mesero].isin(meseros_activos)]
                    
                    if not df_meseros_activos.empty:
                        top_calif = df_meseros_activos.groupby(col_mesero)[col_calif].mean().nlargest(10).reset_index()
                        top_calif.columns = ['Mesero', 'Promedio']
                        fig_cal = px.bar(top_calif, x='Promedio', y='Mesero', orientation='h',
                                         color='Promedio', color_continuous_scale='Reds', text_auto='.2f', range_x=[0,5])
                        fig_cal.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_cal, use_container_width=True)
                    else:
                        st.info("Sin promedios en este rango.")
                else:
                    st.info("Sin calificaciones disponibles.")

        # --- SECCIÓN 3: TABLA DE COMENTARIOS NEGATIVOS EN EL RANGO ---
        if col_calif in df_filtrado.columns and len(df_filtrado) > 0:
            malos_comentarios = df_filtrado[df_filtrado[col_calif] <= 2].dropna(subset=[col_calif])
            if not malos_comentarios.empty:
                st.markdown("---")
                st.subheader("⚠️ Atención Inmediata: Comentarios Negativos en el Rango de Fechas")
                columnas_existentes = [c for c in ['Restaurante_Origen', col_mesero, col_calif, col_comentario] if c in df_filtrado.columns]
                st.dataframe(malos_comentarios[columnas_existentes], use_container_width=True)

        # --- SECCIÓN 4: REVISIÓN GLOBAL DE DATOS ---
        st.markdown("---")
        st.subheader("📋 Consolidado de Datos Auditados (Filtrado)")
        columnas_finales = [c for c in ['Restaurante_Origen', col_mesero, col_calif, col_comentario, 'Submitted at'] if c in df_filtrado.columns]
        st.dataframe(df_filtrado[columnas_finales], use_container_width=True)
    else:
        st.error("El archivo CSV cargado no coincide con el formato esperado de Tally. Verifica las columnas.")
