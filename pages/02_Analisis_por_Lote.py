import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import datetime
import io

#NO TOCAR NADA // TERMINADA EL 27/04/2026 POR CAMILO

def convertir_a_excel(df):
    output = io.BytesIO()
    # Usamos XlsxWriter como motor para asegurar compatibilidad
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Detalle_Auditoria')
    return output.getvalue()

# Motor predictivo avanzado
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

def obtener_prediccion_ia(df_historico, columna_y, semanas_futuras=3):
    try:
        df_base = df_historico[df_historico['Edad Sem.'] >= 30].sort_values('Edad Sem.')
        if len(df_base) < 4: return None, None
        
        semanas_reales = df_base['Edad Sem.'].tolist()
        predicciones_pasadas = []
        
        # Para cada semana desde la 34, predecimos usando las 4 anteriores
        for i in range(4, len(semanas_reales)):
            entrenamiento = df_base.iloc[i-4:i] # Las 4 semanas previas
            X = entrenamiento[['Edad Sem.']].values
            y = entrenamiento[columna_y].values
            
            model = LinearRegression().fit(X, y)
            # Predecimos la semana actual (donde estamos parados)
            sem_actual = semanas_reales[i]
            pred_actual = model.predict([[sem_actual]])[0]
            predicciones_pasadas.append((sem_actual, pred_actual))
            
        # 2. PROYECTAR EL FUTURO (Las 3 semanas que vienen)
        # Usamos las últimas 4 semanas reales para ver el futuro
        ultimas_4 = df_base.tail(4)
        model_futuro = LinearRegression().fit(ultimas_4[['Edad Sem.']].values, ultimas_4[columna_y].values)
        
        ultima_sem = semanas_reales[-1]
        futuro_x = []
        futuro_y = []
        for f in range(1, semanas_futuras + 1):
            s_f = ultima_sem + f
            futuro_x.append(s_f)
            futuro_y.append(model_futuro.predict([[s_f]])[0])
            
        # Unimos todo: Pasado reconstruido + Futuro proyectado
        x_final = [p[0] for p in predicciones_pasadas] + futuro_x
        y_final = [p[1] for p in predicciones_pasadas] + futuro_y
        
        return np.array(x_final), np.array(y_final)
    except:
        return None, None

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
    .v-line { border-left: 2px solid rgba(26, 35, 126, 0.2); height: 100px; margin: auto; width: 1px; }
    @media (max-width: 768px) {
        .v-line { display: none; } /* Desaparece en móvil */
        .hr-custom { margin: 20px 0; } /* Reduce espacios en móvil */
        .main-title { font-size: 1.5rem; padding: 10px; }
    }        
    
    /* BLOQUES NARRATIVOS */
    .intro-box { background-color: #f8f9fa; padding: 25px; border-radius: 15px; border-left: 8px solid #1a237e; margin-bottom: 20px; shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .story-box { background-color: #e3f2fd; padding: 20px; border-radius: 12px; border-left: 6px solid #0d47a1; margin: 20px 0; font-size: 1.1rem; color: #1565c0; line-height: 1.6; }
    .guide-box { background-color: #ffffff; padding: 15px; border: 1px dashed #1a237e; border-radius: 8px; margin-top: 10px; font-size: 0.95rem; color: #333; line-height: 1.6; }
    
    /* --- DISEÑO DE TARJETAS PREMIUM --- */
    .kpi-card { 
        padding: 20px 10px; 
        border-radius: 18px; 
        color: white; 
        text-align: center; 
        margin-bottom: 15px; 
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        border: 1px solid rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }

    /* Efecto de Brillo de Cristal */
    .kpi-card::after {
        content: "";
        position: absolute;
        top: -50%;
        left: -60%;
        width: 20%;
        height: 200%;
        background: rgba(255, 255, 255, 0.1);
        transform: rotate(30deg);
        transition: all 0.6s ease;
    }

    .kpi-card:hover::after { left: 120%; }

    .kpi-card:hover { 
        transform: translateY(-8px); 
        filter: brightness(1.15); 
        box-shadow: 0 15px 30px rgba(0,0,0,0.3);
    }

    /* Colores y Tipografía */
    .kpi-curva { background: linear-gradient(135deg, #1e3a8a, #3b82f6); } 
    .kpi-consumo { background: linear-gradient(135deg, #6a11cb, #2575fc); } 
    .kpi-mort { background: linear-gradient(135deg, #b91c1c, #ef4444); } 
    .kpi-haa { background: linear-gradient(135deg, #d97706, #b45309); }
    .kpi-saldo { background: linear-gradient(135deg, #2c3e50, #4b79a1); }

    .val-num { 
        font-size: clamp(1.6rem, 2vw, 2.3rem); 
        font-weight: 800; 
        display: block; 
        text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        line-height: 1;
        margin: 10px 0;
    }

    .label-card { 
        font-size: clamp(0.8rem, 0.9vw, 1.1rem); 
        font-weight: 800; 
        text-transform: uppercase; 
        letter-spacing: 1.2px;
    }

    .status-ok { color: #2ecc71; font-weight: bold; font-size: 0.9rem; }
    .status-bad { color: rgba(255, 255, 255, 0.85); font-weight: bold; }
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
        saldo_inicial = df_full_lote['Saldo de Aves'].max()
        aves_perdidas = df_full_lote['Mort'].sum()
        
        # --- TARJETAS KPIs CON MOVIMIENTO ---
        k_cols = st.columns(5)
        
        def render_kpi(col, title, emoji, val, tab, ant_val, unit, css_class, is_mort=False):
            html_tab = ""
            if tab is not None:
                dif = val - tab
                status = "status-ok" if (dif >= 0 if not is_mort else dif <= 0) else "status-bad"
                html_tab = f'<span class="{status}" style="font-size:1.2rem;">Vs Tab: {dif:+.1f}{unit}</span>'
    
            html_ant = ""
            if ant_val is not None:
                cambio = val - ant_val
                flecha = "▲" if val >= ant_val else "▼"
                html_ant = f'<span style="font-size:1.2rem; opacity:0.9;">Vs Ant: {flecha}{abs(cambio):.1f}</span>'

            val_display = f"{val:,.0f}" if not unit else f"{val:.1f}"

            if title == "SALDO AVES":
                txt_inicial = f"{saldo_inicial:,.0f}"
                txt_mortalidad = f"{aves_perdidas:,.0f}"
                html_ant = f'<span style="font-size:1.1rem; opacity:0.9;">Alojadas: {txt_inicial}</span>'
                html_tab = f'<span style="font-size:1.1rem; opacity:0.9;">Mort: {txt_mortalidad}</span>'
            col.markdown(f"""
    <div class="kpi-card {css_class}">
    <div style='margin-bottom: 5px;'>
    <span style='font-size:1.2rem; margin-right: 5px;'>{emoji}</span>
    <span class="label-card">{title}</span>
    </div>                
    <span class="val-num">{val_display}{unit}</span>               
    <div style='display: flex; gap: 15px; justify-content: center; width: 100%; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 8px; margin-top: 5px;'>
    {html_ant}
    {html_tab}
    </div>
    </div>
    """, unsafe_allow_html=True)

        # --- LLAMADAS A LAS 5 TARJETAS ---
        render_kpi(k_cols[0], "PRODUCCION", "🥚", ult['% Pdn. Real'], ult['% Pdn. Tabla'], ant['% Pdn. Real'], "%", "kpi-curva")
        render_kpi(k_cols[1], "CONSUMO", "🥣", ult['Gr.A.D Real'], ult['Gr.A.D Tabla'], ant['Gr.A.D Real'], "g", "kpi-consumo")
        render_kpi(k_cols[2], "MORTALIDAD ACUM", "💀", ult['% Mort + Sel Acum.'], ult['%Mort+Sel Acum. Tab'], ant['% Mort + Sel Acum.'], "%", "kpi-mort", True)
        render_kpi(k_cols[3], "H.A.A", "🏆", ult['H.A.A. Real'], ult['H.A.A. Tabla'], ant['H.A.A. Real'], "", "kpi-haa")
        render_kpi(k_cols[4], "SALDO AVES", "🐥", ult['Saldo de Aves'], None, None, "", "kpi-saldo")

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
        range_age = st.slider("⏳ Seleccionar Semanas:", float(df_full_lote['Edad Sem.'].min()), max_age + 1.0, (max_age-6.0, max_age), 1.0)
        df_lote = df_full_lote[(df_full_lote['Edad Sem.'] >= range_age[0]) & (df_full_lote['Edad Sem.'] <= range_age[1])].copy()

        # --- CONTROLES DE GRÁFICOS ---
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            ver_labels = st.toggle("🔖 Ver etiquetas de datos ", value=False)
        with col_t2:
            ver_ia = st.toggle("🤖 Activar Predicción IA", value=False)

        # --- FUNCIÓN GRÁFICOS (VERSIÓN FINAL CON IA) ---
        def plot_hupa_final(df_current, df_total, real_col, tab_col, title, unit):
            df_plot = df_current.copy()

            modo_visual = "lines+markers+text" if ver_labels else "lines+markers"
            if tab_col and tab_col in df_plot.columns:
                df_plot['dif_val'] = (df_plot[real_col] - df_plot[tab_col]).round(1)
                y_list = [real_col, tab_col]
                htemp = "<b>Semana: %{x}</b><br>Real: %{y:.1f}" + unit + "<br>Tabla: %{customdata[0]:.1f}" + unit + "<br>Diferencia: <b>%{customdata[1]:+.1f}</b>" + unit + "<extra></extra>"
                cdata = df_plot[[tab_col, 'dif_val']]
            else:
                y_list = [real_col]
                htemp = "<b>Semana: %{x}</b><br>Real: %{y:.1f}" + unit + "<extra></extra>"
                cdata = df_plot[real_col]

            fig = px.line(df_plot, x='Edad Sem.', y=y_list, markers=True,
              color_discrete_map={
                  real_col: "#ee7f0f", 
                  tab_col: '#808080'    
              })
            fig.update_traces(selector={"name": real_col}, mode=modo_visual, text=df_plot[real_col], 
                              texttemplate="<b>%{text:.1f}</b>", textposition="top center", 
                              textfont=dict(size=15, color="#ee7f0f"), hovertemplate=htemp, customdata=cdata)
              
            if tab_col and tab_col in df_plot.columns:
                fig.update_traces(
                    selector={"name": tab_col}, 
                    mode=modo_visual,
                    text=df_plot[tab_col], 
                    texttemplate="%{text:.1f}", 
                    textposition="bottom center", 
                    textfont=dict(size=15, color=None),
                    line=dict(dash='dot', width=2)
            )
            
            if len(fig.data) > 1:
                for trace in fig.data:
                    if trace.name == tab_col: 
                        trace.update(line=dict(dash='dot', width=2), hoverinfo='skip')
            
            # --- 🤖 IA CON FILTRO DE RANGO ---
            if ver_ia and ML_AVAILABLE:
                semanas_ia, valores_ia = obtener_prediccion_ia(df_total, real_col)
                if semanas_ia is not None:
                    min_vista = df_plot['Edad Sem.'].min()
                    mask = semanas_ia >= min_vista
                    semanas_filtradas = semanas_ia[mask]
                    valores_filtrados = valores_ia[mask]

                    fig.add_trace(go.Scatter(
                        x=semanas_filtradas, 
                        y=valores_filtrados, 
                        name="🤖 Tendencia IA",
                        line=dict(color="#00d2ff", width=3, dash="dashdot"),
                        mode="lines",
                        hovertemplate="<b>Proyección IA:</b> %{y:.1f}" + unit + "<extra></extra>"
                    ))


            fig.update_layout(
                    title={'text': f"<b>{title}</b>", 'x': 0.5, 'xanchor': 'center'},
                    hovermode="x unified",
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)',  
                    font=dict(color=None), 
                    legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5)
            )

            fig.update_xaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            fig.update_yaxes(showgrid=True, gridcolor='rgba(128,128,128,0.2)')

            return fig

        # --- SECCIONES DE GRÁFICOS ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g1, sep1, g2 = st.columns([10, 1, 10])
        with g1: 
            fig1 = plot_hupa_final(df_lote, df_full_lote, '% Pdn. Real', '% Pdn. Tabla', "🥚 PRODUCCION (%)", "%")
            st.plotly_chart(fig1, use_container_width=True, theme="streamlit")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Medimos la eficiencia de la producción. Si la línea azul cae bajo la negra, las aves priorizan su mantenimiento sobre la producción.</div>', unsafe_allow_html=True)
        with sep1: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g2: 
            fig2 = plot_hupa_final(df_lote, df_full_lote, 'Gr.A.D Real', 'Gr.A.D Tabla', "🌽 CONSUMO DE ALIMENTO (G)", "g")
            st.plotly_chart(fig2, use_container_width=True, theme="streamlit")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> El alimento es el costo variable #1. Si comen más sin producir más, hay ineficiencia. Si comen menos, la producción caerá.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g3, sep2, g4 = st.columns([10, 1, 10])
        with g3: 
            fig3 = plot_hupa_final(df_lote, df_full_lote, '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', "⚰️ MORTALIDAD ACUM (%)", "%")
            st.plotly_chart(fig3, use_container_width=True, theme="streamlit")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Supervivencia del lote encasetado. Lo ideal es ir bajo la línea negra. Un repunte es una alerta sanitaria inmediata.</div>', unsafe_allow_html=True)
        with sep2: st.markdown('<div class="v-line"></div>', unsafe_allow_html=True)
        with g4: 
            fig4 = plot_hupa_final(df_lote, df_full_lote, 'Peso Real', 'Peso Tab', "🐤 PESO CORPORAL (G)", "g")
            st.plotly_chart(fig4, use_container_width=True, key="ps_1")
            st.markdown('<div class="guide-box"><b>Observaciones:</b> El peso es la batería del ave. Si es bajo, la gallina no llegará a una vejez productiva rentable.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True) 
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
        
        # 1. TÍTULO Y BOTÓN PROYECTOR
        c_tit, c_tog = st.columns([7, 3])
        with c_tit:
            st.markdown("### 📋 Historial Detallado del Lote")
        with c_tog:
            modo_proyector = st.toggle("📽️ Modo Proyector (Letra Grande)", value=False)
        # 2. LÓGICA DE COLUMNAS SEGÚN USUARIO
        cols_base = ['GRANJA', 
                    'LINEA_AVES',
                    'LOTE',
                    'Final Sem',
                    'Edad Sem.', 
                    'Saldo de Aves', 
                    'Mort', 
                    'Suma Mort + Sel', 
                    '% Mort + Sel Acum.', 
                    '%Mort+Sel Acum. Tab', 
                    'Dif Mort',
                    'Fase de Alimento', 
                    'Observaciones', 
                    'Bulto X 40 K',
                    'Huevos  Semana', 
                    'Gr.A.D Real', 
                    'Gr.A.D Tabla', 
                    'Dif GAD',
                    '% Pdn. Real', 
                    '% Pdn. Tabla', 
                    'Dif Pdn',
                    '% Unif', 
                    'Peso Real', 
                    'Peso Tab', 
                    'Dif Peso', 
                    'H.A.A. Real', 
                    'H.A.A. Tabla', 
                    'Dif HAA',
                    'Costo Alimento Sem', 
                    '$ Huevo por alimento']

        usuario_actual = st.session_state.get('user', 'VET_HUPA')
        if usuario_actual == "VET_HUPA":
            lista_negra = ['Costo Alimento Sem', '$ Huevo por alimento']
            cols_disponibles = [c for c in cols_base if c in df_full_lote.columns and c not in lista_negra]
        else:
            cols_disponibles = [c for c in cols_base if c in df_full_lote.columns]

        # 3. EL SELECTOR DENTRO DE UN MENÚ DESPLEGABLE (Limpio y elegante)
        with st.popover("⚙️ Personalizar columnas visibles"):
            st.write("Marca las columnas que deseas incluir:")  
            columnas_visibles = []

            for col in cols_disponibles:
                es_default = col in ['Edad Sem.', 'Saldo de Aves', 'Mort', '% Mort + Sel Acum.', 'Gr.A.D Real', '% Pdn. Real', 'H.A.A. Real']
                if st.checkbox(col, value=col in cols_disponibles, key=f"check_{col}"):
                    columnas_visibles.append(col)  

        # 4. CREAMOS LA TABLA SOLO CON LAS COLUMNAS QUE ELEGISTE
        if not columnas_visibles:
            st.warning("⚠️ Por favor, selecciona al menos una columna para mostrar la tabla.")
            st.stop()
            
        tabla_final = df_lote[columnas_visibles].sort_values('Edad Sem.', ascending=False).copy()
        
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

        tabla_para_presentar = tabla_final.reset_index(drop=True)

        tabla_estilizada = tabla_para_presentar.style \
            .format({k: v for k, v in formatos.items() if k in tabla_para_presentar.columns}) \
            .map(style_diferencias, subset=[c for c in ['Dif Pdn', 'Dif GAD', 'Dif HAA', 'Dif Peso', 'Dif Mort'] if c in tabla_para_presentar.columns]) \
            .hide(axis="index") 
        if modo_proyector:
            st.markdown("""
                <style>
                /* 1. Encabezados Naranjas */
                thead tr th {
                    background-color: #FF8C00 !important;
                    color: white !important;
                    font-size: 1.2rem !important;
                    font-weight: bold !important;    
                    text-align: center !important;    
                }
                
                /* 2. Cuerpo de la tabla */
                td {
                    font-size: 1.2rem !important;
                    font-weight: bold !important;
                    white-space: nowrap !important;
                    text-align: center !important;
                }

                /* 3. EXTERMINADOR TOTAL DE ÍNDICE (0, 1, 2...) */
                /* Oculta la columna de etiquetas de fila (index) de Pandas */
                .row_heading, .blank {
                    display: none !important;
                }
                th.index_name {
                    display: none !important;
                }
                /* Por si acaso Streamlit usa su selector nativo */
                [data-testid="stTable"] thead tr th:first-child, 
                [data-testid="stTable"] tbody tr td:first-child {
                    display: none !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            st.table(tabla_estilizada)
            
        else:
            st.markdown("""
        <style>
            /* 1. Color para el encabezado del st.dataframe */
            [data-testid="stHeader"], .stDataFrame thead tr th {
                background-color: #1E3A8A !important;
                color: white !important;
                text-align: center !important;
            }

            /* 2. Color para la esquina superior izquierda (donde suele estar el índice vacío) */
            .stDataFrame thead tr th:first-child {
                background-color: #1E3A8A !important;
            }

            /* 3. Tamaño de letra para el cuerpo */
            .stDataFrame td {
                font-size: 0.9rem !important;
            }
        </style>
            """, unsafe_allow_html=True)                            
            st.dataframe(tabla_estilizada, use_container_width=True, hide_index=True)

            # Preparamos los datos (usamos la tabla limpia sin estilos para el Excel)
            excel_data = convertir_a_excel(tabla_para_presentar)

            st.download_button(
                label="📥 Descargar Tabla Detallada (Excel)",
                data=excel_data,
                file_name=f"Auditoria_Granjas_{datetime.datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" 
            )

            

        try:
            mtime = os.path.getmtime(PATH_DATA)
            fecha_act = datetime.datetime.fromtimestamp(mtime).strftime('%d/%m/%Y %I:%M %p')
            
            st.markdown(f"""
                <div style='text-align: right; opacity: 0.5; font-size: 0.85rem; font-style: italic; margin-top: 10px;'>
                    📅 Última sincronización con el servidor: {fecha_act}
                </div>
            """, unsafe_allow_html=True)
        except:
            pass    
    st.divider()
    st.markdown("""<div style='text-align: center; opacity: 0.6;'><div style='font-size: 1.8rem; letter-spacing: 12px; margin-bottom: 15px;'>🐔 🥚 🐔 🥚 🐔 🥚 🐔</div><b>HUPA | División Avícola</b><br>Análisis de Datos para la Excelencia Productiva<br>C.A<br><span style="font-size: 0.8rem;">© 2026</span></div>""", unsafe_allow_html=True)
else:
    st.error("Archivo no encontrado.")