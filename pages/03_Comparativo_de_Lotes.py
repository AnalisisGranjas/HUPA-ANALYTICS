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
    "Huevos Semana": "{:,.0f}",
    "Edad Sem.": "{:.0f}",
    "Mort": "{:.0f}",
    "% Mort + Sel Acum.": "{:.1f}%",
    "%Mort+Sel Acum. Tab": "{:.1f}%",
    "Gr.A.D Real": "{:.1f}",
    "Gr.A.D Tabla": "{:.1f}",
    "% Unif": "{:.1f}%",
    "Peso Real": "{:.1f}",
    "Peso Tab": "{:.1f}",
    "% Pdn. Real": "{:.1f}%",
    "% Pdn. Tabla": "{:.1f}%",
    "H.A.A. Real": "{:.1f}",
    "H.A.A. Tabla": "{:.1f}",
    "Grande": "{:.1f}%",
    "Mediano": "{:.1f}%",
    "Pequeño": "{:.1f}%",
    "Segunda": "{:.1f}%",
    "Conversión": "{:.1f} g",
    "Dif Pdn": "{:+.1f}%",
    "Dif GAD": "{:+.1f}",
    "Dif HAA": "{:+.1f}",
    "Dif Peso": "{:+.1f}",
    "Dif Mort": "{:+.1f}%",
    "Costo Alimento Sem": "${:,.0f}",
    "$ Huevo por alimento": "${:,.1f}",
}

# --- SEGURIDAD Y CONFIGURACIÓN ---
if "auth" not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

st.set_page_config(
    page_title="HUPA | Comparativo de Lotes",
    page_icon="📊",
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

    /* PANEL DE FILTROS ADAPTABLE */
    .filter-panel {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(211, 84, 0, 0.25);
        border-radius: 12px;
        padding: 14px 18px 10px 18px;
        margin-bottom: 20px;
    }

    .guide-box {
        background-color: var(--secondary-background-color);
        padding: 10px 14px;
        border: 1px dashed rgba(211, 84, 0, 0.4);
        border-radius: 8px;
        margin-top: 8px;
        font-size: 0.84rem;
        color: var(--text-color);
        opacity: 0.9;
    }

    /* BADGE DE GENÉTICA DESTACADO EN CADA TABLA */
    .genetica-badge {
        background: rgba(211, 84, 0, 0.15);
        color: #D35400;
        border: 1px solid #D35400;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
        margin-left: 8px;
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
            if "Observaciones" in df.columns:
                df["Observaciones"] = (
                    df["Observaciones"]
                    .astype(str)
                    .replace("nan", "Sin especificar")
                )

            if "Fase de Alimento" in df.columns:
                df["Fase de Alimento"] = df["Fase de Alimento"].fillna("Sin especf.").astype(str)

            num_cols = [
                "Edad Sem.",
                "Saldo de Aves",
                "Mort",
                "Suma Mort + Sel",
                "% Mort + Sel Acum.",
                "%Mort+Sel Acum. Tab",
                "Bulto X 40 K",
                "Gr.A.D Real",
                "Gr.A.D Tabla",
                "Peso Real",
                "Peso Tab",
                "Huevos  Semana",
                "% Pdn. Real",
                "% Pdn. Tabla",
                "H.A.A. Real",
                "H.A.A. Tabla",
                "Jumbo",
                "Extra",
                "AA",
                "A",
                "B",
                "C",
                "Alt Cáscara",
                "Alt. Color",
                "Picado",
                "Roto",
                "Costo Alimento Sem",
                "$ Huevo por alimento",
                "% Unif",
            ]
            for col in [c for c in num_cols if c in df.columns]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            return None
    return None


df_orig = load_data()

# --- SIDEBAR DE USUARIO Y VALIDACIÓN DE ROL ADMI ---
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
            <h1>Comparativo de Desempeño entre Lotes</h1>
            <p>Benchmarking operativo biológico, clasificación comercial y auditoría cruzada</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_orig is not None:
    with st.expander(
        "📌 Protocolo de Benchmarking Operativo e Instrucciones", expanded=False
    ):
        st.markdown(
            """
            En la producción avícola, la verdadera eficiencia se mide a través del **Benchmarking Operativo**, contrastando el desempeño de diferentes granjas, edades y genéticas bajo un mismo prisma técnico.
            
            * **Detección de Brechas:** Identifique si las caídas de postura son generales (clima/alimento) o particulares de un galpón.
            * **Auditoría de Manejo:** Evalúe diferencias de iluminación, agua y nutrición entre lotes pares.
            """
        )

    df_activos = df_orig[df_orig["LOTE"] == df_orig["NUM_GALPON"]].copy()
    df_activos["ID_INTERNO"] = (
        df_activos["GRANJA"] + " - Lote " + df_activos["LOTE"].astype(str)
    )

    # --- PANEL DE FILTROS CON "SELECCIONAR TODO / DESMARCAR TODO" ---
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    # 1. FILTRO EMPRESAS
    empresas_disp = sorted(df_activos["RAZON_SOCIAL"].unique())
    with c1:
        with st.popover("🏢 1. Seleccionar Empresas", use_container_width=True):
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Marcar todo", key="btn_emp_all"):
                for emp in empresas_disp:
                    st.session_state[f"chk_emp_{emp}"] = True
                st.rerun()
            if col_b2.button("Desmarcar", key="btn_emp_none"):
                for emp in empresas_disp:
                    st.session_state[f"chk_emp_{emp}"] = False
                st.rerun()

            empresa_sel = [
                emp for emp in empresas_disp
                if st.checkbox(str(emp), value=st.session_state.get(f"chk_emp_{emp}", False), key=f"chk_emp_{emp}")
            ]

    # 2. FILTRO GRANJAS
    df_g = (
        df_activos[df_activos["RAZON_SOCIAL"].isin(empresa_sel)]
        if empresa_sel
        else df_activos
    )
    granjas_disp = sorted(df_g["GRANJA"].unique())
    with c2:
        with st.popover(f"🗺️ 2. Granjas ({len(granjas_disp)})", use_container_width=True):
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Marcar todo", key="btn_gr_all"):
                for gr in granjas_disp:
                    st.session_state[f"chk_gr_{gr}"] = True
                st.rerun()
            if col_b2.button("Desmarcar", key="btn_gr_none"):
                for gr in granjas_disp:
                    st.session_state[f"chk_gr_{gr}"] = False
                st.rerun()

            granja_sel = [
                gr for gr in granjas_disp
                if st.checkbox(str(gr), value=st.session_state.get(f"chk_gr_{gr}", False), key=f"chk_gr_{gr}")
            ]

    # 3. FILTRO LOTES
    df_l = df_g[df_g["GRANJA"].isin(granja_sel)] if granja_sel else df_g
    lotes_disp = sorted(df_l["LOTE"].unique())
    with c3:
        with st.popover(f"📦 3. Lotes ({len(lotes_disp)})", use_container_width=True):
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Marcar todo", key="btn_lt_all"):
                for lt in lotes_disp:
                    st.session_state[f"chk_lt_{lt}"] = True
                st.rerun()
            if col_b2.button("Desmarcar", key="btn_lt_none"):
                for lt in lotes_disp:
                    st.session_state[f"chk_lt_{lt}"] = False
                st.rerun()

            lote_sel = [
                lt for lt in lotes_disp
                if st.checkbox(f"Lote {lt}", value=st.session_state.get(f"chk_lt_{lt}", False), key=f"chk_lt_{lt}")
            ]

    # 4. FILTRO CASA NUTRICIONAL
    opciones_casa = (
        sorted([str(x) for x in df_l["Observaciones"].unique() if pd.notna(x)])
        if not df_l.empty
        else []
    )
    with c4:
        with st.popover("🥣 4. Casa Nutricional", use_container_width=True):
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Marcar todo", key="btn_cs_all"):
                for cs in opciones_casa:
                    st.session_state[f"chk_cs_{cs}"] = True
                st.rerun()
            if col_b2.button("Desmarcar", key="btn_cs_none"):
                for cs in opciones_casa:
                    st.session_state[f"chk_cs_{cs}"] = False
                st.rerun()

            casa_sel = [
                cs for cs in opciones_casa
                if st.checkbox(str(cs), value=st.session_state.get(f"chk_cs_{cs}", False), key=f"chk_cs_{cs}")
            ]

    st.markdown("<hr style='margin:10px 0; border-color:rgba(211,84,0,0.15);'>", unsafe_allow_html=True)
    cx1, cx2 = st.columns(2)
    with cx1:
        ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas de datos", value=False)
    with cx2:
        ver_tabla_line = st.toggle(
            "📉 Mostrar línea de Meta Ideal (Tabla)", value=True
        )

    st.markdown("</div>", unsafe_allow_html=True)

    if not lote_sel or not granja_sel or not empresa_sel:
        st.info(
            "💡 Despliega los desplegables arriba (**Empresas**, **Granja(s)** y **Lote(s)**) y usa el botón **'Marcar todo'** o marca las casillas que deseas comparar."
        )
    else:
        df_f = df_l[df_l["LOTE"].isin(lote_sel)].copy()
        if casa_sel:
            df_f = df_f[df_f["Observaciones"].isin(casa_sel)]

        # FILTROS AVANZADOS Y SLIDER
        with st.expander("🛠️ Ajustes Avanzados de Filtro", expanded=False):
            fa1, fa2 = st.columns(2)
            with fa1:
                genetica_sel = st.multiselect(
                    "🧬 Línea Genética:",
                    sorted(df_f["LINEA_AVES"].unique()),
                    default=df_f["LINEA_AVES"].unique(),
                )
            with fa2:
                min_e = int(df_f["Edad Sem."].min()) if not df_f.empty else 18
                max_e = int(df_f["Edad Sem."].max()) if not df_f.empty else 100
                rango_edad = st.slider(
                    "⏳ Rango de Edad (Semanas):",
                    min_e,
                    max_e,
                    (max(min_e, max_e - 6), max_e),
                )

        df_final = df_f[
            (df_f["LINEA_AVES"].isin(genetica_sel))
            & (df_f["Edad Sem."].between(rango_edad[0], rango_edad[1]))
        ].copy()

        # FORMATEO DE FECHA PARA TOOLTIP
        if "Final Sem" in df_final.columns:
            df_final["Fecha_Fmt"] = pd.to_datetime(
                df_final["Final Sem"], errors="coerce"
            ).dt.strftime("%d/%b/%Y")
        else:
            df_final["Fecha_Fmt"] = "N/A"

        # CÁLCULOS COMERCIALES Y CONVERSIÓN
        df_final["Grande"] = (
            df_final["Jumbo"] + df_final["Extra"] + df_final["AA"]
        ) * 100
        df_final["Mediano"] = (df_final["A"]) * 100
        df_final["Pequeño"] = (df_final["B"] + df_final["C"]) * 100
        df_final["Segunda"] = (
            df_final["Alt Cáscara"]
            + df_final["Alt. Color"]
            + df_final["Picado"]
            + df_final["Roto"]
        ) * 100

        df_final["Conversión"] = (
            df_final["Bulto X 40 K"] * 40000
        ) / (df_final["Huevos  Semana"].replace(0, 1))

        df_final["Dif Pdn"] = (
            df_final["% Pdn. Real"] - df_final["% Pdn. Tabla"]
        )
        df_final["Dif GAD"] = (
            df_final["Gr.A.D Real"] - df_final["Gr.A.D Tabla"]
        )
        df_final["Dif HAA"] = (
            df_final["H.A.A. Real"] - df_final["H.A.A. Tabla"]
        )
        df_final["Dif Mort"] = (
            df_final["%Mort+Sel Acum. Tab"] - df_final["% Mort + Sel Acum."]
        )
        df_final["Dif Peso"] = df_final["Peso Real"] - df_final["Peso Tab"]

        df_graf = df_final.copy()
        for c in [
            "Grande",
            "Mediano",
            "Pequeño",
            "Segunda",
            "% Pdn. Real",
            "Gr.A.D Real",
            "Peso Real",
            "H.A.A. Real",
            "Conversión",
            "Costo Alimento Sem",
            "$ Huevo por alimento",
        ]:
            if c in df_graf.columns:
                df_graf[c] = df_graf[c].replace(0, np.nan)

        # MOTOR DE GRÁFICOS COMPARATIVOS CON TÍTULOS CENTRADOS Y ESPACIO AMPLIO
        def plot_hupa_comparativo(
            df, y_col, tab_col, title, unit, show_labels, show_table
        ):
            df_plot = df.sort_values(["ID_INTERNO", "Edad Sem."]).copy()
            fig = px.line(
                df_plot,
                x="Edad Sem.",
                y=y_col,
                color="ID_INTERNO",
                markers=True,
            )

            if show_table and tab_col and tab_col in df.columns:
                df_tab = (
                    df.groupby("Edad Sem.")[tab_col].mean().reset_index()
                )
                fig.add_scatter(
                    x=df_tab["Edad Sem."],
                    y=df_tab[tab_col],
                    mode="lines",
                    line=dict(color="#7F8C8D", dash="dot", width=2),
                    name="Meta Ideal (Tabla)",
                )

            cdata = np.stack(
                (df_plot["Fecha_Fmt"], df_plot["Fase de Alimento"]), axis=-1
            )

            fig.update_traces(
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Semana: %{x} (📅 %{customdata[0]})<br>"
                    "🌾 <b>Fase Alimento:</b> %{customdata[1]}<br>"
                    "Valor: <b>%{y:.1f} "
                    + unit
                    + "</b><extra></extra>"
                ),
                customdata=cdata,
            )

            fig.update_layout(
                title={
                    "text": f"<b>{title}</b>",
                    "x": 0.5,
                    "xanchor": "center",
                    "yanchor": "top",
                    "font": dict(size=14),
                },
                height=360,
                margin=dict(t=55, b=25, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.22,
                    xanchor="center",
                    x=0.5,
                ),
                hovermode="x unified",
            )
            fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")
            fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.15)")

            if show_labels:
                fig.update_traces(
                    mode="lines+markers+text",
                    texttemplate="%{y:.1f}",
                    textposition="top center",
                )

            return fig

        # --- 1. SECCIÓN GRÁFICOS: COMERCIALES ---
        with st.expander(
            "💹 Distribución de Tamaño de Huevo Comerciales", expanded=True
        ):
            g1, g2 = st.columns(2)
            with g1:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "Grande",
                        None,
                        "💎 HUEVO GRANDE (Jumbo / Extra / AA) %",
                        "%",
                        ver_etiquetas,
                        False,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with g2:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "Mediano",
                        None,
                        "🥚 HUEVO MEDIANO (A) %",
                        "%",
                        ver_etiquetas,
                        False,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

            g3, g4 = st.columns(2)
            with g3:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "Pequeño",
                        None,
                        "🐣 HUEVO PEQUEÑO (B / C) %",
                        "%",
                        ver_etiquetas,
                        False,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with g4:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "Segunda",
                        None,
                        "⚠️ HUEVO DE SEGUNDA %",
                        "%",
                        ver_etiquetas,
                        False,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        # --- 2. SECCIÓN GRÁFICOS: INDICADORES TÉCNICOS ---
        with st.expander(
            "🥚 Comparativo de Indicadores Técnicos Biológicos", expanded=True
        ):
            b1, b2 = st.columns(2)
            with b1:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "% Pdn. Real",
                        "% Pdn. Tabla",
                        "📈 CURVA DE PRODUCCIÓN (%)",
                        "%",
                        ver_etiquetas,
                        ver_tabla_line,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with b2:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "Gr.A.D Real",
                        "Gr.A.D Tabla",
                        "🥣 CONSUMO DE ALIMENTO (G/AVE/DÍA)",
                        "g",
                        ver_etiquetas,
                        ver_tabla_line,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            b3, b4 = st.columns(2)
            with b3:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "% Mort + Sel Acum.",
                        "%Mort+Sel Acum. Tab",
                        "🛡️ MORTALIDAD ACUMULADA (%)",
                        "%",
                        ver_etiquetas,
                        ver_tabla_line,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with b4:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "Peso Real",
                        "Peso Tab",
                        "⚖️ PESO CORPORAL DE LA AVE (G)",
                        "g",
                        ver_etiquetas,
                        ver_tabla_line,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        # --- 3. SECCIÓN: EFICIENCIA ALIMENTICIA Y COSTO HUEVO ---
        with st.expander(
            "💰 Eficiencia Alimenticia y Costo por Huevo (con Fase Nutricional)",
            expanded=True,
        ):
            c_ec1, c_ec2 = st.columns(2)

            with c_ec1:
                st.plotly_chart(
                    plot_hupa_comparativo(
                        df_graf,
                        "Conversión",
                        None,
                        "🌾 CONVERSIÓN (G Alimento / Huevo)",
                        "g",
                        ver_etiquetas,
                        False,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="guide-box"><b>Interpretación:</b> Gramos de'
                    " alimento consumidos para producir un huevo. Menor valor"
                    " representa mejor eficiencia biológica.</div>",
                    unsafe_allow_html=True,
                )

            with c_ec2:
                if es_admin:
                    st.plotly_chart(
                        plot_hupa_comparativo(
                            df_graf,
                            "$ Huevo por alimento",
                            None,
                            "🥚 COSTO HUEVO POR ALIMENTO ($/Huevo)",
                            "$",
                            ver_etiquetas,
                            False,
                        ),
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )
                    st.markdown(
                        '<div class="guide-box"><b>Interpretación:</b> Dinero'
                        " invertido en alimento por cada huevo producido.</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("🔒 Indicadores de costos restringidos (Sólo accesible para usuario ADMI).")

        # --- 📋 MATRIZ INTEGRAL DE AUDITORÍA CON BADGE DE GENÉTICA DINÁMICO ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

        c_tit, c_mod = st.columns([2.5, 1])
        with c_tit:
            st.markdown(
                "### 📋 Matriz Detallada de Auditoría Comparativa"
            )
        with c_mod:
            modo_vista = st.selectbox(
                "👁️ Modo de Vista de Tabla",
                ["Tabla HTML AgroTech", "Visor Tabular Interactivo"],
                index=0,
            )

        ids = sorted(df_final["ID_INTERNO"].unique())
        tabs = st.tabs([f"📍 {n}" for n in ids])

        cols_base = [
            "Final Sem",
            "Edad Sem.",
            "Saldo de Aves",
            "Mort",
            "% Mort + Sel Acum.",
            "%Mort+Sel Acum. Tab",
            "Dif Mort",
            "Fase de Alimento",
            "Observaciones",
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
            "Conversión",
            "Grande",
            "Mediano",
            "Pequeño",
            "Segunda",
            "Costo Alimento Sem",
            "$ Huevo por alimento",
        ]

        for i, tab in enumerate(tabs):
            with tab:
                df_tab = df_final[df_final["ID_INTERNO"] == ids[i]].copy()

                # MOSTRAR LÍNEA GENÉTICA DE ESTE LOTE ESPECÍFICO
                genetica_lote = (
                    df_tab["LINEA_AVES"].iloc[0]
                    if "LINEA_AVES" in df_tab.columns and not df_tab.empty
                    else "N/A"
                )
                st.markdown(
                    f"#### 🧬 Línea Genética: <span"
                    f' class="genetica-badge">{genetica_lote}</span>',
                    unsafe_allow_html=True,
                )

                if not es_admin:
                    lista_negra = ["Costo Alimento Sem", "$ Huevo por alimento"]
                    cols_finales = [
                        c for c in cols_base if c not in lista_negra
                    ]
                else:
                    cols_finales = cols_base

                cols_disp = [c for c in cols_finales if c in df_tab.columns]
                tabla_render = (
                    df_tab[cols_disp]
                    .sort_values("Edad Sem.", ascending=False)
                    .fillna(0)
                    .copy()
                )

                if "Final Sem" in tabla_render.columns:
                    tabla_render["Final Sem"] = pd.to_datetime(
                        tabla_render["Final Sem"]
                    ).dt.strftime("%d/%m/%y")

                formatos_activos = {
                    k: v for k, v in formatos.items() if k in tabla_render.columns
                }

                if modo_vista == "Tabla HTML AgroTech":

                    def render_custom_table_comp(df_data):
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

                                if col == "Dif Pdn" and pd.notnull(val):
                                    try:
                                        n_v = float(val)
                                        style = (
                                            "background-color:rgba(17,122,101,0.18);"
                                            " color:#117A65; font-weight:bold;"
                                            if n_v >= 0
                                            else "background-color:rgba(169,50,38,0.18);"
                                            " color:#A93226; font-weight:bold;"
                                        )
                                    except:
                                        pass

                                elif col == "Dif GAD" and pd.notnull(val):
                                    try:
                                        n_v = float(val)
                                        style = (
                                            "background-color:rgba(185,119,14,0.18);"
                                            " color:#B9770E; font-weight:bold;"
                                            if n_v > 0
                                            else "background-color:rgba(17,122,101,0.18);"
                                            " color:#117A65; font-weight:bold;"
                                        )
                                    except:
                                        pass

                                elif col == "Dif Mort" and pd.notnull(val):
                                    try:
                                        n_v = float(val)
                                        style = (
                                            "background-color:rgba(169,50,38,0.18);"
                                            " color:#A93226; font-weight:bold;"
                                            if n_v < 0
                                            else "background-color:rgba(17,122,101,0.18);"
                                            " color:#117A65; font-weight:bold;"
                                        )
                                    except:
                                        pass

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

                    render_custom_table_comp(tabla_render)

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
else:
    st.error(
        "⚠️ No se pudo cargar el archivo Consolidado_Produccion_FINAL.xlsx"
    )