import streamlit as st
from groq import Groq
from tavily import TavilyClient
import fitz  # PyMuPDF
from datetime import datetime

# ===================== CONFIGURACIÓN =====================
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# ===================== INTERFAZ STARK ORIGINAL =====================
st.markdown("""
<style>
    .stApp { background-color: #020c1b !important; }
    .jarvis-container { display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 30px; padding-top: 20px; }
    .jarvis-face-original { width: 80px; height: 80px; background: #00ffcc; border-radius: 50%; position: relative; box-shadow: 0 0 30px rgba(0, 255, 204, 0.6); }
    .jarvis-face-original::before, .jarvis-face-original::after { content: ''; position: absolute; width: 18px; height: 3px; background: #020c1b; top: 45%; }
    .jarvis-face-original::before { left: 16px; }
    .jarvis-face-original::after { right: 16px; }
    .user-bubble { background-color: #112240; color: #e6f1ff; padding: 15px; border-radius: 18px 18px 0px 18px; margin: 10px 0 10px auto; max-width: 85%; border: 1px solid #64ffda40; }
    .assistant-bubble { background-color: #0a192f; color: #64ffda; padding: 15px; border-radius: 18px 18px 18px 0px; margin: 10px auto 10px 0; max-width: 85%; border: 1px solid #00b4d840; }
    header, footer, .stDeployButton {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ===================== LÓGICA DE DATOS =====================
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "bienvenida" not in st.session_state:
    st.session_state.bienvenida = False

def buscar_en_web(query):
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        # Forzamos la búsqueda para que siempre traiga datos frescos
        res = tavily.search(query=query, search_depth="advanced", max_results=3)
        return "\n".join([f"Fuente: {r['url']} - Contenido: {r['content']}" for r in res['results']])
    except:
        return "No se pudo conectar a los sensores externos."

# ===================== INTERFAZ VISUAL =====================
st.markdown('<div class="jarvis-container"><div class="jarvis-face-original"></div><h2 style="color: #64ffda; margin-top: 15px; font-family: \'Courier New\'; text-align: center;">J.A.R.V.I.S.</h2></div>', unsafe_allow_html=True)

if not st.session_state.bienvenida:
    nombre = st.text_input("Identificación:", placeholder="Nombre de usuario...")
    if st.button("Establecer Conexión"):
        if nombre:
            st.session_state.nombre_usuario = nombre
            st.session_state.bienvenida = True
            st.session_state.mensajes.append({"role": "assistant", "content": f"Sistemas en línea. Bienvenido, señor {nombre}."})
            st.rerun()

if st.session_state.bienvenida:
    for msg in st.session_state.mensajes:
        clase = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
        st.markdown(f'<div class="{clase}">{msg["content"]}</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Diga sus órdenes..."):
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        
        try:
            client = Groq(api_key=st.secrets["CLAVE_API"])
            
            # JARVIS ahora SIEMPRE busca en la web para asegurar datos reales
            with st.spinner("Consultando bases de datos globales..."):
                info_web = buscar_en_web(prompt)

            instruccion = (
                f"Eres JARVIS. Hoy es {datetime.now().strftime('%d/%m/%Y')}. "
                "ACTÚA COMO UN ASISTENTE DE TIEMPO REAL. "
                f"DATOS ACTUALES DE INTERNET: {info_web}. "
                "Usa los datos de internet para responder. Si te preguntan por el dólar u otra cifra, usa los valores del link más reciente."
            )

            res = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{"role": "system", "content": instruccion}] + st.session_state.mensajes,
                temperature=0.2
            )
            st.session_state.mensajes.append({"role": "assistant", "content": res.choices[0].message.content})
        except Exception as e:
            st.error(f"Fallo en los sistemas: {e}")
        st.rerun()
