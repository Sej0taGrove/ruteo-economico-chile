# ruteo-economico-chile
Sistema de ruteo vehicular optimizado por costo monetario - Fase 2

## Requisitos previos

- [Docker](https://docs.docker.com/get-docker/) y Docker Compose v2.
- Copiar el archivo `.env.example` como `.env` y completar los valores de las API keys si se dispone de ellos.

```bash
cp .env.example .env
# Edita .env con tus credenciales reales
```

## Levantar el proyecto con Docker

1. Construir y levantar los servicios:

   ```bash
   docker compose up --build
   ```

   Esto inicia dos contenedores:
   - `ruteo_db`: PostgreSQL 16 + PostGIS + pgRouting con la base `ruteo_economico_chile`.  
     El esquema se carga automáticamente desde `database/schema.sql` la primera vez que se crea el volumen.
   - `ruteo_web`: ejecuta `python main.py`, que encadena la ejecución de los scripts del proyecto (carga de infraestructura, scrapers de amenazas, etc.) y finalmente levanta la aplicación Flask en `http://localhost:5000`.

2. Si necesitas reinicializar la base de datos (p. ej. para recargar el esquema), elimina el volumen persistente:

   ```bash
   docker compose down -v
   docker compose up --build
   ```

3. Para ejecutar scripts auxiliares dentro del contenedor web (por ejemplo, cargar amenazas):

   ```bash
   docker compose run --rm web python Amenazas/3a_sismos.py
   ```

### Personalizar la ejecución

- Puedes omitir scripts del pipeline configurando la variable `SKIP_TASKS` (usa el nombre de la tarea o el nombre del archivo):

  ```bash
  SKIP_TASKS="Amenazas - Trafico" docker compose up --build
  ```

- Ajusta `LOG_LEVEL` (por ejemplo, `LOG_LEVEL=DEBUG`) para obtener más detalle del flujo de arranque.

## Configuración adicional

- Los archivos generados por los scripts (GeoJSON en `Amenazas_JSON/`) quedan dentro del contenedor. Puedes adaptarlo montando un volumen si necesitas compartirlos con el host.
- Si deseas exponer el puerto de PostgreSQL con un puerto distinto, ajusta la variable `DB_PORT` al ejecutar `docker compose` (`DB_PORT=15432 docker compose up`).
- Recuerda que cualquier cambio en las dependencias de Python requiere reconstruir la imagen (`docker compose build web`).

## Desarrollo sin Docker

Si prefieres ejecutar el proyecto localmente:

```bash
python -m venv venv
source venv/bin/activate  # .\venv\Scripts\activate en Windows
pip install -r requirements.txt
python main.py
```

Asegúrate de contar con una instancia de PostgreSQL/PostGIS disponible y con las mismas credenciales configuradas en `.env`. El script `database/schema.sql` define toda la estructura necesaria.
