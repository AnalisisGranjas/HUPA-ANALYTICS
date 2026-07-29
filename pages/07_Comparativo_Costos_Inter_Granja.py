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
    "Suma Mort + Sel": "{:.1f}",
    "% Mort + Sel Acum.": "{:.1f}%",
    "Bulto X 40 K": "{:,.1f}",
    "Gr.A.D Real": "{:.1f}",
    "Conv": "{:.1f} g",
    "Costo Alimento Sem": "${:,.0f}",
    "$ Huevo por alimento": "${:,.1f}",
}

# --- SEGURIDAD Y CONFIGURACIÓN ---
if "auth" not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

st.set_page_config(
    page_title="HUPA | Comparativo Inter-Granja (Costos)",
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

# --- 2. ESTILO CSS AGROTECH ORANGE CON POPOVERS HOMOGÉNEOS ---
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

    /* PANEL DE FILTROS */
    .filter-panel {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(211, 84, 0, 0.25);
        border-radius: 12px;
        padding: 14px 18px 10px 18px;
        margin-bottom: 20px;
    }

    /* ESTILO DE POPOVER LIMPIO IGUAL A SELECTBOX */
    div[data-testid="stPopover"] {
        width: 100% !important;
    }
    div[data-testid="stPopover"] > button {
        width: 100% !important;
        background-color: rgba(128, 128, 128, 0.08) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 8px !important;
        color: var(--text-color) !important;
        height: 40px !important;
        min-height: 40px !important;
        font-size: 0.88rem !important;
        font-weight: 400 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        padding: 0 12px !important;
        box-shadow: none !important;
    }
    div[data-testid="stPopover"] > button:hover {
        border-color: #D35400 !important;
        color: #D35400 !important;
    }

    /* KPIS FINANCIEROS */
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
            cols_numeric = [
                "Edad Sem.",
                "Saldo de Aves",
                "Huevos  Semana",
                "Mort",
                "Suma Mort + Sel",
                "% Mort + Sel Acum.",
                "Bulto X 40 K",
                "Gr.A.D Real",
                "Conv",
                "Costo Alimento Sem",
                "$ Huevo por alimento",
            ]
            for col in [c for c in cols_numeric if c in df.columns]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception as e:
            st.error(f"Error Crítico al cargar datos comparativos de costos: {e}")
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
            <h1>Auditoría y Comparativo Inter-Granja (Costos Gerenciales)</h1>
            <p>Benchmarking de $/Huevo, Inversión en Alimento y Conversión entre múltiples unidades</p>
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
                Este módulo de <b>Auditoría y Comparativo de Costos</b> contiene análisis confidenciales de rentabilidad.
            </p>
            <p style="font-size: 0.95rem; opacity: 0.7;">
                Inicie sesión con una cuenta de rol <b>ADMIN</b> para acceder a esta información gerencial.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    if df_orig is not None:
        # Lotes consolidados
        df_activos = df_orig[df_orig["LOTE"] == df_orig["NUM_GALPON"]].copy()

        # --- PANEL DE FILTROS MULTI-SELECCIÓN LIMPIOS (POPOVER) ---
        st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
        f_col1, f_col2, f_col3 = st.columns(3)

        granjas_totales = sorted(df_activos["GRANJA"].unique())

        # 1. POPOVER MULTI-GRANJA
        with f_col1:
            st.markdown("<label style='font-size:14px; font-weight:400; margin-bottom:4px; display:block;'>🗺️ 1. Granjas a Comparar:</label>", unsafe_allow_html=True)
            
            # Estado por defecto
            for g in granjas_totales:
                if f"chk_gr_{g}" not in st.session_state:
                    st.session_state[f"chk_gr_{g}"] = True

            granjas_sel = [g for g in granjas_totales if st.session_state.get(f"chk_gr_{g}", True)]
            
            with st.popover(f"Granjas Seleccionadas ({len(granjas_sel)}/{len(granjas_totales)})", use_container_width=True):
                b1, b2 = st.columns(2)
                if b1.button("Marcar todo", key="btn_gr_all"):
                    for g in granjas_totales: st.session_state[f"chk_gr_{g}"] = True
                    st.rerun()
                if b2.button("Desmarcar", key="btn_gr_none"):
                    for g in granjas_totales: st.session_state[f"chk_gr_{g}"] = False
                    st.rerun()

                granjas_sel = [
                    g for g in granjas_totales
                    if st.checkbox(f"{g}", value=st.session_state.get(f"chk_gr_{g}", True), key=f"chk_gr_{g}")
                ]

        # Data filtrada por Granjas
        df_g = df_activos[df_activos["GRANJA"].isin(granjas_sel)].copy()
        lotes_totales = sorted(df_g["LOTE"].unique())

        # 2. POPOVER MULTI-LOTE
        with f_col2:
            st.markdown("<label style='font-size:14px; font-weight:400; margin-bottom:4px; display:block;'>📦 2. Lotes Biológicos:</label>", unsafe_allow_html=True)
            
            for lt in lotes_totales:
                if f"chk_lt_{lt}" not in st.session_state:
                    st.session_state[f"chk_lt_{lt}"] = True

            lotes_sel = [lt for lt in lotes_totales if st.session_state.get(f"chk_lt_{lt}", True)]

            with st.popover(f"Lotes Seleccionados ({len(lotes_sel)}/{len(lotes_totales)})", use_container_width=True):
                bl1, bl2 = st.columns(2)
                if bl1.button("Marcar todo", key="btn_lt_all"):
                    for lt in lotes_totales: st.session_state[f"chk_lt_{lt}"] = True
                    st.rerun()
                if bl2.button("Desmarcar", key="btn_lt_none"):
                    for lt in lotes_totales: st.session_state[f"chk_lt_{lt}"] = False
                    st.rerun()

                lotes_sel = [
                    lt for lt in lotes_totales
                    if st.checkbox(f"Lote {lt}", value=st.session_state.get(f"chk_lt_{lt}", True), key=f"chk_lt_{lt}")
                ]

        # Data filtrada por Lotes
        df_l = df_g[df_g["LOTE"].isin(lotes_sel)].copy()
        casas_totales = sorted([str(x) for x in df_l["Observaciones"].unique() if pd.notna(x)])

        # 3. POPOVER CASA NUTRICIONAL
        with f_col3:
            st.markdown("<label style='font-size:14px; font-weight:400; margin-bottom:4px; display:block;'>🥣 3. Casa Nutricional:</label>", unsafe_allow_html=True)
            
            for cs in casas_totales:
                if f"chk_cs_{cs}" not in st.session_state:
                    st.session_state[f"chk_cs_{cs}"] = True

            casa_sel = [cs for cs in casas_totales if st.session_state.get(f"chk_cs_{cs}", True)]

            with st.popover(f"Casas ({len(casa_sel)}/{len(casas_totales)})", use_container_width=True):
                bc1, bc2 = st.columns(2)
                if bc1.button("Marcar todo", key="btn_cs_all"):
                    for cs in casas_totales: st.session_state[f"chk_cs_{cs}"] = True
                    st.rerun()
                if bc2.button("Desmarcar", key="btn_cs_none"):
                    for cs in casas_totales: st.session_state[f"chk_cs_{cs}"] = False
                    st.rerun()

                casa_sel = [
                    cs for cs in casas_totales
                    if st.checkbox(f"{cs}", value=st.session_state.get(f"chk_cs_{cs}", True), key=f"chk_cs_{cs}")
                ]

        st.markdown("<hr style='margin:10px 0; border-color:rgba(211,84,0,0.15);'>", unsafe_allow_html=True)
        ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas en gráficos", value=False)
        st.markdown("</div>", unsafe_allow_html=True)

        if not granjas_sel or not lotes_sel:
            st.info("💡 Por favor selecciona al menos una granja y un lote en los filtros de arriba para realizar el comparativo.")
        else:
            df_auditoria = df_l[df_l["Observaciones"].isin(casa_sel)].copy()

            if df_auditoria.empty:
                st.warning("⚠️ No hay información de costos para la combinación de filtros seleccionada.")
            else:
                # RANGO DE EDAD
                max_e = int(df_auditoria["Edad Sem."].max())
                min_e = int(df_auditoria["Edad Sem."].min())
                val_ini = max(min_e, max_e - 6)
                rango_edad = st.slider(
                    "⏳ Ventana de Análisis Comparativo (Semanas de Edad Técnica):",
                    min_e,
                    max_e,
                    (val_ini, max_e),
                )

                df_view = df_auditoria[df_auditoria["Edad Sem."].between(rango_edad[0], rango_edad[1])].copy()

                df_view["Conv"] = (
                    (df_view["Bulto X 40 K"] * 40000)
                    / df_view["Huevos  Semana"].replace(0, 1)
                ).round(1)

                if "Final Sem" in df_view.columns:
                    df_view["Fecha_Fmt"] = pd.to_datetime(
                        df_view["Final Sem"], errors="coerce"
                    ).dt.strftime("%d/%b/%Y")
                else:
                    df_view["Fecha_Fmt"] = "N/A"

                df_view["Identificador"] = df_view["GRANJA"] + " - Lote " + df_view["LOTE"].astype(str)

                # KPIS RESUMEN
                total_huevos = df_view["Huevos  Semana"].sum()
                total_costo = df_view["Costo Alimento Sem"].sum()
                costo_huevo_prom = total_costo / total_huevos if total_huevos > 0 else 0
                total_bultos = df_view["Bulto X 40 K"].sum()
                conv_ponderada = (total_bultos * 40000) / total_huevos if total_huevos > 0 else 0

                st.markdown("### 🏆 KPIs Resumen de Benchmarking Gerencial")
                k1, k2, k3, k4 = st.columns(4)

                with k1:
                    st.markdown(f'<div class="kpi-card"><div class="kpi-title">🌾 Total Inversión Alimento</div><div class="kpi-value">${total_costo:,.0f}</div><div class="kpi-sub">{total_bultos:,.0f} Bultos</div></div>', unsafe_allow_html=True)
                with k2:
                    st.markdown(f'<div class="kpi-card"><div class="kpi-title">🥚 Costo Promedio / Huevo ($/H)</div><div class="kpi-value">${costo_huevo_prom:.1f}</div><div class="kpi-sub">Solo alimento</div></div>', unsafe_allow_html=True)
                with k3:
                    st.markdown(f'<div class="kpi-card"><div class="kpi-title">🥣 Conversión Ponderada</div><div class="kpi-value">{conv_ponderada:.1f} g</div><div class="kpi-sub">Alimento / Huevo</div></div>', unsafe_allow_html=True)
                with k4:
                    st.markdown(f'<div class="kpi-card"><div class="kpi-title">📦 Lotes Analizados</div><div class="kpi-value">{df_view["Identificador"].nunique()}</div><div class="kpi-sub">De {df_view["GRANJA"].nunique()} Granjas</div></div>', unsafe_allow_html=True)

                # --- SECCIÓN GRÁFICOS COMPARATIVOS ---
                st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
                with st.expander("📈 Benchmarking Financiero Semanal Comparativo", expanded=True):
                    g1, g2 = st.columns(2)

                    cdata = np.stack(
                        (df_view["Fecha_Fmt"], df_view["Identificador"], df_view["Observaciones"]), axis=-1
                    )

                    mode_graf = "lines+markers+text" if ver_etiquetas else "lines+markers"

                    with g1:
                        fig1 = px.line(
                            df_view.sort_values(["Identificador", "Edad Sem."]),
                            x="Edad Sem.",
                            y="$ Huevo por alimento",
                            color="Identificador",
                            markers=True,
                            title="<b>COSTO POR HUEVO ($/HUEVO) COMPARATIVO</b>",
                        )
                        fig1.update_traces(
                            mode=mode_graf,
                            texttemplate="$%{y:.1f}" if ver_etiquetas else None,
                            textposition="top center",
                            hovertemplate=(
                                "<b>%{customdata[1]}</b><br>📅 Semana: %{x} (%{customdata[0]})<br>"
                                "🥣 Casa: %{customdata[2]}<br>Costo/Huevo: <b>$%{y:.1f}</b><extra></extra>"
                            ),
                            customdata=cdata
                        )
                        fig1.update_layout(
                            title={"x": 0.5, "xanchor": "center"},
                            height=380,
                            margin=dict(t=50, b=25, l=10, r=10),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5),
                        )
                        fig1.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
                        fig1.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")

                        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

                    with g2:
                        fig2 = px.line(
                            df_view.sort_values(["Identificador", "Edad Sem."]),
                            x="Edad Sem.",
                            y="Conv",
                            color="Identificador",
                            markers=True,
                            title="<b>CONVERSIÓN ALIMENTICIA (G ALIMENTO / HUEVO)</b>",
                        )
                        fig2.update_traces(
                            mode=mode_graf,
                            texttemplate="%{y:.1f}g" if ver_etiquetas else None,
                            textposition="top center",
                            hovertemplate=(
                                "<b>%{customdata[1]}</b><br>📅 Semana: %{x} (%{customdata[0]})<br>"
                                "🥣 Casa: %{customdata[2]}<br>Conversión: <b>%{y:.1f}g</b><extra></extra>"
                            ),
                            customdata=cdata
                        )
                        fig2.update_layout(
                            title={"x": 0.5, "xanchor": "center"},
                            height=380,
                            margin=dict(t=50, b=25, l=10, r=10),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5),
                        )
                        fig2.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
                        fig2.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")

                        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

                # --- SECCIÓN TABLAS INDIVIDUALES POR LOTE EN PESTAÑAS ---
                st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

                st.markdown("### 📋 Matrices de Auditoría Individual por Lote")
                
                c_tit, c_mod = st.columns([2.5, 1])
                with c_tit:
                    st.markdown("<p style='opacity:0.8; font-size:0.9rem;'>Cada pestaña representa un lote auditado individualmente con sus valores exactos.</p>", unsafe_allow_html=True)
                with c_mod:
                    modo_vista = st.selectbox(
                        "👁️ Modo de Vista de Tabla",
                        ["Tabla HTML AgroTech", "Visor Tabular Interactivo"],
                        index=0,
                        key="view_mod_costos_ind"
                    )

                lotes_identificados = sorted(df_view["Identificador"].unique())
                tabs_lotes = st.tabs([f"📦 {item}" for item in lotes_identificados])

                cols_auditoria = [
                    "Final Sem",
                    "Edad Sem.",
                    "Observaciones",
                    "Fase de Alimento",
                    "Saldo de Aves",
                    "Mort",
                    "Suma Mort + Sel",
                    "% Mort + Sel Acum.",
                    "Bulto X 40 K",
                    "Gr.A.D Real",
                    "Huevos  Semana",
                    "Conv",
                    "Costo Alimento Sem",
                    "$ Huevo por alimento",
                ]

                for i, tab in enumerate(tabs_lotes):
                    with tab:
                        id_lote = lotes_identificados[i]
                        df_tab = df_view[df_view["Identificador"] == id_lote].sort_values("Edad Sem.", ascending=False).copy()

                        cols_disp = [c for c in cols_auditoria if c in df_tab.columns]
                        tabla_render = df_tab[cols_disp].fillna(0).copy()

                        if "Final Sem" in tabla_render.columns:
                            tabla_render["Final Sem"] = pd.to_datetime(
                                tabla_render["Final Sem"]
                            ).dt.strftime("%d/%m/%y")

                        formatos_activos = {
                            k: v for k, v in formatos.items() if k in tabla_render.columns
                        }

                        if modo_vista == "Tabla HTML AgroTech":

                            def render_custom_table_lote(df_data):
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

                                        if col == "$ Huevo por alimento" and pd.notnull(val):
                                            try:
                                                n_v = float(val)
                                                if n_v > costo_huevo_prom:
                                                    style = "background-color:rgba(192,57,43,0.18); color:#C0392B; font-weight:bold;"
                                                else:
                                                    style = "background-color:rgba(17,122,101,0.18); color:#117A65; font-weight:bold;"
                                            except: pass

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

                            render_custom_table_lote(tabla_render)

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

# FOOTER
st.divider()
st.markdown(
    """
    <div class='footer-tematico' style='margin-top: 20px; padding: 20px 0; text-align: center; opacity: 0.6;'>
        <div><b>HUPA | División Avícola</b> - Análisis de Datos para la Excelencia Productiva</div>
    </div>
    """,
    unsafe_allow_html=True,
)