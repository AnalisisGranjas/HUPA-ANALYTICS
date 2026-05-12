import streamlit as st

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="HUPA | Clasificación", layout="wide")

# --- 2. ESTILOS CSS BLINDADOS (Con Huevo Marrón/Rosado) ---
st.markdown("""
<style>
    /* TÍTULO PRINCIPAL HUPA */
    .main-title { 
        text-align:center; color:white; background-color: #1a237e; 
        padding: 20px; border-radius: 15px; font-weight: bold; font-size: 2.2rem; 
        font-family: sans-serif; margin-bottom: 20px;
    }

    /* CONTENEDOR DE CONSTRUCCIÓN */
    .wip-box {
        border: 2px dashed #1a237e; border-radius: 20px; 
        background-color: #f8f9fa; padding: 60px 40px; text-align: center;
        display: flex; flex-direction: column; align-items: center;
        margin-top: 20px;
    }

    /* EL HUEVO CSS A COLOR Y CON MOVIMIENTO */
    .egg-css {
        width: 120px; height: 160px;
        /* Degradado radial para dar color marrón y volumen */
        background: radial-gradient(circle at 30% 30%, #f7d7b3 10%, #e0ac69 60%, #c68b4d 100%);
        border-radius: 50% 50% 50% 50% / 65% 65% 35% 35%;
        /* Sombra interna sutil y sombra exterior para profundidad */
        box-shadow: 
            inset -10px -10px 20px rgba(0,0,0,0.1), 
            0 20px 45px rgba(26, 35, 126, 0.2);
        position: relative; margin: 0 auto 40px auto;
        /* Animación de Balanceo */
        animation: balanceo 3.2s ease-in-out infinite; transform-origin: bottom center;
    }

    /* Brillo realista sobre el huevo */
    .egg-css::before {
        content: ''; position: absolute; width: 30px; height: 50px;
        background: rgba(255, 255, 255, 0.6); border-radius: 50%;
        top: 20px; left: 20px; transform: rotate(25deg); filter: blur(4px);
    }

    /* TEXTO DE ESTADO (BLINDADO) */
    .status-text { 
        color: #1a237e !important; font-size: 2.3rem; font-weight: 800; 
        margin-bottom: 15px; font-family: sans-serif;
    }
    .sub-text { 
        color: #5c6bc0 !important; font-size: 1.3rem; line-height: 1.6; 
        font-family: sans-serif; max-width: 650px;
    }
    
    /* ANIMACIÓN DE BALANCEO */
    @keyframes balanceo {
        0%, 100% { transform: rotate(-7deg); }
        50% { transform: rotate(7deg); }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. TÍTULO ---
st.markdown('<div class="main-title">🥚 CLASIFICACIÓN DE HUEVO POR GRANJA</div>', unsafe_allow_html=True)

# --- 4. CONTENIDO (TODO EN UN SOLO BLOQUE HTML, SIN ESPACIOS EXTRAÑOS) ---
# Importante: Las etiquetas HTML deben tocar el borde izquierdo para evitar el "cuadro gris"
st.markdown("""
<div class="wip-box">
<div class="egg-css"></div>
<div class="status-text">⏳ Calibrando los datos operativos...</div>
<div class="sub-text">
Estamos ajustando los modelos de distribución para <b>Jumbo, Extra, AA, A, B, C</b>.<br>
Muy pronto podrás auditar el tamaño de huevo de tu lote.
</div>
</div>
""", unsafe_allow_html=True)

# --- 5. FOOTER (Opcional) ---
st.markdown("<br><div style='text-align: center; opacity: 0.5; margin-top: 40px;'><hr style='border-top: 1px solid #1a237e;'><b>HUPA | División Avícola</b></div>", unsafe_allow_html=True)