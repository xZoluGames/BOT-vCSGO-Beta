import undetected_chromedriver as uc
import json
import os
import sys
import time


class TradeitGGWebClient:
    BASE_WEBSITE_URI = "https://tradeit.gg/"
    MAX_PAGE_LIMIT = 1000
    WAIT_TIME = 1
    MAX_RETRY_COUNT = 5  # Máximo de reintentos

    def __init__(self):
        # Configuración del driver
        self.driver = uc.Chrome()

    def get_inventory_data(self, app_id, offset=0, limit=MAX_PAGE_LIMIT):
        url = f"{self.BASE_WEBSITE_URI}api/v2/inventory/data?gameId={app_id}&sortType=Popularity&offset={offset}&limit={limit}&fresh=true"
        print(f"Fetching data from: {url}", flush=True)

        try:
            # Navegar a la URL usando ChromeDriver
            self.driver.get(url)

            # Esperar un momento para que la página cargue completamente
            time.sleep(3)  # Ajusta el tiempo de espera según sea necesario

            # Obtener el contenido JSON usando JavaScript
            page_content = self.driver.execute_script("return document.body.innerText")

            # Parsear el contenido JSON
            data = json.loads(page_content)
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

        except json.JSONDecodeError:
            print("Error: El contenido recibido no es JSON válido.", flush=True)
            return None
        except Exception as e:
            print(f"Error occurred: {e}", flush=True)
            return None

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
            time.sleep(self.WAIT_TIME)


if __name__ == "__main__":
    try:
        app_id = "730"
        client = TradeitGGWebClient()
        client.run(app_id)
    except Exception as e:
        print(f"Error: {e}", flush=True)
