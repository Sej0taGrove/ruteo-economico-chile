import os
import psycopg2
import json
from dotenv import load_dotenv
import glob
from psycopg2.extras import execute_batch

def get_db_connection():
    load_dotenv()
    try:
        return psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("DB_HOST", "db"), port=os.getenv("DB_PORT", "5432")
        )
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

def main():
    conn = get_db_connection()
    if not conn: return

    try:
        with conn.cursor() as cur:
            print("Vaciando todas las tablas de amenazas...")
            cur.execute("TRUNCATE TABLE amenazas_sismos, amenazas_inundaciones, amenazas_incendios, amenazas_trafico RESTART IDENTITY;")

            # --- Carga de SISMOS ---
            sismos_path = 'amenazas/sismos/sismos.geojson'
            if os.path.exists(sismos_path):
                with open(sismos_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = [
                        (
                            p.get('mag'), p.get('profundidad_km'), p.get('place'), p.get('time'),
                            p.get('fecha_legible'), p.get('nivel_alerta'), p.get('url'), json.dumps(f['geometry'])
                        ) for f in data.get('features', []) if (p := f.get('properties'))
                    ]
                    if records:
                        query = "INSERT INTO amenazas_sismos (magnitud, profundidad_km, lugar, timestamp_utc, fecha_legible, nivel_alerta, url_detalle, geom) VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));"
                        execute_batch(cur, query, records)
                        print(f"-> Se insertaron {len(records)} registros de sismos.")

            # --- Carga de INCENDIOS ---
            incendios_path = 'amenazas/incendios/incendios.geojson'
            if os.path.exists(incendios_path):
                with open(incendios_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = [
                        (
                            p.get('titulo'), p.get('descripcion'), p.get('fecha_inicio'),
                            p.get('url_detalle'), json.dumps(f['geometry'])
                        ) for f in data.get('features', []) if (p := f.get('properties'))
                    ]
                    if records:
                        query = "INSERT INTO amenazas_incendios (titulo, descripcion, fecha_inicio, url_detalle, geom) VALUES (%s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));"
                        execute_batch(cur, query, records)
                        print(f"-> Se insertaron {len(records)} registros de incendios.")

            # --- Carga de INUNDACIONES ---
            inundaciones_path = 'amenazas/inundaciones/inundaciones.geojson'
            if os.path.exists(inundaciones_path):
                with open(inundaciones_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = [
                         (
                            p.get('estacion'), p.get('rio'), p.get('region'), p.get('nivel_alerta'),
                            p.get('estado'), p.get('caudal_actual'), p.get('timestamp'), json.dumps(f['geometry'])
                        ) for f in data.get('features', []) if (p := f.get('properties'))
                    ]
                    if records:
                        query = "INSERT INTO amenazas_inundaciones (estacion, rio, region, nivel_alerta, estado, caudal_actual, timestamp, geom) VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));"
                        execute_batch(cur, query, records)
                        print(f"-> Se insertaron {len(records)} registros de inundaciones.")

            # --- Carga de CONGESTIÓN ---
            congestion_files = glob.glob('amenazas/congestion/congestion_metadata_*.json')
            if congestion_files:
                with open(congestion_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    records = []
                    for item in data.get('congestion_data', []):
                        retraso = (item.get('tiempo_con_trafico_seg', 0) - item.get('tiempo_sin_trafico_seg', 0)) / 60.0
                        records.append((
                            f"Segmento ID {item['arista_id']}",
                            item.get('tiempo_sin_trafico_seg') / 60.0 if item.get('tiempo_sin_trafico_seg') else None,
                            item.get('tiempo_con_trafico_seg') / 60.0 if item.get('tiempo_con_trafico_seg') else None,
                            retraso,
                            item.get('factor_congestion'),
                            'rojo' if item.get('factor_congestion', 1) > 1.5 else ('amarillo' if item.get('factor_congestion', 1) > 1.2 else 'verde'),
                            item.get('factor_congestion'),
                            item.get('fecha_medicion'),
                            item.get('geom')
                        ))
                    if records:
                        query = "INSERT INTO amenazas_trafico (nombre_segmento, duracion_normal_min, duracion_con_trafico_min, retraso_min, indice_congestion, nivel_alerta, factor_costo_adicional, timestamp, geom) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326));"
                        execute_batch(cur, query, records)
                        print(f"-> Se insertaron {len(records)} registros de congestión.")

        conn.commit()
        print("\n¡Carga de todas las amenazas completada!")

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso de carga de amenazas: {error}")
        if conn: conn.rollback()
    finally:
        if conn: conn.close()
        print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    main()