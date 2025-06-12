import requests
import json
import time

def make_haloskins_request():
    # URL de la API
    url = "https://api.haloskins.com/steam-trade-center/search/product/list"
    
    # Primero obtener una cookie de sesión
    session = requests.Session()
    
    # Headers de la solicitud
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es",
        "Accept-Encoding": "gzip, deflate, br, zstd",  # Agregado
        "Access_token": "7656500bb7f2486a897361340d24d42e",
        "App_version_code": "web pc",
        "Area": "1",
        "Content-Type": "application/json",
        "Device": "1",
        "Device_id": "b8f49319096d7009487ef6d2ec257a54",
        "Origin": "https://www.haloskins.com",
        "Platform": "halo",
        "Referer": "https://www.haloskins.com/",
        "Host": "api.haloskins.com",  # Agregado
        "Connection": "keep-alive",    # Agregado
        "Sec-Ch-Ua": '"Brave";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Sec-Gpc": "1",
        "Sessionid": "796a8348-c7e8-10a9-6d62-9e83d4ac0e6f",
        "Trace_id": "DvYdqCqDAzYaWSuzmekTfLoOcOpFJw",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }
    
    # Payload de la solicitud
    payload = {
        "appId": 730,
        "limit": 30,
        "page": 2,
        "keyword": "",
        "sort": "2"
    }
    
    try:
        # Primero hacer una petición GET a la página principal para obtener cookies
        session.get("https://www.haloskins.com/", headers={
            "User-Agent": headers["User-Agent"],
            "Origin": headers["Origin"],
            "Referer": "https://www.haloskins.com/"
        })
        
        # Pequeña pausa para simular comportamiento más natural
        time.sleep(1)
        
        # Realizar la solicitud POST con la sesión
        response = session.post(url, headers=headers, json=payload)
        
        # Imprimir headers completos para debug
        print("Request Headers enviados:")
        print(json.dumps(dict(response.request.headers), indent=2))
        
        print("\nResponse Headers recibidos:")
        print(json.dumps(dict(response.headers), indent=2))
        
        # Verificar si la solicitud fue exitosa
        response.raise_for_status()
        
        # Obtener los datos de la respuesta
        data = response.json()
        
        # Imprimir la respuesta formateada
        print("\nRespuesta de la API:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Imprimir información adicional de la respuesta
        print("\nInformación de la respuesta:")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Server: {response.headers.get('Server')}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
    except json.JSONDecodeError as e:
        print(f"Error al decodificar la respuesta JSON: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    make_haloskins_request()