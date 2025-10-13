# metadata/combustible/load_combustible.py
import json
import os
import psycopg2
from dotenv import load_dotenv
import glob


def find_latest_combustible_json(directory):
    """Encuentra el archivo de combustible más reciente en la carpeta."""
    # Busca archivos que coincidan con el patrón
    list_of_files = glob.glob(os.path.join(directory, 'combustible_metadata_*.json'))
    if not list_of_files:
        return None
    # Devuelve el archivo con la fecha de modificación más reciente
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def load_combustibles_data():
    """
    Lee el archivo JSON de estaciones de servicio más reciente y carga sus datos
    en la base de datos PostgreSQL.
    """
    load_dotenv()
    conn = None
    cur = None
    try:
        SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

        json_path = find_latest_combustible_json(SCRIPT_DIR)
        if not json_path:
            raise FileNotFoundError(
                f"No se encontró ningún archivo 'combustible_metadata_*.json' en '{SCRIPT_DIR}'. Ejecuta extract_combustible.py primero.")

        print(f"Cargando datos de combustibles desde: {os.path.basename(json_path)}")

        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        print("Conexión a la BD para combustibles exitosa.")

        print("Vaciando tablas de combustibles...")
        cur.execute("TRUNCATE TABLE precios_combustibles, estaciones_servicio RESTART IDENTITY CASCADE;")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        estaciones_insertadas = 0
        precios_insertados = 0
        for estacion in data.get('estaciones', []):
            if estacion.get('latitud') is None or estacion.get('longitud') is None:
                continue
            try:
                cur.execute(
                    """
                    INSERT INTO estaciones_servicio (id_estacion_cne, nombre, marca, direccion, comuna, region, horario,
                                                     ubicacion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) RETURNING id;
                    """,
                    (
                        estacion.get('id_estacion'), estacion.get('nombre'), estacion.get('marca'),
                        estacion.get('direccion'), estacion.get('comuna'), estacion.get('region'),
                        estacion.get('horario'), estacion.get('longitud'), estacion.get('latitud')
                    )
                )
                estacion_id_db = cur.fetchone()[0]
                estaciones_insertadas += 1

                for tipo_combustible, precio in estacion.get('combustibles', {}).items():
                    if isinstance(precio, (int, float)):
                        cur.execute(
                            "INSERT INTO precios_combustibles (estacion_id, tipo_combustible, precio, fecha_actualizacion) VALUES (%s, %s, %s, %s);",
                            (estacion_id_db, tipo_combustible, int(precio), estacion.get('fecha_actualizacion'))
                        )
                        precios_insertados += 1
            except (Exception, psycopg2.Error) as e:
                print(f"Error al insertar estación {estacion.get('id_estacion')}: {e}")
                conn.rollback()

        conn.commit()
        print(f"\n¡Carga completada! Se insertaron {estaciones_insertadas} estaciones y {precios_insertados} precios.")

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso: {error}")
        if conn: conn.rollback()
    finally:
        if conn:
            if cur: cur.close()
            conn.close()
            print("Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    load_combustibles_data()