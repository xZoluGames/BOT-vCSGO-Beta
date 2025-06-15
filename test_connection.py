#!/usr/bin/env python3
# test_connection.py - Verifica la conexión de red

import socket
import urllib.request
import sys

def test_dns():
    """Prueba resolución DNS"""
    print("1. Probando DNS...")
    try:
        ip = socket.gethostbyname("google.com")
        print(f"   ✓ DNS funcionando - google.com = {ip}")
        return True
    except socket.gaierror:
        print("   ✗ Error de DNS - No se puede resolver nombres de host")
        return False

def test_internet():
    """Prueba conexión a internet"""
    print("\n2. Probando conexión a Internet...")
    try:
        urllib.request.urlopen('http://google.com', timeout=5)
        print("   ✓ Conexión a Internet funcionando")
        return True
    except Exception as e:
        print(f"   ✗ Sin conexión a Internet: {e}")
        return False

def test_proxy():
    """Verifica si estás detrás de un proxy"""
    print("\n3. Verificando proxy del sistema...")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
    proxy_found = False
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ! Proxy encontrado: {var} = {value}")
            proxy_found = True
    
    if not proxy_found:
        print("   - No se detectó proxy del sistema")
    
    return proxy_found

def check_hosts_file():
    """Verifica el archivo hosts"""
    print("\n4. Verificando archivo hosts...")
    hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
    try:
        with open(hosts_path, 'r') as f:
            content = f.read()
            if "mannco.store" in content or "tradeit.gg" in content:
                print("   ! Encontradas entradas personalizadas en hosts")
            else:
                print("   ✓ Archivo hosts normal")
    except:
        print("   - No se pudo leer archivo hosts")

def main():
    print("="*60)
    print("DIAGNÓSTICO DE CONEXIÓN - BOT-vCSGO-Beta")
    print("="*60)
    
    dns_ok = test_dns()
    internet_ok = test_internet()
    proxy_detected = test_proxy()
    check_hosts_file()
    
    print("\n" + "="*60)
    print("RESUMEN:")
    print("="*60)
    
    if not dns_ok:
        print("\n⚠️  PROBLEMA DE DNS DETECTADO")
        print("   Soluciones:")
        print("   1. Cambiar DNS a 8.8.8.8 (Google) o 1.1.1.1 (Cloudflare)")
        print("   2. Ejecutar como admin: ipconfig /flushdns")
        print("   3. Verificar configuración de firewall")
    
    if not internet_ok:
        print("\n⚠️  SIN CONEXIÓN A INTERNET")
        print("   Soluciones:")
        print("   1. Verificar conexión de red")
        print("   2. Desactivar VPN si está activa")
        print("   3. Verificar configuración de proxy")
    
    if proxy_detected:
        print("\n⚠️  PROXY CORPORATIVO DETECTADO")
        print("   Los scrapers necesitarán configuración especial")

if __name__ == "__main__":
    import os
    main()