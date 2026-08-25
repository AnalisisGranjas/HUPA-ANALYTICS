import base64
import datetime
import io
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- 1. CONFIGURACIÓN GLOBAL DE FORMATOS ---
formatos = {
    "Saldo de Aves": "{:,.0f}",
    "Huevos  Semana": "{:,.0f}",
    "Edad Sem.": "{:.0f}",
    "Jumbo %": "{:.1f}%",
    "Extra %": "{:.1f}%",
    "AA %": "{:.1f}%",
    "A %": "{:.1f}%",
    "B %": "{:.1f}%",
    "C %": "{:.1f}%",
    "Grande %": "{:.1f}%",
    "Mediano %": "{:.1f}%",
    "Pequeño %": "{:.1f}%",
    "Blanco %": "{:.1f}%",
    "Segunda %": "{:.1f}%",
    "% Pdn. Real": "{:.1f}%",
}

# --- SEGURIDAD Y CONFIGURACIÓN ---
if "auth" not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

st.set_page_config(
    page_title="HUPA | Clasificación de Huevo por Lote",
    page_icon="🥚",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- CARGAR LOGO BASE64 ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None


logo_path = os.path.join("DATA", "logo hupa.png")
logo_b64 = get_image_base64(logo_path)
logo_html = (
    f'<img src="data:image/png;base64,{logo_b64}" style="height: 55px;'
    ' margin-right: 15px; border-radius: 8px; object-fit: contain;">'
    if logo_b64
    else ""
)

# --- 2. ESTILO CSS AGROTECH ORANGE ADAPTABLE ---
st.markdown(
    """
    <style>
    [data-testid="stHeader"] { background-color: transparent !important; }

    .app-header {
        background: linear-gradient(135deg, #D35400 0%, #E67E22 100%);
        padding: 18px 24px;
        border-radius: 14px;
        color: #FFFFFF !important;
        margin-bottom: 20px;
        box-shadow: 0 8px 20px -4px rgba(211, 84, 0, 0.25);
        display: flex;
        align-items: center;
        flex-wrap: wrap;
    }
    .app-header-text h1 {
        color: #FFFFFF !important;
        font-size: clamp(1.2rem, 2.2vw, 1.7rem) !important;
        font-weight: 800 !important;
        margin: 0 !important;
    }
    .app-header-text p {
        color: #FDF2E9 !important;
        margin: 2px 0 0 0 !important;
        font-size: clamp(0.75rem, 1.3vw, 0.88rem) !important;
        opacity: 0.95;
    }

    .filter-panel {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(211, 84, 0, 0.25);
        border-radius: 12px;
        padding: 14px 18px 10px 18px;
        margin-bottom: 20px;
    }

    .kpi-card {
        background-color: var(--secondary-background-color);
        border-radius: 12px;
        padding: 14px 16px;
        border: 1px solid rgba(211, 84, 0, 0.25);
        border-top: 5px solid #D35400;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .kpi-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--text-color);
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: 800;
        color: #D35400;
        margin: 4px 0;
    }
    .kpi-sub {
        font-size: 0.75rem;
        opacity: 0.7;
    }

    .genetica-badge {
        background: rgba(211, 84, 0, 0.15);
        color: #D35400;
        border: 1px solid #D35400;
        padding: 3px 10px;
        border-radius: 16px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-left: 8px;
    }

    .table-container {
        max-height: 500px;
        overflow-y: auto;
        overflow-x: auto;
        border-radius: 10px;
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 20px;
        background-color: var(--secondary-background-color);
    }

    .custom-agrotech-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.83rem;
        color: var(--text-color);
    }

    .custom-agrotech-table th {
        position: sticky;
        top: 0;
        background-color: #D35400 !important;
        color: #FFFFFF !important;
        padding: 9px 8px;
        text-align: center;
        font-weight: 700;
        border-bottom: 2px solid rgba(0,0,0,0.15);
        z-index: 2;
    }

    .custom-agrotech-table td {
        padding: 7px 6px;
        text-align: center;
        border-bottom: 1px solid rgba(128, 128, 128, 0.15);
        white-space: nowrap;
    }

    .custom-agrotech-table tr:hover {
        background-color: rgba(211, 84, 0, 0.08);
    }

    .hr-custom {
        border: 0; height: 1px;
        background: linear-gradient(to right, rgba(0,0,0,0), rgba(211, 84, 0, 0.35), rgba(0,0,0,0));
        margin: 25px 0;
    }

    @media (max-width: 768px) {
        .app-header { flex-direction: column; text-align: center; }
        .app-header img { margin-right: 0 !important; margin-bottom: 8px; }
        .genetica-badge { display: block; margin: 6px auto 0 auto; width: fit-content; }
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 3. CARGA DE DATOS ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")


@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        try:
            df = pd.read_excel(PATH_DATA)
            df.columns = [
                str(col).replace("\n", " ").strip() for col in df.columns
            ]

            # Normalizar Columna Empresa
            col_empresa = None
            for c in ["EMPRESA", "RAZON_SOCIAL", "RAZON SOCIAL", "SOCIEDAD", "Razon Social", "Razón Social", "RS"]:
                if c in df.columns:
                    col_empresa = c
                    break
            if not col_empresa:
                df["RAZON_SOCIAL"] = "HUPA | DIVISIÓN AVÍCOLA"
            else:
                df["RAZON_SOCIAL"] = df[col_empresa].astype(str).str.strip()

            # Normalizar Genética
            col_linea = None
            posibles_linea = ["LINEA_AVES", "LINEA AVES", "LINEA GENETICA", "LINEA_GENETICA", "GENETICA", "LINEA", "Línea Genética", "RAZA", "Raza"]
            for cl in posibles_linea:
                if cl in df.columns:
                    col_linea = cl
                    break
            if not col_linea:
                df["LINEA_AVES"] = "Sin Especificar"
            else:
                df["LINEA_AVES"] = df[col_linea].fillna("Sin Especificar").astype(str).str.strip()

            # Normalizar Galpón
            col_galpon = None
            for cg in ["GALPON", "GALPÓN", "NUM_GALPON", "NUM GALPON", "Galpon", "Galpón"]:
                if cg in df.columns:
                    col_galpon = cg
                    break

            # FILTRO DE ORO: LOTE == NUM_GALPON
            if col_galpon and "LOTE" in df.columns:
                df["LOTE_STR"] = df["LOTE"].astype(str).str.strip()
                df["GALPON_STR"] = df[col_galpon].astype(str).str.strip()
                df = df[df["LOTE_STR"] == df["GALPON_STR"]].copy()

            if "Final Sem" in df.columns:
                df["Fecha_DT"] = pd.to_datetime(df["Final Sem"], errors="coerce")
            elif "F. Fin De Sem" in df.columns:
                df["Fecha_DT"] = pd.to_datetime(df["F. Fin De Sem"], errors="coerce")
            else:
                df["Fecha_DT"] = pd.NaT

            if "Fase de Alimento" in df.columns:
                df["Fase de Alimento"] = df["Fase de Alimento"].fillna("Sin especf.").astype(str)

            num_cols = [
                "Edad Sem.", "Saldo de Aves", "Huevos  Semana", "% Pdn. Real",
                "Jumbo", "Extra", "AA", "A", "B", "C",
                "Alt Cáscara", "Alt. Color", "Picado", "Roto"
            ]
            for col in [c for c in num_cols if c in df.columns]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception as e:
            st.error(f"Error Crítico al cargar clasificación: {e}")
            return None
    return None


df_orig = load_data()

# --- SIDEBAR DE USUARIO ---
usuario_actual = st.session_state.get("user", "VET_HUPA")

with st.sidebar:
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

# --- 4. RENDERIZADO DE INTERFAZ ---
st.markdown(
    f"""
    <div class="app-header">
        {logo_html}
        <div class="app-header-text">
            <h1>Clasificación Comercial de Huevo por Lote</h1>
            <p>Perfil de gramaje por categoría (Jumbo, Extra, AA, A, B, C), Huevo Blanco y Calidad</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_orig is not None:
    df_activos = df_orig.copy()

    # --- PANEL DE FILTROS ---
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)

    empresas_disp = sorted(df_activos["RAZON_SOCIAL"].unique())
    empresa_default = st.session_state.user if st.session_state.user in empresas_disp else empresas_disp[0]
    idx_default = empresas_disp.index(empresa_default) if empresa_default in empresas_disp else 0

    with f1:
        empresa = st.selectbox("🏢 Empresa:", empresas_disp, index=idx_default)

    df_emp = df_activos[df_activos["RAZON_SOCIAL"] == empresa]

    with f2:
        granjas_disp = sorted(df_emp["GRANJA"].unique())
        granja_sel = st.selectbox("MAP Selecciona Granja:", granjas_disp)

    df_g = df_emp[df_emp["GRANJA"] == granja_sel]

    with f3:
        lotes_disp = sorted(df_g["LOTE"].unique())
        lote_sel = st.selectbox("📦 Selecciona Lote:", lotes_disp)

    df_lote_raw = df_g[df_g["LOTE"] == lote_sel].copy()

    st.markdown("<hr style='margin:10px 0; border-color:rgba(211,84,0,0.15);'>", unsafe_allow_html=True)
    ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas en gráficos", value=False)
    st.markdown("</div>", unsafe_allow_html=True)

    if df_lote_raw.empty:
        st.warning("⚠️ No hay información de clasificación para la selección actual.")
    else:
        # --- CONSOLIDACIÓN HISTÓRICA LIMPIA POR SEMANA ---
        df_full_lote_list = []
        
        for sem, sem_df in df_lote_raw.groupby("Edad Sem."):
            row_sem = sem_df.iloc[-1].copy()
            
            tot_aves = sem_df["Saldo de Aves"].sum()
            tot_huevos = sem_df["Huevos  Semana"].sum() if "Huevos  Semana" in sem_df.columns else 0

            row_sem["Saldo de Aves"] = tot_aves
            row_sem["Huevos  Semana"] = tot_huevos

            cols_gramaje = ["Jumbo", "Extra", "AA", "A", "B", "C", "Alt Cáscara", "Alt. Color", "Picado", "Roto"]
            for cg in cols_gramaje:
                if cg in sem_df.columns:
                    if tot_huevos > 0:
                        row_sem[cg] = (sem_df[cg] * sem_df["Huevos  Semana"]).sum() / tot_huevos
                    else:
                        row_sem[cg] = sem_df[cg].mean()

            if tot_aves > 0 and "% Pdn. Real" in sem_df.columns:
                row_sem["% Pdn. Real"] = (sem_df["% Pdn. Real"] * sem_df["Saldo de Aves"]).sum() / tot_aves

            df_full_lote_list.append(row_sem)

        df_consolidado = pd.DataFrame(df_full_lote_list).sort_values("Edad Sem.")

        # OBTENER GENÉTICA ACTUAL DEL LOTE
        genetica_actual = df_consolidado.iloc[-1].get("LINEA_AVES", "N/A") if not df_consolidado.empty else "N/A"

        # --- SLIDER DE EDAD DEFAULT EN MAX - 6 ---
        max_e = int(df_consolidado["Edad Sem."].max())
        min_e = int(df_consolidado["Edad Sem."].min())
        val_ini_min = max(min_e, max_e - 6)

        rango_edad = st.slider(
            "⏳ Ventana de Análisis (Semanas de Edad):",
            min_e,
            max_e,
            (val_ini_min, max_e),
        )

        df_view = df_consolidado[df_consolidado["Edad Sem."].between(rango_edad[0], rango_edad[1])].copy()

        # CÁLCULOS COMERCIALES CONVERTIDOS A PORCENTAJE (× 100)
        df_view["Jumbo %"] = df_view["Jumbo"] * 100
        df_view["Extra %"] = df_view["Extra"] * 100
        df_view["AA %"] = df_view["AA"] * 100
        df_view["A %"] = df_view["A"] * 100
        df_view["B %"] = df_view["B"] * 100
        df_view["C %"] = df_view["C"] * 100

        # REGLAS COMERCIALES
        df_view["Grande %"] = df_view["Jumbo %"] + df_view["Extra %"]
        df_view["Mediano %"] = df_view["AA %"]
        df_view["Pequeño %"] = df_view["A %"] + df_view["B %"] + df_view["C %"]
        df_view["Blanco %"] = df_view["Alt. Color"] * 100
        df_view["Segunda %"] = (
            (df_view["Alt Cáscara"] + df_view["Picado"] + df_view["Roto"]) * 100
        )

        if "Final Sem" in df_view.columns:
            df_view["Fecha_Fmt"] = pd.to_datetime(
                df_view["Final Sem"], errors="coerce"
            ).dt.strftime("%d/%b/%Y")
        else:
            df_view["Fecha_Fmt"] = "N/A"

        # PROMEDIOS DEL PERÍODO
        prom_grande = df_view["Grande %"].mean()
        prom_mediano = df_view["Mediano %"].mean()
        prom_pequeno = df_view["Pequeño %"].mean()
        prom_blanco = df_view["Blanco %"].mean()
        prom_segunda = df_view["Segunda %"].mean()

        # --- KPIS ESTRATÉGICOS DE TAMAÑO DE HUEVO (5 COLUMNAS) ---
        k1, k2, k3, k4, k5 = st.columns(5)

        with k1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">💎 Grande</div>
                    <div class="kpi-value">{prom_grande:.1f}%</div>
                    <div class="kpi-sub">Jumbo / Extra</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">🥚 Mediano</div>
                    <div class="kpi-value">{prom_mediano:.1f}%</div>
                    <div class="kpi-sub">Categoría AA</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">🐣 Pequeño</div>
                    <div class="kpi-value">{prom_pequeno:.1f}%</div>
                    <div class="kpi-sub">Categorías A / B / C</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k4:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">⚪ Huevo Blanco</div>
                    <div class="kpi-value">{prom_blanco:.1f}%</div>
                    <div class="kpi-sub">Alt. Color independiente</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with k5:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-title">⚠️ Segunda</div>
                    <div class="kpi-value">{prom_segunda:.1f}%</div>
                    <div class="kpi-sub">Cáscara / Roto / Picado</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # --- SECCIÓN GRÁFICOS DE PERFIL COMERCIAL ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
        with st.expander("📈 Evolución Temporal del Perfil Comercial de Huevo", expanded=True):
            g1, g2 = st.columns(2)

            df_plot = df_view.sort_values("Edad Sem.").copy()
            mode_graf = "lines+markers+text" if ver_etiquetas else "lines+markers"

            htemp_lineas = (
                "<b>Semana: %{x}</b> (📅 %{customdata})<br>"
                "<b>%{fullData.name}:</b> %{y:.1f}%<extra></extra>"
            )

            with g1:
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(x=df_plot["Edad Sem."], y=df_plot["Grande %"], mode=mode_graf, name="Grande (Jumbo/Extra)", line=dict(color="#D35400", width=2.5), texttemplate="%{y:.1f}%", textposition="top center", hovertemplate=htemp_lineas, customdata=df_plot["Fecha_Fmt"]))
                fig1.add_trace(go.Scatter(x=df_plot["Edad Sem."], y=df_plot["Mediano %"], mode=mode_graf, name="Mediano (AA)", line=dict(color="#27AE60", width=2.5), texttemplate="%{y:.1f}%", textposition="top center", hovertemplate=htemp_lineas, customdata=df_plot["Fecha_Fmt"]))
                fig1.add_trace(go.Scatter(x=df_plot["Edad Sem."], y=df_plot["Pequeño %"], mode=mode_graf, name="Pequeño (A/B/C)", line=dict(color="#2980B9", width=2.5), texttemplate="%{y:.1f}%", textposition="top center", hovertemplate=htemp_lineas, customdata=df_plot["Fecha_Fmt"]))
                fig1.add_trace(go.Scatter(x=df_plot["Edad Sem."], y=df_plot["Blanco %"], mode=mode_graf, name="Huevo Blanco", line=dict(color="#7F8C8D", width=2, dash="dot"), texttemplate="%{y:.1f}%", textposition="top center", hovertemplate=htemp_lineas, customdata=df_plot["Fecha_Fmt"]))
                fig1.add_trace(go.Scatter(x=df_plot["Edad Sem."], y=df_plot["Segunda %"], mode=mode_graf, name="Segunda / Descarte", line=dict(color="#C0392B", width=2, dash="dash"), texttemplate="%{y:.1f}%", textposition="top center", hovertemplate=htemp_lineas, customdata=df_plot["Fecha_Fmt"]))

                fig1.update_layout(
                    title={"text": "<b>EVOLUCIÓN DE TAMAÑOS (% DEL TOTAL)</b>", "x": 0.5, "xanchor": "center"},
                    height=380,
                    margin=dict(t=55, b=25, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5),
                )
                fig1.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title_text="Edad Semanal")
                fig1.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title_text="% Participación")

                st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

            with g2:
                fig2 = go.Figure()
                
                kwargs_bar = {}
                if ver_etiquetas:
                    kwargs_bar = dict(texttemplate="%{y:.1f}%", textposition="inside")

                htemp_barras = "<b>Semana: %{x}</b> (📅 %{customdata})<br><b>%{fullData.name}:</b> %{y:.1f}%<extra></extra>"

                fig2.add_trace(go.Bar(x=df_plot["Edad Sem."], y=df_plot["Jumbo %"], name="Jumbo", marker_color="#6C3483", hovertemplate=htemp_barras, customdata=df_plot["Fecha_Fmt"], **kwargs_bar))
                fig2.add_trace(go.Bar(x=df_plot["Edad Sem."], y=df_plot["Extra %"], name="Extra", marker_color="#1F618D", hovertemplate=htemp_barras, customdata=df_plot["Fecha_Fmt"], **kwargs_bar))
                fig2.add_trace(go.Bar(x=df_plot["Edad Sem."], y=df_plot["AA %"], name="AA", marker_color="#28B463", hovertemplate=htemp_barras, customdata=df_plot["Fecha_Fmt"], **kwargs_bar))
                fig2.add_trace(go.Bar(x=df_plot["Edad Sem."], y=df_plot["A %"], name="A", marker_color="#F1C40F", hovertemplate=htemp_barras, customdata=df_plot["Fecha_Fmt"], **kwargs_bar))
                fig2.add_trace(go.Bar(x=df_plot["Edad Sem."], y=df_plot["B %"], name="B", marker_color="#E67E22", hovertemplate=htemp_barras, customdata=df_plot["Fecha_Fmt"], **kwargs_bar))
                fig2.add_trace(go.Bar(x=df_plot["Edad Sem."], y=df_plot["C %"], name="C", marker_color="#E74C3C", hovertemplate=htemp_barras, customdata=df_plot["Fecha_Fmt"], **kwargs_bar))
                fig2.add_trace(go.Bar(x=df_plot["Edad Sem."], y=df_plot["Blanco %"], name="Blanco", marker_color="#BDC3C7", hovertemplate=htemp_barras, customdata=df_plot["Fecha_Fmt"], **kwargs_bar))

                fig2.update_layout(
                    barmode="stack",
                    title={"text": "<b>DESGLOSE DETALLADO DE CATEGORÍAS (BARRAS 100%)</b>", "x": 0.5, "xanchor": "center"},
                    height=380,
                    margin=dict(t=55, b=25, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5),
                )
                fig2.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title_text="Edad Semanal")
                fig2.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title_text="% Participación")

                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        # --- SECCIÓN MATRIZ DETALLADA DE CLASIFICACIÓN ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

        c_tit, c_mod = st.columns([2.5, 1])
        with c_tit:
            st.markdown(
                f"### 📋 Matriz Detallada de Clasificación Comercial <span class=\"genetica-badge\">🧬 Genética: {genetica_actual}</span>",
                unsafe_allow_html=True,
            )
        with c_mod:
            modo_vista = st.selectbox(
                "👁️ Modo de Vista de Tabla",
                ["Tabla HTML AgroTech", "Visor Tabular Interactivo"],
                index=0,
            )

        cols_clasificacion = [
            "Final Sem",
            "Edad Sem.",
            "Saldo de Aves",
            "Huevos  Semana",
            "% Pdn. Real",
            "Jumbo %",
            "Extra %",
            "AA %",
            "A %",
            "B %",
            "C %",
            "Grande %",
            "Mediano %",
            "Pequeño %",
            "Blanco %",
            "Segunda %",
        ]

        cols_disp = [c for c in cols_clasificacion if c in df_view.columns]
        tabla_render = df_view[cols_disp].sort_values("Edad Sem.", ascending=False).fillna(0).copy()

        if "Final Sem" in tabla_render.columns:
            tabla_render["Final Sem"] = pd.to_datetime(
                tabla_render["Final Sem"], errors="coerce"
            ).dt.strftime("%d/%m/%y")

        formatos_activos = {
            k: v for k, v in formatos.items() if k in tabla_render.columns
        }
        for c in ["Jumbo %", "Extra %", "AA %", "A %", "B %", "C %", "Grande %", "Mediano %", "Pequeño %", "Blanco %", "Segunda %"]:
            formatos_activos[c] = "{:.1f}%"

        if modo_vista == "Tabla HTML AgroTech":

            def render_custom_table_clasificacion(df_data):
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

                        if col == "Grande %" and pd.notnull(val):
                            style = "background-color:rgba(39,174,96,0.15); color:#27AE60; font-weight:bold;"
                        elif col == "Segunda %" and pd.notnull(val):
                            style = "background-color:rgba(192,57,43,0.15); color:#C0392B; font-weight:bold;"

                        if (
                            col in formatos_activos
                            and pd.notnull(val)
                            and isinstance(val, (int, float))
                        ):
                            fmt_val = formatos_activos[col].format(val)
                        else:
                            fmt_val = str(val) if pd.notnull(val) else ""

                        html += f'<td style="{style}">{fmt_val}</td>'
                    html += "</tr>"

                html += "</tbody></table></div>"
                st.markdown(html, unsafe_allow_html=True)

            render_custom_table_clasificacion(tabla_render)

        else:
            df_interactivo = tabla_render.copy()
            for col, fmt in formatos_activos.items():
                if col in df_interactivo.columns:
                    df_interactivo[col] = df_interactivo[col].apply(
                        lambda x: fmt.format(x) if pd.notnull(x) else ""
                    )

            st.dataframe(
                df_interactivo,
                use_container_width=True,
                hide_index=True,
            )

else:
    st.error("⚠️ No se pudo cargar el archivo Consolidado_Produccion_FINAL.xlsx")

# FOOTER
st.divider()
st.markdown(
    """
    <div class='footer-tematico' style='margin-top: 20px; padding: 20px 0; text-align: center; opacity: 0.6;'>
        <div class='footer-pattern' style='font-size: 1.5rem; letter-spacing: 10px; margin-bottom: 10px;'>
            🐔 🥚 🐔 🥚 🐔 🥚 🐔
        </div>
        <div>
            <b>HUPA | División Avícola</b><br>
            Análisis de Datos para la Excelencia Productiva
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)