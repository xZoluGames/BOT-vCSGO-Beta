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
from tkinter import messagebox


class SearchWindow:
    def __init__(self, master):
        self.search_window = tk.Toplevel(master)
        self.search_window.title("Search Filters")
        self.search_window.geometry("400x500")
        self.search_window.resizable(False, False)

        # Configurar el archivo JSON de búsqueda
        self.SEARCH_JSON = os.path.join(base_path, 'Configs', 'Search.json')

        # Asegurar que el directorio Configs existe
        os.makedirs(os.path.join(base_path, 'Configs'), exist_ok=True)

        # Crear el frame principal con scroll
        self.main_frame = tk.Frame(self.search_window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas y scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Empaquetar canvas y scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Criterios de búsqueda
        self.search_criteria = {
            'Text Criteria': {
                'name': 'Name',
                'platform': 'Platform'
            },
            'Range Criteria': {
                'buy_price': ('buy_price_upto', 'buy_price_downto', 'Buy Price Range'),
                'steam_price': ('steam_price_upto', 'steam_price_downto', 'Steam Price Range'),
                'net_steam_price': ('net_steam_price_upto', 'net_steam_price_downto', 'Net Steam Price Range'),
                'rentabilidad': ('rentabilidad_upto', 'rentabilidad_downto', 'Profitability Range')
            },
            'Numeric Criteria': {
                'buy_price': 'Buy Price',
                'steam_price': 'Steam Price',
                'net_steam_price': 'Net Steam Price',
                'rentabilidad': 'Profitability'
            }
        }

        # Variables para almacenar los valores
        self.entry_vars = {}

        # Crear widgets para criterios de texto
        tk.Label(self.scrollable_frame, text="Search by name", font=('Arial', 10, 'bold')).pack(pady=5)
        for key, label in self.search_criteria['Text Criteria'].items():
            frame = tk.Frame(self.scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=f"{label}:").pack(side=tk.LEFT)
            var = tk.StringVar()
            self.entry_vars[key] = var
            tk.Entry(frame, textvariable=var).pack(side=tk.LEFT, padx=5)

        # Crear widgets para criterios de rango
        tk.Label(self.scrollable_frame, text="\nSearch by ranges", font=('Arial', 10, 'bold')).pack(pady=5)
        for key, (up_key, down_key, label) in self.search_criteria['Range Criteria'].items():
            frame = tk.Frame(self.scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=f"{label}:").pack(side=tk.LEFT)

            # Up to (primera casilla)
            var_up = tk.StringVar()
            self.entry_vars[up_key] = var_up
            entry_up = tk.Entry(frame, textvariable=var_up, width=8)
            entry_up.pack(side=tk.LEFT, padx=5)
            self.validate_numeric_entry(entry_up)

            tk.Label(frame, text="to").pack(side=tk.LEFT)

            # Down to (segunda casilla)
            var_down = tk.StringVar()
            self.entry_vars[down_key] = var_down
            entry_down = tk.Entry(frame, textvariable=var_down, width=8)
            entry_down.pack(side=tk.LEFT, padx=5)
            self.validate_numeric_entry(entry_down)

        # Crear widgets para criterios numéricos
        tk.Label(self.scrollable_frame, text="\nSearch by specific numbers", font=('Arial', 10, 'bold')).pack(pady=5)
        for key, label in self.search_criteria['Numeric Criteria'].items():
            frame = tk.Frame(self.scrollable_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=f"{label}:").pack(side=tk.LEFT)
            var = tk.StringVar()
            self.entry_vars[key] = var
            entry = tk.Entry(frame, textvariable=var)
            entry.pack(side=tk.LEFT, padx=5)
            self.validate_numeric_entry(entry)

        # Botones
        button_frame = tk.Frame(self.search_window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Apply Filters", command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Clear Filters", command=self.clear_filters).pack(side=tk.LEFT, padx=5)

        # Cargar filtros existentes
        self.load_existing_filters()

        # Hacer que la ventana sea modal
        self.search_window.transient(master)
        self.search_window.grab_set()

    def validate_numeric_entry(self, entry):
        vcmd = (self.search_window.register(self.validate_number), '%P')
        entry.configure(validate='key', validatecommand=vcmd)

    def validate_number(self, value):
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def check_numeric_and_range_conflict(self):
        """Verifica si hay datos tanto en criterios numéricos como en rangos."""
        has_numeric = False
        has_range = False

        # Verificar criterios numéricos
        for key in self.search_criteria['Numeric Criteria']:
            if self.entry_vars[key].get().strip():
                has_numeric = True
                break

        # Verificar criterios de rango
        for _, (up_key, down_key, _) in self.search_criteria['Range Criteria'].items():
            if self.entry_vars[up_key].get().strip() or self.entry_vars[down_key].get().strip():
                has_range = True
                break

        if has_numeric and has_range:
            messagebox.showerror(
                "Input Error",
                "You cannot use both Numeric Search Criteria and Range Search Criteria at the same time."
            )
            return False
        return True

    def validate_ranges(self):
        """Valida que los rangos tengan valores coherentes."""
        for key, (up_key, down_key, label) in self.search_criteria['Range Criteria'].items():
            up_value = self.entry_vars[up_key].get().strip()
            down_value = self.entry_vars[down_key].get().strip()

            if up_value and down_value:
                try:
                    up_num = float(up_value)
                    down_num = float(down_value)
                    if up_num > down_num:
                        messagebox.showerror(
                            "Range Error",
                            f"{label}: The maximum value ({up_num}) cannot be greater than the minimum value ({down_num})"
                        )
                        return False
                except ValueError:
                    messagebox.showerror(
                        "Invalid Number",
                        f"{label}: Please enter valid numbers for the range"
                    )
                    return False
        return True

    def load_existing_filters(self):
        """Carga los filtros existentes desde el archivo JSON."""
        try:
            if not os.path.exists(self.SEARCH_JSON):
                with open(self.SEARCH_JSON, 'w', encoding='utf-8') as file:
                    json.dump([], file)
                return

            with open(self.SEARCH_JSON, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data and len(data) > 0:
                    for key, var in self.entry_vars.items():
                        if key in data[0]:
                            var.set(str(data[0][key]))
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error loading filters: {str(e)}"
            )
            # Reset the file
            with open(self.SEARCH_JSON, 'w', encoding='utf-8') as file:
                json.dump([], file)

    def apply_filters(self):
        """Aplica y guarda los filtros después de validarlos."""
        # Verificar conflicto entre criterios numéricos y de rango
        if not self.check_numeric_and_range_conflict():
            return

        # Validar rangos
        if not self.validate_ranges():
            return

        # Crear diccionario con los valores no vacíos
        filter_data = {}
        has_any_filter = False

        for key, var in self.entry_vars.items():
            value = var.get().strip()
            if value:
                has_any_filter = True
                # Convertir a float si es un campo numérico
                if (key in self.search_criteria['Numeric Criteria'] or
                        any(key in (up_key, down_key)
                            for _, (up_key, down_key, _) in self.search_criteria['Range Criteria'].items())):
                    try:
                        filter_data[key] = float(value)
                    except ValueError:
                        messagebox.showerror(
                            "Invalid Number",
                            f"Please enter a valid number for {key}"
                        )
                        return
                else:
                    filter_data[key] = value

        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(self.SEARCH_JSON), exist_ok=True)

            # Guardar en el archivo JSON
            with open(self.SEARCH_JSON, 'w', encoding='utf-8') as file:
                json.dump([filter_data] if has_any_filter else [], file, indent=4)

            if has_any_filter:
                messagebox.showinfo(
                    "Success",
                    "Filters have been applied successfully!"
                )
            else:
                messagebox.showinfo(
                    "Information",
                    "No filters were specified. All filters have been cleared."
                )

            self.search_window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error saving filters: {str(e)}\nPath: {self.SEARCH_JSON}"
            )

    def clear_filters(self):
        """Limpia todos los filtros y el archivo JSON."""
        try:
            # Limpiar todas las entradas
            for var in self.entry_vars.values():
                var.set("")

            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(self.SEARCH_JSON), exist_ok=True)

            # Limpiar archivo JSON
            with open(self.SEARCH_JSON, 'w', encoding='utf-8') as file:
                json.dump([], file)

            messagebox.showinfo(
                "Success",
                "All filters have been cleared successfully!"
            )

            self.search_window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error clearing filters: {str(e)}"
            )
class IgnoreWindow:
    def __init__(self, master):
        self.ignore_window = tk.Toplevel(master)
        self.ignore_window.title("Ignore List")
        self.ignore_window.geometry("700x400")
        self.ignore_window.resizable(False, False)

        # Configurar el archivo JSON de ignorados
        self.IGNORE_JSON = os.path.join(base_path, 'Configs', 'Ignore.json')

        # Asegurar que el directorio Configs existe
        os.makedirs(os.path.join(base_path, 'Configs'), exist_ok=True)

        # Crear el frame principal con scroll
        self.main_frame = tk.Frame(self.ignore_window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas y scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Empaquetar canvas y scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Lista para almacenar los pares de Entry
        self.entry_pairs = []

        # Mostrar los elementos ignorados existentes
        self.load_ignored_items()

        # Botones de control
        button_frame = tk.Frame(self.ignore_window)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Add New", command=self.add_new_entry).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Apply", command=self.apply_ignored).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Clear All", command=self.clear_ignored).pack(side=tk.LEFT, padx=5)

        # Hacer que la ventana sea modal
        self.ignore_window.transient(master)
        self.ignore_window.grab_set()

    def create_entry_pair(self):
        """Crea un nuevo par de entradas para name y platform"""
        frame = tk.Frame(self.scrollable_frame)
        frame.pack(fill=tk.X, pady=2)

        name_frame = tk.Frame(frame)
        name_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(name_frame, text="Name:").pack(side=tk.LEFT)
        name_entry = tk.Entry(name_frame, width=45)
        name_entry.pack(side=tk.LEFT, padx=5)

        platform_frame = tk.Frame(frame)
        platform_frame.pack(side=tk.LEFT, padx=5)
        tk.Label(platform_frame, text="Platform:").pack(side=tk.LEFT)
        platform_entry = tk.Entry(platform_frame, width=25)
        platform_entry.pack(side=tk.LEFT, padx=5)

        # Botón para eliminar esta entrada
        delete_btn = tk.Button(frame, text="X", command=lambda: self.delete_entry_pair(frame))
        delete_btn.pack(side=tk.RIGHT, padx=5)

        self.entry_pairs.append((name_entry, platform_entry, frame))
        return name_entry, platform_entry

    def delete_entry_pair(self, frame):
        """Elimina un par de entradas"""
        for name_entry, platform_entry, f in self.entry_pairs[:]:
            if f == frame:
                self.entry_pairs.remove((name_entry, platform_entry, f))
                frame.destroy()
                break

    def load_ignored_items(self):
        """Carga los elementos ignorados desde el archivo JSON"""
        try:
            if not os.path.exists(self.IGNORE_JSON):
                with open(self.IGNORE_JSON, 'w', encoding='utf-8') as file:
                    json.dump([], file)
                return

            with open(self.IGNORE_JSON, 'r', encoding='utf-8') as file:
                ignored_items = json.load(file)
                for item in ignored_items:
                    name_entry, platform_entry = self.create_entry_pair()
                    name_entry.insert(0, item.get('name', ''))
                    platform_entry.insert(0, item.get('platform', ''))
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error loading ignored items: {str(e)}"
            )
            with open(self.IGNORE_JSON, 'w', encoding='utf-8') as file:
                json.dump([], file)

    def add_new_entry(self):
        """Añade un nuevo par de entradas vacías"""
        self.create_entry_pair()

    def apply_ignored(self):
        """Aplica y guarda los elementos ignorados"""
        ignored_items = []
        for name_entry, platform_entry, _ in self.entry_pairs:
            name = name_entry.get().strip()
            platform = platform_entry.get().strip()

            # Si ambos están vacíos, ignorar esta entrada
            if not name and not platform:
                continue

            # Aplicar "ALL" cuando corresponda
            if not name:
                name = "ALL"
            if not platform:
                platform = "ALL"

            ignored_items.append({
                "name": name,
                "platform": platform
            })

        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(self.IGNORE_JSON), exist_ok=True)

            # Guardar en el archivo JSON
            with open(self.IGNORE_JSON, 'w', encoding='utf-8') as file:
                json.dump(ignored_items, file, indent=4)

            messagebox.showinfo(
                "Success",
                "Ignore list has been updated successfully!"
            )

            self.ignore_window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error saving ignore list: {str(e)}"
            )

    def clear_ignored(self):
        """Limpia todos los elementos ignorados"""
        try:
            # Limpiar todas las entradas visuales
            for _, _, frame in self.entry_pairs:
                frame.destroy()
            self.entry_pairs.clear()

            # Limpiar archivo JSON
            with open(self.IGNORE_JSON, 'w', encoding='utf-8') as file:
                json.dump([], file)

            messagebox.showinfo(
                "Success",
                "Ignore list has been cleared successfully!"
            )

            self.ignore_window.destroy()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Error clearing ignore list: {str(e)}"
            )
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
def cargar_fuentes_desde_json():
    """Carga las fuentes desde el archivo Configs/Font.json."""
    font_file = os.path.join(base_path, 'Configs', 'Font_bot.json')
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
        icon_path = os.path.join(base_path, 'csgo2.ico')
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
            "Profitability.py",
            "Rentabilidad.py",
            "SteamMarket_vproxy.py",
            "SteamNames_vproxy.py",
            "SteamID_vproxy.py",
            "RapidSkins.py",
            "Csdeals.py",
            "Skinport.py",
            "Cstrade.py",
            "Waxpeer.py",
            "ManncoStore.py",
            "Empire.py",
            "Market.csgo_noproxy.py",
            "Tradeit_noproxy.py",
            "Bitskins.py",
            "Skinout.py",
            "Skindeck.py"
        ]

        for script in self.scripts:
            # Crear un ScriptRunner dentro de cada PanedWindow vertical
            script_runner = ScriptRunner(self.main_paned_window, script, self.main_paned_window)
            self.script_runners.append(script_runner)

        # Configurar la expansión de los frames en el PanedWindow principal
        for runner in self.script_runners:
            self.main_paned_window.paneconfigure(runner.vertical_paned_window, minsize=50)  # Mínimo tamaño para cada panel horizontal
        self.root.bind('<Control-f>', self.show_search_window)
        self.root.bind('<Control-s>', self.show_all_consoles)
        self.root.bind('<Control-i>', self.show_ignore_window)
    def show_all_consoles(self, event=None):
        """Muestra todas las consolas que estaban ocultas."""
        for runner in self.script_runners:
            if not runner.is_console_visible:
                runner.toggle_console()
    def show_search_window(self, event=None):
        """Muestra la ventana de búsqueda."""
        SearchWindow(self.root)
    def show_ignore_window(self, event=None):
        """Muestra la ventana de elementos ignorados."""
        IgnoreWindow(self.root)
if __name__ == "__main__":
    # Ocultar la consola de Python al lanzarse
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    root = tk.Tk()
    app = BotApp(root)
    root.state('zoomed')  # Pantalla completa por defecto
    root.mainloop()
