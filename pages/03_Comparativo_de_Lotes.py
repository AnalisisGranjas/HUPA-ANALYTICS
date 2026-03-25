import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import os

# --- 1. SEGURIDAD ---
if 'auth' not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

# --- 2. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="HUPA | Comparativo Estratégico", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align:center; color:#ffffff; background-color: #1a237e; padding: 20px; border-radius: 15px; margin-bottom: 20px; font-weight: bold; font-size: 2.2rem; }
    .filter-box { background-color: #f8f9fa; padding: 25px; border-radius: 15px; margin-bottom: 25px; border: 1px solid #e6e9ef; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .hr-custom { border: 0; height: 4px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(26, 35, 126, 0.8), rgba(0,0,0,0)); margin: 35px 0; }
    .instruction-box { background-color: #fff3cd; color: #856404; padding: 20px; border-radius: 10px; text-align: center; font-weight: bold; margin: 20px 0; border: 1px solid #ffeeba; }
    .guide-box { background-color: #ffffff; padding: 15px; border: 1px dashed #1a237e; border-radius: 8px; margin-top: 10px; font-size: 0.95rem; color: #333; line-height: 1.6; text-align: justify; }
    .footer-tematico { margin-top: 40px; padding: 30px 0; text-align: center; opacity: 0.6; }
    </style>
""", unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")

@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        df = pd.read_excel(PATH_DATA)
        df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
        num_cols = ['Edad Sem.', 'Saldo de Aves', 'Mort', 'Suma Mort + Sel', '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 
                    'Bulto X 40 K', 'Gr.A.D Real', 'Gr.A.D Tabla', 'Peso Real', 'Peso Tab', 'Huevos  Semana', 
                    '% Pdn. Real', '% Pdn. Tabla', 'H.A.A. Real', 'H.A.A. Tabla', 'Costo Alimento Sem', '$ Huevo por alimento']
        for col in [c for c in num_cols if c in df.columns]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    return None

df_orig = load_data()

if df_orig is not None:
    st.markdown('<div class="main-title">📊 AUDITORÍA COMPARATIVA INTER-GRANJAS</div>', unsafe_allow_html=True)

    st.markdown("""
        <div style="background-color: #e3f2fd; padding: 25px; border-radius: 15px; border-left: 8px solid #0d47a1; margin-bottom: 25px;">
            <h4 style="color: #0d47a1; margin-top:0;">🔍 Protocolo de Benchmarking Competitivo</h4>
            <p style="font-size: 1rem; color: #1565c0;">
                Esta matriz permite la <b>fiscalización cruzada</b> de unidades productivas. El objetivo no es solo ver quién produce más, sino entender 
                qué combinación de <b>Genética + Nutrición + Manejo</b> está optimizando el costo por huevo producido. Analizamos la persistencia 
                de la curva y la resiliencia sanitaria (Viabilidad) para identificar las mejores prácticas transferibles a toda la operación.
            </p>
        </div>
    """, unsafe_allow_html=True)

    df_activos = df_orig[df_orig['LOTE'] == df_orig['NUM_GALPON']].copy()
    df_activos['ID_INTERNO'] = df_activos['GRANJA'] + " - Lote " + df_activos['LOTE'].astype(str)

    # --- 1. FILTROS MANDATORIOS ---
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        emp_list = sorted(df_activos['RAZON_SOCIAL'].unique())
        empresa_sel = st.multiselect("🏢 1. Seleccione Empresa:", emp_list)
    with c2:
        granja_list = sorted(df_activos[df_activos['RAZON_SOCIAL'].isin(empresa_sel)]['GRANJA'].unique()) if empresa_sel else []
        granja_sel = st.multiselect("🗺️ 2. Seleccione Granja(s):", granja_list)
    with c3:
        lote_list = sorted(df_activos[df_activos['GRANJA'].isin(granja_sel)]['LOTE'].unique()) if granja_sel else []
        lote_sel = st.multiselect("📦 3. Seleccione Lote(s):", lote_list)
    
    st.write("---")
    cx1, cx2 = st.columns(2)
    with cx1: ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas de datos", value=False)
    with cx2: ver_tabla_line = st.toggle("📉 Mostrar líneas de Tabla (Punteadas)", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not lote_sel:
        st.markdown('<div class="instruction-box">⚠️ ACCIÓN REQUERIDA: Seleccione Empresa, Granja y Lote para inicializar el motor de comparación.</div>', unsafe_allow_html=True)
    else:
        df_f = df_activos[df_activos['LOTE'].isin(lote_sel) & df_activos['GRANJA'].isin(granja_sel)].copy()
        
        with st.expander("🛠️ Ajustes de Auditoría (Genética, Nutrición y Edad)"):
            f1, f2, f3 = st.columns(3)
            with f1: linea_sel = st.multiselect("🧬 Genética:", sorted(df_f['LINEA_AVES'].unique()), default=df_f['LINEA_AVES'].unique())
            with f2: obs_sel = st.multiselect("🧪 Nutrición / Observaciones:", sorted(df_f['Observaciones'].dropna().unique()))
            with f3:
                min_e, max_e = int(df_f['Edad Sem.'].min()), int(df_f['Edad Sem.'].max())
                rango_edad = st.slider("⏳ Ventana de Edad:", min_e, max_e, (min_e, max_e))

        df_final = df_f[
            (df_f['LINEA_AVES'].isin(linea_sel)) & 
            (df_f['Edad Sem.'] >= rango_edad[0]) & (df_f['Edad Sem.'] <= rango_edad[1])
        ].copy()
        if obs_sel: df_final = df_final[df_final['Observaciones'].isin(obs_sel)]

        # Cálculos Redondeados (1 decimal)
        df_final['Dif Pdn'] = (df_final['% Pdn. Real'] - df_final['% Pdn. Tabla']).round(1)
        df_final['Dif GAD'] = (df_final['Gr.A.D Real'] - df_final['Gr.A.D Tabla']).round(1)
        df_final['Dif HAA'] = (df_final['H.A.A. Real'] - df_final['H.A.A. Tabla']).round(1)
        df_final['Dif Peso'] = (df_final['Peso Real'] - df_final['Peso Tab']).round(1)
        df_final['Dif Mort'] = (df_final['%Mort+Sel Acum. Tab'] - df_final['% Mort + Sel Acum.']).round(1)
        df_final['Conversión'] = ((df_final['Bulto X 40 K'] * 40000) / (df_final['Huevos  Semana'].replace(0,1))).round(1)

        def plot_hupa_comp(df, y_col, tab_col, title, unit, show_labels, show_table):
            fig = px.line(df.sort_values('Edad Sem.'), x='Edad Sem.', y=y_col, color='ID_INTERNO', 
                          markers=True, title=f"<b>{title}</b>")
            
            dif_map = {'% Pdn. Real': 'Dif Pdn', 'Gr.A.D Real': 'Dif GAD', 'H.A.A. Real': 'Dif HAA', 'Peso Real': 'Dif Peso', '% Mort + Sel Acum.': 'Dif Mort'}
            dif_col = dif_map.get(y_col)
            
            if show_table and tab_col:
                for lote_id in df['ID_INTERNO'].unique():
                    df_lote = df[df['ID_INTERNO'] == lote_id].sort_values('Edad Sem.')
                    fig.add_scatter(x=df_lote['Edad Sem.'], y=df_lote[tab_col], mode='lines', 
                                    line=dict(color='black', dash='dot', width=1), name=f"Tab {lote_id}", showlegend=False)

            if dif_col:
                htemp = "<b>%{customdata[2]}</b><br>Sem: %{x}<br>Real: %{y:.1f}" + unit + "<br>Tab: %{customdata[0]:.1f}" + unit + "<br>Dif: <b>%{customdata[1]:.1f}</b>" + unit + "<extra></extra>"
                cdata = np.stack((df[tab_col], df[dif_col], df['ID_INTERNO']), axis=-1)
            else:
                htemp = "<b>%{customdata}</b><br>Sem: %{x}<br>Val: %{y:.1f}" + unit + "<extra></extra>"
                cdata = df['ID_INTERNO']

            fig.update_traces(hovertemplate=htemp, customdata=cdata, mode="lines+markers+text" if show_labels else "lines+markers", 
                              texttemplate="%{y:.1f}", textposition="top center")
            fig.update_layout(title_x=0.5, height=450, legend=dict(orientation="h", y=-0.2), margin=dict(t=80, b=50), hovermode="x unified")
            return fig

        # --- FILA 1 ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1: 
            st.plotly_chart(plot_hupa_comp(df_final, '% Pdn. Real', '% Pdn. Tabla', "EFICIENCIA DE POSTURA (%)", "%", ver_etiquetas, ver_tabla_line), use_container_width=True)
            st.markdown('<div class="guide-box">Análisis de la persistencia de la curva. La línea punteada representa el estándar genético esperado para cada lote. Una caída prematura indica estrés ambiental o nutricional.</div>', unsafe_allow_html=True)
        with g2: 
            st.plotly_chart(plot_hupa_comp(df_final, 'Gr.A.D Real', 'Gr.A.D Tabla', "INTAKE DE ALIMENTO (G)", "g", ver_etiquetas, ver_tabla_line), use_container_width=True)
            st.markdown('<div class="guide-box">Comparativa del consumo real vs teórico. Vital para ajustar presupuestos de materia prima y detectar desperdicios o sub-alimentación.</div>', unsafe_allow_html=True)

        # --- FILA 2 ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g3, g4 = st.columns(2)
        with g3: 
            st.plotly_chart(plot_hupa_comp(df_final, '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', "VIABILIDAD ACUMULADA (%)", "%", ver_etiquetas, ver_tabla_line), use_container_width=True)
            st.markdown('<div class="guide-box">Indicador de resiliencia sanitaria. Evalúa la supervivencia del capital invertido. Desviaciones negativas son alertas tempranas de desafíos patológicos.</div>', unsafe_allow_html=True)
        with g4: 
            st.plotly_chart(plot_hupa_comp(df_final, 'Peso Real', 'Peso Tab', "DESARROLLO CORPORAL (G)", "g", ver_etiquetas, ver_tabla_line), use_container_width=True)
            st.markdown('<div class="guide-box">Control de uniformidad y crecimiento. Fundamental para asegurar la calidad de la cáscara y el tamaño del huevo en etapas avanzadas.</div>', unsafe_allow_html=True)

        # --- FILA 3 ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        g5, g6 = st.columns(2)
        with g5: 
            st.plotly_chart(plot_hupa_comp(df_final, 'H.A.A. Real', 'H.A.A. Tabla', "HUEVOS POR AVE ALOJADA", "", ver_etiquetas, ver_tabla_line), use_container_width=True)
            st.markdown('<div class="guide-box">Indicador de éxito biológico acumulado. Compara cuántos huevos ha "pagado" la gallina respecto al potencial genético total de la estirpe.</div>', unsafe_allow_html=True)
        with g6: 
            fig_conv = px.line(df_final.sort_values('Edad Sem.'), x='Edad Sem.', y='Conversión', color='ID_INTERNO', markers=True, title="<b>CONVERSIÓN (G/HUEVO)</b>")
            fig_conv.update_traces(hovertemplate="<b>%{customdata}</b><br>Sem: %{x}<br>Valor: %{y:.1f}g<extra></extra>", customdata=df_final['ID_INTERNO'], mode="lines+markers+text" if ver_etiquetas else "lines+markers", texttemplate="%{y:.1f}")
            fig_conv.update_layout(title_x=0.5, height=450, legend=dict(orientation="h", y=-0.2), hovermode="x unified")
            st.plotly_chart(fig_conv, use_container_width=True)
            st.markdown('<div class="guide-box">¿Cuánto alimento cuesta fabricar un huevo? Este es el indicador financiero puro. Menor valor equivale a un mayor margen operativo por caja vendida.</div>', unsafe_allow_html=True)

        # --- MATRIZ MAESTRA 24 COLUMNAS ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        st.markdown("### 📋 Matriz de Auditoría Detallada")
        
        ids_activos = sorted(df_final['ID_INTERNO'].unique())
        tabs = st.tabs([f"📍 {nombre}" for nombre in ids_activos])

        cols_maestras = [
            'GRANJA', 'LINEA_AVES', 'LOTE', 'Final Sem', 'Edad Sem.', 
            'Saldo de Aves', 'Mort', 'Suma Mort + Sel', 
            '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort', 'Observaciones', 
            'Bulto X 40 K', 'Costo Alimento Sem', '$ Huevo por alimento',
            'Gr.A.D Real', 'Gr.A.D Tabla', 'Dif GAD', '% Unif', 
            'Peso Real', 'Peso Tab', 'Dif Peso', 'Huevos  Semana',
            '% Pdn. Real', '% Pdn. Tabla', 'Dif Pdn',
            'H.A.A. Real', 'H.A.A. Tabla', 'Dif HAA'
        ]

        for i, tab in enumerate(tabs):
            with tab:
                df_tab = df_final[df_final['ID_INTERNO'] == ids_activos[i]].sort_values('Edad Sem.', ascending=False)
                c_finales = [c for c in cols_maestras if c in df_tab.columns]
                user = st.session_state.get('user', 'VET_HUPA')
                if user == "VET_HUPA":
                    c_finales = [c for c in c_finales if c not in ['Costo Alimento Sem', '$ Huevo por alimento']]
                
                if 'Final Sem' in df_tab.columns: 
                    df_tab['Final Sem'] = pd.to_datetime(df_tab['Final Sem']).dt.strftime('%d/%m/%y')
                
                st.dataframe(df_tab[c_finales].style.format({
                    'Saldo de Aves': '{:,.0f}', 'Huevos  Semana': '{:,.0f}', 'Edad Sem.': '{:.0f}', 
                    'Gr.A.D Real': '{:.1f}', 'Gr.A.D Tabla': '{:.1f}', 'Peso Real': '{:.1f}', 'Peso Tab': '{:.1f}', 
                    '% Pdn. Real': '{:.1f}%', '% Pdn. Tabla': '{:.1f}%', 'H.A.A. Real': '{:.1f}', 'H.A.A. Tabla': '{:.1f}',
                    '% Mort + Sel Acum.': '{:.1f}%', '%Mort+Sel Acum. Tab': '{:.1f}%', 'Bulto X 40 K': '{:.1f}',
                    'Dif Pdn': '{:+.1f}%', 'Dif GAD': '{:+.1f}', 'Dif HAA': '{:+.1f}', 'Dif Peso': '{:+.1f}', 'Dif Mort': '{:+.1f}%',
                    'Costo Alimento Sem': '${:,.0f}', '$ Huevo por alimento': '${:,.1f}'
                }).applymap(lambda val: f'color: {"#27ae60" if val > 0 else "#e74c3c" if val < 0 else "#636e72"}; font-weight: bold', 
                            subset=[c for c in ['Dif Pdn', 'Dif GAD', 'Dif HAA', 'Dif Peso', 'Dif Mort'] if c in df_tab.columns]),
                    use_container_width=True, hide_index=True)

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
                <span style="font-size: 0.8rem;">© 2026</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

else:
    st.error("Archivo no encontrado.")