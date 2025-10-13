#!/usr/bin/env python3

import json
import pandas as pd
from datetime import datetime
import os


class ProcesadorPrecios:
    def __init__(self):
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        os.makedirs(self.output_dir, exist_ok=True)

    def procesar_precios_manuales(self):
        try:
            with open('precios.json', 'r', encoding='utf-8') as f:
                data_manual = json.load(f)

            autopistas_procesadas = []
            total_porticos = 0
            tipos_tarifa = set()

            for autopista in data_manual.get("autopistas", []):
                autopista_procesada = {
                    "nombre_autopista": autopista.get("nombre_autopista"),
                    "año_tarifas": autopista.get("año_tarifas", 2025),
                    "tramo_descripcion": autopista.get("tramo_descripcion", ""),
                    "metadata": autopista.get("metadata", {}),
                    "total_ejes": len(autopista.get("ejes", [])),
                    "total_porticos": 0
                }

                porticos_count = 0
                for eje in autopista.get("ejes", []):
                    for direccion in eje.get("direcciones", []):
                        porticos_count += len(direccion.get("porticos", []))

                    for portico in eje.get("porticos", []):
                        porticos_count += 1

                        if "peajes" in portico:
                            for categoria, valores in portico["peajes"].items():
                                if isinstance(valores, dict):
                                    tipos_tarifa.update(valores.keys())

                autopista_procesada["total_porticos"] = porticos_count
                total_porticos += porticos_count
                autopistas_procesadas.append(autopista_procesada)

            data_procesado = {
                "metadata": {
                    "fuente": "Extracción manual desde PDFs MOP",
                    "fecha_extraccion": datetime.now().strftime("%Y-%m-%d"),
                    "descripcion": "Tarifas de peajes extraídas manualmente desde documentos oficiales",
                    "moneda": "CLP",
                    "año_tarifas": "2025",
                    "procesado_por": "Sebastian - Equipo Metadata",
                    "total_autopistas": len(autopistas_procesadas),
                    "total_porticos": total_porticos,
                    "tipos_tarifa": sorted(list(tipos_tarifa)),
                    "estructura_original": "Conservada desde archivo manual"
                },
                "autopistas": data_manual.get("autopistas", []),
                "resumen_autopistas": autopistas_procesadas
            }

            timestamp = datetime.now().strftime("%Y-%m-%d")
            filename = f"peajes_tarifas_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data_procesado, f, ensure_ascii=False, indent=2)

            self.crear_csv_plano(data_manual, timestamp)

            return filepath

        except Exception as e:
            return None

    def crear_csv_plano(self, data_manual, timestamp):
        rows = []

        for autopista in data_manual.get("autopistas", []):
            nombre_autopista = autopista.get("nombre_autopista")
            tramo = autopista.get("tramo_descripcion", "")

            for eje in autopista.get("ejes", []):
                nombre_eje = eje.get("nombre_eje")

                for direccion in eje.get("direcciones", []):
                    sentido = direccion.get("sentido", "")

                    for portico in direccion.get("porticos", []):
                        portico_id = portico.get("portico_id", "")
                        referencia = portico.get("referencia_tramo", "")
                        longitud = portico.get("longitud_km", 0)

                        for categoria, valores in portico.get("peajes", {}).items():
                            if isinstance(valores, dict):
                                for tipo_tarifa, precio in valores.items():
                                    if precio is not None:
                                        rows.append({
                                            "autopista": nombre_autopista,
                                            "tramo": tramo,
                                            "eje": nombre_eje,
                                            "sentido": sentido,
                                            "portico_id": portico_id,
                                            "referencia_tramo": referencia,
                                            "longitud_km": longitud,
                                            "categoria_vehiculo": categoria,
                                            "tipo_tarifa": tipo_tarifa,
                                            "precio_clp": precio
                                        })

                for portico in eje.get("porticos", []):
                    nombre_portico = portico.get("nombre", "")
                    tipo_portico = portico.get("tipo", "")

                    for categoria, precio in portico.get("peajes", {}).items():
                        if isinstance(precio, (int, float)):
                            rows.append({
                                "autopista": nombre_autopista,
                                "tramo": tramo,
                                "eje": nombre_eje,
                                "sentido": "",
                                "portico_id": nombre_portico,
                                "referencia_tramo": tipo_portico,
                                "longitud_km": 0,
                                "categoria_vehiculo": categoria,
                                "tipo_tarifa": "tarifa_unica",
                                "precio_clp": precio
                            })

        if rows:
            df = pd.DataFrame(rows)
            csv_filepath = os.path.join(self.output_dir, f"peajes_tarifas_{timestamp}.csv")
            df.to_csv(csv_filepath, index=False, encoding='utf-8')

    def ejecutar(self):
        return self.procesar_precios_manuales()


def main():
    procesador = ProcesadorPrecios()
    return procesador.ejecutar()


if __name__ == "__main__":
    main()