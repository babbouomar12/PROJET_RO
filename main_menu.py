import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import subprocess


# On importe les fenêtres des projets
from Probleme10.JobShopWindow import MainWindow as JobShopWindow
from Probleme12.topology_ui import MainWindow as CapacityNetworkWindow
from Probleme11 import BinPackingWindow
from Probleme14.main import MainWindow as MinCostFlowWindow


class MainMenuWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.jobshop_window = None  # on stockera ici la fenêtre du problème 10
        self.capacity_network_window = None  # on stockera ici la fenêtre du problème 12
        self.bin_packing_window = None  # on stockera ici la fenêtre du problème 11
        self.min_cost_flow_window = None  # on stockera ici la fenêtre du problème 14
        #Initiliasation de ma fenetre principale
        self.setWindowTitle("Menu commun - Problèmes 10 à 14, Application 5 (Énergie)")
        self.resize(1300, 700)

        # --- Widget central ---
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(30)
        central.setLayout(main_layout)

        # --- Titre principal ---
        title_label = QLabel("Interface commune – Projets RO (Application 5 : Énergie)")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("Choisissez le problème à explorer")
        subtitle_font = QFont()
        subtitle_font.setPointSize(11)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("color: #9CA3AF;")

        main_layout.addWidget(title_label)
        main_layout.addWidget(subtitle_label)

        # --- Groupe des problèmes ---
        group = QGroupBox("Problèmes 10 à 14 – Application 5 : Énergie")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(20, 20, 20, 20)
        group_layout.setSpacing(12)
        group.setLayout(group_layout)

        # Boutons des 5 problèmes
        btn10 = self.create_problem_button(
            "10. Ordonnancement d’Atelier – Énergie : Ordonnancement des tests sur les éoliennes",
            ""
        )
        btn11 = self.create_problem_button(
            "11. Stockage / Emballage – Énergie : Problème de Bin Packing appliqué à l’énergie",
            ""
        )
        btn12 = self.create_problem_button(
            "12. Capacité de Réseau – Énergie : Dimensionnement des lignes de transport d’énergie",
            ""
        )
        btn13 = self.create_problem_button(
            "13. Problème d'Optimisation d'Appariement des Équipages Aériens",
            ""
        )
        btn14 = self.create_problem_button(
            "14. Flux à Coût Minimum – Énergie: Acheminement optimal de flux d’énergie dans un réseau",
            ""
        )

        group_layout.addWidget(btn10)
        group_layout.addWidget(btn11)
        group_layout.addWidget(btn12)
        group_layout.addWidget(btn13)
        group_layout.addWidget(btn14)

        main_layout.addWidget(group)

        # --- Connexions des boutons ---
        btn10.clicked.connect(self.open_problem_10)
        btn11.clicked.connect(self.open_problem_11)
        btn12.clicked.connect(self.open_problem_12)
        btn13.clicked.connect(self.open_problem_13)
        btn14.clicked.connect(self.open_problem_14)

        # --- Style global sombre ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #020617;
            }
            QLabel {
                color: #E5E7EB;
            }
            QGroupBox {
                color: #E5E7EB;
                border: 1px solid #374151;
                border-radius: 12px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 4px 0 4px;
                color: #9CA3AF;
            }
        """)

    def create_problem_button(self, title: str, subtitle: str) -> QPushButton:
        """
        Crée un bouton "carte" avec titre + sous-titre,
        sans HTML, tout stylé avec Qt Stylesheet.
        """
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        btn.setMinimumHeight(70)
        btn.setCheckable(False)

        # Texte sur deux lignes
        btn.setText(f"{title}\n{subtitle}")

        # Police
        font = QFont()
        font.setPointSize(11)
        btn.setFont(font)

        # Style du bouton type "carte"
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 16px;
                border-radius: 14px;
                background-color: #020617;
                border: 1px solid #111827;
                color: #E5E7EB;
            }
            QPushButton:hover {
                background-color: #111827;
                border: 1px solid #2563EB;
            }
            QPushButton:pressed {
                background-color: #0B1120;
                border: 1px solid #1D4ED8;
            }
        """)
        return btn

    # --- Fonctions à relier aux projets de ton équipe ---

    def open_problem_10(self):
        """Ouvre la fenêtre du problème 10 (Job Shop – tests sur les éoliennes)."""
        if self.jobshop_window is None:
            # On crée la fenêtre une seule fois
            self.jobshop_window = JobShopWindow()

        # On affiche la fenêtre
        self.jobshop_window.show()
        self.jobshop_window.raise_()
        self.jobshop_window.activateWindow()


    def open_problem_11(self):
        """Ouvre la fenêtre du problème 11 (Bin Packing - Énergie)."""
        if self.bin_packing_window is None:
            # On crée la fenêtre une seule fois
            self.bin_packing_window = BinPackingWindow()

        # On affiche la fenêtre
        self.bin_packing_window.show()
        self.bin_packing_window.raise_()
        self.bin_packing_window.activateWindow()

    def open_problem_12(self):
        """Ouvre la fenêtre du problème 12 (Capacité de Réseau – Énergie)."""
        if self.capacity_network_window is None:
            # On crée la fenêtre une seule fois
            self.capacity_network_window = CapacityNetworkWindow()

        # On affiche la fenêtre
        self.capacity_network_window.show()
        self.capacity_network_window.raise_()
        self.capacity_network_window.activateWindow()

    def open_problem_13(self):
        print("Ouvrir le projet 13 : Problème d'Optimisation d'Appariement des Équipages Aériens")
        subprocess.Popen([sys.executable, "Probleme13/main.py"])


    def open_problem_14(self):
        """Ouvre la fenêtre du problème 14 (Flux à Coût Minimum – Énergie)."""
        if self.min_cost_flow_window is None:
            # On crée la fenêtre une seule fois
            self.min_cost_flow_window = MinCostFlowWindow()

        # On affiche la fenêtre
        self.min_cost_flow_window.show()
        self.min_cost_flow_window.raise_()
        self.min_cost_flow_window.activateWindow()


def main():
    app = QApplication(sys.argv)
    window = MainMenuWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
