import os
import sys

# Configuración para determinar la ruta base
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Definimos las rutas para el archivo de entrada y el archivo de salida
input_file_path = os.path.join(base_path, "proxy.txt")
output_file_path = os.path.join(base_path, "proxy0.txt")

def convert_proxy_format(line):
    # Dividimos cada línea usando ":" para extraer host, puerto, usuario y contraseña
    parts = line.strip().split(":")
    if len(parts) == 4:
        host, port, user, password = parts
        # Formato de la proxy convertida
        return f"http://{user}:{password}@{host}:{port}"
    else:
        print(f"Línea con formato incorrecto: {line}")
        return None

try:
    with open(input_file_path, "r") as input_file, open(output_file_path, "w") as output_file:
        for line in input_file:
            converted_proxy = convert_proxy_format(line)
            if converted_proxy:
                output_file.write(converted_proxy + "\n")
    print("Conversión completada. Las proxies convertidas están en 'converted_proxies.txt'")
except FileNotFoundError:
    print("Archivo 'proxy.txt' no encontrado en la ruta especificada.")
