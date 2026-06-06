import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard Comparativo de Excelencia - Il Mercato")
st.markdown("---")

# 1. FUNCIÓN INTELIGENTE PARA CARGAR CUALQUIER EXCEL
def procesar_excel(archivo_path):
    try:
        xls = pd.ExcelFile(archivo_path)
    except:
        return None
        
    hojas = [h for h in xls.sheet_names if h.upper() != 'TOTAL']
    if not hojas: 
        hojas = xls.sheet_names
        
    lista_dfs = []
    for hoja in hojas:
        try:
            df_hoja = pd.read_excel(archivo_path, sheet_name=hoja)
            if len(df_hoja.columns) >= 2:
                df_hoja.columns = [str(c).strip() for c in df_hoja.columns]
                df_hoja['Restaurante_Origen'] = str(hoja).strip().upper()
                if 'Submitted at' in df_hoja.columns:
                    df_hoja['Submitted at'] = df_hoja['Submitted at'].astype(str)
                lista_dfs.append(df_hoja)
        except:
            continue
            
    if not lista_dfs: 
        return None
        
    return pd.concat(lista_dfs, ignore_index=True, sort=False)

# 2. DETECTAR TODOS LOS ARCHIVOS DE EXCEL (SÚPER FLEXIBLE)
todos_los_archivos = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]

if len(todos_los_archivos) == 0:
    st.error("⚠️ No se encontraron archivos de Excel (.xlsx) en el repositorio. Por favor sube al menos un archivo Excel a GitHub.")
else:
    # --- BARRA LATERAL: CONTROL DE COMPARATIVAS ---
    st.sidebar.header("🔄 Control de Semanas / Reportes")
    
    # Selector de archivo base (Semana Actual)
    archivo_actual = st.sidebar.selectbox(
        "📅 Selecciona el Reporte Actual (Semana Nueva):", 
        todos_los_archivos, 
        index=0
    )
    
    # Selector de archivo comparativo (Semana Anterior)
    opciones_anterior = ["Ninguno (Ver solo reporte actual)"] + todos_los_archivos
    
    # Intentar poner por defecto el segundo archivo si existe
    def_idx = 1 if len(todos_los_archivos) > 1 else 0
    archivo_anterior = st.sidebar.selectbox(
        "⏳ Selecciona el Reporte Anterior (Para comparar):", 
        opciones_anterior, 
        index=def_idx
    )

    # Cargar Datos
    df_actual_completo = procesar_excel(archivo_actual)
    
    if df_actual_completo is not None:
        # Nombres de las columnas de tu encuesta
        col_mesero = 'Selecciona a la persona que te atendió / Select the person who assisted you'
        col_calif = 'Califica la atención recibida / How would you rate your experience?'
        col_comentario = 'Cuéntanos cómo fue tu experiencia / Tell us about your visit'

        # Limpieza rápida de datos numéricos
        if col_calif in df_actual_completo.columns:
            df_actual_completo[col_calif] = pd.to_numeric(df_actual_completo[col_calif], errors='coerce')

        # Filtro por Sucursal/Unidad para la Semana Actual
        unidades = sorted(df_actual_completo['Restaurante_Origen'].unique())
        sel_unidades = st.sidebar.multiselect("🏢 Filtrar por Unidades:", unidades, default=unidades)
        
        df_act = df_actual_completo[df_actual_completo['Restaurante_Origen'].isin(sel_unidades)].copy()

        # Cargar semana anterior si fue seleccionada
        df_ant = None
        if archivo_anterior != "Ninguno (Ver solo reporte actual)":
            df_anterior_completo = procesar_excel(archivo_anterior)
            if df_anterior_completo is not None:
                if col_calif in df_anterior_completo.columns:
                    df_anterior_completo[col_calif] = pd.to_numeric(df_anterior_completo[col_calif], errors='coerce')
                df_ant = df_anterior_completo[df_anterior_completo['Restaurante_Origen'].isin(sel_unidades)].copy()

        # --- SECCIÓN 1: MÉTRICAS GENERALES CON COMPARATIVA ---
        st.subheader("📈 Rendimiento e Indicadores Clave")
        m1, m2, m3, m4 = st.columns(4)
        
        # Métrica 1: Volumen de Respuestas
        total_act = len(df_act)
        diff_total = None
        if df_ant is not None:
            diff_total = total_act - len(df_ant)
        m1.metric(
            label="Total Encuestas", 
            value=f"{total_act} respuestas", 
            delta=f"{diff_total:+d} vs anterior" if diff_total is not None else None
        )
        
        # Métrica 2: Promedio de Estrellas
        if col_calif in df_act.columns:
            prom_act = df_act[col_calif].mean()
            diff_prom = None
            if df_ant is not None and col_calif in df_ant.columns:
                prom_ant = df_ant[col_calif].mean()
                if not pd.isna(prom_act) and not pd.isna(prom_ant):
                    diff_prom = prom_act - prom_ant
            
            m2.metric(
                label="Promedio Calificación", 
                value=f"{prom_act:.2f} ⭐" if not pd.isna(prom_act) else "N/A", 
                delta=f"{diff_prom:+.2f} ⭐" if diff_prom is not None else None
            )
        else:
            m2.metric("Promedio Calificación", "Falta columna")

        # Métrica 3: Alertas / Comentarios Malos
        if col_calif in df_act.columns:
            alertas_act = len(df_act[df_act[col_calif] <= 2].dropna(subset=[col_calif]))
            diff_alertas = None
            if df_ant is not None and col_calif in df_ant.columns:
                alertas_ant = len(df_ant[df_ant[col_calif] <= 2].dropna(subset=[col_calif]))
                diff_alertas = alertas_act - alertas_ant
            
            m3.metric(
                label="Alertas Críticas (1-2 ⭐)", 
                value=alertas_act, 
                delta=f"{diff_alertas:+d} quejas" if diff_alertas is not None else None,
                delta_color="inverse" if diff_alertas is not None else "normal"
            )
        else:
            m3.metric("Alertas Críticas", "0")

        # Métrica 4: Equipo Activo
        meseros_act = df_act[col_mesero].dropna().nunique() if col_mesero in df_act.columns else 0
        diff_meseros = None
        if df_ant is not None and col_mesero in df_ant.columns:
            diff_meseros = meseros_act - df_ant[col_mesero].dropna().nunique()
        m4.metric(
            label="Meseros Evaluados", 
            value=meseros_act, 
            delta=f"{diff_meseros:+d} integrantes" if diff_meseros is not None else None
        )

        st.markdown("---")

        # --- SECCIÓN 2: GRÁFICOS DE LA SEMANA ACTUAL ---
        st.subheader("🏆 Desempeño del Periodo Actual")
        t1, t2 = st.columns(2)

        with t1:
            st.markdown("##### 🔝 Top 10 Meseros con Mayor Volumen de Encuestas")
            if col_mesero in df_act.columns and not df_act[col_mesero].dropna().empty:
                top_volumen = df_act[col_mesero].value_counts().nlargest(10).reset_index()
                top_volumen.columns = ['Mesero', 'Cantidad']
                fig_vol = px.bar(top_volumen, x='Cantidad', y='Mesero', orientation='h', 
                                 color='Cantidad', color_continuous_scale='Blues', text_auto=True)
                fig_vol.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.info("Sin datos de meseros en este periodo.")

        with t2:
            st.markdown("##### ⭐ Top 10 Meseros con Mejor Calificación Promedio")
            if col_mesero in df_act.columns and col_calif in df_act.columns and not df_act[col_mesero].dropna().empty:
                conteo_votos = df_act[col_mesero].value_counts()
                meseros_activos = conteo_votos[conteo_votos >= 2].index
                df_meseros_activos = df_act[df_act[col_mesero].isin(meseros_activos)]
                
                if not df_meseros_activos.empty:
                    top_calif = df_meseros_activos.groupby(col_mesero)[col_calif].mean().nlargest(10).reset_index()
                    top_calif.columns = ['Mesero', 'Promedio']
                    fig_cal = px.bar(top_calif, x='Promedio', y='Mesero', orientation='h',
                                     color='Promedio', color_continuous_scale='Reds', text_auto='.2f', range_x=[0,5])
                    fig_cal.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_cal, use_container_width=True)
                else:
                    st.info("Se necesitan reportes con más respuestas por mesero para calcular este Top.")
            else:
                st.info("Faltan columnas de calificación en el archivo.")

        # --- SECCIÓN 3: TABLA DE COMENTARIOS NEGATIVOS (ALERTAS ACTUALES) ---
        if col_calif in df_act.columns:
            malos_comentarios = df_act[df_act[col_calif] <= 2].dropna(subset=[col_calif])
            if not malos_comentarios.empty:
                st.markdown("---")
                st.subheader("⚠️ Atención Inmediata: Comentarios Negativos (Periodo Actual)")
                columnas_existentes = [c for c in ['Restaurante_Origen', col_mesero, col_calif, col_comentario] if c in df_act.columns]
                st.dataframe(malos_comentarios[columnas_existentes], use_container_width=True)

        # --- SECCIÓN 4: REVISIÓN GLOBAL DE DATOS ---
        st.markdown("---")
        st.subheader("📋 Consolidado de Datos del Periodo Seleccionado")
        st.dataframe(df_act, use_container_width=True)
    else:
        st.error("Error al procesar el archivo seleccionado. Asegúrate de que tenga las hojas correctas.")
