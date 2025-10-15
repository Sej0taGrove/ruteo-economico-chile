from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import psycopg
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from psycopg.rows import dict_row

load_dotenv()

app = Flask(__name__)


@dataclass(frozen=True)
class RouteNode:
    """Representa un nodo de la red vial utilizable para el cálculo de rutas."""

    node_id: int
    lon: float
    lat: float
    label: str


def _load_db_config() -> dict:
    """Construye la configuración de conexión a Postgres a partir de variables de entorno."""

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([dbname, user, password]):
        raise RuntimeError(
            "Faltan variables de conexión a la base de datos. "
            "Asegúrate de definir DB_NAME, DB_USER y DB_PASSWORD."
        )

    return {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "password": password,
    }


DB_CONFIG = _load_db_config()


def get_db_connection() -> psycopg.Connection:
    """Abre una conexión usando row_factory dict para acceder por nombre de columna."""

    return psycopg.connect(**DB_CONFIG, row_factory=dict_row)


def _parse_bbox(raw_bbox: Optional[str]) -> Optional[Tuple[float, float, float, float]]:
    """Convierte un bbox `minLon,minLat,maxLon,maxLat` en una tupla de floats."""

    if not raw_bbox:
        return None

    parts = raw_bbox.split(",")
    if len(parts) != 4:
        raise ValueError("El parámetro bbox debe tener cuatro valores separados por coma.")

    try:
        min_lon, min_lat, max_lon, max_lat = map(float, parts)
    except ValueError as exc:
        raise ValueError("El parámetro bbox debe contener solo números.") from exc

    if min_lon >= max_lon or min_lat >= max_lat:
        raise ValueError("Los valores del bbox no son válidos (min >= max).")

    return min_lon, min_lat, max_lon, max_lat


def _geojson_from_query(query: str, params: Optional[Sequence] = None) -> dict:
    """Ejecuta un SELECT que expone columnas `geometry` y `properties` como JSON y las empaqueta en GeoJSON."""

    params = params or ()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    features: List[Dict] = []
    for row in rows:
        geometry = row.get("geometry")
        if isinstance(geometry, str):
            geometry = json.loads(geometry)

        properties = row.get("properties") or {}
        if isinstance(properties, str):
            properties = json.loads(properties)

        feature: Dict[str, object] = {"type": "Feature", "geometry": geometry, "properties": properties}
        feature_id = row.get("id")
        if feature_id is not None:
            feature["id"] = feature_id

        features.append(feature)

    return {"type": "FeatureCollection", "features": features}


def _fetch_route_node(node_id: int, conn: Optional[psycopg.Connection] = None) -> RouteNode:
    """Obtiene la geometría del nodo solicitado y la expone como RouteNode."""

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    ST_X(geom)::float AS lon,
                    ST_Y(geom)::float AS lat
                FROM nodos_carreteras
                WHERE id = %s;
                """,
                (node_id,),
            )
            row = cur.fetchone()
    finally:
        if close_conn:
            conn.close()

    if not row:
        raise ValueError(f"El nodo {node_id} no existe en nodos_carreteras.")

    return RouteNode(node_id=row["id"], lon=row["lon"], lat=row["lat"], label=f"Nodo {row['id']}")


def _get_default_route_nodes(conn: Optional[psycopg.Connection] = None) -> Tuple[RouteNode, RouteNode]:
    """Selecciona dos nodos de referencia (mínimo y máximo id) para la ruta de demostración."""

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    ST_X(geom)::float AS lon,
                    ST_Y(geom)::float AS lat
                FROM nodos_carreteras
                ORDER BY id ASC
                LIMIT 1;
                """
            )
            start_row = cur.fetchone()

            cur.execute(
                """
                SELECT
                    id,
                    ST_X(geom)::float AS lon,
                    ST_Y(geom)::float AS lat
                FROM nodos_carreteras
                ORDER BY id DESC
                LIMIT 1;
                """
            )
            end_row = cur.fetchone()
    finally:
        if close_conn:
            conn.close()

    if not start_row or not end_row:
        raise ValueError("No hay nodos suficientes en la red vial para calcular rutas.")
    if start_row["id"] == end_row["id"]:
        raise ValueError("Se requieren al menos dos nodos distintos en la red vial.")

    return (
        RouteNode(
            node_id=start_row["id"],
            lon=start_row["lon"],
            lat=start_row["lat"],
            label=f"Nodo {start_row['id']}",
        ),
        RouteNode(
            node_id=end_row["id"],
            lon=end_row["lon"],
            lat=end_row["lat"],
            label=f"Nodo {end_row['id']}",
        ),
    )


@app.route("/")
def index():
    try:
        start_node, end_node = _get_default_route_nodes()
        default_route = {
            "start": {"lat": start_node.lat, "lon": start_node.lon, "label": start_node.label, "node_id": start_node.node_id},
            "end": {"lat": end_node.lat, "lon": end_node.lon, "label": end_node.label, "node_id": end_node.node_id},
        }
    except ValueError as exc:
        # Fallback para no romper la interfaz; se indicará el error en la ruta
        default_route = {
            "error": str(exc),
            "start": {"lat": -33.45, "lon": -70.66, "label": "Nodo no disponible", "node_id": None},
            "end": {"lat": -33.45, "lon": -70.63, "label": "Nodo no disponible", "node_id": None},
        }

    return render_template("index.html", default_route=default_route)


@app.route("/api/infrastructure")
def api_infrastructure():
    """Expone la red vial (aristas) en GeoJSON, con filtrado opcional por bbox."""

    try:
        bbox = _parse_bbox(request.args.get("bbox"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    bbox_filter = ""
    params: Sequence = ()
    if bbox:
        bbox_filter = "WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)"
        params = bbox

    query = f"""
        SELECT
            id,
            json_build_object(
                'edge_id', id,
                'longitud_m', costo_longitud_m
            ) AS properties,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM aristas_carreteras
        {bbox_filter}
        ORDER BY id
        LIMIT 5000;
    """

    data = _geojson_from_query(query, params)
    return jsonify(data)


@app.route("/api/metadata")
def api_metadata():
    """Expone estaciones de servicio y pórticos de peaje con información básica."""

    metadata_query = """
        SELECT
            CONCAT('estacion_', id) AS id,
            json_build_object(
                'tipo', 'estacion_servicio',
                'nombre', nombre,
                'marca', marca,
                'direccion', direccion,
                'comuna', comuna,
                'region', region,
                'horario', horario
            ) AS properties,
            ST_AsGeoJSON(ubicacion::geometry)::json AS geometry
        FROM estaciones_servicio
        WHERE ubicacion IS NOT NULL

        UNION ALL

        SELECT
            CONCAT('portico_', p.id) AS id,
            json_build_object(
                'tipo', 'portico_peaje',
                'autopista', a.nombre,
                'tramo', a.tramo_descripcion,
                'sentido', p.sentido,
                'referencia', p.referencia_tramo,
                'longitud_km', p.longitud_km
            ) AS properties,
            ST_AsGeoJSON(p.ubicacion::geometry)::json AS geometry
        FROM porticos p
        INNER JOIN autopistas a ON a.id = p.autopista_id
        WHERE p.ubicacion IS NOT NULL;
    """

    summary_query = """
        SELECT
            (SELECT COUNT(*) FROM estaciones_servicio WHERE ubicacion IS NOT NULL) AS estaciones_servicio,
            (SELECT COUNT(*) FROM porticos WHERE ubicacion IS NOT NULL) AS porticos,
            (SELECT COUNT(*) FROM vehiculos) AS modelos_vehiculares;
    """

    geojson = _geojson_from_query(metadata_query)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(summary_query)
            summary_row = cur.fetchone() or {}

    summary = {
        "estaciones_servicio": summary_row.get("estaciones_servicio", 0),
        "porticos": summary_row.get("porticos", 0),
        "modelos_vehiculares": summary_row.get("modelos_vehiculares", 0),
    }

    return jsonify({"geojson": geojson, "summary": summary})


@app.route("/api/amenazas")
def api_amenazas():
    """Consolida amenazas recientes desde la vista `vista_amenazas_activas`."""

    query = """
        SELECT
            CONCAT(tipo, '_', row_number() OVER (ORDER BY fecha DESC, descripcion)) AS id,
            json_build_object(
                'tipo', tipo,
                'nivel_alerta', nivel_alerta,
                'descripcion', descripcion,
                'fecha', to_char(fecha, 'YYYY-MM-DD HH24:MI TZ'),
                'fecha_carga', to_char(fecha_carga, 'YYYY-MM-DD HH24:MI TZ')
            ) AS properties,
            ST_AsGeoJSON(geom)::json AS geometry
        FROM vista_amenazas_activas
        ORDER BY fecha DESC;
    """

    geojson = _geojson_from_query(query)

    resumen_query = """
        SELECT
            COALESCE(SUM((tipo = 'sismo')::INT), 0) AS sismos,
            COALESCE(SUM((tipo = 'inundacion')::INT), 0) AS inundaciones,
            COALESCE(SUM((tipo = 'incendio')::INT), 0) AS incendios,
            COALESCE(SUM((tipo = 'trafico')::INT), 0) AS trafico
        FROM vista_amenazas_activas;
    """

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(resumen_query)
            resumen_row = cur.fetchone() or {}

    summary = {
        "sismos": resumen_row.get("sismos", 0),
        "inundaciones": resumen_row.get("inundaciones", 0),
        "incendios": resumen_row.get("incendios", 0),
        "trafico": resumen_row.get("trafico", 0),
    }

    return jsonify({"geojson": geojson, "summary": summary})


def _resolve_route_nodes(conn: psycopg.Connection) -> Tuple[RouteNode, RouteNode]:
    """Determina los nodos origen/destino a partir de parámetros o usa los predeterminados."""

    start_node_id = request.args.get("start_node", type=int)
    end_node_id = request.args.get("end_node", type=int)

    if start_node_id is not None and end_node_id is not None:
        return _fetch_route_node(start_node_id, conn), _fetch_route_node(end_node_id, conn)

    # Compatibilidad con coordenadas opcionales: si llegan lat/lon, buscar nodo más cercano.
    start_lat = request.args.get("start_lat", type=float)
    start_lon = request.args.get("start_lon", type=float)
    end_lat = request.args.get("end_lat", type=float)
    end_lon = request.args.get("end_lon", type=float)

    if None not in (start_lat, start_lon, end_lat, end_lon):
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH origen AS (
                    SELECT id
                    FROM nodos_carreteras
                    ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    LIMIT 1
                ),
                destino AS (
                    SELECT id
                    FROM nodos_carreteras
                    ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    LIMIT 1
                )
                SELECT
                    (SELECT id FROM origen) AS origen_id,
                    (SELECT id FROM destino) AS destino_id;
                """,
                (start_lon, start_lat, end_lon, end_lat),
            )
            row = cur.fetchone()
        if not row or row["origen_id"] is None or row["destino_id"] is None:
            raise ValueError("No se encontraron nodos cercanos a las coordenadas proporcionadas.")
        return _fetch_route_node(row["origen_id"], conn), _fetch_route_node(row["destino_id"], conn)

    return _get_default_route_nodes(conn)


@app.route("/api/ruta-demo")
def api_ruta_demo():
    """Calcula una ruta entre dos nodos de la red vial utilizando pgr_dijkstra."""

    with get_db_connection() as conn:
        try:
            start_node, end_node = _resolve_route_nodes(conn)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        route_query = """
            WITH
            ruta AS (
                SELECT
                    d.seq,
                    d.edge,
                    d.cost,
                    a.geom
                FROM pgr_dijkstra(
                    $pgr$
                    SELECT
                        id,
                        source,
                        target,
                        costo_longitud_m AS cost,
                        costo_longitud_m AS reverse_cost
                    FROM aristas_carreteras
                    WHERE costo_longitud_m > 0
                    $pgr$,
                    %s,
                    %s,
                    directed := false
                ) AS d
                INNER JOIN aristas_carreteras a ON a.id = d.edge
                WHERE d.edge <> -1
                ORDER BY d.seq
            ),
            origen AS (
                SELECT id, ST_AsGeoJSON(geom)::json AS geom_json
                FROM nodos_carreteras
                WHERE id = %s
            ),
            destino AS (
                SELECT id, ST_AsGeoJSON(geom)::json AS geom_json
                FROM nodos_carreteras
                WHERE id = %s
            )
            SELECT
                COALESCE(SUM(cost), 0) AS total_cost_m,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON(geom)::json,
                            'properties', json_build_object(
                                'seq', seq,
                                'edge_id', edge,
                                'cost_m', cost
                            )
                        )
                        ORDER BY seq
                    ),
                    '[]'::json
                ) AS segments,
                ST_AsGeoJSON(ST_LineMerge(ST_Collect(geom)))::json AS route_geometry,
                (SELECT geom_json FROM origen) AS origen_geom,
                (SELECT geom_json FROM destino) AS destino_geom
            FROM ruta;
        """

        with conn.cursor() as cur:
            cur.execute(
                route_query,
                (
                    start_node.node_id,
                    end_node.node_id,
                    start_node.node_id,
                    end_node.node_id,
                ),
            )
            row = cur.fetchone()

    if not row:
        return jsonify({"error": "No fue posible calcular la ruta en la red vial."}), 500

    segments = row.get("segments") or []
    if isinstance(segments, str):
        segments = json.loads(segments)

    if not segments:
        return (
            jsonify(
                {
                    "error": "No existe un camino entre los nodos seleccionados.",
                    "start_node": start_node.node_id,
                    "end_node": end_node.node_id,
                }
            ),
            404,
        )

    feature_collection = {"type": "FeatureCollection", "features": segments}

    route_geometry = row.get("route_geometry")
    if isinstance(route_geometry, str):
        route_geometry = json.loads(route_geometry)

    origen_geom = row.get("origen_geom")
    destino_geom = row.get("destino_geom")
    if isinstance(origen_geom, str):
        origen_geom = json.loads(origen_geom)
    if isinstance(destino_geom, str):
        destino_geom = json.loads(destino_geom)

    total_cost_m = float(row.get("total_cost_m") or 0)
    total_length_km = round(total_cost_m / 1000, 3)

    summary = {
        "total_cost_m": total_cost_m,
        "total_length_km": total_length_km,
        "start": {
            "label": start_node.label,
            "lat": start_node.lat,
            "lon": start_node.lon,
            "node_id": start_node.node_id,
            "distance_to_request_m": 0.0,
            "geometry": origen_geom,
        },
        "end": {
            "label": end_node.label,
            "lat": end_node.lat,
            "lon": end_node.lon,
            "node_id": end_node.node_id,
            "distance_to_request_m": 0.0,
            "geometry": destino_geom,
        },
    }

    route_feature = None
    if route_geometry:
        route_feature = {
            "type": "Feature",
            "geometry": route_geometry,
            "properties": {
                "total_length_km": total_length_km,
                "segmentos": len(segments),
            },
        }

    return jsonify({"segments": feature_collection, "route": route_feature, "summary": summary})

@app.route("/api/route/calculate", methods=['GET'])
def calculate_route():
    """Calculate route between two nodes using pgr_dijkstra"""
    try:
        # Get coordinates from request
        start_lat = float(request.args.get('start_lat'))
        start_lng = float(request.args.get('start_lng'))
        end_lat = float(request.args.get('end_lat'))
        end_lng = float(request.args.get('end_lng'))

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Find nearest nodes to start/end points
                cur.execute("""
                    WITH start_point AS (
                        SELECT id, geom, 
                            ST_Distance(
                                geom::geography, 
                                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                            ) as distance
                        FROM nodos_carreteras
                        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                        LIMIT 1
                    ),
                    end_point AS (
                        SELECT id, geom,
                            ST_Distance(
                                geom::geography,
                                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                            ) as distance
                        FROM nodos_carreteras
                        ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                        LIMIT 1
                    )
                    SELECT 
                        start_point.id as start_id,
                        start_point.distance as start_distance,
                        end_point.id as end_id,
                        end_point.distance as end_distance
                    FROM start_point, end_point;
                """, (start_lng, start_lat, start_lng, start_lat, 
                      end_lng, end_lat, end_lng, end_lat))
                
                nearest = cur.fetchone()
                
                if not nearest:
                    return jsonify({"error": "No se encontraron nodos cercanos"}), 404

                # Calculate route using pgr_dijkstra
                cur.execute("""
                    WITH dijkstra AS (
                        SELECT * FROM pgr_dijkstra(
                            'SELECT id as id,
                                    source,
                                    target,
                                    costo_longitud_m as cost
                             FROM aristas_carreteras',
                            %s, %s, false)
                    )
                    SELECT 
                        json_build_object(
                            'type', 'Feature',
                            'geometry', ST_AsGeoJSON(ST_LineMerge(ST_Union(ac.geom)))::json,
                            'properties', json_build_object(
                                'length_km', SUM(d.cost)/1000.0,
                                'start_node', %s,
                                'end_node', %s
                            )
                        ) as route
                    FROM dijkstra d
                    JOIN aristas_carreteras ac ON d.edge = ac.id
                    WHERE d.edge > 0
                    GROUP BY d.start_vid, d.end_vid;
                """, (nearest['start_id'], nearest['end_id'], 
                      nearest['start_id'], nearest['end_id']))

                result = cur.fetchone()

                if not result or not result['route']:
                    return jsonify({"error": "No se encontró ruta entre los puntos"}), 404

                return jsonify(result['route'])

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run('0.0.0.0', port=5000,debug=True)