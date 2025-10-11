# METADATA - Proyecto Ruteo Económico Chile

**Responsable:** Sebastian  
**Fecha:** Octubre 2025  
**Estado:** Fase 2  

## 🎯 Descripción

Este módulo maneja la extracción y procesamiento de metadata para el sistema de ruteo económico, incluyendo:
- Tarifas de peajes y pórticos
- Precios de combustibles  
- Georeferenciación de peajes

## 📂 Archivos

### Extractores
- `extract_tarifas_peajes.py` - Procesa tarifas de peajes desde MOP
- `extract_combustible.py` - Extrae precios de combustibles desde CNE API  
- `extract_georef_peajes.py` - Obtiene coordenadas GPS de peajes

### Datos
- `precios.json` - Tarifas existentes (manual)
- Outputs en `/database/`:
  - `peajes_tarifas_YYYY-MM-DD.json`
  - `combustible_metadata_YYYY-MM-DD.json`
  - `peajes_georeferencias_YYYY-MM-DD.json`

## 🚀 Uso


