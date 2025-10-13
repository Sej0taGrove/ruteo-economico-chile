import os
import psycopg2
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv


def get_db_connection():
    """Establece la conexión con la base de datos."""
    # python-dotenv buscará el archivo .env subiendo en el árbol de directorios
    load_dotenv()
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None


def get_road_segments(conn, limit=50):
    """
    Obtiene una muestra de segmentos de carretera (aristas) de la base de datos
    junto con las coordenadas de sus nodos de inicio y fin.
    """
    query = """
            SELECT a.id, \
                   ST_Y(n_inicio.geom)  as lat_inicio, \
                   ST_X(n_inicio.geom)  as lon_inicio, \
                   ST_Y(n_fin.geom)     as lat_fin, \
                   ST_X(n_fin.geom)     as lon_fin, \
                   ST_AsGeoJSON(a.geom) as a_geom
            FROM aristas_carreteras a
                     JOIN nodos_carreteras n_inicio ON a.source = n_inicio.id
                     JOIN nodos_carreteras n_fin ON a.target = n_fin.id
            WHERE a.costo_longitud_m > 500 -- Filtramos segmentos muy cortos para obtener mejores datos
            ORDER BY RANDOM() -- Tomamos una muestra aleatoria para no consultar siempre los mismos
                LIMIT %s; \
            """
    with conn.cursor() as cur:
        cur.execute(query, (limit,))
        return cur.fetchall()


def get_travel_time(api_key, origin, destination, departure_time="now"):
    """
    Consulta la API de Google Directions para obtener el tiempo de viaje.
    'departure_time' puede ser "now" o un timestamp futuro para estimar sin tráfico.
    """
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin['lat']},{origin['lon']}",
        "destination": f"{destination['lat']},{destination['lon']}",
        "departure_time": departure_time,
        "traffic_model": "best_guess",  # Modelo de tráfico más realista
        "key": api_key
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['status'] == 'OK':
            return data['routes'][0]['legs'][0]['duration_in_traffic']['value']
    except requests.exceptions.RequestException as e:
        print(f"Error en la llamada a la API de Google: {e}")
    except (KeyError, IndexError):
        print(f"Respuesta inesperada de la API de Google: {data}")

    return None


def main():
    load_dotenv()
    API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    if not API_KEY:
        print("Error: La variable GOOGLE_MAPS_API_KEY no está definida en el archivo .env.")
        return

    conn = get_db_connection()
    if not conn:
        return

    # NOTA: Para una prueba real, puedes aumentar el límite (ej. 100 o más).
    # Para empezar, 25 es un buen número para no gastar la cuota de la API.
    segments = get_road_segments(conn, limit=25)
    conn.close()

    congestion_data = []

    # Preparamos un tiempo futuro para estimar el viaje sin tráfico (ej. 3 AM del próximo día)
    now = datetime.now()
    future_time = (now + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
    future_timestamp = int(future_time.timestamp())

    print(f"Analizando {len(segments)} segmentos de carretera para medir congestión...")

    for i, (edge_id, lat_inicio, lon_inicio, lat_fin, lon_fin, geom) in enumerate(segments):
        origin = {"lat": lat_inicio, "lon": lon_inicio}
        destination = {"lat": lat_fin, "lon": lon_fin}

        print(f"Segmento {i + 1}/{len(segments)} (ID de arista: {edge_id})... ", end="")

        # 1. Obtener tiempo de viaje AHORA (con tráfico)
        time_with_traffic = get_travel_time(API_KEY, origin, destination, departure_time="now")

        # 2. Obtener tiempo de viaje FUTURO (sin tráfico, ideal)
        time_without_traffic = get_travel_time(API_KEY, origin, destination, departure_time=future_timestamp)

        if time_with_traffic and time_without_traffic and time_without_traffic > 0:
            # Cálculo del factor de congestión
            congestion_factor = (time_with_traffic / time_without_traffic)
            congestion_data.append({
                "arista_id": edge_id,
                "factor_congestion": round(congestion_factor, 4),
                "tiempo_con_trafico_seg": time_with_traffic,
                "tiempo_sin_trafico_seg": time_without_traffic,
                "fecha_medicion": now.isoformat(),
                "geom": geom
            })
            print(f"Factor: {congestion_factor:.2f}")
        else:
            print("No se pudo calcular (revisar respuesta de la API).")

    # Guardar resultados en un archivo JSON en la misma carpeta
    output_dir = os.path.dirname(os.path.realpath(__file__))
    timestamp_str = now.strftime("%Y-%m-%d")
    filepath = os.path.join(output_dir, f'congestion_metadata_{timestamp_str}.json')

    final_output = {
        "metadata": {
            "fuente": "Google Directions API",
            "fecha_extraccion": timestamp_str,
            "descripcion": "Factor de congestión en segmentos de carretera seleccionados."
        },
        "congestion_data": congestion_data
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

    print(f"\n¡Proceso completado! Archivo guardado en: {filepath}")


if __name__ == "__main__":
    main()