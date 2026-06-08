# --- SECCIÓN DE MÉTRICAS PRINCIPALES ---
        st.subheader("📈 Rendimiento e Indicadores Claves del Periodo")
        
        m1, m2, m3, m4, m5 = st.columns(5)
        
        # Métrica 1: Total de envíos
        m1.metric(label="Total Encuestas (Envíos)", value=f"{len(df_act)} envíos", delta=f"Histórico: {total_absoluto_historico}")
        
        # Métrica 2: Promedio
        prom_act = df_act[col_calif].mean() if col_calif in df_act.columns and not df_act.empty else 0
        m2.metric(label="Promedio Calificación", value=f"{prom_act:.2f} ⭐")
        
        # Métrica 3: NPS
        nps_val = calcular_nps_hibrido(df_act, col_nps_nueva, col_calif)
        nps_display = f"{nps_val:.1f}%" if nps_val is not None else "N/A"
        m3.metric(label="Índice NPS (Lealtad)", value=nps_display)
        
        # Métrica 4: Alertas
        alertas = len(df_act[df_act[col_calif] <= 2]) if col_calif in df_act.columns else 0
        m4.metric(label="Alertas Críticas (1-2 ⭐)", value=alertas)
        
        # Métrica 5: Meseros
        meseros = df_act[col_mesero].nunique() if col_mesero in df_act.columns else 0
        m5.metric(label="Meseros Evaluados", value=meseros)
