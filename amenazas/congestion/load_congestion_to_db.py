import os
import psycopg2
import json
from dotenv import load_dotenv
import glob
from psycopg2.extras import execute_batch


def find_latest_congestion_json(directory):
    """Encuentra el archivo de congestión más reciente en la carpeta."""
    list_of_files = glob.glob(os.path.join(directory, 'congestion_metadata_*.json'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)


def load_congestion_data():
    """
    Lee el archivo JSON de congestión más reciente y carga los datos
    en la tabla 'amenazas' de la base de datos.
    """
    load_dotenv()
    conn = None
    try:
        SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
        json_path = find_latest_congestion_json(SCRIPT_DIR)

        if not json_path:
            raise FileNotFoundError(
                "No se encontró 'congestion_metadata_*.json'. Ejecuta extract_transform_congestion.py primero.")

        print(f"Cargando datos de congestión desde: {os.path.basename(json_path)}")

        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        print("Conexión a la BD para amenazas exitosa.")

        print("Vaciando tabla de amenazas...")
        cur.execute("TRUNCATE TABLE amenazas RESTART IDENTITY;")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        congestion_records = data.get('congestion_data', [])

        # Preparar los datos para una inserción masiva
        records_to_insert = []
        for record in congestion_records:
            records_to_insert.append((
                record['arista_id'],
                'congestion',  # Tipo de amenaza
                record['factor_congestion'],  # Valor numérico de la amenaza
                record['fecha_medicion'],
                record['geom']  # El GeoJSON se pasa como string
            ))

        # Usar execute_batch para una inserción eficiente de múltiples filas
        insert_query = """
                       INSERT INTO amenazas (arista_id, tipo_amenaza, valor, fecha_medicion, geom)
                       VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)); \
                       """
        execute_batch(cur, insert_query, records_to_insert)

        conn.commit()
        print(
            f"\n¡Carga completada! Se insertaron {len(records_to_insert)} registros de congestión en la tabla 'amenazas'.")

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso de carga: {error}")
        if conn: conn.rollback()
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    load_congestion_data()