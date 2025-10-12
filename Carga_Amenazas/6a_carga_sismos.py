#!/usr/bin/env python3
"""
Script para cargar sismos desde GeoJSON a la base de datos PostGIS
Basado en datos de USGS Earthquake API
"""

import psycopg2
import json
import os
from datetime import datetime

# Configuración de conexión
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'ruteo_economico'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

def conectar_db():
    """Establece conexión con PostgreSQL/PostGIS"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos: {e}")
        exit(1)

def verificar_tabla_existe(cursor):
    """Verifica si la tabla amenazas_sismos existe"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'amenazas_sismos'
        );
    """)
    return cursor.fetchone()[0]

def limpiar_tabla_sismos(cursor):
    """Limpia registros existentes antes de cargar nuevos datos"""
    cursor.execute("DELETE FROM amenazas_sismos;")
    registros_eliminados = cursor.rowcount
    print(f"[OK] Tabla amenazas_sismos limpiada ({registros_eliminados} registros eliminados)")

def cargar_sismos_desde_json(cursor, json_file):
    """Carga los sismos desde el archivo GeoJSON"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    
    if not features:
        print("[WARN] No se encontraron sismos en el archivo JSON")
        return 0
    
    sql = """
    INSERT INTO amenazas_sismos 
    (tipo_amenaza, magnitud, profundidad_km, lugar, timestamp_utc, 
     fecha_legible, nivel_alerta, url_detalle, fuente, geom)
    VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
    """
    
    count = 0
    errores = 0
    
    for feature in features:
        try:
            props = feature['properties']
            coords = feature['geometry']['coordinates']
            
            # Convertir timestamp Unix a datetime si existe
            fecha_legible = None
            if props.get('timestamp_utc'):
                try:
                    fecha_legible = datetime.fromtimestamp(props['timestamp_utc'] / 1000)
                except:
                    # Si falla, intentar parsear desde fecha_legible
                    fecha_str = props.get('fecha_legible', '')
                    if fecha_str:
                        fecha_legible = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S UTC')
            
            valores = (
                props.get('tipo_amenaza', 'sismo'),
                props.get('magnitud'),
                props.get('profundidad_km'),
                props.get('lugar'),
                props.get('timestamp_utc'),
                fecha_legible,
                props.get('nivel_alerta'),
                props.get('url_detalle'),
                props.get('fuente', 'USGS'),
                coords[0],  # longitud
                coords[1]   # latitud
            )
            
            cursor.execute(sql, valores)
            count += 1
            
        except Exception as e:
            errores += 1
            print(f"[WARN] Error procesando sismo: {e}")
            continue
    
    print(f"[OK] Se insertaron {count} sismos en la base de datos")
    if errores > 0:
        print(f"[WARN] {errores} sismos no pudieron ser procesados")
    
    return count

def main():
    print("="*60)
    print("CARGA DE SISMOS A POSTGIS")
    print("="*60)
    
    json_file = '../Amenazas_JSON/sismos.geojson'
    
    if not os.path.exists(json_file):
        print(f"[ERROR] Archivo no encontrado: {json_file}")
        print(f"[INFO] Ejecute primero: python 3a_sismos_usgs.py")
        exit(1)
    
    conn = conectar_db()
    cursor = conn.cursor()
    
    try:
        # Verificar que la tabla existe
        if not verificar_tabla_existe(cursor):
            print("[ERROR] La tabla amenazas_sismos no existe")
            print("[INFO] Ejecute primero: psql -U postgres -d ruteo_economico -f schema.sql")
            exit(1)
        
        limpiar_tabla_sismos(cursor)
        registros = cargar_sismos_desde_json(cursor, json_file)
        
        conn.commit()
        print(f"\n[COMPLETADO] Carga de sismos finalizada exitosamente")
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