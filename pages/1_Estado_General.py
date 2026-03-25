import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. SEGURIDAD Y SESIÓN ---
if 'auth' not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

# --- 2. CONFIGURACIÓN Y CSS ---
st.set_page_config(page_title="HUPA | Dashboard Operativo", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align:center; color:#ffffff; background-color: #1a237e; padding: 20px; border-radius: 15px; margin-bottom: 20px; font-weight: bold; font-size: 2.5rem; }
    .info-box { background-color: #f8f9fa; border-left: 6px solid #1a237e; padding: 20px; margin-bottom: 25px; border-radius: 0 10px 10px 0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .info-box h4 { color: #1a237e; margin-top: 0; }
    .info-box p { text-align: justify; font-size: 0.95rem; line-height: 1.5; color: #333; }
    .card-design { padding: 25px; border-radius: 20px; color: white; text-align: center; margin-bottom: 20px; transition: all 0.4s ease-in-out; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .card-design:hover { transform: translateY(-12px) scale(1.02); filter: brightness(1.2); cursor: pointer; }
    .card-total { background: linear-gradient(135deg, #0052D4, #4364F7, #6FB1FC); } 
    .card-lotes { background: linear-gradient(135deg, #FF8C00, #FFA500, #FFD700); } 
    .card-edad { background: linear-gradient(135deg, #1D976C, #93F9B9); } 
    .card-prod { background: linear-gradient(135deg, #8E2DE2, #4A00E0); } 
    .val-num { font-size: 2.3rem; font-weight: 800; display: block; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    .label-card { font-size: 1rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .hr-custom { border: 0; height: 2px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(128,128,128,0.5), rgba(0,0,0,0)); margin: 40px 0; }
    .user-log { font-size: 1rem; color: #1a237e; font-weight: bold; margin-bottom: 10px; }
    div[data-testid="stSidebar"] button { background-color: #ff4b4b !important; color: white !important; border-radius: 10px; width: 100%; }
    .footer-tematico { margin-top: 20px; padding: 30px 0; text-align: center; opacity: 0.6; }
    .footer-pattern { font-size: 1.8rem; letter-spacing: 12px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    usuario_actual = st.session_state.get('user', 'VET_HUPA')
    st.markdown(f"<div class='user-log'>👤 Sesión: {usuario_actual}</div>", unsafe_allow_html=True)
    if st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.switch_page("app.py")
    st.divider()

# --- 4. CARGA DE DATOS ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")

@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        df_raw = pd.read_excel(PATH_DATA)
        df_raw.columns = [str(col).replace('\n', ' ').strip() for col in df_raw.columns]
        return df_raw
    return None

df_orig = load_data()

if df_orig is not None:
    # --- A. TÍTULO Y CAJA TÉCNICA ---
    st.markdown('<div class="main-title">🥚 ESTADO GENERAL DE OPERACIÓN 🥚</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-box"><h4>🔍 Interpretación Técnica</h4><p>Análisis de desempeño basado en <b>Edad Máxima</b>. Los valores en verde indican superación de meta técnica y en rojo desviaciones negativas.</p></div>', unsafe_allow_html=True)

    # --- B. FILTRO DE EMPRESA ---
    empresa = st.selectbox("🏢 Seleccione Empresa para filtrar datos:", sorted(df_orig['RAZON_SOCIAL'].unique()))
    df_empresa = df_orig[df_orig['RAZON_SOCIAL'] == empresa].copy()

    # Lógica "Foto Actual" (Lote == Galpón y última edad)
    df_activos = df_empresa[df_empresa['LOTE'] == df_empresa['NUM_GALPON']].copy()
    df_ultimos = df_activos.sort_values('Edad Sem.', ascending=False).drop_duplicates(['GRANJA', 'LOTE'])

    # --- C. CÁLCULO DE DIFERENCIAS ---
    df_ultimos['Dif Pdn'] = pd.to_numeric(df_ultimos['% Pdn. Real'], errors='coerce') - pd.to_numeric(df_ultimos['% Pdn. Tabla'], errors='coerce')
    df_ultimos['Dif GAD'] = pd.to_numeric(df_ultimos['Gr.A.D Real'], errors='coerce') - pd.to_numeric(df_ultimos['Gr.A.D Tabla'], errors='coerce')
    df_ultimos['Dif HAA'] = pd.to_numeric(df_ultimos['H.A.A. Real'], errors='coerce') - pd.to_numeric(df_ultimos['H.A.A. Tabla'], errors='coerce')
    df_ultimos['Dif Peso'] = pd.to_numeric(df_ultimos['Peso Real'], errors='coerce') - pd.to_numeric(df_ultimos['Peso Tab'], errors='coerce')
    df_ultimos['Dif Mort'] = pd.to_numeric(df_ultimos['%Mort+Sel Acum. Tab'], errors='coerce') - pd.to_numeric(df_ultimos['% Mort + Sel Acum.'], errors='coerce')

    # --- D. TARJETAS ---
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown(f'<div class="card-design card-total"><span class="label-card">Población Total</span><span class="val-num">🐔 {df_ultimos["Saldo de Aves"].sum():,.0f}</span></div>', unsafe_allow_html=True)
    col2.markdown(f'<div class="card-design card-lotes"><span class="label-card">Lotes Activos</span><span class="val-num">📦 {len(df_ultimos)}</span></div>', unsafe_allow_html=True)
    col3.markdown(f'<div class="card-design card-edad"><span class="label-card">Edad Promedio</span><span class="val-num">⏳ {df_ultimos["Edad Sem."].mean():.1f}</span></div>', unsafe_allow_html=True)
    col4.markdown(f'<div class="card-design card-prod"><span class="label-card">Postura Prom.</span><span class="val-num">🥚 {df_ultimos["% Pdn. Real"].mean():.1f}%</span></div>', unsafe_allow_html=True)

    # --- E. GRÁFICO ---
    st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
    st.markdown("### 🗺️ Distribución por Granja")
    fig_granja = px.pie(df_ultimos, values='Saldo de Aves', names='GRANJA', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_granja.update_layout(margin=dict(t=30, b=30, l=30, r=30), height=450)
    st.plotly_chart(fig_granja, use_container_width=True, config={'displayModeBar': False})
    st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

    # --- F. TABLA: 24 ORIGINALES + 4 DIFERENCIAS ---
    st.markdown("### 📋 Resumen Detallado de Producción")
    
    cols_base = [
        'GRANJA', 'LINEA_AVES', 'LOTE', 'Final Sem', 'Edad Sem.', 
        'Saldo de Aves', 'Mort', 'Suma Mort + Sel', 
        '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort', 'Fase de Alimento', 
        'Bulto X 40 K', 'Costo Alimento Sem', '$ Huevo por alimento',
        'Gr.A.D Real', 'Gr.A.D Tabla', 'Dif GAD', '% Unif', 
        'Peso Real', 'Peso Tab', 'Dif Peso', 'Huevos  Semana',
        '% Pdn. Real', '% Pdn. Tabla', 'Dif Pdn',
         'H.A.A. Real', 'H.A.A. Tabla', 'Dif HAA',  
    ]

    # Seguridad: Lista Negra VET_HUPA
    if usuario_actual == "VET_HUPA":
        lista_negra = ['Costo Alimento Sem', '$ Huevo por alimento']
        cols_finales = [c for c in cols_base if c not in lista_negra]
    else:
        cols_finales = cols_base

    cols_disponibles = [c for c in cols_finales if c in df_ultimos.columns]
    tabla_final = df_ultimos[cols_disponibles].sort_values('Edad Sem.', ascending=False).copy()

    # --- FORMATO DE FECHAS DD/MM/AA ---
    for col_fecha in ['Final Sem', 'Inicio Sem']:
        if col_fecha in tabla_final.columns:
            tabla_final[col_fecha] = pd.to_datetime(tabla_final[col_fecha]).dt.strftime('%d/%m/%y')

    # Diccionario de formatos numéricos
    formatos = {
        'Saldo de Aves': '{:,.0f}', 'Huevos  Semana': '{:,.0f}',
        'Edad Sem.': '{:.0f}', 'Mort': '{:.0f}', 'Suma Mort + Sel': '{:.1f}',
        '% Mort + Sel Acum.': '{:.1f}%', '%Mort+Sel Acum. Tab': '{:.1f}%', 'Bulto X 40 K': '{:.1f}',
        'Gr.A.D Real': '{:.1f}', 'Gr.A.D Tabla': '{:.1f}', '% Unif': '{:.1f}%',
        'Peso Real': '{:.1f}', 'Peso Tab': '{:.1f}', '% Pdn. Real': '{:.1f}%',
        '% Pdn. Tabla': '{:.1f}%', 'H.A.A. Real': '{:.1f}', 'H.A.A. Tabla': '{:.1f}',
        'Costo Alimento Sem': '${:,.0f}', '$ Huevo por alimento': '${:,.1f}',
        'Dif Pdn': '{:+.1f}%', 'Dif GAD': '{:+.1f}', 'Dif HAA': '{:+.1f}', 'Dif Peso': '{:+.1f}', 'Dif Mort': '{:+.1f}%'
    }
    
    # Semáforo de colores
    def color_diferencia(val):
        color = '#27ae60' if val > 0 else '#e74c3c' if val < 0 else '#636e72'
        return f'color: {color}; font-weight: bold'

    formatos_activos = {k: v for k, v in formatos.items() if k in tabla_final.columns}

    st.dataframe(
        tabla_final.style.format(formatos_activos)
        .applymap(color_diferencia, subset=[c for c in ['Dif Pdn', 'Dif GAD', 'Dif HAA', 'Dif Peso', 'Dif Mort'] if c in tabla_final.columns]),
        use_container_width=True, hide_index=True
    )

    # --- G. FOOTER ---
    st.divider()
    st.markdown("""
        <div class='footer-tematico'>
            <div class='footer-pattern'>🐔 🥚 🐔 🥚 🐔 🥚 🐔</div>
            <div class='footer-text'>
                <b>HUPA | División Avícola</b><br>
                Análisis de Datos para la Excelencia Productiva<br>
                <span style="font-size: 0.8rem;">© 2026</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("No se pudo cargar el archivo.")