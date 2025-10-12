from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import time
import json
from typing import List, Dict, Any


def extract_all_car_urls(base_url):
    # Definimos la lista para guardar todos los links encontrados y un numero maximo de paginas a scrapear
    all_car_links = []
    MAX_PAGES_TO_SCRAPE = 20

    # Bucle para generar páginas y extraer links de vehiculos
    for page_number in range(1, MAX_PAGES_TO_SCRAPE + 1):
        current_page_url = f'{base_url}?Page={page_number}'

        print(f'Analizando pagina {page_number}')

        links_from_page = extract_car_urls_from_page(current_page_url)

        if not links_from_page:
            print(f'No se encontraron más vehículos en la página {page_number}. Terminando el proceso.')
            break

        # Agregamos los links encontrados a la lista general
        all_car_links.extend(links_from_page)

        # Pausa para evitar saturar el servidor y evitar bloqueos
        time.sleep(1)

    return all_car_links

def extract_car_urls_from_page(page_url):
    """
    Recorre una página del catálogo de vehículos y devuelve una lista de URLs de los vehículos.

    :param page_url: La URL de la página del catálogo que se va a analizar.
    :return: Una lista de URLs absolutas para cada vehículo encontrado en la página.
             Retorna una lista vacía si ocurre un error.
    """
    try:
        # Realizamos la petición HTTP GET con un tiempo de espera para evitar que se quede colgada
        response = requests.get(page_url, timeout=10)
        # Lanza una excepción si el codigo de estadi es un error
        response.raise_for_status()
    except requests.RequestException as e:
        # Si hay un error de red o un mal código de estadi, lo imprimimos y retornamos una lista vacia
        print(f'Error al obtener la URL {page_url}: {e}')
        return []

    # Transforma el contenido HTML plano en un objeto BeautifulSoup (arbol de elementos)
    soup = BeautifulSoup(response.content, "html.parser")
    vehicles_urls = []

    # Buscamos todos los 'div' que contiene la información de cada vehículo.
    vehicles_cards = soup.find_all('div', class_='col-12 col-sm-6 col-md-4 col-lg-4 col-xxl-3')

    # Iteramos sobre cada tarjeta de vehiculo encontrada oara extraer el link
    for car in vehicles_cards:
        # buscamos la etiqueta 'a' que contiene el link
        anchor_tag = car.find('a')
        if anchor_tag and anchor_tag.has_attr('href'):
            # obtenemos la url relativa del atributo href
            relative_url = anchor_tag.get('href')
            # Creamos una URL robusta uniendo la url base con la relativa
            absolute_url = urljoin(page_url, relative_url)
            vehicles_urls.append(absolute_url)

    return vehicles_urls


def extract_car_data(car_url: str) -> List[Dict[str, Any]]:
    """
    Extrae los datos de todas las versiones de un vehículo desde su URL específica.
    Una URL puede contener múltiples versiones (ej. manual, automático).

    :param car_url: La URL de la página del detalle del vehículo.
    :return: Una lista de diccionarios, donde cada diccionario es una versión del vehículo.
    """
    # ... (código de la petición requests y la creación del objeto soup) ...
    try:
        response = requests.get(car_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f'Error al obtener la URL del vehículo {car_url}: {e}')
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    vehicle_versions_data = []
    version_cards = soup.find_all('div', class_='card margin-card')

    if not version_cards:
        return []

    for card in version_cards:
        data = {}

        # ... (extracción de modelo_base, version, imagen_url) ...
        # (Esta parte no cambia)
        model_tag = card.find('h6', class_='card-title')
        if model_tag:
            data['modelo_base'] = model_tag.get_text(strip=True)

        version_tag = card.select_one('.title-container > h5.card-title')
        if version_tag:
            data['version'] = version_tag.get_text(strip=True)

        image_tag = card.find('img')
        if image_tag and image_tag.has_attr('src'):
            data['imagen_url'] = image_tag['src']

        # --- SECCIÓN MODIFICADA PARA EL PRECIO ---
        price_tag = card.find('h5', class_='card-title', string=lambda text: '$' in text if text else False)
        if price_tag:
            precio_limpio = price_tag.get_text(strip=True).replace('$', '').replace('.', '')
            # Intentamos convertir el precio a entero. Si falla, asignamos None.
            try:
                data['precio_referencia'] = int(precio_limpio)
            except ValueError:
                # Esto se ejecutará si precio_limpio está vacío o no es un número.
                data['precio_referencia'] = None
                print(
                    f"  -> Advertencia: No se pudo convertir el precio para una versión en {car_url}. Se asignó None.")
        else:
            # Si ni siquiera encontramos la etiqueta del precio, también asignamos None.
            data['precio_referencia'] = None

        # URL de origen
        data['fuente_url'] = car_url

        # --- Extracción de las especificaciones (sin cambios) ---
        specifications = {}
        spec_items = card.select('.card-specifications .list-group-item')

        for item in spec_items:
            key_span = item.find('span')
            value_span = item.find('span', class_='right-span')

            if key_span and value_span:
                key = key_span.get_text(strip=True).replace(':', '')
                value = value_span.get_text(strip=True)
                specifications[key] = value

        data['especificaciones'] = specifications

        vehicle_versions_data.append(data)

    return vehicle_versions_data


# ==============================================================================
# SCRIPT PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    BASE_CATALOG_URL = "https://www.chileautos.cl/catalogo/"

    # --- PASO 1: Obtener todos los links de los vehículos ---
    print("--- INICIANDO PASO 1: Extracción de URLs de vehículos ---")
    car_links = extract_all_car_urls(BASE_CATALOG_URL)
    print(f"\nSe encontraron {len(car_links)} links de modelos de vehículos.")

    # --- PASO 2: Recorrer cada link y extraer los datos de sus versiones ---
    print("\n--- INICIANDO PASO 2: Extracción de datos de cada vehículo ---")
    all_vehicles_data = []

    # Para probar, puedes limitar el número de links a procesar: for car_link in car_links[:5]:
    for i, car_link in enumerate(car_links):
        print(f"Procesando link {i + 1}/{len(car_links)}: {car_link}")

        # La función devuelve una lista de versiones, la agregamos a la lista principal
        versions_on_page = extract_car_data(car_link)

        if versions_on_page:
            print(f"  -> Se encontraron {len(versions_on_page)} versiones en esta página.")
            all_vehicles_data.extend(versions_on_page)
        else:
            print(f"  -> No se encontraron datos de versiones en esta página.")

        # Pausa para ser respetuosos con el servidor
        time.sleep(1)

    # --- PASO 3: Guardar todos los datos en un archivo JSON ---
    print("\n--- INICIANDO PASO 3: Guardando datos en archivo JSON ---")

    # Nombre del archivo de salida
    output_filename = 'chileautos_data.json'

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            # json.dump escribe la lista de diccionarios en el archivo
            # indent=4 formatea el JSON para que sea legible
            # ensure_ascii=False permite guardar caracteres como 'á', 'é', 'ñ' correctamente
            json.dump(all_vehicles_data, f, indent=4, ensure_ascii=False)
        print(
            f"\n¡Éxito! Se guardaron los datos de {len(all_vehicles_data)} vehículos/versiones en el archivo '{output_filename}'")
    except Exception as e:
        print(f"\nOcurrió un error al guardar el archivo JSON: {e}")