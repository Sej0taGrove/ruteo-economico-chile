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

## 4. trafico_vehicular.geojson

### Descripción
Información de congestión vehicular en tiempo real en segmentos clave de una ruta predeterminada, obtenida desde Google Maps Directions API.

### Estructura

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "generado": "2025-10-10T12:30:00Z",
    "fuente": "Google Maps Directions API",
    "total": 5,
    "descripcion": "Congestión vehicular en tiempo real en segmentos clave de la ruta"
  },
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [-70.6519, -33.4430]
      },
      "properties": {
        "tipo_amenaza": "congestion_vehicular",
        "nombre_segmento": "Alameda - Plaza Italia",
        "distancia_km": 2.5,
        "duracion_normal_min": 8.0,
        "duracion_con_trafico_min": 14.0,
        "retraso_min": 6.0,
        "indice_congestion": 1.75,
        "nivel_alerta": "amarillo",
        "factor_costo_adicional": 0.38,
        "descripcion": "Congestionado - Retraso de 6.0 min respecto a condiciones normales",
        "timestamp": "2025-10-10T12:30:00Z",
        "fuente": "Google Maps Directions API"
      }
    }
  ]
}
```

### Campos de properties

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `tipo_amenaza` | string | Siempre "congestion_vehicular" |
| `nombre_segmento` | string | Nombre identificador del segmento de ruta |
| `distancia_km` | float | Distancia del segmento en kilómetros |
| `duracion_normal_min` | float | Tiempo de recorrido en condiciones normales (min) |
| `duracion_con_trafico_min` | float | Tiempo de recorrido actual con tráfico (min) |
| `retraso_min` | float | Retraso adicional debido al tráfico (min) |
| `indice_congestion` | float | IC = duración_con_tráfico / duración_normal |
| `nivel_alerta` | string | "verde", "amarillo" o "rojo" según IC |
| `factor_costo_adicional` | float | Factor de incremento en costo de combustible |
| `descripcion` | string | Descripción legible del estado del tráfico |
| `timestamp` | string | Momento de la consulta (UTC) |
| `fuente` | string | Fuente de los datos |

### Criterios de nivel_alerta

- **verde**: IC < 1.3 (tráfico fluido)
- **amarillo**: 1.3 ≤ IC < 2.0 (tráfico moderado a congestionado)
- **rojo**: IC ≥ 2.0 (muy congestionado)

### Cálculo del Factor de Costo Adicional

El factor de costo adicional se calcula como:
```
factor_costo_adicional = (IC - 1) * 0.5
```

Esto significa:
- IC = 1.0 → factor = 0 (sin aumento de costo)
- IC = 1.5 → factor = 0.25 (25% más costo de combustible)
- IC = 2.0 → factor = 0.50 (50% más costo de combustible)
- IC = 3.0 → factor = 1.00 (100% más costo de combustible)

### Segmentos Monitoreados

La ruta predeterminada incluye los siguientes segmentos clave:

1. **Alameda - Plaza Italia**: Eje central de Santiago
2. **Providencia - Tobalaba**: Av. Providencia
3. **Las Condes - El Golf**: Sector oriente
4. **Costanera Norte Tramo 1**: Autopista urbana
5. **Av. Vicuña Mackenna**: Eje sur

### Notas Importantes

- **Actualización**: Los datos deben actualizarse cada 10-15 minutos para reflejar condiciones actuales
- **API Key requerida**: Necesita una API Key válida de Google Cloud Platform
- **Departure time**: Usa `departure_time=now` para obtener datos en tiempo real
- **Costo por consulta**: Google Maps cobra por cada llamada a la API

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