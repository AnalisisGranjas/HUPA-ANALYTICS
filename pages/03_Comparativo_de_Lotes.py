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
st.set_page_config(page_title="HUPA | Comparativo de Lotes", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align:center; color:#ffffff; background-color: #1a237e; padding: 15px; border-radius: 15px; margin-bottom: 20px; font-weight: bold; font-size: 1.8rem; }
    .filter-box { background-color: #f8f9fa; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #e6e9ef; }
    .hr-custom { border: 0; height: 4px; background-color: #1a237e; margin: 35px 0; opacity: 0.7; }
    .section-header { color: #1a237e; font-weight: bold; font-size: 1.5rem; margin-bottom: 15px; border-left: 6px solid #1a237e; padding-left: 15px; }
    .guide-box { background-color: #ffffff; padding: 15px; border: 1px dashed #1a237e; border-radius: 10px; margin-top: 10px; font-size: 0.95rem; color: #333; line-height: 1.6; text-align: justify; }
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
            if 'Observaciones' in df.columns:
                df['Observaciones'] = df['Observaciones'].astype(str).replace('nan', 'Sin especificar')
            
            num_cols = ['Edad Sem.', 'Saldo de Aves', 'Mort', 'Suma Mort + Sel', '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 
                        'Bulto X 40 K', 'Gr.A.D Real', 'Gr.A.D Tabla', 'Peso Real', 'Peso Tab', 'Huevos  Semana', 
                        '% Pdn. Real', '% Pdn. Tabla', 'H.A.A. Real', 'H.A.A. Tabla', 'Jumbo', 'Extra', 'AA', 'A', 'B', 'C', 
                        'Alt Cáscara', 'Alt. Color', 'Picado', 'Roto', 'Costo Alimento Sem', '$ Huevo por alimento', '% Unif']
            for col in [c for c in num_cols if c in df.columns]:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            return None
    return None

df_orig = load_data()

if df_orig is not None:
    st.markdown('<div class="main-title">📊 COMPARATIVO DE DESEMPEÑO ENTRE LOTES</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #f0f7ff; padding: 30px; border-radius: 20px; border-left: 12px solid #0d47a1; margin-bottom: 30px; box-shadow: 0 6px 15px rgba(0,0,0,0.07); width: 100%; box-sizing: border-box;">
        <p style="text-align: justify; font-size: 1.15rem; line-height: 1.8; color: #1a237e; margin-bottom: 20px;">
            <b style="font-size: 1.25rem;">¿Por qué implementamos este análisis comparativo?</b><br>
            En la producción avícola industrial, el rendimiento aislado de un lote puede ser engañoso. La verdadera eficiencia se mide a través del <b>Benchmarking Operativo</b>, el cual nos permite contrastar el desempeño biológico de diferentes granjas, edades y genéticas bajo un mismo prisma técnico. Este análisis es fundamental para identificar si las variaciones de postura son intrínsecas a la edad del lote o si obedecen a deficiencias en la estandarización de los procesos operativos entre granjas.
        </p>
        <div style="margin-top: 25px; padding: 25px; background-color: rgba(255,255,255,0.6); border-radius: 15px; border: 1px solid #bbdefb;">
            <p style="text-align: justify; font-size: 1.05rem; line-height: 1.8; color: #1a237e; margin: 0;">
                <b style="font-size: 1.15rem;">¿Cómo y Cuándo utilizar esta herramienta para la toma de decisiones?</b><br>
                Al cruzar las curvas de producción reales contra la <b>Meta Genética Ideal</b>, estamos estableciendo un marco de referencia absoluto.<br><br>
                • <b>Detección de Brechas:</b> Si múltiples lotes muestran quiebres productivos en la misma semana cronológica, el problema es externo (clima, calidad de insumos o desafío sanitario zonal).<br>
                • <b>Auditoría de Manejo:</b> Si un lote específico se desvía de la meta mientras sus pares mantienen la consistencia, la causa es operativa (iluminación deficiente, horarios de alimentacion, disposicion de alimento en comederos, disposicion de aguas optimas o manejo de galpones en esa granja).<br>
                • <b>Optimización de Recursos:</b> Este comparativo permite identificar qué granja está logrando la mayor eficiencia biológica para replicar sus protocolos exitosos en el resto de la infraestructura, garantizando que el éxito sea una norma operativa y no una casualidad biológica.
            </p>
        </div>
    </div>
""", unsafe_allow_html=True)

    df_activos = df_orig[df_orig['LOTE'] == df_orig['NUM_GALPON']].copy()
    df_activos['ID_INTERNO'] = df_activos['GRANJA'] + " - Lote " + df_activos['LOTE'].astype(str)

    # --- FILTROS ---
    st.markdown('<div class="filter-box">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: empresa_sel = st.multiselect("🏢 1. Empresa:", sorted(df_activos['RAZON_SOCIAL'].unique()))
    with c2:
        df_g = df_activos[df_activos['RAZON_SOCIAL'].isin(empresa_sel)] if empresa_sel else df_activos
        granja_sel = st.multiselect("🗺️ 2. Granja(s):", sorted(df_g['GRANJA'].unique()))
    with c3:
        df_l = df_g[df_g['GRANJA'].isin(granja_sel)] if granja_sel else df_g
        lote_sel = st.multiselect("📦 3. Lote(s):", sorted(df_l['LOTE'].unique()))
    with c4:
        opciones_casa = sorted(df_l['Observaciones'].unique()) if not df_l.empty else []
        casa_sel = st.multiselect("🌽 4. Casa Nutricional:", opciones_casa)
    
    st.write("---")
    cx1, cx2 = st.columns(2)
    with cx1: ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas de datos", value=False)
    with cx2: ver_tabla_line = st.toggle("📉 Mostrar la linea de Tabla", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not lote_sel:
        st.info("💡 Selecciona los lotes en los filtros de arriba para empezar el análisis.")
    else:
        df_f = df_l[df_l['LOTE'].isin(lote_sel)].copy()
        if casa_sel:
            df_f = df_f[df_f['Observaciones'].isin(casa_sel)]
        
        with st.expander("🛠️ Ajustes Avanzados"):
            fa1, fa2 = st.columns(2)
            with fa1:
                genetica_sel = st.multiselect("🧬 Linea Genetica:", sorted(df_f['LINEA_AVES'].unique()), default=df_f['LINEA_AVES'].unique())
            with fa2:
                min_e, max_e = int(df_f['Edad Sem.'].min()), int(df_f['Edad Sem.'].max())
                rango_edad = st.slider("⏳ Rango de Edad (Semanas):", min_e, max_e, (max(min_e, max_e-4), max_e))
        
        df_final = df_f[(df_f['LINEA_AVES'].isin(genetica_sel)) & (df_f['Edad Sem.'].between(rango_edad[0], rango_edad[1]))].copy()

        # Cálculos Comerciales
        df_final['Grande'] = (df_final['Jumbo'] + df_final['Extra'] + df_final['AA']) * 100
        df_final['Mediano'] = (df_final['A']) * 100
        df_final['Pequeño'] = (df_final['B'] + df_final['C']) * 100
        df_final['Segunda'] = (df_final['Alt Cáscara'] + df_final['Alt. Color'] + df_final['Picado'] + df_final['Roto']) * 100
        
        df_final['Dif Pdn'] = df_final['% Pdn. Real'] - df_final['% Pdn. Tabla']
        df_final['Dif GAD'] = df_final['Gr.A.D Real'] - df_final['Gr.A.D Tabla']
        df_final['Dif HAA'] = df_final['H.A.A. Real'] - df_final['H.A.A. Tabla']
        df_final['Dif Mort'] = df_final['%Mort+Sel Acum. Tab'] - df_final['% Mort + Sel Acum.']
        df_final['Dif Peso'] = df_final['Peso Real'] - df_final['Peso Tab']

        df_graf = df_final.copy()
        for c in ['Grande', 'Mediano', 'Pequeño', 'Segunda', '% Pdn. Real', 'Gr.A.D Real', 'Peso Real', 'H.A.A. Real']:
            df_graf[c] = df_graf[c].replace(0, np.nan)

        def plot_hupa(df, y_col, tab_col, title, unit, show_labels, show_table):
            df_plot = df.sort_values(['ID_INTERNO', 'Edad Sem.'])
            fig = px.line(df_plot, x='Edad Sem.', y=y_col, color='ID_INTERNO', markers=True, title=f"<b>{title}</b>")
            
            if show_table and tab_col:
                df_tab = df.groupby('Edad Sem.')[tab_col].mean().reset_index()
                fig.add_scatter(x=df_tab['Edad Sem.'], y=df_tab[tab_col], mode='lines', 
                                line=dict(color='black', dash='dot', width=2), name='Meta Ideal')
            
            # Tooltip 1 decimal para todos
            fig.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Semana: %{x}<br>Valor: %{y:.1f}" + unit + "<extra></extra>")
            
            fig.update_layout(title_x=0.5, height=420, legend=dict(orientation="h", y=-0.25), hovermode="x unified")
            fig.update_traces(mode="lines+markers+text" if show_labels else "lines+markers", 
                              texttemplate="%{y:.1f}", textposition="top center")
            return fig

        # --- SECCIONES GRÁFICOS ---
        st.markdown('<div class="section-header">💹 ¿CÓMO SE DISTRIBUYE EL TAMAÑO DE TU HUEVO?</div>', unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.plotly_chart(plot_hupa(df_graf, 'Grande', None, "💎 HUEVO GRANDE (Jum/Ext/AA) %", "%", ver_etiquetas, False), use_container_width=True)
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Huevos de mayor tamaño y valor comercial. Si esta línea sube, mejora el ingreso por huevo.</div>', unsafe_allow_html=True)
        with g2:
            st.plotly_chart(plot_hupa(df_graf, 'Mediano', None, "🥚 HUEVO MEDIANO (A) %", "%", ver_etiquetas, False), use_container_width=True)
            st.markdown('<div class="guide-box"><b>Observaciones:</b> El tamaño estándar de mercado. Predomina al inicio del ciclo productivo.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        
        g3, g4 = st.columns(2)
        with g3:
            st.plotly_chart(plot_hupa(df_graf, 'Pequeño', None, "🐣 HUEVO PEQUEÑO (B/C) %", "%", ver_etiquetas, False), use_container_width=True)
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Huevos pequeños. Si persiste en aves adultas, indica problemas de peso o nutrición.</div>', unsafe_allow_html=True)
        with g4:
            st.plotly_chart(plot_hupa(df_graf, 'Segunda', None, "⚠️ HUEVO DE SEGUNDA %", "%", ver_etiquetas, False), use_container_width=True)
            st.markdown('<div class="guide-box"><b>Observaciones:</b> Merma (roto, picado, sucio). Debe estar lo más cerca posible de 0%.</div>', unsafe_allow_html=True)

        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">🥚 INDICADORES TECNICOS</div>', unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            st.plotly_chart(plot_hupa(df_graf, '% Pdn. Real', '% Pdn. Tabla', "📈 PRODUCCIÓN (%)", "%", ver_etiquetas, ver_tabla_line), use_container_width=True)
        with b2:
            st.plotly_chart(plot_hupa(df_graf, 'Gr.A.D Real', 'Gr.A.D Tabla', "🥣 CONSUMO DE ALIMENTO", "g", ver_etiquetas, ver_tabla_line), use_container_width=True)
        
        st.markdown('---')
        b3, b4 = st.columns(2)
        with b3:
            st.plotly_chart(plot_hupa(df_graf, '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', "🛡️ MORTALIDAD ACUMULADA", "%", ver_etiquetas, ver_tabla_line), use_container_width=True)
        with b4:
            st.plotly_chart(plot_hupa(df_graf, 'Peso Real', 'Peso Tab', "⚖️ PESO CORPORAL DE LA GALLINA", "g", ver_etiquetas, ver_tabla_line), use_container_width=True)

        # --- 📋 MATRIZ INTEGRAL DE AUDITORÍA CON SEGURIDAD ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📋 MATRIZ INTEGRAL DE AUDITORÍA</div>', unsafe_allow_html=True)
        
        ids = sorted(df_final['ID_INTERNO'].unique())
        tabs = st.tabs([f"📍 {n}" for n in ids])

        cols_base = [
            'GRANJA', 'LOTE', 'Final Sem', 'Edad Sem.', 
            'Saldo de Aves', 'Mort', '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort', 'Observaciones', 
            'Gr.A.D Real', 'Gr.A.D Tabla', 'Dif GAD', '% Unif', 
            'Peso Real', 'Peso Tab', 'Dif Peso', 'Huevos  Semana',
            '% Pdn. Real', '% Pdn. Tabla', 'Dif Pdn',
            'H.A.A. Real', 'H.A.A. Tabla', 'Dif HAA', 'Grande', 'Mediano', 'Pequeño', 'Segunda',
            'Costo Alimento Sem', '$ Huevo por alimento'
        ]

        usuario_actual = st.session_state.get('user', 'VET_HUPA')

        for i, tab in enumerate(tabs):
            with tab:
                df_tab = df_final[df_final['ID_INTERNO'] == ids[i]].copy()
                
                # RESTRICCIÓN DE SEGURIDAD
                if usuario_actual == "VET_HUPA":
                    lista_negra = ['Costo Alimento Sem', '$ Huevo por alimento']
                    cols_finales = [c for c in cols_base if c not in lista_negra]
                else:
                    cols_finales = cols_base

                cols_disp = [c for c in cols_finales if c in df_tab.columns]
                tabla_render = df_tab[cols_disp].sort_values('Edad Sem.', ascending=False).fillna(0).copy()

                if 'Final Sem' in tabla_render.columns:
                    tabla_render['Final Sem'] = pd.to_datetime(tabla_render['Final Sem']).dt.strftime('%d/%m/%y')

                formatos = {
                    'Saldo de Aves': '{:,.0f}', 'Huevos  Semana': '{:,.0f}',
                    'Edad Sem.': '{:.1f}', 'Mort': '{:.0f}',
                    '% Mort + Sel Acum.': '{:.1f}%', '%Mort+Sel Acum. Tab': '{:.1f}%',
                    'Gr.A.D Real': '{:.1f}', 'Gr.A.D Tabla': '{:.1f}', '% Unif': '{:.1f}%',
                    'Peso Real': '{:.1f}', 'Peso Tab': '{:.1f}', '% Pdn. Real': '{:.1f}%',
                    '% Pdn. Tabla': '{:.1f}%', 'H.A.A. Real': '{:.1f}', 'H.A.A. Tabla': '{:.1f}',
                    'Grande': '{:.1f}%', 'Mediano': '{:.1f}%', 'Pequeño': '{:.1f}%', 'Segunda': '{:.1f}%',
                    'Dif Pdn': '{:+.1f}%', 'Dif GAD': '{:+.1f}', 'Dif HAA': '{:+.1f}', 'Dif Peso': '{:+.1f}', 'Dif Mort': '{:+.1f}%',
                    
                    'Costo Alimento Sem': '${:,.1f}', 
                    '$ Huevo por alimento': '${:,.1f}'
                }
                
                def style_dif(val):
                    color = '#27ae60' if val > 0 else '#e74c3c' if val < 0 else '#636e72'
                    return f'color: {color}; font-weight: bold;'

                formatos_activos = {k: v for k, v in formatos.items() if k in tabla_render.columns}
                cols_estilo = [c for c in ['Dif Pdn', 'Dif GAD', 'Dif HAA', 'Dif Peso', 'Dif Mort'] if c in tabla_render.columns]

                st.dataframe(
                    tabla_render.style.format(formatos_activos)
                    .applymap(style_dif, subset=cols_estilo),
                    use_container_width=True, hide_index=True
                )

    # --- G. FOOTER TEMÁTICO
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
else:
    st.error("Archivo no encontrado en DATA/Consolidado_Produccion_FINAL.xlsx")