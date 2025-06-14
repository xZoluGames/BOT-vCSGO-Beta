#!/usr/bin/env python3
# gui_launcher.py - Lanzador de interfaces gráficas

import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
from pathlib import Path

def launch_modern_gui():
    """Lanza la interfaz moderna"""
    try:
        subprocess.Popen([sys.executable, "gui_modern.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo lanzar la GUI moderna: {e}")

def launch_classic_gui():
    """Lanza la interfaz clásica (Bot.py)"""
    try:
        subprocess.Popen([sys.executable, "Bot.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo lanzar la GUI clásica: {e}")

def launch_lite_gui():
    """Lanza la interfaz lite"""
    try:
        subprocess.Popen([sys.executable, "Bot_lite.py"])
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo lanzar la GUI lite: {e}")

def launch_console():
    """Lanza en modo consola"""
    root.destroy()
    print("\n" + "="*60)
    print("MODO CONSOLA - BOT-vCSGO-Beta v2.0")
    print("="*60)
    print("\nComandos disponibles:")
    print("  python run_scrapers.py status")
    print("  python run_scrapers.py monitor")
    print("  python run_scrapers.py profitability")
    print("  python setup_database.py --check")
    print("\nConsulta el README.md para más información")

# Crear ventana principal
root = tk.Tk()
root.title("BOT-vCSGO-Beta - Selector de Interfaz")
root.geometry("400x300")
root.configure(bg='#1e1e1e')

# Título
title_label = tk.Label(
    root,
    text="BOT-vCSGO-Beta v2.0",
    font=('Arial', 16, 'bold'),
    bg='#1e1e1e',
    fg='#00d4ff'
)
title_label.pack(pady=20)

# Descripción
desc_label = tk.Label(
    root,
    text="Selecciona la interfaz que prefieres usar:",
    font=('Arial', 12),
    bg='#1e1e1e',
    fg='white'
)
desc_label.pack(pady=10)

# Botones
button_style = {
    'font': ('Arial', 12, 'bold'),
    'width': 25,
    'height': 2,
    'bd': 0,
    'cursor': 'hand2'
}

# GUI Moderna (Recomendada)
modern_btn = tk.Button(
    root,
    text="🎮 Interfaz Moderna\n(Recomendada)",
    command=launch_modern_gui,
    bg='#00d4ff',
    fg='black',
    **button_style
)
modern_btn.pack(pady=5)

# GUI Clásica
classic_btn = tk.Button(
    root,
    text="📺 Interfaz Clásica\n(Bot.py original)",
    command=launch_classic_gui,
    bg='#3d3d3d',
    fg='white',
    **button_style
)
classic_btn.pack(pady=5)

# GUI Lite
lite_btn = tk.Button(
    root,
    text="⚡ Interfaz Lite\n(Bot_lite.py)",
    command=launch_lite_gui,
    bg='#3d3d3d',
    fg='white',
    **button_style
)
lite_btn.pack(pady=5)

# Modo Consola
console_btn = tk.Button(
    root,
    text="💻 Modo Consola\n(Terminal)",
    command=launch_console,
    bg='#2d2d2d',
    fg='white',
    **button_style
)
console_btn.pack(pady=5)

# Centrar ventana
root.update_idletasks()
x = (root.winfo_screenwidth() // 2) - (200)
y = (root.winfo_screenheight() // 2) - (150)
root.geometry(f"400x300+{x}+{y}")

root.mainloop()