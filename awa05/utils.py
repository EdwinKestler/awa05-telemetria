import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def ruta_proyecto(ruta):
    ruta = Path(ruta)
    return ruta if ruta.is_absolute() else PROJECT_ROOT / ruta


def cargar_config(ruta):
    with open(ruta_proyecto(ruta), "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_entorno(ruta=".env"):
    env_path = ruta_proyecto(ruta)
    try:
        from dotenv import load_dotenv
    except ImportError:
        if env_path.exists():
            print("[CONFIG] python-dotenv no instalado; usando variables de entorno existentes.")
        return False
    return bool(load_dotenv(env_path))


def timestamp_ahora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def env_bool(nombre, default=False):
    valor = os.getenv(nombre)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "yes", "y", "si", "sí", "on"}


def env_float(nombre, default):
    valor = os.getenv(nombre)
    if valor in (None, ""):
        return default
    try:
        return float(valor)
    except ValueError:
        print(f"[CONFIG] Valor inválido para {nombre}: {valor!r}; usando {default}")
        return default


def env_int(nombre, default):
    valor = os.getenv(nombre)
    if valor in (None, ""):
        return default
    try:
        return int(valor)
    except ValueError:
        print(f"[CONFIG] Valor inválido para {nombre}: {valor!r}; usando {default}")
        return default


def ejecutar_seguro(nombre, trabajo):
    awa05_logger = logging.getLogger("awa05")
    logger = logging.getLogger("awa05.scheduler")
    from awa05.core.errors import run_safely

    resultado = run_safely(nombre, trabajo)
    if resultado.failed:
        if awa05_logger.handlers:
            logger.error(
                "Error en %s: %s: %s",
                nombre,
                resultado.error_type,
                resultado.message,
                exc_info=(
                    type(resultado.error),
                    resultado.error,
                    resultado.error.__traceback__,
                ),
            )
        print(f"[SCHEDULER] Error en {nombre}: {resultado.message}")
    return resultado


def guardar_csv(ruta, fila, encabezados=None):
    ruta = ruta_proyecto(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    archivo_nuevo = not ruta.exists() or ruta.stat().st_size == 0
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=encabezados or fila.keys())
        if archivo_nuevo:
            writer.writeheader()
        writer.writerow(fila)


def configurar_log(nombre, ruta_log):
    from awa05.core.logging import configure_logging

    return configure_logging(name=nombre, path=ruta_log)
