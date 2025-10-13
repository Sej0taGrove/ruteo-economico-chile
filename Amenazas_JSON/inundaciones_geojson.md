# Estructura del archivo inundaciones.geojson

## Descripción General
El archivo `inundaciones.geojson` contiene información sobre alertas hidrológicas y eventos de inundación en Chile, registrados por la Dirección General de Aguas (DGA) y ONEMI.

## Estructura del GeoJSON

```json
{
    "type": "FeatureCollection",
    "metadata": {
        "generado": "2025-10-10T12:00:00Z",
        "fuente": "DGA ALERTAS MapServer/ONEMI",
        "total": "número total de alertas"
    },
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-71.234, -36.567]
            },
            "properties": {
                "tipo_amenaza": "inundacion",
                "estacion": "Estación Ñuble",
                "rio": "Río Ñuble",
                "region": "Región de Ñuble",
                "nivel_alerta": "amarillo",
                "estado": "Alerta Amarilla",
                "caudal_actual": 450.5,
                "caudal_normal": 300.0,
                "porcentaje_aumento": 50.2,
                "precipitacion_24h": 45.2,
                "timestamp": "2025-10-10T10:30:00Z",
                "fuente": "DGA MOP"
            }
        }
    ]
}
```

## Descripción de Campos

### Metadata
- `generado`: Timestamp de cuando se generó el archivo
- `fuente`: Origen de los datos (DGA/ONEMI)
- `total`: Cantidad de alertas activas registradas

### Features
Cada alerta de inundación se representa como un Feature con:

#### Geometry
- `coordinates`: Par ordenado [longitud, latitud] que representa la ubicación de la estación o punto de monitoreo

#### Properties
- `tipo_amenaza`: Siempre "inundacion"
- `estacion`: Nombre de la estación de monitoreo
- `rio`: Nombre del río o curso de agua monitoreado
- `region`: Región administrativa donde se ubica
- `nivel_alerta`: Estado de la alerta
  - "verde": Normal o precaución
  - "amarillo": Alerta temprana preventiva
  - "rojo": Alerta de peligro inminente
- `estado`: Descripción textual del estado de alerta
- `caudal_actual`: Caudal medido en metros cúbicos por segundo (m³/s)
- `caudal_normal`: Caudal promedio histórico para el período
- `porcentaje_aumento`: Porcentaje de aumento respecto al caudal normal
- `precipitacion_24h`: Precipitación acumulada en las últimas 24 horas (mm)
- `timestamp`: Fecha y hora de la medición en formato ISO 8601
- `fuente`: Institución que proporciona los datos

### Criterios de nivel_alerta
- **verde**: Caudal < 120% del normal
- **amarillo**: Caudal entre 120% y 150% del normal
- **rojo**: Caudal > 150% del normal o desborde confirmado

### Notas Importantes
- Las coordenadas utilizan el sistema WGS84 (EPSG:4326)
- Los timestamps están en UTC
- El caudal se mide en metros cúbicos por segundo (m³/s)
- La precipitación se mide en milímetros (mm)