import json
import os
import psycopg2
import ijson
from psycopg2.extras import execute_batch
from dotenv import load_dotenv


def node_generator(json_path):
    """
    Un generador que lee los nodos de un archivo JSON gigante uno por uno,
    evitando cargar todo el archivo en memoria.
    """
    with open(json_path, 'rb') as f:
        for nodo in ijson.items(f, 'nodos.item'):
            yield (nodo['id'], nodo['lon'], nodo['lat'])


def edge_generator(json_path):
    """
    Un generador que lee las aristas de un archivo JSON gigante una por una.
    """
    with open(json_path, 'rb') as f:
        for arista in ijson.items(f, 'aristas.item'):
            linestring_wkt = "LINESTRING(" + ", ".join([f"{lon} {lat}" for lon, lat in arista['geom']]) + ")"
            yield (arista['source'], arista['target'], arista['costo_longitud_m'], linestring_wkt)


def load_infrastructure_to_db(json_path):
    """
    Lee el archivo 'infraestructura.json' en streaming y carga los nodos y aristas
    en la base de datos PostgreSQL usando un método de carga masiva.
    """
    load_dotenv()
    conn = None
    cur = None

    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        print("Conexión a la base de datos para infraestructura exitosa.")

        print("Vaciando tablas de infraestructura (nodos_carreteras, aristas_carreteras)...")
        cur.execute("TRUNCATE TABLE nodos_carreteras, aristas_carreteras RESTART IDENTITY CASCADE;")
        conn.commit()

        print(f"Iniciando la carga de nodos desde '{json_path}'...")
        node_iter = node_generator(json_path)
        execute_batch(cur,
                      "INSERT INTO nodos_carreteras (id, geom) VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326));",
                      node_iter, page_size=5000)
        conn.commit()
        print("Nodos cargados exitosamente.")

        print(f"Iniciando la carga de aristas desde '{json_path}'...")
        edge_iter = edge_generator(json_path)
        execute_batch(cur,
                      "INSERT INTO aristas_carreteras (source, target, costo_longitud_m, geom) VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326));",
                      edge_iter, page_size=5000)
        conn.commit()
        print("Aristas cargadas exitosamente.")

        print("\n¡Carga de datos de infraestructura completada!")

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso de carga: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            if cur:
                cur.close()
            conn.close()
            print("Conexión a la base de datos cerrada.")


# --- BLOQUE MODIFICADO ---
if __name__ == "__main__":
    # Obtiene la ruta de la carpeta donde se encuentra este script
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

    # Construye la ruta completa y correcta al archivo JSON
    JSON_FILE_PATH = os.path.join(SCRIPT_DIR, "infraestructura.json")

    # Verifica si el archivo JSON existe en la ruta correcta
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: No se encontró el archivo '{JSON_FILE_PATH}'.")
        print("Asegúrate de ejecutar primero 'extract_transform_infra.py' para generarlo.")
    else:
        # Llama a la función de carga con la ruta completa
        load_infrastructure_to_db(JSON_FILE_PATH)