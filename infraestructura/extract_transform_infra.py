import json
import os
import sys
from pathlib import Path

import osmium as o
import requests
from tqdm import tqdm

URL_CHILE_PBF = "http://download.geofabrik.de/south-america/chile-latest.osm.pbf"
LOCAL_PBF_FILENAME = "chile-latest.osm.pbf"
OUTPUT_JSON_FILENAME = "infraestructura.json"

SCRIPT_DIR = Path(__file__).resolve().parent

HIGHWAY_TYPES = {
    "motorway",
    "trunk",
    "primary",
    "secondary",
    "tertiary",
    "unclassified",
    "residential",
    "motorway_link",
    "trunk_link",
    "primary_link",
    "secondary_link",
    "tertiary_link",
    "living_street",
    "service",
    "road",
}


class RoadHandler(o.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.aristas = []

    def way(self, way_obj):
        if "highway" not in way_obj.tags:
            return
        if way_obj.tags["highway"] not in HIGHWAY_TYPES:
            return

        try:
            for index in range(len(way_obj.nodes) - 1):
                source_node = way_obj.nodes[index]
                target_node = way_obj.nodes[index + 1]
                length = o.geom.haversine_distance(source_node.location, target_node.location)
                self.aristas.append(
                    {
                        "source": source_node.ref,
                        "target": target_node.ref,
                        "costo_longitud_m": round(length, 2),
                        "geom": [
                            [source_node.location.lon, source_node.location.lat],
                            [target_node.location.lon, target_node.location.lat],
                        ],
                    }
                )
        except o.InvalidLocationError:
            pass


def download_file_with_progress(url: str, destination: Path) -> bool:
    print(f"Descargando archivo desde {url}...")
    try:
        with requests.get(url, stream=True, timeout=20) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            with tqdm(total=total_size, unit="iB", unit_scale=True, desc=destination.name) as progress_bar:
                with open(destination, "wb") as file_handle:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file_handle.write(chunk)
                            progress_bar.update(len(chunk))
        print(f"Archivo descargado exitosamente en '{destination}'.")
        return True
    except requests.RequestException as exc:
        print(f"Error al descargar el archivo: {exc}")
        return False


def extract_and_transform_infrastructure(osm_pbf_path: Path, output_json_path: Path) -> None:
    print(f"Iniciando la extraccion y transformacion desde '{osm_pbf_path}'...")
    print("Este proceso puede tardar varios minutos.")

    road_handler = RoadHandler()
    road_handler.apply_file(str(osm_pbf_path), locations=True)
    print(f"Procesamiento de aristas completado. Se encontraron {len(road_handler.aristas)} segmentos.")

    print("Construyendo diccionario de nodos unicos...")
    nodos_finales = {}
    for arista in road_handler.aristas:
        source_id = arista["source"]
        target_id = arista["target"]

        if source_id not in nodos_finales:
            lon, lat = arista["geom"][0]
            nodos_finales[source_id] = {"id": source_id, "lon": lon, "lat": lat}

        if target_id not in nodos_finales:
            lon, lat = arista["geom"][1]
            nodos_finales[target_id] = {"id": target_id, "lon": lon, "lat": lat}

    final_structure = {"nodos": list(nodos_finales.values()), "aristas": road_handler.aristas}

    print(f"Guardando la infraestructura transformada en '{output_json_path}'...")
    with open(output_json_path, "w", encoding="utf-8") as file_handle:
        json.dump(final_structure, file_handle)

    print(f"Proceso completado. Archivo '{output_json_path}' generado con exito.")


def file_exists_and_not_empty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


if __name__ == "__main__":
    pbf_path = SCRIPT_DIR / LOCAL_PBF_FILENAME
    json_path = SCRIPT_DIR / OUTPUT_JSON_FILENAME

    force_refresh = any(
        os.getenv(var, "").lower() in {"1", "true", "yes"} for var in ("FORCE_REFRESH_INFRA", "FORCE_REFRESH")
    )

    if file_exists_and_not_empty(json_path) and not force_refresh:
        print(
            f"El archivo transformado '{json_path}' ya existe. Se omite la extraccion "
            "(usa FORCE_REFRESH_INFRA=1 para forzar una nueva descarga)."
        )
        sys.exit(0)

    if force_refresh or not file_exists_and_not_empty(pbf_path):
        if not pbf_path.exists():
            print(f"El archivo de datos '{pbf_path}' no existe. Se iniciara la descarga.")
        elif pbf_path.stat().st_size == 0:
            print(f"El archivo '{pbf_path}' esta vacio. Se iniciara la descarga nuevamente.")
        else:
            print(f"Se forzara la descarga de '{pbf_path}'.")

        if not download_file_with_progress(URL_CHILE_PBF, pbf_path):
            print("La descarga fallo. No se puede continuar.")
            sys.exit(1)
    else:
        print(f"El archivo de datos '{pbf_path}' ya existe. Se omitira la descarga.")

    extract_and_transform_infrastructure(pbf_path, json_path)
