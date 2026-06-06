import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Il Mercato - Inteligencia Operativa", layout="wide", page_icon="📊")
st.title("📊 Dashboard Avanzado de Excelencia - Il Mercato")
st.markdown("---")

# Meta u Objetivo del Grupo para el Semáforo de Calificaciones
META_CALIFICACION = 4.6

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

# 2. DETECTAR TODOS LOS ARCHIVOS DE EXCEL
todos_los_archivos = [f for f in os.listdir('.') if f.lower().endswith('.xlsx') and not f.startswith('~$')]

if len(todos_los_archivos) == 0:
    st.error("⚠️ No se encontraron archivos de Excel (.xlsx) en el repositorio. Por favor sube al menos un archivo Excel a GitHub.")
else:
    # --- BARRA LATERAL: CONTROL DE COMPARATIVAS Y FILTROS ---
    st.sidebar.header("🔄 Control de Semanas / Reportes")
    
    archivo_actual = st.sidebar.selectbox(
        "📅 Selecciona el Reporte Actual (Semana Nueva):", 
        todos_los_archivos, 
        index=0
    )
    
    opciones_anterior = ["Ninguno (Ver solo reporte actual)"] + todos_los_archivos
    def_idx = 1 if len(todos_los_archivos) > 1 else 0
    archivo_anterior = st.sidebar.selectbox(
        "⏳ Selecciona el Reporte Anterior (Para comparar):", 
        opciones_anterior, 
        index=def_idx
    )

    # Cargar Datos Base
    df_actual_completo = procesar_excel(archivo_actual)
    
    if df_actual_completo is not None:
        col_mesero = 'Selecciona a la persona que te atendió / Select the person who assisted you'
        col_calif = 'Califica la atención recibida / How would you rate your experience?'
        col_comentario = 'Cuéntanos cómo fue tu experiencia / Tell us about your visit'

        if col_calif in df_actual_completo.columns:
            df_actual_completo[col_calif] = pd.to_numeric(df_actual_completo[col_calif], errors='coerce')

        # Filtro 1: Sucursal/Unidad
        unidades = sorted(df_actual_completo['Restaurante_Origen'].unique())
        sel_unidades = st.sidebar.multiselect("🏢 Filtrar por Unidades:", unidades, default=unidades)
        
        df_act = df_actual_completo[df_actual_completo['Restaurante_Origen'].isin(sel_unidades)].copy()

        # --- BUSCADOR INDIVIDUAL DE MESEROS ---
        st.sidebar.markdown("---")
        st.sidebar.header("🔍 Auditoría de Colaborador")
        
        lista_meseros = ["TODOS LOS MESEROS"]
        if col_mesero in df_act.columns:
            meseros_unicos = sorted(df_act[col_mesero].dropna().unique())
            lista_meseros.extend(meseros_unicos)
            
        sel_mesero = st.sidebar.selectbox("👤 Selecciona un Mesero Específico:", lista_meseros, index=0)

        # Si se selecciona un mesero, filtramos toda la información por él
        if sel_mesero != "TODOS LOS MESEROS":
            df_act = df_act[df_act[col_mesero] == sel_mesero].copy()

        # Cargar semana anterior si aplica
        df_ant = None
        if archivo_anterior != "Ninguno (Ver solo reporte actual)":
            df_anterior_completo = procesar_excel(archivo_anterior)
            if df_anterior_completo is not None:
                if col_calif in df_anterior_completo.columns:
                    df_anterior_completo[col_calif] = pd.to_numeric(df_anterior_completo[col_calif], errors='coerce')
                df_ant = df_anterior_completo[df_anterior_completo['Restaurante_Origen'].isin(sel_unidades)].copy()
                if sel_mesero != "TODOS LOS MESEROS":
                    df_ant = df_ant[df_ant[col_mesero] == sel_mesero].copy()

        # --- SECCIÓN TÍTULO DINÁMICO ---
        if sel_mesero == "TODOS LOS MESEROS":
            st.subheader("📈 Rendimiento e Indicadores Claves (Visión General)")
        else:
            st.markdown(f"### 👤 Expediente de Servicio: **{sel_mesero}**")
            st.info(f"Mostrando únicamente las encuestas y métricas donde participó este colaborador.")

        # --- SECCIÓN 1: MÉTRICAS GENERALES CON SEMÁFORO DE OBJETIVOS ---
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
            
            if not pd.isna(prom_act):
                m2.metric(
                    label="Promedio Calificación", 
                    value=f"{prom_act:.2f} ⭐", 
                    delta=f"{diff_prom:+.2f} ⭐" if diff_prom is not None else None
                )
                if prom_act >= META_CALIFICACION:
                    st.success(f"🟢 **Semáforo: Excelente.** Supera el objetivo de {META_CALIFICACION} ⭐")
                elif prom_act >= 4.3:
                    st.warning(f"🟡 **Semáforo: En Observación.** Cerca de la meta ({prom_act:.2f}/{META_CALIFICACION})")
                else:
                    st.error(f"🔴 **Semáforo: Alerta Crítica.** Por debajo del estándar operativo.")
            else:
                m2.metric("Promedio Calificación", "N/A")
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

        # Métrica 4: Participación
        if sel_mesero == "TODOS LOS MESEROS":
            meseros_act = df_act[col_mesero].dropna().nunique() if col_mesero in df_act.columns else 0
            diff_meseros = None
            if df_ant is not None and col_mesero in df_ant.columns:
                diff_meseros = meseros_act - df_ant[col_mesero].dropna().nunique()
            m4.metric(
                label="Meseros Evaluados", 
                value=meseros_act, 
                delta=f"{diff_meseros:+d} integrantes" if diff_meseros is not None else None
            )
        else:
            total_sucursales = len(df_actual_completo[df_actual_completo['Restaurante_Origen'].isin(sel_unidades)])
            porcentaje_participacion = (total_act / total_sucursales * 100) if total_sucursales > 0 else 0
            m4.metric(
                label="Cuota de Captura", 
                value=f"{porcentaje_participacion:.1f}%"
            )

        st.markdown("---")

        # --- SECCIÓN 2: GRÁFICOS DINÁMICOS CORREGIDOS ---
        st.subheader("🏆 Análisis Visual del Periodo")
        
        if sel_mesero == "TODOS LOS MESEROS":
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
            # VISTA INDIVIDUAL CORREGIDA (RANGOS BLINDADOS)
            g1, g2 = st.columns(2)
            with g1:
                st.markdown(f"##### 📊 Histograma de Calificaciones para {sel_mesero}")
                if col_calif in df_act.columns and len(df_act) > 0:
                    df_dist = df_act[col_calif].value_counts().reset_index()
                    df_dist.columns = ['Estrellas', 'Conteo']
                    fig_dist = px.bar(df_dist, x='Estrellas', y='Conteo', text_auto=True,
                                      color='Estrellas', color_continuous_scale='Gold', range_x=[0.5, 5.5])
                    st.plotly_chart(fig_dist, use_container_width=True)
            with g2:
                st.markdown("##### 🏢 Desempeño por Sucursal asignada")
                df_suc = df_act.groupby('Restaurante_Origen')[col_calif].agg(['count', 'mean']).reset_index()
                df_suc.columns = ['Restaurante', 'Encuestas', 'Promedio']
                fig_suc = px.bar(df_suc, x='Restaurante', y='Promedio', text=df_suc['Encuestas'].apply(lambda x: f"{x} encuestas"),
                                 color='Promedio', color_continuous_scale='Teal', range_y=[0,5])
                st.plotly_chart(fig_suc, use_container_width=True)

        # --- SECCIÓN 3: TABLA DE COMENTARIOS NEGATIVOS ---
        if col_calif in df_act.columns:
            malos_comentarios = df_act
