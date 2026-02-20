import streamlit as st
from groq import Groq
from tavily import TavilyClient
import fitz  # PyMuPDF
from datetime import datetime

# ===================== CONFIGURACIÓN Y LIMPIEZA VISUAL =====================
st.set_page_config(page_title="JARVIS", page_icon="🤖", layout="centered")

# Este bloque de CSS es el que borra las leyendas de "Streamlit" y mejora el diseño
st.markdown("""
<style>
    .stApp { background-color: #020c1b !important; }
    /* Ocultar menús y marcas de agua de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .jarvis-container { display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 20px; }
    .jarvis-face { width: 80px; height: 80px; background: #00ffcc; border-radius: 50%; box-shadow: 0 0 30px rgba(0, 255, 204, 0.6); position: relative; }
    .user-bubble { background-color: #112240; color: #e6f1ff; padding: 15px; border-radius: 18px 18px 0px 18px; margin: 10px 0 10px auto; max-width: 85%; border: 1px solid #64ffda40; }
    .assistant-bubble { background-color: #0a192f; color: #64ffda; padding: 15px; border-radius: 18px 18px 18px 0px; margin: 10px auto 10px 0; max-width: 85%; border: 1px solid #00b4d840; }
    
    /* Estilo para el cargador de archivos */
    .stFileUploader { background-color: #0a192f; border: 1px dashed #64ffda; border-radius: 10px; padding: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

# ===================== LÓGICA DE SENSORES =====================
def buscar_en_web(query):
    try:
        tavily = TavilyClient(api_key=st.secrets["TAVILY_API_KEY"])
        res = tavily.search(query=query, search_depth="advanced", max_results=3)
        return "\n".join([f"Dato: {r['content']}" for r in res['results']])
    except:
        return "No hay conexión a internet."

def extraer_pdf(archivo):
    texto = ""
    with fitz.open(stream=archivo.read(), filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto

# ===================== INTERFAZ PRINCIPAL =====================
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "bienvenida" not in st.session_state:
    st.session_state.bienvenida = False

st.markdown('<div class="jarvis-container"><div class="jarvis-face"></div><h2 style="color: #64ffda; font-family: \'Courier New\';">J.A.R.V.I.S.</h2></div>', unsafe_allow_html=True)

# --- APARTADO DE PDF (Solo visible si ya inició sesión) ---
if st.session_state.bienvenida:
    with st.expander("📂 Analizar Documentos PDF"):
        pdf_subido = st.file_uploader("Sube un reporte para analizar", type="pdf")
        if pdf_subido:
            with st.spinner("Analizando documento..."):
                contenido_pdf = extraer_pdf(pdf_subido)
                st.session_state.contexto_pdf = contenido_pdf
                st.success("Documento cargado en la memoria de JARVIS.")

# --- CHAT ---
if not st.session_state.bienvenida:
    nombre = st.text_input("Identificación:", placeholder="Nombre...")
    if st.button("Establecer Conexión"):
        st.session_state.nombre_usuario = nombre
        st.session_state.bienvenida = True
        st.rerun()
else:
    for msg in st.session_state.mensajes:
        clase = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
        st.markdown(f'<div class="{clase}">{msg["content"]}</div>', unsafe_allow_html=True)

    if prompt := st.chat_input("Diga sus órdenes..."):
        st.session_state.mensajes.append({"role": "user", "content": prompt})
        
        try:
            client = Groq(api_key=st.secrets["CLAVE_API"])
            info_web = buscar_en_web(prompt)
            contexto_extra = st.session_state.get("contexto_pdf", "No hay archivos cargados.")

            instruccion = (
                f"Eres JARVIS. Usuario: {st.session_state.nombre_usuario}. "
                f"INFO WEB ACTUAL: {info_web}. "
                f"CONTENIDO DEL PDF: {contexto_extra}. "
                "Responde de forma elegante y usa el contenido del PDF si el usuario pregunta sobre él."
            )

            res = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[{"role": "system", "content": instruccion}] + st.session_state.mensajes,
                temperature=0.3
            )
            st.session_state.mensajes.append({"role": "assistant", "content": res.choices[0].message.content})
        except Exception as e:
            st.error(f"Error: {e}")
        st.rerun()
