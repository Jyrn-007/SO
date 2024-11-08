import tkinter as tk
from tkinter import ttk, messagebox
import platform
import psutil
import subprocess
import sys
import ctypes
import winreg
import threading

# Función para obtener la versión de Windows
def obtener_version_windows():
    system = platform.system()
    version = platform.release()
    version_detalle = platform.version()
    return f"{system} {version} ({version_detalle})"

# Función para obtener la memoria RAM total y libre
def obtener_memoria():
    memoria = psutil.virtual_memory()
    total = memoria.total / (1024 ** 3)  # Convertir a GB
    libre = memoria.available / (1024 ** 3)  # Convertir a GB
    return f"Total RAM: {total:.2f} GB | Libre: {libre:.2f} GB"

# Función para actualizar la información del sistema
def actualizar_info():
    # Obtener la versión de Windows y la memoria
    version_info = obtener_version_windows()
    memoria_info = obtener_memoria()
    
    # Actualizar las etiquetas con la nueva información
    version_label.config(text=f"Versión de Windows: {version_info}")
    memoria_label_info.config(text=f"{memoria_info}")
    
    # Actualizar cada 5 segundos
    root.after(5000, actualizar_info)

# Función para obtener los datos de rendimiento utilizando typeperf
def obtener_performance_data():
    command = 'typeperf "\\Processor(_Total)\\% Processor Time" "\\Memory\\Available MBytes" "\\LogicalDisk(_Total)\\% Free Space" -sc 1'
    
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
        return result.splitlines()[-1]  # Obtener la última línea de la salida
    except subprocess.CalledProcessError as e:
        return f"Error al ejecutar typeperf: {e}"

# Función para actualizar los datos en la interfaz cada segundo
def actualizar_datos():
    # Obtener los datos de rendimiento
    data = obtener_performance_data()

    # Procesar la salida
    try:
        cpu, memoria, disco = data.split(',')
        cpu_usage = cpu.split('=')[1].strip().replace('"', '')
        memoria_available = memoria.split('=')[1].strip().replace('"', '')
        disco_free = disco.split('=')[1].strip().replace('"', '')
        
        # Actualizar las etiquetas en la interfaz
        cpu_label.config(text=f"Uso de CPU: {cpu_usage}%")
        memoria_label_monitor.config(text=f"Memoria Disponible: {memoria_available} MB")
        disco_label.config(text=f"Espacio libre en Disco: {disco_free} %")
        
    except Exception as e:
        print(f"Error al procesar los datos: {e}")

    # Actualizar cada 1 segundo
    root.after(1000, actualizar_datos)

# Función para verificar si es administrador
def es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Re-ejecuta el script con permisos de administrador si no los tiene
def ejecutar_como_admin():
    if not es_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
        sys.exit()

# Función para obtener la lista de programas instalados
def obtener_programas():
    programas = []
    clave_registro = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clave_registro) as key:
        for i in range(0, winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                with winreg.OpenKey(key, subkey_name) as subkey:
                    programa = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    programas.append(programa)
            except FileNotFoundError:
                pass
    return programas

# Función para mostrar la lista de programas instalados
def mostrar_programas():
    programas = obtener_programas()
    for programa in programas:
        lista_programas.insert("", "end", text=programa)

# Función para listar reglas del cortafuegos
def listar_reglas_cortafuegos():
    try:
        comando = ["netsh", "advfirewall", "firewall", "show", "rule", "name=all"]
        resultado = subprocess.run(comando, capture_output=True, text=True)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, resultado.stdout)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo listar las reglas del cortafuegos: {e}")

# Función para agregar una regla al cortafuegos
def agregar_regla_cortafuegos():
    nombre_regla = entry_nombre.get().strip()
    puerto = entry_puerto.get().strip()

    if not nombre_regla or not puerto.isdigit():
        messagebox.showwarning("Entrada inválida", "Por favor, ingrese un nombre válido para la regla y un puerto numérico.")
        return

    if not es_admin():
        ejecutar_como_admin()
        return

    try:
        comando = [
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={nombre_regla}",
            "dir=in",
            "action=allow",
            "protocol=TCP",
            f"localport={puerto}"
        ]
        resultado = subprocess.run(comando, capture_output=True, text=True)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, resultado.stdout)

        if "Ok" in resultado.stdout:
            messagebox.showinfo("Éxito", f"Regla '{nombre_regla}' agregada con éxito.")
        else:
            messagebox.showwarning("Advertencia", f"No se pudo agregar la regla: {resultado.stdout}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo agregar la regla del cortafuegos: {e}")

# Función para eliminar una regla del cortafuegos
def eliminar_regla_cortafuegos():
    nombre_regla = entry_nombre.get().strip()

    if not nombre_regla:
        messagebox.showwarning("Entrada inválida", "Por favor, ingrese un nombre válido para la regla.")
        return

    if not es_admin():
        ejecutar_como_admin()
        return

    try:
        comando = ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={nombre_regla}"]
        resultado = subprocess.run(comando, capture_output=True, text=True)
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, resultado.stdout)

        if "No rules match" in resultado.stdout:
            messagebox.showwarning("Advertencia", f"No se encontró ninguna regla con el nombre '{nombre_regla}' para eliminar.")
        else:
            messagebox.showinfo("Éxito", f"Regla '{nombre_regla}' eliminada con éxito.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo eliminar la regla del cortafuegos: {e}")

# Crear la ventana principal
root = tk.Tk()
root.title("Panel de Administración del Sistema y Cortafuegos")

root.geometry("1000x700")

# Crear un notebook (pestañas)
notebook = ttk.Notebook(root)
notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Pestaña de Información del Sistema
tab_info = ttk.Frame(notebook)
notebook.add(tab_info, text="Información del Sistema")

# Pestaña de Monitoreo de Recursos
tab_monitoreo = ttk.Frame(notebook)
notebook.add(tab_monitoreo, text="Monitoreo de Recursos")

# Pestaña de Cortafuegos
tab_cortafuegos = ttk.Frame(notebook)
notebook.add(tab_cortafuegos, text="Cortafuegos")

# Pestaña de Programas Instalados
tab_programas = ttk.Frame(notebook)
notebook.add(tab_programas, text="Programas Instalados")

# --- Pestaña Información del Sistema ---
title_label = tk.Label(tab_info, text="Detalles del Sistema", font=('Arial', 16))
title_label.pack(pady=10)

# Etiquetas de información del sistema
version_label = tk.Label(tab_info, text="Versión de Windows: Cargando...", font=('Arial', 12))
version_label.pack(pady=10)

memoria_label_info = tk.Label(tab_info, text="Cargando memoria RAM...", font=('Arial', 12))
memoria_label_info.pack(pady=10)

# --- Pestaña Monitoreo de Recursos ---
cpu_label = tk.Label(tab_monitoreo, text="Uso de CPU: Cargando...", font=('Arial', 12))
cpu_label.pack(pady=10)

memoria_label_monitor = tk.Label(tab_monitoreo, text="Memoria Disponible: Cargando...", font=('Arial', 12))
memoria_label_monitor.pack(pady=10)

disco_label = tk.Label(tab_monitoreo, text="Espacio libre en Disco: Cargando...", font=('Arial', 12))
disco_label.pack(pady=10)

# Iniciar la actualización de los datos
root.after(1000, actualizar_datos)

# --- Pestaña Cortafuegos ---
entry_nombre = tk.Entry(tab_cortafuegos)
entry_nombre.pack(pady=5)
entry_nombre.insert(0, "Nombre de la regla")

entry_puerto = tk.Entry(tab_cortafuegos)
entry_puerto.pack(pady=5)
entry_puerto.insert(0, "Puerto")

btn_agregar_regla = ttk.Button(tab_cortafuegos, text="Agregar Regla", command=agregar_regla_cortafuegos)
btn_agregar_regla.pack(pady=5)

btn_eliminar_regla = ttk.Button(tab_cortafuegos, text="Eliminar Regla", command=eliminar_regla_cortafuegos)
btn_eliminar_regla.pack(pady=5)

btn_listar_reglas = ttk.Button(tab_cortafuegos, text="Listar Reglas", command=listar_reglas_cortafuegos)
btn_listar_reglas.pack(pady=5)

# Área de texto para mostrar reglas del cortafuegos
text_area = tk.Text(tab_cortafuegos, height=15, width=80)
text_area.pack(pady=10)

# --- Pestaña Programas Instalados ---
btn_programas_instalados = ttk.Button(tab_programas, text="Mostrar Programas", command=mostrar_programas)
btn_programas_instalados.pack(pady=10)

lista_programas = ttk.Treeview(tab_programas, columns=("Programas"), show="headings")
lista_programas.heading("Programas", text="Programas Instalados")
lista_programas.pack(pady=10)

# Ejecutar la aplicación
root.mainloop()
