import base64
import datetime
import io
import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- 1. CONFIGURACIÓN GLOBAL DE FORMATOS DE TEXTO ---
formatos = {
    "Saldo de Aves": "{:,.0f}",
    "Huevos  Semana": "{:,.0f}",
    "Huevos Faltantes Sem.": "{:+,.0f}",
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

# --- MOTOR PREDICTIVO IA ---
try:
    from sklearn.linear_model import LinearRegression

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


def obtener_prediccion_ia(df_historico, columna_y, semanas_futuras=3):
    try:
        df_base = df_historico[df_historico["Edad Sem."] >= 30].sort_values(
            "Edad Sem."
        )
        if len(df_base) < 4:
            return None, None

        semanas_reales = df_base["Edad Sem."].tolist()
        predicciones_pasadas = []

        for i in range(4, len(semanas_reales)):
            entrenamiento = df_base.iloc[i - 4 : i]
            X = entrenamiento[["Edad Sem."]].values
            y = entrenamiento[columna_y].values

            model = LinearRegression().fit(X, y)
            sem_actual = semanas_reales[i]
            pred_actual = model.predict([[sem_actual]])[0]
            predicciones_pasadas.append((sem_actual, pred_actual))

        ultimas_4 = df_base.tail(4)
        model_futuro = LinearRegression().fit(
            ultimas_4[["Edad Sem."]].values, ultimas_4[columna_y].values
        )

        ultima_sem = semanas_reales[-1]
        futuro_x = []
        futuro_y = []
        for f in range(1, semanas_futuras + 1):
            s_f = ultima_sem + f
            futuro_x.append(s_f)
            futuro_y.append(model_futuro.predict([[s_f]])[0])

        x_final = [p[0] for p in predicciones_pasadas] + futuro_x
        y_final = [p[1] for p in predicciones_pasadas] + futuro_y

        return np.array(x_final), np.array(y_final)
    except:
        return None, None


def convertir_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Detalle_Auditoria")
    return output.getvalue()


# --- SEGURIDAD Y CONFIGURACIÓN ---
if "auth" not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

st.set_page_config(
    page_title="HUPA | Auditoría Técnica de Producción",
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

# --- 2. ESTILO CSS RESPONSIVE ADAPTABLE A MODO CLARO Y OSCURO ---
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

    /* PANEL DE FILTROS CREADO CON VARIABLES DINÁMICAS NATIVAS */
    .filter-panel {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(211, 84, 0, 0.25);
        border-radius: 12px;
        padding: 14px 18px 6px 18px;
        margin-bottom: 20px;
    }

    /* BARRA DE HERRAMIENTAS ADAPTABLE */
    .toolbar-box {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 10px 18px 2px 18px;
        margin-bottom: 15px;
    }

    /* TARJETAS KPI EXECUTIVE CON VARIABLES DE TEMA */
    .kpi-card-exec {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 14px 8px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        position: relative;
        overflow: hidden;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }
    .kpi-card-exec:hover { transform: translateY(-2px); }
    .kpi-card-exec::before {
        content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px;
        background: linear-gradient(90deg, #D35400, #F39C12);
    }
    .kpi-title-exec {
        font-size: clamp(0.68rem, 0.85vw, 0.78rem);
        font-weight: 700;
        color: var(--text-color);
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }
    .kpi-val-exec {
        font-size: clamp(1.2rem, 1.6vw, 1.6rem);
        font-weight: 800;
        color: var(--text-color);
        line-height: 1.1;
    }

    /* BLOQUE NARRATIVO Y DE GUÍA CON ADAPTABILIDAD OCURA/CLARA */
    .story-box {
        background-color: var(--secondary-background-color);
        padding: 16px 20px;
        border-radius: 10px;
        border-left: 5px solid #D35400;
        margin: 12px 0 18px 0;
        font-size: 0.95rem;
        color: var(--text-color);
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
        padding: 3px 10px;
        border-radius: 16px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-left: 8px;
    }

    /* TABLA AGROTECH CON RETROALIMENTACIÓN DE TEMA CLARO Y OSCURO */
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
        df = pd.read_excel(PATH_DATA)
        df.columns = [str(col).replace("\n", " ").strip() for col in df.columns]
        num_cols = [
            "% Pdn. Real",
            "% Pdn. Tabla",
            "Gr.A.D Real",
            "Gr.A.D Tabla",
            "% Mort + Sel Acum.",
            "%Mort+Sel Acum. Tab",
            "H.A.A. Real",
            "H.A.A. Tabla",
            "Peso Real",
            "Peso Tab",
            "Saldo de Aves",
            "Bulto X 40 K",
            "Huevos  Semana",
        ]
        for col in [c for c in num_cols if c in df.columns]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        return df
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

# --- 4. RENDERIZADO DE INTERFAZ ---
st.markdown(
    f"""
    <div class="app-header">
        {logo_html}
        <div class="app-header-text">
            <h1>Auditoría Técnica de Producción</h1>
            <p>Protocolo de fiscalización operativa, comportamiento biológico y proyecciones de lote</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_orig is not None:
    with st.expander(
        "🔍 Protocolo de Fiscalización Operativa e Instrucciones",
        expanded=False,
    ):
        st.markdown(
            """
            Bienvenido al sistema de **Control y Seguimiento Biológico por Lote**. Esta interfaz audita el cumplimiento de los estándares de manejo y la respuesta metabólica del lote frente a su potencial genético.
            
            A través de modelos de **Inteligencia Artificial (Regresión Polinomial)**, analizamos la trayectoria real de la curva de postura y el consumo de alimento para detectar desviaciones en el confort ambiental o fallos en el protocolo de alimentación.
            """
        )

    # PANEL INTEGRADO DE FILTROS DE LOTE
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    empresas_disp = sorted(df_orig["RAZON_SOCIAL"].unique())
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

    with c1:
        empresa = st.selectbox("🏢 Empresa:", empresas_disp, index=idx_default)
    with c2:
        granjas_disp = sorted(
            df_orig[df_orig["RAZON_SOCIAL"] == empresa]["GRANJA"].unique()
        )
        granja = st.selectbox("🏘️ Granja:", granjas_disp)
    with c3:
        df_activos = df_orig[
            (df_orig["RAZON_SOCIAL"] == empresa)
            & (df_orig["GRANJA"] == granja)
        ]
        df_activos = df_activos[df_activos["LOTE"] == df_activos["NUM_GALPON"]]
        lotes_disp = sorted(df_activos["LOTE"].unique())
        lote_sel = st.selectbox("📦 Lote Activo:", lotes_disp)

    st.markdown("</div>", unsafe_allow_html=True)

    df_full_lote = df_activos[df_activos["LOTE"] == lote_sel].sort_values(
        "Edad Sem."
    )

    if not df_full_lote.empty:
        # CÁLCULOS TÉCNICOS
        df_full_lote["Dif Pdn"] = (
            df_full_lote["% Pdn. Real"] - df_full_lote["% Pdn. Tabla"]
        )
        df_full_lote["Dif GAD"] = (
            df_full_lote["Gr.A.D Real"] - df_full_lote["Gr.A.D Tabla"]
        )
        df_full_lote["Dif HAA"] = (
            df_full_lote["H.A.A. Real"] - df_full_lote["H.A.A. Tabla"]
        )
        df_full_lote["Dif Peso"] = (
            df_full_lote["Peso Real"] - df_full_lote["Peso Tab"]
        )
        df_full_lote["Dif Mort"] = (
            df_full_lote["%Mort+Sel Acum. Tab"]
            - df_full_lote["% Mort + Sel Acum."]
        )

        # INDICADOR SOLICITADO: HUEVOS FALTANTES/GANADOS
        df_full_lote["Huevos Faltantes Sem."] = (
            df_full_lote["Saldo de Aves"] * (df_full_lote["Dif Pdn"] / 100.0) * 7
        )

        df_full_lote["Conversión"] = (
            df_full_lote["Bulto X 40 K"] * 40000
        ) / (df_full_lote["Huevos  Semana"].replace(0, 1))

        # FORMATEO DE FECHA PARA TOOLTIP FLOTANTE
        if "Final Sem" in df_full_lote.columns:
            df_full_lote["Fecha_Fmt"] = pd.to_datetime(
                df_full_lote["Final Sem"], errors="coerce"
            ).dt.strftime("%d/%b/%Y")
        else:
            df_full_lote["Fecha_Fmt"] = "N/A"

        ult = df_full_lote.iloc[-1]
        ant = df_full_lote.iloc[-2] if len(df_full_lote) > 1 else ult
        saldo_inicial = df_full_lote["Saldo de Aves"].max()
        aves_perdidas = df_full_lote["Mort"].sum()
        genetica_actual = ult.get("LINEA_AVES", "N/A")

        # TARJETAS KPI EXECUTIVE
        k_cols = st.columns(5)

        def render_kpi(
            col, title, emoji, val, tab, ant_val, unit, is_mort=False
        ):
            sub_tab = ""
            if tab is not None:
                dif = val - tab
                color_sub = (
                    "#117A65"
                    if (dif >= 0 if not is_mort else dif <= 0)
                    else "#A93226"
                )
                sub_tab = f'<span style="color:{color_sub}; font-weight:bold;">Vs Tab: {dif:+.1f}{unit}</span>'

            sub_ant = ""
            if ant_val is not None:
                cambio = val - ant_val
                flecha = "▲" if val >= ant_val else "▼"
                sub_ant = f'<span style="opacity:0.8;">Vs Ant: {flecha}{abs(cambio):.1f}</span>'

            if title == "SALDO AVES":
                sub_ant = (
                    f'<span style="opacity:0.8;">Alojadas:'
                    f" {saldo_inicial:,.0f}</span>"
                )
                sub_tab = (
                    f'<span style="opacity:0.8;">Mort:'
                    f" {aves_perdidas:,.0f}</span>"
                )

            val_display = f"{val:,.0f}" if not unit else f"{val:.1f}"

            col.markdown(
                f"""
            <div class="kpi-card-exec">
                <div class="kpi-title-exec">{emoji} {title}</div>
                <div class="kpi-val-exec">{val_display}{unit}</div>
                <div style='display: flex; gap: 8px; justify-content: center; width: 100%; border-top: 1px solid rgba(128,128,128,0.15); padding-top: 5px; margin-top: 5px; font-size:0.76rem;'>
                    {sub_ant} | {sub_tab}
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        render_kpi(
            k_cols[0],
            "PRODUCCIÓN",
            "🥚",
            ult["% Pdn. Real"],
            ult["% Pdn. Tabla"],
            ant["% Pdn. Real"],
            "%",
        )
        render_kpi(
            k_cols[1],
            "CONSUMO",
            "🥣",
            ult["Gr.A.D Real"],
            ult["Gr.A.D Tabla"],
            ant["Gr.A.D Real"],
            "g",
        )
        render_kpi(
            k_cols[2],
            "MORTALIDAD ACUM",
            "💀",
            ult["% Mort + Sel Acum."],
            ult["%Mort+Sel Acum. Tab"],
            ant["% Mort + Sel Acum."],
            "%",
            is_mort=True,
        )
        render_kpi(
            k_cols[3],
            "H.A.A",
            "🏆",
            ult["H.A.A. Real"],
            ult["H.A.A. Tabla"],
            ant["H.A.A. Real"],
            "",
        )
        render_kpi(
            k_cols[4],
            "SALDO AVES",
            "🐥",
            ult["Saldo de Aves"],
            None,
            None,
            "",
        )

        # BLOQUE NARRATIVO CONTEXTUAL
        st.markdown(
            f"""
            <div class="story-box">
                📖 <b>Contexto del Lote:</b> Granja <b>{granja}</b> (Ubicación: <b>{ult.get('UBICACION', 'N/A')}</b>) | 
                Lote: <b>{lote_sel}</b> | Genética: <b>{genetica_actual}</b> | 
                Observaciones/Nutrición: <b>{ult.get('Observaciones', 'N/A')}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        # --- CONTROLES GENERALES CREADOS POR FUERA DEL ACORDEÓN ---
        st.markdown('<div class="toolbar-box">', unsafe_allow_html=True)
        max_age = float(df_full_lote["Edad Sem."].max())
        min_age = float(df_full_lote["Edad Sem."].min())

        c_sl1, c_sl2, c_sl3 = st.columns([2.5, 1, 1])
        with c_sl1:
            range_age = st.slider(
                "⏳ Filtrar Rango de Semanas para Análisis:",
                min_age,
                max_age,
                (max(min_age, max_age - 8.0), max_age),
                1.0,
            )
        with c_sl2:
            ver_labels = st.toggle("🔖 Ver etiquetas de datos", value=False)
        with c_sl3:
            ver_ia = st.toggle("🤖 Activar Predicción IA", value=False)

        st.markdown("</div>", unsafe_allow_html=True)

        df_lote = df_full_lote[
            (df_full_lote["Edad Sem."] >= range_age[0])
            & (df_full_lote["Edad Sem."] <= range_age[1])
        ].copy()

        # --- SECCIÓN DE GRÁFICOS PLEGABLES ---
        with st.expander(
            "📊 Ver Curvas de Comportamiento Técnico", expanded=True
        ):
            def plot_hupa_final(
                df_current, df_total, real_col, tab_col, title, unit
            ):
                df_plot = df_current.copy()
                modo_visual = (
                    "lines+markers+text" if ver_labels else "lines+markers"
                )

                if tab_col and tab_col in df_plot.columns:
                    df_plot["dif_val"] = (
                        df_plot[real_col] - df_plot[tab_col]
                    ).round(1)
                    y_list = [real_col, tab_col]
                    htemp = (
                        "<b>Semana: %{x}</b> (📅 %{customdata[2]})<br>"
                        "Real: %{y:.1f}"
                        + unit
                        + "<br>Tabla: %{customdata[0]:.1f}"
                        + unit
                        + "<br>Diferencia: <b>%{customdata[1]:+.1f}</b>"
                        + unit
                        + "<extra></extra>"
                    )
                    cdata = df_plot[[tab_col, "dif_val", "Fecha_Fmt"]]
                else:
                    y_list = [real_col]
                    htemp = (
                        "<b>Semana: %{x}</b> (📅 %{customdata[0]})<br>"
                        "Real: %{y:.1f}" + unit + "<extra></extra>"
                    )
                    cdata = df_plot[["Fecha_Fmt"]]

                fig = px.line(
                    df_plot,
                    x="Edad Sem.",
                    y=y_list,
                    markers=True,
                    color_discrete_map={
                        real_col: "#D35400",
                        tab_col: "#7F8C8D",
                    },
                )

                fig.update_traces(
                    selector={"name": real_col},
                    mode=modo_visual,
                    text=df_plot[real_col],
                    texttemplate="<b>%{text:.1f}</b>",
                    textposition="top center",
                    textfont=dict(size=12, color="#D35400"),
                    hovertemplate=htemp,
                    customdata=cdata,
                )

                if tab_col and tab_col in df_plot.columns:
                    fig.update_traces(
                        selector={"name": tab_col},
                        mode=modo_visual,
                        text=df_plot[tab_col],
                        texttemplate="%{text:.1f}",
                        textposition="bottom center",
                        line=dict(dash="dot", width=2),
                    )

                if ver_ia and ML_AVAILABLE:
                    semanas_ia, valores_ia = obtener_prediccion_ia(
                        df_total, real_col
                    )
                    if semanas_ia is not None:
                        min_vista = df_plot["Edad Sem."].min()
                        mask = semanas_ia >= min_vista
                        fig.add_trace(
                            go.Scatter(
                                x=semanas_ia[mask],
                                y=valores_ia[mask],
                                name="🤖 IA Proyección",
                                line=dict(
                                    color="#17A2B8", width=2.5, dash="dash"
                                ),
                                mode="lines",
                                hovertemplate="<b>Proyección IA:</b> %{y:.1f}"
                                + unit
                                + "<extra></extra>",
                            )
                        )

                fig.update_layout(
                    title={
                        "text": f"<b>{title}</b>",
                        "x": 0.5,
                        "xanchor": "center",
                        "font": dict(size=14),
                    },
                    hovermode="x unified",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=320,
                    margin=dict(t=35, b=20, l=10, r=10),
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.18,
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

                return fig

            g1, g2 = st.columns(2)
            with g1:
                fig1 = plot_hupa_final(
                    df_lote,
                    df_full_lote,
                    "% Pdn. Real",
                    "% Pdn. Tabla",
                    "🥚 POSTURA REAL VS TABLA (%)",
                    "%",
                )
                st.plotly_chart(
                    fig1,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="guide-box"><b>Observaciones:</b> Mide la'
                    " eficiencia en la curva de postura. Una caída sostenida"
                    " bajo la guía requiere revisión.</div>",
                    unsafe_allow_html=True,
                )

            with g2:
                fig2 = plot_hupa_final(
                    df_lote,
                    df_full_lote,
                    "Gr.A.D Real",
                    "Gr.A.D Tabla",
                    "🌽 CONSUMO DE ALIMENTO (G/AVE/DÍA)",
                    "g",
                )
                st.plotly_chart(
                    fig2,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="guide-box"><b>Observaciones:</b> Mide'
                    " consumo de alimento acumulado y diario frente a la guía"
                    " genética.</div>",
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

            g3, g4 = st.columns(2)
            with g3:
                fig3 = plot_hupa_final(
                    df_lote,
                    df_full_lote,
                    "% Mort + Sel Acum.",
                    "%Mort+Sel Acum. Tab",
                    "💀 MORTALIDAD ACUMULADA (%)",
                    "%",
                )
                st.plotly_chart(
                    fig3,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="guide-box"><b>Observaciones:</b>'
                    " Supervivencia del lote encasetado vs. tabla"
                    " guía.</div>",
                    unsafe_allow_html=True,
                )

            with g4:
                fig4 = plot_hupa_final(
                    df_lote,
                    df_full_lote,
                    "Peso Real",
                    "Peso Tab",
                    "🐤 PESO CORPORAL (G)",
                    "g",
                )
                st.plotly_chart(
                    fig4,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="guide-box"><b>Observaciones:</b> Evolución'
                    " del peso corporativo promedio del lote.</div>",
                    unsafe_allow_html=True,
                )

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

            g5, g6 = st.columns(2)
            with g5:
                fig5 = plot_hupa_final(
                    df_lote,
                    df_full_lote,
                    "H.A.A. Real",
                    "H.A.A. Tabla",
                    "🏆 HUEVOS POR AVE ALOJADA (H.A.A.)",
                    "",
                )
                st.plotly_chart(
                    fig5,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="guide-box"><b>Observaciones:</b> Sumatoria'
                    " acumulada de huevos producidos por ave.</div>",
                    unsafe_allow_html=True,
                )

            with g6:
                fig6 = plot_hupa_final(
                    df_lote,
                    df_full_lote,
                    "Conversión",
                    None,
                    "💰 CONVERSIÓN (G ALIMENTO / HUEVO)",
                    "g",
                )
                st.plotly_chart(
                    fig6,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
                st.markdown(
                    '<div class="guide-box"><b>Observaciones:</b> Eficiencia'
                    " de conversión alimenticia.</div>",
                    unsafe_allow_html=True,
                )

        # TABLA TÉCNICA DETALLADA (ELIMINADAS GRANJA, LINEA_AVES Y LOTE)
        st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)

        c_tit, c_mod = st.columns([2.5, 1])
        with c_tit:
            st.markdown(
                f"### 📋 Historial Detallado del Lote <span"
                f' class="genetica-badge">🧬 Genética: {genetica_actual}</span>',
                unsafe_allow_html=True,
            )
        with c_mod:
            modo_vista = st.selectbox(
                "👁️ Modo de Vista de Tabla",
                ["Tabla HTML AgroTech", "Visor Tabular Interactivo"],
                index=0,
            )

        # ❌ SE ELIMINARON "GRANJA", "LINEA_AVES" Y "LOTE" DE LA COLS_BASE
        cols_base = [
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
            "Huevos  Semana",
            "Huevos Faltantes Sem.",
            "Gr.A.D Real",
            "Gr.A.D Tabla",
            "Dif GAD",
            "% Pdn. Real",
            "% Pdn. Tabla",
            "Dif Pdn",
            "% Unif",
            "Peso Real",
            "Peso Tab",
            "Dif Peso",
            "H.A.A. Real",
            "H.A.A. Tabla",
            "Dif HAA",
            "Costo Alimento Sem",
            "$ Huevo por alimento",
        ]

        if usuario_actual == "VET_HUPA":
            lista_negra = ["Costo Alimento Sem", "$ Huevo por alimento"]
            cols_disponibles = [
                c
                for c in cols_base
                if c in df_full_lote.columns and c not in lista_negra
            ]
        else:
            cols_disponibles = [
                c for c in cols_base if c in df_full_lote.columns
            ]

        with st.popover("⚙️ Seleccionar Columnas Visibles"):
            cols_visibles = [
                col
                for col in cols_disponibles
                if st.checkbox(col, value=True, key=f"hist_vis_{col}")
            ]

        if not cols_visibles:
            cols_visibles = cols_disponibles

        df_tabla_source = (
            df_lote
            if "df_lote" in locals() and not df_lote.empty
            else df_full_lote
        )
        tabla_final = (
            df_tabla_source[cols_visibles]
            .sort_values("Edad Sem.", ascending=False)
            .copy()
        )
        formatos_activos = {
            k: v for k, v in formatos.items() if k in tabla_final.columns
        }

        # DESCARGA DE EXCEL
        with st.expander("📥 Descargar Reporte del Lote (Excel)"):
            st.download_button(
                label="🚀 Descargar Excel",
                data=convertir_a_excel(tabla_final),
                file_name=(
                    f"Reporte_Lote_{lote_sel}_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
                ),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # RENDER TABLA CON SOPORTE DE TEMAS NATIVOS
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

                        if col in ["Dif Pdn", "Huevos Faltantes Sem."] and pd.notnull(val):
                            try:
                                n_v = float(val)
                                style = (
                                    "background-color:rgba(17,122,101,0.18); color:#117A65; font-weight:bold;"
                                    if n_v >= 0
                                    else "background-color:rgba(169,50,38,0.18); color:#A93226; font-weight:bold;"
                                )
                            except:
                                pass

                        elif col == "Dif GAD" and pd.notnull(val):
                            try:
                                n_v = float(val)
                                style = (
                                    "background-color:rgba(185,119,14,0.18); color:#B9770E; font-weight:bold;"
                                    if n_v > 0
                                    else "background-color:rgba(17,122,101,0.18); color:#117A65; font-weight:bold;"
                                )
                            except:
                                pass

                        elif col == "Dif Mort" and pd.notnull(val):
                            try:
                                n_v = float(val)
                                style = (
                                    "background-color:rgba(169,50,38,0.18); color:#A93226; font-weight:bold;"
                                    if n_v < 0
                                    else "background-color:rgba(17,122,101,0.18); color:#117A65; font-weight:bold;"
                                )
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

                        html += f'<td style="{style}">{fmt_val}</td>'
                    html += "</tr>"

                html += "</tbody></table></div>"
                st.markdown(html, unsafe_allow_html=True)

            render_custom_table_lote(tabla_final)

        else:
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

        # SELLO DE SINCRONIZACIÓN
        try:
            mtime = os.path.getmtime(PATH_DATA)
            fecha_act = datetime.datetime.fromtimestamp(mtime).strftime(
                "%d/%m/%Y %I:%M %p"
            )
            st.markdown(
                f"<div style='text-align: right; opacity: 0.6; font-size:"
                f" 0.85rem; font-style: italic; margin-top: 10px;'>📅 Última"
                f" actualización: {fecha_act}</div>",
                unsafe_allow_html=True,
            )
        except:
            pass

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
    st.error("⚠️ No se pudo cargar el archivo Consolidado_Produccion_FINAL.xlsx.")