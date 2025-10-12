import json
import os
import psycopg2
from dotenv import load_dotenv

"""
Arreglen la data que se obtiene, por que corri extract combustible y genero un json vacio, el json guardenlo en esta misma carpeta
"""

def load_combustibles_data():
    """
    Lee el archivo JSON de estaciones de servicio y carga sus datos
    en la base de datos PostgreSQL.
    """
    load_dotenv()
    conn = None
    cur = None

    try:
        # 1. Conectar a la base de datos
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        print("Conexión a la base de datos para combustibles exitosa.")

        # 2. Leer el archivo JSON
        with open('combustible_metadata_2025-10-11.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 3. Iterar y cargar los datos
        estaciones_insertadas = 0
        precios_insertados = 0

        for estacion in data['estaciones']:
            # Ignorar estaciones sin datos de ubicación, ya que no sirven para el ruteo
            if estacion.get('latitud') is None or estacion.get('longitud') is None:
                continue

            # --- Insertar en la tabla 'estaciones_servicio' ---
            # Se usa ST_MakePoint para crear un punto geográfico a partir de latitud y longitud.
            # PostGIS espera (longitud, latitud).
            insert_station_query = """
                                   INSERT INTO estaciones_servicio (id_estacion_cne, nombre, marca, direccion, comuna, \
                                                                    region, horario, ubicacion) \
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, \
                                           ST_SetSRID(ST_MakePoint(%s, %s), 4326)) RETURNING id; \
                                   """

            try:
                cur.execute(insert_station_query, (
                    estacion.get('id_estacion'),
                    estacion.get('nombre'),
                    estacion.get('marca'),
                    estacion.get('direccion'),
                    estacion.get('comuna'),
                    estacion.get('region'),
                    estacion.get('horario'),
                    estacion.get('longitud'),
                    estacion.get('latitud')
                ))

                estacion_id_db = cur.fetchone()[0]
                estaciones_insertadas += 1

                # --- Insertar en la tabla 'precios_combustibles' ---
                for tipo_combustible, precio in estacion.get('combustibles', {}).items():
                    # Solo insertamos si el precio es un número válido
                    if isinstance(precio, (int, float)):
                        cur.execute(
                            """
                            INSERT INTO precios_combustibles (estacion_id, tipo_combustible, precio, fecha_actualizacion)
                            VALUES (%s, %s, %s, %s);
                            """,
                            (estacion_id_db, tipo_combustible, int(precio), estacion.get('fecha_actualizacion'))
                        )
                        precios_insertados += 1

            except psycopg2.Error as e:
                print(f"Error al insertar estación {estacion.get('id_estacion')}: {e}")
                conn.rollback()  # Revertir la inserción de esta estación específica

        # 4. Guardar los cambios en la base de datos
        conn.commit()
        print(
            f"\n¡Carga completada! Se insertaron {estaciones_insertadas} estaciones y {precios_insertados} precios de combustibles.")

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso: {error}")
        if conn:
            conn.rollback()
    finally:
        # 5. Cerrar la conexión
        if conn:
            cur.close()
            conn.close()
            print("Conexión a la base de datos de combustibles cerrada.")


if __name__ == "__main__":
    # Vaciar las tablas antes de cargar para evitar duplicados en cada ejecución
    # Esto es opcional y útil para desarrollo. Comentar en producción.
    load_dotenv()
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        print("Vaciando tablas de combustibles antes de la carga...")
        cur.execute("TRUNCATE TABLE precios_combustibles, estaciones_servicio RESTART IDENTITY CASCADE;")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"No se pudieron vaciar las tablas: {e}")

    # Ejecutar la función de carga principal
    load_combustibles_data()