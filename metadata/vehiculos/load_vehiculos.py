# Archivo: Metadata/vehiculos/load_vehiculos.py
import os
import psycopg2
from dotenv import load_dotenv
import json


def load_data_to_db():
    load_dotenv()
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(SCRIPT_DIR, 'metadata_vehiculos.json')
    # ... (el resto de tu función load_data_to_db es idéntica) ...
    # ... (Cópiala y pégala aquí, asegurándote de que lea desde `json_path`)
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("DB_HOST", "localhost")
        )
        cur = conn.cursor()

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cur.execute("TRUNCATE TABLE vehiculos RESTART IDENTITY CASCADE;")

        for vehiculo in data:
            specs = vehiculo.get('especificaciones_clave', {})
            insert_query = """
                           INSERT INTO vehiculos (modelo_base, version, consumo_mixto_kml, consumo_urbano_kml,
                                                  consumo_extraurbano_kml, capacidad_estanque_litros, motor_litros,
                                                  transmision, traccion)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s); \
                           """
            values = (
                vehiculo.get('modelo_base'), vehiculo.get('version'), specs.get('consumo_mixto_kml'),
                specs.get('consumo_urbano_kml'), specs.get('consumo_extraurbano_kml'),
                specs.get('capacidad_estanque_litros'), specs.get('motor_litros'),
                specs.get('transmision'), specs.get('traccion')
            )
            cur.execute(insert_query, values)

        conn.commit()
        print(f"¡Carga completada! Se insertaron {len(data)} registros en la tabla 'vehiculos'.")

    except (Exception, psycopg2.Error) as error:
        print(f"Error durante la carga a la BD: {error}")
    finally:
        if conn: cur.close(); conn.close()


if __name__ == "__main__":
    load_data_to_db()