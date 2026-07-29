import base64
import datetime
import io
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- 1. CONFIGURACIÓN Y SEGURIDAD ---
if "auth" not in st.session_state or not st.session_state.auth:
    st.switch_page("app.py")
    st.stop()

st.set_page_config(
    page_title="HUPA | Informe Gerencial y Diagnóstico PDF",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

usuario_actual = st.session_state.get("user", "VET_HUPA")
es_admin = "ADM" in str(usuario_actual).upper()


def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return None


logo_path = os.path.join("DATA", "logo hupa.png")
logo_b64 = get_image_base64(logo_path)
logo_src = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
logo_html = (
    f'<img src="{logo_src}" style="height: 55px;'
    ' margin-right: 15px; border-radius: 8px; object-fit: contain;">'
    if logo_b64
    else ""
)

# --- 2. CONFIGURACIÓN DE COLORES DINÁMICOS POR RAZÓN SOCIAL ---
def obtener_color_empresa(empresa_nombre):
    emp_upper = str(empresa_nombre).upper().strip()
    if "AGNO" in emp_upper:
        return "#D35400", "#E67E22"  # Naranja
    elif "RRL" in emp_upper:
        return "#1E8449", "#27AE60"  # Verde
    elif "CHIHEN" in emp_upper:
        return "#1F618D", "#2980B9"  # Azul
    else:
        return "#D35400", "#E67E22"  # Default Naranja

# --- 3. ESTILO CSS GENERAL ---
st.markdown(
    """
    <style>
    [data-testid="stHeader"] { background-color: transparent !important; }

    .filter-panel {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }

    div[data-testid="stPopover"] { width: 100% !important; }
    div[data-testid="stPopover"] > button {
        width: 100% !important;
        background-color: rgba(128, 128, 128, 0.08) !important;
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 8px !important;
        color: var(--text-color) !important;
        height: 40px !important;
        min-height: 40px !important;
    }

    .callout-problem {
        background-color: rgba(192, 57, 43, 0.08);
        border-left: 4px solid #C0392B;
        padding: 14px 18px;
        border-radius: 6px;
        margin-top: 15px;
    }
    .callout-solution {
        background-color: rgba(39, 174, 96, 0.08);
        border-left: 4px solid #27AE60;
        padding: 14px 18px;
        border-radius: 6px;
        margin-top: 15px;
    }

    .hr-custom {
        border: 0; height: 1px;
        background: linear-gradient(to right, rgba(0,0,0,0), rgba(128, 128, 128, 0.35), rgba(0,0,0,0));
        margin: 25px 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 4. CARGA Y LIMPIEZA DE DATOS ---
PATH_DATA = os.path.join("DATA", "Consolidado_Produccion_FINAL.xlsx")


@st.cache_data
def load_data():
    if os.path.exists(PATH_DATA):
        try:
            df = pd.read_excel(PATH_DATA)
            df.columns = [str(col).replace("\n", " ").strip() for col in df.columns]

            # Detección Empresa
            col_empresa = None
            for c in ["EMPRESA", "RAZON_SOCIAL", "RAZON SOCIAL", "SOCIEDAD", "Razon Social", "Razón Social"]:
                if c in df.columns:
                    col_empresa = c
                    break
            
            if not col_empresa:
                df["EMPRESA"] = "HUPA | DIVISIÓN AVÍCOLA"
                col_empresa = "EMPRESA"
            else:
                df[col_empresa] = df[col_empresa].astype(str).str.strip()

            if "Final Sem" in df.columns:
                df["Fecha_DT"] = pd.to_datetime(df["Final Sem"], errors="coerce")
                df["Fecha_Fmt"] = df["Fecha_DT"].dt.strftime("%d/%b/%Y")
            else:
                df["Fecha_DT"] = pd.NaT
                df["Fecha_Fmt"] = "N/A"

            if "Fase de Alimento" not in df.columns:
                df["Fase de Alimento"] = "Sin Especificar"

            # Detección de columna Línea Genética (LINEA_AVES)
            col_linea = None
            posibles_linea = [
                "LINEA_AVES", "LINEA AVES", "LINEA GENETICA", "LINEA_GENETICA", 
                "GENETICA", "LINEA", "Línea Genética", "RAZA", "Raza"
            ]
            for cl in posibles_linea:
                if cl in df.columns:
                    col_linea = cl
                    break
            
            if not col_linea:
                df["LINEA_AVES"] = "Sin Especificar"
                col_linea = "LINEA_AVES"
            else:
                df[col_linea] = df[col_linea].astype(str).str.strip().replace(["0", "nan", "0.0", "N/A", ""], "Sin Especificar")

            num_cols = [
                "Edad Sem.", "Huevos  Semana", "Costo Alimento Sem",
                "$ Huevo por alimento", "Bulto X 40 K", "Jumbo", "Extra",
                "AA", "A", "B", "C", "Alt Cáscara", "Alt. Color", "Picado", "Roto", "% Pdn. Real", "Saldo de Aves"
            ]
            for col in [c for c in num_cols if c in df.columns]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            return df, col_empresa, col_linea
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            return None, None, None
    return None, None, None


df_orig, col_emp, col_gen = load_data()

with st.sidebar:
    st.markdown(f"<b>👤 Sesión Activa:</b> {usuario_actual}", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.switch_page("app.py")
        st.rerun()
    st.divider()

if df_orig is not None:
    df_activos = df_orig[df_orig["LOTE"] == df_orig["NUM_GALPON"]].copy()

    hoy_date = datetime.date.today()
    ayer_date = hoy_date - datetime.timedelta(days=1)
    hace_mes_date = ayer_date - datetime.timedelta(days=30)

    f_max_data = df_activos["Fecha_DT"].max()
    f_min_data = df_activos["Fecha_DT"].min()

    if pd.notnull(f_max_data):
        max_permitido = f_max_data.date()
        min_permitido = f_min_data.date()
    else:
        max_permitido = ayer_date
        min_permitido = hace_mes_date

    # --- PANEL DE FILTROS ---
    st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
    st.markdown("#### 🎛️ Parámetros de Emisión del Informe")

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        empresas_disp = sorted([x for x in df_activos[col_emp].unique() if pd.notna(x) and str(x).strip() != "nan"])
        empresa_sel = st.selectbox("🏢 1. Razón Social:", empresas_disp)

    color_p, color_s = obtener_color_empresa(empresa_sel)
    df_emp = df_activos[df_activos[col_emp] == empresa_sel].copy()

    with f2:
        val_ini_default = max(min_permitido, min(hace_mes_date, max_permitido))
        val_fin_default = min(max_permitido, ayer_date)

        rango_fechas = st.date_input(
            "📅 2. Rango de Fechas:",
            value=(val_ini_default, val_fin_default),
            min_value=min_permitido,
            max_value=max_permitido,
            help="Inicializado en HOY() - 1 - 30 días."
        )

    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        f_inicio, f_fin = rango_fechas
    else:
        f_inicio = f_fin = rango_fechas[0] if isinstance(rango_fechas, tuple) else rango_fechas

    df_emp_fechas = df_emp[
        (df_emp["Fecha_DT"].dt.date >= f_inicio) & 
        (df_emp["Fecha_DT"].dt.date <= f_fin)
    ].copy()

    with f3:
        granjas_emp = sorted(df_emp_fechas["GRANJA"].unique())
        st.markdown("<label style='font-size:14px; font-weight:400; margin-bottom:4px; display:block;'>MAPA 3. Filtrar Granjas:</label>", unsafe_allow_html=True)

        for g in granjas_emp:
            if f"chk_inf_gr_{g}" not in st.session_state:
                st.session_state[f"chk_inf_gr_{g}"] = True

        granjas_sel = [g for g in granjas_emp if st.session_state.get(f"chk_inf_gr_{g}", True)]

        with st.popover(f"Granjas ({len(granjas_sel)}/{len(granjas_emp)})", use_container_width=True):
            b1, b2 = st.columns(2)
            if b1.button("Marcar todo", key="btn_inf_gr_all"):
                for g in granjas_emp: st.session_state[f"chk_inf_gr_{g}"] = True
                st.rerun()
            if b2.button("Desmarcar", key="btn_inf_gr_none"):
                for g in granjas_emp: st.session_state[f"chk_inf_gr_{g}"] = False
                st.rerun()

            granjas_sel = [
                g for g in granjas_emp
                if st.checkbox(f"{g}", value=st.session_state.get(f"chk_inf_gr_{g}", True), key=f"chk_inf_gr_{g}")
            ]

    df_emp_granjas = df_emp_fechas[df_emp_fechas["GRANJA"].isin(granjas_sel)].copy()

    with f4:
        lotes_emp = sorted(df_emp_granjas["LOTE"].unique())
        st.markdown("<label style='font-size:14px; font-weight:400; margin-bottom:4px; display:block;'>📦 4. Filtrar Lotes:</label>", unsafe_allow_html=True)

        for lt in lotes_emp:
            if f"chk_inf_lt_{lt}" not in st.session_state:
                st.session_state[f"chk_inf_lt_{lt}"] = True

        lotes_sel = [lt for lt in lotes_emp if st.session_state.get(f"chk_inf_lt_{lt}", True)]

        with st.popover(f"Lotes ({len(lotes_sel)}/{len(lotes_emp)})", use_container_width=True):
            bl1, bl2 = st.columns(2)
            if bl1.button("Marcar todo", key="btn_inf_lt_all"):
                for lt in lotes_emp: st.session_state[f"chk_inf_lt_{lt}"] = True
                st.rerun()
            if bl2.button("Desmarcar", key="btn_inf_lt_none"):
                for lt in lotes_emp: st.session_state[f"chk_inf_lt_{lt}"] = False
                st.rerun()

            lotes_sel = [
                lt for lt in lotes_emp
                if st.checkbox(f"Lote {lt}", value=st.session_state.get(f"chk_inf_lt_{lt}", True), key=f"chk_inf_lt_{lt}")
            ]

    st.markdown("</div>", unsafe_allow_html=True)

    # --- HEADER DINÁMICO ---
    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, {color_p} 0%, {color_s} 100%); padding: 18px 24px; border-radius: 14px; color: #FFFFFF; margin-bottom: 20px; box-shadow: 0 8px 20px -4px rgba(0,0,0,0.25); display: flex; align-items: center; flex-wrap: wrap;">
            {logo_html}
            <div>
                <h1 style="color: #FFFFFF; font-size: 1.6rem; font-weight: 800; margin: 0;">Informe Gerencial y Diagnóstico Avícola</h1>
                <p style="color: #FDF2E9; margin: 2px 0 0 0; font-size: 0.88rem; opacity: 0.95;">Razón Social: <b>{empresa_sel}</b> • Matriz de Producción, Alertas Operativas y Descarga en PDF</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    txt_periodo = f"Del {f_inicio.strftime('%d/%b/%Y')} al {f_fin.strftime('%d/%b/%Y')}"

    if df_emp_fechas.empty:
        st.warning(f"⚠️ No se encontraron registros para **{empresa_sel}** en el rango seleccionado ({txt_periodo}).")
    elif not granjas_sel or not lotes_sel:
        st.info("💡 Por favor selecciona al menos una granja y un lote para emitir el informe.")
    else:
        df_final = df_emp_granjas[df_emp_granjas["LOTE"].isin(lotes_sel)].copy()

        df_costos_validos = df_final[(df_final["$ Huevo por alimento"] > 0) & (df_final["Costo Alimento Sem"] > 0)].copy()

        df_final["Suma_Clasificacion"] = (
            df_final["Jumbo"] + df_final["Extra"] + df_final["AA"] + 
            df_final["A"] + df_final["B"] + df_final["C"]
        )
        df_clas_valida = df_final[df_final["Suma_Clasificacion"] > 0].copy()

        # CÁLCULOS GENERALES AUDITADOS
        total_huevos = df_final["Huevos  Semana"].sum()
        total_costo_valido = df_costos_validos["Costo Alimento Sem"].sum()
        total_huevos_costo_valido = df_costos_validos["Huevos  Semana"].sum()
        
        costo_prom_huevo = total_costo_valido / total_huevos_costo_valido if total_huevos_costo_valido > 0 else 0
        total_bultos = df_final["Bulto X 40 K"].sum()
        total_toneladas = (total_bultos * 40) / 1000.0
        
        conv_prom = (total_bultos * 40000) / total_huevos if total_huevos > 0 else 0
        pdn_prom = df_final["% Pdn. Real"].mean()

        st.markdown("### 📄 Documento Oficial de Auditoría y Diagnóstico Operativo")
        
        with st.container():
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, {color_p}, {color_s}); color: white; padding: 22px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem; font-weight: 800;">{empresa_sel}</h2>
                    <p style="margin: 5px 0 0 0; color: #FDF2E9; font-size: 0.9rem;"><b>Informe Gerencial y Diagnóstico de Ejecución (Relación Granja-Lote)</b> • Período: {txt_periodo}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # KPIS GENERALES (ACTUALIZADO: COSTO / HUEVO POR ALIMENTO)
            k1, k2, k3, k4 = st.columns(4)
            card_style = f'background-color: var(--secondary-background-color); border-radius: 10px; padding: 14px; border: 1px solid rgba(128,128,128,0.2); border-top: 4px solid {color_p}; text-align: center;'
            
            with k1:
                st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">PRODUCCIÓN REAL</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">{pdn_prom:.1f}%</div></div>', unsafe_allow_html=True)
            with k2:
                st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">ALIMENTO CONSUMIDO</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">{total_toneladas:,.1f} Ton</div></div>', unsafe_allow_html=True)
            with k3:
                st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">COSTO / HUEVO POR ALIMENTO</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">${costo_prom_huevo:.1f}</div></div>', unsafe_allow_html=True)
            with k4:
                st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">CONVERSIÓN PONDERADA</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">{conv_prom:.1f} g</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SECCIÓN 1: CONSOLIDADO ORDENADO POR EDAD SEMANAL ---
            st.markdown("#### 1. Consolidado de Ejecución por Granja y Lote (Ordenado de Mayor a Menor Edad)")
            
            res_lotes = []
            alertas_lista = []

            for (g_name, lt_num), g_df in df_final.groupby(["GRANJA", "LOTE"]):
                g_df_costos = g_df[(g_df["$ Huevo por alimento"] > 0) & (g_df["Costo Alimento Sem"] > 0)]
                
                fases_unicas = sorted([str(x) for x in g_df["Fase de Alimento"].unique() if pd.notna(x) and str(x).strip() not in ["0", "nan"]])
                str_fases = ", ".join(fases_unicas) if fases_unicas else "Sin Especificar"

                genetica_vals = sorted([str(x) for x in g_df[col_gen].unique() if pd.notna(x) and str(x).strip() not in ["0", "nan", "N/A"]])
                str_genetica = ", ".join(genetica_vals) if genetica_vals else "Sin Especificar"

                h_g = g_df["Huevos  Semana"].sum()
                c_g = g_df_costos["Costo Alimento Sem"].sum()
                b_g = g_df["Bulto X 40 K"].sum()
                ton_lote = (b_g * 40) / 1000.0
                h_g_costo = g_df_costos["Huevos  Semana"].sum()

                costo_h = c_g / h_g_costo if h_g_costo > 0 else 0
                conv_g = (b_g * 40000) / h_g if h_g > 0 else 0
                pdn_g = g_df["% Pdn. Real"].mean()
                aves_g = g_df["Saldo de Aves"].mean()
                edad_g = g_df["Edad Sem."].max()

                pct_segunda = (g_df["Alt Cáscara"] + g_df["Picado"] + g_df["Roto"]).mean() * 100

                motivos_alerta = []
                if pdn_g < 80.0:
                    motivos_alerta.append(f"Postura baja ({pdn_g:.1f}%)")
                if conv_g > 142.0:
                    motivos_alerta.append(f"Conversión elevada ({conv_g:.1f}g)")
                if costo_h > (costo_prom_huevo * 1.15) and costo_h > 0:
                    motivos_alerta.append(f"Costo/Huevo desfasado (${costo_h:.1f})")
                if pct_segunda > 5.0:
                    motivos_alerta.append(f"Alto % Segunda/Roto ({pct_segunda:.1f}%)")

                estado_lote = "⚠️ Revisa Atención" if motivos_alerta else "✅ Óptimo"

                if motivos_alerta:
                    alertas_lista.append({
                        "Granja": g_name,
                        "Lote": lt_num,
                        "Edad": f"{edad_g:.0f} Sem",
                        "Problemas Detectados": ", ".join(motivos_alerta),
                    })

                res_lotes.append({
                    "Granja": g_name,
                    "Lote": f"Lote {lt_num}",
                    "Edad_Num": edad_g,
                    "Edad Sem.": f"{edad_g:.0f} Sem",
                    "Línea Genética": str_genetica,
                    "Aves_Num": aves_g,
                    "Aves Activas": f"{aves_g:,.0f}",
                    "Fase Alimento": str_fases,
                    "Toneladas_Num": ton_lote,
                    "Consumo (Ton)": f"{ton_lote:,.1f} Ton",
                    "Pdn_Num": pdn_g,
                    "% Pdn. Real": f"{pdn_g:.1f}%",
                    "$/Huevo x Alimento": f"${costo_h:.1f}" if costo_h > 0 else "Sin Registro",
                    "Conversión (g)": f"{conv_g:.1f} g",
                    "Estado": estado_lote
                })

            df_tabla_lotes = pd.DataFrame(res_lotes)

            # ORDENAMIENTO POR EDAD DESCENDENTE
            df_tabla_lotes = df_tabla_lotes.sort_values(by="Edad_Num", ascending=False).reset_index(drop=True)

            # FILA DE RESUMEN Y TOTALES
            total_aves_sum = df_tabla_lotes["Aves_Num"].sum()
            total_ton_sum = df_tabla_lotes["Toneladas_Num"].sum()
            prom_edad_val = df_tabla_lotes["Edad_Num"].mean()
            prom_pdn_val = df_tabla_lotes["Pdn_Num"].mean()

            fila_totales = {
                "Granja": "TOTAL / PROMEDIOS",
                "Lote": f"{len(df_tabla_lotes)} Lotes",
                "Edad Sem.": f"{prom_edad_val:.0f} Sem (Prom)",
                "Línea Genética": "Varias",
                "Aves Activas": f"{total_aves_sum:,.0f} (Total)",
                "Fase Alimento": "Consolidado",
                "Consumo (Ton)": f"{total_ton_sum:,.1f} Ton",
                "% Pdn. Real": f"{prom_pdn_val:.1f}% (Prom)",
                "$/Huevo x Alimento": f"${costo_prom_huevo:.1f} (Prom)",
                "Conversión (g)": f"{conv_prom:.1f} g (Prom)",
                "Estado": "📊 RESUMEN"
            }

            df_display_clean = df_tabla_lotes[["Granja", "Lote", "Edad Sem.", "Línea Genética", "Aves Activas", "Fase Alimento", "Consumo (Ton)", "% Pdn. Real", "$/Huevo x Alimento", "Conversión (g)", "Estado"]].copy()
            df_display_final = pd.concat([df_display_clean, pd.DataFrame([fila_totales])], ignore_index=True)

            st.dataframe(df_display_final, use_container_width=True, hide_index=True)

            # --- SECCIÓN 2: CASA NUTRICIONAL ---
            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            st.markdown("#### 🥗 2. Casa Nutricional: Participación por Línea Genética y Fase de Alimento")

            g_c1, g_c2 = st.columns(2)

            with g_c1:
                # 1. PORCENTAJE POR LÍNEA GENÉTICA (AVES ACTIVAS)
                df_pie_gen = df_final.groupby(col_gen)["Saldo de Aves"].mean().reset_index()
                df_pie_gen.columns = ["Línea Genética", "Aves"]
                df_pie_gen["Línea Genética"] = df_pie_gen["Línea Genética"].astype(str).replace(["0", "nan", ""], "Sin Especificar")

                fig_gen = px.pie(
                    df_pie_gen,
                    names="Línea Genética",
                    values="Aves",
                    hole=0.45,
                    title="<b>% PARTICIPACIÓN POR LÍNEA GENÉTICA (AVES)</b>",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_gen.update_traces(
                    textposition='inside',
                    textinfo='percent',
                    hovertemplate="<b>%{label}</b><br>Aves: %{value:,.0f}<br>Participación: <b>%{percent}</b>"
                )
                fig_gen.update_layout(
                    height=380,
                    margin=dict(t=50, b=20, l=20, r=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.02,
                        font=dict(size=12)
                    )
                )
                st.plotly_chart(fig_gen, use_container_width=True, config={"displayModeBar": False})

            with g_c2:
                # 2. PORCENTAJE POR FASE DE ALIMENTO (TONELADAS CONSUMIDAS)
                df_pie_fase = df_final.groupby("Fase de Alimento")["Bulto X 40 K"].sum().reset_index()
                df_pie_fase["Toneladas"] = (df_pie_fase["Bulto X 40 K"] * 40) / 1000.0
                df_pie_fase["Fase de Alimento"] = df_pie_fase["Fase de Alimento"].astype(str).replace(["0", "nan", ""], "Sin Especificar")

                fig_fase = px.pie(
                    df_pie_fase,
                    names="Fase de Alimento",
                    values="Toneladas",
                    hole=0.45,
                    title="<b>% PARTICIPACIÓN POR FASE DE ALIMENTO (TONELADAS)</b>",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_fase.update_traces(
                    textposition='inside',
                    textinfo='percent',
                    hovertemplate="<b>%{label}</b><br>Consumo: %{value:,.1f} Ton<br>Participación: <b>%{percent}</b>"
                )
                fig_fase.update_layout(
                    height=380,
                    margin=dict(t=50, b=20, l=20, r=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.02,
                        font=dict(size=12)
                    )
                )
                st.plotly_chart(fig_fase, use_container_width=True, config={"displayModeBar": False})

            # --- SECCIÓN 3: DIAGNÓSTICO Y SOLUCIONES ---
            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            st.markdown("#### 🚨 3. Diagnóstico: ¿A qué Granjas y Lotes debemos prestar más atención?")

            if not alertas_lista:
                st.success("🎉 **Excelente Desempeño Operativo**: Todos los lotes evaluados en este periodo están operando dentro de los parámetros técnicos normales.")
            else:
                st.warning(f"⚠️ Se han identificado **{len(alertas_lista)} Lotes con desviaciones técnicas y financieras** que requieren intervención gerencial:")

                col_prob, col_sol = st.columns(2)

                with col_prob:
                    st.markdown(
                        """
                        <div class="callout-problem">
                            <b style="color:#C0392B; font-size:1.05rem;">🔍 Muestrario de Problemas Detectados:</b>
                            <ul style="margin-top:8px; font-size:0.88rem; padding-left:18px;">
                        """,
                        unsafe_allow_html=True
                    )
                    for item in alertas_lista:
                        st.markdown(f"<li><b>{item['Granja']} - Lote {item['Lote']}</b> ({item['Edad']}): <br><span style='color:#C0392B;'>• {item['Problemas Detectados']}</span></li><br>", unsafe_allow_html=True)
                    st.markdown("</ul></div>", unsafe_allow_html=True)

                with col_sol:
                    st.markdown(
                        """
                        <div class="callout-solution">
                            <b style="color:#27AE60; font-size:1.05rem;">💡 Plan de Acción y Soluciones Recomendadas:</b>
                            <ul style="margin-top:8px; font-size:0.88rem; padding-left:18px;">
                                <li><b>Para Lotes con Conversión Alta (> 142g):</b> Auditar desperdicio en comederos, calibración de cortinas y nivel de energía metabólica en la fase de alimento.</li>
                                <li><b>Para Lotes con Alto % de Segunda (> 5%):</b> Ajustar niveles de Calcio/Fósforo en dieta, revisar frecuencia de recogida de huevo y estado de mallas/bandejas.</li>
                                <li><b>Para Lotes con Postura Baja (< 80%):</b> Realizar perfilaje sanitario (muestreo de serología) y verificar uniforme consumo de agua.</li>
                            </ul>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # --- SECCIÓN 4: TABLA DETALLADA DE CLASIFICACIÓN ---
            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            st.markdown("#### 4. Tabla Detallada de Perfil Comercial")

            if not df_clas_valida.empty:
                prom_g = (df_clas_valida["Jumbo"] + df_clas_valida["Extra"] + df_clas_valida["AA"]).mean() * 100
                prom_m = df_clas_valida["A"].mean() * 100
                prom_p = (df_clas_valida["B"] + df_clas_valida["C"]).mean() * 100
                
                prom_b = df_clas_valida["Alt. Color"].mean() * 100
                prom_s = (df_clas_valida["Alt Cáscara"] + df_clas_valida["Picado"] + df_clas_valida["Roto"]).mean() * 100
            else:
                prom_g = prom_m = prom_p = prom_b = prom_s = 0.0

            res_clasificacion = [
                {"Categoría Comercial": "💎 Huevo Grande", "Detalle Gramaje / Tipo": "Jumbo + Extra + AA", "% Participación Mes": f"{prom_g:.1f}%"},
                {"Categoría Comercial": "🥚 Huevo Mediano", "Detalle Gramaje / Tipo": "Categoría A", "% Participación Mes": f"{prom_m:.1f}%"},
                {"Categoría Comercial": "🐣 Huevo Pequeño", "Detalle Gramaje / Tipo": "Categorías B + C", "% Participación Mes": f"{prom_p:.1f}%"},
                {"Categoría Comercial": "⚪ Huevo Blanco", "Detalle Gramaje / Tipo": "Alt. Color (Independiente)", "% Participación Mes": f"{prom_b:.1f}%"},
                {"Categoría Comercial": "⚠️ Segunda / Descarte", "Detalle Gramaje / Tipo": "Cáscara, Picado, Roto", "% Participación Mes": f"{prom_s:.1f}%"},
            ]

            df_tabla2 = pd.DataFrame(res_clasificacion)
            st.dataframe(df_tabla2, use_container_width=True, hide_index=True)

        # GENERADOR HTML PDF
        def generar_pdf_html(emp_nombre, df_ordered, t2_data, alertas, tot_row, c_prim, c_sec, logo_tag, ton_tot):
            rows_1 = ""
            for _, r in df_ordered.iterrows():
                rows_1 += f"<tr><td>{r['Granja']}</td><td>{r['Lote']}</td><td>{r['Edad Sem.']}</td><td>{r['Línea Genética']}</td><td>{r['Aves Activas']}</td><td>{r['Fase Alimento']}</td><td>{r['Consumo (Ton)']}</td><td>{r['% Pdn. Real']}</td><td>{r['$/Huevo x Alimento']}</td><td>{r['Conversión (g)']}</td><td>{r['Estado']}</td></tr>"
            
            row_tot_html = f"<tr style='background-color:#FDF2E9; font-weight:bold; border-top:2px solid {c_prim};'><td>{tot_row['Granja']}</td><td>{tot_row['Lote']}</td><td>{tot_row['Edad Sem.']}</td><td>{tot_row['Línea Genética']}</td><td>{tot_row['Aves Activas']}</td><td>{tot_row['Fase Alimento']}</td><td>{tot_row['Consumo (Ton)']}</td><td>{tot_row['% Pdn. Real']}</td><td>{tot_row['$/Huevo x Alimento']}</td><td>{tot_row['Conversión (g)']}</td><td>{tot_row['Estado']}</td></tr>"
            
            rows_2 = "".join([f"<tr><td>{r['Categoría Comercial']}</td><td>{r['Detalle Gramaje / Tipo']}</td><td style='font-weight:bold;'>{r['% Participación Mes']}</td></tr>" for r in t2_data])
            
            p_text = "".join([f"<li><b>{a['Granja']} - Lote {a['Lote']}</b> ({a['Edad']}): <span style='color:#C0392B;'>{a['Problemas Detectados']}</span></li>" for a in alertas]) if alertas else "<li>No se registraron desviaciones severas en el periodo.</li>"

            html_str = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Informe Gerencial - {emp_nombre}</title>
    <style>
        @page {{ size: A4; margin: 12mm; }}
        body {{ font-family: Arial, sans-serif; padding: 20px; color: #2C3E50; background: white; }}
        .banner {{ background: linear-gradient(135deg, {c_prim}, {c_sec}); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; }}
        .banner-text h1 {{ margin: 0; font-size: 22px; color: white; }}
        .banner-text p {{ margin: 5px 0 0 0; font-size: 13px; opacity: 0.95; color: white; }}
        .kpi-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 20px; }}
        .kpi-box {{ flex: 1; background: #FAFAFA; border-top: 4px solid {c_prim}; border-radius: 6px; padding: 12px; text-align: center; border: 1px solid #E0E0E0; }}
        .kpi-title {{ font-size: 11px; font-weight: bold; color: #7F8C8D; text-transform: uppercase; }}
        .kpi-val {{ font-size: 18px; font-weight: bold; color: {c_prim}; margin-top: 4px; }}
        h2 {{ color: {c_prim}; font-size: 15px; border-left: 4px solid {c_prim}; padding-left: 8px; margin-top: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; }}
        th {{ background: {c_prim}; color: white; padding: 7px; text-align: center; font-size: 11px; }}
        td {{ padding: 6px; border-bottom: 1px solid #EEE; text-align: center; }}
        tr:nth-child(even) {{ background-color: #FAFAFA; }}
        .alert-box {{ background: #FDEDEC; border-left: 4px solid #C0392B; padding: 12px; border-radius: 6px; margin: 15px 0; }}
        .sol-box {{ background: #EAFAF1; border-left: 4px solid #27AE60; padding: 12px; border-radius: 6px; margin: 15px 0; }}
        .footer {{ text-align: center; font-size: 10px; color: #95A5A6; border-top: 1px solid #DDD; padding-top: 10px; margin-top: 30px; }}
    </style>
</head>
<body onload="window.print()">
    <div class="banner">
        {logo_tag}
        <div class="banner-text">
            <h1>{emp_nombre}</h1>
            <p><b>Informe Gerencial y Diagnóstico de Ejecución</b> • Período: {txt_periodo}</p>
        </div>
    </div>

    <div class="kpi-container">
        <div class="kpi-box"><div class="kpi-title">PRODUCCIÓN REAL</div><div class="kpi-val">{pdn_prom:.1f}%</div></div>
        <div class="kpi-box"><div class="kpi-title">ALIMENTO CONSUMIDO</div><div class="kpi-val">{ton_tot:,.1f} Ton</div></div>
        <div class="kpi-box"><div class="kpi-title">COSTO / HUEVO POR ALIMENTO</div><div class="kpi-val">${costo_prom_huevo:.1f}</div></div>
        <div class="kpi-box"><div class="kpi-title">CONVERSIÓN PONDERADA</div><div class="kpi-val">{conv_prom:.1f} g</div></div>
    </div>

    <h2>1. Consolidado de Ejecución por Granja y Lote (Ordenado de Mayor a Menor Edad)</h2>
    <table>
        <thead>
            <tr><th>Granja</th><th>Lote</th><th>Edad Sem.</th><th>Línea Genética</th><th>Aves</th><th>Fase</th><th>Consumo</th><th>Pdn %</th><th>$/Huevo x Alimento</th><th>Conversión</th><th>Estado</th></tr>
        </thead>
        <tbody>{rows_1}{row_tot_html}</tbody>
    </table>

    <h2>2. Diagnóstico de Puntos Críticos y Soluciones</h2>
    <div class="alert-box">
        <b style="color:#C0392B;">🔍 Muestrario de Problemas Detectados:</b>
        <ul style="margin: 6px 0 0 0; padding-left: 20px;">{p_text}</ul>
    </div>
    <div class="sol-box">
        <b style="color:#27AE60;">💡 Plan de Acción Recomendado:</b>
        <ul style="margin: 6px 0 0 0; padding-left: 20px;">
            <li><b>Conversión Alta (>142g):</b> Auditar desperdicios en comederos y nivel de energía metabólica.</li>
            <li><b>Alto % Segunda (>5%):</b> Ajustar niveles de Calcio/Fósforo y frecuencia de recolección de huevo.</li>
            <li><b>Postura Baja (<80%):</b> Realizar perfilaje sanitario y verificar uniformidad de consumo de agua.</li>
        </ul>
    </div>

    <h2>3. Perfil Comercial de Huevo</h2>
    <table>
        <thead>
            <tr><th>Categoría Comercial</th><th>Detalle Gramaje / Tipo</th><th>% Participación</th></tr>
        </thead>
        <tbody>{rows_2}</tbody>
    </table>

    <div class="footer"><b>HUPA | División Avícola</b> • Documento Oficial Autogenerado • Confidencial</div>
</body>
</html>"""
            return html_str

        html_pdf = generar_pdf_html(empresa_sel, df_tabla_lotes, res_clasificacion, alertas_lista, fila_totales, color_p, color_s, logo_html, total_toneladas)

        # BOTONES DE EXPORTACIÓN DIRECTOS
        st.markdown("<br>", unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)

        with btn_c1:
            st.download_button(
                label=f"🖨️ Descargar Documento Listo para Guardar PDF ({empresa_sel})",
                data=html_pdf.encode("utf-8"),
                file_name=f"Informe_Gerencial_{empresa_sel.replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True,
                help="Abre el informe preparado para guardarse como PDF en 1 clic."
            )

        with btn_c2:
            st.download_button(
                label=f"📊 Descargar Matriz Consolidada en Excel (.csv)",
                data=df_final.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Consolidado_Diagnostico_{empresa_sel.replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

else:
    st.error("⚠️ No se pudo cargar el archivo Consolidado_Produccion_FINAL.xlsx")

st.divider()
st.markdown(
    "<div style='text-align:center; opacity:0.6;'><b>HUPA | División Avícola</b> - Análisis de Datos para la Excelencia Productiva</div>",
    unsafe_allow_html=True,
)