import json
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
import queue

base_path = os.path.dirname(os.path.abspath(__file__))

MANNCOSTORE_JSON = os.path.join(base_path, "JSON", "manncostore_data.json")
STEAM_ITEMS_JSON = os.path.join(base_path, "JSON", "steam_listing_prices.json")

class ThreadSafeLogger:
    def __init__(self):
        self._lock = threading.Lock()
    
    def log(self, message):
        with self._lock:
            print(message)

logger = ThreadSafeLogger()

def cargar_datos(ruta):
    try:
        with open(ruta, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        logger.log(f"Archivo {ruta} no encontrado.")
        return []

def iniciar_navegadores(num_navegadores=8):
    navegadores = []
    for i in range(num_navegadores):
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        row = i // 4
        col = i % 4
        width = 384
        height = 432

        driver_path = os.path.join(base_path, 'Chromedriver', 'chromedriver.exe')
        driver = uc.Chrome(options=options, executable_path=driver_path)
        driver.set_window_size(width, height)
        driver.set_window_position(col * width, row * height)
        
        navegadores.append(driver)
    
    return navegadores

def obtener_precio_mas_alto(driver, url):
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-striped tbody"))
            )
            rows = driver.find_elements(By.CSS_SELECTOR, "table.table-striped tbody tr")
            precios = []

            for row in rows:
                celdas = row.find_elements(By.TAG_NAME, 'td')
                if celdas:
                    precio_text = celdas[0].text.strip()
                    if precio_text.startswith('$'):
                        precio_text = precio_text[1:].replace(',', '')
                        if 'or less' in precio_text:
                            precio_text = precio_text.replace('or less', '').strip()
                        try:
                            precio = float(precio_text)
                            precios.append(precio)
                        except ValueError:
                            continue

            if precios:
                return max(precios)
            
            time.sleep(2)
            
        except Exception as e:
            logger.log(f"Error en intento {intento + 1} para URL {url}: {e}")
            if intento < max_intentos - 1:
                time.sleep(3)
            continue
    
    return None

def procesar_item(item, steam_items, navegadores_queue):
    # Obtener un navegador de la cola
    driver = navegadores_queue.get()
    
    try:
        nombre_item = item['Item']
        steam_item = next((item for item in steam_items if item['name'] == nombre_item), None)
        
        if not steam_item or steam_item['price'] == 0:
            return None
            
        precio_steam = steam_item['price']
        url_mannco = item['URL']
        precio_mannco = obtener_precio_mas_alto(driver, url_mannco)
        
        if precio_mannco:
            precio_mannco_con_comision = precio_mannco * 0.95
            rentabilidad = precio_mannco_con_comision - precio_steam
            rentabilidad_porcentaje = (rentabilidad / precio_steam) * 100
            
            if rentabilidad_porcentaje >= 0:
                resultado = {
                    'nombre': nombre_item,
                    'precio_steam': precio_steam,
                    'precio_mannco': precio_mannco,
                    'precio_mannco_con_comision': precio_mannco_con_comision,
                    'rentabilidad': rentabilidad,
                    'rentabilidad_porcentaje': rentabilidad_porcentaje,
                    'url_mannco': url_mannco
                }
                logger.log(f"Item rentable encontrado: {nombre_item} - Rentabilidad: {rentabilidad_porcentaje:.2f}%")
                return resultado
    except Exception as e:
        logger.log(f"Error procesando item {nombre_item}: {e}")
    finally:
        # Devolver el navegador a la cola
        navegadores_queue.put(driver)
    
    return None

def procesar_items_en_paralelo(items, steam_items, navegadores):
    # Crear una cola de navegadores
    navegadores_queue = queue.Queue()
    for nav in navegadores:
        navegadores_queue.put(nav)

    todos_resultados = []
    
    # Usar ThreadPoolExecutor con el número total de navegadores
    with ThreadPoolExecutor(max_workers=len(navegadores)) as executor:
        # Enviar todas las tareas
        futures = {
            executor.submit(procesar_item, item, steam_items, navegadores_queue): item 
            for item in items
        }

        # Recoger resultados
        for future in as_completed(futures):
            resultado = future.result()
            if resultado:
                todos_resultados.append(resultado)
    
    return todos_resultados

def guardar_resultados(resultados, filename='profiteable_sells_manncostore.json'):
    result_path = os.path.join(base_path, "JSON", filename)
    with open(result_path, 'w', encoding='utf-8') as file:
        json.dump(resultados, file, indent=4, ensure_ascii=False)

def main():
    logger.log("Iniciando el script...")
    mannco_items = cargar_datos(MANNCOSTORE_JSON)
    steam_items = cargar_datos(STEAM_ITEMS_JSON)
    
    if not all([mannco_items, steam_items]):
        logger.log("No se pudieron cargar todos los datos necesarios.")
        return
    
    logger.log(f"Datos cargados: {len(mannco_items)} items de MannCo, {len(steam_items)} items de Steam")
    
    # Iniciar navegadores
    navegadores = iniciar_navegadores()
    
    try:
        # Procesar todos los items en paralelo
        todos_resultados = procesar_items_en_paralelo(mannco_items, steam_items, navegadores)
        
        # Ordenar resultados
        todos_resultados = sorted(todos_resultados, key=lambda x: x['rentabilidad_porcentaje'], reverse=True)
        
        if todos_resultados:
            logger.log(f"Proceso completado. Se encontraron {len(todos_resultados)} oportunidades rentables.")
            guardar_resultados(todos_resultados)
            logger.log(f"Resultados guardados en {os.path.join(base_path, 'JSON', 'profiteable_sells_manncostore.json')}")
        else:
            logger.log("No se encontraron oportunidades rentables.")
    
    finally:
        # Cerrar navegadores
        for driver in navegadores:
            driver.quit()

if __name__ == "__main__":
    main()