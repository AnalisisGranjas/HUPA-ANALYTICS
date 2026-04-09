import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime
import io
from fpdf import FPDF 

# --- 1. TU LISTA MAESTRA (La que me pasaste en la imagen) ---
cols_base = [
    'GRANJA', 'LINEA_AVES', 'LOTE', 'Final Sem', 'Edad Sem.',
    'Saldo de Aves', 'Mort', 'Suma Mort + Sel',
    '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort', 'Fase de Alimento', 'Observaciones',
    'Bulto X 40 K', 'Costo Alimento Sem', '$ Huevo por alimento',
    'Gr.A.D Real', 'Gr.A.D Tabla', 'Dif GAD', '% Unif',
    'Peso Real', 'Peso Tab', 'Dif Peso', 'Huevos Semana',
    '% Pdn. Real', '% Pdn. Tabla', 'Dif Pdn',
    'H.A.A. Real', 'H.A.A. Tabla', 'Dif HAA'
]

def registrar_log(accion):
    ahora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    with open("registro_descargas.txt", "a", encoding="utf-8") as f:
        f.write(f"[{ahora}] {accion}\n")

def crear_excel(df_formateado):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_formateado.to_excel(writer, index=False, sheet_name='Reporte_HUPA')
    return output.getvalue()

def crear_pdf(df_formateado):
    # 'A2' es el secreto para que las 30 columnas respiren
    pdf = FPDF(orientation='L', unit='mm', format=(420,594))
    pdf.add_page()
    
    # Título elegante
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 20, "REPORTE DETALLADO DE PRODUCCIÓN - HUPA", ln=True, align='C')
    pdf.ln(10)
    
    cols = df_formateado.columns.tolist()
    
    pdf.set_font("Arial", 'B', 8)
    pdf.set_fill_color(26, 35, 126) 
    pdf.set_text_color(255, 255, 255)

    ancho_col = 575 / len(cols)
    
    for col in cols:
        pdf.cell(ancho_col, 12, str(col), 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Arial", '', 8)
    pdf.set_text_color(0, 0, 0)
    
    for i in range(min(len(df_formateado), 100)): # Subimos a 100 filas, la A2 aguanta
        for col in cols:
            valor = str(df_formateado.iloc[i][col])
            pdf.cell(ancho_col, 10, valor, 1, 0, 'C')
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1', 'ignore')

# --- 1. SEGURIDAD Y SESIÓN ---
if 'auth' not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

# --- 2. CONFIGURACIÓN Y CSS ---
st.set_page_config(page_title="HUPA | Dashboard Operativo", layout="wide")

st.markdown("""
    <style>
    .main-title { text-align:center; color:#ffffff; background: linear-gradient(90deg, #1a237e, #0d47a1); padding: 20px; border-radius: 15px; margin-bottom: 20px; font-weight: bold; font-size: clamp(1.5rem, 3vw, 2.5rem); box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
    .info-box { background-color: #f8f9fa; border-left: 6px solid #1a237e; padding: 20px; margin-bottom: 25px; border-radius: 0 10px 10px 0; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    .info-box h4 { color: #1a237e; margin-top: 0; }
    .info-box p { text-align: justify; font-size: 0.95rem; line-height: 1.5; color: #333; }
/* --- REEMPLAZO DESDE LÍNEA 79 A 87 --- */
    .card-design { 
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
    }

    /* Efecto de Brillo de Cristal */
    .card-design::after {
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

    .card-design:hover::after { left: 120%; }

    .card-design:hover { 
        transform: translateY(-10px); 
        filter: brightness(1.2); 
        box-shadow: 0 15px 30px rgba(0,0,0,0.3);
    }

    /* Degradados Actualizados */
    .card-total { background: linear-gradient(135deg, #1e3a8a, #3b82f6); } 
    .card-lotes { background: linear-gradient(135deg, #f59e0b, #fbbf24); } 
    .card-edad  { background: linear-gradient(135deg, #059669, #34d399); } 
    .card-prod  { background: linear-gradient(135deg, #7c3aed, #a78bfa); }
    .card-mort  { background: linear-gradient(135deg, #b91c1c, #ef4444); }

    .val-num { 
        font-size: clamp(1.6rem, 2vw, 2.3rem); 
        font-weight: 800; 
        display: block; 
        text-shadow: 2px 2px 8px rgba(0,0,0,0.4);
        line-height: 1;
        margin-top: 5px;
    }

    .label-card { 
        font-size: clamp(0.9rem, 1.1vw, 1.2rem);
        font-weight: 800;
        text-transform: uppercase; 
        letter-spacing: 1.5px;
        opacity: 1;
        margin-bottom: 5px;
    }
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
    # --- BLOQUE INTRODUCTORIO ESTRATÉGICO: ESTADO OPERATIVO ---
    st.markdown("""
        <div style="background-color: #e3f2fd; padding: 30px; border-radius: 15px; border-left: 10px solid #0d47a1; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
            <h3 style="color: #0d47a1; margin-top:0; text-align:center;"> BALANCE TÁCTICO: INFORME SEMANAL </h3>
            <p style="text-align: justify; font-size: 1.1rem; line-height: 1.7; color: #1a237e;">
                Bienvenido a la <b>Torre de Control HUPA</b>. Esta interfaz presenta el consolidado del desempeño biológico y operativo al cierre de la última semana técnica. Aquí, la complejidad de la producción se traduce en una visión ejecutiva diseñada para auditar la salud del negocio y la consistencia del manejo en todas sus granjas.<br><br>
                El objetivo primordial es evaluar el <b>Estado Operativo Actual</b> de cada lote, contrastando sus resultados reales frente a las proyecciones y metas genéticas. Este tablero le permite identificar brechas críticas de rendimiento de manera inmediata, facilitando una gestión basada en datos que asegura la estabilidad de la operación y la optimización de los recursos en cada granja.
            </p>
        </div>
    """, unsafe_allow_html=True)
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
    col1, col2, col3, col4, col5 = st.columns(5)
    # Busca esta parte más abajo en tu código y reemplaza:
    col1.markdown(f'''<div class="card-design card-total"><span class="label-card">🐔 Aves Totales</span><span class="val-num">{df_ultimos["Saldo de Aves"].sum():,.0f}</span></div>''', unsafe_allow_html=True)
    col2.markdown(f'''<div class="card-design card-lotes"><span class="label-card">📦 Lotes Activos</span><span class="val-num">{len(df_ultimos)}</span></div>''', unsafe_allow_html=True)
    col3.markdown(f'''<div class="card-design card-edad"><span class="label-card">⌛Edad Media</span><span class="val-num">{df_ultimos["Edad Sem."].mean():.1f} <small style="font-size:1rem">Sem</small></span></div>''', unsafe_allow_html=True)
    col4.markdown(f'''<div class="card-design card-prod"><span class="label-card">🥚 Postura Prom.</span><span class="val-num">{df_ultimos["% Pdn. Real"].mean():.1f}%</span></div>''', unsafe_allow_html=True)
    col5.markdown(f'''<div class="card-design card-mort"><span class="label-card">💀 Mortalidad</span><span class="val-num">{df_ultimos["% Mort + Sel Acum."].mean():.1f}%</span></div>''', unsafe_allow_html=True)

    # --- E. GRÁFICOS DE DISTRIBUCIÓN (VERSIÓN LIMPIA Y PROFESIONAL) ---
    st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
    st.markdown("### ℹ️ Graficos de Distribucion")
    # CSS minimalista: Solo para los títulos azules
    st.markdown("""
        <style>
        .plot-title-clean {
            text-align: center;
            color: var(--text-color,#31333F)
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 5px; /* Acerca el título al gráfico */
        }
        </style>
    """, unsafe_allow_html=True)

    cg1, cg2, cg3 = st.columns(3)

    # Función de configuración rápida para los gráficos
    def clean_fig(fig):

        fig.update_traces(textposition='inside', textinfo='percent+label', textfont_size=12)
        fig.update_layout(
            margin=dict(t=30, b=0, l=0, r=0),
            height=350, # Altura ideal para que no ocupe toda la pantalla
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return fig
  
    with cg1:
        st.markdown('<p class="plot-title-clean">🗺️ Por Granja</p>', unsafe_allow_html=True)
        fig1 = px.pie(df_ultimos, values='Saldo de Aves', names='GRANJA', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(clean_fig(fig1), use_container_width=True, config={'displayModeBar': False})

    with cg2:
        st.markdown('<p class="plot-title-clean">🧬 Por Genética</p>', unsafe_allow_html=True)
        fig2 = px.pie(df_ultimos, values='Saldo de Aves', names='LINEA_AVES', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(clean_fig(fig2), use_container_width=True, config={'displayModeBar': False})

    with cg3:
        st.markdown('<p class="plot-title-clean">🥣 Por Fase Alimento</p>', unsafe_allow_html=True)
        fig3 = px.pie(df_ultimos, values='Saldo de Aves', names='Fase de Alimento', hole=0.4, 
                     color_discrete_sequence=px.colors.qualitative.Bold)
        st.plotly_chart(clean_fig(fig3), use_container_width=True, config={'displayModeBar': False})

    st.markdown('<div class="hr-custom" style="margin-top: 20px; margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
    st.markdown("### 📋 Resumen Detallado de Producción")

    # Una pequeña línea divisoria para separar de los gráficos
    st.markdown('<div class="hr-custom" style="margin: 20px 0;"></div>', unsafe_allow_html=True)

    # --- LÓGICA DE LA TABLA (Sin mostrar nada todavía) ---
    cols_base = ['GRANJA', 'LINEA_AVES', 'LOTE', 'Final Sem', 'Edad Sem.', 
             'Saldo de Aves', 'Mort', 'Suma Mort + Sel', 
             '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort', 'Fase de Alimento', 'Observaciones', 
             'Bulto X 40 K', 'Costo Alimento Sem', '$ Huevo por alimento',
             'Gr.A.D Real', 'Gr.A.D Tabla', 'Dif GAD', '% Unif', 
             'Peso Real', 'Peso Tab', 'Dif Peso', 'Huevos Semana',
             '% Pdn. Real', '% Pdn. Tabla', 'Dif Pdn',
             'H.A.A. Real', 'H.A.A. Tabla', 'Dif HAA'] # Tu lista de la imagen

    if usuario_actual == "VET_HUPA":
        lista_negra = ['Costo Alimento Sem', '$ Huevo por alimento']
        cols_finales = [c for c in cols_base if c not in lista_negra]
    else:
        cols_finales = cols_base

    cols_disponibles = [c for c in cols_finales if c in df_ultimos.columns]
    tabla_final = df_ultimos[cols_disponibles].sort_values('Edad Sem.', ascending=False).copy()

    formatos = { 'Saldo de Aves': '{:,.0f}', 'Huevos  Semana': '{:,.0f}',
        'Edad Sem.': '{:.0f}', 'Mort': '{:.0f}', 'Suma Mort + Sel': '{:.1f}',
        '% Mort + Sel Acum.': '{:.1f}%', '%Mort+Sel Acum. Tab': '{:.1f}%', 'Bulto X 40 K': '{:.1f}',
        'Gr.A.D Real': '{:.1f}', 'Gr.A.D Tabla': '{:.1f}', '% Unif': '{:.1f}%',
        'Peso Real': '{:.1f}', 'Peso Tab': '{:.1f}', '% Pdn. Real': '{:.1f}%',
        '% Pdn. Tabla': '{:.1f}%', 'H.A.A. Real': '{:.1f}', 'H.A.A. Tabla': '{:.1f}',
        'Costo Alimento Sem': '${:,.0f}', '$ Huevo por alimento': '${:,.1f}',
        'Dif Pdn': '{:+.1f}%', 'Dif GAD': '{:+.1f}', 'Dif HAA': '{:+.1f}', 'Dif Peso': '{:+.1f}', 'Dif Mort': '{:+.1f}%' } # Tu dict de formatos
    
    formatos_activos = {k: v for k, v in formatos.items() if k in tabla_final.columns}

    # --- SECCIÓN DE EXPORTACIÓN LIMPIA ---
    with st.expander("📥 Exportar esta Tabla (Excel / PDF)"):
        c1, c2 = st.columns(2)
        with c1:
            nombre_persona = st.text_input("Tu nombre para el registro", key="input_descarga")
        with c2:
            opcion = st.radio("Formato de archivo:", ["Excel", "PDF"], horizontal=True)

        # --- ESTA ES LA PARTE ESTILO EXCEL (POPOVER) ---
        with st.popover("⚙️ Seleccionar Columnas"):
            st.write("Marca las columnas que deseas incluir:")
            # Creamos un diccionario de checkboxes para que se vea como Excel
            seleccionadas = {}
            for col in cols_disponibles:
                # Por defecto todas en True (marcadas)
                seleccionadas[col] = st.checkbox(col, value=True, key=f"check_{col}")
    
        # Filtramos las columnas que el usuario dejó marcadas en el popover
        cols_a_incluir = [col for col, marcado in seleccionadas.items() if marcado]

        if nombre_persona:
            if not cols_a_incluir:
                st.error("⚠️ Selecciona al menos una columna.")
            else:
                # 1. Filtramos la tabla con la selección del Popover
                df_espejo = tabla_final[cols_a_incluir].copy()
            
                # --- AJUSTE MAESTRO PARA LA FECHA ---
            if 'Final Sem' in df_espejo.columns:
                # Convertimos a fecha y formateamos a DD/MM/AA directamente
                df_espejo['Final Sem'] = pd.to_datetime(df_espejo['Final Sem']).dt.strftime('%d/%m/%y')
                # 2. Aplicamos formatos (decimales, %, $)
                for col, fmt in formatos_activos.items():
                    if col in df_espejo.columns:
                        df_espejo[col] = df_espejo[col].apply(
                            lambda x: fmt.format(x) if pd.notnull(x) else ""
                        )

                # 3. Generación y Botón (igual que antes)
                try:
                    if opcion == "Excel":
                        archivo_bytes = crear_excel(df_espejo)
                        ext, mime = "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    else:
                        archivo_bytes = crear_pdf(df_espejo)
                        ext, mime = "pdf", "application/pdf"

                    st.download_button(
                        label=f"📥 Descargar {len(cols_a_incluir)} columnas",
                        data=archivo_bytes,
                        file_name=f"HUPA_Reporte_{nombre_persona}.{ext}",
                        mime=mime,
                        on_click=registrar_log,
                        args=(f"Usuario '{nombre_persona}' descargó {opcion}",)
                    )
                except Exception as e:
                    st.error(f"Error: {e}")
            
        else:
            # Este else debe estar alineado con el 'if nombre_persona' de arriba
            st.warning("⚠️ Por favor, ingresa tu nombre para habilitar los botones de descarga.")             
 
    
    cols_base = [
        'GRANJA', 'LINEA_AVES', 'LOTE', 'Final Sem', 'Edad Sem.', 
        'Saldo de Aves', 'Mort', 'Suma Mort + Sel', 
        '% Mort + Sel Acum.', '%Mort+Sel Acum. Tab', 'Dif Mort', 'Fase de Alimento', 'Observaciones', 
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
        .map(color_diferencia, subset=[c for c in ['Dif Pdn', 'Dif GAD', 'Dif HAA', 'Dif Peso', 'Dif Mort'] if c in tabla_final.columns]),
        use_container_width=True, hide_index=True
    )

    # --- G. FOOTER ---
    st.divider()
    st.markdown("""
        <div class='footer-tematico'>
            <div class='footer-pattern'>🐔 🥚 🐔 🥚 🐔 🥚</div>
            <div class='footer-text'>
                <b>HUPA | División Avícola</b><br>
                Análisis de Datos para la Excelencia Productiva<br>
                C.A<b><br>
                <span style="font-size: 0.8rem;">© 2026</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.error("No se pudo cargar el archivo.")