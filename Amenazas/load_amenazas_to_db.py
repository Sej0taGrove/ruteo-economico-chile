#!/usr/bin/env python3
"""
Script para cargar datos de amenazas (sismos, inundaciones, incendios, tráfico) 
desde archivos GeoJSON a la base de datos PostgreSQL/PostGIS
"""

import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
AMENAZAS_JSON_DIR = BASE_DIR / "Amenazas_JSON"


def get_db_connection():
    """
    Establece conexión con la base de datos PostgreSQL
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'ruteo_db'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error al conectar a la base de datos: {e}")
        sys.exit(1)


def limpiar_tabla(cursor, tabla: str) -> None:
    """
    Limpia los datos antiguos de una tabla de amenazas
    """
    try:
        cursor.execute(f"DELETE FROM {tabla}")
        logger.info(f"Tabla {tabla} limpiada")
    except psycopg2.Error as e:
        logger.error(f"Error al limpiar tabla {tabla}: {e}")
        raise


def cargar_sismos(cursor, filepath: Path) -> int:
    """
    Carga datos de sismos desde archivo GeoJSON
    """
    logger.info(f"Cargando sismos desde {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    
    if not features:
        logger.warning("No se encontraron sismos para cargar")
        return 0
    
    # Limpiar tabla antes de cargar
    limpiar_tabla(cursor, 'amenazas_sismos')
    
    query = """
        INSERT INTO amenazas_sismos (
            tipo_amenaza, magnitud, profundidad_km, lugar, 
            timestamp_utc, fecha_legible, nivel_alerta, 
            url_detalle, fuente, geom
        ) VALUES (
            %(tipo_amenaza)s, %(magnitud)s, %(profundidad_km)s, %(lugar)s,
            %(timestamp_utc)s, %(fecha_legible)s, %(nivel_alerta)s,
            %(url_detalle)s, %(fuente)s, 
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)
        )
    """
    
    records = []
    for feature in features:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        # Convertir timestamp a fecha legible si existe
        fecha_legible = None
        if props.get('timestamp_utc'):
            try:
                fecha_legible = datetime.fromtimestamp(
                    props['timestamp_utc'] / 1000, 
                    tz=timezone.utc
                )
            except (ValueError, TypeError):
                fecha_legible = None
        
        record = {
            'tipo_amenaza': props.get('tipo_amenaza', 'sismo'),
            'magnitud': props.get('magnitud'),
            'profundidad_km': props.get('profundidad_km'),
            'lugar': props.get('lugar'),
            'timestamp_utc': props.get('timestamp_utc'),
            'fecha_legible': fecha_legible,
            'nivel_alerta': props.get('nivel_alerta'),
            'url_detalle': props.get('url_detalle'),
            'fuente': props.get('fuente', 'USGS'),
            'lon': coords[0],
            'lat': coords[1]
        }
        records.append(record)
    
    execute_batch(cursor, query, records)
    logger.info(f"✓ {len(records)} sismos cargados exitosamente")
    return len(records)


def cargar_inundaciones(cursor, filepath: Path) -> int:
    """
    Carga datos de inundaciones desde archivo GeoJSON
    """
    logger.info(f"Cargando inundaciones desde {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    
    if not features:
        logger.warning("No se encontraron alertas de inundación para cargar")
        return 0
    
    # Limpiar tabla antes de cargar
    limpiar_tabla(cursor, 'amenazas_inundaciones')
    
    query = """
        INSERT INTO amenazas_inundaciones (
            tipo_amenaza, estacion, rio, region, nivel_alerta,
            estado, caudal_actual, timestamp, fuente, geom
        ) VALUES (
            %(tipo_amenaza)s, %(estacion)s, %(rio)s, %(region)s, %(nivel_alerta)s,
            %(estado)s, %(caudal_actual)s, %(timestamp)s, %(fuente)s,
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)
        )
    """
    
    records = []
    for feature in features:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        # Convertir timestamp si es string ISO
        timestamp = props.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                timestamp = None
        
        record = {
            'tipo_amenaza': props.get('tipo_amenaza', 'inundacion'),
            'estacion': props.get('estacion'),
            'rio': props.get('rio'),
            'region': props.get('region'),
            'nivel_alerta': props.get('nivel_alerta'),
            'estado': props.get('estado'),
            'caudal_actual': props.get('caudal_actual'),
            'timestamp': timestamp,
            'fuente': props.get('fuente', 'DGA MOP'),
            'lon': coords[0],
            'lat': coords[1]
        }
        records.append(record)
    
    execute_batch(cursor, query, records)
    logger.info(f"✓ {len(records)} alertas de inundación cargadas exitosamente")
    return len(records)


def cargar_incendios(cursor, filepath: Path) -> int:
    """
    Carga datos de incendios forestales desde archivo GeoJSON
    """
    logger.info(f"Cargando incendios desde {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    
    if not features:
        logger.warning("No se encontraron incendios para cargar")
        return 0
    
    # Limpiar tabla antes de cargar
    limpiar_tabla(cursor, 'amenazas_incendios')
    
    query = """
        INSERT INTO amenazas_incendios (
            tipo_amenaza, titulo, descripcion, fecha_inicio,
            nivel_alerta, categoria, url_detalle, fuente, geom
        ) VALUES (
            %(tipo_amenaza)s, %(titulo)s, %(descripcion)s, %(fecha_inicio)s,
            %(nivel_alerta)s, %(categoria)s, %(url_detalle)s, %(fuente)s,
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)
        )
    """
    
    records = []
    for feature in features:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        # Convertir fecha_inicio si es string
        fecha_inicio = props.get('fecha_inicio')
        if isinstance(fecha_inicio, str):
            try:
                fecha_inicio = datetime.fromisoformat(fecha_inicio.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                fecha_inicio = None
        
        record = {
            'tipo_amenaza': props.get('tipo_amenaza', 'incendio_forestal'),
            'titulo': props.get('titulo'),
            'descripcion': props.get('descripcion'),
            'fecha_inicio': fecha_inicio,
            'nivel_alerta': props.get('nivel_alerta', 'rojo'),
            'categoria': props.get('categoria', 'wildfires'),
            'url_detalle': props.get('url_detalle'),
            'fuente': props.get('fuente', 'NASA EONET'),
            'lon': coords[0],
            'lat': coords[1]
        }
        records.append(record)
    
    execute_batch(cursor, query, records)
    logger.info(f"✓ {len(records)} incendios forestales cargados exitosamente")
    return len(records)


def cargar_trafico(cursor, filepath: Path) -> int:
    """
    Carga datos de tráfico vehicular desde archivo GeoJSON
    """
    logger.info(f"Cargando datos de tráfico desde {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    
    if not features:
        logger.warning("No se encontraron datos de tráfico para cargar")
        return 0
    
    # Limpiar tabla antes de cargar
    limpiar_tabla(cursor, 'amenazas_trafico')
    
    query = """
        INSERT INTO amenazas_trafico (
            tipo_amenaza, nombre_segmento, distancia_km,
            duracion_normal_min, duracion_con_trafico_min, retraso_min,
            indice_congestion, nivel_alerta, factor_costo_adicional,
            descripcion, timestamp, fuente, geom
        ) VALUES (
            %(tipo_amenaza)s, %(nombre_segmento)s, %(distancia_km)s,
            %(duracion_normal_min)s, %(duracion_con_trafico_min)s, %(retraso_min)s,
            %(indice_congestion)s, %(nivel_alerta)s, %(factor_costo_adicional)s,
            %(descripcion)s, %(timestamp)s, %(fuente)s,
            ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)
        )
    """
    
    records = []
    for feature in features:
        props = feature['properties']
        coords = feature['geometry']['coordinates']
        
        # Convertir timestamp si es string
        timestamp = props.get('timestamp')
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                timestamp = None
        
        record = {
            'tipo_amenaza': props.get('tipo_amenaza', 'congestion_vehicular'),
            'nombre_segmento': props.get('nombre_segmento'),
            'distancia_km': props.get('distancia_km'),
            'duracion_normal_min': props.get('duracion_normal_min'),
            'duracion_con_trafico_min': props.get('duracion_con_trafico_min'),
            'retraso_min': props.get('retraso_min'),
            'indice_congestion': props.get('indice_congestion'),
            'nivel_alerta': props.get('nivel_alerta'),
            'factor_costo_adicional': props.get('factor_costo_adicional'),
            'descripcion': props.get('descripcion'),
            'timestamp': timestamp,
            'fuente': props.get('fuente', 'Google Maps Directions API'),
            'lon': coords[0],
            'lat': coords[1]
        }
        records.append(record)
    
    execute_batch(cursor, query, records)
    logger.info(f"✓ {len(records)} segmentos de tráfico cargados exitosamente")
    return len(records)


def verificar_archivos() -> Dict[str, Path]:
    """
    Verifica que existan los archivos GeoJSON de amenazas
    """
    archivos = {
        'sismos': AMENAZAS_JSON_DIR / 'sismos.geojson',
        'inundaciones': AMENAZAS_JSON_DIR / 'inundaciones.geojson',
        'incendios': AMENAZAS_JSON_DIR / 'incendios.geojson',
        'trafico': AMENAZAS_JSON_DIR / 'trafico_vehicular.geojson'
    }
    
    archivos_encontrados = {}
    archivos_faltantes = []
    
    for nombre, path in archivos.items():
        if path.exists():
            archivos_encontrados[nombre] = path
            logger.info(f"✓ Encontrado: {path.name}")
        else:
            archivos_faltantes.append(path.name)
            logger.warning(f"✗ No encontrado: {path.name}")
    
    if archivos_faltantes:
        logger.warning(f"Archivos faltantes: {', '.join(archivos_faltantes)}")
        logger.warning("Se cargarán solo los archivos disponibles")
    
    return archivos_encontrados


def main():
    """
    Función principal que coordina la carga de todas las amenazas
    """
    logger.info("=" * 70)
    logger.info("CARGA DE DATOS DE AMENAZAS A LA BASE DE DATOS")
    logger.info("=" * 70)
    
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar archivos disponibles
    logger.info("\n[1/3] Verificando archivos GeoJSON...")
    archivos = verificar_archivos()
    
    if not archivos:
        logger.error("No se encontraron archivos GeoJSON para cargar")
        logger.error("Ejecute primero los scripts de extracción de amenazas")
        sys.exit(1)
    
    # Conectar a la base de datos
    logger.info("\n[2/3] Conectando a la base de datos...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    logger.info("✓ Conexión establecida")
    
    # Cargar datos
    logger.info("\n[3/3] Cargando datos de amenazas...")
    total_registros = 0
    
    try:
        # Cargar cada tipo de amenaza si el archivo existe
        if 'sismos' in archivos:
            total_registros += cargar_sismos(cursor, archivos['sismos'])
        
        if 'inundaciones' in archivos:
            total_registros += cargar_inundaciones(cursor, archivos['inundaciones'])
        
        if 'incendios' in archivos:
            total_registros += cargar_incendios(cursor, archivos['incendios'])
        
        if 'trafico' in archivos:
            total_registros += cargar_trafico(cursor, archivos['trafico'])
        
        # Confirmar cambios
        conn.commit()
        
        logger.info("\n" + "=" * 70)
        logger.info(f"✓ CARGA COMPLETADA EXITOSAMENTE")
        logger.info(f"✓ Total de registros cargados: {total_registros}")
        logger.info("=" * 70)
        
    except Exception as e:
        conn.rollback()
        logger.error(f"\n✗ Error durante la carga: {e}")
        logger.error("Se realizó rollback de los cambios")
        sys.exit(1)
    
    finally:
        cursor.close()
        conn.close()
        logger.info("Conexión cerrada")


if __name__ == '__main__':
    main()