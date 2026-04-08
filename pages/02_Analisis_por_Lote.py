import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

# Motor predictivo avanzado
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# --- 1. SEGURIDAD ---
if 'auth' not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

# --- 2. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="HUPA | Auditoría Gerencial", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align:center; color:#ffffff; background-color: #1a237e; padding: 20px; border-radius: 15px; margin-bottom: 20px; font-weight: bold; font-size: 2.2rem; }
    .hr-custom { border: 0; height: 4px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(26, 35, 126, 0.8), rgba(0,0,0,0)); margin: 45px 0; }
    .v-line { border-left: 2px solid rgba(26, 35, 126, 0.2); height: 450px; margin: auto; width: 1px; }
    
    /* BLOQUES NARRATIVOS */
    .intro-box { background-color: #f8f9fa; padding: 25px; border-radius: 15px; border-left: 8px solid #1a237e; margin-bottom: 20px; shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .story-box { background-color: #e3f2fd; padding: 20px; border-radius: 12px; border-left: 6px solid #0d47a1; margin: 20px 0; font-size: 1.1rem; color: #1565c0; line-height: 1.6; }
    .guide-box { background-color: #ffffff; padding: 15px; border: 1px dashed #1a237e; border-radius: 8px; margin-top: 10px; font-size: 0.95rem; color: #333; line-height: 1.6; }
    
    /* TARJETAS CON MOVIMIENTO */
    .kpi-card { 
        padding: 20px 10px; border-radius: 15px; text-align: center; color: white; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); transition: all 0.4s ease; 
        min-height: 180px; display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .kpi-card:hover { transform: translateY(-10px) scale(1.02); box-shadow: 0 12px 24px rgba(0,0,0,0.2); filter: brightness(1.1); }
    
    .kpi-curva { background: linear-gradient(135deg, #0052D4, #4364F7); }
    .kpi-consumo { background: linear-gradient(135deg, #FF8C00, #FFA500); }
    .kpi-mort { background: linear-gradient(135deg, #e74c3c, #c0392b); }
    .kpi-haa { background: linear-gradient(135deg, #27ae60, #1D976C); }
    
    .status-ok { color: #2ecc71; font-weight: bold; font-size: 0.95rem; }
    .status-bad { color: #ffeb3b; font-weight: bold; font-size: 0.95rem; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")

@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        df = pd.read_excel(PATH_DATA)
        df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
        num_cols = ['% Pdn. Real', '% Pdn. Tabla', 'Gr.A.D Real', 'Gr.A.D Tabla', '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'H.A.A. Real', 'H.A.A. Tabla', 'Peso Real', 'Peso Tab', 'Saldo de Aves', 'Bulto X 40 K', 'Huevos  Semana']
        for col in [c for c in num_cols if c in df.columns]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    return None

df_orig = load_data()

if df_orig is not None:
    st.markdown('<div class="main-title">📈 AUDITORÍA TÉCNICA DE PRODUCCIÓN</div>', unsafe_allow_html=True)

    # --- INTRODUCCIÓN GERENCIAL ---
    st.markdown("""
        <div style="background-color: #f8f9fa; padding: 30px; border-radius: 15px; border-left: 10px solid #1a237e; margin-bottom: 30px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
            <h3 style="color: #1a237e; margin-top:0; display: flex; align-items: center;">🔍 PROTOCOLO DE FISCALIZACIÓN OPERATIVA</h3>
            <p style="text-align: justify; font-size: 1.1rem; line-height: 1.7; color: #333;">
                Bienvenido al sistema de <b>Control y Seguimiento Biológico</b>. Esta interfaz ha sido diseñada para auditar el cumplimiento de los estándares de manejo y la respuesta metabólica del lote frente a su potencial genético. Aquí, los datos dejan de ser registros aislados para convertirse en un historial vivo de la disciplina operativa en granja.<br><br>
                A través de modelos de <b>Inteligencia Artificial (Regresión Polinomial)</b>, analizamos la trayectoria real de la curva de postura y el consumo de alimento para detectar desviaciones en el confort ambiental o fallos en el protocolo de alimentación. El objetivo es asegurar que la operatividad se mantenga dentro de los parámetros de excelencia, garantizando la estabilidad biológica y la persistencia del lote durante todo su ciclo productivo.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Filtros
    c1, c2, c3 = st.columns(3)
    with c1: empresa = st.selectbox("🏢 Empresa:", sorted(df_orig['RAZON_SOCIAL'].unique()))
    with c2: granja = st.selectbox("🗺️ Granja:", sorted(df_orig[df_orig['RAZON_SOCIAL']==empresa]['GRANJA'].unique()))
    with c3:
        df_activos = df_orig[(df_orig['RAZON_SOCIAL']==empresa) & (df_orig['GRANJA']==granja)]
        df_activos = df_activos[df_activos['LOTE'] == df_activos['NUM_GALPON']]
        lote_sel = st.selectbox("📦 Lote Activo:", sorted(df_activos['LOTE'].unique()))
    
    df_full_lote = df_activos[df_activos['LOTE'] == lote_sel].sort_values('Edad Sem.')

    if not df_full_lote.empty:
        # Cálculos de Diferencias
        df_full_lote['Dif Pdn'] = df_full_lote['% Pdn. Real'] - df_full_lote['% Pdn. Tabla']
        df_full_lote['Dif GAD'] = df_full_lote['Gr.A.D Real'] - df_full_lote['Gr.A.D Tabla']
        df_full_lote['Dif HAA'] = df_full_lote['H.A.A. Real'] - df_full_lote['H.A.A. Tabla']
        df_full_lote['Dif Peso'] = df_full_lote['Peso Real'] - df_full_lote['Peso Tab']
        df_full_lote['Dif Mort'] = df_full_lote['%Mort+Sel Acum. Tab'] - df_full_lote['% Mort + Sel Acum.']
        
        df_full_lote['Conversión'] = (df_full_lote['Bulto X 40 K'] * 40000) / (df_full_lote['Huevos  Semana'].replace(0,1))
        ult = df_full_lote.iloc[-1]
        ant = df_full_lote.iloc[-2] if len(df_full_lote) > 1 else ult

        # --- TARJETAS KPIs CON MOVIMIENTO ---
        k_cols = st.columns(4)
        def render_kpi(col, title, emoji, val, tab, ant_val, unit, css_class, is_mort=False):
            dif = val - tab; status = "status-ok" if (dif >= 0 if not is_mort else dif <= 0) else "status-bad"
            col.markdown(f"""<div class="kpi-card {css_class}"><span style='font-size:1.8rem'>{emoji}</span><br><small>{title}</small><br><span style='font-size:2.2rem; font-weight:800'>{val:.1f}{unit}</span><br><small>Vs Ant: {"▲" if val >= ant_val else "▼"} {abs(val-ant_val):.1f}</small><br><span class="{status}">Vs Tab: {dif:+.1f}{unit}</span></div>""", unsafe_allow_html=True)

        render_kpi(k_cols[0], "PRODUCCION", "🥚", ult['% Pdn. Real'], ult['% Pdn. Tabla'], ant['% Pdn. Real'], "%", "kpi-curva")
        render_kpi(k_cols[1], "CONSUMO", "🥣", ult['Gr.A.D Real'], ult['Gr.A.D Tabla'], ant['Gr.A.D Real'], "g", "kpi-consumo")
        render_kpi(k_cols[2], "MORTALIDAD ACUM", "💀", ult['% Mort + Sel Acum.'], ult['%Mort+Sel Acum. Tab'], ant['% Mort + Sel Acum.'], "%", "kpi-mort", True)
        render_kpi(k_cols[3], "H.A.A", "🏆", ult['H.A.A. Real'], ult['H.A.A. Tabla'], ant['H.A.A. Real'], "", "kpi-haa")

        # --- BLOQUE NARRATIVO (HISTORIA DEL LOTE) ---
        st.markdown(f"""
            <div class="story-box">
                📖 <b>Contexto del Lote:</b> Actualmente estamos auditando la granja <b>{granja}</b>, ubicada en <b>{ult.get('UBICACION', 'N/A')}</b>. 
                El lote seleccionado es el <b>{lote_sel}</b>, el cual cuenta con una genética <b>{ult.get('LINEA_AVES', 'N/A')}</b>. 
                Toda la estrategia nutricional de este periodo está siendo respaldada por la casa nutricional <b>{ult.get('Observaciones', 'N/A')}</b>. 
                A continuación, presentamos el comportamiento técnico y su proyección a futuro.
            </div>
        """, unsafe_allow_html=True)

        # --- CONFIGURACIÓN DE VISTA ---
        max_age = float(df_full_lote['Edad Sem.'].max())
        range_age = st.slider("⏳ Ventana:", float(df_full_lote['Edad Sem.'].min()), max_age + 3.0, (max_age-4.0, max_age), 1.0)
        df_lote = df_full_lote[(df_full_lote['Edad Sem.'] >= range_age[0]) & (df_full_lote['Edad Sem.'] <= range_age[1])].copy()

        # --- FUNCIÓN GRÁFICOS (VERSIÓN FINAL LIMPIA) ---
        def plot_hupa_final(df_current, df_total, real_col, tab_col, title, unit):
            df_plot = df_current.copy()
            if tab_col and tab_col in df_plot.columns:
                df_plot['dif_val'] = (df_plot[real_col] - df_plot[tab_col]).round(1)
                y_list = [real_col, tab_col]
                htemp = "<b>Semana: %{x}</b><br>Real: %{y:.1f}" + unit + "<br>Tabla: %{customdata[0]:.1f}" + unit + "<br>Diferencia: <b>%{customdata[1]:+.1f}</b>" + unit + "<extra></extra>"
                cdata = df_plot[[tab_col, 'dif_val']]
            else:
                y_list = [real_col]
                htemp = "<b>Semana: %{x}</b><br>Real: %{y:.1f}" + unit + "<extra></extra>"
                cdata = df_plot[real_col]

            fig = px.line(df_plot, x='Edad Sem.', y=y_list, markers=True, color_discrete_map={real_col: '#1a237e', tab_col: '#000000'})
            fig.update_traces(selector={"name": real_col}, mode="lines+markers+text", text=df_plot[real_col], 
                              texttemplate="<b>%{text:.1f}</b>", textposition="top center", 
                              textfont=dict(size=15, color="#1a237e"), hovertemplate=htemp, customdata=cdata)
            
            if len(fig.data) > 1:
                for trace in fig.data:
                    if trace.name == tab_col: 
                        trace.update(line=dict(dash='dot', width=2), hoverinfo='skip')
            
            fig.update_layout(title={'text': f"<b>{title}</b>", 'x': 0.5, 'xanchor': 'center'}, 
                              hovermode="x", height=450, margin=dict(t=100, b=50),
                              legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
            return fig

        # --- SECCIONES DE GRÁFICOS ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g1, sep1, g2 = st.columns([10, 1, 10])
        with g1: 
            fig1 = plot_hupa_final(df_lote, df_full_lote, '% Pdn. Real', '% Pdn. Tabla', "🥚 PRODUCCION (%)", "%")
            st.plotly_chart(fig1, use_container_width=True, key="p_1")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Medimos la eficiencia de la producción. Si la línea azul cae bajo la negra, las aves priorizan su mantenimiento sobre la producción.</div>', unsafe_allow_html=True)
        with sep1: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g2: 
            fig2 = plot_hupa_final(df_lote, df_full_lote, 'Gr.A.D Real', 'Gr.A.D Tabla', "🌽 CONSUMO DE ALIMENTO (G)", "g")
            st.plotly_chart(fig2, use_container_width=True, key="c_1")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> El alimento es el costo variable #1. Si comen más sin producir más, hay ineficiencia. Si comen menos, la producción caerá.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g3, sep2, g4 = st.columns([10, 1, 10])
        with g3: 
            fig3 = plot_hupa_final(df_lote, df_full_lote, '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', "⚰️ MORTALIDAD ACUM (%)", "%")
            st.plotly_chart(fig3, use_container_width=True, key="m_1")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Supervivencia del lote encasetado. Lo ideal es ir bajo la línea negra. Un repunte es una alerta sanitaria inmediata.</div>', unsafe_allow_html=True)
        with sep2: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g4: 
            fig4 = plot_hupa_final(df_lote, df_full_lote, 'Peso Real', 'Peso Tab', "🐤 PESO CORPORAL (G)", "g")
            st.plotly_chart(fig4, use_container_width=True, key="ps_1")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> El peso es la batería del ave. Si es bajo, la gallina no llegará a una vejez productiva rentable.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g5, sep3, g6 = st.columns([10, 1, 10])
        with g5: 
            fig5 = plot_hupa_final(df_lote, df_full_lote, 'H.A.A. Real', 'H.A.A. Tabla', "🧑‍🌾 HUEVOS AVE ALOJADA", "")
            st.plotly_chart(fig5, use_container_width=True, key="h_1") 
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Es el contador de huevos que ha pagado cada ave. La brecha con la tabla es dinero dejado de percibir.</div>', unsafe_allow_html=True)
        with sep3: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g6:
            fig6 = plot_hupa_final(df_lote, df_full_lote, 'Conversión', None, "💰 CONVERSIÓN (G Alimento / Huevo)", "g")
            st.plotly_chart(fig6, use_container_width=True, key="cv_1")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> ¿Cuántos gramos cuesta fabricar un huevo? Menor valor significa más dinero en el bolsillo.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g1_d, sep1_d, g2_d = st.columns([10, 1, 10])
        with g1_d: 
            st.plotly_chart(plot_hupa_final(df_lote, df_full_lote, '% Pdn. Real', '% Pdn. Tabla', "🥚 PRODUCCION (%)", "%"), use_container_width=True, key="p_dup")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Medimos la eficiencia de la producción. Si la línea azul cae bajo la negra, las aves priorizan su mantenimiento sobre la producción. La curva púrpura proyecta el agotamiento del lote y/o la pérdida de productividad.</div>', unsafe_allow_html=True)
        with sep1_d: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g2_d: 
            st.plotly_chart(plot_hupa_final(df_lote, df_full_lote, 'Gr.A.D Real', 'Gr.A.D Tabla', "🌽 CONSUMO DE ALIMENTO (G)", "g" ), use_container_width=True, key="c_dup")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> El alimento es el costo variable #1. Si comen más sin producir más, hay ineficiencia. Si comen menos, la producción caerá en los próximos días.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True) # --- LÍNEA SEPARADORA Fila 1 ---
        g3_d, sep2_d, g4_d = st.columns([10, 1, 10])
        with g3_d: 
            st.plotly_chart(plot_hupa_final(df_lote, df_full_lote, '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', "⚰️ MORTALIDAD ACUM (%)", "%"), use_container_width=True, key="m_dup")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Supervivencia del lote encasetado. Lo ideal es ir bajo la línea negra. Un repunte en la curva predictiva es una alerta de incendio sanitario inmediata, analizar el modelo ML nos puede ayudar a anticipar un alsa en la mortalidad.</div>', unsafe_allow_html=True)
        with sep2_d: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g4_d: 
            st.plotly_chart(plot_hupa_final(df_lote, df_full_lote, 'Peso Real', 'Peso Tab', "🐤 PESO CORPORAL (G)", "g"), use_container_width=True, key="ps_dup")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> El peso es la batería del ave. Si es bajo, la gallina se agotará rápido y no llegará a una vejez productiva rentable (se recomienda hacer pesajes todas las semanas).</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True) # --- LÍNEA SEPARADORA Fila 2 ---
        g5_d, sep3_d, g6_d = st.columns([10, 1, 10])
        with g5_d: 
            st.plotly_chart(plot_hupa_final(df_lote, df_full_lote, 'H.A.A. Real', 'H.A.A. Tabla', "🧑‍🌾 HUEVOS AVE ALOJADA", ""), use_container_width=True, key="h_dup")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Es el contador de huevos que ha pagado cada ave. La brecha con la tabla es el dinero dejado de percibir por la falta de eficiencia biológica.</div>', unsafe_allow_html=True)
        with sep3_d: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g6_d:
            st.plotly_chart(plot_hupa_final(df_lote, df_full_lote, 'Conversión', None, "💰 CONVERSIÓN (G Alimento / Huevo)", "g"), use_container_width=True, key="cv_dup")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> ¿Cuántos gramos cuesta fabricar un huevo? Menor valor significa más dinero en el bolsillo. La tendencia púrpura indica la rentabilidad del próximo mes.</div>', unsafe_allow_html=True)

        # --- TABLA TÉCNICA MAESTRA ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        st.markdown("### 📋 Historial Detallado del Lote")
        
        cols_base = ['GRANJA', 'LINEA_AVES', 'LOTE', 'Final Sem', 'Edad Sem.', 'Saldo de Aves', 'Mort', 'Suma Mort + Sel', '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort', 'Observaciones', 'Bulto X 40 K', 'Costo Alimento Sem', '$ Huevo por alimento', 'Gr.A.D Real', 'Gr.A.D Tabla', 'Dif GAD', '% Unif', 'Peso Real', 'Peso Tab', 'Dif Peso', 'Huevos  Semana', '% Pdn. Real', '% Pdn. Tabla', 'Dif Pdn', 'H.A.A. Real', 'H.A.A. Tabla', 'Dif HAA']

        usuario_actual = st.session_state.get('user', 'VET_HUPA')
        if usuario_actual == "VET_HUPA":
            lista_negra = ['Costo Alimento Sem', '$ Huevo por alimento']
            cols_finales = [c for c in cols_base if c in df_full_lote.columns and c not in lista_negra]
        else:
            cols_finales = [c for c in cols_base if c in df_full_lote.columns]

        tabla_final = df_lote[cols_finales].sort_values('Edad Sem.', ascending=False).copy()
        if 'Final Sem' in tabla_final.columns:
            tabla_final['Final Sem'] = pd.to_datetime(tabla_final['Final Sem']).dt.strftime('%d/%m/%y')

        formatos = {
            'Saldo de Aves': '{:,.0f}', 'Huevos  Semana': '{:,.0f}', 'Edad Sem.': '{:.0f}', 'Mort': '{:.0f}', 'Suma Mort + Sel': '{:.1f}',
            '% Mort + Sel Acum.': '{:.1f}%', '%Mort+Sel Acum. Tab': '{:.1f}%', 'Bulto X 40 K': '{:.1f}',
            'Gr.A.D Real': '{:.1f}', 'Gr.A.D Tabla': '{:.1f}', '% Unif': '{:.1f}%',
            'Peso Real': '{:.1f}', 'Peso Tab': '{:.1f}', '% Pdn. Real': '{:.1f}%',
            '% Pdn. Tabla': '{:.1f}%', 'H.A.A. Real': '{:.1f}', 'H.A.A. Tabla': '{:.1f}',
            'Costo Alimento Sem': '${:,.0f}', '$ Huevo por alimento': '${:,.1f}',
            'Dif Pdn': '{:+.1f}%', 'Dif GAD': '{:+.1f}', 'Dif HAA': '{:+.1f}', 'Dif Peso': '{:+.1f}', 'Dif Mort': '{:+.1f}%'
        }
        
        def style_diferencias(val):
            color = '#27ae60' if val > 0 else '#e74c3c' if val < 0 else '#636e72'
            return f'color: {color}; font-weight: bold;'

        st.dataframe(tabla_final.style.format({k: v for k, v in formatos.items() if k in tabla_final.columns}).map(style_diferencias, subset=[c for c in ['Dif Pdn', 'Dif GAD', 'Dif HAA', 'Dif Peso', 'Dif Mort'] if c in tabla_final.columns]), use_container_width=True, hide_index=True)

    # --- FOOTER ---
    st.divider()
    st.markdown("""<div style='text-align: center; opacity: 0.6;'><div style='font-size: 1.8rem; letter-spacing: 12px; margin-bottom: 15px;'>🐔 🥚 🐔 🥚 🐔 🥚 🐔</div><b>HUPA | División Avícola</b><br>Análisis de Datos para la Excelencia Productiva<br>C.A<br><span style="font-size: 0.8rem;">© 2026</span></div>""", unsafe_allow_html=True)
else:
    st.error("Archivo no encontrado.")