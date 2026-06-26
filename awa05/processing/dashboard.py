import csv
import json
import os

from awa05.drivers.system import SystemMonitor
from awa05.utils import ruta_proyecto, timestamp_ahora


RUTA_NIVEL = ruta_proyecto("data/raw/nivel_raw.csv")
RUTA_CLIMA = ruta_proyecto("data/raw/clima_raw.csv")
RUTA_JSON = ruta_proyecto("data/processed/dashboard_data.json")


def numero(valor, decimales=None):
    if valor in (None, "", "N/A"):
        return None
    try:
        resultado = float(valor)
        return round(resultado, decimales) if decimales is not None else resultado
    except (TypeError, ValueError):
        return None


def f_a_c(f):
    valor = numero(f)
    return round((valor - 32) * 5 / 9, 1) if valor is not None else None


def mph_a_kmh(v):
    valor = numero(v)
    return round(valor * 1.60934, 1) if valor is not None else None


def leer_csv(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def estado_sistema():
    return SystemMonitor().snapshot()


def filtrar_outliers_nivel(nivel_r):
    nivel_filtrado = []
    volumen_anterior = None
    for row in nivel_r:
        vol = numero(row.get("volumen_litros"))
        if vol is None:
            nivel_filtrado.append(row)
            continue
        if volumen_anterior is not None:
            diff = vol - volumen_anterior
            if diff > 6:
                row = dict(row)
                row["volumen_litros"] = str(volumen_anterior)
                vol = volumen_anterior
            elif diff < 0 and diff > -5:
                row = dict(row)
                row["volumen_litros"] = str(volumen_anterior)
                vol = volumen_anterior
        volumen_anterior = vol
        nivel_filtrado.append(row)
    return nivel_filtrado


def generar_dashboard_json():
    RUTA_JSON.parent.mkdir(parents=True, exist_ok=True)
    nivel = leer_csv(RUTA_NIVEL)
    clima = leer_csv(RUTA_CLIMA)
    limite = 9999
    nivel_r = filtrar_outliers_nivel(nivel[-limite:])
    clima_r = clima[-limite:]

    labels_nivel = [f.get("timestamp") for f in nivel_r]
    nivel_l = [numero(f.get("volumen_litros"), 2) for f in nivel_r]

    paso = max(1, len(clima_r) // 96)
    clima_sub = clima_r[::paso]
    labels = [f.get("timestamp") for f in clima_sub] if clima_sub else labels_nivel
    humedad = [numero(f.get("humedad"), 1) for f in clima_sub]
    temp_c = [f_a_c(f.get("temp_exterior")) for f in clima_sub]
    rocio_c = [f_a_c(f.get("punto_rocio")) for f in clima_sub]
    presion = [numero(f.get("presion"), 3) for f in clima_sub]
    viento = [mph_a_kmh(f.get("viento_vel")) for f in clima_sub]
    dir_v = [numero(f.get("viento_dir"), 0) for f in clima_sub]
    lluvia = [numero(f.get("lluvia_hora"), 2) for f in clima_sub]
    solar = [numero(f.get("radiacion_solar"), 1) for f in clima_sub]
    uv = [numero(f.get("uv"), 1) for f in clima_sub]
    ultima_nivel = nivel[-1] if nivel else {}
    ultima_clima = clima[-1] if clima else {}
    kpis = {
        "nivel_l": numero(ultima_nivel.get("volumen_litros"), 2),
        "humedad_pct": numero(ultima_clima.get("humedad"), 1),
        "temp_c": f_a_c(ultima_clima.get("temp_exterior")) if ultima_clima else None,
        "punto_rocio_c": f_a_c(ultima_clima.get("punto_rocio")) if ultima_clima else None,
        "presion_inhg": numero(ultima_clima.get("presion"), 3),
        "viento_kmh": mph_a_kmh(ultima_clima.get("viento_vel")) if ultima_clima else None,
        "viento_dir_deg": numero(ultima_clima.get("viento_dir"), 0),
        "lluvia_hora_mm": numero(ultima_clima.get("lluvia_hora"), 2),
        "radiacion_solar_wm2": numero(ultima_clima.get("radiacion_solar"), 1),
        "uv": numero(ultima_clima.get("uv"), 1),
    }
    data = {
        "actualizado": timestamp_ahora(),
        "kpis": kpis,
        "sistema": estado_sistema(),
        "series": {
            "labels": labels,
            "labels_nivel": labels_nivel,
            "nivel_l": nivel_l,
            "humedad_pct": humedad,
            "temp_c": temp_c,
            "punto_rocio_c": rocio_c,
            "presion_inhg": presion,
            "viento_kmh": viento,
            "viento_dir_deg": dir_v,
            "lluvia_hora_mm": lluvia,
            "radiacion_solar_wm2": solar,
            "uv": uv,
        },
    }
    with open(RUTA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[OK] dashboard_data.json generado: {timestamp_ahora()}")
    return data


if __name__ == "__main__":
    data = generar_dashboard_json()
    print(f"KPIs: {data['kpis']}")
