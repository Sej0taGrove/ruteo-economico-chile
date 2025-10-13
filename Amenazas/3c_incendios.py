#!/usr/bin/env python3
"""
Script para extraer incendios forestales de NASA EONET y transformarlos a GeoJSON
"""

import requests
import json
from datetime import datetime
import sys
import os

def extraer_incendios_nasa():
    """
    Extrae incendios forestales activos de la API de NASA EONET
    """
    
    url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    
    params = {
        'status': 'open',
        'category': 'wildfires',
        'limit': 100
    }
    
    print("[INFO] Consultando NASA EONET API...")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Filtrar incendios en Chile y transformar
        incendios_transformados = transformar_incendios_chile(data)
        
        print(f"[OK] Se obtuvieron {len(incendios_transformados['features'])} incendios en Chile")
        
        return incendios_transformados
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error al consultar NASA EONET: {e}")
        sys.exit(1)

def transformar_incendios_chile(data_nasa):
    """
    Filtra incendios en Chile y transforma al formato GeoJSON del proyecto
    """
    
    features_transformadas = []
    
    for event in data_nasa.get('events', []):
        # Verificar si hay geometrías disponibles
        geometries = event.get('geometry', [])
        if not geometries:
            continue
        
        # Usar la geometría más reciente
        latest_geom = geometries[-1]
        coords = latest_geom.get('coordinates', [])
        
        if len(coords) < 2:
            continue
        
        lon, lat = coords[0], coords[1]
        
        # Filtrar solo incendios en Chile
        # Chile: lat -56 a -17, lon -76 a -66
        if not (-56 <= lat <= -17 and -76 <= lon <= -66):
            continue
        
        # Crear feature GeoJSON
        feature_transformada = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat]
            },
            'properties': {
                'tipo_amenaza': 'incendio_forestal',
                'titulo': event.get('title'),
                'descripcion': event.get('description', 'Incendio forestal activo'),
                'fecha_inicio': latest_geom.get('date'),
                'nivel_alerta': 'rojo',  # Incendios activos son alerta roja
                'categoria': 'wildfires',
                'fuente': 'NASA EONET',
                'url_detalle': event.get('link', '')
            }
        }
        
        features_transformadas.append(feature_transformada)
    
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'generado': datetime.utcnow().isoformat() + 'Z',
            'fuente': 'NASA EONET Wildfires API',
            'total': len(features_transformadas)
        },
        'features': features_transformadas
    }

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
    print("EXTRACCIÓN DE INCENDIOS FORESTALES - NASA EONET")
    print("="*60)
    
    incendios = extraer_incendios_nasa()
    guardar_json(incendios, 'incendios.geojson')
    
    print("\n[COMPLETADO] Extracción de incendios finalizada")