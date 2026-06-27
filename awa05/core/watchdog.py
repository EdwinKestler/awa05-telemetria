import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from awa05.drivers.system import SystemMonitor
from awa05.utils import cargar_config, env_bool, env_float, env_int


ULTIMA_ACCION_TERMICA = None


@dataclass
class ThermalWatchdogResult:
    temperature_c: Optional[float] = None
    threshold_c: Optional[float] = None
    critical: bool = False
    cooldown_active: bool = False
    shutdown_enabled: bool = False
    shutdown_executed: bool = False
    report_uploaded: bool = False
    error: Optional[str] = None


def reset_estado_watchdog():
    global ULTIMA_ACCION_TERMICA
    ULTIMA_ACCION_TERMICA = None


def _config_watchdog():
    try:
        return cargar_config("config/settings.json").get("watchdog", {})
    except Exception as e:
        print(f"[WATCHDOG] No se pudo cargar config/settings.json: {e}")
        return {}


def leer_temperatura_cpu():
    temp = SystemMonitor().cpu_temperature_c()
    if temp is None:
        raise RuntimeError("No se pudo leer temperatura CPU")
    return temp


def parametros_watchdog():
    config = _config_watchdog()
    return {
        "temperatura_critica_c": env_float(
            "AWA05_TEMP_CRITICA_C",
            float(config.get("temperatura_critica_c", 75.0)),
        ),
        "habilitar_apagado": env_bool(
            "AWA05_ENABLE_SHUTDOWN",
            bool(config.get("habilitar_apagado", False)),
        ),
        "cooldown_minutos": env_int(
            "AWA05_WATCHDOG_COOLDOWN_MINUTES",
            int(config.get("cooldown_minutos", 30)),
        ),
        "espera_apagado_segundos": env_int(
            "AWA05_SHUTDOWN_DELAY_SECONDS",
            int(config.get("espera_apagado_segundos", 10)),
        ),
    }


def watchdog_termico(leer_temperatura=leer_temperatura_cpu, ejecutar_apagado=None):
    global ULTIMA_ACCION_TERMICA
    ejecutar_apagado = ejecutar_apagado or os.system
    try:
        from awa05.processing.dashboard import generar_dashboard_json
        from awa05.upload.github import subir_dashboard

        params = parametros_watchdog()
        temp = leer_temperatura()
        result = ThermalWatchdogResult(
            temperature_c=temp,
            threshold_c=params["temperatura_critica_c"],
            shutdown_enabled=params["habilitar_apagado"],
        )
        print(f"[WATCHDOG] Temperatura CPU: {temp}°C")
        if temp < params["temperatura_critica_c"]:
            return result

        ahora = datetime.now()
        cooldown = timedelta(minutes=params["cooldown_minutos"])
        result.critical = True
        if ULTIMA_ACCION_TERMICA and ahora - ULTIMA_ACCION_TERMICA < cooldown:
            result.cooldown_active = True
            print(
                "[WATCHDOG] Temperatura crítica ya atendida; "
                f"cooldown activo por {params['cooldown_minutos']} min."
            )
            return result

        ULTIMA_ACCION_TERMICA = ahora
        print(
            f"[WATCHDOG] TEMPERATURA CRITICA {temp}°C "
            f"(umbral {params['temperatura_critica_c']}°C). Generando reporte..."
        )
        generar_dashboard_json()
        subir_dashboard()
        result.report_uploaded = True
        if not params["habilitar_apagado"]:
            print(
                "[WATCHDOG] Apagado automático deshabilitado. "
                "Use AWA05_ENABLE_SHUTDOWN=true solo con aprobación humana."
            )
            return result

        espera = params["espera_apagado_segundos"]
        print(f"[WATCHDOG] Apagado habilitado; ejecutando en {espera}s...")
        time.sleep(espera)
        ejecutar_apagado("sudo shutdown -h now")
        result.shutdown_executed = True
        return result
    except Exception as e:
        print(f"[WATCHDOG] Error leyendo temperatura: {e}")
        return ThermalWatchdogResult(error=str(e))
