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
    "Conv": "{:.1f} g",
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
    page_title="HUPA | Análisis por Lote y Galpón",
    page_icon="🏠",
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

# --- 2. ESTILO CSS PARA IGUALAR BOTÓN POPOVER A LOS SELECTBOX ---
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

    /* HOMOGENEIZACIÓN FORZADA DEL POPOVER A SELECTBOX */
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
        margin-top: 0px !important;
    }
    div[data-testid="stPopover"] > button:hover {
        border-color: #D35400 !important;
        color: #D35400 !important;
    }

    /* TARJETAS DE IA Y ASISTENCIA TÉCNICA */
    .ai-card {
        background-color: var(--secondary-background-color);
        padding: 20px 24px;
        border-radius: 12px;
        border-left: 6px solid #D35400;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }

    .galpon-ai-box {
        background-color: rgba(211, 84, 0, 0.05);
        padding: 14px 16px;
        border-radius: 10px;
        margin-bottom: 12px;
        border: 1px solid rgba(211, 84, 0, 0.2);
        color: var(--text-color);
        font-size: 0.92rem;
        line-height: 1.5;
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

    /* BADGE DE GENÉTICA DESTACADO */
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
            for col in df.columns:
                if col not in [
                    "GRANJA",
                    "LOTE",
                    "NUM_GALPON",
                    "Final Sem",
                    "Observaciones",
                    "Fase de Alimento",
                    "LINEA_AVES",
                ]:
                    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
            return df
        except Exception as e:
            st.error(f"Error Crítico: {e}")
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
            <h1>Análisis por Lote y Galpón</h1>
            <p>Disección biológica por galpón, auditoría operativa de ambiente y diagnóstico asistido</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_orig is not None:
    with st.expander(
        "📌 Fundamentos de la Auditoría por Galpón e Instrucciones", expanded=False
    ):
        st.markdown(
            """
            **¿Qué estamos analizando?** Disección técnica de un Lote Biológico para comparar el comportamiento individual de sus Galpones. Desglosamos la masa de datos para encontrar ineficiencias que el promedio general del lote suele ocultar.
            
            **¿Por qué es vital?** En galpones de la misma edad, genética y nutrición, cualquier diferencia en resultados es una auditoría directa al manejo operativo (ambiente, iluminación, ventilación o agua).
            """
        )

    # Filtrar solo registros donde LOTE != NUM_GALPON (desglose por galpones)
    df_desglose = df_orig[df_orig["LOTE"] != df_orig["NUM_GALPON"]].copy()
    df_desglose["GALPON_ID"] = "Galpón " + df_desglose["NUM_GALPON"].astype(str)

    # --- PANEL DE FILTROS 100% HOMOGÉNEOS Y SIN ERRORES ---
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)

    with f1:
        granjas_disp = sorted(df_desglose["GRANJA"].unique())
        granja_sel = st.selectbox("🗺️ Selecciona Granja:", granjas_disp)

    df_g = df_desglose[df_desglose["GRANJA"] == granja_sel]

    with f2:
        lotes_disp = sorted(df_g["LOTE"].unique())
        lote_padre = st.selectbox("📦 Selecciona Lote Padre:", lotes_disp)

    df_l = df_g[df_g["LOTE"] == lote_padre]
    
    # Estandarizamos galpones a entero/cadena limpia
    galpones_disp = sorted(list(set(df_l["NUM_GALPON"].unique())))

    # POPOVER CON BOTÓN "MARCAR TODO" PERO ESTÉTICA EXACTA DE SELECTBOX
    with f3:
        st.markdown("<label style='font-size:14px; font-weight:400; margin-bottom:4px; display:block;'>🏠 Auditoría por Galpón:</label>", unsafe_allow_html=True)
        
        # Conteo dinámico de seleccionados
        count_sel = sum([1 for gp in galpones_disp if st.session_state.get(f"chk_gal_{gp}", True)])
        texto_popover = f"Galpones ({count_sel}/{len(galpones_disp)})"
        
        with st.popover(texto_popover, use_container_width=True):
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Marcar todo", key="btn_gal_all"):
                for gp in galpones_disp:
                    st.session_state[f"chk_gal_{gp}"] = True
                st.rerun()
            if col_b2.button("Desmarcar", key="btn_gal_none"):
                for gp in galpones_disp:
                    st.session_state[f"chk_gal_{gp}"] = False
                st.rerun()

            galpon_sel = [
                gp
                for gp in galpones_disp
                if st.checkbox(
                    f"Galpón {gp}",
                    value=st.session_state.get(f"chk_gal_{gp}", True),
                    key=f"chk_gal_{gp}",
                )
            ]

    st.markdown("<hr style='margin:10px 0; border-color:rgba(211,84,0,0.15);'>", unsafe_allow_html=True)
    cx1, cx2 = st.columns(2)
    with cx1:
        ver_etiquetas = st.toggle("🏷️ Mostrar etiquetas de datos", value=False)
    with cx2:
        ver_meta = st.toggle("📉 Mostrar línea de Meta Genética", value=True)

    st.markdown("</div>", unsafe_allow_html=True)

    if not galpon_sel:
        st.info(
            "💡 Despliega el selector **'Auditoría por Galpón'** y usa **'Marcar todo'** o selecciona los galpones que deseas auditar."
        )
    else:
        df_filtered = df_l[df_l["NUM_GALPON"].isin(galpon_sel)].copy()

        # CONTROL DE SLIDER DE EDAD
        max_e = int(df_filtered["Edad Sem."].max())
        min_e = int(df_filtered["Edad Sem."].min())
        rango_edad = st.slider(
            "⏳ Ventana de Análisis (Semanas de Edad):",
            min_e,
            max_e,
            (max(min_e, max_e - 6), max_e),
        )

        df_view = df_filtered[
            df_filtered["Edad Sem."].between(rango_edad[0], rango_edad[1])
        ].copy()

        # FORMATEO DE FECHA PARA TOOLTIP
        if "Final Sem" in df_view.columns:
            df_view["Fecha_Fmt"] = pd.to_datetime(
                df_view["Final Sem"], errors="coerce"
            ).dt.strftime("%d/%b/%Y")
        else:
            df_view["Fecha_Fmt"] = "N/A"

        # CÁLCULOS DE DIFERENCIAS Y REQUISITOS TÉCNICOS
        df_view["Conv"] = (
            (df_view["Bulto X 40 K"] * 40000)
            / df_view["Huevos  Semana"].replace(0, 1)
        ).round(1)
        df_view["Dif Pdn"] = (
            df_view["% Pdn. Real"] - df_view["% Pdn. Tabla"]
        ).round(1)
        df_view["Dif GAD"] = (
            df_view["Gr.A.D Real"] - df_view["Gr.A.D Tabla"]
        ).round(1)
        df_view["Dif Mort"] = (
            df_view["%Mort+Sel Acum. Tab"] - df_view["% Mort + Sel Acum."]
        ).round(1)
        df_view["Dif Peso"] = (
            df_view["Peso Real"] - df_view["Peso Tab"]
        ).round(1)

        # --- SECCIÓN A: ASISTENCIA TÉCNICA IA (DIAGNÓSTICO ESTRATÉGICO) ---
        with st.expander(
            "🤖 ASISTENCIA TÉCNICA ESTRATÉGICA IA - Clic para desplegar"
            " diagnóstico",
            expanded=False,
        ):
            ultimo_corte = df_view[
                df_view["Edad Sem."] == df_view["Edad Sem."].max()
            ].copy()

            if not ultimo_corte.empty:
                sem_max = int(df_view["Edad Sem."].max())
                st.markdown(
                    f"""
                    <div class="ai-card">
                        <h3 style="margin-top:0; text-align:center; color:#D35400;">🩺 Evaluación Técnica de Campo - Semana {sem_max}</h3>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                for _, row in ultimo_corte.iterrows():
                    g = row["NUM_GALPON"]
                    pdn_r, pdn_t = row["% Pdn. Real"], row["% Pdn. Tabla"]
                    gad_r, gad_t = row["Gr.A.D Real"], row["Gr.A.D Tabla"]
                    mort_s = row["% Mort + Sel Acum."]

                    diag_html = (
                        f'<div class="galpon-ai-box"><b>🏠 GALPÓN'
                        f" {g}:</b><br>"
                    )

                    # LÓGICA DE PRODUCCIÓN Y MANEJO
                    if pdn_r >= pdn_t:
                        diag_html += (
                            f"🚀 <b>Producción Excelente:</b> El galpón supera"
                            f" la meta genética ({pdn_r:.1f}%). <b>Manejo:</b>"
                            " Mantener estímulo lumínico y evitar cambios"
                            " bruscos en horarios de alimentación. "
                        )
                    elif pdn_r < pdn_t and pdn_r >= (pdn_t - 2):
                        diag_html += (
                            f"📉 <b>Producción Estable:</b> Se mantiene en el"
                            " rango de tolerancia. <b>Manejo:</b> Monitorear"
                            " uniformidad y revisar la limpieza de las líneas"
                            " de agua. "
                        )
                    else:
                        diag_html += (
                            f"🚨 <b>Producción Bajo Meta:</b> Brecha crítica de"
                            f" {abs(pdn_r-pdn_t):.1f}%. <b>Manejo:</b> Revisar"
                            " inmediatamente intensidad lumínica (Lux) y"
                            " descartar desafíos sanitarios. "
                        )

                    # LÓGICA DE CONSUMO
                    if gad_r > (gad_t + 4):
                        diag_html += (
                            f"<br>🥣 <b>Alerta de Consumo:</b> Ingesta elevada"
                            f" ({gad_r:.1f}g). <b>Acción:</b> Verificar"
                            " desperdicio mecánico en comederos o nivel de"
                            " tolvas. "
                        )
                    elif gad_r < (gad_t - 4):
                        diag_html += (
                            f"<br>⚠️ <b>Consumo Deficiente:</b> Ingesta baja"
                            f" ({gad_r:.1f}g). <b>Acción:</b> Revisar"
                            " palatabilidad y ventilación por posible exceso"
                            " de amoniaco. "
                        )
                    else:
                        diag_html += (
                            "<br>✅ <b>Consumo Óptimo:</b> Ingesta alineada con"
                            " el requerimiento metabólico. "
                        )

                    # LÓGICA DE MORTALIDAD
                    if mort_s > 0.05:
                        diag_html += (
                            f"<br>⚰️ <b>Alerta Sanitaria:</b> Tasa elevada de"
                            f" mortalidad/descarte ({mort_s:.2f}%). <b>Acción:</b>"
                            " Realizar necropsias de aves frescas y verificar"
                            " cloración de agua. "
                        )

                    diag_html += "</div>"
                    st.markdown(diag_html, unsafe_allow_html=True)

        # --- SECCIÓN B: MAPA DE CALOR CON FILA DE META GENÉTICA ---
        with st.expander("🔥 Mapa de Calor: Evolución de Postura por Galpón", expanded=True):
            df_heat_base = (
                df_view.pivot(
                    index="GALPON_ID",
                    columns="Edad Sem.",
                    values="% Pdn. Real",
                )
                .fillna(0)
                .round(1)
            )

            # CÁLCULO DE LA FILA DE META GENÉTICA
            meta_semanal = (
                df_view.groupby("Edad Sem.")["% Pdn. Tabla"]
                .mean()
                .round(1)
            )
            df_meta_row = pd.DataFrame([meta_semanal], index=["🎯 Meta Genética"])

            # CONCATENAR META ARRIBA DE LOS GALPONES
            df_heat = pd.concat([df_meta_row, df_heat_base])

            fig_heat = px.imshow(
                df_heat,
                color_continuous_scale="RdYlGn",
                labels=dict(x="Semana de Edad", y="Fila / Galpón", color="% Postura"),
                text_auto=".1f",
            )
            fig_heat.update_layout(
                title={
                    "text": "<b>MATRIZ DE POSTURA SEMANAL VS META GENÉTICA (%)</b>",
                    "x": 0.5,
                    "xanchor": "center",
                },
                height=360,
                margin=dict(t=45, b=20, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig_heat.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>Semana: %{x}<br>Producción:"
                    " <b>%{z:.1f}%</b><extra></extra>"
                )
            )
            st.plotly_chart(
                fig_heat,
                use_container_width=True,
                config={"displayModeBar": False},
            )

        # --- SECCIÓN C: GRÁFICOS TÉCNICOS COMPARATIVOS ---
        with st.expander("📈 Comparativo de Indicadores Biológicos Técnicos", expanded=True):

            def plot_tecnico_galpon(
                df, y_col, tab_col, title, unit, labels, meta_line
            ):
                df_plot = df.sort_values(["GALPON_ID", "Edad Sem."]).copy()
                fig = px.line(
                    df_plot,
                    x="Edad Sem.",
                    y=y_col,
                    color="GALPON_ID",
                    markers=True,
                )

                if meta_line and tab_col and tab_col in df.columns:
                    df_m = (
                        df.groupby("Edad Sem.")[tab_col].mean().reset_index()
                    )
                    fig.add_scatter(
                        x=df_m["Edad Sem."],
                        y=df_m[tab_col],
                        mode="lines",
                        line=dict(color="#7F8C8D", dash="dot", width=2),
                        name="Meta Genética",
                    )

                fig.update_traces(
                    hovertemplate=(
                        "<b>%{fullData.name}</b><br>Semana: %{x} (📅"
                        " %{customdata})<br>Valor: <b>%{y:.1f} "
                        + unit
                        + "</b><extra></extra>"
                    ),
                    customdata=df_plot["Fecha_Fmt"],
                )

                fig.update_layout(
                    title={
                        "text": f"<b>{title}</b>",
                        "x": 0.5,
                        "xanchor": "center",
                        "yanchor": "top",
                        "font": dict(size=14),
                    },
                    height=350,
                    margin=dict(t=50, b=25, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.22,
                        xanchor="center",
                        x=0.5,
                    ),
                )
                fig.update_xaxes(
                    showgrid=True, gridcolor="rgba(128,128,128,0.15)"
                )
                fig.update_yaxes(
                    showgrid=True, gridcolor="rgba(128,128,128,0.15)"
                )

                if labels:
                    fig.update_traces(
                        mode="lines+markers+text",
                        texttemplate="%{y:.1f}",
                        textposition="top center",
                    )

                return fig

            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(
                    plot_tecnico_galpon(
                        df_view,
                        "% Pdn. Real",
                        "% Pdn. Tabla",
                        "🥚 PRODUCCIÓN SEMANAL (%)",
                        "%",
                        ver_etiquetas,
                        ver_meta,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with c2:
                st.plotly_chart(
                    plot_tecnico_galpon(
                        df_view,
                        "Gr.A.D Real",
                        "Gr.A.D Tabla",
                        "🥣 CONSUMO DE ALIMENTO (G/AVE/DÍA)",
                        "g",
                        ver_etiquetas,
                        ver_meta,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

            c3, c4 = st.columns(2)
            with c3:
                st.plotly_chart(
                    plot_tecnico_galpon(
                        df_view,
                        "% Mort + Sel Acum.",
                        "%Mort+Sel Acum. Tab",
                        "⚰️ MORTALIDAD ACUMULADA (%)",
                        "%",
                        ver_etiquetas,
                        ver_meta,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with c4:
                st.plotly_chart(
                    plot_tecnico_galpon(
                        df_view,
                        "Peso Real",
                        "Peso Tab",
                        "⚖️ PESO CORPORAL (G)",
                        "g",
                        ver_etiquetas,
                        ver_meta,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

            c5, c6 = st.columns(2)
            with c5:
                st.plotly_chart(
                    plot_tecnico_galpon(
                        df_view,
                        "H.A.A. Real",
                        "H.A.A. Tabla",
                        "🐣 HUEVOS POR AVE ALOJADA (H.A.A.)",
                        "",
                        ver_etiquetas,
                        ver_meta,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            with c6:
                st.plotly_chart(
                    plot_tecnico_galpon(
                        df_view,
                        "Conv",
                        None,
                        "💰 CONVERSIÓN (G ALIMENTO / HUEVO)",
                        "g",
                        ver_etiquetas,
                        False,
                    ),
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

        # --- SECCIÓN D: MATRIZ DE AUDITORÍA INTEGRAL CON LÍNEA GENÉTICA ---
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

        c_tit, c_mod = st.columns([2.5, 1])
        with c_tit:
            st.markdown("### 📋 Matriz Detallada de Auditoría por Galpón")
        with c_mod:
            modo_vista = st.selectbox(
                "👁️ Modo de Vista de Tabla",
                ["Tabla HTML AgroTech", "Visor Tabular Interactivo"],
                index=0,
            )

        list_galpones = sorted(df_view["NUM_GALPON"].unique())
        tabs = st.tabs([f"🏠 Galpón {n}" for n in list_galpones])

        cols_base = [
            "Final Sem",
            "Edad Sem.",
            "Saldo de Aves",
            "Mort",
            "Suma Mort + Sel",
            "% Mort + Sel Acum.",
            "%Mort+Sel Acum. Tab",
            "Dif Mort",
            "Bulto X 40 K",
            "Gr.A.D Real",
            "Gr.A.D Tabla",
            "Dif GAD",
            "Peso Real",
            "Peso Tab",
            "Dif Peso",
            "Huevos  Semana",
            "% Pdn. Real",
            "% Pdn. Tabla",
            "Dif Pdn",
            "H.A.A. Real",
            "H.A.A. Tabla",
            "% Unif",
            "Conv",
            "Costo Alimento Sem",
            "$ Huevo por alimento",
        ]

        for i, tab in enumerate(tabs):
            with tab:
                gp_num = list_galpones[i]
                df_tab = (
                    df_view[df_view["NUM_GALPON"] == gp_num]
                    .sort_values("Edad Sem.", ascending=False)
                    .copy()
                )

                # DATO DINÁMICO DE LÍNEA GENÉTICA DEL GALPÓN
                genetica_galpon = (
                    df_tab["LINEA_AVES"].iloc[0]
                    if "LINEA_AVES" in df_tab.columns and not df_tab.empty
                    else "N/A"
                )
                st.markdown(
                    f"#### 🧬 Línea Genética: <span"
                    f' class="genetica-badge">{genetica_galpon}</span>',
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
                    df_tab[cols_disp].sort_values("Edad Sem.", ascending=False).fillna(0).copy()
                )

                if "Final Sem" in tabla_render.columns:
                    tabla_render["Final Sem"] = pd.to_datetime(
                        tabla_render["Final Sem"]
                    ).dt.strftime("%d/%m/%y")

                formatos_activos = {
                    k: v for k, v in formatos.items() if k in tabla_render.columns
                }

                if modo_vista == "Tabla HTML AgroTech":

                    def render_custom_table_galpon(df_data):
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

                    render_custom_table_galpon(tabla_render)

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