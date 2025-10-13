import requests
import json
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv


class ExtractorCombustibleCNE:
    def __init__(self):
        load_dotenv()
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        self.token = os.getenv("CNE_API_TOKEN")
        if not self.token:
            raise ValueError("La variable CNE_API_TOKEN no está definida en el archivo .env. Obtén uno nuevo.")
        self.url_api = f"https://api.cne.cl/api/v4/estaciones?token={self.token}"
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def extraer_datos_cne(self):
        print("Conectando con la API de la CNE...")
        try:
            respuesta = requests.get(self.url_api, headers=self.headers)
            respuesta.raise_for_status()
            datos_json = respuesta.json()

            # --- CORRECCIÓN FINAL: La API devuelve una lista directamente ---
            if isinstance(datos_json, list):
                print(f"Datos recibidos exitosamente. Se encontraron {len(datos_json)} estaciones.")
                return datos_json
            else:
                # Esto podría pasar si el token expira y la API devuelve un objeto de error
                print("Error: La respuesta de la API no fue una lista como se esperaba.")
                print(f"Respuesta del servidor: {datos_json}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Ocurrió un error en la solicitud: {e}")
            return None
        except json.JSONDecodeError:
            print("Error al decodificar la respuesta JSON. Token expirado o respuesta inválida.")
            return None

    def procesar_estaciones(self, datos_raw):
        if not isinstance(datos_raw, list):
            print("Error: Los datos a procesar no son una lista.")
            return []

        estaciones_procesadas = []
        for estacion in datos_raw:
            try:
                ubicacion = estacion.get('ubicacion', {})
                distribuidor = estacion.get('distribuidor', {})

                combustibles_dict = {}
                for key, val in estacion.get('precios', {}).items():
                    if isinstance(val, dict) and 'precio' in val:
                        try:
                            # Limpia el precio: "1310.000" -> 1310
                            precio_limpio = float(val['precio'].replace('.', ''))
                            combustibles_dict[key] = int(precio_limpio)
                        except (ValueError, TypeError):
                            continue

                estacion_info = {
                    "id_estacion": estacion.get("codigo", ""),
                    "nombre": estacion.get("razon_social", "Sin Nombre").strip(),
                    "direccion": ubicacion.get("direccion", "").strip(),
                    "comuna": ubicacion.get("nombre_comuna", ""),
                    "region": ubicacion.get("nombre_region", ""),
                    "latitud": float(ubicacion.get("latitud")) if ubicacion.get("latitud") else None,
                    "longitud": float(ubicacion.get("longitud")) if ubicacion.get("longitud") else None,
                    "marca": distribuidor.get("marca", "Sin Bandera"),
                    "horario": estacion.get("horario_atencion", "No informado"),
                    "servicios": estacion.get("servicios", {}),
                    "combustibles": combustibles_dict,
                    "fecha_actualizacion": datetime.now().isoformat()
                }
                estaciones_procesadas.append(estacion_info)

            except (ValueError, TypeError) as e:
                print(f"Saltando estación por datos inválidos (ID: {estacion.get('codigo', 'N/A')}). Error: {e}")
                continue

        print(f"Se procesaron {len(estaciones_procesadas)} estaciones con éxito.")
        return estaciones_procesadas

    def guardar_resultados(self, estaciones_data):
        timestamp_str = datetime.now().strftime("%Y-%m-%d")
        filename_json = f"combustible_metadata_{timestamp_str}.json"
        filepath_json = os.path.join(self.output_dir, filename_json)

        final_data = {
            "metadata": {
                "fuente": "CNE - Comisión Nacional de Energía",
                "fecha_extraccion": timestamp_str,
                "total_estaciones": len(estaciones_data)
            },
            "estaciones": estaciones_data
        }

        try:
            with open(filepath_json, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            print(f"Archivo JSON generado exitosamente en: {filepath_json}")
            return filepath_json
        except Exception as e:
            print(f"Error al guardar el archivo JSON: {e}")
            return None

    def ejecutar(self):
        datos_crudos = self.extraer_datos_cne()
        if datos_crudos:
            estaciones_procesadas = self.procesar_estaciones(datos_crudos)
            if estaciones_procesadas:
                return self.guardar_resultados(estaciones_procesadas)
        return None


def main():
    extractor = ExtractorCombustibleCNE()
    resultado = extractor.ejecutar()

    if not resultado:
        print("El proceso de extracción de combustibles falló.")


if __name__ == "__main__":
    main()