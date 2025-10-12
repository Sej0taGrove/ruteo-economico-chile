# Estructura de Archivos JSON/GeoJSON - Amenazas

Este documento describe la estructura de cada archivo GeoJSON generado por los scripts de extracción de amenazas.

---

## 1. sismos.geojson

### Descripción
Contiene información geolocalizada de sismos recientes (últimas 24 horas) con magnitud >= 5.0 en territorio chileno.

### Estructura

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generado": "2025-10-10T12:00:00Z",
    "fuente": "NASA EONET Wildfires API",
    "total": 8
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-72.345, -38.123]
      },
      "properties": {
        "tipo_amenaza": "incendio_forestal",
        "titulo": "Wildfire - Araucanía Region, Chile",
        "descripcion": "Incendio forestal activo",
        "fecha_inicio": "2025-10-08T14:30:00Z",
        "nivel_alerta": "rojo",
        "categoria": "wildfires",
        "fuente": "NASA EONET",
        "url_detalle": "https://eonet.gsfc.nasa.gov/..."
      }
    }
  ]
}
```

### Campos de properties

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo_amenaza` | string | Siempre "incendio_forestal" |
| `titulo` | string | Título del evento |
| `descripcion` | string | Descripción del incendio |
| `fecha_inicio` | string | Fecha/hora de detección inicial |
| `nivel_alerta` | string | Siempre "rojo" para incendios activos |
| `categoria` | string | Categoría del evento (wildfires) |
| `fuente` | string | Fuente de los datos |
| `url_detalle` | string | URL con información detallada |

---

## 4. apagones.geojson

### Descripción
Interrupciones del suministro eléctrico (programadas y no programadas) reportadas por el Coordinador Eléctrico Nacional.

### Estructura

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generado": "2025-10-10T12:00:00Z",
    "fuente": "SIPUB - Coordinador Eléctrico Nacional",
    "total": 15
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-70.6693, -33.4489]
      },
      "properties": {
        "tipo_amenaza": "apagon",
        "tipo_interrupcion": "no_programada",
        "region": "Metropolitana",
        "comuna": "Santiago",
        "sector": "Centro",
        "clientes_afectados": 1500,
        "fecha_inicio": "2025-10-10T11:20:00Z",
        "fecha_estimada_fin": "2025-10-10T15:00:00Z",
        "nivel_alerta": "rojo",
        "causa": "Falla en subestación eléctrica",
        "fuente": "SIPUB Coordinador Eléctrico"
      }
    }
  ]
}
```

### Campos de properties

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo_amenaza` | string | Siempre "apagon" |
| `tipo_interrupcion` | string | "programada" o "no_programada" |
| `region` | string | Región administrativa afectada |
| `comuna` | string | Comuna afectada |
| `sector` | string | Sector específico afectado |
| `clientes_afectados` | integer | Número de clientes sin suministro |
| `fecha_inicio` | string | Fecha/hora de inicio del corte |
| `fecha_estimada_fin` | string | Fecha/hora estimada de restablecimiento |
| `nivel_alerta` | string | "rojo" (no programada) o "amarillo" (programada) |
| `causa` | string | Causa de la interrupción |
| `fuente` | string | Fuente de los datos |

---

## Notas Generales

### Formato de Coordenadas
Todas las geometrías usan el sistema de coordenadas WGS84 (EPSG:4326):
- **Longitud** (longitude): primer valor, rango [-180, 180]
- **Latitud** (latitude): segundo valor, rango [-90, 90]
- **Altitud/Profundidad** (opcional): tercer valor en metros

### Niveles de Alerta Estandarizados
- **verde**: Situación normal o bajo riesgo
- **amarillo**: Precaución, riesgo moderado
- **rojo**: Peligro, riesgo alto o crítico

### Timestamps
- Todos los timestamps están en formato ISO 8601 UTC
- Ejemplo: `"2025-10-10T12:30:45Z"`

### Uso en el Sistema
Estos archivos GeoJSON son:
1. Generados automáticamente por los scripts de extracción
2. Cargados a la base de datos PostGIS
3. Utilizados por el algoritmo de ruteo para evitar zonas de riesgo
4. Visualizados en el mapa web con Leaflet
{
  "type": "FeatureCollection",
  "metadata": {
    "generado": "2025-10-10T12:00:00Z",
    "fuente": "USGS Earthquake API",
    "total": 5
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-70.123, -33.456, 45.2]
      },
      "properties": {
        "tipo_amenaza": "sismo",
        "magnitud": 6.2,
        "profundidad_km": 45.2,
        "lugar": "23 km al sur de Santiago",
        "timestamp_utc": 1728561600000,
        "fecha_legible": "2025-10-10 08:00:00 UTC",
        "nivel_alerta": "amarillo",
        "url_detalle": "https://earthquake.usgs.gov/...",
        "fuente": "USGS"
      }
    }
  ]
}
```

### Campos de properties

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo_amenaza` | string | Siempre "sismo" |
| `magnitud` | float | Magnitud del sismo en escala Richter |
| `profundidad_km` | float | Profundidad del epicentro en kilómetros |
| `lugar` | string | Descripción legible de la ubicación |
| `timestamp_utc` | integer | Timestamp Unix en milisegundos |
| `fecha_legible` | string | Fecha/hora en formato legible UTC |
| `nivel_alerta` | string | "verde", "amarillo" o "rojo" según magnitud |
| `url_detalle` | string | URL con información detallada en USGS |
| `fuente` | string | Fuente de los datos |

### Criterios de nivel_alerta
- **rojo**: magnitud >= 7.0
- **amarillo**: magnitud >= 6.0 y < 7.0
- **verde**: magnitud >= 5.0 y < 6.0

---

## 2. inundaciones.geojson

### Descripción
Alertas hidrológicas activas del sistema de monitoreo de la Dirección General de Aguas (DGA).

### Estructura

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generado": "2025-10-10T12:00:00Z",
    "fuente": "DGA ALERTAS MapServer",
    "total": 12
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
        "timestamp": "2025-10-10T10:30:00Z",
        "fuente": "DGA MOP"
      }
    }
  ]
}
```

### Campos de properties

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo_amenaza` | string | Siempre "inundacion" |
| `estacion` | string | Nombre de la estación de monitoreo |
| `rio` | string | Nombre del río monitoreado |
| `region` | string | Región administrativa |
| `nivel_alerta` | string | "verde", "amarillo" o "rojo" |
| `estado` | string | Estado descriptivo de la alerta |
| `caudal_actual` | float | Caudal en m³/s (si disponible) |
| `timestamp` | string | Fecha/hora del registro |
| `fuente` | string | Fuente de los datos |

---

## 3. incendios.geojson

### Descripción
Incendios forestales activos detectados por satélite en territorio chileno.

### Estructura

```json