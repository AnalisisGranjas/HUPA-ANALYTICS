import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Verificación de seguridad (Por si alguien intenta entrar directo al link sin loguearse)
if 'auth' not in st.session_state or not st.session_state.auth:
    st.warning("⚠️ Por favor, inicie sesión en la página principal.")
    st.stop()

st.title("🐔 Estado General de Granjas")
st.markdown("---")

# RUTA DEL EXCEL (Usando tu estructura de carpetas)
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")

@st.cache_data
def cargar_datos():
    if os.path.exists(PATH_DATA):
        df = pd.read_excel(PATH_DATA)
        return df
    return None

df = cargar_datos()

if df is not None:
    # FILTROS RÁPIDOS
    col1, col2 = st.columns(2)
    with col1:
        empresa = st.selectbox("Empresa:", df["RAZON_SOCIAL"].unique())
    with col2:
        df_filt = df[df["RAZON_SOCIAL"] == empresa]
        granja = st.selectbox("Granja:", df_filt["GRANJA"].unique())

    # DATOS FINALES
    final_df = df_filt[df_filt["GRANJA"] == granja]

    # MÉTRICAS
    st.subheader(f"Resumen: {granja}")
    m1, m2, m3 = st.columns(3)
    poblacion_act = final_df.groupby("LOTE")["Saldo de Aves"].last().sum()
    m1.metric("Población Actual", f"{poblacion_act:,.0f}")
    m2.metric("Lotes Activos", final_df["LOTE"].nunique())
    m3.metric("Edad Máx", f"{final_df['Edad'].max()} Sem")

    # GRÁFICA SENCILLA
    fig = px.area(final_df, x="Final Sem", y="Saldo de Aves", color="LOTE", title="Curva de Población")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("❌ No se encontró el archivo de datos en DATA/")