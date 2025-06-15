#!/usr/bin/env python3
# start_web.py - Inicia la interfaz web moderna

import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    print("\n" + "="*60)
    print("BOT-vCSGO-Beta - Interfaz Web Moderna")
    print("="*60)
    
    # Crear carpeta static si no existe
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    
    # Guardar el HTML en static/index.html
    print("\n1. Configurando archivos...")
    
    # Verificar si existe el HTML
    index_file = static_dir / "index.html"
    if not index_file.exists():
        print("   ❌ No se encontró static/index.html")
        print("   Por favor, guarda el archivo HTML de la interfaz web en static/index.html")
        return
    
    print("   ✓ Archivos configurados")
    
    # Arreglar archivos de Steam si no existen
    print("\n2. Verificando archivos de Steam...")
    if not Path("JSON/item_nameids.json").exists():
        subprocess.run([sys.executable, "fix_steam_files.py"])
    else:
        print("   ✓ Archivos de Steam encontrados")
    
    # Iniciar servidor
    print("\n3. Iniciando servidor web...")
    print("   Servidor: http://localhost:8000")
    print("   Presiona Ctrl+C para detener\n")
    
    # Esperar un poco y abrir navegador
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:8000")
    
    import threading
    threading.Thread(target=open_browser).start()
    
    # Iniciar servidor
    try:
        subprocess.run([sys.executable, "web_server.py"])
    except KeyboardInterrupt:
        print("\n\nServidor detenido")

if __name__ == "__main__":
    main()