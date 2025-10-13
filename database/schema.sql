-- =============================================================================
-- SCHEMA PARA LA BASE DE DATOS DEL PROYECTO "RUTEO ECONÓMICO CHILE"
-- =============================================================================

-- Habilitar extensiones necesarias: PostGIS para datos geográficos y pgRouting para ruteo.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;

----------------------------------------------------
--                TABLAS DE METADATA                --
----------------------------------------------------

-- --- Tabla de Vehículos ---
CREATE TABLE IF NOT EXISTS vehiculos (
    id SERIAL PRIMARY KEY,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    version VARCHAR(255),
    ano INTEGER,
    tipo_carroceria VARCHAR(50),
    precio_referencia_clp INTEGER,
    tipo_combustible VARCHAR(50),
    rendimiento_mixto_km_l REAL,
    transmision VARCHAR(50),
    fuente VARCHAR(50)
);
CREATE INDEX IF NOT EXISTS idx_vehiculos_modelo ON vehiculos (marca, modelo);

-- --- Tablas de Peajes ---
CREATE TABLE IF NOT EXISTS autopistas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS peajes (
    id SERIAL PRIMARY KEY,
    peaje_id VARCHAR(50) UNIQUE NOT NULL,
    autopista_id INTEGER REFERENCES autopistas(id) ON DELETE CASCADE,
    nombre VARCHAR(255),
    ruta VARCHAR(100),
    region VARCHAR(100),
    tipo VARCHAR(50), -- Troncal, Lateral
    ubicacion GEOMETRY(Point, 4326)
);

CREATE TABLE IF NOT EXISTS porticos (
    id SERIAL PRIMARY KEY,
    portico_id VARCHAR(50) UNIQUE NOT NULL,
    autopista_id INTEGER REFERENCES autopistas(id) ON DELETE CASCADE,
    nombre VARCHAR(255),
    sentido VARCHAR(100),
    comuna VARCHAR(100),
    region VARCHAR(100),
    costo_base REAL,
    costo_saturacion REAL,
    ubicacion GEOMETRY(Point, 4326)
);

-- --- Tablas de Estaciones de Servicio ---
CREATE TABLE IF NOT EXISTS estaciones_servicio (
    id SERIAL PRIMARY KEY,
    id_estacion_cne VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(255),
    marca VARCHAR(100),
    direccion VARCHAR(255),
    comuna VARCHAR(100),
    region VARCHAR(100),
    horario TEXT,
    ubicacion GEOMETRY(Point, 4326)
);

CREATE TABLE IF NOT EXISTS precios_combustibles (
    id SERIAL PRIMARY KEY,
    estacion_id INTEGER NOT NULL REFERENCES estaciones_servicio(id) ON DELETE CASCADE,
    tipo_combustible VARCHAR(50) NOT NULL,
    precio INTEGER NOT NULL,
    fecha_actualizacion TIMESTAMPTZ
);

----------------------------------------------------
--             TABLAS DE INFRAESTRUCTURA            --
----------------------------------------------------
-- Estas tablas son generadas por osm2pgrouting, pero las definimos para referencia.
-- El script de carga se encargará de crearlas si no existen.
CREATE TABLE IF NOT EXISTS nodos_carreteras (
    id BIGINT PRIMARY KEY,
    geom GEOMETRY(Point, 4326)
);

CREATE TABLE IF NOT EXISTS aristas_carreteras (
    id SERIAL PRIMARY KEY,
    source BIGINT, -- FK a nodos_carreteras(id)
    target BIGINT, -- FK a nodos_carreteras(id)
    costo_longitud_m FLOAT,
    geom GEOMETRY(LineString, 4326)
);

----------------------------------------------------
--                 TABLA DE AMENAZAS                --
----------------------------------------------------
-- Tabla unificada para almacenar diferentes tipos de amenazas geo-localizadas.
CREATE TABLE IF NOT EXISTS amenazas (
    id SERIAL PRIMARY KEY,
    arista_id BIGINT, -- FK a 'aristas_carreteras.id', nulo para amenazas puntuales.
    tipo_amenaza VARCHAR(50) NOT NULL, -- 'congestion', 'incendio_forestal', 'inundacion', 'sismo'
    valor REAL, -- Factor de congestión, magnitud de sismo, etc.
    fecha_medicion TIMESTAMPTZ,
    geom GEOMETRY(Geometry, 4326), -- Puede ser Point (incendio) o LineString (congestión)
    detalles JSONB -- Datos adicionales específicos de cada amenaza (ej: título del incendio, nombre del río)
);


----------------------------------------------------
--              ÍNDICES PARA OPTIMIZACIÓN             --
----------------------------------------------------
-- Índices para tablas de metadata
CREATE INDEX IF NOT EXISTS idx_precios_estacion_id ON precios_combustibles (estacion_id);
CREATE INDEX IF NOT EXISTS idx_peajes_autopista_id ON peajes (autopista_id);
CREATE INDEX IF NOT EXISTS idx_porticos_autopista_id ON porticos (autopista_id);

-- Índices espaciales para consultas geográficas rápidas
CREATE INDEX IF NOT EXISTS idx_estaciones_ubicacion ON estaciones_servicio USING GIST (ubicacion);
CREATE INDEX IF NOT EXISTS idx_peajes_ubicacion ON peajes USING GIST (ubicacion);
CREATE INDEX IF NOT EXISTS idx_porticos_ubicacion ON porticos USING GIST (ubicacion);
CREATE INDEX IF NOT EXISTS idx_amenazas_geom ON amenazas USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_aristas_geom ON aristas_carreteras USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_nodos_geom ON nodos_carreteras USING GIST (geom);

-- Índices para mejorar el rendimiento de los joins de ruteo
CREATE INDEX IF NOT EXISTS idx_aristas_source ON aristas_carreteras(source);
CREATE INDEX IF NOT EXISTS idx_aristas_target ON aristas_carreteras(target);

-- Otros índices útiles
CREATE INDEX IF NOT EXISTS idx_amenazas_tipo ON amenazas (tipo_amenaza);