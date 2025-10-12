import osmium as o
import json
import os

# Lista de tipos de carreteras que consideraremos válidas para vehículos.
# ... (esta parte no cambia)
HIGHWAY_TYPES = {
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
    "residential", "motorway_link", "trunk_link", "primary_link",
    "secondary_link", "tertiary_link", "living_street", "service", "road"
}


class RoadHandler(o.SimpleHandler):
    # ... (toda la clase RoadHandler no cambia) ...
    def __init__(self):
        super(RoadHandler, self).__init__()
        self.nodes = {}
        self.aristas = []
        self.nodes_in_ways = set()

    def way(self, w):
        if 'highway' in w.tags and w.tags['highway'] in HIGHWAY_TYPES:
            for i in range(len(w.nodes) - 1):
                source_node = w.nodes[i]
                target_node = w.nodes[i + 1]
                self.nodes_in_ways.add(source_node.ref)
                self.nodes_in_ways.add(target_node.ref)
                try:
                    length = o.geom.haversine_distance(source_node.location, target_node.location)
                except o.InvalidLocationError:
                    continue
                self.aristas.append({
                    'source': source_node.ref,
                    'target': target_node.ref,
                    'costo_longitud_m': round(length, 2),
                    'geom': [
                        [source_node.location.lon, source_node.location.lat],
                        [target_node.location.lon, target_node.location.lat]
                    ]
                })

    def node(self, n):
        pass


def extract_and_transform_infrastructure(osm_pbf_path, output_folder="infraestructura"): # Cambiado a minúscula por consistencia
    print(f"Iniciando la extracción y transformación desde '{osm_pbf_path}'...")
    print("Este proceso puede tardar varios minutos...")

    road_handler = RoadHandler()
    road_handler.apply_file(osm_pbf_path, locations=True)
    print(f"Procesamiento de aristas completado. Se encontraron {len(road_handler.aristas)} segmentos de carretera.")

    print("Construyendo el diccionario de nodos únicos...")
    nodos_finales = {}
    for arista in road_handler.aristas:
        source_id = arista['source']
        target_id = arista['target']
        if source_id not in nodos_finales:
            lon, lat = arista['geom'][0]
            nodos_finales[source_id] = {'id': source_id, 'lon': lon, 'lat': lat}
        if target_id not in nodos_finales:
            lon, lat = arista['geom'][1]
            nodos_finales[target_id] = {'id': target_id, 'lon': lon, 'lat': lat}

    nodos_lista = list(nodos_finales.values())
    print(f"Se encontraron {len(nodos_lista)} nodos únicos en las carreteras.")

    final_structure = {
        'nodos': nodos_lista,
        'aristas': road_handler.aristas
    }

    # --- CAMBIO CLAVE AQUÍ ---
    # Asegurarse de que la carpeta de salida exista antes de intentar escribir en ella.
    os.makedirs(output_folder, exist_ok=True)
    # -------------------------

    output_path = os.path.join(output_folder, 'infraestructura.json')
    print(f"Guardando la infraestructura transformada en '{output_path}'...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_structure, f)

    print(f"¡Proceso completado! Archivo '{output_path}' generado con éxito.")


if __name__ == "__main__":
    # El script busca el archivo .pbf en la misma carpeta donde se ejecuta.
    OSM_FILE_PATH = "chile-251011.osm.pbf"

    if not os.path.exists(OSM_FILE_PATH):
        print(f"Error: No se encontró el archivo '{OSM_FILE_PATH}' en el directorio actual.")
    else:
        # Le decimos que guarde en el directorio actual ('.')
        extract_and_transform_infrastructure(OSM_FILE_PATH, output_folder=".")