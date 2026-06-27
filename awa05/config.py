import os

from awa05.utils import cargar_config
from awa05.utils import env_int


SETTINGS_PATH = "config/settings.json"


class ConfigError(ValueError):
    pass


def cargar_settings():
    return cargar_config(SETTINGS_PATH)


def obtener(settings, ruta, default=None):
    actual = settings
    for parte in ruta.split("."):
        if not isinstance(actual, dict) or parte not in actual:
            return default
        actual = actual[parte]
    return actual


def obtener_int(settings, ruta, default):
    valor = obtener(settings, ruta, default)
    try:
        return int(valor)
    except (TypeError, ValueError):
        print(f"[CONFIG] Valor inválido para {ruta}: {valor!r}; usando {default}")
        return default


def obtener_float(settings, ruta, default):
    valor = obtener(settings, ruta, default)
    try:
        return float(valor)
    except (TypeError, ValueError):
        print(f"[CONFIG] Valor inválido para {ruta}: {valor!r}; usando {default}")
        return default


def requerir_numero(settings, ruta, minimo=None):
    valor = obtener(settings, ruta)
    if valor is None:
        raise ConfigError(f"Falta configuración requerida: {ruta}")
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Configuración inválida para {ruta}: {valor!r}") from exc
    if minimo is not None and numero < minimo:
        raise ConfigError(f"Configuración inválida para {ruta}: {numero} < {minimo}")
    return numero


def validar_settings(settings=None):
    settings = settings or cargar_settings()
    if not isinstance(settings, dict):
        raise ConfigError("config/settings.json debe contener un objeto JSON")

    requerir_numero(settings, "frecuencia_muestreo_minutos", minimo=1)
    requerir_numero(settings, "sensor_distancia.trig_gpio", minimo=0)
    requerir_numero(settings, "sensor_distancia.echo_gpio", minimo=0)
    requerir_numero(settings, "sensor_distancia.altura_total_cm", minimo=0)
    requerir_numero(settings, "sensor_distancia.altura_max_agua_cm", minimo=0)
    requerir_numero(settings, "sensor_distancia.radio_cm", minimo=0)
    requerir_numero(settings, "sensor_distancia.num_muestras", minimo=1)
    requerir_numero(settings, "sensor_distancia.pausa_muestras_s", minimo=0)
    requerir_numero(settings, "sensor_distancia.timeout_echo_s", minimo=0)

    altura_total = obtener_float(settings, "sensor_distancia.altura_total_cm", 0)
    altura_max = obtener_float(settings, "sensor_distancia.altura_max_agua_cm", 0)
    if altura_max > altura_total:
        raise ConfigError(
            "sensor_distancia.altura_max_agua_cm no puede superar "
            "sensor_distancia.altura_total_cm"
        )
    return settings


def scheduler_config():
    settings = validar_settings()
    frecuencia = obtener_int(settings, "frecuencia_muestreo_minutos", 15)
    return {
        "espera_red_minutos": env_int(
            "AWA05_SCHEDULER_ESPERA_RED_MINUTOS",
            obtener_int(settings, "scheduler.espera_red_minutos", 10),
        ),
        "lectura_intervalo_minutos": env_int(
            "AWA05_SCHEDULER_LECTURA_INTERVALO_MINUTOS",
            obtener_int(
                settings,
                "scheduler.lectura_intervalo_minutos",
                frecuencia,
            ),
        ),
        "kpi_intervalo_minutos": env_int(
            "AWA05_SCHEDULER_KPI_INTERVALO_MINUTOS",
            obtener_int(
                settings,
                "scheduler.kpi_intervalo_minutos",
                frecuencia,
            ),
        ),
        "watchdog_intervalo_minutos": env_int(
            "AWA05_SCHEDULER_WATCHDOG_INTERVALO_MINUTOS",
            obtener_int(
                settings,
                "scheduler.watchdog_intervalo_minutos",
                5,
            ),
        ),
    }


def sensor_distancia_config():
    settings = validar_settings()
    radio = obtener_float(settings, "sensor_distancia.radio_cm", 12.9)
    altura_total = obtener_float(settings, "sensor_distancia.altura_total_cm", 72.5)
    altura_max = obtener_float(settings, "sensor_distancia.altura_max_agua_cm", 38.3)
    return {
        "trig_gpio": obtener_int(settings, "sensor_distancia.trig_gpio", 17),
        "echo_gpio": obtener_int(settings, "sensor_distancia.echo_gpio", 18),
        "altura_total_cm": altura_total,
        "altura_max_agua_cm": altura_max,
        "radio_cm": radio,
        "area_base_cm2": 3.14159265 * (radio ** 2),
        "distancia_min_cm": altura_total - altura_max,
        "distancia_max_cm": altura_total,
        "num_muestras": obtener_int(settings, "sensor_distancia.num_muestras", 11),
        "pausa_muestras_s": obtener_float(settings, "sensor_distancia.pausa_muestras_s", 0.06),
        "timeout_echo_s": obtener_float(settings, "sensor_distancia.timeout_echo_s", 0.04),
    }


def ws2000_config():
    settings = validar_settings()
    secret_env_var = str(
        obtener(settings, "ws2000.shared_secret_env", "AWA05_WS2000_SHARED_SECRET")
        or "AWA05_WS2000_SHARED_SECRET"
    )
    return {
        "shared_secret": os.getenv(secret_env_var, ""),
        "shared_secret_env": secret_env_var,
        "max_content_length_bytes": env_int(
            "AWA05_WS2000_MAX_CONTENT_LENGTH_BYTES",
            obtener_int(settings, "ws2000.max_content_length_bytes", 8192),
        ),
    }


if __name__ == "__main__":
    validar_settings()
    print("[OK] config/settings.json válido")
