import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awa05.drivers.weight import (  # noqa: E402,F401
    SimulatedWeightSensor,
    UnavailableWeightSensor,
    leer_peso,
)
from awa05.utils import timestamp_ahora  # noqa: E402


def leer_peso_simulado():
    """Retorna un peso simulado para pruebas sin hardware."""
    return SimulatedWeightSensor().read()


if __name__ == "__main__":
    peso = leer_peso_simulado()
    print(f"[{timestamp_ahora()}] Peso simulado: {peso} kg")
