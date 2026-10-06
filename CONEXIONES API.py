import pandas as pd
import requests
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Validador de API MIAA - Web", page_icon="💧", layout="centered"
)

st.title("💧 Validador Definitivo MIAA")
st.write(
    "Herramienta web para validar la autenticación y descarga masiva de"
    " instalaciones desde la API de MIAA."
)

# Lectura de credenciales desde la sección [api] de los secretos
BASE_URL = "https://prelec.miaa.mx"
URL_LOGIN_CORRECTA = "/auth/login"
URL_INSTALACIONES = "https://prelec.miaa.mx/msvc-tecnica/medidores/instalaciones"

try:
  USUARIO = st.secrets["api"]["usuario"]
  PASSWORD = st.secrets["api"]["password"]
except Exception as e:
  st.error(
      "Faltan las credenciales o la sección [api] en el archivo de secretos"
      f" de Streamlit. Detalle: {e}"
  )
  st.stop()

# Botón para ejecutar la prueba de conexión
if st.button("Probar Conexión y Descarga"):
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

        # Procesar los datos JSON a DataFrame de Pandas
        data_json = res_inst.json()

        # Validar si la respuesta es una lista directa o viene dentro de un diccionario
        if isinstance(data_json, list):
          df = pd.DataFrame(data_json)
        elif isinstance(data_json, dict):
          # Si la lista de registros está en una clave común como 'data' o 'content', búscala; de lo contrario, intenta convertir el dict
          lista_datos = (
              data_json.get("data")
              or data_json.get("content")
              or data_json.get("results")
              or [data_json]
          )
          df = pd.DataFrame(lista_datos)
        else:
          df = pd.DataFrame()

        st.subheader("📋 Primeros 10 registros de instalaciones:")
        if not df.empty:
          # Muestra interactiva de los primeros 10 registros en formato de tabla
          st.dataframe(df.head(10), use_container_width=True)
          st.info(f"Total de registros totales descargados: {len(df)}")
        else:
          st.warning(
              "La respuesta no contiene una estructura tabular reconocible."
          )
          st.json(data_json)

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
