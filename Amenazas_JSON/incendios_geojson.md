# Estructura del archivo incendios.geojson

## Descripción General
El archivo `incendios.geojson` contiene información sobre incendios forestales y urbanos en Chile, incluyendo su ubicación, extensión y nivel de riesgo.

## Estructura del GeoJSON

```json
{
    "type": "FeatureCollection",
    "metadata": {
        "generado": "timestamp ISO 8601",
        "fuente": "CONAF/ONEMI",
        "total": "número total de incendios"
    },
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[lon1,lat1], [lon2,lat2], ...]]
            },
            "properties": {
                "id_incendio": "identificador único del incendio",
                "nivel_alerta": "nivel de alerta del incendio",
                "estado": "estado actual del incendio",
                "fecha_inicio": "timestamp ISO 8601",
                "fecha_control": "timestamp ISO 8601",
                "superficie_ha": "superficie afectada en hectáreas",
                "tipo": "tipo de incendio",
                "causa": "causa del incendio",
                "recursos": {
                    "brigadas": "número de brigadas",
                    "aeronaves": "número de aeronaves",
                    "vehiculos": "número de vehículos"
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
- `total`: Cantidad de incendios activos registrados

### Features
Cada incendio se representa como un Feature con:

#### Geometry
- `coordinates`: Array de polígonos que delimitan el área afectada
  - Cada polígono es un array de coordenadas [longitud, latitud]

#### Properties
- `id_incendio`: Identificador único del evento
- `nivel_alerta`: Nivel de alerta (ej: "Verde", "Amarilla", "Roja")
- `estado`: Estado actual ("Activo", "Controlado", "Extinguido")
- `fecha_inicio`: Fecha y hora de inicio del incendio
- `fecha_control`: Fecha y hora de control del incendio (si aplica)
- `superficie_ha`: Área afectada en hectáreas
- `tipo`: Clasificación del incendio (ej: "Forestal", "Urbano")
- `causa`: Causa probable del incendio
- `recursos`: Detalle de recursos desplegados para el control