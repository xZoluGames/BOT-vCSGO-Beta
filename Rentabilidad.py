import json
import os
import platform
import sys
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
RAPIDSKINS_JSON = os.path.join(base_path, "JSON", "rapidskins_data.json")
STEAM_ITEMS_JSON = os.path.join(base_path, "JSON", "steam_items.json")
CSDEALS_JSON = os.path.join(base_path, "JSON", "csdeals_data.json")
MANNCOSTORE_JSON = os.path.join(base_path, "JSON", "manncostore_data.json")
SNIPESKINS_JSON = os.path.join(base_path, "JSON", "snipeskins_data.json")
CSTRADE_JSON = os.path.join(base_path, "JSON", "cstrade_data.json")
RUSTSKINS_JSON = os.path.join(base_path, "JSON", "rustskins_data.json")
WAXPEER_JSON = os.path.join(base_path, "JSON", "waxpeer_data.json")
SKINPORT_JSON = os.path.join(base_path, "JSON", "skinport_data.json")
RENTABILIDAD_JSON = os.path.join(base_path, "JSON", "rentabilidad.json")
TRADEIT_JSON = os.path.join(base_path, "JSON", "tradeit_data.json")
EMPIRE_JSON = os.path.join(base_path, "JSON", "empire_data.json")
MARKETCSGO_JSON = os.path.join(base_path, "JSON", "market.csgo_data.json")
BITSKINS_JSON = os.path.join(base_path, "JSON", "bitskins_data.json")
NOTIFICATIONS_JSON = os.path.join(base_path, "Configs", "Notifications.json")
SKINOUT_JSON = os.path.join(base_path, "JSON", "skinout_data.json")
SKINDECK_JSON = os.path.join(base_path, "JSON", "skindeck_data.json")
WHITE_JSON = os.path.join(base_path, "JSON", "white_data.json")
LISSKINS_JSON = os.path.join(base_path, "JSON", "lisskins_data.json")
SHADOWPAY_JSON = os.path.join(base_path, "JSON", "shadowpay_data.json")

CSDEALS_URL = "https://cs.deals/es/market/csgo/?name="
CSDEALS_URL2 = "&sort=price"
STEAM_URL = "https://steamcommunity.com/market/listings/730/"
WAXPEER_URL = "https://waxpeer.com/es/?game=csgo&sort=ASC&order=price&all=0&exact=0&search="
SKINPORT_URL = "https://skinport.com/es/market?search="
SKINPORT_URL2 = "&sort=price&order=asc"
RAPIDSKINS_URL = "https://rapidskins.com/market"
CSTRADE_URL = "https://cs.trade/trade?market_name="
TRADEIT_URL = "https://tradeit.gg/csgo/trade"
EMPIRE_URL = "https://csgoempire.com/item/"
MARKETCSGO_URL = "https://market.csgo.com/"
BITSKINS_URL = 'https://bitskins.com/market/cs2?search={"order":[{"field":"price","order":"ASC"}],"where":{"skin_name":"'
BITSKINS_URL2 = '"}}'
SKINOUT_URL = "https://skinout.gg/en/market/"
SKINDECK_URL = "https://skindeck.com/sell?tab=withdraw"
LISSKINS_URL = "https://lis-skins.com/ru/market/csgo/"
SHADOWPAY_URL = "https://shadowpay.com/csgo-items?search="
SHADOWPAY_URL2 = "&sort_column=price&sort_dir=asc"

def obtener_tiempo_modificacion(filepath):
    return os.path.getmtime(filepath)
last_modified_rapidskins = obtener_tiempo_modificacion(RAPIDSKINS_JSON)
last_modified_csdeals = obtener_tiempo_modificacion(CSDEALS_JSON)
last_modified_manncostore = obtener_tiempo_modificacion(MANNCOSTORE_JSON)
last_modified_cstrade = obtener_tiempo_modificacion(CSTRADE_JSON)
last_modified_waxpeer = obtener_tiempo_modificacion(WAXPEER_JSON)
last_modified_skinport = obtener_tiempo_modificacion(SKINPORT_JSON)
last_modified_tradeit = obtener_tiempo_modificacion(TRADEIT_JSON)
last_modified_empire = obtener_tiempo_modificacion(EMPIRE_JSON)
last_modified_marketcsgo = obtener_tiempo_modificacion(MARKETCSGO_JSON)
last_modified_bitskins = obtener_tiempo_modificacion(BITSKINS_JSON)
last_modified_skinout = obtener_tiempo_modificacion(SKINOUT_JSON)
last_modified_skindeck = obtener_tiempo_modificacion(SKINDECK_JSON)
last_modified_white = obtener_tiempo_modificacion(WHITE_JSON)
last_modified_lisskins = obtener_tiempo_modificacion(LISSKINS_JSON)
last_modified_shadowpay = obtener_tiempo_modificacion(SHADOWPAY_JSON)
def cargar_idioma():
    config_file = os.path.join(base_path, 'Configs', 'Language.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config.get("Language", "en")
    except FileNotFoundError:
        print("Archivo de configuración 'Language.json' no encontrado. Usando idioma por defecto 'en'.")
        return "en"
class Translator:
    def __init__(self, script_name, lang_code):
        self.script_name = script_name
        self.lang_code = lang_code
        self.translations = self.load_translations()
    def load_translations(self):
        translation_file = os.path.join(base_path, 'Languages', self.lang_code, f'{self.script_name}_{self.lang_code}.json')
        try:
            with open(translation_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Archivo de traducción para el script '{self.script_name}' y el idioma '{self.lang_code}' no encontrado.")
            return {}
    def gettext(self, key, **kwargs):
        template = self.translations.get(key, key)
        return template.format(**kwargs)
language_code = cargar_idioma()
translator = Translator('rentabilidad', language_code)
def subtract_fee(input_value):
    intervals = [0.02, 0.21, 0.32, 0.43]
    fees = [0.02, 0.03, 0.04, 0.05, 0.07, 0.09]
    while input_value > intervals[-1]:
        last_element = intervals[-1]
        if len(intervals) % 2 == 0:
            intervals.append(round(last_element + 0.12, 2))
        else:
            intervals.append(round(last_element + 0.11, 2))
    while len(intervals) > len(fees):
        last_element = fees[-1]
        if len(fees) % 2 == 0:
            fees.append(round(last_element + 0.01, 2))
        else:
            fees.append(round(last_element + 0.02, 2))
    first_greater = next((value for value in intervals if value >= input_value), None)
    index_of_first_greater = intervals.index(first_greater)
    fee_subtraction = round(input_value - fees[index_of_first_greater - 1], 2)
    return fee_subtraction
def calcular_rentabilidad(steam_price, purchase_price):
    net_steam_price = subtract_fee(steam_price)
    if purchase_price == 0:
        return 0, net_steam_price
    rentabilidad = round((net_steam_price - purchase_price) / purchase_price, 4)
    return rentabilidad, net_steam_price
def limpiar_consola():
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    print(translator.gettext('CLEAR_CONSOLE'), flush=True)
def emitir_pitido():
    if platform.system() == 'Windows':
        import winsound
        winsound.Beep(3000, 150)
def cargar_rentabilidad_anterior():
    if os.path.exists(RENTABILIDAD_JSON):
        with open(RENTABILIDAD_JSON, 'r', encoding='utf-8') as file:
            return json.load(file)
    return []
def guardar_rentabilidad_nueva(nueva_rentabilidad):
    rentabilidad_anterior = cargar_rentabilidad_anterior()
    if nueva_rentabilidad != rentabilidad_anterior:
        with open(RENTABILIDAD_JSON, 'w', encoding='utf-8') as file:
            json.dump(nueva_rentabilidad, file, indent=4)
        print("Nueva rentabilidad guardada.")
    else:
        print("No se ha encontrado rentabilidad diferente.")
def organizar_compras_rentables(compras_rentables):
    compras_rentables.sort(key=lambda x: x['rentabilidad'])
    return compras_rentables
def comparar_precios():
    compras_rentables = []
    profitability_csdeals = 0.5
    profitability_cstrade = 0.5
    profitability_manncostore = 0.5
    profitability_rapidskins = 0.5
    profitability_skinport = 0.5
    profitability_tradeit = 0.5
    profitability_waxpeer = 0.5
    profitability_empire = 0.5
    profitability_marketcsgo = 0.5
    profitability_bitskins = 0.5
    profitability_skinout = 0.5
    profitability_skindeck = 0.5
    profitability_white = 0.5
    profitability_lisskins = 0.5
    profitability_shadowpay = 0.5
    try:
        with open(RAPIDSKINS_JSON, 'r', encoding='utf-8') as file:
            rapidskins_data = json.load(file)
        with open(STEAM_ITEMS_JSON, 'r', encoding='utf-8') as file:
            steam_items_data = json.load(file)
        with open(CSDEALS_JSON, 'r', encoding='utf-8') as file:
            csdeals_data = json.load(file)
        with open(MANNCOSTORE_JSON, 'r', encoding='utf-8') as file:
            manncostore_data = json.load(file)
        with open(CSTRADE_JSON, 'r', encoding='utf-8') as file:
            cstrade_data = json.load(file)
        with open(WAXPEER_JSON, 'r', encoding='utf-8') as file:
            waxpeer_data = json.load(file)
        with open(SKINPORT_JSON, 'r', encoding='utf-8') as file:
            skinport_data = json.load(file)
        with open(EMPIRE_JSON, 'r', encoding='utf-8') as file:
            empire_data = json.load(file)
        with open(TRADEIT_JSON, 'r', encoding='utf-8') as file:
            tradeit_data = json.load(file)
        with open(MARKETCSGO_JSON, 'r', encoding='utf-8') as file:
            marketcsgo_data = json.load(file)
        with open(BITSKINS_JSON, 'r', encoding='utf-8') as file:
            bitskins_data = json.load(file)
        with open(SKINOUT_JSON, 'r', encoding='utf-8') as file:
            skinout_data = json.load(file)
        with open(SKINDECK_JSON, 'r', encoding='utf-8') as file:
            skindeck_data = json.load(file)
        with open(WHITE_JSON, 'r', encoding='utf-8') as file:
            white_data = json.load(file)
        with open(LISSKINS_JSON, 'r', encoding='utf-8') as file:
            lisskins_data = json.load(file)
        with open(SHADOWPAY_JSON, 'r', encoding='utf-8') as file:
            shadowpay_data = json.load(file)
        steam_items_dict = {item['name']: item['price'] for item in steam_items_data}
        try:
            with open(NOTIFICATIONS_JSON, 'r') as f:
                notifications = json.load(f)
                profitability_csdeals = float(notifications.get('profitability_csdeals', profitability_csdeals))
                profitability_cstrade = float(notifications.get('profitability_cstrade', profitability_cstrade))
                profitability_manncostore = float(notifications.get('profitability_manncostore', profitability_manncostore))
                profitability_rapidskins = float(notifications.get('profitability_rapidskins', profitability_rapidskins))
                profitability_empire = float(notifications.get('profitability_empire', profitability_empire))
                profitability_skinport = float(notifications.get('profitability_skinport', profitability_skinport))
                profitability_tradeit = float(notifications.get('profitability_tradeit', profitability_tradeit))
                profitability_waxpeer = float(notifications.get('profitability_waxpeer', profitability_waxpeer))
                profitability_marketcsgo = float(notifications.get('profitability_marketcsgo', profitability_marketcsgo))
                profitability_bitskins = float(notifications.get('profitability_bitskins', profitability_bitskins))
                profitability_skinout = float(notifications.get('profitability_skinout', profitability_skinout))
                profitability_skindeck = float(notifications.get('profitability_skindeck', profitability_skindeck))
                profitability_white = float(notifications.get('profitability_white', profitability_white))
                profitability_lisskins = float(notifications.get('profitability_lisskins', profitability_lisskins))
                profitability_shadowpay = float(notifications.get('profitability_shadowpay', profitability_shadowpay))
        except FileNotFoundError:
            print(f"Error: '{NOTIFICATIONS_JSON}' not found.", flush=True)
        for item in rapidskins_data:
            name = item['marketHashName']
            buy_price = item['price']['coinAmount'] / 100.0
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_rapidskins:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Rapidskins',
                        'link': RAPIDSKINS_URL
                    }
                    compras_rentables.append(info)
        for item in csdeals_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_csdeals:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Csdeals',
                        'link': CSDEALS_URL + name + CSDEALS_URL2
                    }
                    compras_rentables.append(info)
        for item in manncostore_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            link = item['URL']
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_manncostore:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Manncostore',
                        'link': link
                    }
                    compras_rentables.append(info)
        for item in cstrade_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_cstrade:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Cstrade',
                        'link': CSTRADE_URL + name
                    }
                    compras_rentables.append(info)
        for item in waxpeer_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_waxpeer:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Waxpeer',
                        'link': WAXPEER_URL + name
                    }
                    compras_rentables.append(info)
        for item in skinport_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_skinport:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Skinport',
                        'link': SKINPORT_URL + name + SKINPORT_URL2
                    }
                    compras_rentables.append(info)
        for item in tradeit_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_tradeit:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Tradeit',
                        'link': TRADEIT_URL
                    }
                    compras_rentables.append(info)
        for item in empire_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            item_id = str(item.get("id", "Unknown"))
            buy_coin = float(item['Coin'])
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_empire:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'buy_coin': buy_coin,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Empire',
                        'link': EMPIRE_URL + item_id
                    }
                    compras_rentables.append(info)
        for item in marketcsgo_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_marketcsgo:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'MarketCsgo',
                        'link': MARKETCSGO_URL + name
                    }
                    compras_rentables.append(info)
        for item in bitskins_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_bitskins:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Bitskins',
                        'link': BITSKINS_URL + name + BITSKINS_URL2
                    }
                    compras_rentables.append(info)
        def limpiar_texto(texto):
            # Removemos los paréntesis y su contenido
            texto = texto.replace("(", "").replace(")", "")

            # Reemplazamos caracteres especiales y espacios con guiones
            caracteres_especiales = ["|", " ", ".", ",", ";", ":", "!", "?", "'", '"', "™"]
            for caracter in caracteres_especiales:
                texto = texto.replace(caracter, "-")

            # Eliminamos guiones múltiples si se generaron
            while "--" in texto:
                texto = texto.replace("--", "-")

            # Eliminamos guiones al inicio y final si existen
            texto = texto.strip("-")

            return texto
        for item in skinout_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            name_format = limpiar_texto(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_skinout:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Skinout',
                        'link': SKINOUT_URL + name_format
                    }
                    compras_rentables.append(info)
        for item in skindeck_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_skindeck:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Skindeck',
                        'link': SKINDECK_URL
                    }
                    compras_rentables.append(info)
        for item in white_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            link = item['URL']
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_white:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'White',
                        'link': link
                    }
                    compras_rentables.append(info)
        for item in lisskins_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            link = item['URL']
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_lisskins:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Lisskins',
                        'link': link
                    }
                    compras_rentables.append(info)
        for item in shadowpay_data:
            name = item['Item']
            buy_price = float(item['Price'])
            steam_price = steam_items_dict.get(name)
            if steam_price:
                rentabilidad, net_steam_price = calcular_rentabilidad(steam_price, buy_price)
                if rentabilidad >= profitability_shadowpay:
                    info = {
                        'name': name,
                        'buy_price': buy_price,
                        'steam_price': steam_price,
                        'steam_link': STEAM_URL + name,
                        'net_steam_price': net_steam_price,
                        'rentabilidad': rentabilidad,
                        'platform': 'Shadowpay',
                        'link': SHADOWPAY_URL + name + SHADOWPAY_URL2
                    }
                    compras_rentables.append(info)
        compras_rentables = organizar_compras_rentables(compras_rentables)
        guardar_rentabilidad_nueva(compras_rentables)
    except Exception as e:
        print(translator.gettext('ERROR_CALCULATING_PROFITABILITY'), flush=True)
        print(f"{e}")
while True:
    current_modified_rapidskins = os.path.getmtime(RAPIDSKINS_JSON)
    current_modified_csdeals = os.path.getmtime(CSDEALS_JSON)
    current_modified_manncostore = os.path.getmtime(MANNCOSTORE_JSON)
    current_modified_cstrade = os.path.getmtime(CSTRADE_JSON)
    current_modified_waxpeer = os.path.getmtime(WAXPEER_JSON)
    current_modified_skinport = os.path.getmtime(SKINPORT_JSON)
    current_modified_tradeit = os.path.getmtime(TRADEIT_JSON)
    current_modified_empire = os.path.getmtime(EMPIRE_JSON)
    current_modified_marketcsgo = os.path.getmtime(MARKETCSGO_JSON)
    current_modified_bitskins = os.path.getmtime(BITSKINS_JSON)
    current_modified_skinout = os.path.getmtime(SKINOUT_JSON)
    current_modified_skindeck = os.path.getmtime(SKINDECK_JSON)
    current_modified_white = os.path.getmtime(WHITE_JSON)
    current_modified_lisskins = os.path.getmtime(LISSKINS_JSON)
    current_modified_shadowpay = os.path.getmtime(SHADOWPAY_JSON)
    if (current_modified_rapidskins != last_modified_rapidskins) or \
       (current_modified_csdeals != last_modified_csdeals) or \
       (current_modified_manncostore != last_modified_manncostore) or \
       (current_modified_cstrade != last_modified_cstrade) or \
       (current_modified_waxpeer != last_modified_waxpeer) or \
       (current_modified_skinport != last_modified_skinport) or \
       (current_modified_empire != last_modified_empire) or \
       (current_modified_marketcsgo != last_modified_marketcsgo) or \
       (current_modified_bitskins != last_modified_bitskins) or \
       (current_modified_skinout != last_modified_skinout) or \
       (current_modified_skindeck != last_modified_skindeck) or \
       (current_modified_white != last_modified_white) or \
       (current_modified_lisskins != last_modified_lisskins) or \
       (current_modified_shadowpay != last_modified_shadowpay) or \
       (current_modified_tradeit != last_modified_tradeit):
        last_modified_white = current_modified_white
        last_modified_bitskins = current_modified_bitskins
        last_modified_marketcsgo = current_modified_marketcsgo
        last_modified_empire = current_modified_empire
        last_modified_rapidskins = current_modified_rapidskins
        last_modified_csdeals = current_modified_csdeals
        last_modified_manncostore = current_modified_manncostore
        last_modified_cstrade = current_modified_cstrade
        last_modified_waxpeer = current_modified_waxpeer
        last_modified_skinport = current_modified_skinport
        last_modified_tradeit = current_modified_tradeit
        last_modified_skinout = current_modified_skinout
        last_modified_skindeck = current_modified_skindeck
        last_modified_lisskins = current_modified_lisskins
        last_modified_shadowpay = current_modified_shadowpay
        limpiar_consola()
        print(translator.gettext('WAITING_FOR_NEXT_UPDATE'), flush=True)
        comparar_precios()
