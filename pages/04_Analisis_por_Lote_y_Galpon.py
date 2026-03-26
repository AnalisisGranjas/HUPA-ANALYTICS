import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os
from sklearn.ensemble import IsolationForest

# --- 1. SEGURIDAD ---
if 'auth' not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

# --- 2. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="HUPA | Asistencia Técnica Senior", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align:center; color:#ffffff; background-color: #0d47a1; padding: 15px; border-radius: 15px; margin-bottom: 20px; font-weight: bold; font-size: 1.8rem; }
    .filter-box { background-color: #f8f9fa; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #e6e9ef; }
    .hr-custom { border: 0; height: 4px; background-color: #0d47a1; margin: 35px 0; opacity: 0.8; border-radius: 2px; }
    .section-header { color: #0d47a1; font-weight: bold; font-size: 1.5rem; margin-bottom: 15px; border-left: 8px solid #ff9800; padding-left: 15px; text-transform: uppercase; text-align: left; }
    .ai-card { background-color: #fff3e0; padding: 30px; border-radius: 15px; border-left: 15px solid #ff9800; margin-bottom: 25px; color: #1a237e; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .galpon-ai-box { background-color: rgba(255,255,255,0.5); padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #ffcc80; }
    .intro-card { background-color: #e3f2fd; padding: 25px; border-radius: 15px; border-left: 8px solid #0d47a1; margin-bottom: 25px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")

@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        try:
            df = pd.read_excel(PATH_DATA)
            df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
            # Limpieza y conversión masiva
            for col in df.columns:
                if col not in ['GRANJA', 'LOTE', 'NUM_GALPON', 'Final Sem', 'Observaciones']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Error Crítico: {e}")
            return None
    return None

df_orig = load_data()

if df_orig is not None:

    
    st.markdown('<div class="main-title">🚀 INTELIGENCIA DE GALPONES Y ASISTENCIA TÉCNICA</div>', unsafe_allow_html=True)


    # --- PROTOCOLO ESTRATÉGICO DE AUDITORÍA ---
    st.markdown(f"""
        <div class="intro-card" style="background-color: #e3f2fd; padding: 30px; border-radius: 15px; border-left: 10px solid #0d47a1; margin-bottom: 25px;">
            <h3 style="color: #0d47a1; margin-top:0; text-align:center;">📋 FUNDAMENTOS DE LA AUDITORÍA DE GALPONES</h3>
            <p style="text-align: justify; font-size: 1.05rem; line-height: 1.6; color: #1a237e;">
                <b>¿Qué estamos analizando?</b> Realizamos una disección técnica de un Lote Biológico para comparar el comportamiento individual de sus naves (Galpones). Desglosamos la "masa" de datos para encontrar ineficiencias que el promedio general del lote suele ocultar.<br><br>
                <b>¿Cómo lo hacemos?</b> Mediante algoritmos de correlación, comparamos cada galpón contra su propia meta genética y contra sus "hermanos". Evaluamos la tríada maestra: <b>Producción de Huevo, Dinámica de Consumo y Tasa de Viabilidad.</b><br><br>
                <b>¿Por qué es vital?</b> En lotes de la misma edad, genética y nutrición, cualquier diferencia en resultados es una <b>auditoría directa al manejo</b>. Si un galpón rinde menos, el problema no es el ave ni el alimento; es el ambiente, el equipo o el protocolo operativo de esa nave específica.<br><br>
                <b>Importancia:</b> La uniformidad entre galpones es el indicador más puro de <b>Rentabilidad Real</b>. Detectar un desvío a tiempo permite corregir fallas en iluminación, ventilación o desperdicio de alimento antes de que se conviertan en pérdidas económicas irreversibles.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Lógica Galpón individual
    df_desglose = df_orig[df_orig['LOTE'] != df_orig['NUM_GALPON']].copy()
    df_desglose['GALPON_ID'] = "Galpón " + df_desglose['NUM_GALPON'].astype(str)

    # --- FILTROS ---
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1: granja_sel = st.selectbox("🗺️ Selecciona Granja:", sorted(df_desglose['GRANJA'].unique()))
    with f2:
        df_g = df_desglose[df_desglose['GRANJA'] == granja_sel]
        lote_padre = st.selectbox("📦 Selecciona Lote Padre:", sorted(df_g['LOTE'].unique()))
    with f3:
        df_l = df_g[df_g['LOTE'] == lote_padre]
        galpones_disp = sorted(df_l['NUM_GALPON'].unique())
        galpon_sel = st.multiselect("🏠 Auditoría por Galpón:", galpones_disp, default=galpones_disp)
    
    st.write("---")
    cx1, cx2 = st.columns(2)
    with cx1: ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas en gráficos", value=False)
    with cx2: ver_meta = st.toggle("📉 Ver Meta Genética Ideal", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

    df_filtered = df_l[df_l['NUM_GALPON'].isin(galpon_sel)].copy()
    
    if df_filtered.empty:
        st.warning("⚠️ Por favor seleccione galpones para procesar los datos.")
    else:
        # Control de Slider
        max_e = int(df_filtered['Edad Sem.'].max())
        min_e = int(df_filtered['Edad Sem.'].min())
        rango_edad = st.slider("⏳ Ventana de Análisis (Semanas):", min_e, max_e, (max(min_e, max_e-3), max_e))
        
        df_view = df_filtered[df_filtered['Edad Sem.'].between(rango_edad[0], rango_edad[1])].copy()
        
        # Cálculos de Diferencias y Redondeo a 1 decimal
        df_view['Conv'] = ((df_view['Bulto X 40 K'] * 40000) / df_view['Huevos  Semana'].replace(0,1)).round(1)
        df_view['Dif Pdn'] = (df_view['% Pdn. Real'] - df_view['% Pdn. Tabla']).round(1)
        df_view['Dif GAD'] = (df_view['Gr.A.D Real'] - df_view['Gr.A.D Tabla']).round(1)
        df_view['Dif Mort'] = (df_view['%Mort+Sel Acum. Tab'] - df_view['% Mort + Sel Acum.']).round(1)
        df_view['Dif Peso'] = (df_view['Peso Real'] - df_view['Peso Tab']).round(1)

        # --- SECCIÓN A: ASISTENCIA TÉCNICA IA (DIAGNÓSTICO ESTRATÉGICO) ---
        st.markdown('<div class="section-header">🤖 ASISTENCIA TÉCNICA ESTRATÉGICA IA</div>', unsafe_allow_html=True)
        
        ultimo_corte = df_view[df_view['Edad Sem.'] == df_view['Edad Sem.'].max()].copy()
        
        if not ultimo_corte.empty:
            st.markdown(f'<div class="ai-card"><h3 style="text-align:center;">🩺 Evaluación Técnica de Campo - Semana {int(df_view["Edad Sem."].max())}</h3>', unsafe_allow_html=True)
            
            for _, row in ultimo_corte.iterrows():
                g = row['NUM_GALPON']
                pdn_r, pdn_t = row['% Pdn. Real'], row['% Pdn. Tabla']
                gad_r, gad_t = row['Gr.A.D Real'], row['Gr.A.D Tabla']
                mort_s = row['Mort']
                conv = row['Conv']
                
                # Construcción de la Narrativa Técnica Integral
                diag_html = f'<div class="galpon-ai-box"><b>🏠 GALPÓN {g}:</b><br>'
                
                # --- LÓGICA DE PRODUCCIÓN Y MANEJO ---
                if pdn_r >= pdn_t:
                    diag_html += f"🚀 <b>Producción Excelente:</b> El galpón está superando la meta genética ({pdn_r:.1f}%). <b>Manejo:</b> Mantener el estímulo lumínico actual y no realizar cambios bruscos en el horario de alimentación para evitar estrés. "
                elif pdn_r < pdn_t and pdn_r >= (pdn_t - 2):
                    diag_html += f"📉 <b>Producción Estable:</b> Se mantiene en el rango de tolerancia. <b>Manejo:</b> Monitorear la uniformidad del lote; si la persistencia flaquea, revisar la calidad del agua y la limpieza de tuberías. "
                else:
                    diag_html += f"🚨 <b>Producción Bajo Meta:</b> Brecha crítica de {abs(pdn_r-pdn_t):.1f}%. <b>Manejo:</b> Revisar inmediatamente la intensidad lumínica (Lux) en los puntos oscuros del galpón y descartar cuadros virales. "

                # --- LÓGICA DE CONSUMO Y EFICIENCIA ---
                if gad_r > (gad_t + 4):
                    diag_html += f"<br>🥣 <b>Alerta de Consumo:</b> Ingesta elevada ({gad_r:.1f}g). <b>Acción:</b> Si la producción no sube proporcionalmente, hay desperdicio mecánico en comederos o falta de frescura en el alimento. Ajustar niveles de tolva. "
                elif gad_r < (gad_t - 4):
                    diag_html += f"<br>⚠️ <b>Consumo Deficiente:</b> La gallina no está alcanzando la ingesta necesaria. <b>Acción:</b> Revisar palatabilidad del alimento o posibles problemas de ventilación que generen amoniaco alto. "
                else:
                    diag_html += f"<br>✅ <b>Consumo Óptimo:</b> Ingesta alineada con el gasto metabólico requerido para la postura. "

                # --- LÓGICA DE MORTALIDAD ---
                if mort_s > 0.05:
                    diag_html += f"<br>⚰️ <b>Alerta Sanitaria:</b> Mortalidad semanal fuera de control ({mort_s:.2f}%). <b>Acción:</b> Realizar necropsias de aves frescas de inmediato. Revisar niveles de cloro en agua y bioseguridad en el ingreso. "
                
                diag_html += "</div>"
                st.markdown(diag_html, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- SECCIÓN B: MAPA DE CALOR ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🔥 MAPA DE CALOR: EVOLUCIÓN DE PRODUCCIÓN</div>', unsafe_allow_html=True)
        df_heat = df_view.pivot(index='GALPON_ID', columns='Edad Sem.', values='% Pdn. Real').fillna(0).round(1)
        fig_heat = px.imshow(df_heat, color_continuous_scale="RdYlGn", labels=dict(x="Semana", y="Galpón", color="% Pdn"))
        fig_heat.update_layout(title="<b>POSTURA POR SEMANA Y GALPÓN</b>", title_x=0.5, height=350)
        fig_heat.update_traces(hovertemplate="Galpón: %{y}<br>Semana: %{x}<br>Producción: %{z:.1f}%<extra></extra>")
        st.plotly_chart(fig_heat, use_container_width=True)

        # --- SECCIÓN C: LOS 6 GRÁFICOS TÉCNICOS ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align:center; color:#0d47a1;">📈 INDICADORES TÉCNICOS DE PRODUCCIÓN</h2>', unsafe_allow_html=True)

        def plot_tecnico(df, y_col, tab_col, title, unit, labels, meta_line):
            fig = px.line(df.sort_values(['GALPON_ID', 'Edad Sem.']), x='Edad Sem.', y=y_col, color='GALPON_ID', markers=True)
            if meta_line and tab_col in df.columns:
                df_m = df.groupby('Edad Sem.')[tab_col].mean().reset_index()
                fig.add_scatter(x=df_m['Edad Sem.'], y=df_m[tab_col], mode='lines', line=dict(color='black', dash='dot', width=2), name='Meta Genética')
            fig.update_layout(title=f"<b>{title}</b>", title_x=0.5, height=400, hovermode="x unified", legend=dict(orientation="h", y=-0.2))
            fig.update_traces(texttemplate="%{y:.1f}" if labels else None, textposition="top center", 
                              hovertemplate="Valor: %{y:.1f}"+unit)
            return fig

        # Fila 1: Postura y Consumo
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(plot_tecnico(df_view, '% Pdn. Real', '% Pdn. Tabla', "PRODUCCIÓN SEMANAL (%)", "%", ver_etiquetas, ver_meta), use_container_width=True)
        with c2: st.plotly_chart(plot_tecnico(df_view, 'Gr.A.D Real', 'Gr.A.D Tabla', "CONSUMO DE ALIMENTO (G)", "g", ver_etiquetas, ver_meta), use_container_width=True)
        
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        
        # Fila 2: Viabilidad y Peso
        c3, c4 = st.columns(2)
        with c3: st.plotly_chart(plot_tecnico(df_view, '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', "VIABILIDAD ACUMULADA (%)", "%", ver_etiquetas, ver_meta), use_container_width=True)
        with c4: st.plotly_chart(plot_tecnico(df_view, 'Peso Real', 'Peso Tab', "PESO CORPORAL (GRAMOS)", "g", ver_etiquetas, ver_meta), use_container_width=True)
        
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        
        # Fila 3: HAA y Conversión
        c5, c6 = st.columns(2)
        with c5: st.plotly_chart(plot_tecnico(df_view, 'H.A.A. Real', 'H.A.A. Tabla', "HUEVOS POR AVE ALOJADA", "", ver_etiquetas, ver_meta), use_container_width=True)
        with c6: st.plotly_chart(plot_tecnico(df_view, 'Conv', None, "CONVERSIÓN (G ALIMENTO / HUEVO)", "g", ver_etiquetas, False), use_container_width=True)

        # --- SECCIÓN D: MATRIZ DE AUDITORÍA INTEGRAL ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📋 MATRIZ DE AUDITORÍA INTEGRAL</div>', unsafe_allow_html=True)
        
        tabs = st.tabs([f"🏠 Galpón {n}" for n in sorted(df_view['NUM_GALPON'].unique())])
        
        cols_finales = [
            'GRANJA', 'LOTE', 'NUM_GALPON', 'Final Sem', 'Edad Sem.', 'Saldo de Aves', 
            'Mort', 'Suma Mort + Sel', '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort',
            'Bulto X 40 K', 'Gr.A.D Real', 'Gr.A.D Tabla', 'Dif GAD',
            'Peso Real', 'Peso Tab', 'Dif Peso',
            'Huevos  Semana', '% Pdn. Real', '% Pdn. Tabla', 'Dif Pdn',
            'H.A.A. Real', 'H.A.A. Tabla', 'Picado', 'Roto', '% Unif',
            'Costo Alimento Sem', '$ Huevo por alimento'
        ]

        usuario = st.session_state.get('user', 'VET_HUPA')

        for i, tab in enumerate(tabs):
            with tab:
                df_tab = df_view[df_view['NUM_GALPON'] == sorted(df_view['NUM_GALPON'].unique())[i]].sort_values('Edad Sem.', ascending=False).copy()
                
                # Seguridad de costos
                render_cols = [c for c in cols_finales if c not in (['Costo Alimento Sem', '$ Huevo por alimento'] if usuario == "VET_HUPA" else [])]
                present_cols = [c for c in render_cols if c in df_tab.columns]
                
                if 'Final Sem' in df_tab.columns:
                    df_tab['Final Sem'] = pd.to_datetime(df_tab['Final Sem']).dt.strftime('%d/%m/%y')

                # Formateo estricto a 1 decimal
                formatos = {c: '{:.1f}' for c in df_tab.columns if df_tab[c].dtype in ['float64', 'int64']}
                formatos.update({
                    '% Pdn. Real': '{:.1f}%', '% Pdn. Tabla': '{:.1f}%', 'Dif Pdn': '{:+.1f}%',
                    '% Mort + Sel Acum.': '{:.1f}%', 'Dif Mort': '{:+.1f}%', 'Dif GAD': '{:+.1f}',
                    'Costo Alimento Sem': '${:,.0f}', '$ Huevo por alimento': '${:,.1f}'
                })

                st.dataframe(df_tab[present_cols].fillna(0).style.format(formatos).applymap(
                    lambda v: f'color: {"#27ae60" if v > 0 else "#e74c3c" if v < 0 else "#636e72"}; font-weight: bold',
                    subset=[c for c in ['Dif Pdn', 'Dif GAD', 'Dif Mort', 'Dif Peso'] if c in df_tab.columns]
                ), use_container_width=True, hide_index=True)

    # --- G. FOOTER TEMÁTICO (Añadir al final del bloque if df_orig is not None) ---
    st.divider()
    st.markdown("""
        <div class='footer-tematico' style='margin-top: 20px; padding: 30px 0; text-align: center; opacity: 0.6;'>
            <div class='footer-pattern' style='font-size: 1.8rem; letter-spacing: 12px; margin-bottom: 15px;'>
                🐔 🥚 🐔 🥚 🐔 🥚 🐔
            </div>
            <div class='footer-text'>
                <b>HUPA | División Avícola</b><br>
                Análisis de Datos para la Excelencia Productiva<br>
                C.A<b><br>
                <span style="font-size: 0.8rem;">© 2026</span>
            </div>
        </div>
    """, unsafe_allow_html=True)