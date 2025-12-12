"""
Point d'entrée principal de l'application d'optimisation de capacité réseau
Lance l'interface graphique
"""

import sys
from PySide6.QtWidgets import QApplication
from topology_ui import MainWindow


def main():
    """Fonction principale qui démarre l'application"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
