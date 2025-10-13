# Estructura del archivo trafico_vehicular.geojson

## Descripción General
El archivo `trafico_vehicular.geojson` contiene información sobre el estado del tráfico en las principales vías de Chile, incluyendo congestiones, accidentes y obras viales.

## Estructura del GeoJSON

```json
{
    "type": "FeatureCollection",
    "metadata": {
        "generado": "timestamp ISO 8601",
        "fuente": "UOCT/Concesionarias",
        "total": "número total de eventos"
    },
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon1,lat1], [lon2,lat2], ...]
            },
            "properties": {
                "id_evento": "identificador único del evento",
                "tipo": "tipo de evento de tráfico",
                "nivel_congestion": "nivel de congestión",
                "velocidad_promedio": "velocidad promedio en km/h",
                "fecha_inicio": "timestamp ISO 8601",
                "fecha_estimada_fin": "timestamp ISO 8601",
                "causa": "causa del evento",
                "impacto": "nivel de impacto en el tráfico",
                "longitud_km": "longitud del tramo afectado",
                "via": {
                    "nombre": "nombre de la vía",
                    "tipo": "tipo de vía",
                    "sentido": "sentido del tráfico"
                }
            }
        }
    ]
}
```

## Descripción de Campos

### Metadata
- `generado`: Timestamp de cuando se generó el archivo
- `fuente`: Origen de los datos
- `total`: Cantidad de eventos de tráfico registrados

### Features
Cada evento de tráfico se representa como un Feature con:

#### Geometry
- `coordinates`: Array de puntos que forman la línea del tramo afectado
  - Cada punto es un par [longitud, latitud]

#### Properties
- `id_evento`: Identificador único del evento
- `tipo`: Tipo de evento ("Congestión", "Accidente", "Obras", etc.)
- `nivel_congestion`: Nivel de congestión ("Bajo", "Medio", "Alto")
- `velocidad_promedio`: Velocidad promedio actual en km/h
- `fecha_inicio`: Fecha y hora de inicio del evento
- `fecha_estimada_fin`: Fecha y hora estimada de finalización
- `causa`: Causa del evento
- `impacto`: Nivel de impacto ("Bajo", "Medio", "Alto")
- `longitud_km`: Extensión del tramo afectado en kilómetros
- `via`: Información sobre la vía afectada
  - `nombre`: Nombre de la vía o carretera
  - `tipo`: Tipo de vía (ej: "Autopista", "Avenida")
  - `sentido`: Sentido del tráfico afectado