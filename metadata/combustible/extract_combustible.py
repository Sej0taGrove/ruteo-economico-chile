import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

class ExtractorCombustibleCNE:
    def __init__(self):
        load_dotenv()
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        self.token = os.getenv("CNE_API_TOKEN")
        if not self.token:
            raise ValueError("La variable CNE_API_TOKEN no está definida en el archivo .env.")
        self.url_api = f"https://api.cne.cl/api/v4/estaciones?token={self.token}"
        self.headers = {'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}

    def extraer_datos_cne(self):
        print("Conectando con la API de la CNE...")
        try:
            respuesta = requests.get(self.url_api, headers=self.headers)
            respuesta.raise_for_status()
            datos_json = respuesta.json()
            if isinstance(datos_json, list):
                print(f"Datos recibidos exitosamente. Se encontraron {len(datos_json)} registros de estaciones.")
                return datos_json
            else:
                print(f"Error: La respuesta de la API no fue una lista. Verifica el token. Respuesta: {datos_json}")
                return None
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Error crítico al consultar o decodificar la API de la CNE: {e}")
            return None

    def procesar_estaciones(self, datos_raw):
        if not isinstance(datos_raw, list): return []

        estaciones_procesadas = {} # Usar un diccionario para manejar duplicados por 'codigo'
        for estacion in datos_raw:
            try:
                codigo = estacion.get("codigo")
                if not codigo: continue

                # Si la estación ya existe, solo actualizamos precios si es necesario
                if codigo in estaciones_procesadas and estacion.get('precios'):
                    estaciones_procesadas[codigo]['combustibles'].update(self._extraer_precios(estacion))
                    continue

                if codigo in estaciones_procesadas:
                    continue

                ubicacion = estacion.get('ubicacion', {})
                lat_str = str(ubicacion.get("latitud", "")).replace(',', '.')
                lon_str = str(ubicacion.get("longitud", "")).replace(',', '.')

                estacion_info = {
                    "id_estacion": codigo,
                    "nombre": estacion.get("razon_social", "Sin Nombre").strip(),
                    "direccion": ubicacion.get("direccion", "").strip(),
                    "comuna": ubicacion.get("nombre_comuna", ""),
                    "region": ubicacion.get("nombre_region", ""),
                    "latitud": float(lat_str) if lat_str else None,
                    "longitud": float(lon_str) if lon_str else None,
                    "marca": estacion.get('distribuidor', {}).get("marca", "Sin Bandera"),
                    "horario": estacion.get("horario_atencion", "No informado"),
                    "combustibles": self._extraer_precios(estacion),
                    "fecha_actualizacion": datetime.now().isoformat()
                }
                estaciones_procesadas[codigo] = estacion_info

            except (ValueError, TypeError) as e:
                print(f"Advertencia: Saltando estación por datos inválidos (ID: {estacion.get('codigo', 'N/A')}). Error: {e}")
                continue

        final_list = list(estaciones_procesadas.values())
        print(f"Se procesaron {len(final_list)} estaciones únicas y válidas.")
        return final_list

    def _extraer_precios(self, estacion_data):
        combustibles_dict = {}
        for key, val in estacion_data.get('precios', {}).items():
            if isinstance(val, dict) and 'precio' in val:
                try:
                    precio_limpio = int(float(str(val['precio']).replace('.', '')))
                    combustibles_dict[key] = precio_limpio
                except (ValueError, TypeError):
                    continue
        return combustibles_dict

    def guardar_resultados(self, estaciones_data):
        timestamp_str = datetime.now().strftime("%Y-%m-%d")
        filename_json = f"combustible_metadata_{timestamp_str}.json"
        filepath_json = os.path.join(self.output_dir, filename_json)

        final_data = {
            "metadata": { "fuente": "CNE", "fecha_extraccion": timestamp_str, "total_estaciones": len(estaciones_data) },
            "estaciones": estaciones_data
        }

        with open(filepath_json, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        print(f"Archivo JSON generado exitosamente en: {filepath_json}")
        return filepath_json

    def ejecutar(self):
        datos_crudos = self.extraer_datos_cne()
        if datos_crudos:
            estaciones_procesadas = self.procesar_estaciones(datos_crudos)
            if estaciones_procesadas:
                return self.guardar_resultados(estaciones_procesadas)
        return None

if __name__ == "__main__":
    extractor = ExtractorCombustibleCNE()
    if not extractor.ejecutar():
        print("El proceso de extracción de combustibles falló.")