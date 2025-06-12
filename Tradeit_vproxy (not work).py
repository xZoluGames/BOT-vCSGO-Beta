import requests
import json
import os
import sys
import time


class TradeitGGWebClient:
    BASE_API_URI = "https://tradeit.gg/api/v2/"
    BASE_WEBSITE_URI = "https://tradeit.gg/"
    MAX_PAGE_LIMIT = 1000
    WAIT_TIME = 5
    MAX_RETRY_COUNT = 50  # Máximo de reintentos

    def __init__(self, proxies):
        self.proxies = proxies
        self.current_proxy_index = 0

    def get_next_proxy(self):
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy

    def get_inventory_data(self, app_id, offset=0, limit=MAX_PAGE_LIMIT):
        url = f"{self.BASE_API_URI}inventory/data?gameId={app_id}&sortType=Popularity&offset={offset}&limit={limit}&fresh=true"
        print(f"Fetching data from: {url}", flush=True)

        proxy = self.get_next_proxy()
        print(f"Using proxy: {proxy}", flush=True)

        try:
            response = requests.get(url, headers={'Referer': self.BASE_WEBSITE_URI},
                                    proxies={"http": proxy, "https": proxy})

            if response.status_code != 200:
                print(f"Failed to retrieve data: {response.status_code}", flush=True)
                return None

            data = response.json()
            items = data.get('items', [])

            if not items:
                return None

            inventory_data = []

            for item in items:
                name = item.get('name', 'Unnamed Item')
                price_for_trade = item.get('priceForTrade', 0)

                # Convertir el precio a float
                price_for_trade = float(price_for_trade) / 100

                inventory_data.append({
                    "Item": name,
                    "Price": price_for_trade
                })

            return inventory_data

        except requests.RequestException as e:
            print(f"Request error with proxy {proxy}: {e}", flush=True)
            return None

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}", flush=True)
            return None

        except Exception as e:
            print(f"Unexpected error occurred: {e}", flush=True)
            return None

    def load_proxies(self, filename):
        try:
            with open(filename, 'r') as file:
                return [line.strip() for line in file.readlines()]
        except Exception as e:
            print(f"Error loading proxies from {filename}: {e}", flush=True)
            return []

    def save_data_to_json(self, data, filename="tradeit_data.json"):
        # Determinar la ruta base
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        json_folder = os.path.join(base_path, "JSON")
        if not os.path.exists(json_folder):
            os.makedirs(json_folder)

        json_file_path = os.path.join(json_folder, filename)

        try:
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4)
            print(f"Data saved to {json_file_path}", flush=True)
        except Exception as e:
            print(f"Error saving data: {e}", flush=True)

    def run(self, app_id):
        while True:
            offset = 0
            total_inventory = []
            retry_count = 0  # Contador de reintentos

            while True:
                inventory_data = self.get_inventory_data(app_id, offset=offset)

                if not inventory_data:
                    retry_count += 1
                    print(f"No items found. Retry count: {retry_count}/{self.MAX_RETRY_COUNT}", flush=True)

                    if retry_count >= self.MAX_RETRY_COUNT:
                        print(f"Max retry limit ({self.MAX_RETRY_COUNT}) reached. Stopping scraping.", flush=True)
                        break

                    print(f"Waiting {self.WAIT_TIME} seconds before retrying...", flush=True)
                    time.sleep(self.WAIT_TIME)
                    continue  # Volver a intentar

                # Reiniciar el contador de reintentos al encontrar ítems
                retry_count = 0
                total_inventory.extend(inventory_data)
                print(f"Fetched {len(inventory_data)} items. Total so far: {len(total_inventory)}", flush=True)

                offset += 1000  # Incrementar el offset para la siguiente solicitud

            # Guardar los datos recopilados en un archivo JSON
            self.save_data_to_json(total_inventory)

            # Esperar antes de reiniciar el bucle completo
            time.sleep(120)


if __name__ == "__main__":
    # Cargar proxies desde el archivo
    proxies = []
    try:
        # Determinar la ruta base
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        client = TradeitGGWebClient([])
        client.proxies = client.load_proxies(os.path.join(base_path, 'proxy.txt'))  # Cargar proxies desde proxy.txt

        if not client.proxies:
            print("No proxies loaded. Exiting.", flush=True)
            sys.exit(1)  # Salir si no se cargaron proxies

        app_id = "730"
        client.run(app_id)
    except FileNotFoundError:
        print("Archivo de proxies 'proxy.txt' no encontrado. Asegúrate de que el archivo exista.", flush=True)
