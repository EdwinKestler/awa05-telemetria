import unittest
from unittest.mock import patch

from awa05.config import ConfigError, obtener, obtener_int, scheduler_config, sensor_distancia_config, validar_settings


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

    def test_validacion_reporta_config_faltante(self):
        with self.assertRaisesRegex(ConfigError, "sensor_distancia.trig_gpio"):
            validar_settings({"frecuencia_muestreo_minutos": 15, "sensor_distancia": {}})


if __name__ == "__main__":
    unittest.main()
