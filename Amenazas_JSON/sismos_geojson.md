# Estructura del archivo sismos.geojson

## Descripción General
El archivo `sismos.geojson` contiene información sobre eventos sísmicos registrados en Chile. Los datos son obtenidos desde la API del USGS (United States Geological Survey).

## Estructura del GeoJSON

```json
{
    "type": "FeatureCollection",
    "metadata": {
        "generado": "timestamp ISO 8601",
        "fuente": "USGS Earthquake API",
        "total": "número total de sismos"
    },
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [longitud, latitud, profundidad]
            },
            "properties": {
                "magnitud": "magnitud del sismo en escala Richter",
                "lugar": "descripción de la ubicación",
                "fecha": "timestamp ISO 8601",
                "profundidad_km": "profundidad en kilómetros",
                "tipo": "tipo de evento sísmico",
                "id_original": "identificador único del USGS"
            }
        }
    ]
}
```

## Descripción de Campos

### Metadata
- `generado`: Timestamp de cuando se generó el archivo
- `fuente`: Origen de los datos
- `total`: Cantidad de sismos en el archivo

### Features
Cada sismo se representa como un Feature con:

#### Geometry
- `coordinates`: Array [longitud, latitud, profundidad]
  - `longitud`: Coordenada longitudinal (-180 a 180)
  - `latitud`: Coordenada latitudinal (-90 a 90)
  - `profundidad`: Profundidad en kilómetros

#### Properties
- `magnitud`: Intensidad del sismo en escala Richter
- `lugar`: Descripción textual de la ubicación
- `fecha`: Fecha y hora del evento en formato ISO 8601
- `profundidad_km`: Profundidad del hipocentro en kilómetros
- `tipo`: Clasificación del evento (ej: "earthquake")
- `id_original`: Identificador único asignado por USGS
```

2. Create inundaciones_geojson.md:

````markdown
// filepath: c:\Users\diego\OneDrive\Documentos\GitHub\ruteo-economico-chile\Amenazas_JSON\inundaciones_geojson.md
# Estructura del archivo inundaciones.geojson

## Descripción General
El archivo `inundaciones.geojson` contiene información sobre zonas de inundación y alertas de inundación en Chile.

## Estructura del GeoJSON

```json
{
    "type": "FeatureCollection",
    "metadata": {
        "generado": "timestamp ISO 8601",
        "fuente": "DGA/ONEMI",
        "total": "número total de registros"
    },
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[lon1,lat1], [lon2,lat2], ...]]
            },
            "properties": {
                "nivel_alerta": "nivel de la alerta de inundación",
                "descripcion": "descripción del evento",
                "fecha": "timestamp ISO 8601",
                "region": "región afectada",
                "comuna": "comuna afectada",
                "causa": "causa de la inundación",
                "area_km2": "área afectada en km²"
            }
        }
    ]
}
```

## Descripción de Campos

### Metadata
- `generado`: Timestamp de generación del archivo
- `fuente`: Origen de los datos
- `total`: Cantidad de zonas de inundación registradas

### Features
Cada zona de inundación se representa como un Feature con:

#### Geometry
- `coordinates`: Array de polígonos que delimitan el área afectada
  - Cada polígono es un array de coordenadas [longitud, latitud]

#### Properties
- `nivel_alerta`: Nivel de alerta (ej: "Verde", "Amarilla", "Roja")
- `descripcion`: Descripción detallada del evento
- `fecha`: Fecha y hora del registro
- `region`: Región administrativa afectada
- `comuna`: Comuna afectada
- `causa`: Causa de la inundación (ej: "Lluvia", "Desborde", etc.)
- `area_km2`: Extensión del área afectada en kilómetros cuadrados
```