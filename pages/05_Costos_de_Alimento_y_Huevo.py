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
    "Mort": "{:.0f}",
    "Gr.A.D Real": "{:.1f}",
    "Gr.A.D Tabla": "{:.1f}",
    "Bulto X 40 K": "{:,.1f}",
    "Peso Real": "{:.1f}",
    "% Pdn. Real": "{:.1f}%",
    "Conversión": "{:.1f} g",
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

# --- 2. ESTILO CSS AGROTECH ORANGE ADAPTABLE ---
st.markdown(
    """
    <style>
    [data-testid="stHeader"] { background-color: transparent !important; }

    /* BANNER PRINCIPAL NARANJA CORPORATIVO RESPONSIVE */
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

    /* PANEL DE FILTROS Y CONTROLES ADAPTABLES */
    .filter-panel {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(211, 84, 0, 0.25);
        border-radius: 12px;
        padding: 14px 18px 10px 18px;
        margin-bottom: 20px;
    }

    /* TARJETAS KPI FINANCIERAS */
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

    /* RESTICCION DE SEGURIDAD */
    .security-lock-card {
        background-color: var(--secondary-background-color);
        border: 2px dashed #C0392B;
        border-radius: 16px;
        padding: 40px;
        text-align: center;
        margin: 30px 0;
    }

    /* TABLA NATIVA AGROTECH */
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

            if "Fase de Alimento" in df.columns:
                df["Fase de Alimento"] = df["Fase de Alimento"].fillna("Sin especf.").astype(str)

            num_cols = [
                "Edad Sem.",
                "Saldo de Aves",
                "Mort",
                "Bulto X 40 K",
                "Gr.A.D Real",
                "Gr.A.D Tabla",
                "Peso Real",
                "Huevos  Semana",
                "% Pdn. Real",
                "Costo Alimento Sem",
                "$ Huevo por alimento",
            ]
            for col in [c for c in num_cols if c in df.columns]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception as e:
            st.error(f"Error Crítico al cargar datos de costos: {e}")
            return None
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
    # --- PANTALLA DE BLOQUEO PARA USUARIOS NO ADMINISTRADORES ---
    st.markdown(
        """
        <div class="security-lock-card">
            <h1 style="font-size: 3rem; margin: 0;">🔒</h1>
            <h2 style="color: #C0392B; margin-top: 10px;">Acceso Restringido a Información Financiera</h2>
            <p style="font-size: 1.1rem; opacity: 0.85; max-width: 600px; margin: 15px auto;">
                El módulo de <b>Costos de Alimento y Huevo</b> contiene datos confidenciales sobre estructura de precios y margen de rentabilidad.
            </p>
            <p style="font-size: 0.95rem; opacity: 0.7;">
                Consulte con la Dirección Financiera o inicie sesión con una cuenta autorizada de rol <b>ADMIN</b> para acceder.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # --- PANTALLA COMPLETA PARA ROL ADMIN ---
    if df_orig is not None:
        # Filtramos lotes activos
        df_activos = df_orig[df_orig["LOTE"] == df_orig["NUM_GALPON"]].copy()

        # --- PANEL DE FILTROS ---
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        f1, f2, f3 = st.columns(3)

        with f1:
            granjas_disp = sorted(df_activos["GRANJA"].unique())
            granja_sel = st.selectbox("MAP Selecciona Granja:", granjas_disp)

        df_g = df_activos[df_activos["GRANJA"] == granja_sel]

        with f2:
            lotes_disp = sorted(df_g["LOTE"].unique())
            lote_sel = st.selectbox("📦 Selecciona Lote:", lotes_disp)

        df_l = df_g[df_g["LOTE"] == lote_sel].copy()

        with f3:
            casas_disp = sorted([str(x) for x in df_l["Observaciones"].unique() if pd.notna(x)])
            casa_sel = st.multiselect("🥣 Casa Nutricional / Observaciones:", casas_disp, default=casas_disp)

        if casa_sel:
            df_l = df_l[df_l["Observaciones"].isin(casa_sel)]

        st.markdown("<hr style='margin:10px 0; border-color:rgba(211,84,0,0.15);'>", unsafe_allow_html=True)
        ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas en gráficos", value=False)
        st.markdown("</div>", unsafe_allow_html=True)

        if df_l.empty:
            st.warning("⚠️ No hay información de costos disponible para la selección actual.")
        else:
            # RANGO DE EDAD
            max_e = int(df_l["Edad Sem."].max())
            min_e = int(df_l["Edad Sem."].min())
            rango_edad = st.slider(
                "⏳ Ventana de Análisis (Semanas de Edad):",
                min_e,
                max_e,
                (min_e, max_e),
            )

            df_view = df_l[df_l["Edad Sem."].between(rango_edad[0], rango_edad[1])].copy()

            # CÁLCULOS CLAVE
            df_view["Conversión"] = (
                (df_view["Bulto X 40 K"] * 40000)
                / df_view["Huevos  Semana"].replace(0, 1)
            ).round(1)

            if "Final Sem" in df_view.columns:
                df_view["Fecha_Fmt"] = pd.to_datetime(
                    df_view["Final Sem"], errors="coerce"
                ).dt.strftime("%d/%b/%Y")
            else:
                df_view["Fecha_Fmt"] = "N/A"

            total_costo_alimento = df_view["Costo Alimento Sem"].sum()
            total_huevos = df_view["Huevos  Semana"].sum()
            costo_prom_huevo = (
                total_costo_alimento / total_huevos if total_huevos > 0 else 0
            )
            conv_promedio = (
                (df_view["Bulto X 40 K"].sum() * 40000) / total_huevos
                if total_huevos > 0
                else 0
            )
            total_bultos = df_view["Bulto X 40 K"].sum()

            # --- KPIS ESTRATÉGICOS FINANCIEROS ---
            k1, k2, k3, k4 = st.columns(4)

            with k1:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">💵 Inversión Total Alimento</div>
                        <div class="kpi-value">${total_costo_alimento:,.0f}</div>
                        <div class="kpi-sub">{total_bultos:,.0f} Bultos (40kg)</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k2:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">🥚 Costo Promedio / Huevo</div>
                        <div class="kpi-value">${costo_prom_huevo:,.1f}</div>
                        <div class="kpi-sub">Solo alimento consumido</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k3:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">🌾 Conversión Promedio</div>
                        <div class="kpi-value">{conv_promedio:.1f} g</div>
                        <div class="kpi-sub">Gramos Alimento / Huevo</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with k4:
                st.markdown(
                    f"""
                    <div class="kpi-card">
                        <div class="kpi-title">📦 Total Huevo Producido</div>
                        <div class="kpi-value">{total_huevos:,.0f}</div>
                        <div class="kpi-sub">Acumulado en ventana selec.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            # --- SECCIÓN GRÁFICOS FINANCIEROS ---
            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            with st.expander("📈 Evolución de Costos e Inversión Nutricional", expanded=True):
                g1, g2 = st.columns(2)

                cdata = np.stack(
                    (df_view["Fecha_Fmt"], df_view["Fase de Alimento"]), axis=-1
                )

                with g1:
                    fig1 = px.line(
                        df_view.sort_values("Edad Sem."),
                        x="Edad Sem.",
                        y="Costo Alimento Sem",
                        markers=True,
                        title="<b>COSTO SEMANAL DE ALIMENTO ($)</b>",
                    )
                    fig1.update_traces(
                        line_color="#D35400",
                        hovertemplate=(
                            "<b>Semana: %{x}</b> (📅 %{customdata[0]})<br>"
                            "🌾 <b>Fase:</b> %{customdata[1]}<br>"
                            "Costo Semanal: <b>$%{y:,.0f}</b><extra></extra>"
                        ),
                        customdata=cdata,
                    )
                    fig1.update_layout(
                        title={"x": 0.5, "xanchor": "center"},
                        height=350,
                        margin=dict(t=50, b=25, l=10, r=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    fig1.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
                    fig1.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
                    if ver_etiquetas:
                        fig1.update_traces(
                            mode="lines+markers+text",
                            texttemplate="$%{y:,.0f}",
                            textposition="top center",
                        )

                    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

                with g2:
                    fig2 = px.line(
                        df_view.sort_values("Edad Sem."),
                        x="Edad Sem.",
                        y="$ Huevo por alimento",
                        markers=True,
                        title="<b>COSTO POR HUEVO ($/HUEVO)</b>",
                    )
                    fig2.update_traces(
                        line_color="#E67E22",
                        hovertemplate=(
                            "<b>Semana: %{x}</b> (📅 %{customdata[0]})<br>"
                            "🌾 <b>Fase:</b> %{customdata[1]}<br>"
                            "Costo/Huevo: <b>$%{y:.1f}</b><extra></extra>"
                        ),
                        customdata=cdata,
                    )
                    fig2.update_layout(
                        title={"x": 0.5, "xanchor": "center"},
                        height=350,
                        margin=dict(t=50, b=25, l=10, r=10),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                    )
                    fig2.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
                    fig2.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
                    if ver_etiquetas:
                        fig2.update_traces(
                            mode="lines+markers+text",
                            texttemplate="$%{y:.1f}",
                            textposition="top center",
                        )

                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

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
                "Huevos  Semana",
                "% Pdn. Real",
                "Conversión",
                "Costo Alimento Sem",
                "$ Huevo por alimento",
            ]

            cols_disp = [c for c in cols_financieras if c in df_view.columns]
            tabla_render = df_view[cols_disp].sort_values("Edad Sem.", ascending=False).fillna(0).copy()

            if "Final Sem" in tabla_render.columns:
                tabla_render["Final Sem"] = pd.to_datetime(
                    tabla_render["Final Sem"]
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