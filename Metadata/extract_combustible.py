#!/usr/bin/env python3

import requests
import json
import pandas as pd
from datetime import datetime
import os

class ExtractorCombustibleCNE:
    def __init__(self):
        self.output_dir = "../database"
        self.token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vYXBpLmNuZS5jbC9hcGkvbG9naW4iLCJpYXQiOjE3NjAxNTEzNzQsImV4cCI6MTc2MDE1NDk3NCwibmJmIjoxNzYwMTUxMzc0LCJqdGkiOiJFdFllMUFjNFJ6Y201ZDN5Iiwic3ViIjoiMzc0MSIsInBydiI6IjIzYmQ1Yzg5NDlmNjAwYWRiMzllNzAxYzQwMDg3MmRiN2E1OTc2ZjcifQ.9EdGubB-K41wTomswM0zwdHVa3NBOy9vR95eu_-GBIo"
        self.url_api = f"https://api.cne.cl/api/v4/estaciones?token={self.token}"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def extraer_datos_cne(self):
        try:
            respuesta = requests.get(self.url_api)
            
            if respuesta.status_code == 200:
                datos_json = respuesta.json()
                return datos_json
            else:
                print(f"Error al conectar con la API. Código de estado: {respuesta.status_code}")
                print(f"Respuesta del servidor: {respuesta.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Ocurrió un error en la solicitud: {e}")
            return None
    
    def procesar_estaciones(self, datos_raw):
        estaciones_procesadas = []
        
        if not isinstance(datos_raw, list):
            return estaciones_procesadas
        
        for estacion in datos_raw:
            try:
                # Procesar servicios
                servicios_dict = {}
                if isinstance(estacion.get("servicios"), list):
                    for servicio in estacion.get("servicios", []):
                        if isinstance(servicio, str):
                            servicios_dict[servicio] = True
                        elif isinstance(servicio, dict) and servicio.get("nombre"):
                            servicios_dict[servicio["nombre"]] = True
                
                # Procesar combustibles
                combustibles_dict = {}
                if isinstance(estacion.get("combustibles"), list):
                    for combustible in estacion.get("combustibles", []):
                        if isinstance(combustible, dict):
                            nombre = combustible.get("nombre")
                            precio = combustible.get("precio")
                            if nombre and precio:
                                try:
                                    combustibles_dict[nombre] = float(precio)
                                except:
                                    pass
                
                # Procesar coordenadas
                latitud = estacion.get("latitud")
                longitud = estacion.get("longitud")
                
                try:
                    if latitud:
                        latitud = float(latitud)
                    if longitud:
                        longitud = float(longitud)
                except:
                    latitud = None
                    longitud = None
                
                estacion_info = {
                    "id_estacion": str(estacion.get("id", "")),
                    "nombre": str(estacion.get("nombre", "")),
                    "direccion": str(estacion.get("direccion", "")),
                    "comuna": str(estacion.get("comuna", "")),
                    "region": str(estacion.get("region", "")),
                    "latitud": latitud,
                    "longitud": longitud,
                    "marca": str(estacion.get("marca", "")),
                    "horario": str(estacion.get("horario", "")),
                    "servicios": servicios_dict,
                    "combustibles": combustibles_dict,
                    "fecha_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                estaciones_procesadas.append(estacion_info)
                    
            except Exception as e:
                continue
                
        return estaciones_procesadas
    
    def generar_metadata(self, estaciones_data):
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        total_estaciones = len(estaciones_data)
        regiones = set()
        marcas = set()
        combustibles_disponibles = set()
        precios_promedio = {}
        
        for estacion in estaciones_data:
            if estacion.get("region") and estacion["region"].strip():
                regiones.add(estacion["region"])
            if estacion.get("marca") and estacion["marca"].strip():
                marcas.add(estacion["marca"])
            
            if estacion.get("combustibles"):
                for combustible, precio in estacion["combustibles"].items():
                    if combustible and precio and isinstance(precio, (int, float)) and precio > 0:
                        combustibles_disponibles.add(combustible)
                        if combustible not in precios_promedio:
                            precios_promedio[combustible] = []
                        precios_promedio[combustible].append(precio)
        
        # Calcular promedios
        for combustible in precios_promedio:
            if precios_promedio[combustible]:
                precios_promedio[combustible] = round(
                    sum(precios_promedio[combustible]) / len(precios_promedio[combustible]), 0
                )
        
        return {
            "metadata": {
                "fuente": "CNE - Comisión Nacional de Energía",
                "api_endpoint": "https://api.cne.cl/api/v4/estaciones",
                "fecha_extraccion": timestamp,
                "descripcion": "Precios y ubicaciones de estaciones de servicio en Chile",
                "total_estaciones": total_estaciones,
                "regiones_disponibles": sorted(list(regiones)),
                "marcas_disponibles": sorted(list(marcas)),
                "combustibles_disponibles": sorted(list(combustibles_disponibles)),
                "precios_promedio_clp": precios_promedio,
                "moneda": "CLP",
                "metodo_extraccion": "Token en URL (método compañero)"
            },
            "estaciones": estaciones_data
        }
    
    def guardar_resultados(self, data):
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename_json = f"combustible_metadata_{timestamp}.json"
        filepath_json = os.path.join(self.output_dir, filename_json)
        
        try:
            with open(filepath_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Crear CSV limpio
            if data.get("estaciones"):
                estaciones_para_csv = []
                for estacion in data["estaciones"]:
                    if estacion.get("nombre") or estacion.get("id_estacion"):
                        row = {
                            "id_estacion": estacion.get("id_estacion", ""),
                            "nombre": estacion.get("nombre", ""),
                            "direccion": estacion.get("direccion", ""),
                            "comuna": estacion.get("comuna", ""),
                            "region": estacion.get("region", ""),
                            "latitud": estacion.get("latitud"),
                            "longitud": estacion.get("longitud"),
                            "marca": estacion.get("marca", ""),
                            "horario": estacion.get("horario", "")
                        }
                        
                        # Agregar combustibles como columnas
                        for combustible, precio in estacion.get("combustibles", {}).items():
                            row[f"precio_{combustible.replace(' ', '_')}"] = precio
                        
                        estaciones_para_csv.append(row)
                
                if estaciones_para_csv:
                    df = pd.DataFrame(estaciones_para_csv)
                    filename_csv = f"combustible_estaciones_{timestamp}.csv"
                    filepath_csv = os.path.join(self.output_dir, filename_csv)
                    df.to_csv(filepath_csv, index=False, encoding='utf-8')
            
            return filepath_json
        except Exception as e:
            return None
    
    def ejecutar(self):
        datos_raw = self.extraer_datos_cne()
        
        if datos_raw:
            estaciones_procesadas = self.procesar_estaciones(datos_raw)
            data_final = self.generar_metadata(estaciones_procesadas)
            return self.guardar_resultados(data_final)
        else:
            return None

def main():
    extractor = ExtractorCombustibleCNE()
    resultado = extractor.ejecutar()
    
    if resultado:
        print(f"Archivo generado: {resultado}")
    else:
        print("Error al generar el archivo")

if __name__ == "__main__":
    main()
