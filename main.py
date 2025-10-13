import subprocess
import os

def run_step(step_name, command):
    print(f"\\n--- PASO: {step_name} ---\\n")
    try:
        # Ejecutar el comando. Se mostrará la salida en tiempo real.
        subprocess.run(command, shell=True, check=True, text=True)
        print(f"\\n--- {step_name} FINALIZADO CON ÉXITO ---\\n")
    except subprocess.CalledProcessError as e:
        print(f"\\n--- ERROR en {step_name}: El script falló con el código de salida {e.returncode} ---")
        # Opcional: decidir si detener todo el proceso o continuar
        # exit(1) # Descomentar para detener el flujo completo si un paso falla
    except Exception as e:
        print(f"\\n--- ERROR INESPERADO en {step_name}: {e} ---")

def main():
    print("=============================================")
    print("=  INICIANDO PROCESO ETL COMPLETO           =")
    print("=============================================")

    # --- PASO 1: VEHÍCULOS ---
    run_step("Extracción y Transformación de Vehículos", "python3 metadata/vehiculos/scraper-chileautos.py && python3 metadata/vehiculos/transform_vehiculos.py")
    run_step("Carga de Vehículos", "python3 metadata/vehiculos/load_vehiculos.py")

    # --- PASO 2: COMBUSTIBLES ---
    run_step("Extracción y Transformación de Combustibles", "python3 metadata/combustible/extract_combustible.py")
    run_step("Carga de Combustibles", "python3 metadata/combustible/load_combustible_data.py")

    # --- PASO 3: PEAJES ---
    run_step("Extracción y Transformación de Peajes", "python3 metadata/peajes/extract_georef_peajes.py && python3 metadata/peajes/procesar_precios.py")
    run_step("Carga de Peajes", "python3 metadata/peajes/load_peajes_to_db.py")

    # --- PASO 4: INFRAESTRUCTURA DE CARRETERAS ---
    # Nota: Este paso es muy largo y sensible a interrupciones.
    run_step("Extracción y Transformación de Infraestructura", "python3 infraestructura/extract_transform_infra.py")
    run_step("Carga de Infraestructura a la BD", "python3 infraestructura/load_infra_to_db.py")

    # --- PASO 5: AMENAZAS ---
    run_step("Extracción de Amenazas (Incendios, Inundaciones, Sismos, Congestión)",
             "python3 amenazas/incendios/incendios_nasa.py && "
             "python3 amenazas/inundaciones/inundaciones_dga.py && "
             "python3 amenazas/sismos/sismos_usgs.py && "
             "python3 amenazas/congestion/extract_transform_congestion.py")
    run_step("Carga de Todas las Amenazas a la BD", "python3 amenazas/load_amenazas.py")

    print("\\n=============================================")
    print("=  PROCESO ETL FINALIZADO                     =")
    print("=============================================")

if __name__ == "__main__":
    main()