#!/usr/bin/env python3
"""
Script para extraer alertas de inundaciones de DGA y transformarlas a GeoJSON
"""

import requests
import json
from datetime import datetime
import sys
import os

def extraer_alertas_dga():
    """
    Extrae alertas hidrológicas del servicio MapServer de la DGA
    """
    
    url = "https://rest-sit.mop.gob.cl/arcgis/rest/services/DGA/ALERTAS/MapServer/0/query"
    
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'json',
        'returnGeometry': 'true'
    }
    
    print("[INFO] Consultando DGA ALERTAS MapServer...")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Transformar a GeoJSON
        alertas_transformadas = transformar_alertas_dga(data)
        
        print(f"[OK] Se obtuvieron {len(alertas_transformadas['features'])} alertas")
        
        return alertas_transformadas
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error al consultar DGA: {e}")
        sys.exit(1)

def transformar_alertas_dga(data_dga):
    """
    Transforma la respuesta de DGA ArcGIS al formato GeoJSON del proyecto
    """
    
    features_transformadas = []
    
    for feature in data_dga.get('features', []):
        attrs = feature.get('attributes', {})
        geom = feature.get('geometry', {})
        
        # Convertir geometría de ArcGIS a GeoJSON
        geometry_geojson = {
            'type': 'Point',
            'coordinates': [geom.get('x'), geom.get('y')]
        }
        
        # Extraer nivel de alerta
        nivel_alerta = determinar_nivel_alerta(attrs)
        
        feature_transformada = {
            'type': 'Feature',
            'geometry': geometry_geojson,
            'properties': {
                'tipo_amenaza': 'inundacion',
                'estacion': attrs.get('NOMBRE_ESTACION') or attrs.get('nombre_estacion'),
                'rio': attrs.get('RIO') or attrs.get('rio'),
                'region': attrs.get('REGION') or attrs.get('region'),
                'nivel_alerta': nivel_alerta,
                'estado': attrs.get('ESTADO_ALERTA') or attrs.get('estado'),
                'caudal_actual': attrs.get('CAUDAL') or attrs.get('caudal'),
                'timestamp': attrs.get('FECHA_REGISTRO') or attrs.get('fecha'),
                'fuente': 'DGA MOP'
            }
        }
        
        features_transformadas.append(feature_transformada)
    
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'generado': datetime.utcnow().isoformat() + 'Z',
            'fuente': 'DGA ALERTAS MapServer',
            'total': len(features_transformadas)
        },
        'features': features_transformadas
    }

def determinar_nivel_alerta(attrs):
    """
    Determina nivel de alerta basado en los atributos disponibles
    """
    estado = str(attrs.get('ESTADO_ALERTA', '')).lower()
    
    if 'rojo' in estado or 'crítico' in estado:
        return 'rojo'
    elif 'amarillo' in estado or 'moderado' in estado:
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
    print("EXTRACCIÓN DE ALERTAS DE INUNDACIONES - DGA")
    print("="*60)
    
    alertas = extraer_alertas_dga()
    guardar_json(alertas, 'inundaciones.geojson')
    
    print("\n[COMPLETADO] Extracción de alertas finalizada")