import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from awa05.upload.github import *  # noqa: F401,F403

if __name__ == "__main__":
    subir_archivos()
