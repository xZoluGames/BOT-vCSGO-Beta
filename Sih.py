import requests

# Definir la URL y los parámetros de consulta
url = 'https://api.sih.market/api/v1/get-items'
params = {
    'minified': 'false',
    'extended': 'false',
    'appId': '730',
}

# Realizar la solicitud GET
response = requests.get(url, params=params)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Imprimir el contenido de la respuesta en formato JSON
    print(response.json())
else:
    print(f"Error: {response.status_code}")
