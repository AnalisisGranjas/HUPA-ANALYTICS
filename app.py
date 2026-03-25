import streamlit as st
import base64
import os
import time
from PIL import Image

# --- 1. CONFIGURACIÓN DE PÁGINA ---
logo_path = os.path.join("DATA", "logo hupa.png")
try:
    img_pestana = Image.open(logo_path)
    st.set_page_config(page_title="HUPA | Portal", layout="wide", page_icon=img_pestana)
except:
    st.set_page_config(page_title="HUPA | Portal", layout="wide", page_icon="🐔")

if 'auth' not in st.session_state: st.session_state.auth = False
if 'loading_stage' not in st.session_state: st.session_state.loading_stage = 'none'
if 'user' not in st.session_state: st.session_state.user = None

def get_base64(bin_file):
    with open(bin_file, 'rb') as f: data = f.read()
    return base64.b64encode(data).decode()

ruta_fondo = os.path.join("DATA", "fondo.jpg")
bin_str = get_base64(ruta_fondo) if os.path.exists(ruta_fondo) else ""

st.markdown(f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url("data:image/png;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    { '[data-testid="stSidebar"], [data-testid="stSidebarNav"], header {display: none !important;}' if not st.session_state.auth else '' }

    [data-testid="stForm"] {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(15px); padding: 40px; border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    [data-testid="stForm"] h3, [data-testid="stForm"] label, [data-testid="stForm"] p {{
        color: white !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
    }}
    [data-testid="stForm"] input {{ background-color: rgba(255, 255, 255, 0.9) !important; color: #333 !important; border-radius: 10px; }}
    [data-testid="stForm"] button {{ background-color: #FFD700 !important; color: #333 !important; font-weight: bold !important; border-radius: 10px; }}

    /* ANIMACIÓN POLLITO */
    .loading-stage {{ display: flex; flex-direction: column; align-items: center; justify-content: center; height: 75vh; width: 100%; }}
    .egg-container {{ position: relative; width: 240px; height: 300px; }}
    .egg {{ position: absolute; width: 100%; height: 100%; background-color: #fff5e6; border-radius: 50% 50% 50% 50% / 65% 65% 35% 35%; box-shadow: inset -15px -15px 0 rgba(0,0,0,0.05); z-index: 5; transform-origin: bottom center; }}
    .rocking .egg {{ animation: rock 0.8s ease-in-out infinite; }}
    .chick {{ position: absolute; bottom: 40px; left: 50%; transform: translateX(-50%); width: 140px; height: 140px; background: #FFD700; border-radius: 50%; display: none; z-index: 4; box-shadow: inset -10px -10px 0 #F0C600; }}
    .eye {{ position: absolute; top: 50px; width: 12px; height: 12px; background: #333; border-radius: 50%; animation: blink 3s infinite; }}
    .eye.left {{ left: 35px; }} .eye.right {{ right: 35px; }}
    .beak {{ position: absolute; top: 65px; left: 50%; transform: translateX(-50%); border-left: 12px solid transparent; border-right: 12px solid transparent; border-top: 15px solid #FF8C00; }}
    .wing {{ position: absolute; top: 70px; width: 30px; height: 40px; background: #FFD700; border-radius: 50%; }}
    .wing.left {{ left: -15px; transform: rotate(-30deg); animation: flap-l 0.4s infinite; }}
    .wing.right {{ right: -15px; transform: rotate(30deg); animation: flap-r 0.4s infinite; }}
    .shell-top, .shell-bottom {{ position: absolute; width: 100%; height: 55%; background-color: #fff5e6; left: 0; z-index: 6; }}
    .shell-top {{ top: 0; border-radius: 50% 50% 0 0; clip-path: polygon(0% 0%, 100% 0%, 100% 80%, 85% 65%, 70% 80%, 55% 65%, 40% 80%, 25% 65%, 10% 80%, 0% 65%); }}
    .shell-bottom {{ bottom: 0; border-radius: 0 0 50% 50%; clip-path: polygon(0% 20%, 15% 35%, 30% 20%, 45% 35%, 60% 20%, 75% 35%, 90% 20%, 100% 35%, 100% 100%, 0% 100%); }}
    @keyframes rock {{ 0%, 100% {{ transform: rotate(-10deg); }} 50% {{ transform: rotate(10deg); }} }}
    @keyframes blink {{ 0%, 90%, 100% {{ height: 12px; }} 95% {{ height: 1px; }} }}
    @keyframes flap-l {{ 0%, 100% {{ transform: rotate(-30deg); }} 50% {{ transform: rotate(-60deg); }} }}
    @keyframes flap-r {{ 0%, 100% {{ transform: rotate(30deg); }} 50% {{ transform: rotate(60deg); }} }}
    .hatched .egg {{ display: none; }}
    .hatched .shell-top {{ animation: shell-up 0.8s forwards; }}
    .hatched .shell-bottom {{ animation: shell-down 0.8s forwards; }}
    .hatched .chick {{ display: block; animation: chick-emerge 0.8s 0.2s forwards, breathe 2s infinite 1s; }}
    @keyframes shell-up {{ to {{ transform: translateY(-100px) rotate(-20deg); opacity: 0; }} }}
    @keyframes shell-down {{ to {{ transform: translateY(60px) rotate(15deg); opacity: 0; }} }}
    @keyframes chick-emerge {{ 0% {{ bottom: 20px; transform: translateX(-50%) scale(0.5); }} 100% {{ bottom: 90px; transform: translateX(-50%) scale(1.1); }} }}
    @keyframes breathe {{ 0%, 100% {{ transform: translateX(-50%) scale(1.1); }} 50% {{ transform: translateX(-50%) scale(1.15); }} }}
    .loading-text {{ color: #FFD700; text-align: center; font-weight: bold; font-size: 38px; text-shadow: 2px 2px 10px rgba(0,0,0,0.8); margin-top: 40px; }}
    </style>
    """, unsafe_allow_html=True)

if not st.session_state.auth:
    if st.session_state.loading_stage == 'none':
        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if os.path.exists(logo_path): st.image(logo_path, use_container_width=True)
            with st.form("login_form"):
                st.markdown("<h3 style='text-align: center;'>Acceso al Dashboard</h3>", unsafe_allow_html=True)
                u = st.text_input("Usuario").upper()
                p = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("ENTRAR", use_container_width=True)
                if submit:
                    usuarios = {"ADMIN_HUPA": "PASCUAL2026", "VET_HUPA": "YURI2026"}
                    if u in usuarios and p == usuarios[u]:
                        st.session_state.user = u
                        st.session_state.loading_stage = 'rocking'
                        st.rerun()
                    else: st.error("Credenciales incorrectas")
    else:
        if st.session_state.loading_stage == 'rocking':
            st.markdown('<div class="loading-stage rocking"><div class="egg-container"><div class="egg"></div></div><div class="loading-text">🥚 INCUBANDO DATOS...</div></div>', unsafe_allow_html=True)
            time.sleep(2.5); st.session_state.loading_stage = 'hatched'; st.rerun()
        elif st.session_state.loading_stage == 'hatched':
            st.markdown('''<div class="loading-stage hatched"><div class="egg-container"><div class="shell-top"></div><div class="chick"><div class="eye left"></div><div class="eye right"></div><div class="beak"></div><div class="wing left"></div><div class="wing right"></div></div><div class="shell-bottom"></div></div><div class="loading-text">🐣 ¡BIENVENIDO A HUPA!</div></div>''', unsafe_allow_html=True)
            time.sleep(3); st.session_state.auth = True; st.session_state.loading_stage = 'none'; st.rerun()
    st.stop()

st.switch_page("pages/1_Estado_General.py")