import base64
import datetime
import io
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# --- 1. CONFIGURACIÓN GLOBAL DE FORMATOS DE TEXTO ---
formatos = {
    "Saldo de Aves": "{:,.0f}",
    "Huevos  Semana": "{:,.0f}",
    "Edad Sem.": "{:.0f}",
    "Mort": "{:.0f}",
    "Bulto X 40 K": "{:.1f}",
    "Toneladas": "{:,.2f} Ton",
    "Gr.A.D Real": "{:.1f}",
    "Gr.A.D Tabla": "{:.1f}",
    "Peso Real": "{:.1f}",
    "% Pdn. Real": "{:.1f}%",
    "Conversión": "{:.1f} g",
    "Costo Kg Alimento": "${:,.1f}",
    "Costo Alimento Sem": "${:,.0f}",
    "$ Huevo por alimento": "${:,.1f}",
}

# --- SEGURIDAD Y CONFIGURACIÓN ---
if "auth" not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

st.set_page_config(
    page_title="HUPA | Costos de Alimento y Huevo",
    page_icon="💰",
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

# --- 2. ESTILO CSS AGROTECH ORANGE ---
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
        padding: 16px 20px;
        border: 1px solid rgba(211, 84, 0, 0.25);
        border-top: 5px solid #D35400;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .kpi-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--text-color);
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #D35400;
        margin: 6px 0;
    }
    .kpi-sub {
        font-size: 0.78rem;
        opacity: 0.7;
    }

    .security-lock-card {
        background-color: var(--secondary-background-color);
        border: 2px dashed #C0392B;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        margin: 30px 0;
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
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 3. CARGA DE DATOS IDÉNTICA A ANÁLISIS POR LOTE ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")


@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        df = pd.read_excel(PATH_DATA)
        df.columns = [str(col).replace("\n", " ").strip() for col in df.columns]

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

        # Normalizar Galpón
        col_galpon = None
        for cg in ["GALPON", "GALPÓN", "NUM_GALPON", "NUM GALPON", "Galpon", "Galpón"]:
            if cg in df.columns:
                col_galpon = cg
                break

        # FILTRO DE ORO: LOTE == NUM_GALPON (EVITA DUPLICAR AVES)
        if col_galpon and "LOTE" in df.columns:
            df["LOTE_STR"] = df["LOTE"].astype(str).str.strip()
            df["GALPON_STR"] = df[col_galpon].astype(str).str.strip()
            df = df[df["LOTE_STR"] == df["GALPON_STR"]].copy()

        # Normalizar Saldo Aves
        if "Saldo Aves" in df.columns and "Saldo de Aves" not in df.columns:
            df["Saldo de Aves"] = df["Saldo Aves"]

        num_cols = [
            "% Pdn. Real", "% Pdn. Tabla", "Gr.A.D Real", "Gr.A.D Tabla",
            "Saldo de Aves", "Bulto X 40 K", "Huevos  Semana", "Costo Alimento Sem", "$ Huevo por alimento"
        ]
        for col in [c for c in num_cols if c in df.columns]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df
    return None


df_orig = load_data()

# --- SIDEBAR DE USUARIO Y VALIDACIÓN DE ROL ADMIN ---
usuario_actual = st.session_state.get("user", "VET_HUPA")
es_admin = "ADM" in str(usuario_actual).upper()

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
            <h1>Costos de Alimento y Huevo</h1>
            <p>Análisis de inversión en nutrición, costo unitario por huevo y eficiencia económica</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not es_admin:
    st.markdown(
        """
        <div class="security-lock-card">
            <h1 style="font-size: 3rem; margin: 0;">🔒</h1>
            <h2 style="color: #C0392B; margin-top: 10px;">Acceso Restringido a Información Financiera</h2>
            <p style="font-size: 1.1rem; opacity: 0.85; max-width: 600px; margin: 15px auto;">
                El módulo de <b>Costos de Alimento y Huevo</b> contiene datos confidenciales sobre estructura de precios y margen de rentabilidad.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    if df_orig is not None:
        df_activos = df_orig.copy()

        # --- PANEL DE FILTROS INDIVIDUALES ---
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
            granja_sel = st.selectbox("🏘️ Granja:", granjas_disp)

        df_g = df_emp[df_emp["GRANJA"] == granja_sel]

        with f3:
            lotes_disp = sorted(df_g["LOTE"].unique())
            lote_sel = st.selectbox("📦 Lote Activo:", lotes_disp)

        df_lote_raw = df_g[df_g["LOTE"] == lote_sel].copy()

        st.markdown("<hr style='margin:10px 0; border-color:rgba(211,84,0,0.15);'>", unsafe_allow_html=True)
        ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas en gráficos", value=False)
        st.markdown("</div>", unsafe_allow_html=True)

        if df_lote_raw.empty:
            st.warning("⚠️ No hay información de costos disponible para la selección actual.")
        else:
            # --- CONSOLIDACIÓN HISTÓRICA IDÉNTICA A ANÁLISIS POR LOTE ---
            col_archivo = None
            for ca in ["ARCHIVO_ORIGEN", "Archivo_Origen", "archivo_origen", "ARCHIVO", "Archivo", "archivo"]:
                if ca in df_lote_raw.columns:
                    col_archivo = ca
                    break

            df_full_lote_list = []
            for sem, sem_df in df_lote_raw.groupby("Edad Sem."):
                row_sem = sem_df.iloc[-1].copy()
                
                tot_aves = sem_df["Saldo de Aves"].sum()
                tot_huevos = sem_df["Huevos  Semana"].sum() if "Huevos  Semana" in sem_df.columns else 0
                tot_bultos = sem_df["Bulto X 40 K"].sum() if "Bulto X 40 K" in sem_df.columns else 0
                tot_costo = sem_df["Costo Alimento Sem"].sum() if "Costo Alimento Sem" in sem_df.columns else 0

                row_sem["Saldo de Aves"] = tot_aves
                row_sem["Huevos  Semana"] = tot_huevos
                row_sem["Bulto X 40 K"] = tot_bultos
                row_sem["Costo Alimento Sem"] = tot_costo
                row_sem["Toneladas"] = (tot_bultos * 40.0) / 1000.0

                if tot_aves > 0:
                    if "% Pdn. Real" in sem_df.columns:
                        row_sem["% Pdn. Real"] = (sem_df["% Pdn. Real"] * sem_df["Saldo de Aves"]).sum() / tot_aves
                    if "Gr.A.D Real" in sem_df.columns:
                        row_sem["Gr.A.D Real"] = (sem_df["Gr.A.D Real"] * sem_df["Saldo de Aves"]).sum() / tot_aves
                    if "Gr.A.D Tabla" in sem_df.columns:
                        row_sem["Gr.A.D Tabla"] = (sem_df["Gr.A.D Tabla"] * sem_df["Saldo de Aves"]).sum() / tot_aves

                row_sem["Costo Kg Alimento"] = (tot_costo / (tot_bultos * 40.0)) if (tot_bultos * 40.0) > 0 else 0
                row_sem["$ Huevo por alimento"] = (tot_costo / tot_huevos) if tot_huevos > 0 else 0

                df_full_lote_list.append(row_sem)

            df_consolidado = pd.DataFrame(df_full_lote_list).sort_values("Edad Sem.")

            # --- RANGO DE EDAD SLIDER (MAX_E - 6) ---
            max_e = int(df_consolidado["Edad Sem."].max())
            min_e = int(df_consolidado["Edad Sem."].min())
            inicio_defecto = max(min_e, max_e - 6)

            rango_edad = st.slider(
                "⏳ Ventana de Análisis (Semanas de Edad):",
                min_e,
                max_e,
                (inicio_defecto, max_e),
            )

            df_view = df_consolidado[df_consolidado["Edad Sem."].between(rango_edad[0], rango_edad[1])].copy()

            df_view["Conversión"] = np.where(
                df_view["Huevos  Semana"] > 0,
                (df_view["Bulto X 40 K"] * 40000) / df_view["Huevos  Semana"],
                0
            ).round(1)

            df_view["Conversión_Graf"] = np.where(df_view["Conversión"] <= 500, df_view["Conversión"], 0)

            total_costo_alimento = df_view["Costo Alimento Sem"].sum()
            total_huevos = df_view["Huevos  Semana"].sum()
            total_bultos = df_view["Bulto X 40 K"].sum()
            total_kilos = total_bultos * 40.0

            costo_prom_huevo = (total_costo_alimento / total_huevos) if total_huevos > 0 else 0
            costo_prom_kg = (total_costo_alimento / total_kilos) if total_kilos > 0 else 0

            df_conv_validas = df_view[df_view["Conversión_Graf"] > 0]
            conv_promedio = (
                (df_conv_validas["Bulto X 40 K"].sum() * 40000) / df_conv_validas["Huevos  Semana"].sum()
                if not df_conv_validas.empty and df_conv_validas["Huevos  Semana"].sum() > 0
                else 0
            )

            # --- 5 TARJETAS KPI ESTRATÉGICAS FINANCIERAS Y PRESUPUESTALES ---
            k1, k2, k3, k4, k5 = st.columns(5)

            with k1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">💵 Inversión Alimento</div>
                        <div class="kpi-value">${total_costo_alimento:,.0f}</div>
                        <div class="kpi-sub">{total_bultos:,.0f} Bultos ({total_kilos/1000:,.1f} Ton)</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k2:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">📦 Huevo Producido</div>
                        <div class="kpi-value">{total_huevos:,.0f}</div>
                        <div class="kpi-sub">Total en ventana selec.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k3:
                dif_huevo = costo_prom_huevo - 235.0
                sub_h = f"<span style='color:{'#27AE60' if dif_huevo <=0 else '#C0392B'}; font-weight:bold;'>Meta: $235 ({dif_huevo:+.1f})</span>"
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">🥚 Costo / Huevo</div>
                        <div class="kpi-value">${costo_prom_huevo:,.1f}</div>
                        <div class="kpi-sub">{sub_h}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k4:
                dif_kg = costo_prom_kg - 1600.0
                sub_k = f"<span style='color:{'#27AE60' if dif_kg <=0 else '#C0392B'}; font-weight:bold;'>Meta: $1,600 ({dif_kg:+.1f})</span>"
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">🌽 Costo / Kg Alimento</div>
                        <div class="kpi-value">${costo_prom_kg:,.1f}</div>
                        <div class="kpi-sub">{sub_k}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k5:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">🌾 Conversión Prom.</div>
                        <div class="kpi-value">{conv_promedio:.1f} g</div>
                        <div class="kpi-sub">Gramos Alimento / Huevo</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # --- SECCIÓN TRES GRÁFICOS ESPECIALIZADOS ---
            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            with st.expander("📈 Dashboard de Métricas Integradas de Alimento y Producción", expanded=True):
                df_plot = df_view.sort_values("Edad Sem.").copy()

                # 1. CONSUMO (TON) vs COSTO ($) vs % PDN REAL
                fig1 = make_subplots(specs=[[{"secondary_y": True}]])

                fig1.add_trace(
                    go.Bar(
                        x=df_plot["Edad Sem."],
                        y=df_plot["Toneladas"],
                        name="Consumo (Ton)",
                        marker_color="#E67E22",
                        opacity=0.65,
                        hovertemplate="<b>Semana: %{x}</b><br>Consumo: <b>%{y:,.2f} Ton</b><br>🌾 Fase: %{customdata}<extra></extra>",
                        customdata=df_plot["Fase de Alimento"],
                    ),
                    secondary_y=True,
                )

                fig1.add_trace(
                    go.Scatter(
                        x=df_plot["Edad Sem."],
                        y=df_plot["Costo Alimento Sem"],
                        mode="lines+markers",
                        name="Costo Alimento ($)",
                        line=dict(color="#D35400", width=2.5),
                        hovertemplate="<b>Semana: %{x}</b><br>Costo: <b>$%{y:,.0f}</b><br>🌾 Fase: %{customdata}<extra></extra>",
                        customdata=df_plot["Fase de Alimento"],
                    ),
                    secondary_y=False,
                )

                fig1.add_trace(
                    go.Scatter(
                        x=df_plot["Edad Sem."],
                        y=df_plot["% Pdn. Real"],
                        mode="lines+markers",
                        name="% Pdn. Real",
                        line=dict(color="#2980B9", width=2.5),
                        hovertemplate="<b>Semana: %{x}</b><br>Producción: <b>%{y:.1f}%</b><extra></extra>",
                    ),
                    secondary_y=True,
                )

                fig1.update_layout(
                    title={"text": "<b>1. CONSUMO (TON) / COSTO ALIMENTO ($) VS % PDN REAL</b>", "x": 0.5, "xanchor": "center"},
                    height=380,
                    margin=dict(t=50, b=25, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
                    hovermode="x unified",
                )
                fig1.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title_text="Edad Semanal")
                fig1.update_yaxes(title_text="Costo Alimento Semanal ($)", showgrid=True, gridcolor="rgba(128,128,128,0.15)", secondary_y=False)
                fig1.update_yaxes(title_text="Consumo (Ton) / % Pdn", showgrid=False, secondary_y=True)

                if ver_etiquetas:
                    fig1.update_traces(mode="lines+markers+text", texttemplate="%{y:.1f}%", textposition="top center", selector=dict(name="% Pdn. Real"))

                st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

                st.markdown("<hr style='margin:15px 0; border-color:rgba(211,84,0,0.15);'>", unsafe_allow_html=True)
                col_g2, col_g3 = st.columns(2)

                # 2. COSTO POR HUEVO VS COSTO KILO DE ALIMENTO (CON LÍNEAS METAS PRESUPUESTALES)
                with col_g2:
                    fig2 = make_subplots(specs=[[{"secondary_y": True}]])

                    fig2.add_trace(
                        go.Scatter(
                            x=df_plot["Edad Sem."],
                            y=df_plot["$ Huevo por alimento"],
                            mode="lines+markers",
                            name="Costo / Huevo ($)",
                            line=dict(color="#C0392B", width=2.5),
                            hovertemplate="<b>Semana: %{x}</b><br>Costo/Huevo: <b>$%{y:.1f}</b><br>🌾 Fase: %{customdata}<extra></extra>",
                            customdata=df_plot["Fase de Alimento"],
                        ),
                        secondary_y=False,
                    )

                    fig2.add_trace(
                        go.Scatter(
                            x=df_plot["Edad Sem."],
                            y=df_plot["Costo Kg Alimento"],
                            mode="lines+markers",
                            name="Costo Kg Alimento ($/kg)",
                            line=dict(color="#27AE60", width=2),
                            hovertemplate="<b>Semana: %{x}</b><br>Costo/Kg: <b>$%{y:,.1f}</b><br>🌾 Fase: %{customdata}<extra></extra>",
                            customdata=df_plot["Fase de Alimento"],
                        ),
                        secondary_y=True,
                    )

                    # LÍNEA META PRESUPUESTAL 1: $235 / HUEVO
                    fig2.add_shape(
                        type="line",
                        x0=df_plot["Edad Sem."].min(), x1=df_plot["Edad Sem."].max(),
                        y0=235, y1=235,
                        line=dict(color="#C0392B", width=1.5, dash="dash"),
                        xref="x", yref="y1"
                    )

                    # LÍNEA META PRESUPUESTAL 2: $1,600 / KG ALIMENTO
                    fig2.add_shape(
                        type="line",
                        x0=df_plot["Edad Sem."].min(), x1=df_plot["Edad Sem."].max(),
                        y0=1600, y1=1600,
                        line=dict(color="#27AE60", width=1.5, dash="dash"),
                        xref="x", yref="y2"
                    )

                    fig2.update_layout(
                        title={"text": "<b>2. COSTO HUEVO ($) VS COSTO KILO ALIMENTO ($/KG)</b>", "x": 0.5, "xanchor": "center"},
                        height=360,
                        margin=dict(t=50, b=25, l=10, r=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
                        hovermode="x unified",
                    )
                    fig2.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title_text="Edad Semanal")
                    fig2.update_yaxes(title_text="Costo / Huevo ($) [Meta $235]", showgrid=True, gridcolor="rgba(128,128,128,0.15)", secondary_y=False)
                    fig2.update_yaxes(title_text="Costo Kg ($) [Meta $1,600]", showgrid=False, secondary_y=True)

                    if ver_etiquetas:
                        fig2.update_traces(mode="lines+markers+text", texttemplate="$%{y:.1f}", textposition="top center", secondary_y=False)

                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

                # 3. CONSUMO AVE/DÍA (REAL VS TABLA) VS CONVERSIÓN
                with col_g3:
                    fig3 = make_subplots(specs=[[{"secondary_y": True}]])

                    fig3.add_trace(
                        go.Scatter(
                            x=df_plot["Edad Sem."],
                            y=df_plot["Gr.A.D Real"],
                            mode="lines+markers",
                            name="Gr.A.D Real (g)",
                            line=dict(color="#16A085", width=2.5),
                            hovertemplate="<b>Semana: %{x}</b><br>Gr.A.D Real: <b>%{y:.1f} g</b><extra></extra>",
                        ),
                        secondary_y=False,
                    )

                    if "Gr.A.D Tabla" in df_plot.columns and (df_plot["Gr.A.D Tabla"] > 0).any():
                        fig3.add_trace(
                            go.Scatter(
                                x=df_plot["Edad Sem."],
                                y=df_plot["Gr.A.D Tabla"],
                                mode="lines",
                                name="Gr.A.D Tabla (g)",
                                line=dict(color="#7F8C8D", width=2, dash="dot"),
                                hovertemplate="<b>Semana: %{x}</b><br>Gr.A.D Tabla: <b>%{y:.1f} g</b><extra></extra>",
                            ),
                            secondary_y=False,
                        )

                    df_plot_conv = df_plot[df_plot["Conversión_Graf"] > 0]
                    fig3.add_trace(
                        go.Scatter(
                            x=df_plot_conv["Edad Sem."],
                            y=df_plot_conv["Conversión_Graf"],
                            mode="lines+markers",
                            name="Conversión (g/Huevo)",
                            line=dict(color="#8E44AD", width=2, dash="dashdot"),
                            hovertemplate="<b>Semana: %{x}</b><br>Conversión: <b>%{y:.1f} g/Huevo</b><extra></extra>",
                        ),
                        secondary_y=True,
                    )

                    fig3.update_layout(
                        title={"text": "<b>3. CONSUMO AVE/DÍA (REAL VS TABLA) VS CONVERSIÓN</b>", "x": 0.5, "xanchor": "center"},
                        height=360,
                        margin=dict(t=50, b=25, l=10, r=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.28, xanchor="center", x=0.5),
                        hovermode="x unified",
                    )
                    fig3.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)", title_text="Edad Semanal")
                    fig3.update_yaxes(title_text="Consumo Gramos Ave/Día", showgrid=True, gridcolor="rgba(128,128,128,0.15)", secondary_y=False)
                    fig3.update_yaxes(title_text="Conversión (g/Huevo)", showgrid=False, secondary_y=True)

                    if ver_etiquetas:
                        fig3.update_traces(mode="lines+markers+text", texttemplate="%{y:.1f}g", textposition="top center", secondary_y=True)

                    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

            # --- SECCIÓN MATRIZ TABULAR DE AUDITORÍA ---
            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

            c_tit, c_mod = st.columns([2.5, 1])
            with c_tit:
                st.markdown("### 📋 Matriz Detallada de Costos Semanales")
            with c_mod:
                modo_vista = st.selectbox(
                    "👁️ Modo de Vista de Tabla",
                    ["Tabla HTML AgroTech", "Visor Tabular Interactivo"],
                    index=0,
                )

            cols_financieras = [
                "Final Sem",
                "Edad Sem.",
                "Saldo de Aves",
                "Fase de Alimento",
                "Observaciones",
                "Gr.A.D Real",
                "Bulto X 40 K",
                "Toneladas",
                "Huevos  Semana",
                "% Pdn. Real",
                "Conversión",
                "Costo Kg Alimento",
                "Costo Alimento Sem",
                "$ Huevo por alimento",
            ]

            cols_disp = [c for c in cols_financieras if c in df_view.columns]
            tabla_render = df_view[cols_disp].sort_values("Edad Sem.", ascending=False).fillna(0).copy()

            if "Final Sem" in tabla_render.columns:
                tabla_render["Final Sem"] = pd.to_datetime(
                    tabla_render["Final Sem"], errors="coerce"
                ).dt.strftime("%d/%m/%y")

            formatos_activos = {
                k: v for k, v in formatos.items() if k in tabla_render.columns
            }

            if modo_vista == "Tabla HTML AgroTech":

                def render_custom_table_costos(df_data):
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

                render_custom_table_costos(tabla_render)

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