import os
import time
import json
import platform
import sys

# Obtener la ruta base, considerando si el script está congelado (ej. PyInstaller)
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

def cargar_idioma():
    """Carga el idioma desde el archivo de configuración Language.json."""
    config_file = os.path.join(base_path, 'Configs', 'Language.json')
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            config = json.load(file)
            return config.get("Language", "en")  # Por defecto, 'en' si no se encuentra la clave
    except FileNotFoundError:
        print("Archivo de configuración 'Language.json' no encontrado. Usando idioma por defecto 'en'.")
        return "en"

def emitir_pitido():
    if platform.system() == 'Windows':
        import winsound
        winsound.Beep(3000, 150)

# Clase para gestionar las traducciones
class Translator:
    def __init__(self, script_name, lang_code):
        self.script_name = script_name
        self.lang_code = lang_code
        self.translations = self.load_translations()

    def load_translations(self):
        """Carga las traducciones desde el archivo JSON correspondiente."""
        translation_file = os.path.join(base_path, 'Languages', self.lang_code, f'{self.script_name}_{self.lang_code}.json')
        try:
            with open(translation_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Archivo de traducción para el script '{self.script_name}' y el idioma '{self.lang_code}' no encontrado.")
            return {}

    def gettext(self, key, **kwargs):
        """Obtiene la traducción para una clave dada y formatea con parámetros si es necesario."""
        template = self.translations.get(key, key)
        return template.format(**kwargs)

# Ruta al archivo de rentabilidad
RENTABILIDAD_JSON = os.path.join(base_path, 'JSON', 'rentabilidad.json')

# Ruta al archivo de ignorados
IGNORE_JSON = os.path.join(base_path, 'Configs', 'Ignore.json')

# Ruta al archivo de búsqueda
SEARCH_JSON = os.path.join(base_path, 'Configs', 'Search.json')

# Función para limpiar la consola
def limpiar_consola():
    os.system('cls' if platform.system() == 'Windows' else 'clear')
    print(translator.gettext('CLEAR_CONSOLE'), flush=True)


def cargar_ignorados():
    """Carga la configuración de ignorados desde el archivo Ignore.json."""
    try:
        with open(IGNORE_JSON, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Archivo {IGNORE_JSON} no encontrado.", flush=True)
        return []
    except json.JSONDecodeError:
        print(f"Error al decodificar {IGNORE_JSON}. Verificar formato.", flush=True)
        return []


def esta_ignorado(item, ignorados):
    nombre = item['name']
    plataforma = item['platform']
    for ignorado in ignorados:
        if ignorado['name'] == nombre:
            if ignorado['platform'] == 'ALL' or ignorado['platform'] == plataforma:
                return True
        if ignorado['name'] == 'ALL' and ignorado['platform'] == plataforma:
            return True
    return False
def cargar_busquedas():
    """Carga las búsquedas desde el archivo Search.json."""
    try:
        with open(SEARCH_JSON, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Archivo {SEARCH_JSON} no encontrado.", flush=True)
        return []
    except json.JSONDecodeError:
        print(f"Error al decodificar {SEARCH_JSON}. Verificar formato.", flush=True)
        return []


def buscar_coincidencias(compras_rentables, ignorados):
    """Busca coincidencias entre las compras rentables y los criterios de búsqueda."""
    busquedas = cargar_busquedas()

    # Verificar si hay más de un objeto en el array de búsquedas
    if len(busquedas) > 1:
        print("More than 1 item to look for!", flush=True)
        return

    coincidencias = []

    # Campos numéricos que requieren comparación exacta
    campos_numericos = {'buy_price', 'steam_price', 'net_steam_price', 'rentabilidad'}

    # Campos para búsqueda por rango
    campos_rango = {
        'buy_price': ['buy_price_upto', 'buy_price_downto'],
        'steam_price': ['steam_price_upto', 'steam_price_downto'],
        'net_steam_price': ['net_steam_price_upto', 'net_steam_price_downto'],
        'rentabilidad': ['rentabilidad_upto', 'rentabilidad_downto']
    }

    # Si hay criterios de búsqueda
    if busquedas:
        busqueda = busquedas[0]  # Tomamos el único objeto de búsqueda

        for compra in compras_rentables:
            if esta_ignorado(compra, ignorados):
                continue

            # Verificar cada criterio en la búsqueda
            coincide = True
            for campo, valor_busqueda in busqueda.items():
                valor_compra = compra.get(campo, '')

                # Verificar si es un campo de rango
                es_campo_rango = False
                for campo_base, variantes in campos_rango.items():
                    if campo in variantes:
                        es_campo_rango = True
                        valor_compra = compra.get(campo_base, 0)
                        # Multiplicar por 100 si es rentabilidad
                        if campo_base == 'rentabilidad':
                            valor_compra = float(valor_compra) * 100

                        try:
                            valor_compra = float(valor_compra)
                            valor_busqueda = float(valor_busqueda)

                            if campo.endswith('_upto'):
                                if valor_compra < valor_busqueda:
                                    coincide = False
                                    break
                            elif campo.endswith('_downto'):
                                if valor_compra > valor_busqueda:
                                    coincide = False
                                    break
                        except (ValueError, TypeError):
                            coincide = False
                            break
                        break

                if es_campo_rango:
                    continue

                # Si el campo es numérico, hacer comparación exacta
                if campo in campos_numericos:
                    try:
                        # Para rentabilidad, multiplicamos por 100 ya que así se muestra
                        if campo == 'rentabilidad':
                            valor_compra = float(valor_compra) * 100
                        else:
                            valor_compra = float(valor_compra)
                        valor_busqueda = float(valor_busqueda)

                        if valor_compra != valor_busqueda:
                            coincide = False
                            break
                    except (ValueError, TypeError):
                        coincide = False
                        break
                else:
                    # Para campos de texto, mantener la búsqueda por subcadena
                    if str(valor_compra).lower().find(str(valor_busqueda).lower()) == -1:
                        coincide = False
                        break

            if coincide:
                coincidencias.append(compra)

        if coincidencias:
            print(f"{translator.gettext('SEARCH_RESULTS')}", flush=True)
            for compra in coincidencias:
                imprimir_compra(compra)
        else:
            print(f"{translator.gettext('NOTHING_WAS_FOUND')}", flush=True)
    else:
        # Si no hay búsquedas, mostrar todas las compras rentables no ignoradas
        for compra in compras_rentables:
            if not esta_ignorado(compra, ignorados):
                imprimir_compra(compra)


def imprimir_compra(compra):
    """Imprime los detalles de una compra."""
    nombre = compra['name']
    precio_compra = compra['buy_price']
    precio_steam = compra['steam_price']
    precio_steam_neto = compra['net_steam_price']
    rentabilidad = compra['rentabilidad'] * 100
    plataforma = compra['platform']
    link_plataforma = compra['link']
    link_steam = compra['steam_link']

    emitir_pitido()
    print(f"{translator.gettext('ITEM_NAME')}: {nombre}", flush=True)
    print(f"{translator.gettext('BUY_PRICE')}: {plataforma} {translator.gettext('FOR')} $ {precio_compra:.2f}",
          flush=True)
    print(f"{translator.gettext('LINK')}: {link_plataforma}", flush=True)
    print(
        f"{translator.gettext('SELL_PRICE')}: {translator.gettext('STEAM')} {translator.gettext('FOR')} $ {precio_steam:.2f} {translator.gettext('AFTER_FEE')} $ {precio_steam_neto:.2f}",
        flush=True)
    print(f"{translator.gettext('LINK')}: {link_steam}", flush=True)
    print(f"{translator.gettext('PROFITABILITY')}: {rentabilidad:.2f}%", flush=True)
    print("-" * 40, flush=True)


def imprimir_compras_rentables(ignorados):
    """Lee e imprime las compras rentables desde el archivo JSON, excluyendo las ignoradas."""
    try:
        with open(RENTABILIDAD_JSON, 'r', encoding='utf-8') as file:
            compras_rentables = json.load(file)

        print(f"{translator.gettext('PROFITEABLE_FLIPS')}", flush=True)
        for compra in compras_rentables:
            if not esta_ignorado(compra, ignorados):
                imprimir_compra(compra)

    except Exception as e:
        print(f"{translator.gettext('ERROR_CALCULATING_PROFITABILITY').format(str(e))}", flush=True)
        print(f"{e}", flush=True)


def monitorear_archivos():
    """Monitorea cambios en los archivos rentabilidad.json, Ignore.json y Search.json."""
    try:
        ultima_modificacion_rentabilidad = os.path.getmtime(RENTABILIDAD_JSON)
        ultima_modificacion_ignore = os.path.getmtime(IGNORE_JSON)
        ultima_modificacion_search = os.path.getmtime(SEARCH_JSON)

        while True:
            try:
                nueva_modificacion_rentabilidad = os.path.getmtime(RENTABILIDAD_JSON)
                nueva_modificacion_ignore = os.path.getmtime(IGNORE_JSON)
                nueva_modificacion_search = os.path.getmtime(SEARCH_JSON)

                if (nueva_modificacion_rentabilidad != ultima_modificacion_rentabilidad or
                        nueva_modificacion_ignore != ultima_modificacion_ignore or
                        nueva_modificacion_search != ultima_modificacion_search):
                    limpiar_consola()
                    ignorados = cargar_ignorados()

                    with open(RENTABILIDAD_JSON, 'r', encoding='utf-8') as file:
                        compras_rentables = json.load(file)

                    # Solo llamar a buscar_coincidencias() ya que manejará tanto el caso
                    # de búsqueda como el caso de mostrar todas las compras no ignoradas
                    buscar_coincidencias(compras_rentables, ignorados)

                    ultima_modificacion_rentabilidad = nueva_modificacion_rentabilidad
                    ultima_modificacion_ignore = nueva_modificacion_ignore
                    ultima_modificacion_search = nueva_modificacion_search

            except FileNotFoundError:
                time.sleep(1)
                continue
            except json.JSONDecodeError:
                time.sleep(1)
                continue

            time.sleep(1)

    except Exception as e:
        print(f"Error en la monitorización de archivos: {e}", flush=True)

# Cargar el idioma desde la configuración
language_code = cargar_idioma()

# Cargar el archivo de traducciones para 'rentabilidad'
translator = Translator('rentabilidad', language_code)

if __name__ == "__main__":
    ignorados = cargar_ignorados()
    with open(RENTABILIDAD_JSON, 'r', encoding='utf-8') as file:
        compras_rentables = json.load(file)
    buscar_coincidencias(compras_rentables, ignorados)
    monitorear_archivos()
