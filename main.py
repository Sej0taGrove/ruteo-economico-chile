from __future__ import annotations

import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence, Set

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


@dataclass(frozen=True)
class ScriptTask:
    name: str
    script: Path
    working_dir: Path
    args: Sequence[str] = field(default_factory=tuple)
    optional: bool = False
    long_running: bool = False

    def command(self) -> List[str]:
        """Construye el comando a ejecutar para el script."""
        if self.script.suffix == ".py":
            return [sys.executable, str(self.script)]
        return [str(self.script)]


# ORDEN CORRECTO DE EJECUCIÓN:
# 1. AMENAZAS (metadata) - Se ejecutan siempre para actualizar datos
# 2. INFRAESTRUCTURA - Se ejecuta solo si no existen los datos
# 3. APLICACIÓN WEB - Se ejecuta al final
TASKS: Sequence[ScriptTask] = (
    # ==== FASE 1: AMENAZAS (METADATA) ====
    ScriptTask(
        name="Amenazas - Sismos",
        script=BASE_DIR / "Amenazas" / "3a_sismos.py",
        working_dir=BASE_DIR / "Amenazas",
    ),
    ScriptTask(
        name="Amenazas - Inundaciones",
        script=BASE_DIR / "Amenazas" / "3b_inundaciones.py",
        working_dir=BASE_DIR / "Amenazas",
    ),
    ScriptTask(
        name="Amenazas - Incendios",
        script=BASE_DIR / "Amenazas" / "3c_incendios.py",
        working_dir=BASE_DIR / "Amenazas",
    ),
    ScriptTask(
        name="Amenazas - Trafico",
        script=BASE_DIR / "Amenazas" / "3d_trafico.py",
        working_dir=BASE_DIR / "Amenazas",
        optional=True,  # puede requerir API key de Google Maps
    ),
    ScriptTask(
        name="Carga amenazas a BD",
        script=BASE_DIR / "Amenazas" / "load_amenazas_to_db.py",
        working_dir=BASE_DIR / "Amenazas",
        optional=True,  # puede fallar si no se generaron datos nuevos
    ),
    # ==== FASE 2: INFRAESTRUCTURA ====
    ScriptTask(
        name="Infraestructura vial",
        script=BASE_DIR / "infraestructura" / "load_infra_to_db.py",
        working_dir=BASE_DIR / "infraestructura",
    ),
    # ==== FASE 3: APLICACIÓN WEB ====
    ScriptTask(
        name="Aplicacion web",
        script=BASE_DIR / "Sitio_web" / "app.py",
        working_dir=BASE_DIR,
        long_running=True,
    ),
)


def parse_skip_list() -> Set[str]:
    raw = os.getenv("SKIP_TASKS", "")
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def should_skip(task: ScriptTask, skip_tokens: Set[str]) -> bool:
    identifiers = {task.name.lower(), task.script.name.lower(), str(task.script).lower()}
    return bool(skip_tokens & identifiers)


def execute_task(task: ScriptTask) -> None:
    logger = logging.getLogger("bootstrap")

    if not task.script.exists():
        message = f"No se encontro el script {task.script}"
        if task.optional:
            logger.warning("%s; se omite por ser opcional.", message)
            return
        raise FileNotFoundError(message)

    cmd = task.command() + list(task.args)
    logger.info("Ejecutando %s -> %s", task.name, " ".join(cmd))

    try:
        subprocess.run(cmd, cwd=str(task.working_dir), check=True)
    except subprocess.CalledProcessError as exc:
        if task.optional:
            logger.warning("El script opcional %s fallo con codigo %s. Continuando...", task.name, exc.returncode)
            return
        logger.error("El script %s finalizo con codigo %s.", task.name, exc.returncode)
        raise


def run_tasks() -> None:
    logger = logging.getLogger("bootstrap")
    skip_tokens = parse_skip_list()
    long_running: ScriptTask | None = None

    logger.info("="*60)
    logger.info("INICIANDO PROCESO DE BOOTSTRAP DEL PROYECTO")
    logger.info("="*60)
    logger.info("")
    logger.info("Orden de ejecucion:")
    logger.info("  1. Amenazas (metadata) - Actualizacion de datos")
    logger.info("  2. Infraestructura vial - Carga si es necesario")
    logger.info("  3. Aplicacion web - Servidor Flask")
    logger.info("")

    for task in TASKS:
        if should_skip(task, skip_tokens):
            logger.info("Saltando tarea %s por configuracion.", task.name)
            continue

        if task.long_running:
            long_running = task
            continue

        execute_task(task)

    if long_running:
        logger.info("")
        logger.info("="*60)
        logger.info("Iniciando tarea final de larga ejecucion: %s", long_running.name)
        logger.info("="*60)
        execute_task(long_running)


def main() -> None:
    load_dotenv()
    configure_logging()

    try:
        run_tasks()
    except FileNotFoundError as exc:
        logging.error(str(exc))
        sys.exit(1)
    except subprocess.CalledProcessError:
        sys.exit(1)
    except KeyboardInterrupt:
        logging.warning("Ejecucion interrumpida por el usuario.")
        sys.exit(130)


if __name__ == "__main__":
    main()