import streamlit as st
import time
from PIL import Image
import os

# 1. CONFIGURACIÓN (Rutas relativas a tu carpeta DATA)
logo_path = os.path.join("DATA", "logo hupa.png")

try:
    img_pestana = Image.open(logo_path)
except:
    img_pestana = "🐣"

st.set_page_config(
    page_title="HUPA | Dashboard Avícola", 
    layout="wide", 
    page_icon=img_pestana,
    initial_sidebar_state="collapsed"
)

# 2. ESTADOS DE SESIÓN
if 'auth' not in st.session_state:
    st.session_state.auth = False
if 'loading_stage' not in st.session_state:
    st.session_state.loading_stage = 'none'

# --- CSS Y ANIMACIÓN DEL POLLITO ---
# (Copia aquí todo el bloque <style> que tienes en tu código original)
st.markdown("""
    <style>
    /* ... (Tu CSS del pollito y el huevo) ... */
    </style>
    """, unsafe_allow_html=True)

# 3. LÓGICA DE LOGIN
if not st.session_state.auth:
    if st.session_state.loading_stage == 'none':
        _, col, _ = st.columns([1, 1.2, 1])
        with col:
            if os.path.exists(logo_path):
                st.image(logo_path, use_container_width=True)
            
            with st.form("login_form"):
                u = st.text_input("Usuario").upper()
                p = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("ENTRAR AL DASHBOARD")
                if submit:
                    if u == "ADMIN_HUPA" and p == "PASCUAL2026":
                        st.session_state.loading_stage = 'rocking'
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
    else:
        # PANTALLA DE CARGA (INCUBACIÓN)
        if st.session_state.loading_stage == 'rocking':
            st.markdown('<div class="loading-stage rocking"><div class="egg-container"><div class="egg"></div></div><div class="loading-text">🥚 INCUBANDO DATOS...</div></div>', unsafe_allow_html=True)
            time.sleep(2.5)
            st.session_state.loading_stage = 'hatched'
            st.rerun()
        elif st.session_state.loading_stage == 'hatched':
            st.markdown('''<div class="loading-stage hatched"><div class="egg-container"><div class="shell-top"></div><div class="chick">...</div><div class="shell-bottom"></div></div><div class="loading-text">🐣 ¡BIENVENIDO A HUPA!</div></div>''', unsafe_allow_html=True)
            time.sleep(3)
            st.session_state.auth = True
            st.session_state.loading_stage = 'none'
            st.rerun()
    st.stop()

# 4. REDIRECCIÓN TRAS LOGIN EXITOSO
st.switch_page("pages/1_Estado_General.py")