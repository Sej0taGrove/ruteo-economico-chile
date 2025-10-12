-- Archivo: schema.sql
-- Este script crea la estructura completa de la base de datos para el proyecto de ruteo.

-- Habilitar las extensiones necesarias: PostGIS para datos geográficos y pgRouting para el cálculo de rutas.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

----------------------------------------------------
--                TABLAS DE METADATA                --
----------------------------------------------------

-- --- Tabla de Vehículos ---
DROP TABLE IF EXISTS vehiculos CASCADE;
CREATE TABLE vehiculos (
    id SERIAL PRIMARY KEY,
    modelo_base VARCHAR(255) NOT NULL,
    version VARCHAR(255) NOT NULL,
    consumo_mixto_kml NUMERIC(4, 1),
    consumo_urbano_kml NUMERIC(4, 1),
    consumo_extraurbano_kml NUMERIC(4, 1),
    capacidad_estanque_litros INTEGER,
    motor_litros NUMERIC(3, 1),
    transmision VARCHAR(50),
    traccion VARCHAR(50)
);
CREATE INDEX idx_vehiculos_modelo ON vehiculos (modelo_base);


-- --- Tablas de Peajes ---
DROP TABLE IF EXISTS peajes CASCADE;
DROP TABLE IF EXISTS porticos CASCADE;
DROP TABLE IF EXISTS autopistas CASCADE;

CREATE TABLE autopistas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    tramo_descripcion VARCHAR(255),
    año_tarifas INTEGER
);

CREATE TABLE porticos (
    id SERIAL PRIMARY KEY,
    autopista_id INTEGER NOT NULL REFERENCES autopistas(id) ON DELETE CASCADE,
    portico_id_concesion VARCHAR(100),
    nombre_eje VARCHAR(255),
    sentido VARCHAR(100),
    referencia_tramo VARCHAR(255),
    longitud_km NUMERIC(6, 4),
    ubicacion GEOGRAPHY(Point, 4326)
);

CREATE TABLE peajes (
    id SERIAL PRIMARY KEY,
    portico_id INTEGER NOT NULL REFERENCES porticos(id) ON DELETE CASCADE,
    categoria_vehiculo VARCHAR(255) NOT NULL,
    tipo_tarifa VARCHAR(100) NOT NULL,
    valor INTEGER NOT NULL,
    tipo_dia VARCHAR(50),
    horario VARCHAR(100)
);


-- --- Tablas de Estaciones de Servicio ---
DROP TABLE IF EXISTS precios_combustibles CASCADE;
DROP TABLE IF EXISTS estaciones_servicio CASCADE;

CREATE TABLE estaciones_servicio (
    id SERIAL PRIMARY KEY,
    id_estacion_cne VARCHAR(100) UNIQUE,
    nombre VARCHAR(255),
    marca VARCHAR(100),
    direccion VARCHAR(255),
    comuna VARCHAR(100),
    region VARCHAR(100),
    horario TEXT,
    ubicacion GEOGRAPHY(Point, 4326)
);

CREATE TABLE precios_combustibles (
    id SERIAL PRIMARY KEY,
    estacion_id INTEGER NOT NULL REFERENCES estaciones_servicio(id) ON DELETE CASCADE,
    tipo_combustible VARCHAR(50) NOT NULL,
    precio INTEGER NOT NULL,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE
);


----------------------------------------------------
--             TABLAS DE INFRAESTRUCTURA            --
----------------------------------------------------
DROP TABLE IF EXISTS aristas_carreteras CASCADE;
DROP TABLE IF EXISTS nodos_carreteras CASCADE;

CREATE TABLE nodos_carreteras (
    id BIGINT PRIMARY KEY,
    geom GEOMETRY(Point, 4326)
);

CREATE TABLE aristas_carreteras (
    id SERIAL PRIMARY KEY,
    source BIGINT REFERENCES nodos_carreteras(id),
    target BIGINT REFERENCES nodos_carreteras(id),
    costo_longitud_m FLOAT,
    geom GEOMETRY(LineString, 4326)
);

-- Índices para acelerar las consultas de ruteo y visualización
CREATE INDEX idx_aristas_source ON aristas_carreteras(source);
CREATE INDEX idx_aristas_target ON aristas_carreteras(target);
CREATE INDEX idx_aristas_geom ON aristas_carreteras USING GIST (geom);
CREATE INDEX idx_nodos_geom ON nodos_carreteras USING GIST (geom);


----------------------------------------------------
--                 TABLAS DE AMENAZAS               --
----------------------------------------------------

-- --- Tabla de Sismos ---
DROP TABLE IF EXISTS amenazas_sismos CASCADE;
CREATE TABLE amenazas_sismos (
    id SERIAL PRIMARY KEY,
    tipo_amenaza VARCHAR(50) NOT NULL DEFAULT 'sismo',
    magnitud NUMERIC(3, 1) NOT NULL,
    profundidad_km NUMERIC(6, 3),
    lugar VARCHAR(500),
    timestamp_utc BIGINT,
    fecha_legible TIMESTAMP,
    nivel_alerta VARCHAR(20),
    url_detalle TEXT,
    fuente VARCHAR(100) DEFAULT 'USGS',
    geom GEOMETRY(Point, 4326) NOT NULL,
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sismos_geom ON amenazas_sismos USING GIST(geom);
CREATE INDEX idx_sismos_alerta ON amenazas_sismos(nivel_alerta);
CREATE INDEX idx_sismos_magnitud ON amenazas_sismos(magnitud);
CREATE INDEX idx_sismos_fecha ON amenazas_sismos(fecha_legible);


-- --- Tabla de Inundaciones ---
DROP TABLE IF EXISTS amenazas_inundaciones CASCADE;
CREATE TABLE amenazas_inundaciones (
    id SERIAL PRIMARY KEY,
    tipo_amenaza VARCHAR(50) NOT NULL DEFAULT 'inundacion',
    estacion VARCHAR(255),
    rio VARCHAR(255),
    region VARCHAR(100),
    nivel_alerta VARCHAR(20),
    estado VARCHAR(100),
    caudal_actual NUMERIC(10, 2),
    timestamp TIMESTAMP,
    fuente VARCHAR(100) DEFAULT 'DGA MOP',
    geom GEOMETRY(Point, 4326) NOT NULL,
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inundaciones_geom ON amenazas_inundaciones USING GIST(geom);
CREATE INDEX idx_inundaciones_alerta ON amenazas_inundaciones(nivel_alerta);
CREATE INDEX idx_inundaciones_region ON amenazas_inundaciones(region);
CREATE INDEX idx_inundaciones_timestamp ON amenazas_inundaciones(timestamp);


-- --- Tabla de Incendios Forestales ---
DROP TABLE IF EXISTS amenazas_incendios CASCADE;
CREATE TABLE amenazas_incendios (
    id SERIAL PRIMARY KEY,
    tipo_amenaza VARCHAR(50) NOT NULL DEFAULT 'incendio_forestal',
    titulo VARCHAR(500),
    descripcion TEXT,
    fecha_inicio TIMESTAMP,
    nivel_alerta VARCHAR(20) DEFAULT 'rojo',
    categoria VARCHAR(100) DEFAULT 'wildfires',
    url_detalle TEXT,
    fuente VARCHAR(100) DEFAULT 'NASA EONET',
    geom GEOMETRY(Point, 4326) NOT NULL,
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_incendios_geom ON amenazas_incendios USING GIST(geom);
CREATE INDEX idx_incendios_alerta ON amenazas_incendios(nivel_alerta);
CREATE INDEX idx_incendios_fecha ON amenazas_incendios(fecha_inicio);


-- --- Tabla de Tráfico Vehicular ---
DROP TABLE IF EXISTS amenazas_trafico CASCADE;
CREATE TABLE amenazas_trafico (
    id SERIAL PRIMARY KEY,
    tipo_amenaza VARCHAR(50) NOT NULL DEFAULT 'congestion_vehicular',
    nombre_segmento VARCHAR(255),
    distancia_km NUMERIC(6, 2),
    duracion_normal_min NUMERIC(6, 1),
    duracion_con_trafico_min NUMERIC(6, 1),
    retraso_min NUMERIC(6, 1),
    indice_congestion NUMERIC(4, 2),
    nivel_alerta VARCHAR(20),
    factor_costo_adicional NUMERIC(4, 2),
    descripcion TEXT,
    timestamp TIMESTAMP,
    fuente VARCHAR(100) DEFAULT 'Google Maps Directions API',
    geom GEOMETRY(Point, 4326) NOT NULL,
    fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trafico_geom ON amenazas_trafico USING GIST(geom);
CREATE INDEX idx_trafico_alerta ON amenazas_trafico(nivel_alerta);
CREATE INDEX idx_trafico_congestion ON amenazas_trafico(indice_congestion);
CREATE INDEX idx_trafico_timestamp ON amenazas_trafico(timestamp);
CREATE INDEX idx_trafico_segmento ON amenazas_trafico(nombre_segmento);


----------------------------------------------------
--              FUNCIONES AUXILIARES                --
----------------------------------------------------

-- Función para limpiar tablas de amenazas (útil para refrescar datos)
CREATE OR REPLACE FUNCTION limpiar_amenazas_antiguas(dias INTEGER DEFAULT 7)
RETURNS void AS $$
BEGIN
    -- Limpiar sismos más antiguos que X días
    DELETE FROM amenazas_sismos WHERE fecha_legible < NOW() - INTERVAL '1 day' * dias;
    
    -- Limpiar inundaciones más antiguas que X días
    DELETE FROM amenazas_inundaciones WHERE timestamp < NOW() - INTERVAL '1 day' * dias;
    
    -- Limpiar incendios resueltos más antiguos que X días
    DELETE FROM amenazas_incendios WHERE fecha_inicio < NOW() - INTERVAL '1 day' * dias;
    
    -- Limpiar datos de tráfico más antiguos que 1 día (siempre debe ser reciente)
    DELETE FROM amenazas_trafico WHERE timestamp < NOW() - INTERVAL '1 day';
    
    RAISE NOTICE 'Amenazas antiguas limpiadas exitosamente';
END;
$$ LANGUAGE plpgsql;

-- Función para obtener amenazas cercanas a una ruta
CREATE OR REPLACE FUNCTION obtener_amenazas_cercanas_ruta(
    ruta_geom GEOMETRY,
    radio_metros NUMERIC DEFAULT 5000
)
RETURNS TABLE (
    tipo_amenaza VARCHAR,
    nivel_alerta VARCHAR,
    distancia_metros NUMERIC,
    descripcion TEXT,
    ubicacion GEOMETRY
) AS $$
BEGIN
    RETURN QUERY
    -- Sismos cercanos
    SELECT 
        s.tipo_amenaza::VARCHAR,
        s.nivel_alerta::VARCHAR,
        ST_Distance(s.geom::geography, ruta_geom::geography)::NUMERIC as distancia_metros,
        ('Sismo magnitud ' || s.magnitud || ' - ' || s.lugar)::TEXT as descripcion,
        s.geom as ubicacion
    FROM amenazas_sismos s
    WHERE ST_DWithin(s.geom::geography, ruta_geom::geography, radio_metros)
    
    UNION ALL
    
    -- Inundaciones cercanas
    SELECT 
        i.tipo_amenaza::VARCHAR,
        i.nivel_alerta::VARCHAR,
        ST_Distance(i.geom::geography, ruta_geom::geography)::NUMERIC as distancia_metros,
        ('Alerta de inundación - ' || COALESCE(i.rio, 'Río no especificado'))::TEXT as descripcion,
        i.geom as ubicacion
    FROM amenazas_inundaciones i
    WHERE ST_DWithin(i.geom::geography, ruta_geom::geography, radio_metros)
    
    UNION ALL
    
    -- Incendios cercanos
    SELECT 
        inc.tipo_amenaza::VARCHAR,
        inc.nivel_alerta::VARCHAR,
        ST_Distance(inc.geom::geography, ruta_geom::geography)::NUMERIC as distancia_metros,
        ('Incendio forestal - ' || COALESCE(inc.titulo, 'Sin título'))::TEXT as descripcion,
        inc.geom as ubicacion
    FROM amenazas_incendios inc
    WHERE ST_DWithin(inc.geom::geography, ruta_geom::geography, radio_metros)
    
    UNION ALL
    
    -- Tráfico en la ruta
    SELECT 
        t.tipo_amenaza::VARCHAR,
        t.nivel_alerta::VARCHAR,
        ST_Distance(t.geom::geography, ruta_geom::geography)::NUMERIC as distancia_metros,
        t.descripcion::TEXT,
        t.geom as ubicacion
    FROM amenazas_trafico t
    WHERE ST_DWithin(t.geom::geography, ruta_geom::geography, radio_metros)
    ORDER BY distancia_metros;
END;
$$ LANGUAGE plpgsql;


----------------------------------------------------
--                    VISTAS                        --
----------------------------------------------------

-- Vista consolidada de todas las amenazas activas
CREATE OR REPLACE VIEW vista_amenazas_activas AS
SELECT 
    'sismo' as tipo,
    nivel_alerta,
    fecha_legible as fecha,
    lugar as descripcion,
    geom,
    fecha_carga
FROM amenazas_sismos
WHERE fecha_legible > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'inundacion' as tipo,
    nivel_alerta,
    timestamp as fecha,
    COALESCE(rio, estacion) as descripcion,
    geom,
    fecha_carga
FROM amenazas_inundaciones
WHERE timestamp > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'incendio' as tipo,
    nivel_alerta,
    fecha_inicio as fecha,
    titulo as descripcion,
    geom,
    fecha_carga
FROM amenazas_incendios
WHERE fecha_inicio > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'trafico' as tipo,
    nivel_alerta,
    timestamp as fecha,
    nombre_segmento as descripcion,
    geom,
    fecha_carga
FROM amenazas_trafico
WHERE timestamp > NOW() - INTERVAL '1 day';


----------------------------------------------------
--              COMENTARIOS DE TABLAS               --
----------------------------------------------------

COMMENT ON TABLE amenazas_sismos IS 'Sismos registrados >= magnitud 5.0 en territorio chileno desde USGS';
COMMENT ON TABLE amenazas_inundaciones IS 'Alertas hidrológicas activas desde DGA MOP';
COMMENT ON TABLE amenazas_incendios IS 'Incendios forestales activos detectados por NASA EONET';
COMMENT ON TABLE amenazas_trafico IS 'Congestión vehicular en tiempo real desde Google Maps';

COMMENT ON COLUMN amenazas_sismos.indice_congestion IS 'Índice de congestión: duracion_con_trafico / duracion_normal';
COMMENT ON COLUMN amenazas_trafico.factor_costo_adicional IS 'Factor de incremento en costo de combustible debido a congestión';