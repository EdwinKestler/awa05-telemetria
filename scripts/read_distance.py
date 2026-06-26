import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awa05.sensors.distance import *  # noqa: F401,F403


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.WARNING)
    print("=== Prueba JSN-SR04T — AWA05 ===")
    dist, vol = leer_nivel()
    if dist is not None:
        print(f"Resultado: {dist} cm | {vol} L")
    else:
        print("Sin lectura. Revisar conexion del sensor.")
