import os
import sys
import subprocess
from pathlib import Path

import ijson
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch
from dotenv import load_dotenv


def node_generator(json_path: Path):
    """Yield nodes without loading the full JSON into memory."""
    with open(json_path, "rb") as file_handle:
        for nodo in ijson.items(file_handle, "nodos.item"):
            yield nodo["id"], nodo["lon"], nodo["lat"]


def edge_generator(json_path: Path):
    """Yield edges without loading the full JSON into memory."""
    with open(json_path, "rb") as file_handle:
        for arista in ijson.items(file_handle, "aristas.item"):
            coords = ", ".join(f"{lon} {lat}" for lon, lat in arista["geom"])
            linestring_wkt = f"LINESTRING({coords})"
            yield arista["source"], arista["target"], arista["costo_longitud_m"], linestring_wkt


def table_has_rows(cursor, table_name: str) -> bool:
    cursor.execute(sql.SQL("SELECT EXISTS (SELECT 1 FROM {} LIMIT 1)").format(sql.Identifier(table_name)))
    return bool(cursor.fetchone()[0])


def file_exists_and_not_empty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def ensure_infrastructure_json_exists(json_path: Path) -> bool:
    """
    Verifica que el archivo JSON de infraestructura exista.
    Si no existe, intenta ejecutar extract_transform_infra.py para generarlo.
    
    Returns:
        True si el archivo existe o se generó exitosamente
        False si hubo un error
    """
    if file_exists_and_not_empty(json_path):
        print(f"Archivo de infraestructura encontrado: {json_path}")
        return True
    
    print(f"No se encontró '{json_path}'.")
    print("Intentando generar el archivo ejecutando 'extract_transform_infra.py'...")
    
    extract_script = json_path.parent / "extract_transform_infra.py"
    
    if not extract_script.exists():
        print(f"ERROR: No se encontró el script de extracción: {extract_script}")
        return False
    
    try:
        # Ejecutar el script de extracción
        result = subprocess.run(
            [sys.executable, str(extract_script)],
            cwd=str(extract_script.parent),
            check=True,
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        # Verificar que se haya generado el archivo
        if file_exists_and_not_empty(json_path):
            print(f"Archivo de infraestructura generado exitosamente: {json_path}")
            return True
        else:
            print(f"ERROR: El script se ejecutó pero no generó el archivo esperado.")
            return False
            
    except subprocess.CalledProcessError as exc:
        print(f"ERROR al ejecutar extract_transform_infra.py:")
        print(exc.stderr)
        return False
    except Exception as exc:
        print(f"ERROR inesperado: {exc}")
        return False


def load_infrastructure_to_db(json_path: Path) -> bool:
    """
    Load road infrastructure from the JSON file using batched inserts.
    Returns True when the load completes or is skipped because data already exists.
    Returns False if an error occurs or the input file is missing.
    """
    load_dotenv()

    force_refresh = any(
        os.getenv(var, "").lower() in {"1", "true", "yes"} for var in ("FORCE_REFRESH_INFRA", "FORCE_REFRESH")
    )

    json_path = Path(json_path)

    # Conectar a la base de datos
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
    except psycopg2.Error as exc:
        print(f"Error al conectar con la base de datos: {exc}")
        return False

    try:
        with conn:
            with conn.cursor() as cur:
                nodos_presentes = table_has_rows(cur, "nodos_carreteras")
                aristas_presentes = table_has_rows(cur, "aristas_carreteras")

                # Si ya hay datos y no se fuerza refresh, saltar
                if nodos_presentes and aristas_presentes and not force_refresh:
                    print(
                        "Las tablas nodos_carreteras y aristas_carreteras ya contienen datos. "
                        "Se omite la carga (usa FORCE_REFRESH_INFRA=1 para forzar)."
                    )
                    return True

                # Verificar/generar el archivo JSON si es necesario
                if not ensure_infrastructure_json_exists(json_path):
                    print(
                        f"No se pudo obtener el archivo de infraestructura. "
                        "Verifica que extract_transform_infra.py esté disponible y funcione correctamente."
                    )
                    return False

                print("Vaciando tablas de infraestructura (nodos_carreteras, aristas_carreteras)...")
                cur.execute("TRUNCATE TABLE nodos_carreteras, aristas_carreteras RESTART IDENTITY CASCADE;")

                print("Insertando nodos (esto puede tardar varios minutos)...")
                execute_batch(
                    cur,
                    "INSERT INTO nodos_carreteras (id, geom) VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326));",
                    node_generator(json_path),
                    page_size=5000,
                )

                print("Insertando aristas (esto puede tardar varios minutos)...")
                execute_batch(
                    cur,
                    (
                        "INSERT INTO aristas_carreteras (source, target, costo_longitud_m, geom) "
                        "VALUES (%s, %s, %s, ST_GeomFromText(%s, 4326));"
                    ),
                    edge_generator(json_path),
                    page_size=5000,
                )

        print("Carga de datos de infraestructura completada con exito.")
        return True
    except (Exception, psycopg2.Error) as exc:
        print(f"Error durante la carga de infraestructura: {exc}")
        return False
    finally:
        if conn:
            conn.close()
            print("Conexion a la base de datos cerrada.")


if __name__ == "__main__":
    json_file_path = Path(__file__).resolve().parent / "infraestructura.json"
    success = load_infrastructure_to_db(json_file_path)
    sys.exit(0 if success else 1)