import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import process_data


CLIMA_FIELDS = [
    "timestamp",
    "temp_exterior",
    "humedad",
    "punto_rocio",
    "presion",
    "viento_vel",
    "viento_dir",
    "lluvia_hora",
    "radiacion_solar",
    "uv",
]


def escribir_csv(ruta, campos, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


class ProcessDataTests(unittest.TestCase):
    def test_preserva_alineacion_y_tolera_datos_faltantes(self):
        with tempfile.TemporaryDirectory() as temporal:
            raiz = Path(temporal)
            nivel = raiz / "nivel.csv"
            clima = raiz / "clima.csv"
            salida = raiz / "dashboard.json"

            escribir_csv(
                nivel,
                ["timestamp", "distancia_cm", "volumen_litros"],
                [
                    {"timestamp": "2026-01-01 00:00:00", "distancia_cm": "60", "volumen_litros": "10"},
                    {"timestamp": "2026-01-01 00:15:00", "distancia_cm": "59", "volumen_litros": "20"},
                    {"timestamp": "2026-01-01 00:30:00", "distancia_cm": "58", "volumen_litros": "N/A"},
                ],
            )
            escribir_csv(
                clima,
                CLIMA_FIELDS,
                [
                    {
                        "timestamp": "2026-01-01 00:00:00",
                        "temp_exterior": "68",
                        "humedad": "N/A",
                        "punto_rocio": "50",
                        "presion": "25",
                        "viento_vel": "1",
                        "viento_dir": "90",
                        "lluvia_hora": "0",
                        "radiacion_solar": "10",
                        "uv": "0",
                    },
                    {
                        "timestamp": "2026-01-01 00:01:00",
                        "temp_exterior": "N/A",
                        "humedad": "70",
                        "punto_rocio": "N/A",
                        "presion": "N/A",
                        "viento_vel": "N/A",
                        "viento_dir": "N/A",
                        "lluvia_hora": "N/A",
                        "radiacion_solar": "N/A",
                        "uv": "N/A",
                    },
                ],
            )

            with (
                patch.object(process_data, "RUTA_NIVEL", nivel),
                patch.object(process_data, "RUTA_CLIMA", clima),
                patch.object(process_data, "RUTA_JSON", salida),
                patch.object(process_data, "estado_sistema", return_value={}),
            ):
                datos = process_data.generar_dashboard_json()

            series = datos["series"]
            self.assertEqual(len(series["labels"]), len(series["humedad_pct"]))
            self.assertEqual(len(series["labels"]), len(series["temp_c"]))
            self.assertEqual(series["humedad_pct"], [None, 70.0])
            self.assertEqual(series["temp_c"], [20.0, None])
            self.assertEqual(series["nivel_l"], [10.0, 10.0, None])
            self.assertIsNone(datos["kpis"]["nivel_l"])
            self.assertIsNone(datos["kpis"]["temp_c"])
            self.assertTrue(salida.exists())


if __name__ == "__main__":
    unittest.main()
