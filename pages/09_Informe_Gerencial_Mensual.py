import base64
import datetime
import io
import os
from fpdf import FPDF
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

    .ieb-card-ui {
        background-color: rgba(41, 128, 185, 0.08);
        border-left: 4px solid #2980B9;
        padding: 14px 16px;
        border-radius: 8px;
        font-size: 0.88rem;
        line-height: 1.5;
        height: 100%;
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
            for c in ["EMPRESA", "RAZON_SOCIAL", "RAZON SOCIAL", "SOCIEDAD", "Razon Social", "Razón Social", "RS"]:
                if c in df.columns:
                    col_empresa = c
                    break
            
            if not col_empresa:
                df["EMPRESA"] = "HUPA | DIVISIÓN AVÍCOLA"
                col_empresa = "EMPRESA"
            else:
                df[col_empresa] = df[col_empresa].astype(str).str.strip()

            # Detectar columna GALPON
            col_galpon = None
            for cg in ["GALPON", "GALPÓN", "NUM_GALPON", "NUM GALPON", "Galpon", "Galpón"]:
                if cg in df.columns:
                    col_galpon = cg
                    break

            # FILTRO FLEXIBLE DE ORO: COMPARACIÓN NUMÉRICA PARA INCLUIR FELISA 63
            if col_galpon and "LOTE" in df.columns:
                lote_num = pd.to_numeric(df["LOTE"].astype(str).str.extract(r'(\d+)')[0], errors='coerce')
                galpon_num = pd.to_numeric(df[col_galpon].astype(str).str.extract(r'(\d+)')[0], errors='coerce')
                
                # Mantenemos las filas donde coinciden o donde galpon/lote sean válidos
                mask_valida = (lote_num == galpon_num) | (lote_num.isna() & galpon_num.isna())
                df = df[mask_valida].copy()

            if "Final Sem" in df.columns:
                df["Fecha_DT"] = pd.to_datetime(df["Final Sem"], errors="coerce")
                df["Fecha_Fmt"] = df["Fecha_DT"].dt.strftime("%d/%b/%Y")
            elif "F. Fin De Sem" in df.columns:
                df["Fecha_DT"] = pd.to_datetime(df["F. Fin De Sem"], errors="coerce")
                df["Fecha_Fmt"] = df["Fecha_DT"].dt.strftime("%d/%b/%Y")
            else:
                df["Fecha_DT"] = pd.NaT
                df["Fecha_Fmt"] = "N/A"

            if "Fase de Alimento" not in df.columns:
                df["Fase de Alimento"] = "Sin Especificar"
            else:
                df["Fase de Alimento"] = df["Fase de Alimento"].fillna("Sin Especificar").astype(str).str.strip()
                df["Fase de Alimento"] = df["Fase de Alimento"].replace(["0", "nan", "0.0", "N/A", "", "None", "NaN"], "Sin Especificar")

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
                df[col_linea] = df[col_linea].fillna("Sin Especificar").astype(str).str.strip()
                df[col_linea] = df[col_linea].replace(["0", "nan", "0.0", "N/A", "", "None", "NaN"], "Sin Especificar")

            col_mort = None
            for cm in ["Mort", "Mortalidad", "Aves Muertas", "Bajas", "MORT"]:
                if cm in df.columns:
                    col_mort = cm
                    break
            if not col_mort:
                df["Mort"] = 0
                col_mort = "Mort"

            col_pdn_tabla = None
            for ct in ["Pdn tabla", "Pdn Tabla", "Pdn_Tabla", "% Pdn. Tabla", "% Pdn Tabla", "Guia Pdn", "Pdn Gui"]:
                if ct in df.columns:
                    col_pdn_tabla = ct
                    break
            if not col_pdn_tabla:
                df["Pdn tabla"] = 0.0
                col_pdn_tabla = "Pdn tabla"

            num_cols = [
                "Edad Sem.", "Huevos  Semana", "Costo Alimento Sem",
                "$ Huevo por alimento", "Bulto X 40 K", "Jumbo", "Extra",
                "AA", "A", "B", "C", "Alt Cáscara", "Alt. Color", "Picado", "Roto", 
                "% Pdn. Real", col_pdn_tabla, "Saldo de Aves", "Saldo Aves", col_mort
            ]
            for col in [c for c in num_cols if c in df.columns]:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

            if "Saldo Aves" in df.columns and "Saldo de Aves" not in df.columns:
                df["Saldo de Aves"] = df["Saldo Aves"]

            return df, col_empresa, col_linea, col_mort, col_pdn_tabla
        except Exception as e:
            st.error(f"Error al cargar datos: {e}")
            return None, None, None, None, None
    return None, None, None, None, None


df_orig, col_emp, col_gen, col_mortalidad_num, col_pdn_tabla = load_data()

with st.sidebar:
    st.markdown(f"<b>👤 Sesión Activa:</b> {usuario_actual}", unsafe_allow_html=True)
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.auth = False
        st.switch_page("app.py")
        st.rerun()
    st.divider()

if df_orig is not None:
    df_activos = df_orig.copy()

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
        st.markdown("<label style='font-size:14px; font-weight:400; margin-bottom:4px; display:block;'>🗺️ 3. Filtrar Granjas:</label>", unsafe_allow_html=True)

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
                <p style="color: #FDF2E9; margin: 2px 0 0 0; font-size: 0.88rem; opacity: 0.95;">Razón Social: <b>{empresa_sel}</b> • <i>"Presente en la mesa de los colombianos"</i></p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    txt_periodo = f"Del {f_inicio.strftime('%d/%b/%Y')} al {f_fin.strftime('%d/%b/%Y')}"

    if df_emp_fechas.empty:
        st.warning(f"⚠️ No se encontraron registros coincidentes para **{empresa_sel}** en el rango ({txt_periodo}).")
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

        col_archivo = next((ca for ca in ["ARCHIVO_ORIGEN", "Archivo_Origen", "archivo_origen", "ARCHIVO", "Archivo", "archivo"] if ca in df_final.columns), None)

        group_cols = ["GRANJA", "LOTE"]
        if col_archivo:
            group_cols.append(col_archivo)

        res_lotes = []
        alertas_lista = []
        lotes_descarte_lista = []
        lotes_base_dict = {}

        for group_keys, g_df in df_final.groupby(group_cols):
            if col_archivo:
                g_name, lt_num, arch_val = group_keys
                arch_clean = str(arch_val).split("/")[-1].split("\\")[-1].replace(".xlsx", "").replace(".csv", "")
            else:
                g_name, lt_num = group_keys
                arch_clean = "N/A"

            lote_num_str = str(lt_num)
            lote_key = (g_name, lt_num, arch_clean)

            g_df_costos = g_df[(g_df["$ Huevo por alimento"] > 0) & (g_df["Costo Alimento Sem"] > 0)]
            
            fases_unicas = sorted([str(x) for x in g_df["Fase de Alimento"].unique() if pd.notna(x) and str(x).strip() not in ["0", "nan"]])
            str_fases = ", ".join(fases_unicas) if fases_unicas else "Sin Especificar"

            genetica_vals = sorted([str(x) for x in g_df[col_gen].unique() if pd.notna(x) and str(x).strip() not in ["0", "nan", "N/A"]])
            str_genetica = genetica_vals[0] if genetica_vals else "Sin Especificar"

            h_g = g_df["Huevos  Semana"].sum()
            c_g = g_df_costos["Costo Alimento Sem"].sum()
            b_g = g_df["Bulto X 40 K"].sum()
            ton_lote = (b_g * 40) / 1000.0
            h_g_costo = g_df_costos["Huevos  Semana"].sum()

            costo_h = c_g / h_g_costo if h_g_costo > 0 else 0
            conv_g = (b_g * 40000) / h_g if h_g > 0 else 0
            pdn_g = g_df["% Pdn. Real"].mean()
            pdn_tabla_g = g_df[col_pdn_tabla].mean()
            dif_pdn_val = pdn_g - pdn_tabla_g

            # CENSO EXACTO EN LA ÚLTIMA FECHA DISPONIBLE DEL LOTE
            max_fecha_lote = g_df["Fecha_DT"].max()
            df_max_fecha = g_df[g_df["Fecha_DT"] == max_fecha_lote]
            aves_g = df_max_fecha["Saldo de Aves"].iloc[-1] if not df_max_fecha.empty else g_df["Saldo de Aves"].max()

            edad_g = g_df["Edad Sem."].max()

            muertas_periodo = g_df[col_mortalidad_num].sum()
            poblacion_base = max(aves_g + muertas_periodo, g_df["Saldo de Aves"].max())
            mort_pct_periodo = (muertas_periodo / poblacion_base * 100.0) if poblacion_base > 0 else 0.0

            lotes_base_dict[lote_key] = {
                "Granja": g_name,
                "Lote": lote_num_str,
                "Genética": str_genetica,
                "Censo_Aves": aves_g,
                "Toneladas": ton_lote,
                "Pdn_Prom": pdn_g,
                "Muertas_Tot": muertas_periodo
            }

            viabilidad_periodo = max(0.0, 100.0 - mort_pct_periodo)
            ieb_score = min(100.0, max(0.0, (pdn_g * 0.50) + ((200.0 - conv_g) * 0.35) + (viabilidad_periodo * 0.15)))

            if edad_g > 75:
                lotes_descarte_lista.append({"Granja": g_name, "Lote": f"Lote {lote_num_str}", "Edad": edad_g, "Aves": aves_g})

            pct_segunda = (g_df["Alt Cáscara"] + g_df["Picado"] + g_df["Roto"]).mean() * 100

            motivos_alerta = []
            if pdn_tabla_g > 0:
                if dif_pdn_val < -2.0:
                    motivos_alerta.append(f"Postura {pdn_g:.1f}% por debajo de tabla {pdn_tabla_g:.1f}% (Brecha: {dif_pdn_val:.1f}%)")
            else:
                if pdn_g < 80.0:
                    motivos_alerta.append(f"Postura baja ({pdn_g:.1f}%)")

            if conv_g > 142.0:
                motivos_alerta.append(f"Conversión elevada ({conv_g:.1f}g)")
            if mort_pct_periodo > 1.5:
                motivos_alerta.append(f"Mortalidad periodo elevada ({mort_pct_periodo:.1f}% / {muertas_periodo:,.0f} aves)")
            if pct_segunda > 5.0:
                motivos_alerta.append(f"Alto % Segunda/Roto ({pct_segunda:.1f}%)")

            estado_lote = "⚠️ Revisa Atención" if motivos_alerta else "✅ Óptimo"

            if motivos_alerta:
                alertas_lista.append({
                    "Granja": g_name,
                    "Lote": f"Lote {lote_num_str}",
                    "Edad": f"{edad_g:.0f} Sem",
                    "Problemas Detectados": ", ".join(motivos_alerta),
                })

            item_lote = {
                "Granja": g_name,
                "Lote": lote_num_str,  # <--- SOLO NÚMERO
                "Edad_Num": edad_g,
                "Edad Sem.": f"{edad_g:.0f} Sem",
                "Línea Genética": str_genetica,
                "Aves_Num": aves_g,
                "Saldo de Aves": f"{aves_g:,.0f}",  # <--- RENOMBRADO A Saldo de Aves
                "Mort": f"{muertas_periodo:,.0f}",  # <--- RENOMBRADO A Mort Y SOLO NÚMERO
                "CASA NUTRICIONAL": str_fases,     # <--- RENOMBRADO A CASA NUTRICIONAL
                "Toneladas_Num": ton_lote,
                "Consumo (Ton)": f"{ton_lote:,.1f} Ton",
                "Pdn_Num": pdn_g,
                "% Pdn. Real": f"{pdn_g:.1f}%",
                "% Pdn. Tabla": f"{pdn_tabla_g:.1f}%", # <--- NUEVA COLUMNA PDN TABLA
                "Dif Pdn": f"{dif_pdn_val:+.1f}%",       # <--- NUEVA COLUMNA DIF PDN
                "Conversión (g)": f"{conv_g:.1f} g",
                "IEB (Pts)": f"{ieb_score:.1f} / 100",
                "Estado": estado_lote
            }

            if es_admin:
                item_lote["$/Huevo x Alimento"] = f"${costo_h:.1f}" if costo_h > 0 else "Sin Registro"

            res_lotes.append(item_lote)

        df_tabla_lotes = pd.DataFrame(res_lotes)

        # CÁLCULOS PONDERADOS GLOBALES
        df_unificado_lotes = pd.DataFrame(list(lotes_base_dict.values()))

        total_aves_sum = df_unificado_lotes["Censo_Aves"].sum()
        total_ton_sum = df_unificado_lotes["Toneladas"].sum()
        total_muertas_sum = df_unificado_lotes["Muertas_Tot"].sum()

        if total_aves_sum > 0:
            pdn_prom = (df_unificado_lotes["Pdn_Prom"] * df_unificado_lotes["Censo_Aves"]).sum() / total_aves_sum
            mort_pct_global = (total_muertas_sum / (total_aves_sum + total_muertas_sum)) * 100.0 if (total_aves_sum + total_muertas_sum) > 0 else 0.0
        else:
            pdn_prom = df_final["% Pdn. Real"].mean()
            mort_pct_global = 0.0

        total_huevos = df_final["Huevos  Semana"].sum()
        total_costo_valido = df_costos_validos["Costo Alimento Sem"].sum()
        total_huevos_costo_valido = df_costos_validos["Huevos  Semana"].sum()
        costo_prom_huevo = total_costo_valido / total_huevos_costo_valido if total_huevos_costo_valido > 0 else 0

        total_bultos = df_final["Bulto X 40 K"].sum()
        total_toneladas = (total_bultos * 40) / 1000.0
        conv_prom = (total_bultos * 40000) / total_huevos if total_huevos > 0 else 0

        viab_global = max(0.0, 100.0 - mort_pct_global)
        ieb_prom_global = min(100.0, max(0.0, (pdn_prom * 0.50) + ((200.0 - conv_prom) * 0.35) + (viab_global * 0.15)))

        pdn_tabla_prom_global = df_final[col_pdn_tabla].mean()
        dif_pdn_prom_global = pdn_prom - pdn_tabla_prom_global

        st.markdown("### 📄 Documento Oficial de Auditoría y Diagnóstico Operativo")
        
        with st.container():
            st.markdown(
                f"""
                <div style="background: linear-gradient(135deg, {color_p}, {color_s}); color: white; padding: 22px; border-radius: 10px; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #FFFFFF; font-size: 1.6rem; font-weight: 800;">{empresa_sel}</h2>
                    <p style="margin: 5px 0 0 0; color: #FDF2E9; font-size: 0.9rem;"><b>Informe Gerencial y Diagnóstico de Ejecución</b> • Período: {txt_periodo} • <i>"Presente en la mesa de los colombianos"</i></p>
                </div>
                """,
                unsafe_allow_html=True
            )

            k1, k2, k3, k4 = st.columns(4)
            card_style = f'background-color: var(--secondary-background-color); border-radius: 10px; padding: 14px; border: 1px solid rgba(128,128,128,0.2); border-top: 4px solid {color_p}; text-align: center;'
            
            with k1:
                st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">PRODUCCIÓN REAL</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">{pdn_prom:.1f}%</div></div>', unsafe_allow_html=True)
            with k2:
                st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">ALIMENTO CONSUMIDO</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">{total_toneladas:,.1f} Ton</div></div>', unsafe_allow_html=True)
            
            with k3:
                if es_admin:
                    st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">COSTO / HUEVO POR ALIMENTO</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">${costo_prom_huevo:.1f}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">MORTALIDAD DEL PERIODO</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">{total_muertas_sum:,.0f} Aves ({mort_pct_global:.1f}%)</div></div>', unsafe_allow_html=True)
            
            with k4:
                st.markdown(f'<div style="{card_style}"><div style="font-size: 0.78rem; font-weight: 700; opacity: 0.8; text-transform: uppercase;">CONVERSIÓN PONDERADA</div><div style="font-size: 1.5rem; font-weight: 800; color: {color_p}; margin: 4px 0;">{conv_prom:.1f} g</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("#### 1. Consolidado de Ejecución por Granja y Lote")

            df_tabla_lotes = df_tabla_lotes.sort_values(by="Edad_Num", ascending=False).reset_index(drop=True)

            prom_edad_val = df_tabla_lotes["Edad_Num"].mean() if not df_tabla_lotes.empty else 0

            fila_totales = {
                "Granja": "TOTAL / PROMEDIOS",
                "Lote": f"{len(df_tabla_lotes)} Registros",
                "Edad Sem.": f"{prom_edad_val:.0f} Sem (Prom)",
                "Línea Genética": "Varias",
                "Saldo de Aves": f"{total_aves_sum:,.0f}",
                "Mort": f"{total_muertas_sum:,.0f}",
                "CASA NUTRICIONAL": "Consolidado",
                "Consumo (Ton)": f"{total_ton_sum:,.1f} Ton",
                "% Pdn. Real": f"{pdn_prom:.1f}%",
                "% Pdn. Tabla": f"{pdn_tabla_prom_global:.1f}%",
                "Dif Pdn": f"{dif_pdn_prom_global:+.1f}%",
                "Conversión (g)": f"{conv_prom:.1f} g",
                "IEB (Pts)": f"{ieb_prom_global:.1f} / 100",
                "Estado": "📊 RESUMEN"
            }

            if es_admin:
                fila_totales["$/Huevo x Alimento"] = f"${costo_prom_huevo:.1f}"
                cols_display = ["Granja", "Lote", "Edad Sem.", "Línea Genética", "Saldo de Aves", "Mort", "CASA NUTRICIONAL", "Consumo (Ton)", "% Pdn. Real", "% Pdn. Tabla", "Dif Pdn", "$/Huevo x Alimento", "Conversión (g)", "IEB (Pts)", "Estado"]
            else:
                cols_display = ["Granja", "Lote", "Edad Sem.", "Línea Genética", "Saldo de Aves", "Mort", "CASA NUTRICIONAL", "Consumo (Ton)", "% Pdn. Real", "% Pdn. Tabla", "Dif Pdn", "Conversión (g)", "IEB (Pts)", "Estado"]

            df_display_clean = df_tabla_lotes[cols_display].copy()
            df_display_final = pd.concat([df_display_clean, pd.DataFrame([fila_totales])], ignore_index=True)

            st.dataframe(df_display_final, use_container_width=True, hide_index=True)

            col_ieb_exp1, col_ieb_exp2 = st.columns(2)
            with col_ieb_exp1:
                st.markdown(
                    """
                    <div class="ieb-card-ui">
                        <b>💡 ¿Qué es la columna IEB (Índice de Eficiencia Biológica)?</b><br>
                        Es la <b>nota de calificación del lote (0 a 100 Pts)</b> que evalúa el rendimiento integral combinando <b>Postura, Conversión y Mortalidad del periodo</b>:<br>
                        • 🟢 <b>85 - 100 Pts (Excelente):</b> Alta postura, excelente conversión y mínima mortalidad.<br>
                        • 🟡 <b>75 - 84 Pts (Normal):</b> Rendimiento dentro del estándar esperado.<br>
                        • 🔴 <b>Menos de 75 Pts (Alerta):</b> Caída en postura, sobreconsumo o bajas elevadas.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with col_ieb_exp2:
                st.markdown(
                    """
                    <div class="ieb-card-ui">
                        <b>📐 Fórmula y Ejemplo de Cálculo (Con Mortalidad del Periodo):</b><br>
                        <code>IEB = (% Postura x 0.50) + ((200 - Conversión) x 0.35) + ((100 - % Mort Periodo) x 0.15)</code><br><br>
                        • <b>Caso Real (Lote con 85% Postura, 140g Conversión y 0.2% Mort Mes):</b><br>
                        <code>IEB = (85 x 0.50) + ((200 - 140) x 0.35) + ((100 - 0.2) x 0.15)</code><br>
                        <code>IEB = 42.5 + 21.0 + 14.97</code> = <b>78.5 Pts</b>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            st.markdown("#### 2. Casa Nutricional: Participación por Línea Genética y Fase de Alimento")

            df_pie_gen = df_unificado_lotes.groupby("Genética").apply(
                lambda x: pd.Series({
                    "Aves": x["Censo_Aves"].sum(),
                    "% Pdn. Prom": (x["Pdn_Prom"] * x["Censo_Aves"]).sum() / x["Censo_Aves"].sum() if x["Censo_Aves"].sum() > 0 else 0
                }),
                include_groups=False
            ).reset_index()
            df_pie_gen.columns = ["Línea Genética", "Aves", "% Pdn. Prom"]

            tot_aves_p = df_pie_gen["Aves"].sum()
            df_pie_gen["% Participación"] = (df_pie_gen["Aves"] / tot_aves_p * 100) if tot_aves_p > 0 else 0

            df_pie_fase = df_final.groupby("Fase de Alimento", dropna=False)["Bulto X 40 K"].sum().reset_index()
            df_pie_fase["Fase de Alimento"] = df_pie_fase["Fase de Alimento"].fillna("Sin Especificar").astype(str).str.strip()
            df_pie_fase["Fase de Alimento"] = df_pie_fase["Fase de Alimento"].replace(["0", "nan", "0.0", "N/A", "", "None", "NaN"], "Sin Especificar")
            
            df_pie_fase = df_pie_fase.groupby("Fase de Alimento")["Bulto X 40 K"].sum().reset_index()
            df_pie_fase["Toneladas"] = (df_pie_fase["Bulto X 40 K"] * 40) / 1000.0
            
            tot_ton_p = df_pie_fase["Toneladas"].sum()
            df_pie_fase["% Participación"] = (df_pie_fase["Toneladas"] / tot_ton_p * 100) if tot_ton_p > 0 else 0

            g_c1, g_c2 = st.columns(2)

            with g_c1:
                fig_gen = px.pie(
                    df_pie_gen,
                    names="Línea Genética",
                    values="Aves",
                    hole=0.45,
                    title="<b>% PARTICIPACIÓN POR LÍNEA GENÉTICA (CENSO FINAL)</b>",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_gen.update_traces(
                    textposition='inside',
                    textinfo='percent',
                    hovertemplate="<b>%{label}</b><br>Censo Aves: %{value:,.0f}<br>Participación: <b>%{percent}</b>"
                )
                fig_gen.update_layout(
                    height=380,
                    margin=dict(t=50, b=20, l=20, r=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=12))
                )
                st.plotly_chart(fig_gen, use_container_width=True, config={"displayModeBar": False})

            with g_c2:
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
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=12))
                )
                st.plotly_chart(fig_fase, use_container_width=True, config={"displayModeBar": False})

            st.markdown('<div class="hr-custom"></div>', unsafe_allow_html=True)
            st.markdown("#### 🚨 3. Diagnóstico de Eficiencia Biológica y Plan de Reemplazo de Flota")

            c_audit1, c_audit2 = st.columns(2)

            with c_audit1:
                st.markdown(
                    """
                    <div style="background-color: rgba(192, 57, 43, 0.08); border-left: 4px solid #C0392B; padding: 16px; border-radius: 8px;">
                        <b style="color:#C0392B; font-size:1.1rem;">🔍 Desviaciones Técnicas Registradas:</b>
                        <p style="margin:6px 0; font-size:0.9rem;">Lotes con métricas por fuera de la curva estándar de producción (Evaluado vs Tabla de Raza con 2% tolerancia):</p>
                        <ul style="margin-top:10px; font-size:0.85rem; padding-left:18px;">
                    """,
                    unsafe_allow_html=True
                )
                if alertas_lista:
                    for a in alertas_lista:
                        st.markdown(f"<li><b>{a['Granja']} - {a['Lote']}</b> ({a['Edad']}): <span style='color:#C0392B;'>{a['Problemas Detectados']}</span></li>", unsafe_allow_html=True)
                else:
                    st.markdown("<li>✅ No se registraron desviaciones en el periodo.</li>", unsafe_allow_html=True)
                st.markdown("</ul></div>", unsafe_allow_html=True)

            with c_audit2:
                st.markdown(
                    """
                    <div style="background-color: rgba(211, 84, 0, 0.08); border-left: 4px solid #D35400; padding: 16px; border-radius: 8px;">
                        <b style="color:#D35400; font-size:1.1rem;">🐔 Semáforo de Descarte y Plan de Renuevo (>75 Semanas):</b>
                        <p style="margin:6px 0; font-size:0.9rem;">Lotes en etapa avanzada de ciclo con oportunidad de renovación:</p>
                    """,
                    unsafe_allow_html=True
                )
                if lotes_descarte_lista:
                    for d in lotes_descarte_lista:
                        st.markdown(f"• 🔴 <b>{d['Granja']} - {d['Lote']}</b>: {d['Edad']:.0f} Semanas | Censo: <b>{d['Aves']:,.0f} aves</b>.<br>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color:#27AE60;'>✅ No hay lotes en zona de descarte crítico (>75 Sem) en el periodo.</p>", unsafe_allow_html=True)
                
                st.markdown(
                    """
                    <div style="margin-top:12px; font-size:0.85rem; color:#555;">
                        <b>💡 Acción Recomendada:</b> Programar depuración sanitaria y rotación para lotes mayores a 75 semanas para optimizar conversión alimenticia global.
                    </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

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

        # GENERADOR PDF HTML LIMPIO Y CORREGIDO
        def generar_pdf_html(emp_nombre, df_ordered, t2_data, alertas, descarte_lotes, tot_row, c_prim, c_sec, logo_tag, ton_tot, df_gen_pct, df_fase_pct, logo_b64_str, pdn_global_val, es_adm):
            
            if es_adm:
                th_costo_col = "<th>$/Huevo x Alimento</th>"
                kpi_costo_html = f'<div class="kpi-box"><div class="kpi-title">COSTO / HUEVO POR ALIMENTO</div><div class="kpi-val">${costo_prom_huevo:.1f}</div></div>'
            else:
                th_costo_col = ""
                kpi_costo_html = f'<div class="kpi-box"><div class="kpi-title">MORTALIDAD DEL PERIODO</div><div class="kpi-val">{total_muertas_sum:,.0f} Aves ({mort_pct_global:.1f}%)</div></div>'

            rows_1 = ""
            for _, r in df_ordered.iterrows():
                val_costo_td = f"<td>{r['$/Huevo x Alimento']}</td>" if es_adm else ""
                rows_1 += f"<tr><td>{r['Granja']}</td><td>{r['Lote']}</td><td>{r['Edad Sem.']}</td><td>{r['Línea Genética']}</td><td>{r['Saldo de Aves']}</td><td>{r['Mort']}</td><td>{r['CASA NUTRICIONAL']}</td><td>{r['Consumo (Ton)']}</td><td>{r['% Pdn. Real']}</td><td>{r['% Pdn. Tabla']}</td><td>{r['Dif Pdn']}</td>{val_costo_td}<td>{r['Conversión (g)']}</td><td>{r['IEB (Pts)']}</td><td>{r['Estado']}</td></tr>"
            
            val_costo_tot_td = f"<td>{tot_row['$/Huevo x Alimento']}</td>" if es_adm else ""
            row_tot_html = f"<tr style='background-color:#FDF2E9; font-weight:bold; border-top:2px solid {c_prim};'><td>{tot_row['Granja']}</td><td>{tot_row['Lote']}</td><td>{tot_row['Edad Sem.']}</td><td>{tot_row['Línea Genética']}</td><td>{tot_row['Saldo de Aves']}</td><td>{tot_row['Mort']}</td><td>{tot_row['CASA NUTRICIONAL']}</td><td>{tot_row['Consumo (Ton)']}</td><td>{tot_row['% Pdn. Real']}</td><td>{tot_row['% Pdn. Tabla']}</td><td>{tot_row['Dif Pdn']}</td>{val_costo_tot_td}<td>{tot_row['Conversión (g)']}</td><td>{tot_row['IEB (Pts)']}</td><td>{tot_row['Estado']}</td></tr>"
            
            rows_2 = "".join([f"<tr><td>{r['Categoría Comercial']}</td><td>{r['Detalle Gramaje / Tipo']}</td><td style='font-weight:bold;'>{r['% Participación Mes']}</td></tr>" for r in t2_data])
            
            p_text = "".join([f"<li><b>{a['Granja']} - {a['Lote']}</b> ({a['Edad']}): <span style='color:#C0392B;'>{a['Problemas Detectados']}</span></li>" for a in alertas]) if alertas else "<li>No se registraron desviaciones en el periodo.</li>"

            d_text = "".join([f"<li>🔴 <b>{d['Granja']} - {d['Lote']}</b> ({d['Edad']:.0f} Sem): Censo de <b>{d['Aves']:,.0f} aves</b>.</li>" for d in descarte_lotes]) if descarte_lotes else "<li>No hay lotes en zona de descarte crítico (>75 Sem).</li>"

            tot_aves_gen = df_gen_pct["Aves"].sum()
            tot_pct_gen = df_gen_pct["% Participación"].sum()
            
            rows_gen = "".join([f"<tr><td>{r['Línea Genética']}</td><td>{r['Aves']:,.0f}</td><td style='font-weight:bold;'>{r['% Participación']:.1f}%</td><td>{r['% Pdn. Prom']:.1f}%</td></tr>" for _, r in df_gen_pct.iterrows()])
            row_tot_gen = f"<tr style='background-color:#FDF2E9; font-weight:bold; border-top:1.5px solid {c_prim};'><td>TOTAL GENERAL</td><td>{tot_aves_gen:,.0f}</td><td>{tot_pct_gen:.0f}%</td><td>{pdn_global_val:.1f}% (Prom)</td></tr>"

            tot_ton_fase = df_fase_pct["Toneladas"].sum()
            tot_pct_fase = df_fase_pct["% Participación"].sum()

            rows_fase = "".join([f"<tr><td>{r['Fase de Alimento']}</td><td>{r['Toneladas']:,.1f} Ton</td><td style='font-weight:bold;'>{r['% Participación']:.1f}%</td></tr>" for _, r in df_fase_pct.iterrows()])
            row_tot_fase = f"<tr style='background-color:#FDF2E9; font-weight:bold; border-top:1.5px solid {c_prim};'><td>TOTAL GENERAL</td><td>{tot_ton_fase:,.1f} Ton</td><td>{tot_pct_fase:.0f}%</td></tr>"

            html_watermark = f'<div class="watermark"><img src="data:image/png;base64,{logo_b64_str}"></div>' if logo_b64_str else ""

            html_str = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Informe Gerencial - {emp_nombre}</title>
    <style>
        @page {{ size: A4; margin: 8mm 10mm; }}
        body {{ font-family: Arial, sans-serif; padding: 5px; color: #2C3E50; background: white; position: relative; }}
        
        h2 {{ color: {c_prim}; font-size: 14.5px; border-left: 4px solid {c_prim}; padding-left: 8px; margin-top: 16px; margin-bottom: 10px; page-break-after: avoid; break-after: avoid; }}
        
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 10px; page-break-inside: auto; }}
        tr {{ page-break-inside: avoid; break-inside: avoid; page-break-after: auto; }}
        thead {{ display: table-header-group; }}
        
        .banner {{ background: linear-gradient(135deg, {c_prim}, {c_sec}); color: white; padding: 14px 18px; border-radius: 6px; margin-bottom: 12px; display: flex; align-items: center; }}
        .banner-text h1 {{ margin: 0; font-size: 22px; color: white; }}
        .banner-text p {{ margin: 3px 0 0 0; font-size: 12px; opacity: 0.95; color: white; }}
        .slogan {{ font-style: italic; opacity: 0.9; font-size: 11px; margin-top: 2px; }}

        .kpi-container {{ display: flex; justify-content: space-between; gap: 10px; margin-bottom: 12px; }}
        .kpi-box {{ flex: 1; background: #FAFAFA; border-top: 3.5px solid {c_prim}; border-radius: 5px; padding: 10px; text-align: center; border: 1px solid #E0E0E0; }}
        .kpi-title {{ font-size: 10px; font-weight: bold; color: #7F8C8D; text-transform: uppercase; }}
        .kpi-val {{ font-size: 17px; font-weight: bold; color: {c_prim}; margin-top: 3px; }}

        th {{ background: {c_prim}; color: white; padding: 6px; text-align: center; font-size: 10px; }}
        td {{ padding: 5px; border-bottom: 1px solid #EEE; text-align: center; }}
        tr:nth-child(even) {{ background-color: #FAFAFA; }}

        .ieb-box-container {{ display: flex; gap: 12px; margin-bottom: 14px; page-break-inside: avoid; }}
        .ieb-box-col {{ flex: 1; background: #EBF5FB; border-left: 4px solid #2980B9; padding: 9px 12px; border-radius: 5px; font-size: 10px; color: #1F618D; line-height: 1.4; }}

        .alert-box {{ background: #FDEDEC; border-left: 4px solid #C0392B; padding: 10px 14px; border-radius: 5px; margin: 10px 0; font-size: 10.5px; page-break-inside: avoid; }}
        .sol-box {{ background: #EAF2F8; border-left: 4px solid #D35400; padding: 10px 14px; border-radius: 5px; margin: 10px 0; font-size: 10.5px; page-break-inside: avoid; }}
        .flex-container {{ display: flex; gap: 18px; margin-bottom: 12px; page-break-inside: avoid; }}
        .flex-box {{ flex: 1; }}

        .watermark {{
            position: fixed;
            top: 45%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-25deg);
            opacity: 0.035;
            z-index: -1000;
            width: 65%;
            text-align: center;
            pointer-events: none;
        }}
        .watermark img {{ width: 100%; height: auto; }}

        .footer {{ text-align: center; font-size: 10px; color: #7F8C8D; border-top: 1px solid #DDD; padding-top: 8px; margin-top: 18px; page-break-inside: avoid; }}
    </style>
</head>
<body onload="window.print()">
    {html_watermark}

    <div class="banner">
        {logo_tag}
        <div class="banner-text">
            <h1>{emp_nombre}</h1>
            <p><b>Informe Gerencial y Diagnóstico de Ejecución</b> • Período: {txt_periodo}</p>
            <div class="slogan">"Presente en la mesa de los colombianos"</div>
        </div>
    </div>

    <div class="kpi-container">
        <div class="kpi-box"><div class="kpi-title">PRODUCCIÓN REAL</div><div class="kpi-val">{pdn_global_val:.1f}%</div></div>
        <div class="kpi-box"><div class="kpi-title">ALIMENTO CONSUMIDO</div><div class="kpi-val">{ton_tot:,.1f} Ton</div></div>
        {kpi_costo_html}
        <div class="kpi-box"><div class="kpi-title">CONVERSIÓN PONDERADA</div><div class="kpi-val">{conv_prom:.1f} g</div></div>
    </div>

    <h2>1. Consolidado de Ejecución por Granja y Lote (Ordenado de Mayor a Menor Edad)</h2>
    <table>
        <thead>
            <tr><th>Granja</th><th>Lote</th><th>Edad Sem.</th><th>Línea Genética</th><th>Saldo de Aves</th><th>Mort</th><th>CASA NUTRICIONAL</th><th>Consumo</th><th>Pdn Real %</th><th>Pdn Tabla %</th><th>Dif Pdn</th>{th_costo_col}<th>Conversión</th><th>IEB</th><th>Estado</th></tr>
        </thead>
        <tbody>{rows_1}{row_tot_html}</tbody>
    </table>
    
    <div class="ieb-box-container">
        <div class="ieb-box-col">
            <b>💡 ¿Qué es la columna IEB (Índice de Eficiencia Biológica)?</b><br>
            Es la <b>nota de calificación del lote (0 a 100 Pts)</b> que evalúa el rendimiento integral combinando <b>Postura, Conversión y Mortalidad del periodo</b>:<br>
            • 🟢 <b>85 - 100 Pts (Excelente):</b> Alta postura, excelente conversión y mínima mortalidad.<br>
            • 🟡 <b>75 - 84 Pts (Normal):</b> Rendimiento dentro del estándar esperado.<br>
            • 🔴 <b>Menos de 75 Pts (Alerta):</b> Caída en postura, sobreconsumo o bajas elevadas.
        </div>
        <div class="ieb-box-col">
            <b>📐 Fórmula y Ejemplo de Cálculo (Con Mortalidad del Periodo):</b><br>
            <code>IEB = (% Postura x 0.50) + ((200 - Conversión) x 0.35) + ((100 - % Mort Periodo) x 0.15)</code><br>
            • <b>Caso Real (Lote con 85% Postura, 140g Conversión y 0.2% Mort Mes):</b><br>
            <code>IEB = (85 x 0.50) + ((200 - 140) x 0.35) + ((100 - 0.2) x 0.15)</code><br>
            <code>IEB = 42.5 + 21.0 + 14.97 = <b>78.5 Pts</b></code>
        </div>
    </div>

    <h2>2. Casa Nutricional: Participación por Línea Genética y Fase de Alimento</h2>
    <div class="flex-container">
        <div class="flex-box">
            <b style="font-size:11.5px; color:{c_prim};">A. Participación por Línea Genética (Censo Final)</b>
            <table style="margin-top:5px;">
                <thead><tr><th>Línea Genética</th><th>Censo Final Aves</th><th>% Participación</th><th>% Pdn Prom</th></tr></thead>
                <tbody>{rows_gen}{row_tot_gen}</tbody>
            </table>
        </div>
        <div class="flex-box">
            <b style="font-size:11.5px; color:{c_prim};">B. Participación por Fase de Alimento</b>
            <table style="margin-top:5px;">
                <thead><tr><th>Fase de Alimento</th><th>Consumo (Ton)</th><th>% Participación</th></tr></thead>
                <tbody>{rows_fase}{row_tot_fase}</tbody>
            </table>
        </div>
    </div>

    <h2>3. Diagnóstico de Eficiencia Biológica y Plan de Renuevo</h2>
    <div class="alert-box">
        <b style="color:#C0392B; font-size:12px;">🔍 Desviaciones Técnicas Registradas:</b>
        <ul style="margin: 4px 0 0 0; padding-left: 18px;">{p_text}</ul>
    </div>
    <div class="sol-box">
        <b style="color:#D35400; font-size:12px;">🐔 Lotes en Zona de Renuevo / Descarte (>75 Semanas):</b>
        <ul style="margin: 4px 0 0 0; padding-left: 18px;">{d_text}</ul>
    </div>

    <h2>4. Perfil Comercial de Huevo</h2>
    <table>
        <thead>
            <tr><th>Categoría Comercial</th><th>Detalle Gramaje / Tipo</th><th>% Participación</th></tr>
        </thead>
        <tbody>{rows_2}</tbody>
    </table>

    <div class="footer">
        <b>HUPA | División Avícola</b> • <i>"Presente en la mesa de los colombianos"</i> • Documento Oficial Autogenerado • Confidencial
    </div>
</body>
</html>"""
            return html_str

        html_pdf = generar_pdf_html(
            empresa_sel, 
            df_tabla_lotes, 
            res_clasificacion, 
            alertas_lista, 
            lotes_descarte_lista,
            fila_totales, 
            color_p, 
            color_s, 
            logo_html, 
            total_toneladas,
            df_pie_gen,
            df_pie_fase,
            logo_b64,
            pdn_prom,
            es_admin
        )

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
    "<div style='text-align:center; opacity:0.6;'><b>HUPA | División Avícola</b> - <i>'Presente en la mesa de los colombianos'</i></div>",
    unsafe_allow_html=True,
)