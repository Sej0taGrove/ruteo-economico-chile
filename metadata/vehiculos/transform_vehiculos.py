# Archivo: Metadata/vehiculos/transform_vehiculos.py
import json
import os


# --- Lógica de la función limpiar_y_filtrar_datos (sin cambios) ---
def limpiar_y_filtrar_datos(archivo_entrada: str, archivo_salida: str):
    # ... (El código de esta función es idéntico al que ya tenías) ...
    # ... (Lo he omitido aquí por brevedad, solo cópialo y pégalo)
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            datos_completos = json.load(f)
    except FileNotFoundError:
        print(f"Error: El archivo de entrada '{archivo_entrada}' no fue encontrado.")
        return

    mapa_especificaciones_clave = {
        "Consumo combustible - mixto (km/l)": "consumo_mixto_kml",
        "Consumo combustible - urbano (km/l)": "consumo_urbano_kml",
        "Consumo combustible - extraurbano (km/l)": "consumo_extraurbano_kml",
        "Depósito de combustible - capacidad": "capacidad_estanque_litros",
        "Motor - Litros": "motor_litros",
        "Transmisión": "transmision",
        "Tracción": "traccion"
    }
    campos_numericos = [
        "consumo_mixto_kml", "consumo_urbano_kml", "consumo_extraurbano_kml",
        "capacidad_estanque_litros", "motor_litros"
    ]
    data_filtrada = []

    for vehiculo in datos_completos:
        if 'modelo_base' not in vehiculo or 'version' not in vehiculo:
            continue
        especificaciones_filtradas = {}
        for clave_original, clave_nueva in mapa_especificaciones_clave.items():
            if 'especificaciones' in vehiculo and clave_original in vehiculo['especificaciones']:
                valor_original = vehiculo['especificaciones'][clave_original]
                if clave_nueva in campos_numericos:
                    try:
                        valor_str = valor_original.split()[0]
                        if not valor_str or valor_str == '-': raise ValueError("No es un número válido")
                        valor_procesado = float(valor_str.replace(',', '.'))
                        especificaciones_filtradas[clave_nueva] = valor_procesado
                    except (ValueError, IndexError):
                        especificaciones_filtradas[clave_nueva] = None
                else:
                    especificaciones_filtradas[clave_nueva] = valor_original.strip() if valor_original else None

        vehiculo_filtrado = {
            "modelo_base": vehiculo.get('modelo_base', 'N/A'),
            "version": vehiculo.get('version', 'N/A'),
            "especificaciones_clave": especificaciones_filtradas
        }
        data_filtrada.append(vehiculo_filtrado)

    try:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(data_filtrada, f, indent=4, ensure_ascii=False)
        print(
            f"\n¡Proceso completado! Se han guardado {len(data_filtrada)} vehículos con datos limpios en '{archivo_salida}'.")
    except Exception as e:
        print(f"\nOcurrió un error al guardar el archivo JSON: {e}")


if __name__ == "__main__":
    # Usar rutas relativas al script para que funcione desde cualquier lugar
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    archivo_original = os.path.join(SCRIPT_DIR, 'chileautos_data.json')
    archivo_final = os.path.join(SCRIPT_DIR, 'metadata_vehiculos.json')

    print("Iniciando la transformación de datos de vehículos...")
    limpiar_y_filtrar_datos(archivo_original, archivo_final)