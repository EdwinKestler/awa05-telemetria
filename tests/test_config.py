import unittest
from unittest.mock import patch

from awa05.config import (
    ConfigError,
    obtener,
    obtener_int,
    logging_config,
    scheduler_config,
    sensor_distancia_config,
    validar_settings,
    ws2000_config,
)


def settings_base():
    return {
        "frecuencia_muestreo_minutos": 20,
        "sensor_distancia": {
            "trig_gpio": 17,
            "echo_gpio": 18,
            "altura_total_cm": 72.5,
            "altura_max_agua_cm": 38.3,
            "radio_cm": 12.9,
            "num_muestras": 11,
            "pausa_muestras_s": 0.06,
            "timeout_echo_s": 0.04,
        },
    }


class ConfigTests(unittest.TestCase):
    def test_obtener_valor_anidado_o_default(self):
        settings = {"scheduler": {"espera_red_minutos": 7}}

        self.assertEqual(obtener(settings, "scheduler.espera_red_minutos"), 7)
        self.assertEqual(obtener(settings, "scheduler.falta", 15), 15)

    def test_scheduler_config_usa_frecuencia_como_default(self):
        settings = settings_base()
        settings["scheduler"] = {"watchdog_intervalo_minutos": 3}

        with patch("awa05.config.cargar_settings", return_value=settings), \
             patch.dict("os.environ", {}, clear=True):
            config = scheduler_config()

        self.assertEqual(config["lectura_intervalo_minutos"], 20)
        self.assertEqual(config["kpi_intervalo_minutos"], 20)
        self.assertEqual(config["watchdog_intervalo_minutos"], 3)

    def test_scheduler_config_permite_overrides_de_smoke_test(self):
        settings = settings_base()
        settings["scheduler"] = {"espera_red_minutos": 10}

        with patch("awa05.config.cargar_settings", return_value=settings), \
             patch.dict(
                 "os.environ",
                 {
                     "AWA05_SCHEDULER_ESPERA_RED_MINUTOS": "0",
                     "AWA05_SCHEDULER_LECTURA_INTERVALO_MINUTOS": "1",
                 },
                 clear=True,
             ):
            config = scheduler_config()

        self.assertEqual(config["espera_red_minutos"], 0)
        self.assertEqual(config["lectura_intervalo_minutos"], 1)

    def test_obtener_int_tolera_valor_invalido(self):
        self.assertEqual(obtener_int({"x": "no"}, "x", 5), 5)

    def test_sensor_distancia_config_calcula_derivados(self):
        settings = settings_base()

        with patch("awa05.config.cargar_settings", return_value=settings):
            config = sensor_distancia_config()

        self.assertEqual(config["distancia_min_cm"], 34.2)
        self.assertEqual(config["distancia_max_cm"], 72.5)
        self.assertAlmostEqual(config["area_base_cm2"], 522.7924, places=4)

    def test_ws2000_config_lee_secreto_desde_variable_de_entorno(self):
        settings = settings_base()
        settings["ws2000"] = {
            "shared_secret_env": "AWA05_TEST_WS_SECRET",
            "max_content_length_bytes": 4096,
        }

        with patch("awa05.config.cargar_settings", return_value=settings), \
             patch.dict(
                 "os.environ",
                 {
                     "AWA05_TEST_WS_SECRET": "secreto",
                     "AWA05_WS2000_MAX_CONTENT_LENGTH_BYTES": "2048",
                 },
                 clear=True,
             ):
            config = ws2000_config()

        self.assertEqual(config["shared_secret"], "secreto")
        self.assertEqual(config["shared_secret_env"], "AWA05_TEST_WS_SECRET")
        self.assertEqual(config["max_content_length_bytes"], 2048)

    def test_logging_config_lee_settings_y_overrides(self):
        settings = settings_base()
        settings["logging"] = {
            "enabled": True,
            "level": "WARNING",
            "path": "logs/custom.log",
            "max_bytes": 1000,
            "backup_count": 2,
        }

        with patch("awa05.config.cargar_settings", return_value=settings), \
             patch.dict(
                 "os.environ",
                 {
                     "AWA05_LOG_LEVEL": "ERROR",
                     "AWA05_LOG_MAX_BYTES": "2048",
                 },
                 clear=True,
             ):
            config = logging_config()

        self.assertTrue(config["enabled"])
        self.assertEqual(config["level"], "ERROR")
        self.assertEqual(config["path"], "logs/custom.log")
        self.assertEqual(config["max_bytes"], 2048)
        self.assertEqual(config["backup_count"], 2)

    def test_validacion_reporta_config_faltante(self):
        with self.assertRaisesRegex(ConfigError, "sensor_distancia.trig_gpio"):
            validar_settings({"frecuencia_muestreo_minutos": 15, "sensor_distancia": {}})


if __name__ == "__main__":
    unittest.main()
