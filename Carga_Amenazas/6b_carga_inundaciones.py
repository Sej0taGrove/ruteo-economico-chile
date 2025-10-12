#!/usr/bin/env python3
"""
Script para cargar alertas de inundaciones desde GeoJSON a PostGIS
Basado en datos de DGA ALERTAS MapServer
"""

import psycopg2
import json
import os
from datetime import datetime

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'ruteo_economico'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

def conectar_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        exit(1)

def verificar_tabla_existe(cursor):
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'amenazas_inundaciones'
        );
    """)
    return cursor.fetchone()[0]

def limpiar_tabla_inundaciones(cursor):
    cursor.execute("DELETE FROM amenazas_inundaciones;")
    registros_eliminados = cursor.rowcount
    print(f"[OK] Tabla amenazas_inundaciones limpiada ({registros_eliminados} registros eliminados)")

def cargar_inundaciones_desde_json(cursor, json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    
    if not features:
        print("[WARN] No se encontraron alertas de inundación en el archivo JSON")
        return 0
    
    sql = """
    INSERT INTO amenazas_inundaciones 
    (tipo_amenaza, estacion, rio, region, nivel_alerta, estado, 
     caudal_actual, timestamp, fuente, geom)
    VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
    """
    
    count = 0
    errores = 0
    
    for feature in features:
        try:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            
            # Parsear timestamp si está como string
            timestamp_val = None
            if props.get('timestamp'):
                timestamp_str = props['timestamp']
                if isinstance(timestamp_str, str):
                    try:
                        timestamp_val = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        timestamp_val = None
                else:
                    timestamp_val = timestamp_str
            
            valores = (
                props.get('tipo_amenaza', 'inundacion'),
                props.get('estacion'),
                props.get('rio'),
                props.get('region'),
                props.get('nivel_alerta'),
                props.get('estado'),
                props.get('caudal_actual'),
                timestamp_val,
                props.get('fuente', 'DGA MOP'),
                coords[0],
                coords[1]
            )
            
            cursor.execute(sql, valores)
            count += 1
            
        except Exception as e:
            errores += 1
            print(f"[WARN] Error procesando inundación: {e}")
            continue
    
    print(f"[OK] Se insertaron {count} alertas de inundaciones")
    if errores > 0:
        print(f"[WARN] {errores} alertas no pudieron ser procesadas")
    
    return count

def main():
    print("="*60)
    print("CARGA DE INUNDACIONES A POSTGIS")
    print("="*60)
    
    json_file = '../Amenazas_JSON/inundaciones.geojson'
    
    if not os.path.exists(json_file):
        print(f"[ERROR] Archivo no encontrado: {json_file}")
        print(f"[INFO] Ejecute primero: python 3b_inundaciones_dga.py")
        exit(1)
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        if not verificar_tabla_existe(cursor):
            print("[ERROR] La tabla amenazas_inundaciones no existe")
            print("[INFO] Ejecute primero: psql -U postgres -d ruteo_economico -f schema.sql")
            exit(1)
        
        limpiar_tabla_inundaciones(cursor)
        registros = cargar_inundaciones_desde_json(cursor, json_file)
        
        conn.commit()
        print(f"\n[COMPLETADO] Carga de inundaciones finalizada")
        print(f"[INFO] Total de registros cargados: {registros}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Error durante la carga: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    main()