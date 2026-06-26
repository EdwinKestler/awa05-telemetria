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
    try:
        trabajo()
    except Exception as e:
        print(f"[SCHEDULER] Error en {nombre}: {e}")


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
    ruta_log = ruta_proyecto(ruta_log)
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(ruta_log)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
