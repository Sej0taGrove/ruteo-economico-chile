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
DROP TABLE IF EXISTS amenazas_congestion CASCADE;

CREATE TABLE amenazas_congestion (
    id SERIAL PRIMARY KEY,
    arista_id INTEGER NOT NULL REFERENCES aristas_carreteras(id) ON DELETE CASCADE,
    tiempo_ideal_seg INTEGER,
    tiempo_actual_seg INTEGER,
    factor_congestion NUMERIC(5, 2),
    fecha_medicion TIMESTAMP WITH TIME ZONE NOT NULL
);
CREATE INDEX idx_amenazas_arista_id ON amenazas_congestion(arista_id);