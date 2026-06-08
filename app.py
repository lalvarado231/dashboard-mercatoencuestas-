# --- SECCIÓN DE MÉTRICAS PRINCIPALES ---
st.subheader("📈 Rendimiento e Indicadores Claves del Periodo")

# Creamos las 5 columnas para las métricas
m1, m2, m3, m4, m5 = st.columns(5)

# Definimos los valores de forma segura antes de mostrarlos
total_envios = len(df_act)
prom_calif = df_act[col_calif].mean() if col_calif in df_act.columns and not df_act.empty else 0
nps_valor = calcular_nps_hibrido(df_act, col_nps_nueva, col_calif)
num_alertas = len(df_act[df_act[col_calif] <= 2]) if col_calif in df_act.columns else 0
num_meseros = df_act[col_mesero].nunique() if col_mesero in df_act.columns else 0

# Mostramos las métricas
m1.metric("Total Encuestas", f"{total_envios} resp.")
m2.metric("Promedio", f"{prom_calif:.2f} ⭐")
m3.metric("NPS", f"{nps_valor:.1f}%" if nps_valor is not None else "N/A")
m4.metric("Alertas (1-2⭐)", num_alertas)
m5.metric("Colaboradores", num_meseros)
