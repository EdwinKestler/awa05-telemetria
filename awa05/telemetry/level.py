from awa05.sensors.distance import leer_nivel
from awa05.utils import guardar_csv, ruta_proyecto, timestamp_ahora


RUTA_RAW = ruta_proyecto("data/raw/nivel_raw.csv")


def tomar_lectura(sensor=None):
    distancia, volumen = leer_nivel(sensor=sensor)
    if distancia is None:
        print("[SKIP] Lectura descartada, sin respuesta del sensor.")
        return
    fila = {
        "timestamp": timestamp_ahora(),
        "distancia_cm": distancia,
        "volumen_litros": volumen,
    }
    guardar_csv(RUTA_RAW, fila)
    print(f"[{fila['timestamp']}] Nivel: {distancia} cm | Volumen: {volumen} L")


if __name__ == "__main__":
    print("Sistema AWA05 iniciado.")
    tomar_lectura()
