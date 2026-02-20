import streamlit as st
from groq import Groq
from tavily import TavilyClient
import fitz  # PyMuPDF
from datetime import datetime

# ===================== CONFIGURACIÓN Y LIMPIEZA TOTAL =====================
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# CSS Avanzado para fijar el chat y borrar TODO lo de abajo
st.markdown("""
<style>
    .stApp { background-color: #020c1b !important; }
    
    /* ELIMINAR LOGOS Y MARCAS DE AGUA DEL FONDO */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stStatusWidget"] {display:none;}
    div.block-container {padding-bottom: 5rem;} /* Espacio para que el input no tape el chat */

    /* CONTENEDOR DE CHAT CON SCROLL INDEPENDIENTE */
    .chat-container {
        height: 60vh;
        overflow-y: auto;
        padding: 10px;
        display: flex;
        flex-direction: column;
    }

    .jarvis-container { display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px; }
    .jarvis-face { width: 70px; height: 70px; background: #00ffcc; border-radius: 50%; box-shadow: 0 0 25px rgba(0, 255, 204, 0.5); }
    
    .user-bubble { background-color: #112240; color: #e6f1ff; padding: 12px; border-radius: 15px 15px 0px 15px; margin: 8px 0 8px auto; max-width: 80%; border: 1px solid #64ffda30; }
    .assistant-bubble { background-color: #0a192f; color: #64ffda; padding: 12px; border-radius: 15px 15px 15px 0px; margin: 8px auto 8px 0; max-width: 80%; border: 1px solid #00b4d830; }
</style>
""", unsafe_allow_html=True)

# ===================== FUNCIONES DE APOYO =====================
def extraer_pdf(archivo):
    texto = ""
    with fitz.open(stream=archivo.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

def buscar_en_web(query):
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        res = tavily.search(query=query, search_depth="advanced", max_results=3)
        return "\n".join([r['content'] for r in res['results']])
    except: return ""

# ===================== INTERFAZ =====================
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "bienvenida" not in st.session_state:
    st.session_state.bienvenida = False

st.markdown('<div class="jarvis-container"><div class="jarvis-face"></div><h2 style="color: #64ffda; font-family: \'Courier New\'; text-align:center;">J.A.R.V.I.S.</h2></div>', unsafe_allow_html=True)

if not st.session_state.bienvenida:
    nombre = st.text_input("Identificación:", key="login_input")
    if st.button("Conectar"):
        st.session_state.nombre_usuario = nombre
        st.session_state.bienvenida = True
        st.rerun()
else:
    # Selector de PDF discreto
    with st.expander("📂 Cargar Documento (PDF)"):
        pdf_subido = st.file_uploader("Sube un archivo para analizar", type="pdf")
        if pdf_subido:
            st.session_state.contexto_pdf = extraer_pdf(pdf_subido)
            st.success("PDF procesado.")

    # Área de chat fija
    for msg in st.session_state.mensajes:
        clase = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
        st.markdown(f'<div class="{clase}">{msg["content"]}</div>', unsafe_allow_html=True)

    # Input fijo abajo
    if prompt := st.chat_input("Diga sus órdenes..."):
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        
        # Respuesta de la IA
        try:
            client = Groq(api_key=st.secrets["CLAVE_API"])
            contexto_pdf = st.session_state.get("contexto_pdf", "")
            info_web = buscar_en_web(prompt)

            instruccion = (
                f"Eres JARVIS. Usuario: {st.session_state.nombre_usuario}. "
                f"Datos PDF: {contexto_pdf}. Info Web: {info_web}. "
                "Responde de forma concisa y técnica."
            )

            res = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{"role": "system", "content": instruccion}] + st.session_state.mensajes
            )
            st.session_state.mensajes.append({"role": "assistant", "content": res.choices[0].message.content})
        except:
            st.error("Error de conexión.")
        st.rerun()
