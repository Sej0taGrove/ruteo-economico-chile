import os
import psycopg2
from dotenv import load_dotenv
import json

def limpiar_y_filtrar_datos(archivo_entrada: str, archivo_salida: str):
    """
    Lee un archivo JSON, filtra las especificaciones relevantes, limpia los datos
    y los guarda en un nuevo JSON, usando 'Motor - Litros' como fuente para el tamaño del motor.
    """
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            datos_completos = json.load(f)
    except FileNotFoundError:
        print(f"Error: El archivo de entrada '{archivo_entrada}' no fue encontrado.")
        return
    # ... (resto de los try/except) ...

    # --- MAPA MODIFICADO: Quitamos 'Cilindrada' y nos quedamos con 'Motor - Litros' ---
    mapa_especificaciones_clave = {
        "Consumo combustible - mixto (km/l)": "consumo_mixto_kml",
        "Consumo combustible - urbano (km/l)": "consumo_urbano_kml",
        "Consumo combustible - extraurbano (km/l)": "consumo_extraurbano_kml",
        "Depósito de combustible - capacidad": "capacidad_estanque_litros",
        "Motor - Litros": "motor_litros",  # <-- Usaremos este como fuente de verdad
        "Transmisión": "transmision",
        "Tracción": "traccion"
    }

    campos_numericos = [
        "consumo_mixto_kml", "consumo_urbano_kml", "consumo_extraurbano_kml",
        "capacidad_estanque_litros", "motor_litros"
    ]

    data_filtrada = []

    for vehiculo in datos_completos:
        # ... (código para verificar modelo y versión) ...
        if 'modelo_base' not in vehiculo or 'version' not in vehiculo:
            continue

        especificaciones_filtradas = {}

        for clave_original, clave_nueva in mapa_especificaciones_clave.items():
            if 'especificaciones' in vehiculo and clave_original in vehiculo['especificaciones']:
                valor_original = vehiculo['especificaciones'][clave_original]

                if clave_nueva in campos_numericos:
                    try:
                        valor_str = valor_original.split()[0]
                        if not valor_str or valor_str == '-':
                            raise ValueError("No es un número válido")

                        # La lógica para kml, litros, etc., ahora se aplica a todos los numéricos
                        # Reemplazamos la coma por el punto para un formato decimal estándar
                        valor_procesado = float(valor_str.replace(',', '.'))

                        especificaciones_filtradas[clave_nueva] = valor_procesado

                    except (ValueError, IndexError):
                        especificaciones_filtradas[clave_nueva] = None
                else:
                    # Campos de texto
                    especificaciones_filtradas[clave_nueva] = valor_original.strip() if valor_original else None

        vehiculo_filtrado = {
            "modelo_base": vehiculo.get('modelo_base', 'N/A'),
            "version": vehiculo.get('version', 'N/A'),
            "especificaciones_clave": especificaciones_filtradas
        }

        data_filtrada.append(vehiculo_filtrado)

    # ... (código para guardar el JSON) ...
    try:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(data_filtrada, f, indent=4, ensure_ascii=False)
        print(
            f"\n¡Proceso completado! Se han guardado {len(data_filtrada)} vehículos con datos limpios en '{archivo_salida}'.")
    except Exception as e:
        print(f"\nOcurrió un error al guardar el archivo JSON: {e}")


load_dotenv()
def load_data_to_db():
    """
    Lee el archivo 'metadata_vehiculos.json' y carga sus datos
    en la tabla 'vehiculos' de la base de datos PostgreSQL.
    """
    try:
        # Cargar la configuración de la BD desde variables de entorno (práctica recomendada para Docker)
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host="localhost"  # 'db' es el nombre del servicio de la BD en docker-compose
        )
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        return

    # Abrir el archivo JSON
    try:
        with open('metadata_vehiculos.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'metadata_vehiculos.json'.")
        return

    # Crear un cursor para ejecutar comandos
    cur = conn.cursor()

    for vehiculo in data:
        specs = vehiculo.get('especificaciones_clave', {})

        # --- CONSULTA INSERT MODIFICADA ---
        insert_query = """
                       INSERT INTO vehiculos (modelo_base, version, consumo_mixto_kml, consumo_urbano_kml, \
                                              consumo_extraurbano_kml, capacidad_estanque_litros, motor_litros, \
                                              transmision, traccion) \
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s); \
                       """

        # --- VALORES MODIFICADOS ---
        values = (
            vehiculo.get('modelo_base'),
            vehiculo.get('version'),
            specs.get('consumo_mixto_kml'),
            specs.get('consumo_urbano_kml'),
            specs.get('consumo_extraurbano_kml'),
            specs.get('capacidad_estanque_litros'),
            specs.get('motor_litros'),  # <-- Usamos el nuevo campo
            specs.get('transmision'),
            specs.get('traccion')
        )

        cur.execute(insert_query, values)

    # Confirmar los cambios en la base de datos
    conn.commit()

    # Cerrar la comunicación
    cur.close()
    conn.close()

    print(f"¡Carga completada! Se insertaron {len(data)} registros en la tabla 'vehiculos'.")


# --- Ejecución del script ---
if __name__ == "__main__":
    nombre_archivo_original = 'chileautos_data.json'
    nombre_archivo_final = 'metadata_vehiculos.json'
    limpiar_y_filtrar_datos(nombre_archivo_original, nombre_archivo_final)
    load_data_to_db()