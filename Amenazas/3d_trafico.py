#!/usr/bin/env python3
"""
Script para extraer información de tráfico vehicular en tiempo real
usando Google Maps Directions API con duration_in_traffic

Analiza segmentos clave de una ruta predeterminada para identificar congestión
"""

import requests
import json
from datetime import datetime
import sys
import os

# API Key de Google Maps (debe configurarse como variable de entorno)
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

# Ruta predeterminada: Santiago Centro -> Las Condes (ejemplo)
# Define segmentos críticos de la ruta a monitorear
SEGMENTOS_RUTA = [
    {
        'nombre': 'Alameda - Plaza Italia',
        'origen': (-33.4489, -70.6693),  # Santiago Centro
        'destino': (-33.4372, -70.6345)   # Plaza Italia
    },
    {
        'nombre': 'Providencia - Tobalaba',
        'origen': (-33.4372, -70.6345),   # Plaza Italia
        'destino': (-33.4258, -70.6051)   # Metro Tobalaba
    },
    {
        'nombre': 'Las Condes - El Golf',
        'origen': (-33.4258, -70.6051),   # Metro Tobalaba
        'destino': (-33.4158, -70.5804)   # El Golf
    },
    {
        'nombre': 'Costanera Norte Tramo 1',
        'origen': (-33.4489, -70.6693),   # Entrada Costanera
        'destino': (-33.4123, -70.6234)   # Salida Tobalaba
    },
    {
        'nombre': 'Av. Vicuña Mackenna',
        'origen': (-33.4575, -70.6514),   # Plaza Italia
        'destino': (-33.5018, -70.6102)   # La Florida
    }
]

def extraer_trafico_google():
    """
    Extrae datos de tráfico en tiempo real de segmentos predeterminados
    """
    
    if not GOOGLE_MAPS_API_KEY:
        print("[ADVERTENCIA] GOOGLE_MAPS_API_KEY no configurado. Usando datos de ejemplo.")
        return generar_datos_ejemplo()
    
    print(f"[INFO] Consultando Google Maps Directions API...")
    print(f"[INFO] Analizando {len(SEGMENTOS_RUTA)} segmentos de ruta")
    
    segmentos_con_trafico = []
    
    for i, segmento in enumerate(SEGMENTOS_RUTA, 1):
        print(f"[INFO] Consultando segmento {i}/{len(SEGMENTOS_RUTA)}: {segmento['nombre']}")
        
        datos_trafico = consultar_trafico_segmento(segmento)
        
        if datos_trafico:
            segmentos_con_trafico.append(datos_trafico)
        
        # Pequeña pausa para no saturar la API
        import time
        time.sleep(0.2)
    
    # Transformar a GeoJSON
    trafico_geojson = transformar_a_geojson(segmentos_con_trafico)
    
    print(f"[OK] Se obtuvieron datos de tráfico para {len(segmentos_con_trafico)} segmentos")
    
    return trafico_geojson

def consultar_trafico_segmento(segmento):
    """
    Consulta el tráfico de un segmento específico usando Google Directions API
    """
    
    url = "https://maps.googleapis.com/maps/api/directions/json"
    
    origen_lat, origen_lon = segmento['origen']
    destino_lat, destino_lon = segmento['destino']
    
    params = {
        'origin': f"{origen_lat},{origen_lon}",
        'destination': f"{destino_lat},{destino_lon}",
        'departure_time': 'now',  # Para obtener duration_in_traffic
        'mode': 'driving',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['status'] != 'OK':
            print(f"[WARN] Error en API para {segmento['nombre']}: {data['status']}")
            return None
        
        # Extraer información relevante
        route = data['routes'][0]
        leg = route['legs'][0]
        
        # Duración sin tráfico (baseline)
        duracion_normal = leg['duration']['value']  # en segundos
        
        # Duración con tráfico actual
        duracion_con_trafico = leg.get('duration_in_traffic', {}).get('value', duracion_normal)
        
        # Calcular índice de congestión (IC)
        if duracion_normal > 0:
            indice_congestion = duracion_con_trafico / duracion_normal
        else:
            indice_congestion = 1.0
        
        # Distancia del segmento
        distancia = leg['distance']['value']  # en metros
        
        # Calcular punto medio del segmento para geolocalización
        punto_medio_lat = (origen_lat + destino_lat) / 2
        punto_medio_lon = (origen_lon + destino_lon) / 2
        
        return {
            'nombre': segmento['nombre'],
            'origen': segmento['origen'],
            'destino': segmento['destino'],
            'punto_medio': (punto_medio_lat, punto_medio_lon),
            'distancia_metros': distancia,
            'duracion_normal_seg': duracion_normal,
            'duracion_con_trafico_seg': duracion_con_trafico,
            'indice_congestion': indice_congestion,
            'nivel_alerta': calcular_nivel_alerta(indice_congestion),
            'polyline': route['overview_polyline']['points']
        }
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error consultando Google Maps para {segmento['nombre']}: {e}")
        return None

def calcular_nivel_alerta(indice_congestion):
    """
    Determina el nivel de alerta según el índice de congestión
    IC = duracion_con_trafico / duracion_normal
    """
    if indice_congestion >= 2.0:
        return 'rojo'  # Tráfico muy congestionado (toma el doble o más)
    elif indice_congestion >= 1.3:
        return 'amarillo'  # Tráfico moderado (30% más lento)
    else:
        return 'verde'  # Tráfico fluido

def transformar_a_geojson(segmentos):
    """
    Transforma los datos de tráfico a formato GeoJSON
    """
    
    features = []
    
    for seg in segmentos:
        # Calcular impacto en costo de combustible
        # A mayor congestión, mayor consumo (aproximadamente +50% por cada unidad de IC)
        factor_costo_adicional = (seg['indice_congestion'] - 1) * 0.5
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [seg['punto_medio'][1], seg['punto_medio'][0]]
            },
            'properties': {
                'tipo_amenaza': 'congestion_vehicular',
                'nombre_segmento': seg['nombre'],
                'distancia_km': round(seg['distancia_metros'] / 1000, 2),
                'duracion_normal_min': round(seg['duracion_normal_seg'] / 60, 1),
                'duracion_con_trafico_min': round(seg['duracion_con_trafico_seg'] / 60, 1),
                'retraso_min': round((seg['duracion_con_trafico_seg'] - seg['duracion_normal_seg']) / 60, 1),
                'indice_congestion': round(seg['indice_congestion'], 2),
                'nivel_alerta': seg['nivel_alerta'],
                'factor_costo_adicional': round(factor_costo_adicional, 2),
                'descripcion': generar_descripcion(seg),
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'fuente': 'Google Maps Directions API'
            }
        }
        
        features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'generado': datetime.utcnow().isoformat() + 'Z',
            'fuente': 'Google Maps Directions API',
            'total': len(features),
            'descripcion': 'Congestión vehicular en tiempo real en segmentos clave de la ruta'
        },
        'features': features
    }

def generar_descripcion(segmento):
    """
    Genera una descripción legible del estado del tráfico
    """
    ic = segmento['indice_congestion']
    retraso = (segmento['duracion_con_trafico_seg'] - segmento['duracion_normal_seg']) / 60
    
    if ic >= 2.0:
        estado = "Muy congestionado"
    elif ic >= 1.5:
        estado = "Congestionado"
    elif ic >= 1.3:
        estado = "Tráfico moderado"
    elif ic >= 1.1:
        estado = "Tráfico lento"
    else:
        estado = "Tráfico fluido"
    
    if retraso > 0:
        return f"{estado} - Retraso de {round(retraso, 1)} min respecto a condiciones normales"
    else:
        return estado

def generar_datos_ejemplo():
    """
    Genera datos de ejemplo para testing cuando no hay API key
    """
    
    print("[INFO] Generando datos de ejemplo...")
    
    ejemplos = [
        {
            'nombre': 'Alameda - Plaza Italia',
            'punto_medio': (-33.4430, -70.6519),
            'ic': 1.8,
            'distancia': 2.5,
            'duracion_normal': 8,
            'duracion_trafico': 14
        },
        {
            'nombre': 'Providencia - Tobalaba',
            'punto_medio': (-33.4315, -70.6198),
            'ic': 1.4,
            'distancia': 3.2,
            'duracion_normal': 10,
            'duracion_trafico': 14
        },
        {
            'nombre': 'Las Condes - El Golf',
            'punto_medio': (-33.4208, -70.5927),
            'ic': 1.1,
            'distancia': 2.8,
            'duracion_normal': 7,
            'duracion_trafico': 8
        },
        {
            'nombre': 'Costanera Norte Tramo 1',
            'punto_medio': (-33.4306, -70.6463),
            'ic': 2.3,
            'distancia': 5.0,
            'duracion_normal': 8,
            'duracion_trafico': 18
        },
        {
            'nombre': 'Av. Vicuña Mackenna',
            'punto_medio': (-33.4796, -70.6308),
            'ic': 1.6,
            'distancia': 6.5,
            'duracion_normal': 15,
            'duracion_trafico': 24
        }
    ]
    
    features = []
    
    for ej in ejemplos:
        nivel_alerta = calcular_nivel_alerta(ej['ic'])
        factor_costo = (ej['ic'] - 1) * 0.5
        retraso = ej['duracion_trafico'] - ej['duracion_normal']
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [ej['punto_medio'][1], ej['punto_medio'][0]]
            },
            'properties': {
                'tipo_amenaza': 'congestion_vehicular',
                'nombre_segmento': ej['nombre'],
                'distancia_km': ej['distancia'],
                'duracion_normal_min': ej['duracion_normal'],
                'duracion_con_trafico_min': ej['duracion_trafico'],
                'retraso_min': retraso,
                'indice_congestion': ej['ic'],
                'nivel_alerta': nivel_alerta,
                'factor_costo_adicional': round(factor_costo, 2),
                'descripcion': f"{'Muy congestionado' if ej['ic'] >= 2.0 else 'Congestionado' if ej['ic'] >= 1.5 else 'Tráfico moderado'} - Retraso de {retraso} min",
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'fuente': 'Google Maps (DATOS DE EJEMPLO)'
            }
        }
        
        features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'metadata': {
            'generado': datetime.utcnow().isoformat() + 'Z',
            'fuente': 'Google Maps - DATOS DE EJEMPLO',
            'total': len(features),
            'advertencia': 'Estos son datos de ejemplo. Configure GOOGLE_MAPS_API_KEY para datos reales.',
            'descripcion': 'Congestión vehicular en segmentos clave'
        },
        'features': features
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
    print("EXTRACCIÓN DE TRÁFICO VEHICULAR - GOOGLE MAPS")
    print("="*60)
    print()
    print("IMPORTANTE: Configure la variable de entorno GOOGLE_MAPS_API_KEY")
    print("Obtenga su API Key en: https://console.cloud.google.com")
    print()
    
    trafico = extraer_trafico_google()
    guardar_json(trafico, 'trafico_vehicular.geojson')
    
    print("\n[COMPLETADO] Extracción de tráfico finalizada")