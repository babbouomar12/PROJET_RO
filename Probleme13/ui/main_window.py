# ui/main_window.py
"""
MainWindow - Fenêtre principale moderne et simplifiée
"""
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Modules locaux
from models.data_model import DataModel
from models.gurobi_solver import GurobiSolver
from widgets.flight_table import FlightTableWidget
from widgets.crew_table import CrewTableWidget
from widgets.solution_viz import SolutionVisualizationWidget

PRIMARY_COLOR = "#4F6EF7"
ACCENT_COLOR = "#2ECC71"
BACKGROUND_DARK = "#1E1E1E"
BACKGROUND_LIGHT = "#2b2d31"
TEXT_LIGHT = "#f0f0f0"
FONT_FAMILY = "Segoe UI"


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application - Version simplifiée"""

    def __init__(self):
        super().__init__()
        self.data_model = DataModel()
        self.solver_thread = None
        self.initUI()
        self.load_example_data()

    def initUI(self):
        self.setWindowTitle("✈️ Optimisation d'Affectation d'Équipage")
        self.setGeometry(100, 100, 1400, 800)

        # Style de la fenêtre
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BACKGROUND_DARK};
            }}
        """)

        # Créer les onglets (sans barre de menu)
        self.create_tabs()

        # Configurer le widget central
        self.setup_central_widget()

        # Barre de statut simple
        self.statusBar().showMessage("Prêt")

    def create_tabs(self):
        """Crée les onglets avec style moderne"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(False)
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #444;
                border-radius: 8px;
                background-color: {BACKGROUND_DARK};
                margin-top: -1px;
            }}
            QTabBar::tab {{
                background-color: {BACKGROUND_LIGHT};
                color: {TEXT_LIGHT};
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-family: {FONT_FAMILY};
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #444;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background-color: {PRIMARY_COLOR};
                color: white;
                border-color: {PRIMARY_COLOR};
            }}
            QTabBar::tab:hover {{
                background-color: #3a3c40;
            }}
        """)

        # Onglet Paramètres
        self.create_parameters_tab()

        # Onglet Vols
        self.flight_tab = FlightTableWidget(self.data_model)
        self.tab_widget.addTab(self.flight_tab, "✈️ Vols")

        # Onglet Pilotes
        self.pilot_tab = CrewTableWidget(self.data_model, is_pilots=True)
        self.tab_widget.addTab(self.pilot_tab, "👨‍✈️ Pilotes")

        # Onglet Copilotes
        self.copilot_tab = CrewTableWidget(self.data_model, is_pilots=False)
        self.tab_widget.addTab(self.copilot_tab, "👨‍✈️ Copilotes")

        # Onglet Résultats
        self.results_tab = SolutionVisualizationWidget()
        self.tab_widget.addTab(self.results_tab, "📊 Résultats")

    def create_parameters_tab(self):
        """Crée l'onglet des paramètres"""
        tab = QWidget()
        tab.setStyleSheet(f"background-color: {BACKGROUND_DARK};")

        # ScrollArea pour les paramètres
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2b2d31;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #4F6EF7;
                border-radius: 5px;
                min-height: 20px;
            }
        """)

        content = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Titre principal
        title_label = QLabel("⚙️ Paramètres de l'Optimisation")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #4F6EF7;
                padding-bottom: 15px;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Carte des paramètres principaux
        main_params_card = QFrame()
        main_params_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BACKGROUND_LIGHT};
                border: 1px solid #444;
                border-radius: 12px;
                padding: 25px;
            }}
        """)

        main_form = QFormLayout()
        main_form.setSpacing(20)

        # Repos minimum
        self.min_rest_spin = QSpinBox()
        self.min_rest_spin.setRange(0, 24)
        self.min_rest_spin.setValue(8)
        self.min_rest_spin.setSuffix(" heures")
        self.min_rest_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px;
                border: 1px solid #555;
                border-radius: 8px;
                background-color: #35373b;
                color: white;
                font-size: 14px;
                min-width: 150px;
            }
        """)
        main_form.addRow("🕐 Temps de repos minimum:", self.min_rest_spin)

        # Pénalité de base
        self.penalty_spin = QSpinBox()
        self.penalty_spin.setRange(0, 1000)
        self.penalty_spin.setValue(100)
        self.penalty_spin.setPrefix("€ ")
        self.penalty_spin.setStyleSheet("""
            QSpinBox {
                padding: 10px;
                border: 1px solid #555;
                border-radius: 8px;
                background-color: #35373b;
                color: white;
                font-size: 14px;
                min-width: 150px;
            }
        """)
        main_form.addRow("💰 Pénalité de base:", self.penalty_spin)

        main_params_card.setLayout(main_form)
        layout.addWidget(main_params_card)

        # Carte du paramètre lambda
        lambda_card = QFrame()
        lambda_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BACKGROUND_LIGHT};
                border: 1px solid #444;
                border-radius: 12px;
                padding: 25px;
            }}
        """)

        lambda_layout = QVBoxLayout()
        lambda_layout.setSpacing(15)

        # Titre lambda
        lambda_title = QLabel("⚖️ Priorité d'Optimisation (λ)")
        lambda_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #f0f0f0;
                padding-bottom: 10px;
            }
        """)
        lambda_layout.addWidget(lambda_title)

        # Slider lambda
        slider_container = QHBoxLayout()
        slider_container.setSpacing(20)

        self.lambda_slider = QSlider(Qt.Horizontal)
        self.lambda_slider.setRange(0, 100)
        self.lambda_slider.setValue(50)
        self.lambda_slider.setMinimumWidth(300)
        self.lambda_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 8px;
                background: #3a3c40;
                margin: 0px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #2ECC71;
                border: 2px solid #444;
                width: 22px;
                margin: -7px 0;
                border-radius: 11px;
            }
        """)

        self.lambda_label = QLabel("0.50")
        self.lambda_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2ECC71;
                min-width: 60px;
                text-align: center;
            }
        """)

        self.lambda_slider.valueChanged.connect(self.update_lambda)
        slider_container.addWidget(self.lambda_slider)
        slider_container.addWidget(self.lambda_label)
        lambda_layout.addLayout(slider_container)

        # Échelle de valeurs
        scale_container = QHBoxLayout()

        left_label = QLabel("Minimiser les coûts")
        left_label.setStyleSheet("color: #888; font-size: 13px;")

        right_label = QLabel("Maximiser les vols")
        right_label.setStyleSheet("color: #888; font-size: 13px;")

        scale_container.addWidget(left_label)
        scale_container.addStretch()
        scale_container.addWidget(right_label)
        lambda_layout.addLayout(scale_container)

        # Description
        description = QLabel(
            "Le paramètre λ contrôle le compromis entre le nombre de vols assignés "
            "et le coût total. À λ=0, on privilégie les coûts bas. À λ=1, on maximise "
            "le nombre de vols couverts."
        )
        description.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 13px;
                font-style: italic;
                padding-top: 10px;
                line-height: 1.4;
            }
        """)
        description.setWordWrap(True)
        lambda_layout.addWidget(description)

        lambda_card.setLayout(lambda_layout)
        layout.addWidget(lambda_card)

        # Boutons d'action
        buttons_card = QFrame()
        buttons_card.setStyleSheet(f"""
            QFrame {{
                background-color: {BACKGROUND_LIGHT};
                border: 1px solid #444;
                border-radius: 12px;
                padding: 25px;
            }}
        """)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Bouton Exemple
        example_btn = QPushButton("📥 Charger l'exemple")
        example_btn.clicked.connect(self.load_example_data)
        example_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #3a3c40;
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #555;
                min-width: 180px;
            }}
            QPushButton:hover {{
                background-color: #4a4c50;
                border-color: #666;
            }}
        """)
        buttons_layout.addWidget(example_btn)

        # Bouton Effacer
        clear_btn = QPushButton("🗑️ Effacer tout")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #E74C3C;
                color: white;
                padding: 15px 25px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #C0392B;
                min-width: 180px;
            }}
            QPushButton:hover {{
                background-color: #FF6B6B;
                border-color: #E74C3C;
            }}
        """)
        buttons_layout.addWidget(clear_btn)

        # Bouton Principal
        solve_btn = QPushButton("🚀 Lancer l'optimisation")
        solve_btn.clicked.connect(self.run_solver)
        solve_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: white;
                padding: 18px 35px;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
                border: none;
                min-width: 250px;
            }}
            QPushButton:hover {{
                background-color: #27AE60;
            }}
            QPushButton:pressed {{
                background-color: #219653;
            }}
        """)
        buttons_layout.addWidget(solve_btn)

        buttons_card.setLayout(buttons_layout)
        layout.addWidget(buttons_card)

        # Espace vide en bas
        layout.addStretch()

        content.setLayout(layout)
        scroll.setWidget(content)

        # Layout pour le tab
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)

        self.tab_widget.addTab(tab, "⚙️ Paramètres")

    def setup_central_widget(self):
        """Configure le widget central"""
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {BACKGROUND_DARK};")

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Ajouter uniquement les onglets (pas de logs)
        layout.addWidget(self.tab_widget)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    # ---------------- UI et Data ----------------
    def update_lambda(self, value):
        """Met à jour la valeur lambda"""
        lambda_val = value / 100.0
        self.lambda_label.setText(f"{lambda_val:.2f}")
        self.data_model.lambda_weight = lambda_val

    def load_example_data(self):
        """Charge les données d'exemple"""
        self.data_model.load_example_data()
        self.update_ui_from_model()
        self.show_status_message("✅ Données d'exemple chargées", 3000)

    def clear_all(self):
        """Efface toutes les données"""
        reply = QMessageBox.question(self, 'Confirmation',
                                     'Voulez-vous vraiment effacer toutes les données?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.data_model.clear()
            self.update_ui_from_model()
            self.show_status_message("🗑️ Toutes les données ont été effacées", 3000)

    def update_ui_from_model(self):
        """Met à jour l'UI depuis le modèle"""
        if hasattr(self, 'min_rest_spin'):
            self.min_rest_spin.setValue(self.data_model.min_rest)
        if hasattr(self, 'penalty_spin'):
            self.penalty_spin.setValue(self.data_model.base_penalty_coeff)
        if hasattr(self, 'lambda_slider'):
            self.lambda_slider.setValue(int(self.data_model.lambda_weight * 100))
            self.lambda_label.setText(f"{self.data_model.lambda_weight:.2f}")

        if hasattr(self, 'flight_tab') and hasattr(self.flight_tab, 'load_from_model'):
            self.flight_tab.load_from_model()
        if hasattr(self, 'pilot_tab') and hasattr(self.pilot_tab, 'load_from_model'):
            self.pilot_tab.load_from_model()
        if hasattr(self, 'copilot_tab') and hasattr(self.copilot_tab, 'load_from_model'):
            self.copilot_tab.load_from_model()

    def save_all_data(self):
        """Sauvegarde toutes les données"""
        self.data_model.min_rest = self.min_rest_spin.value()
        self.data_model.base_penalty_coeff = self.penalty_spin.value()
        if hasattr(self.flight_tab, 'save_to_model'):
            self.flight_tab.save_to_model()
        if hasattr(self.pilot_tab, 'save_to_model'):
            self.pilot_tab.save_to_model()
        if hasattr(self.copilot_tab, 'save_to_model'):
            self.copilot_tab.save_to_model()

    # ---------------- Solveur ----------------
    def run_solver(self):
        """Lance le solveur"""
        self.save_all_data()
        if (len(self.data_model.flights) == 0 or
                len(self.data_model.pilots) == 0 or
                len(self.data_model.copilots) == 0):
            QMessageBox.warning(self, "Données manquantes",
                                "Veuillez entrer des données pour les vols, pilotes et copilotes.")
            return

        # Désactiver l'interface pendant la résolution
        self.tab_widget.setEnabled(False)
        self.show_status_message("🔄 Résolution en cours...")

        # Créer et lancer le thread du solveur
        self.solver_thread = GurobiSolver(self.data_model)
        self.solver_thread.finished_signal.connect(self.on_solver_finished)
        self.solver_thread.start()

    def on_solver_finished(self, results):
        """Appelé quand le solveur a fini"""
        # Réactiver l'interface
        self.tab_widget.setEnabled(True)

        if 'error' in results:
            QMessageBox.critical(self, "Erreur", f"Erreur: {results['error']}")
            self.show_status_message("❌ Erreur lors de la résolution", 5000)
            return

        self.data_model.solution = results.get('solution')
        self.data_model.objective_value = results.get('objective_value')

        if hasattr(self.results_tab, 'update_solution'):
            self.results_tab.update_solution(self.data_model, results)

        # Aller à l'onglet des résultats
        self.tab_widget.setCurrentIndex(4)
        self.show_status_message("✅ Résolution terminée avec succès!", 3000)

    def show_status_message(self, message, timeout=3000):
        """Affiche un message dans la barre de statut"""
        self.statusBar().showMessage(message, timeout)

    # ---------------- Événements de fermeture ----------------
    def closeEvent(self, event):
        """Gère la fermeture de la fenêtre"""
        if self.solver_thread and self.solver_thread.isRunning():
            reply = QMessageBox.question(self, "Solveur en cours",
                                         "Le solveur est en cours d'exécution. Voulez-vous vraiment quitter?",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.solver_thread.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ---------------- Thème de l'application ----------------
def apply_modern_theme(app):
    """Applique un thème moderne à l'application"""
    # Palette sombre
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(BACKGROUND_DARK))
    palette.setColor(QPalette.WindowText, QColor(TEXT_LIGHT))
    palette.setColor(QPalette.Base, QColor(BACKGROUND_LIGHT))
    palette.setColor(QPalette.AlternateBase, QColor("#35373b"))
    palette.setColor(QPalette.Text, QColor(TEXT_LIGHT))
    palette.setColor(QPalette.Button, QColor(BACKGROUND_LIGHT))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_LIGHT))
    palette.setColor(QPalette.Highlight, QColor(PRIMARY_COLOR))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)

    # Style Fusion
    app.setStyle("Fusion")

    # StyleSheet global minimal
    app.setStyleSheet(f"""
        /* Widgets de base */
        QWidget {{
            font-family: {FONT_FAMILY};
            font-size: 13px;
            color: {TEXT_LIGHT};
        }}

        /* Boutons */
        QPushButton {{
            background-color: {BACKGROUND_LIGHT};
            color: {TEXT_LIGHT};
            border: 1px solid #444;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: #3a3c40;
            border-color: #555;
        }}

        QPushButton:pressed {{
            background-color: {PRIMARY_COLOR};
        }}

        /* Entrées */
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: #35373b;
            border: 1px solid #555;
            border-radius: 6px;
            padding: 8px;
            selection-background-color: {PRIMARY_COLOR};
        }}

        /* GroupBox */
        QGroupBox {{
            font-weight: bold;
            border: 2px solid #444;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
        }}

        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px;
            color: {PRIMARY_COLOR};
        }}

        /* MessageBox */
        QMessageBox {{
            background-color: {BACKGROUND_DARK};
        }}

        QMessageBox QLabel {{
            color: {TEXT_LIGHT};
        }}

        /* FileDialog */
        QFileDialog {{
            background-color: {BACKGROUND_DARK};
            color: {TEXT_LIGHT};
        }}

        /* StatusBar */
        QStatusBar {{
            background-color: {BACKGROUND_LIGHT};
            color: {TEXT_LIGHT};
            border-top: 1px solid #444;
            padding: 5px;
        }}
    """)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Appliquer le thème moderne
    apply_modern_theme(app)

    # Créer et afficher la fenêtre
    window = MainWindow()
    window.show()

    sys.exit(app.exec_())