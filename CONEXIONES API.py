import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests

# URL Base y la ruta de login descubierta
BASE_URL = "https://prelec.miaa.mx"
URL_LOGIN_CORRECTA = "/auth/login"
URL_INSTALACIONES = "https://prelec.miaa.mx/msvc-tecnica/medidores/instalaciones"

USUARIO = "pedro.templos@miaa.mx"
PASSWORD = "Pedro02081984"

def ejecutar_prueba():
    btn_probar.config(state=tk.DISABLED, bg="#cccccc")
    hilo = threading.Thread(target=probar_conexion)
    hilo.daemon = True
    hilo.start()

def probar_conexion():
    try:
        txt_output.delete(1.0, tk.END)
        txt_output.insert(tk.END, "Iniciando proceso de autenticación...\n\n")
        
        # 1. Petición de Login con la ruta correcta /auth/login
        url_login = BASE_URL + URL_LOGIN_CORRECTA
        txt_output.insert(tk.END, f"-> Conectando a: {url_login}\n")
        root.update()
        
        res_login = requests.post(
            url_login,
            json={"username": USUARIO, "password": PASSWORD},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        txt_output.insert(tk.END, f"   Código HTTP (Login): {res_login.status_code}\n")
        
        if res_login.status_code == 200:
            data_login = res_login.json()
            token = data_login.get("token") or data_login.get("access_token")
            
            if token:
                txt_output.insert(tk.END, "   [¡ÉXITO!] Token obtenido correctamente.\n\n")
            else:
                txt_output.insert(tk.END, f"   [AVISO] Login 200 pero no se encontró la llave del token. Respuesta: {res_login.text[:200]}\n")
                root.after(0, lambda: messagebox.showerror("Error", "No se encontró el token en la respuesta."))
                return
        else:
            txt_output.insert(tk.END, f"   [FALLÓ] Autenticación rechazada. Respuesta: {res_login.text[:150]}\n")
            root.after(0, lambda: messagebox.showerror("Error de Autenticación", f"Código HTTP: {res_login.status_code}"))
            return

        # 2. Petición de Instalaciones con mayor límite de espera (45 segundos)
        txt_output.insert(tk.END, f"-> Consultando instalaciones (esto puede demorar unos segundos por el volumen de datos)...\n   {URL_INSTALACIONES}\n")
        root.update()
        
        res_inst = requests.get(
            URL_INSTALACIONES,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=45  # Timeout ampliado para evitar cortes por descarga pesada
        )
        
        txt_output.insert(tk.END, f"   Código de estado (Instalaciones): {res_inst.status_code}\n")
        
        if res_inst.status_code == 200:
            txt_output.insert(tk.END, "\n[ÉXITO TOTAL] ¡Conexión y descarga de datos completadas!\n\n")
            txt_output.insert(tk.END, "Muestra parcial de los registros obtenidos:\n")
            respuesta_json = str(res_inst.json())
            txt_output.insert(tk.END, respuesta_json[:1000] + ("...\n[Datos truncados por visualización]" if len(respuesta_json) > 1000 else ""))
            root.after(0, lambda: messagebox.showinfo("Conexión Exitosa", "La API respondió y entregó las instalaciones correctamente."))
        else:
            txt_output.insert(tk.END, f"\n[ERROR] El token funcionó pero falló la consulta de instalaciones.\nRespuesta: {res_inst.text[:200]}\n")
            root.after(0, lambda: messagebox.showwarning("Aviso", f"Falló instalaciones (HTTP {res_inst.status_code})"))

    except requests.exceptions.Timeout:
        txt_output.insert(tk.END, f"\n[EXCEPCIÓN] La API tardó demasiado en responder (>45 segundos). El servidor podría estar saturado.\n")
        root.after(0, lambda: messagebox.showerror("Tiempo agotado", "El servidor tardó mucho en responder las instalaciones."))
    except requests.exceptions.RequestException as e:
        txt_output.insert(tk.END, f"\n[EXCEPCIÓN DE RED] {e}\n")
        root.after(0, lambda: messagebox.showerror("Error de Red", str(e)))
    finally:
        root.after(0, lambda: btn_probar.config(state=tk.NORMAL, bg="#007acc"))

# ==========================================
# CONFIGURACIÓN DE LA INTERFAZ GRÁFICA (UI)
# ==========================================
root = tk.Tk()
root.title("Validador de API MIAA - Visual")
root.geometry("720x550")
root.config(bg="#f0f2f5")

lbl_title = tk.Label(root, text="Validador Definitivo MIAA", font=("Arial", 14, "bold"), bg="#f0f2f5", fg="#333333")
lbl_title.pack(pady=15)

btn_probar = tk.Button(root, text="Probar Conexión y Descarga", font=("Arial", 11, "bold"), bg="#007acc", fg="white", padx=10, pady=5, command=ejecutar_prueba)
btn_probar.pack(pady=5)

lbl_log = tk.Label(root, text="Registro de depuración:", font=("Arial", 10), bg="#f0f2f5", fg="#666666")
lbl_log.pack(anchor="w", padx=30, pady=(10, 0))

txt_output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=82, height=19, font=("Consolas", 9))
txt_output.pack(padx=30, pady=5)

root.mainloop()