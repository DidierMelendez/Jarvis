import streamlit as st
from groq import Groq
from tavily import TavilyClient
import fitz  # PyMuPDF
from datetime import datetime

# ===================== CONFIGURACIÓN =====================
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# ===================== INTERFAZ STARK ORIGINAL (CORREGIDA) =====================
st.markdown("""
<style>
    /* Fondo Oscuro Total */
    .stApp { background-color: #020c1b !important; }
    
    /* LA CARA DE JARVIS ORIGINAL (Círculo con ojos de línea) */
    .jarvis-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-bottom: 30px;
        padding-top: 20px;
    }
    .jarvis-face-original {
        width: 80px;
        height: 80px;
        background: #00ffcc;
        border-radius: 50%;
        position: relative;
        box-shadow: 0 0 30px rgba(0, 255, 204, 0.6);
    }
    /* Ojos de línea corregidos */
    .jarvis-face-original::before, .jarvis-face-original::after {
        content: '';
        position: absolute;
        width: 18px;
        height: 3px;
        background: #020c1b;
        top: 45%;
    }
    .jarvis-face-original::before { left: 16px; }
    .jarvis-face-original::after { right: 16px; }

    /* Burbujas de Chat */
    .user-bubble {
        background-color: #112240;
        color: #e6f1ff;
        padding: 15px;
        border-radius: 18px 18px 0px 18px;
        margin: 10px 0 10px auto;
        max-width: 85%;
        border: 1px solid #64ffda40;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .assistant-bubble {
        background-color: #0a192f;
        color: #64ffda;
        padding: 15px;
        border-radius: 18px 18px 18px 0px;
        margin: 10px auto 10px 0;
        max-width: 85%;
        border: 1px solid #00b4d840;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Ocultar elementos de Streamlit que molestan */
    header, footer, .stDeployButton {visibility: hidden;}
    
    /* Estilo para el Expander de PDF */
    .stExpander {
        border: 1px solid #64ffda20 !important;
        background-color: #0a192f !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ===================== LÓGICA DE DATOS =====================
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "bienvenida" not in st.session_state:
    st.session_state.bienvenida = False
if "contexto_pdf" not in st.session_state:
    st.session_state.contexto_pdf = ""

def extraer_pdf(archivo):
    try:
        doc = fitz.open(stream=archivo.read(), filetype="pdf")
        return "".join([p.get_text() for p in doc])[:15000]
    except:
        return "Error leyendo el archivo."

# ===================== INTERFAZ VISUAL =====================

# Dibujar la cara original
st.markdown('''
    <div class="jarvis-container">
        <div class="jarvis-face-original"></div>
        <h2 style="color: #64ffda; margin-top: 15px; font-family: 'Courier New'; text-align: center;">J.A.R.V.I.S.</h2>
    </div>
''', unsafe_allow_html=True)

if not st.session_state.bienvenida:
    nombre = st.text_input("Identificación:", placeholder="Nombre de usuario...")
    if st.button("Establecer Conexión"):
        if nombre:
            st.session_state.nombre_usuario = nombre
            st.session_state.bienvenida = True
            st.session_state.mensajes.append({"role": "assistant", "content": f"Sistemas en línea. Bienvenido, señor {nombre}."})
            st.rerun()

if st.session_state.bienvenida:
    # Historial de Chat
    for msg in st.session_state.mensajes:
        clase = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
        st.markdown(f'<div class="{clase}">{msg["content"]}</div>', unsafe_allow_html=True)

    # Dock de Herramientas (PDF + Reset) justo encima del input
    with st.expander("📎 Adjuntar PDF / Gestionar"):
        col1, col2 = st.columns([4, 1])
        with col1:
            archivo = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
            if archivo and ("leido" not in st.session_state or st.session_state.leido != archivo.name):
                st.session_state.contexto_pdf = extraer_pdf(archivo)
                st.session_state.leido = archivo.name
                st.session_state.mensajes.append({"role": "user", "content": f"Protocolo cargado: {archivo.name}"})
                st.rerun()
        with col2:
            if st.button("🗑️"):
                st.session_state.mensajes = []
                st.session_state.contexto_pdf = ""
                st.rerun()

    # Input de Comandos
    if prompt := st.chat_input("Diga sus órdenes..."):
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        
        try:
            client = Groq(api_key=st.secrets["CLAVE_API"])
            tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
            
            # Búsqueda automática
            info_web = ""
            if any(x in prompt.lower() for x in ["hoy", "noticias", "precio", "link", "dolar"]):
                res = tavily.search(query=prompt, max_results=2)
                info_web = "\n".join([f"Fuente: {r['url']} - {r['content']}" for r in res['results']])

            instruccion = (
                f"Eres JARVIS. Hoy es {datetime.now().strftime('%d/%m/%Y')}. "
                "Responde como la IA de Tony Stark: elegante y eficiente. "
                f"Web: {info_web}. "
                f"PDF: {st.session_state.contexto_pdf}."
            )

            res = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{"role": "system", "content": instruccion}] + st.session_state.mensajes,
                temperature=0.4
            )
            st.session_state.mensajes.append({"role": "assistant", "content": res.choices[0].message.content})
        except Exception as e:
            st.error(f"Fallo: {e}")
        st.rerun()
