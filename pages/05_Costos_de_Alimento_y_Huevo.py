import streamlit as st

st.set_page_config(layout="wide", page_title="HUPA | Costos")

# --- 1. ESTILOS (CSS) ---
st.markdown("""
<style>
    @keyframes walking { 0%, 100% { transform: translateX(-60px); } 50% { transform: translateX(60px); } }
    @keyframes lay_egg { 0% { opacity: 0; transform: scale(0.5); } 20% { opacity: 1; transform: scale(1); } 80% { opacity: 1; } 100% { opacity: 0; } }
    .stage { background: #fcfcfc; padding: 60px; border-radius: 30px; border: 2px dashed #b0bec5; text-align: center; position: relative; overflow: hidden; }
    .walker { font-size: 70px; animation: walking 6s ease-in-out infinite; position: relative; z-index: 2; margin-bottom: 20px; }
    .eggs { display: flex; justify-content: center; gap: 15px; font-size: 30px; position: absolute; width: 100%; left: 0; z-index: 1; margin-top: -30px; }
    .egg { animation: lay_egg 3s linear infinite; opacity: 0; }
</style>
""", unsafe_allow_html=True)

# --- 2. HTML (TODO EN UNA LÍNEA PARA EVITAR ERROR DE INDENTACIÓN) ---
html_minificado = "<div class='stage'><div class='walker'>🏗️</div><div class='eggs'><div class='egg' style='animation-delay:0s'>🥚</div><div class='egg' style='animation-delay:1s'>🥚</div><div class='egg' style='animation-delay:2s'>🥚</div></div><h1 style='color:#1a237e;font-family:sans-serif;font-size:3rem;font-weight:800;margin-top:20px;'>Área de Costos Avícolas</h1><p style='color:#546e7a;font-size:1.5rem;max-width:700px;margin:20px auto;line-height:1.4;'>Nuestra <b>Unidad de Maquinaria Pesada</b> está instalando los algoritmos de rentabilidad, dejando todo listo huevo por huevo.</p><div style='background-color:#ffc107;color:black;padding:12px 30px;border-radius:50px;font-weight:bold;display:inline-block;'>🚧 INSTALANDO CAPAS DE RENTABILIDAD 🚧</div></div>"

st.markdown(html_minificado, unsafe_allow_html=True)

st.info("💡 Este módulo integrará próximamente el costo por gramo de alimento y el margen operativo por lote.")