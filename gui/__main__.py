"""
Permite executar a GUI como módulo:
    python -m gui
    ou
    python -m gui.app
"""

import os
import sys

# Garante que o diretório raiz do projeto esteja no sys.path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_THIS_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from gui.app import run

if __name__ == "__main__":
    run()
