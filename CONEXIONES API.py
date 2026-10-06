import requests
import streamlit as st

# Configuración de la página (Tema y diseño)
st.set_page_config(
    page_title="Validador de API MIAA - Web", page_icon="💧", layout="centered"
)

# Estilo visual personalizado (HUD / Dark o limpio adaptado)
st.markdown(
    """
    <style>
    .main {
        background-color: #f0f2f5;
    }
    .stButton>button {
        width: 100%;
        background-color: #007acc;
        color: white;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.5rem;
    }
    .stButton>button:hover {
        background-color: #005999;
        color: white;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("💧 Validador Definitivo MIAA")
st.write(
    "Herramienta web para validar la autenticación y descarga masiva de instalaciones desde la API de MIAA."
)

# Carga segura de credenciales y rutas desde st.secrets
try:
    BASE_URL = st.secrets["api"]["base_url"]
    URL_LOGIN_CORRECTA = st.secrets["api"]["url_login"]
    URL_INSTALACIONES = st.secrets["api"]["url_instalaciones"]
    USUARIO = st.secrets["api"]["usuario"]
    PASSWORD = st.secrets["api"]["password"]
except Exception as e:
    st.error(
        "Faltan las credenciales o la sección [api] en el archivo de secretos (`secrets.toml`)."
    )
    st.stop()

# Botón para ejecutar la prueba de conexión
if st.button("Probar Conexión y Descarga"):
  # Contenedor para los logs en tiempo real dentro de la interfaz web
  log_container = st.empty()
  logs = []

  def registrar(mensaje):
    logs.append(mensaje)
    log_container.code("\n".join(logs), language="text")

  with st.spinner(
      "Conectando con el servidor y descargando datos (esto puede tardar"
      " unos segundos)..."
  ):
    try:
      registrar("Iniciando proceso de autenticación...")

      # 1. Petición de Login
      url_login = BASE_URL + URL_LOGIN_CORRECTA
      registrar(f"-> Conectando a: {url_login}")

      res_login = requests.post(
          url_login,
          json={"username": USUARIO, "password": PASSWORD},
          headers={"Content-Type": "application/json"},
          timeout=10,
      )

      registrar(f"   Código HTTP (Login): {res_login.status_code}")

      if res_login.status_code == 200:
        data_login = res_login.json()
        token = data_login.get("token") or data_login.get("access_token")

        if token:
          registrar("   [¡ÉXITO!] Token obtenido correctamente.\n")
        else:
          registrar(
              "   [AVISO] Login 200 pero no se encontró la llave del token."
              f" Respuesta: {res_login.text[:200]}"
          )
          st.error("No se encontró el token en la respuesta.")
          st.stop()
      else:
        registrar(
            "   [FALLÓ] Autenticación rechazada. Respuesta:"
            f" {res_login.text[:150]}"
        )
        st.error(f"Error de Autenticación - Código HTTP: {res_login.status_code}")
        st.stop()

      # 2. Petición de Instalaciones
      registrar(
          "-> Consultando instalaciones (puede demorar por el volumen de"
          f" datos)...\n   {URL_INSTALACIONES}"
      )

      res_inst = requests.get(
          URL_INSTALACIONES,
          headers={
              "Content-Type": "application/json",
              "Authorization": f"Bearer {token}",
          },
          timeout=45,
      )

      registrar(
          f"   Código de estado (Instalaciones): {res_inst.status_code}"
      )

      if res_inst.status_code == 200:
        registrar(
            "\n[ÉXITO TOTAL] ¡Conexión y descarga de datos completadas!\n"
        )
        st.success(
            "La API respondió y entregó las instalaciones correctamente."
        )

        respuesta_json = str(res_inst.json())
        muestra = respuesta_json[:1000] + (
            "...\n[Datos truncados por visualización]"
            if len(respuesta_json) > 1000
            else ""
        )

        st.subheader("Muestra parcial de los registros obtenidos:")
        st.code(muestra, language="json")
      else:
        registrar(
            "\n[ERROR] El token funcionó pero falló la consulta de"
            f" instalaciones.\nRespuesta: {res_inst.text[:200]}"
        )
        st.warning(f"Falló instalaciones (HTTP {res_inst.status_code})")

    except requests.exceptions.Timeout:
      registrar(
          "\n[EXCEPCIÓN] La API tardó demasiado en responder (>45 segundos)."
          " Servidor saturado.\n"
      )
      st.error("El servidor tardó mucho en responder las instalaciones.")
    except requests.exceptions.RequestException as e:
      registrar(f"\n[EXCEPCIÓN DE RED] {e}\n")
      st.error(f"Error de Red: {e}")
