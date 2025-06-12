import json
import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import os
import time
import ctypes
import webbrowser
import pyperclip
import sys

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
def cargar_fuentes_desde_json():
    """Carga las fuentes desde el archivo Configs/Font.json."""
    font_file = os.path.join(base_path, 'Configs', 'Font_bot_sell.json')
    try:
        with open(font_file, 'r', encoding='utf-8') as f:
            font_data = json.load(f)
            return font_data.get("fonts", [])
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {font_file}. Usando fuentes predeterminadas.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error al leer el archivo de fuentes: {e}")
        return []
class ScriptRunner:
    def get_default_font(self):
        """Obtiene la fuente predeterminada desde el archivo JSON, si está disponible."""
        fonts = cargar_fuentes_desde_json()
        if fonts:
            font_name = fonts[0].get("name", "TkDefaultFont")  # Usa la primera fuente del JSON
            font_size = fonts[0].get("size", 9)
            return (font_name, font_size)
    def __init__(self, master, script_name, main_paned_window):
        self.master = master
        self.script_name = script_name
        self.main_paned_window = main_paned_window
        self.process = None
        self.running = False
        self.is_console_visible = True

        # PanedWindow vertical para contener la consola
        self.vertical_paned_window = tk.PanedWindow(master, orient=tk.VERTICAL)
        self.main_paned_window.add(self.vertical_paned_window, stretch="always")

        # Frame para el botón Show/Hide Console (que ahora reemplaza al tag/label)
        self.toggle_frame = tk.Frame(self.vertical_paned_window)
        self.vertical_paned_window.add(self.toggle_frame)

        # Botón para alternar la visibilidad de la consola
        self.toggle_button = tk.Button(self.toggle_frame, text=f"{script_name}", command=self.toggle_console)
        self.toggle_button.pack(padx=5, pady=5, fill=tk.X)

        # Frame para los controles de cada script
        self.frame = tk.Frame(self.vertical_paned_window, bg='lightgrey')
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Área de texto para la salida del script
        self.text_area = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, height=8, font=self.get_default_font())
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.tag_configure("Link", foreground="Blue", underline=True)


        # Botones para el control de los scripts
        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(fill=tk.X, padx=5, pady=5)

        self.start_stop_button = tk.Button(self.button_frame, text="Start", command=self.start_stop_script)
        self.start_stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.restart_button = tk.Button(self.button_frame, text="Restart", command=self.restart_script, state=tk.DISABLED)
        self.restart_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Añadir el frame de controles al PanedWindow vertical
        self.vertical_paned_window.add(self.frame)

        self.text_area.bind("<Button-1>", self._click_link)
    def start_stop_script(self):
        if self.running:
            self.stop_script()
        else:
            self.start_script()

    def start_script(self):
        if not self.running:
            self.running = True
            self.start_stop_button.config(text="Stop")
            self.restart_button.config(state=tk.NORMAL)

            # Ruta completa del script
            script_path = os.path.join(base_path, self.script_name)

            # Iniciar el script
            self.process = subprocess.Popen(
                ['python', script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            threading.Thread(target=self._monitor_process).start()

    def _monitor_process(self):
        for line in iter(self.process.stdout.readline, ''):
            line = line.strip()
            if "CLEAR_CONSOLE" in line:
                # Llamada al hilo principal para borrar el área de texto
                self.text_area.after(0, self.text_area.delete, 1.0, tk.END)
            elif "Link:" in line:
                url, display_text = line.split(" ", 1)
                # Llamada al hilo principal para insertar el enlace
                self.text_area.after(0, self._insert_link, display_text.strip(), url.strip())
            elif "Item:" in line:
                _, copy_text = line.split(" ", 1)
                # Llamada al hilo principal para insertar texto copiable
                self.text_area.after(0, self._insert_copy_text, copy_text.strip())
            else:
                # Llamada al hilo principal para insertar texto normal
                self.text_area.after(0, self._insert_text, line)
        self.process.stdout.close()

    def _insert_text(self, text):
        """Inserta texto en el área de texto y hace scroll al final."""
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.yview(tk.END)

    def _insert_link(self, text, url):
        """Inserta texto que actúa como un enlace."""
        start = self.text_area.index(tk.END)
        self.text_area.insert(tk.END, text + "\n")
        end = self.text_area.index(tk.END)
        self.text_area.tag_add("link", start, end)
        self.text_area.tag_bind("link", "<Button-1>", lambda e: webbrowser.open(url))

    def _insert_copy_text(self, text):
        """Inserta texto que se copiará al portapapeles al hacer clic."""
        start = self.text_area.index(tk.END)
        self.text_area.insert(tk.END, text + "\n")
        end = self.text_area.index(tk.END)
        self.text_area.tag_add("Objeto", start, end)
        self.text_area.tag_bind("Objeto", "<Button-1>", lambda e: pyperclip.copy(text))

    def _click_link(self, event):
        """Maneja el evento de clic en los enlaces y texto copiable."""
        # Llamada al hilo principal para obtener el texto seleccionado
        clicked_text = self.text_area.get("insert linestart", "insert lineend").strip()

        if clicked_text.startswith("http"):
            # Llamada al hilo principal para abrir el enlace en el navegador
            self.text_area.after(0, webbrowser.open, clicked_text)
        elif any(clicked_text.startswith(keyword) for keyword in
                 ["Rentabilidad:", "Comprar", "Vender", "Esperando", "Buy", "Sell", "Profitability:", "Waiting", "----------------------------------------", "==="]):
            # Llamada al hilo principal para manejar los textos no copiables
            self.text_area.after(0, print, "No copiar")
        else:
            # Llamada al hilo principal para copiar el texto al portapapeles
            self.text_area.after(0, pyperclip.copy, clicked_text)

    def toggle_console(self):
        """Oculta o muestra toda la consola, incluidos los botones."""
        if self.is_console_visible:
            self.main_paned_window.forget(self.vertical_paned_window)  # Oculta la consola completa
            self.toggle_button.config(text=f"{self.script_name}")
        else:
            self.main_paned_window.add(self.vertical_paned_window, stretch="always")  # Muestra la consola completa
            self.toggle_button.config(text=f"{self.script_name}")
            self.main_paned_window.paneconfigure(self.vertical_paned_window, minsize=50)
        self.is_console_visible = not self.is_console_visible
        self.main_paned_window.update_idletasks()  # Redibuja el PanedWindow

    def stop_script(self):
        if self.running:
            self.running = False
            self.start_stop_button.config(text="Start")
            self.restart_button.config(state=tk.DISABLED)

            if self.process:
                self.process.terminate()
                self.process.wait()

    def restart_script(self):
        self.stop_script()
        time.sleep(1)  # Esperar para asegurar que el proceso se detenga
        self.start_script()


class BotApp:
    def __init__(self, root):
        icon_path = os.path.join(base_path, 'sell.ico')
        self.root = root
        self.root.title("Profiteable Flips vCSGO")
        self.root.iconbitmap(icon_path)
        # Crear un PanedWindow principal para el ajuste horizontal
        self.main_paned_window = tk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned_window.pack(fill=tk.BOTH, expand=True)

        # Crear una lista para almacenar referencias a los ScriptRunners
        self.script_runners = []

        # Crear un PanedWindow para cada consola y añadirlo al principal
        self.scripts = [
            "SteamListingPrices_proxy.py",
            "",

        ]

        for script in self.scripts:
            # Crear un ScriptRunner dentro de cada PanedWindow vertical
            script_runner = ScriptRunner(self.main_paned_window, script, self.main_paned_window)
            self.script_runners.append(script_runner)

        # Configurar la expansión de los frames en el PanedWindow principal
        for runner in self.script_runners:
            self.main_paned_window.paneconfigure(runner.vertical_paned_window, minsize=50)  # Mínimo tamaño para cada panel horizontal

        # Atajo de teclado para mostrar todas las consolas ocultas
        self.root.bind('<Control-s>', self.show_all_consoles)

    def show_all_consoles(self, event=None):
        """Muestra todas las consolas que estaban ocultas."""
        for runner in self.script_runners:
            if not runner.is_console_visible:
                runner.toggle_console()


if __name__ == "__main__":
    # Ocultar la consola de Python al lanzarse
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    root = tk.Tk()
    app = BotApp(root)
    root.state('zoomed')  # Pantalla completa por defecto
    root.mainloop()
