import json
import os
import psycopg2
from dotenv import load_dotenv


def load_peajes_data():
    """
    Lee los archivos de precios y georreferencias de peajes, los procesa
    y carga los datos consolidados en la base de datos PostgreSQL en una sola ejecución.
    """
    load_dotenv()
    conn = None
    cur = None

    try:
        # --- 1. PRE-CARGAR DATOS DE GEORREFERENCIAS EN MEMORIA ---
        print("Cargando archivo de georreferencias en memoria...")
        with open('peajes_georeferencias_2025-10-10.json', 'r', encoding='utf-8') as f:
            geo_data = json.load(f)

        # Crear un diccionario para búsqueda rápida: { 'nombre_normalizado': {lat: ..., lon: ...} }
        geo_locations = {
            peaje['nombre'].lower().strip(): {
                'latitude': peaje['latitude'],
                'longitude': peaje['longitude']
            }
            for peaje in geo_data['peajes'] if peaje.get('nombre')
        }
        print(f"Se cargaron {len(geo_locations)} ubicaciones de peajes.")

        # --- 2. CONECTAR A LA BASE DE DATOS ---
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432")
        )
        cur = conn.cursor()
        print("Conexión a la base de datos para peajes exitosa.")

        # Vaciar tablas para una carga limpia
        print("Vaciando tablas de peajes (autopistas, porticos, peajes)...")
        cur.execute("TRUNCATE TABLE peajes, porticos, autopistas RESTART IDENTITY CASCADE;")

        # --- 3. LEER Y PROCESAR EL JSON DE PRECIOS ---
        with open('precios.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for autopista_data in data['autopistas']:
            nombre_autopista = autopista_data['nombre_autopista']
            print(f"\nProcesando autopista: {nombre_autopista}...")

            cur.execute(
                "INSERT INTO autopistas (nombre, tramo_descripcion, año_tarifas) VALUES (%s, %s, %s) RETURNING id;",
                (nombre_autopista, autopista_data.get('tramo_descripcion'), autopista_data.get('año_tarifas'))
            )
            autopista_id = cur.fetchone()[0]

            for eje in autopista_data.get('ejes', []):
                if 'direcciones' in eje:
                    for direccion in eje['direcciones']:
                        for portico_info in direccion.get('porticos', []):
                            insert_portico_and_peajes(cur, autopista_id, eje, direccion, portico_info, geo_locations)
                elif 'tramos' in eje:
                    for tramo_info in eje['tramos']:
                        portico_simulado = {
                            'portico_id': f"{tramo_info.get('portico_entrada', '')}-{tramo_info.get('portico_salida', '')}",
                            'referencia_tramo': f"{tramo_info.get('portico_entrada')} - {tramo_info.get('portico_salida')}",
                            'longitud_km': tramo_info.get('longitud_km'),
                            'peajes': tramo_info.get('peajes'),
                            'horarios': eje.get('horarios', {})
                        }
                        insert_portico_and_peajes(cur, autopista_id, eje, {}, portico_simulado, geo_locations)
                elif 'porticos' in eje:
                    for portico_info in eje['porticos']:
                        portico_info['referencia_tramo'] = portico_info.get('nombre')
                        insert_portico_and_peajes(cur, autopista_id, eje, {}, portico_info, geo_locations)
                elif 'usuarios_con_tag' in eje:
                    parse_tunel_san_cristobal(cur, autopista_id, eje, geo_locations)
                elif 'tarifas' in eje:
                    parse_tarifas_simples(cur, autopista_id, eje, geo_locations)

        conn.commit()
        print("\n¡Carga de datos de peajes completada exitosamente!")

    except (Exception, psycopg2.Error) as error:
        print(f"\nError durante el proceso: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            if cur:
                cur.close()
            conn.close()
            print("Conexión a la base de datos cerrada.")


def find_location(portico_info, geo_locations):
    """Intenta encontrar una ubicación geográfica para un pórtico basado en su nombre o ID."""
    # Normalizar nombres para la búsqueda
    portico_id_c = (portico_info.get('portico_id') or "").lower().strip()
    ref_tramo = (portico_info.get('referencia_tramo') or "").lower().strip()

    # Estrategia 1: Búsqueda por ID de concesión si existe (ej. 'p9', 'pa2')
    if portico_id_c and portico_id_c in geo_locations:
        return geo_locations[portico_id_c]

    # Estrategia 2: Búsqueda por coincidencia exacta del nombre/tramo
    if ref_tramo and ref_tramo in geo_locations:
        return geo_locations[ref_tramo]

    # Estrategia 3: Búsqueda parcial (el nombre del peaje geo está contenido en la referencia del tramo)
    for geo_nombre, coords in geo_locations.items():
        if geo_nombre in ref_tramo:
            return coords

    return None


def parse_schedule_key(key):
    """Parsea una clave de horario (ej: 'punta_laboral_tbp') en tipo_tarifa y tipo_dia."""
    tipo_tarifa = None
    tipo_dia = " ".join(key.split('_')[:-1]).replace('_', ' ').capitalize()

    if key.endswith('_ts'):
        tipo_tarifa = 'TS'
    elif key.endswith('_tbp'):
        tipo_tarifa = 'TBP'
    elif key.endswith('_tbfp'):
        tipo_tarifa = 'TBFP'

    return tipo_tarifa, tipo_dia


def insert_portico_and_peajes(cur, autopista_id, eje, direccion, portico_info, geo_locations):
    """Inserta un pórtico (incluyendo su ubicación si se encuentra) y todos sus precios asociados."""

    # 1. Buscar la ubicación del pórtico
    location = find_location(portico_info, geo_locations)

    # 2. Insertar el pórtico en la base de datos
    cur.execute(
        """
        INSERT INTO porticos (autopista_id, portico_id_concesion, nombre_eje, sentido, referencia_tramo, longitud_km,
                              ubicacion)
        VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) RETURNING id;
        """,
        (
            autopista_id,
            portico_info.get('portico_id'),
            eje.get('nombre_eje'),
            direccion.get('sentido'),
            portico_info.get('referencia_tramo'),
            portico_info.get('longitud_km'),
            location['longitude'] if location else None,
            location['latitude'] if location else None
        )
    )
    portico_id_db = cur.fetchone()[0]

    # 3. Procesar horarios para asociarlos a las tarifas
    schedules = {}
    horarios_obj = portico_info.get('horarios', {})
    for key, time_ranges in horarios_obj.items():
        tipo_tarifa, tipo_dia = parse_schedule_key(key)
        if tipo_tarifa and time_ranges:
            if tipo_tarifa not in schedules: schedules[tipo_tarifa] = []
            for time_range in time_ranges:
                schedules[tipo_tarifa].append({'tipo_dia': tipo_dia, 'horario': time_range})

    # 4. Iterar sobre los precios y guardarlos en la BD
    peajes = portico_info.get('peajes', {})
    for categoria, tarifas in peajes.items():
        if isinstance(tarifas, dict):
            for tipo_tarifa, valor in tarifas.items():
                if valor is not None:
                    if tipo_tarifa in schedules:
                        for schedule in schedules[tipo_tarifa]:
                            cur.execute(
                                "INSERT INTO peajes (portico_id, categoria_vehiculo, tipo_tarifa, valor, tipo_dia, horario) VALUES (%s, %s, %s, %s, %s, %s);",
                                (portico_id_db, categoria, tipo_tarifa, valor, schedule['tipo_dia'],
                                 schedule['horario'])
                            )
                    else:
                        cur.execute(
                            "INSERT INTO peajes (portico_id, categoria_vehiculo, tipo_tarifa, valor) VALUES (%s, %s, %s, %s);",
                            (portico_id_db, categoria, tipo_tarifa, valor)
                        )
        elif tarifas is not None:
            cur.execute(
                "INSERT INTO peajes (portico_id, categoria_vehiculo, tipo_tarifa, valor) VALUES (%s, %s, %s, %s);",
                (portico_id_db, categoria, 'NORMAL', tarifas)
            )


def parse_tunel_san_cristobal(cur, autopista_id, eje, geo_locations):
    """Función específica para la estructura compleja del Túnel San Cristóbal."""
    # (Esta lógica asume que el túnel es un único "pórtico" por sentido)
    for tipo_usuario, data_usuario in eje.items():
        if 'tarifas' in str(tipo_usuario):
            for tarifa_info in data_usuario:
                sentido = tarifa_info.get('sentido')

                portico_info_simulado = {'referencia_tramo': f"Túnel San Cristóbal {sentido}"}
                location = find_location(portico_info_simulado, geo_locations)

                cur.execute(
                    "INSERT INTO porticos (autopista_id, nombre_eje, sentido, referencia_tramo, ubicacion) VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) RETURNING id;",
                    (autopista_id, eje.get('nombre_eje'), sentido, f"{sentido} ({tipo_usuario})",
                     location['longitude'] if location else None, location['latitude'] if location else None)
                )
                portico_id_db = cur.fetchone()[0]

                for categoria, valor in tarifa_info.get('peajes', {}).items():
                    if valor is not None:
                        cur.execute(
                            "INSERT INTO peajes (portico_id, categoria_vehiculo, tipo_tarifa, valor, tipo_dia, horario) VALUES (%s, %s, %s, %s, %s, %s);",
                            (portico_id_db, categoria, tarifa_info.get('tipo_tarifa'), valor,
                             tarifa_info.get('tipo_dia'), tarifa_info.get('horario'))
                        )


def parse_tarifas_simples(cur, autopista_id, eje, geo_locations):
    """Función para autopistas con una lista simple de 'tarifas'."""

    portico_info_simulado = {'referencia_tramo': eje.get('nombre_eje')}
    location = find_location(portico_info_simulado, geo_locations)

    cur.execute(
        "INSERT INTO porticos (autopista_id, nombre_eje, referencia_tramo, ubicacion) VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) RETURNING id;",
        (autopista_id, eje.get('nombre_eje'), eje.get('nombre_eje'), location['longitude'] if location else None,
         location['latitude'] if location else None)
    )
    portico_id_db = cur.fetchone()[0]

    for tarifa_info in eje['tarifas']:
        tipo_tarifa = tarifa_info.get('tipo', 'NORMAL')
        for categoria, valor in tarifa_info.get('peajes', {}).items():
            if valor is not None:
                cur.execute(
                    "INSERT INTO peajes (portico_id, categoria_vehiculo, tipo_tarifa, valor) VALUES (%s, %s, %s, %s);",
                    (portico_id_db, categoria, tipo_tarifa, valor)
                )


if __name__ == "__main__":
    load_peajes_data()