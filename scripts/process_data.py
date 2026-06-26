import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awa05.processing import dashboard as _dashboard


RUTA_NIVEL = _dashboard.RUTA_NIVEL
RUTA_CLIMA = _dashboard.RUTA_CLIMA
RUTA_JSON = _dashboard.RUTA_JSON

numero = _dashboard.numero
f_a_c = _dashboard.f_a_c
mph_a_kmh = _dashboard.mph_a_kmh
leer_csv = _dashboard.leer_csv
estado_sistema = _dashboard.estado_sistema
filtrar_outliers_nivel = _dashboard.filtrar_outliers_nivel


def _sincronizar_rutas():
    _dashboard.RUTA_NIVEL = RUTA_NIVEL
    _dashboard.RUTA_CLIMA = RUTA_CLIMA
    _dashboard.RUTA_JSON = RUTA_JSON


def generar_dashboard_json():
    _sincronizar_rutas()
    estado_original = _dashboard.estado_sistema
    _dashboard.estado_sistema = estado_sistema
    try:
        return _dashboard.generar_dashboard_json()
    finally:
        _dashboard.estado_sistema = estado_original


if __name__ == "__main__":
    data = generar_dashboard_json()
    print(f"KPIs: {data['kpis']}")
