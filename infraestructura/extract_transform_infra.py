import os
import json
import osmium as o
import requests
from tqdm import tqdm

# --- CONFIGURACIÓN ---
URL_CHILE_PBF = "http://download.geofabrik.de/south-america/chile-latest.osm.pbf"
LOCAL_PBF_FILENAME = "chile-latest.osm.pbf"
OUTPUT_JSON_FILENAME = "infraestructura.json"

# --- OBTENER LA RUTA DEL DIRECTORIO ACTUAL DEL SCRIPT ---
# Esto es clave: __file__ es la ruta del script que se está ejecutando.
# os.path.dirname() obtiene la carpeta que lo contiene.
# Así, SCRIPT_DIR siempre será la carpeta 'infraestructura/'.
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

HIGHWAY_TYPES = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
    "residential", "motorway_link", "trunk_link", "primary_link",
    "secondary_link", "tertiary_link", "living_street", "service", "road"
}

class RoadHandler(o.SimpleHandler):
    def __init__(self):
        super(RoadHandler, self).__init__()
        self.aristas = []

    def way(self, w):
        if 'highway' in w.tags and w.tags['highway'] in HIGHWAY_TYPES:
            try:
                for i in range(len(w.nodes) - 1):
                    source_node, target_node = w.nodes[i], w.nodes[i + 1]
                    length = o.geom.haversine_distance(source_node.location, target_node.location)
                    self.aristas.append({
                        'source': source_node.ref,
                        'target': target_node.ref,
                        'costo_longitud_m': round(length, 2),
                        'geom': [[source_node.location.lon, source_node.location.lat],
                                 [target_node.location.lon, target_node.location.lat]]
                    })
            except o.InvalidLocationError:
                pass

def download_file_with_progress(url, destination):
    print(f"Descargando archivo desde {url}...")
    try:
        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with tqdm(total=total_size, unit='iB', unit_scale=True, desc=os.path.basename(destination)) as progress_bar:
                with open(destination, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        progress_bar.update(len(chunk))
                        f.write(chunk)
        print(f"Archivo descargado exitosamente en '{destination}'.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error al descargar el archivo: {e}")
        return False

def extract_and_transform_infrastructure(osm_pbf_path, output_json_path):
    print(f"Iniciando la extracción y transformación desde '{osm_pbf_path}'...")
    print("Este proceso puede tardar varios minutos...")

    road_handler = RoadHandler()
    road_handler.apply_file(osm_pbf_path, locations=True)
    print(f"Procesamiento de aristas completado. Se encontraron {len(road_handler.aristas)} segmentos.")

    print("Construyendo diccionario de nodos únicos...")
    nodos_finales = {}
    for arista in road_handler.aristas:
        source_id, target_id = arista['source'], arista['target']
        if source_id not in nodos_finales:
            lon, lat = arista['geom'][0]
            nodos_finales[source_id] = {'id': source_id, 'lon': lon, 'lat': lat}
        if target_id not in nodos_finales:
            lon, lat = arista['geom'][1]
            nodos_finales[target_id] = {'id': target_id, 'lon': lon, 'lat': lat}

    nodos_lista = list(nodos_finales.values())
    print(f"Se encontraron {len(nodos_lista)} nodos únicos.")

    final_structure = {'nodos': nodos_lista, 'aristas': road_handler.aristas}

    print(f"Guardando la infraestructura transformada en '{output_json_path}'...")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_structure, f)

    print(f"¡Proceso completado! Archivo '{output_json_path}' generado con éxito.")

if __name__ == "__main__":
    # Construir las rutas de los archivos usando el directorio del script como base
    pbf_path = os.path.join(SCRIPT_DIR, LOCAL_PBF_FILENAME)
    json_path = os.path.join(SCRIPT_DIR, OUTPUT_JSON_FILENAME)

    # --- LÓGICA DE AUTOMATIZACIÓN ---
    if not os.path.exists(pbf_path):
        print(f"El archivo de datos '{pbf_path}' no existe.")
        if not download_file_with_progress(URL_CHILE_PBF, pbf_path):
            print("La descarga falló. No se puede continuar.")
            exit()
    else:
        print(f"El archivo de datos '{pbf_path}' ya existe. Se omitirá la descarga.")

    extract_and_transform_infrastructure(pbf_path, json_path)