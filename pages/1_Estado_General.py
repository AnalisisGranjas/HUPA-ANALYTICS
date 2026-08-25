import base64
import datetime
import io
import os
from fpdf import FPDF
import pandas as pd
import plotly.express as px
import streamlit as st

# --- 1. CONFIGURACIÓN DE PÁGINA Y FORMATOS GLOBALES ---
st.set_page_config(
    page_title="HUPA | Estado General de Operación",
    page_icon="🥚",
    layout="wide",
    initial_sidebar_state="expanded",
)

cols_base = [
    "GRANJA",
    "LINEA_AVES",
    "LOTE",
    "GALPON",
    "Final Sem",
    "Edad Sem.",
    "Saldo de Aves",
    "Mort",
    "Suma Mort + Sel",
    "% Mort + Sel Acum.",
    "%Mort+Sel Acum. Tab",
    "Dif Mort",
    "Fase de Alimento",
    "Observaciones",
    "Bulto X 40 K",
    "Costo Alimento Sem",
    "$ Huevo por alimento",
    "Gr.A.D Real",
    "Gr.A.D Tabla",
    "Dif GAD",
    "% Unif",
    "Peso Real",
    "Peso Tab",
    "Dif Peso",
    "Huevos  Semana",
    "% Pdn. Real",
    "% Pdn. Tabla",
    "Dif Pdn",
    "H.A.A. Real",
    "H.A.A. Tabla",
    "Dif HAA",
]

formatos = {
    "Saldo de Aves": "{:,.0f}",
    "Huevos  Semana": "{:,.0f}",
    "Edad Sem.": "{:.0f}",
    "Mort": "{:.0f}",
    "Suma Mort + Sel": "{:.1f}",
    "% Mort + Sel Acum.": "{:.1f}%",
    "%Mort+Sel Acum. Tab": "{:.1f}%",
    "Bulto X 40 K": "{:.1f}",
    "Gr.A.D Real": "{:.1f}",
    "Gr.A.D Tabla": "{:.1f}",
    "% Unif": "{:.1f}%",
    "Peso Real": "{:.1f}",
    "Peso Tab": "{:.1f}",
    "% Pdn. Real": "{:.1f}%",
    "% Pdn. Tabla": "{:.1f}%",
    "H.A.A. Real": "{:.1f}",
    "H.A.A. Tabla": "{:.1f}",
    "Costo Alimento Sem": "${:,.0f}",
    "$ Huevo por alimento": "${:,.1f}",
    "Dif Pdn": "{:+.1f}%",
    "Dif GAD": "{:+.1f}",
    "Dif HAA": "{:+.1f}",
    "Dif Peso": "{:+.1f}",
    "Dif Mort": "{:+.1f}%",
}


# --- CARGAR LOGO BASE64 ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None


logo_path = os.path.join("DATA", "logo hupa.png")
logo_b64 = get_image_base64(logo_path)
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" style="height: 60px;'
    ' margin-right: 18px; border-radius: 8px; object-fit: contain;">'
    if logo_b64
    else ""
)

# --- 2. ESTILO CSS AGROTECH EXECUTIVE NARANJA ---
st.markdown(
    """
    <style>
    [data-testid="stHeader"] { background-color: transparent !important; }

    .app-header {
        background: linear-gradient(135deg, #D35400 0%, #E67E22 100%);
        padding: 20px 28px;
        border-radius: 16px;
        color: #FFFFFF !important;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px -4px rgba(211, 84, 0, 0.25);
        display: flex;
        align-items: center;
    }
    .app-header-text h1 {
        color: #FFFFFF !important;
        font-size: clamp(1.3rem, 2.5vw, 1.8rem) !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }
    .app-header-text p {
        color: #FDF2E9 !important;
        margin: 4px 0 0 0 !important;
        font-size: clamp(0.75rem, 1.5vw, 0.9rem) !important;
        opacity: 0.95;
    }

    .filter-panel {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(211, 84, 0, 0.2);
        border-radius: 14px;
        padding: 16px 20px 10px 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    .kpi-card-exec {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.18);
        border-radius: 14px;
        padding: 16px 10px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        position: relative;
        overflow: hidden;
        margin-bottom: 15px;
        transition: transform 0.2s ease;
    }
    .kpi-card-exec:hover { transform: translateY(-3px); }
    .kpi-card-exec::before {
        content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, #D35400, #F39C12);
    }
    .kpi-title-exec {
        font-size: clamp(0.7rem, 0.9vw, 0.8rem);
        font-weight: 700;
        color: var(--text-color);
        opacity: 0.75;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .kpi-val-exec {
        font-size: clamp(1.3rem, 1.8vw, 1.7rem);
        font-weight: 800;
        color: var(--text-color);
        line-height: 1.1;
    }

    .alert-card-item {
        background-color: var(--secondary-background-color);
        border-left: 5px solid #E74C3C;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
    }
    .alert-card-title {
        font-weight: 800;
        font-size: 0.9rem;
        color: #C0392B;
        margin-bottom: 2px;
    }
    .alert-card-desc {
        font-size: 0.82rem;
        color: var(--text-color);
        opacity: 0.85;
    }

    .table-container {
        max-height: 520px;
        overflow-y: auto;
        border-radius: 12px;
        border: 1px solid rgba(128, 128, 128, 0.18);
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        background-color: var(--secondary-background-color);
    }

    .custom-agrotech-table {
        width: 100%;
        border-collapse: collapse;
        font-family: inherit;
        font-size: 0.84rem;
        color: var(--text-color);
    }

    .custom-agrotech-table th {
        position: sticky;
        top: 0;
        background-color: #D35400 !important;
        color: #FFFFFF !important;
        padding: 10px 8px;
        text-align: center;
        font-weight: 700;
        border-bottom: 2px solid rgba(0,0,0,0.1);
        z-index: 2;
    }

    .custom-agrotech-table td {
        padding: 8px 6px;
        text-align: center;
        border-bottom: 1px solid rgba(128, 128, 128, 0.12);
        white-space: nowrap;
    }

    .custom-agrotech-table tr:hover {
        background-color: rgba(211, 84, 0, 0.06);
    }

    .total-row {
        background-color: rgba(211, 84, 0, 0.12) !important;
        font-weight: bold;
        border-top: 2px solid #D35400;
    }

    .footer-tematico { margin-top: 30px; padding: 20px 0; text-align: center; opacity: 0.7; }
    .footer-pattern { font-size: 1.5rem; letter-spacing: 10px; margin-bottom: 8px; }

    @media (max-width: 768px) {
        .app-header { flex-direction: column; text-align: center; }
        .app-header img { margin-right: 0 !important; margin-bottom: 10px; }
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 3. VALIDACIÓN DE SESIÓN Y SEGURIDAD ---
if "auth" not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()


# --- 4. FUNCIONES AUXILIARES DE EXPORTACIÓN ---
def crear_excel(df_formateado):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_formateado.to_excel(writer, index=False, sheet_name="Reporte_HUPA")
    return output.getvalue()


def crear_pdf(df_formateado):
    pdf = FPDF(orientation="L", unit="mm", format=(420, 594))
    pdf.add_page()
    pdf.set_font("Arial", "B", 22)
    pdf.cell(
        0, 20, "REPORTE DETALLADO DE PRODUCCIÓN - HUPA", ln=True, align="C"
    )
    pdf.ln(10)

    cols = df_formateado.columns.tolist()
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(211, 84, 0)
    pdf.set_text_color(255, 255, 255)
    ancho_col = 575 / len(cols) if len(cols) > 0 else 20

    for col in cols:
        pdf.cell(ancho_col, 12, str(col), 1, 0, "C", True)
    pdf.ln()

    pdf.set_text_color(0, 0, 0)
    for i in range(len(df_formateado)):
        es_total = "TOTALES" in str(df_formateado.iloc[i].values)
        if es_total:
            pdf.set_font("Arial", "B", 9)
            pdf.set_fill_color(253, 242, 233)
            fill = True
        else:
            pdf.set_font("Arial", "", 8)
            fill = False

        for col in cols:
            valor = str(df_formateado.iloc[i][col])
            pdf.cell(ancho_col, 10, valor, 1, 0, "C", fill)
        pdf.ln()

    return pdf.output(dest="S").encode("latin-1", "ignore")


# --- 5. CARGA DE DATOS ALINEADA Y LIMPIA ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")


@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        df_raw = pd.read_excel(PATH_DATA)
        df_raw.columns = [
            str(col).replace("\n", " ").strip() for col in df_raw.columns
        ]

        # Normalizar Columna Empresa
        col_empresa = None
        for c in [
            "EMPRESA",
            "RAZON_SOCIAL",
            "RAZON SOCIAL",
            "SOCIEDAD",
            "Razon Social",
            "Razón Social",
            "RS",
        ]:
            if c in df_raw.columns:
                col_empresa = c
                break
        if not col_empresa:
            df_raw["RAZON_SOCIAL"] = "HUPA | DIVISIÓN AVÍCOLA"
        else:
            df_raw["RAZON_SOCIAL"] = (
                df_raw[col_empresa].astype(str).str.strip()
            )

        # Normalizar Columna Galpón
        col_galpon = None
        for cg in [
            "GALPON",
            "GALPÓN",
            "NUM_GALPON",
            "NUM GALPON",
            "Galpon",
            "Galpón",
        ]:
            if cg in df_raw.columns:
                col_galpon = cg
                break

        if col_galpon and "GALPON" not in df_raw.columns:
            df_raw["GALPON"] = df_raw[col_galpon]

        # FILTRO DE ORO: LOTE == NUM_GALPON
        if col_galpon and "LOTE" in df_raw.columns:
            df_raw["LOTE_STR"] = df_raw["LOTE"].astype(str).str.strip()
            df_raw["GALPON_STR"] = df_raw[col_galpon].astype(str).str.strip()
            df_raw = df_raw[df_raw["LOTE_STR"] == df_raw["GALPON_STR"]].copy()

        # Normalizar Fecha
        if "Final Sem" in df_raw.columns:
            df_raw["Fecha_DT"] = pd.to_datetime(
                df_raw["Final Sem"], errors="coerce"
            )
        elif "F. Fin De Sem" in df_raw.columns:
            df_raw["Fecha_DT"] = pd.to_datetime(
                df_raw["F. Fin De Sem"], errors="coerce"
            )
        else:
            df_raw["Fecha_DT"] = pd.NaT

        # Normalizar Línea Genética
        col_linea = None
        posibles_linea = [
            "LINEA_AVES",
            "LINEA AVES",
            "LINEA GENETICA",
            "LINEA_GENETICA",
            "GENETICA",
            "LINEA",
            "Línea Genética",
            "RAZA",
            "Raza",
        ]
        for cl in posibles_linea:
            if cl in df_raw.columns:
                col_linea = cl
                break
        if not col_linea:
            df_raw["LINEA_AVES"] = "Sin Especificar"
        else:
            df_raw["LINEA_AVES"] = (
                df_raw[col_linea].fillna("Sin Especificar").astype(str).str.strip()
            )

        # Normalizar Saldo de Aves
        if "Saldo Aves" in df_raw.columns and "Saldo de Aves" not in df_raw.columns:
            df_raw["Saldo de Aves"] = df_raw["Saldo Aves"]

        # Normalizar Observaciones / Casas Nutricionales
        if "Observaciones" in df_raw.columns:
            df_raw["Observaciones"] = (
                df_raw["Observaciones"]
                .astype(str)
                .replace(["nan", "None", "", "0", "NaN"], "Sin especificar")
            )

        return df_raw
    return None


df_orig = load_data()

# --- SIDEBAR DE USUARIO ---
with st.sidebar:
    usuario_actual = st.session_state.get("user", "VET_HUPA")
    st.markdown(
        f"<div style='font-weight:bold; color:var(--text-color);"
        f" margin-bottom:10px;'>👤 Sesión Activa: {usuario_actual}</div>",
        unsafe_allow_html=True,
    )
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.switch_page("app.py")
        st.rerun()
    st.divider()

# --- 6. RENDERIZADO DE INTERFAZ ---
st.markdown(
    f"""
    <div class="app-header">
        {logo_html}
        <div class="app-header-text">
            <h1>Estado General de Operación</h1>
            <p>Balance táctico, desempeño biológico y auditoría ejecutiva de lotes de postura (Foto Actual)</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_orig is not None:
    with st.expander(
        "📌 Balance Táctico e Instrucciones del Tablero", expanded=False
    ):
        st.markdown(
            """
            Bienvenido a la **Torre de Control HUPA**. Esta interfaz presenta el consolidado del desempeño biológico y operativo al cierre de la última semana técnica. 
            El objetivo es evaluar el **Estado Operativo Actual** de cada lote, contrastando sus resultados reales frente a las metas genéticas, facilitando una gestión basada en datos para optimizar recursos.
            """
        )

    # PANEL INTEGRADO DE FILTROS
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)

    c_emp, c_mod = st.columns([2, 1])

    empresas_disp = sorted(
        [x for x in df_orig["RAZON_SOCIAL"].unique() if pd.notna(x)]
    )
    empresa_default = (
        st.session_state.user
        if st.session_state.user in empresas_disp
        else empresas_disp[0]
    )
    idx_default = (
        empresas_disp.index(empresa_default)
        if empresa_default in empresas_disp
        else 0
    )

    with c_emp:
        empresa = st.selectbox(
            "🏢 Empresa / Razón Social:", empresas_disp, index=idx_default
        )

    with c_mod:
        modo_vista = st.selectbox(
            "👁️ Modo de Vista de Tabla:",
            ["Tabla HTML AgroTech", "Visor Tabular Interactivo"],
            index=0,
        )

    # Filtrar por Empresa seleccionada
    df_empresa = df_orig[df_orig["RAZON_SOCIAL"] == empresa].copy()

    # DETECTAR COLUMNA DE ARCHIVO ORIGEN
    col_archivo = next(
        (
            ca
            for ca in [
                "ARCHIVO_ORIGEN",
                "Archivo_Origen",
                "archivo_origen",
                "ARCHIVO",
                "Archivo",
                "archivo",
            ]
            if ca in df_empresa.columns
        ),
        None,
    )

    # CLAVE DE AGRUPACIÓN PARA MANTENER CADA SUB-ARCHIVO / GALPÓN INDEPENDIENTE
    clave_agrupacion = ["GRANJA", "LOTE"]
    if col_archivo:
        clave_agrupacion.append(col_archivo)

    # EXTRAER LA ÚLTIMA FECHA/EDAD MÁXIMA DE CADA REGISTRO/SUB-ARCHIVO
    df_sorted = df_empresa.sort_values("Fecha_DT", ascending=True)
    df_ultimos_galpones = (
        df_sorted.groupby(clave_agrupacion).last().reset_index()
    )

    df_ultimos_base = df_ultimos_galpones.copy()

    st.markdown(
        "<hr style='margin:10px 0; border-color:rgba(211,84,0,0.15);'>",
        unsafe_allow_html=True,
    )

    # Fila 2: Filtros Específicos (Granja, Genética, Alimento)
    f_col1, f_col2, f_col3 = st.columns(3)

    lista_granjas = ["Todas"] + sorted(
        [str(x) for x in df_ultimos_base["GRANJA"].unique() if pd.notna(x)]
    )
    lista_genetica = ["Todas"] + sorted(
        [str(x) for x in df_ultimos_base["LINEA_AVES"].unique() if pd.notna(x)]
    )
    lista_alimento = ["Todas"] + sorted(
        [
            str(x)
            for x in df_ultimos_base["Fase de Alimento"].unique()
            if pd.notna(x)
        ]
    )

    with f_col1:
        sel_granja = st.selectbox(
            "MAP Filtrar Granja:", lista_granjas, index=0
        )
    with f_col2:
        sel_genetica = st.selectbox(
            "🧬 Filtrar Genética:", lista_genetica, index=0
        )
    with f_col3:
        sel_alimento = st.selectbox(
            "🥣 Filtrar Fase de Alimento:", lista_alimento, index=0
        )

    # Fila 3: Slider Rango de Edad (PROTEGIDO CONTRA ERRORES DE MIN_VALUE == MAX_VALUE)
    if not df_ultimos_base.empty:
        edad_min = int(df_ultimos_base["Edad Sem."].min())
        edad_max = int(df_ultimos_base["Edad Sem."].max())
    else:
        edad_min, edad_max = 18, 100

    if edad_min < edad_max:
        rango_edad = st.slider(
            "⌛ Rango de Edad (Semanas):",
            min_value=edad_min,
            max_value=edad_max,
            value=(edad_min, edad_max),
            step=1,
        )
    else:
        st.info(f"ℹ️ Todos los lotes filtrados tienen la misma edad: **{edad_min} Semanas**")
        rango_edad = (edad_min, edad_max)

    st.markdown("</div>", unsafe_allow_html=True)

    # APLICACIÓN DE FILTROS AL DATASET
    df_ultimos = df_ultimos_base.copy()

    if sel_granja != "Todas":
        df_ultimos = df_ultimos[
            df_ultimos["GRANJA"].astype(str) == sel_granja
        ]

    if sel_genetica != "Todas":
        df_ultimos = df_ultimos[
            df_ultimos["LINEA_AVES"].astype(str) == sel_genetica
        ]

    if sel_alimento != "Todas":
        df_ultimos = df_ultimos[
            df_ultimos["Fase de Alimento"].astype(str) == sel_alimento
        ]

    df_ultimos = df_ultimos[
        (df_ultimos["Edad Sem."] >= rango_edad[0])
        & (df_ultimos["Edad Sem."] <= rango_edad[1])
    ].copy()

    # CÁLCULO DE DIFERENCIAS TÉCNICAS
    df_ultimos["Dif Pdn"] = pd.to_numeric(
        df_ultimos["% Pdn. Real"], errors="coerce"
    ) - pd.to_numeric(df_ultimos["% Pdn. Tabla"], errors="coerce")
    df_ultimos["Dif GAD"] = pd.to_numeric(
        df_ultimos["Gr.A.D Real"], errors="coerce"
    ) - pd.to_numeric(df_ultimos["Gr.A.D Tabla"], errors="coerce")
    df_ultimos["Dif HAA"] = pd.to_numeric(
        df_ultimos["H.A.A. Real"], errors="coerce"
    ) - pd.to_numeric(df_ultimos["H.A.A. Tabla"], errors="coerce")
    df_ultimos["Dif Peso"] = pd.to_numeric(
        df_ultimos["Peso Real"], errors="coerce"
    ) - pd.to_numeric(df_ultimos["Peso Tab"], errors="coerce")
    df_ultimos["Dif Mort"] = pd.to_numeric(
        df_ultimos["%Mort+Sel Acum. Tab"], errors="coerce"
    ) - pd.to_numeric(df_ultimos["% Mort + Sel Acum."], errors="coerce")

    # TARJETAS KPI EXECUTIVE (FOTO ACTUAL REAL)
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(
            f"""<div class="kpi-card-exec">
                <div class="kpi-title-exec">🐔 Aves Totales (Censo Actual)</div>
                <div class="kpi-val-exec">{df_ultimos["Saldo de Aves"].sum():,.0f}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="kpi-card-exec">
                <div class="kpi-title-exec">📦 Registros/Lotes Activos</div>
                <div class="kpi-val-exec">{len(df_ultimos)}</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        val_edad_m = (
            df_ultimos["Edad Sem."].mean() if not df_ultimos.empty else 0
        )
        st.markdown(
            f"""<div class="kpi-card-exec">
                <div class="kpi-title-exec">⌛ Edad Media</div>
                <div class="kpi-val-exec">{val_edad_m:.1f} <small style="font-size:0.9rem">Sem</small></div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        val_pdn_m = (
            df_ultimos["% Pdn. Real"].mean() if not df_ultimos.empty else 0
        )
        st.markdown(
            f"""<div class="kpi-card-exec">
                <div class="kpi-title-exec">🥚 Postura Prom.</div>
                <div class="kpi-val-exec">{val_pdn_m:.1f}%</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col5:
        val_mort_m = (
            df_ultimos["% Mort + Sel Acum."].mean()
            if not df_ultimos.empty
            else 0
        )
        st.markdown(
            f"""<div class="kpi-card-exec">
                <div class="kpi-title-exec">💀 Mortalidad</div>
                <div class="kpi-val-exec">{val_mort_m:.1f}%</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # --- ALERTAS TEMPRANAS OPERATIVAS ---
    lotes_alerta_pdn = df_ultimos[df_ultimos["Dif Pdn"] < -3.0]
    lotes_alerta_mort = df_ultimos[df_ultimos["Dif Mort"] < 0]
    cant_alertas = len(lotes_alerta_pdn) + len(lotes_alerta_mort)

    titulo_expander_alertas = (
        f"🚨 Alertas Tempranas Operativas ({cant_alertas} Desviaciones"
        " Detectadas)"
        if cant_alertas > 0
        else (
            "✅ Diagnóstico de Alertas Operativas (Sin Desviaciones"
            " Críticas)"
        )
    )

    with st.expander(titulo_expander_alertas, expanded=False):
        if cant_alertas == 0:
            st.success(
                "🎉 Todos los lotes en la vista actual se encuentran operando"
                " dentro de los parámetros biológicos esperados."
            )
        else:
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                st.markdown(
                    "#### 🔴 Desviación Crítica en Postura (<-3% vs Meta)"
                )
                if lotes_alerta_pdn.empty:
                    st.caption("No hay lotes con caída de postura grave.")
                else:
                    for _, row in lotes_alerta_pdn.iterrows():
                        st.markdown(
                            f"""
                            <div class="alert-card-item">
                                <div class="alert-card-title">Granja {row['GRANJA']} - Lote {row['LOTE']} ({row['LINEA_AVES']})</div>
                                <div class="alert-card-desc">
                                    <b>Postura Real:</b> {row['% Pdn. Real']:.1f}% | <b>Meta:</b> {row['% Pdn. Tabla']:.1f}% 
                                    (<span style="color:#C0392B; font-weight:bold;">{row['Dif Pdn']:.1f}%</span>)
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            with col_a2:
                st.markdown("#### 💀 Mortalidad Por Encima de Guía Genética")
                if lotes_alerta_mort.empty:
                    st.caption("No hay lotes con exceso de mortalidad.")
                else:
                    for _, row in lotes_alerta_mort.iterrows():
                        st.markdown(
                            f"""
                            <div class="alert-card-item">
                                <div class="alert-card-title">Granja {row['GRANJA']} - Lote {row['LOTE']} (Edad: {row['Edad Sem.']} sem)</div>
                                <div class="alert-card-desc">
                                    <b>Mort. Acum. Real:</b> {row['% Mort + Sel Acum.']:.1f}% | <b>Meta Tab:</b> {row['%Mort+Sel Acum. Tab']:.1f}%
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

    # GRÁFICOS DE DISTRIBUCIÓN
    with st.expander(
        "📊 Ver Gráficos de Distribución de Aves (Foto Actual)", expanded=True
    ):
        cg1, cg2, cg3 = st.columns(3)

        def clean_fig(fig):
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                textfont_size=12,
            )
            fig.update_layout(
                margin=dict(t=25, b=0, l=0, r=0),
                height=320,
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            return fig

        with cg1:
            st.markdown(
                "<p style='text-align:center; font-weight:bold;'>MAP"
                " Distribución por Granja</p>",
                unsafe_allow_html=True,
            )
            if not df_ultimos.empty:
                df_g1 = df_ultimos.groupby("GRANJA", as_index=False)[
                    "Saldo de Aves"
                ].sum()
                fig1 = px.pie(
                    df_g1,
                    values="Saldo de Aves",
                    names="GRANJA",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Oranges_r,
                )
                st.plotly_chart(
                    clean_fig(fig1),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            else:
                st.info("Sin datos para los filtros seleccionados.")

        with cg2:
            st.markdown(
                "<p style='text-align:center; font-weight:bold;'>🧬"
                " Distribución por Genética</p>",
                unsafe_allow_html=True,
            )
            if not df_ultimos.empty:
                df_g2 = df_ultimos.groupby("LINEA_AVES", as_index=False)[
                    "Saldo de Aves"
                ].sum()
                df_g2 = df_g2[df_g2["Saldo de Aves"] > 0]

                fig2 = px.pie(
                    df_g2,
                    values="Saldo de Aves",
                    names="LINEA_AVES",
                    hole=0.45,
                    color_discrete_sequence=px.colors.qualitative.Set3,
                )
                fig2.update_traces(
                    hovertemplate=(
                        "<b>%{label}</b><br>Censo Aves:"
                        " %{value:,.0f}<br>Participación: <b>%{percent}</b>"
                    )
                )
                st.plotly_chart(
                    clean_fig(fig2),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            else:
                st.info("Sin datos para los filtros seleccionados.")

        with cg3:
            st.markdown(
                "<p style='text-align:center; font-weight:bold;'>🥣"
                " Distribución por Fase Alimento / Casa Nutricional</p>",
                unsafe_allow_html=True,
            )
            if not df_ultimos.empty:
                col_pie_nutricion = (
                    "Fase de Alimento"
                    if "Fase de Alimento" in df_ultimos.columns
                    else "Observaciones"
                )

                df_pie_nutr = df_ultimos.copy()
                df_pie_nutr[col_pie_nutricion] = (
                    df_pie_nutr[col_pie_nutricion]
                    .fillna("Sin Especificar")
                    .astype(str)
                    .str.strip()
                )
                df_pie_nutr[col_pie_nutricion] = df_pie_nutr[
                    col_pie_nutricion
                ].replace(
                    ["nan", "None", "", "0", "NaN"], "Sin Especificar"
                )

                df_g3 = df_pie_nutr.groupby(
                    col_pie_nutricion, as_index=False
                )["Saldo de Aves"].sum()
                df_g3 = df_g3[df_g3["Saldo de Aves"] > 0]

                fig3 = px.pie(
                    df_g3,
                    values="Saldo de Aves",
                    names=col_pie_nutricion,
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set2,
                )
                fig3.update_traces(
                    hovertemplate=(
                        "<b>%{label}</b><br>Censo Aves:"
                        " %{value:,.0f}<br>Participación: <b>%{percent}</b>"
                    )
                )
                st.plotly_chart(
                    clean_fig(fig3),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            else:
                st.info("Sin datos para los filtros seleccionados.")

    # RESTRICCIÓN DE COLUMNAS SEGÚN USUARIO/ROL
    if usuario_actual == "VET_HUPA":
        lista_negra = ["Costo Alimento Sem", "$ Huevo por alimento"]
        cols_finales = [c for c in cols_base if c not in lista_negra]
    else:
        cols_finales = cols_base

    cols_disponibles = [c for c in cols_finales if c in df_ultimos.columns]
    tabla_base = (
        df_ultimos[cols_disponibles]
        .sort_values(["LOTE", "Edad Sem."], ascending=[True, False])
        .copy()
    )
    formatos_activos = {
        k: v for k, v in formatos.items() if k in tabla_base.columns
    }

    # SELECCIÓN DINÁMICA DE COLUMNAS VISIBLES EN PANTALLA
    c_head1, c_head2 = st.columns([2.5, 1])
    with c_head1:
        st.markdown("### 📋 Resumen Detallado de Producción")
    with c_head2:
        with st.popover("⚙️ Seleccionar Columnas Visibles"):
            cols_visibles = [
                col
                for col in cols_disponibles
                if st.checkbox(col, value=True, key=f"vis_{col}")
            ]

    if not cols_visibles:
        cols_visibles = cols_disponibles

    tabla_final = tabla_base[cols_visibles].copy()

    # MÓDULO DE EXPORTACIÓN (EXCEL / PDF)
    with st.expander("📥 Exportar Reporte Operativo (Excel / PDF)"):
        c1, c2 = st.columns(2)
        with c1:
            nombre_persona = st.text_input(
                "Nombre del auditor responsable:", key="input_descarga"
            )
        with c2:
            formato_archivo = st.radio(
                "Seleccione formato:", ["Excel", "PDF"], horizontal=True
            )

        with st.popover("⚙️ Personalizar Columnas de Descarga"):
            cols_exportar = [
                col
                for col in cols_disponibles
                if st.checkbox(col, value=True, key=f"check_exp_{col}")
            ]

        if nombre_persona and cols_exportar:
            resumen_data = {}
            for col in cols_exportar:
                if col == cols_exportar[0]:
                    resumen_data[col] = "TOTALES"
                elif col in [
                    "Saldo de Aves",
                    "Mort",
                    "Bulto X 40 K",
                    "Costo Alimento Sem",
                    "Huevos  Semana",
                ]:
                    resumen_data[col] = tabla_base[col].sum()
                elif col in [
                    "Edad Sem.",
                    "% Mort + Sel Acum.",
                    "%Mort+Sel Acum. Tab",
                    "Dif Mort",
                    "$ Huevo por alimento",
                    "Gr.A.D Real",
                    "Gr.A.D Tabla",
                    "Dif GAD",
                    "% Pdn. Real",
                    "% Pdn. Tabla",
                    "Dif Pdn",
                    "H.A.A. Real",
                    "H.A.A. Tabla",
                    "Dif HAA",
                ]:
                    resumen_data[col] = tabla_base[col].mean()
                else:
                    resumen_data[col] = ""

            df_reporte_num = pd.concat(
                [
                    tabla_base[cols_exportar],
                    pd.DataFrame([resumen_data])[cols_exportar],
                ],
                ignore_index=True,
            )
            df_descarga = df_reporte_num.copy()

            if "Final Sem" in df_descarga.columns:
                df_descarga["Final Sem"] = pd.to_datetime(
                    df_descarga["Final Sem"]
                ).dt.strftime("%d/%m/%y")

            for col, fmt in formatos.items():
                if col in df_descarga.columns:
                    df_descarga[col] = df_descarga[col].apply(
                        lambda x: (
                            fmt.format(x)
                            if (pd.notnull(x) and not isinstance(x, str))
                            else x
                        )
                    )

            if formato_archivo == "Excel":
                st.download_button(
                    label="🚀 Descargar Excel",
                    data=crear_excel(df_descarga),
                    file_name=f"HUPA_{nombre_persona}.xlsx",
                )
            else:
                st.download_button(
                    label="🚀 Descargar PDF",
                    data=crear_pdf(df_descarga),
                    file_name=f"HUPA_{nombre_persona}.pdf",
                )
        else:
            st.info(
                "💡 Ingrese el nombre del auditor para habilitar el botón de"
                " descarga."
            )

    # RENDERIZADO SEGÚN MODO DE VISTA
    if modo_vista == "Tabla HTML AgroTech":

        def render_custom_table(df_data):
            html = (
                '<div class="table-container"><table'
                ' class="custom-agrotech-table"><thead><tr>'
            )
            for col in df_data.columns:
                html += f"<th>{col}</th>"
            html += "</tr></thead><tbody>"

            for idx, row in df_data.iterrows():
                html += "<tr>"
                for col in df_data.columns:
                    val = row[col]
                    style = ""
                    title_tip = ""

                    # ALERTAS VISUALES EN CELDAS
                    if col == "Dif Pdn" and pd.notnull(val):
                        try:
                            n_v = float(val)
                            if n_v >= 0:
                                style = (
                                    "background-color:#E8F8F5; color:#117A65;"
                                    " font-weight:bold;"
                                )
                                title_tip = f"🟢 +{n_v:.1f}% sobre la meta"
                            else:
                                style = (
                                    "background-color:#FDEDEC; color:#A93226;"
                                    " font-weight:bold;"
                                )
                                title_tip = f"🔴 {n_v:.1f}% bajo la meta"
                        except:
                            pass

                    elif col == "Dif HAA" and pd.notnull(val):
                        try:
                            n_v = float(val)
                            if n_v >= 0:
                                style = (
                                    "background-color:#E8F8F5; color:#117A65;"
                                    " font-weight:bold;"
                                )
                                title_tip = (
                                    f"🟢 +{n_v:.1f} huevos/ave alojada sobre"
                                    " meta"
                                )
                            else:
                                style = (
                                    "background-color:#FDEDEC; color:#A93226;"
                                    " font-weight:bold;"
                                )
                                title_tip = (
                                    f"🔴 {n_v:.1f} huevos/ave alojada bajo meta"
                                )
                        except:
                            pass

                    elif col == "Dif GAD" and pd.notnull(val):
                        try:
                            n_v = float(val)
                            if n_v > 1.5:
                                style = (
                                    "background-color:#FEF5E7; color:#B9770E;"
                                    " font-weight:bold;"
                                )
                                title_tip = f"🟠 +{n_v:.1f}g sobreconsumo"
                            else:
                                style = (
                                    "background-color:#E8F8F5; color:#117A65;"
                                    " font-weight:bold;"
                                )
                                title_tip = f"🟢 {n_v:.1f}g consumo normal"
                        except:
                            pass

                    elif col == "Dif Mort" and pd.notnull(val):
                        try:
                            n_v = float(val)
                            if n_v < 0:
                                style = (
                                    "background-color:#FDEDEC; color:#A93226;"
                                    " font-weight:bold;"
                                )
                                title_tip = "🔴 Mortalidad superior a la guía"
                            else:
                                style = (
                                    "background-color:#E8F8F5; color:#117A65;"
                                    " font-weight:bold;"
                                )
                                title_tip = "🟢 Mortalidad dentro de meta"
                        except:
                            pass

                    if (
                        col in formatos_activos
                        and pd.notnull(val)
                        and isinstance(val, (int, float))
                    ):
                        fmt_val = formatos_activos[col].format(val)
                    elif col == "Final Sem" and hasattr(val, "strftime"):
                        fmt_val = val.strftime("%d/%m/%y")
                    else:
                        fmt_val = str(val) if pd.notnull(val) else ""

                    if style:
                        html += (
                            f'<td style="{style}"'
                            f' title="{title_tip}">{fmt_val}</td>'
                        )
                    else:
                        html += f"<td>{fmt_val}</td>"
                html += "</tr>"

            # FILA DE TOTALES / PROMEDIOS
            html += '<tr class="total-row">'
            for col in df_data.columns:
                if col == df_data.columns[0]:
                    val_tot = "TOTALES / PROM."
                elif col in [
                    "Saldo de Aves",
                    "Mort",
                    "Bulto X 40 K",
                    "Costo Alimento Sem",
                    "Huevos  Semana",
                ]:
                    val_tot = formatos_activos.get(col, "{:,.0f}").format(
                        df_data[col].sum()
                    )
                elif col in [
                    "Edad Sem.",
                    "% Mort + Sel Acum.",
                    "%Mort+Sel Acum. Tab",
                    "Dif Mort",
                    "$ Huevo por alimento",
                    "Gr.A.D Real",
                    "Gr.A.D Tabla",
                    "Dif GAD",
                    "% Pdn. Real",
                    "% Pdn. Tabla",
                    "Dif Pdn",
                    "H.A.A. Real",
                    "H.A.A. Tabla",
                    "Dif HAA",
                ]:
                    val_tot = formatos_activos.get(col, "{:.1f}").format(
                        df_data[col].mean()
                    )
                else:
                    val_tot = ""
                html += f"<td>{val_tot}</td>"
            html += "</tr>"

            html += "</tbody></table></div>"
            st.markdown(html, unsafe_allow_html=True)

        render_custom_table(tabla_final)

    else:
        # VISOR TABULAR INTERACTIVO
        df_interactivo = tabla_final.copy()
        if "Final Sem" in df_interactivo.columns:
            df_interactivo["Final Sem"] = pd.to_datetime(
                df_interactivo["Final Sem"]
            ).dt.strftime("%d/%m/%y")

        for col, fmt in formatos_activos.items():
            if col in df_interactivo.columns:
                df_interactivo[col] = df_interactivo[col].apply(
                    lambda x: fmt.format(x) if pd.notnull(x) else ""
                )

        st.dataframe(
            df_interactivo, use_container_width=True, hide_index=True
        )

    # SELLO DE SINCRONIZACIÓN CON SERVIDOR
    try:
        mtime = os.path.getmtime(PATH_DATA)
        fecha_act = datetime.datetime.fromtimestamp(mtime).strftime(
            "%d/%m/%Y %I:%M %p"
        )
        st.markdown(
            f"<div style='text-align: right; opacity: 0.6; font-size: 0.85rem;"
            f" font-style: italic; margin-top: 10px;'>📅 Última actualización:"
            f" {fecha_act}</div>",
            unsafe_allow_html=True,
        )
    except:
        pass

    # FOOTER AVÍCOLA
    st.divider()
    st.markdown(
        """
        <div class='footer-tematico'>
            <div class='footer-pattern'>🐔 🥚 🐔 🥚 🐔 🥚</div>
            <div><b>HUPA | División Avícola</b><br>Análisis de Datos para la Excelencia Productiva</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.error("⚠️ No se pudo cargar el archivo Consolidado_Produccion_FINAL.xlsx")