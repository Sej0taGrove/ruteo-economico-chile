import os
import psycopg2
import json
from dotenv import load_dotenv
import glob


def get_db_connection():
    """Establece la conexión con la base de datos."""
    load_dotenv()
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None


def process_feature(feature):
    """
    Procesa un 'feature' de GeoJSON y lo adapta para la inserción en la BD.
    Devuelve una tupla con los valores a insertar.
    """
    properties = feature.get('properties', {})
    geom = feature.get('geometry')

    tipo_amenaza = properties.get('tipo_amenaza')
    valor = 0
    detalles = {}

    # Mapeo específico por tipo de amenaza
    if tipo_amenaza == 'congestion':
        valor = properties.get('factor_congestion')
        fecha = properties.get('fecha_medicion')
        detalles = {
            'tiempo_con_trafico_seg': properties.get('tiempo_con_trafico_seg'),
            'tiempo_sin_trafico_seg': properties.get('tiempo_sin_trafico_seg')
        }
    elif tipo_amenaza == 'incendio_forestal':
        valor = 1  # Representa la presencia del incendio
        fecha = properties.get('fecha_inicio')
        detalles = {
            'titulo': properties.get('titulo'),
            'fuente': properties.get('fuente'),
            'url_detalle': properties.get('url_detalle')
        }
    elif tipo_amenaza == 'inundacion':
        valor = {'rojo': 3, 'amarillo': 2, 'verde': 1}.get(properties.get('nivel_alerta'), 0)
        fecha = properties.get('timestamp')
        detalles = {
            'estacion': properties.get('estacion'),
            'rio': properties.get('rio'),
            'estado': properties.get('estado'),
            'caudal_actual': properties.get('caudal_actual')
        }
    elif tipo_amenaza == 'sismo':
        valor = properties.get('magnitud')
        fecha = properties.get('fecha_legible')
        detalles = {
            'lugar': properties.get('lugar'),
            'profundidad_km': properties.get('profundidad_km'),
            'url_detalle': properties.get('url_detalle')
        }
    else:
        return None  # Ignorar si el tipo de amenaza no es conocido

    # Convertir la geometría a string para la inserción
    geom_str = json.dumps(geom)

    return (
        properties.get('arista_id'),  # Puede ser None para sismos, incendios, etc.
        tipo_amenaza,
        valor,
        fecha,
        geom_str,
        json.dumps(detalles)  # Convertir el diccionario de detalles a un string JSONB
    )


def main():
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            print("Vaciando la tabla de amenazas para una carga limpia...")
            cur.execute("TRUNCATE TABLE amenazas RESTART IDENTITY;")

            # Buscar todos los archivos .geojson en todas las subcarpetas de 'amenazas'
            amenazas_dir = os.path.dirname(os.path.realpath(__file__))
            geojson_files = glob.glob(os.path.join(amenazas_dir, '**', '*.geojson'), recursive=True)
            # También busca los json de congestión
            geojson_files.extend(glob.glob(os.path.join(amenazas_dir, '**', 'congestion_*.json'), recursive=True))

            if not geojson_files:
                print("No se encontraron archivos de amenazas (.geojson o congestion_*.json) para cargar.")
                return

            records_to_insert = []
            for file_path in geojson_files:
                print(f"Procesando archivo: {os.path.basename(file_path)}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # La estructura puede ser una 'FeatureCollection' o una lista de 'features'
                    features = data.get('features', [])
                    if not features and 'congestion_data' in data:  # Caso especial para tu script de congestión
                        features = data['congestion_data']

                    for feature in features:
                        record = process_feature(feature)
                        if record:
                            records_to_insert.append(record)

            if records_to_insert:
                insert_query = """
                               INSERT INTO amenazas (arista_id, tipo_amenaza, valor, fecha_medicion, geom, detalles)
                               VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326), %s); \
                               """
                # Usar execute_batch para eficiencia
                psycopg2.extras.execute_batch(cur, insert_query, records_to_insert)
                print(f"\n¡Carga completada! Se insertaron {len(records_to_insert)} registros en la tabla 'amenazas'.")

        conn.commit()

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso de carga: {error}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
        print("Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    main()