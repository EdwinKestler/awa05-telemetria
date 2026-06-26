import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from awa05.drivers.ws2000 import (  # noqa: E402,F401
    RUTA_CLIMA,
    WS2000Receiver,
    create_app,
    iniciar_servidor,
)


app = None


if __name__ == "__main__":
    iniciar_servidor()
