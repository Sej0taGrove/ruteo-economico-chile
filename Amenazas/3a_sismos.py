#!/usr/bin/env python3
"""
Script para extraer sismos de USGS y transformarlos a GeoJSON
Filtra sismos relevantes para Chile (magnitud >= 5.0)
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import os

def extraer_sismos_usgs():
    """
    Extrae sismos de la API de USGS para las últimas 24 horas
    Filtra por magnitud >= 5.0 y proximidad a Chile
    """
    
    # Configurar fechas (últimas 24 horas)
    fecha_fin = datetime.utcnow()
    fecha_inicio = fecha_fin - timedelta(days=1)
    
    # Formato requerido por USGS: YYYY-MM-DD
    start_time = fecha_inicio.strftime('%Y-%m-%d')
    
    # Endpoint USGS
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    params = {
        'format': 'geojson',
        'starttime': start_time,
        'minmagnitude': 5.0,
        'minlatitude': -56.0,  # Límite sur de Chile
        'maxlatitude': -17.0,  # Límite norte de Chile
        'minlongitude': -76.0, # Límite oeste
        'maxlongitude': -66.0  # Límite este
    }
    
    print(f"[INFO] Consultando USGS API desde {start_time}...")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Transformar a formato específico del proyecto
        sismos_transformados = transformar_sismos(data)
        
        print(f"[OK] Se obtuvieron {len(sismos_transformados['features'])} sismos")
        
        return sismos_transformados
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error al consultar USGS: {e}")
        sys.exit(1)

def transformar_sismos(data_usgs):
    """
    Transforma la respuesta de USGS al formato del proyecto
    """
    
    features_transformadas = []
    
    for feature in data_usgs.get('features', []):
        props = feature['properties']
        geom = feature['geometry']
        
        # Extraer datos relevantes
        feature_transformada = {
            'type': 'Feature',
            'geometry': geom,
            'properties': {
                'tipo_amenaza': 'sismo',
                'magnitud': props.get('mag'),
                'profundidad_km': geom['coordinates'][2] if len(geom['coordinates']) > 2 else None,
                'lugar': props.get('place'),
                'timestamp_utc': props.get('time'),
                'fecha_legible': datetime.fromtimestamp(props.get('time', 0)/1000).strftime('%Y-%m-%d %H:%M:%S UTC'),
                'nivel_alerta': calcular_nivel_alerta_sismo(props.get('mag')),
                'url_detalle': props.get('url'),
                'fuente': 'USGS'
            }
        }
        
        features_transformadas.append(feature_transformada)
    
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'generado': datetime.utcnow().isoformat() + 'Z',
            'fuente': 'USGS Earthquake API',
            'total': len(features_transformadas)
        },
        'features': features_transformadas
    }

def calcular_nivel_alerta_sismo(magnitud):
    """
    Determina el nivel de alerta según la magnitud
    """
    if magnitud >= 7.0:
        return 'rojo'
    elif magnitud >= 6.0:
        return 'amarillo'
    else:
        return 'verde'

def guardar_json(data, filename):
    """
    Guarda los datos en archivo JSON
    """
    output_dir = '../Amenazas_JSON'
    os.makedirs(output_dir, exist_ok=True)
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Archivo guardado: {filepath}")

if __name__ == '__main__':
    print("="*60)
    print("EXTRACCIÓN DE SISMOS - USGS")
    print("="*60)
    
    sismos = extraer_sismos_usgs()
    guardar_json(sismos, 'sismos.geojson')
    
    print("\n[COMPLETADO] Extracción de sismos finalizada")