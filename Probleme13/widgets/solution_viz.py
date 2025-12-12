# widgets/solution_viz.py - VERSION RESPONSIVE
"""
SolutionVisualizationWidget - Version responsive avec scrolling correct
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np


class MetricCard(QFrame):
    """Carte de métrique réutilisable"""

    def __init__(self, title, value, color="#4F6EF7", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.color = color
        self.initUI()

    def initUI(self):
        self.setMinimumWidth(180)
        self.setMaximumWidth(250)

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Titre
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #aaa;
                font-weight: bold;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Valeur
        self.value_label = QLabel(self.value)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: {self.color};
            }}
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #444;")
        separator.setMaximumHeight(1)
        layout.addWidget(separator)

        # Icône
        icon_label = QLabel(self.get_icon())
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                color: {self.color};
            }}
        """)
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        self.setLayout(layout)

    def get_icon(self):
        """Retourne l'icône appropriée selon le titre"""
        icons = {
            "Vols Assignés": "✈️",
            "Coût Total": "💰",
            "Taux Couverture": "📈",
            "Équipage Utilisé": "👨‍✈️",
            "Temps de Résolution": "⏱️"
        }
        return icons.get(self.title, "📊")

    def update_value(self, new_value):
        """Met à jour la valeur affichée"""
        self.value_label.setText(new_value)


class SolutionVisualizationWidget(QWidget):
    """Widget pour visualiser les résultats - Version responsive"""

    def __init__(self):
        super().__init__()
        self.assignments = []
        self.data_model = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container principal avec onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 0px;
                background: #1E1E1E;
                margin: 0px;
            }
            QTabBar::tab {
                background: #2b2d31;
                padding: 12px 20px;
                border-radius: 0px;
                margin-right: 1px;
                font-weight: bold;
                color: #aaa;
                border: 1px solid #444;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #4F6EF7;
                color: white;
                border-bottom: 2px solid #4F6EF7;
            }
            QTabBar::tab:hover {
                background: #3a3c40;
            }
        """)

        # Onglet 1: Dashboard (avec ScrollArea)
        self.create_dashboard_tab()

        # Onglet 2: Détails complets (avec ScrollArea)
        self.create_details_tab()

        # Onglet 3: Graphique avancé (avec ScrollArea)
        self.create_graph_tab()

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Initialiser un graphique vide
        self.update_empty_plot()

    def create_dashboard_tab(self):
        """Onglet Dashboard avec vue d'ensemble"""
        # Créer un widget container avec ScrollArea
        tab = QWidget()

        # ScrollArea principale
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2b2d31;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4F6EF7;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6d88ff;
            }
            QScrollBar:horizontal {
                background: #2b2d31;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #4F6EF7;
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #6d88ff;
            }
        """)

        # Widget contenu
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QHBoxLayout()

        title_label = QLabel("📊 Tableau de Bord")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #4F6EF7;
            }
        """)
        header.addWidget(title_label)
        header.addStretch()

        # Badge de statut
        self.status_badge = QLabel("● EN ATTENTE")
        self.status_badge.setStyleSheet("""
            QLabel {
                background-color: #2b2d31;
                color: #3498DB;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 16px;
                font-size: 11px;
                border: 1px solid #444;
            }
        """)
        header.addWidget(self.status_badge)
        content_layout.addLayout(header)

        # Container pour les métriques (responsive)
        metrics_container = QWidget()
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(15)
        metrics_layout.setContentsMargins(0, 0, 0, 0)

        # Créer les cartes de métriques
        self.metric_vols = MetricCard("Vols Assignés", "0/0", "#4F6EF7")
        self.metric_cout = MetricCard("Coût Total", "€0", "#2ECC71")
        self.metric_taux = MetricCard("Taux Couverture", "0%", "#F39C12")
        self.metric_temps = MetricCard("Temps de Résolution", "0s", "#9B59B6")

        # Ajouter les métriques avec stretching
        metrics_layout.addWidget(self.metric_vols, 0, 0)
        metrics_layout.addWidget(self.metric_cout, 0, 1)
        metrics_layout.addWidget(self.metric_taux, 1, 0)
        metrics_layout.addWidget(self.metric_temps, 1, 1)

        # Configurer les colonnes pour s'étirer
        metrics_layout.setColumnStretch(0, 1)
        metrics_layout.setColumnStretch(1, 1)
        metrics_layout.setRowStretch(0, 1)
        metrics_layout.setRowStretch(1, 1)

        metrics_container.setLayout(metrics_layout)
        content_layout.addWidget(metrics_container)

        # Section Dernières Affectations
        section_title = QLabel("🔄 Dernières Affectations")
        section_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                margin-top: 10px;
                margin-bottom: 10px;
            }
        """)
        content_layout.addWidget(section_title)

        # Liste des dernières affectations
        self.recent_assignments = QTextEdit()
        self.recent_assignments.setReadOnly(True)
        self.recent_assignments.setMinimumHeight(150)
        self.recent_assignments.setMaximumHeight(250)
        self.recent_assignments.setStyleSheet("""
            QTextEdit {
                background-color: #2b2d31;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #f0f0f0;
            }
        """)
        self.recent_assignments.setHtml("<i>Aucune affectation disponible. Lancez une optimisation.</i>")
        content_layout.addWidget(self.recent_assignments)

        # Statistiques rapides
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2d31;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 15px;
                margin-top: 10px;
            }
        """)

        stats_layout = QVBoxLayout()
        stats_title = QLabel("📈 Vue d'ensemble")
        stats_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
                margin-bottom: 10px;
            }
        """)
        stats_layout.addWidget(stats_title)

        self.stats_text = QLabel("Statistiques non disponibles")
        self.stats_text.setStyleSheet("""
            QLabel {
                color: #aaa;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        self.stats_text.setWordWrap(True)
        stats_layout.addWidget(self.stats_text)

        stats_frame.setLayout(stats_layout)
        content_layout.addWidget(stats_frame)

        content_layout.addStretch()
        content_widget.setLayout(content_layout)

        # Définir une politique de taille minimale
        content_widget.setMinimumSize(600, 600)

        scroll_area.setWidget(content_widget)

        # Layout pour le tab
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll_area)
        tab.setLayout(tab_layout)

        self.tab_widget.addTab(tab, "📊 Dashboard")

    def create_details_tab(self):
        """Onglet avec tous les détails"""
        tab = QWidget()

        # ScrollArea principale
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2b2d31;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #4F6EF7;
                border-radius: 6px;
                min-height: 30px;
            }
        """)

        # Widget contenu
        content = QWidget()
        content.setMinimumWidth(800)  # Largeur minimale

        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Titre principal
        title = QLabel("📋 Détails Complets des Résultats")
        title.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #4F6EF7;
                padding-bottom: 10px;
                border-bottom: 2px solid #444;
            }
        """)
        content_layout.addWidget(title)

        # Section Informations Générales
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2d31;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        info_layout = QVBoxLayout()
        info_title = QLabel("📄 Informations de l'Optimisation")
        info_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                margin-bottom: 15px;
            }
        """)
        info_layout.addWidget(info_title)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(180)
        self.info_text.setMaximumHeight(250)
        self.info_text.setStyleSheet("""
            QTextEdit {
                background-color: #35373b;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #f0f0f0;
                selection-background-color: #4F6EF7;
            }
        """)
        self.info_text.setHtml("""
            <div style='color: #888; font-style: italic; text-align: center; padding: 40px;'>
                Aucune information disponible. Lancez une optimisation d'abord.
            </div>
        """)
        info_layout.addWidget(self.info_text)

        info_frame.setLayout(info_layout)
        content_layout.addWidget(info_frame)

        # Section Affectations Détaillées - AGRANDIE
        assignments_frame = QFrame()
        assignments_frame.setStyleSheet("""
            QFrame {
                background-color: #2b2d31;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 20px;
            }
        """)

        assignments_layout = QVBoxLayout()
        assignments_title = QLabel("✈️ Liste Complète des Affectations")
        assignments_title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                margin-bottom: 15px;
            }
        """)
        assignments_layout.addWidget(assignments_title)

        # Container pour le tableau avec scroll
        table_container = QWidget()
        table_container_layout = QVBoxLayout()
        table_container_layout.setContentsMargins(0, 0, 0, 0)

        # Tableau des affectations - AGRANDI
        self.assignments_table = QTableWidget()
        self.assignments_table.setColumnCount(6)
        self.assignments_table.setHorizontalHeaderLabels([
            "Vol", "Départ", "Arrivée", "Durée", "Pilote", "Copilote"
        ])
        self.assignments_table.setStyleSheet("""
            QTableWidget {
                background-color: #35373b;
                border: 1px solid #555;
                border-radius: 8px;
                gridline-color: #444;
                alternate-background-color: #2b2d31;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #3a3c40;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
                color: white;
            }
            QTableWidget::item:selected {
                background-color: #4F6EF7;
                color: white;
            }
        """)
        self.assignments_table.horizontalHeader().setStretchLastSection(True)
        self.assignments_table.verticalHeader().setDefaultSectionSize(40)
        self.assignments_table.setMinimumHeight(400)  # Augmenté de 200 à 400
        self.assignments_table.setMaximumHeight(800)  # Augmenté de 400 à 800

        # Ajouter le tableau à un QScrollArea
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setWidget(self.assignments_table)
        table_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        table_scroll.setMinimumHeight(450)  # Hauteur minimale pour le scroll
        table_scroll.setMaximumHeight(850)  # Hauteur maximale pour le scroll

        table_container_layout.addWidget(table_scroll)
        table_container.setLayout(table_container_layout)
        assignments_layout.addWidget(table_container)
        assignments_frame.setLayout(assignments_layout)
        content_layout.addWidget(assignments_frame)

        content_layout.addStretch()
        content.setLayout(content_layout)
        scroll.setWidget(content)

        # Layout pour le tab
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)

        self.tab_widget.addTab(tab, "📋 Détails")



    def create_graph_tab(self):
        """Onglet avec visualisation graphique avancée"""
        tab = QWidget()

        # ScrollArea pour le graphique
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        # Widget contenu
        content = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Titre
        title = QLabel("📈 Visualisation Graphique")
        title.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #4F6EF7;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)

        # Container pour le graphique
        graph_container = QFrame()
        graph_container.setStyleSheet("""
            QFrame {
                background-color: #2b2d31;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 15px;
            }
        """)

        graph_layout = QVBoxLayout()

        # Figure Matplotlib
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.figure.patch.set_facecolor('#2b2d31')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(600, 400)

        # Barre d'outils de navigation
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #2b2d31;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 5px;
                spacing: 5px;
            }
            QToolButton {
                background-color: #35373b;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                color: white;
                min-width: 30px;
                min-height: 30px;
            }
            QToolButton:hover {
                background-color: #4F6EF7;
            }
        """)

        graph_layout.addWidget(self.toolbar)
        graph_layout.addWidget(self.canvas)

        # Légende
        legend_frame = QFrame()
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(20)

        legend_items = [
            ("■", "#4F6EF7", "Pilote"),
            ("■", "#2ECC71", "Copilote"),
            ("■", "#F39C12", "Vol"),
            ("■", "#9B59B6", "Repos")
        ]

        for symbol, color, text in legend_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(5)
            symbol_label = QLabel(symbol)
            symbol_label.setStyleSheet(f"color: {color}; font-size: 18px;")
            text_label = QLabel(text)
            text_label.setStyleSheet("color: #aaa; font-size: 13px; font-weight: bold;")
            item_layout.addWidget(symbol_label)
            item_layout.addWidget(text_label)
            legend_layout.addLayout(item_layout)

        legend_layout.addStretch()
        legend_frame.setLayout(legend_layout)
        graph_layout.addWidget(legend_frame)

        graph_container.setLayout(graph_layout)
        layout.addWidget(graph_container)

        content.setLayout(layout)
        scroll.setWidget(content)

        # Layout pour le tab
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)

        self.tab_widget.addTab(tab, "📈 Graphique")

    def resizeEvent(self, event):
        """Redimensionnement de la fenêtre"""
        super().resizeEvent(event)
        # Forcer la mise à jour des layouts
        self.updateGeometry()

    def update_solution(self, data_model, results):
        """Mettre à jour l'affichage avec la nouvelle solution"""
        self.data_model = data_model

        print("=== DEBUG RESULTS ===")
        print(f"Results keys: {results.keys()}")
        if 'assignments' in results:
            print(f"Number of assignments: {len(results['assignments'])}")
        if 'total_cost' in results:
            print(f"Total cost in results: {results['total_cost']}")
        print("====================")

        # Extraire les affectations
        self.assignments = []

        if 'assignments' in results and results['assignments']:
            # Format direct depuis GurobiSolver
            self.assignments = results['assignments']
            print(f"DEBUG: {len(self.assignments)} assignments from results")

        elif 'solution' in results and results['solution']:
            # Convertir l'ancien format
            print("DEBUG: Converting old format solution")
            for (f_idx, p_idx, c_idx), value in results['solution'].items():
                if value > 0.5:
                    try:
                        flight = data_model.flights[f_idx]
                        pilot = data_model.pilots[p_idx]
                        copilot = data_model.copilots[c_idx]

                        # Calculer le coût manuellement
                        flight_cost = self.calculate_manual_cost(flight, pilot, copilot, data_model)

                        self.assignments.append({
                            'vol': flight.get('id', f'AF{f_idx + 1:04d}'),
                            'pilote': pilot.get('name', f'Pilote {p_idx + 1}'),
                            'copilote': copilot.get('name', f'Copilote {c_idx + 1}'),
                            'heure_depart': flight.get('departure', 8),
                            'heure_arrivee': flight.get('arrival', 10),
                            'duree': flight.get('duration', 2),
                            'aircraft': flight.get('aircraft_type', 'A320'),
                            'cout': flight_cost,
                            'cost': flight_cost
                        })
                    except Exception as e:
                        print(f"Erreur extraction: {e}")
                        continue

        # Calculer le coût total
        total_cost = results.get('total_cost', 0)
        if total_cost == 0 and self.assignments:
            total_cost = sum(assign.get('cout', assign.get('cost', 0)) for assign in self.assignments)

        print(f"DEBUG: Total cost: €{total_cost:,.0f}")

        # Mettre à jour le badge de statut
        status = results.get('status_str', 'INCONNU')
        self.update_status_badge(status)

        # Mettre à jour les métriques
        self.update_metrics(data_model, results, total_cost)

        # Mettre à jour les détails textuels
        self.update_text_details(data_model, results, total_cost)

        # Mettre à jour le tableau
        self.update_assignments_table()

        # Mettre à jour le graphique
        self.update_graph()
    def update_status_badge(self, status):
        """Mettre à jour le badge de statut"""
        status_color = {
            'OPTIMAL': '#2ECC71',
            'FEASIBLE': '#F39C12',
            'INFEASIBLE': '#E74C3C',
            'INCONNU': '#3498DB',
            'OPTIMAL (secours)': '#2ECC71'
        }.get(status, '#3498DB')

        if hasattr(self, 'status_badge'):
            self.status_badge.setText(f"● {status}")
            self.status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: #2b2d31;
                    color: {status_color};
                    font-weight: bold;
                    padding: 6px 12px;
                    border-radius: 16px;
                    font-size: 11px;
                    border: 1px solid #444;
                }}
            """)

    def update_metrics(self, data_model, results, total_cost):
        """Mettre à jour les métriques"""
        total_flights = len(data_model.flights)
        assigned_flights = len(self.assignments)
        objective_value = results.get('objective_value', 0)
        solve_time = results.get('solve_time', 0)

        # Mettre à jour les cartes de métriques
        self.metric_vols.update_value(f"{assigned_flights}/{total_flights}")

        # AFFICHER LE COÛT TOTAL CORRECTEMENT
        print(f"DEBUG update_metrics: total_cost = {total_cost}")
        self.metric_cout.update_value(f"€{total_cost:,.0f}")

        if total_flights > 0:
            coverage_rate = (assigned_flights / total_flights) * 100
            self.metric_taux.update_value(f"{coverage_rate:.1f}%")
        else:
            self.metric_taux.update_value("N/A")

        self.metric_temps.update_value(f"{solve_time:.2f}s")

    def update_text_details(self, data_model, results, total_cost):
        """Mettre à jour les détails textuels"""
        status = results.get('status_str', 'INCONNU')
        objective_value = results.get('objective_value', 0)
        solve_time = results.get('solve_time', 0)
        message = results.get('message', '')

        # DEBUG
        print(f"DEBUG update_text_details: total_cost = {total_cost}")

        # Calculer le coût moyen par vol
        if len(self.assignments) > 0:
            avg_cost = total_cost / len(self.assignments)
            cost_text = f"€{avg_cost:,.2f}"
        else:
            avg_cost = 0
            cost_text = "€0.00"

        # Calculer le taux de couverture
        if len(data_model.flights) > 0:
            coverage_rate = (len(self.assignments) / len(data_model.flights)) * 100
            coverage_text = f"{coverage_rate:.1f}%"
        else:
            coverage_text = "0%"

        # Calculer le taux d'utilisation
        total_crew = len(data_model.pilots) + len(data_model.copilots)
        if total_crew > 0:
            utilization_rate = ((len(self.assignments) * 2) / total_crew) * 100
            utilization_text = f"{utilization_rate:.1f}%"
        else:
            utilization_text = "0%"

        # Informations générales
        info_html = f"""
        <div style='font-family: "Segoe UI", Arial, sans-serif;'>
            <h3 style='color:#4F6EF7;'>Résultats de l'Optimisation</h3>

            <div style='margin: 15px 0; padding: 15px; background-color: #35373b; border-radius: 8px;'>
                <table style='width: 100%; border-collapse: collapse;'>
                    <tr>
                        <td style='color: #aaa; padding: 5px;'><b>Statut:</b></td>
                        <td style='color: #2ECC71; padding: 5px;'><b>{status}</b></td>
                    </tr>
                    <tr>
                        <td style='color: #aaa; padding: 5px;'><b>Valeur objectif:</b></td>
                        <td style='color: white; padding: 5px;'>{objective_value:,.2f}</td>
                    </tr>
                    <tr>
                        <td style='color: #aaa; padding: 5px;'><b>Coût total:</b></td>
                        <td style='color: #F39C12; padding: 5px; font-weight: bold;'>€{total_cost:,.2f}</td>
                    </tr>
                    <tr>
                        <td style='color: #aaa; padding: 5px;'><b>Temps de résolution:</b></td>
                        <td style='color: white; padding: 5px;'>{solve_time:.2f} secondes</td>
                    </tr>
                    <tr>
                        <td style='color: #aaa; padding: 5px;'><b>Message:</b></td>
                        <td style='color: white; padding: 5px;'>{message}</td>
                    </tr>
                </table>
            </div>

            <h4 style='color:#F39C12; margin-top: 20px;'>Statistiques</h4>
            <div style='margin: 10px 0; padding: 10px; background-color: #2b2d31; border-radius: 6px;'>
                <p>• Nombre de vols: {len(data_model.flights)}</p>
                <p>• Nombre de pilotes: {len(data_model.pilots)}</p>
                <p>• Nombre de copilotes: {len(data_model.copilots)}</p>
                <p>• Affectations trouvées: {len(self.assignments)}</p>
                <p>• Taux de couverture: {coverage_text}</p>
                <p>• Coût total: <b style='color:#F39C12;'>€{total_cost:,.2f}</b></p>
                <p>• Coût moyen par vol: {cost_text}</p>
            </div>
        </div>
        """

        self.info_text.setHtml(info_html)

        # Dernières affectations pour le dashboard
        if self.assignments:
            recent_html = ""
            for i, assign in enumerate(self.assignments[:5]):
                vol = assign.get('vol', assign.get('flight', f'V{i + 1}'))
                pilote = assign.get('pilote', assign.get('pilot', f'P{i + 1}'))
                copilote = assign.get('copilote', assign.get('copilot', f'C{i + 1}'))
                cout = assign.get('cout', assign.get('cost', 0))

                recent_html += f"""
                <div style='margin: 8px 0; padding: 8px; background-color: #35373b; border-radius: 6px; border-left: 4px solid #4F6EF7;'>
                    <b>✈️ {vol}</b> - 👨‍✈️ {pilote} + 👨‍✈️ {copilote}<br>
                    <span style='color: #888; font-size: 12px;'>Coût: €{cout:,.0f}</span>
                </div>
                """
            self.recent_assignments.setHtml(recent_html)
        else:
            self.recent_assignments.setHtml(
                "<div style='color: #888; font-style: italic; text-align: center; padding: 20px;'>Aucune affectation trouvée</div>")

        # Statistiques pour le dashboard
        stats_text = f"""• Vols assignés: {len(self.assignments)}/{len(data_model.flights)}
    • Coût total: €{total_cost:,.0f}
    • Coût moyen par vol: {cost_text}
    • Taux d'utilisation équipage: {utilization_text}
    • Temps de repos minimum: {data_model.min_rest}h"""

        self.stats_text.setText(stats_text)

    def update_assignments_table(self):
        """Mettre à jour le tableau des affectations avec les bonnes heures"""
        if not hasattr(self, 'assignments_table'):
            return

        self.assignments_table.setRowCount(len(self.assignments))

        for row, assign in enumerate(self.assignments):
            # Récupérer les données correctement
            vol = assign.get('vol', assign.get('flight', f'V{row + 1}'))

            # Heures (avec formatage correct)
            heure_depart = assign.get('heure_depart', assign.get('departure', 8))
            heure_arrivee = assign.get('heure_arrivee', assign.get('arrival', 10))
            duree = assign.get('duree', assign.get('duration', 2))

            # Convertir en float si nécessaire
            if isinstance(heure_depart, str):
                heure_depart = float(heure_depart)
            if isinstance(heure_arrivee, str):
                heure_arrivee = float(heure_arrivee)
            if isinstance(duree, str):
                duree = float(duree)

            # Formater les heures (8.0 -> "08:00")
            def format_hour(hour_float):
                hours = int(hour_float)
                minutes = int((hour_float - hours) * 60)
                return f"{hours:02d}:{minutes:02d}"

            # Créer les items
            items = [
                QTableWidgetItem(vol),
                QTableWidgetItem(format_hour(heure_depart)),
                QTableWidgetItem(format_hour(heure_arrivee)),
                QTableWidgetItem(f"{duree}h"),
                QTableWidgetItem(assign.get('pilote', assign.get('pilot', f'P{row + 1}'))),
                QTableWidgetItem(assign.get('copilote', assign.get('copilot', f'C{row + 1}')))
            ]

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                item.setForeground(QColor('white'))
                self.assignments_table.setItem(row, col, item)

        self.assignments_table.resizeColumnsToContents()

    def update_results_text(self, data_model, results, total_cost):
        """Mettre à jour le texte des résultats avec les bonnes heures"""
        status = results.get('status_str', 'INCONNU')
        objective_value = results.get('objective_value', 0)
        solve_time = results.get('solve_time', 0)
        message = results.get('message', '')

        text = f"<h3 style='color:#4F6EF7;'>📊 RÉSULTATS DE L'OPTIMISATION</h3>"
        text += f"<div style='margin: 15px 0; padding: 15px; background-color: #35373b; border-radius: 8px;'>"
        text += f"<p><b>Statut:</b> <span style='color:#2ECC71;'>{status}</span></p>"
        text += f"<p><b>Message:</b> {message}</p>"
        text += f"<p><b>Valeur objectif:</b> €{objective_value:,.2f}</p>"
        text += f"<p><b>Coût total:</b> <span style='color:#F39C12; font-weight:bold;'>€{total_cost:,.2f}</span></p>"
        text += f"<p><b>Temps de résolution:</b> {solve_time:.2f}s</p>"
        text += f"<p><b>Paramètre λ:</b> {data_model.lambda_weight:.2f}</p>"
        text += f"</div>"

        if self.assignments:
            text += f"<h4 style='color:#F39C12;'>✈️ AFFECTATIONS DÉTAILLÉES</h4>"
            text += f"<div style='margin: 10px 0;'>"

            # Trier par heure de départ
            sorted_assignments = sorted(self.assignments,
                                        key=lambda x: x.get('heure_depart', x.get('departure', 0)))

            for i, assign in enumerate(sorted_assignments, 1):
                vol = assign.get('vol', assign.get('flight', f'V{i}'))
                pilote = assign.get('pilote', assign.get('pilot', f'P{i}'))
                copilote = assign.get('copilote', assign.get('copilot', f'C{i}'))

                # Récupérer les heures correctement
                heure_depart = assign.get('heure_depart', assign.get('departure', 8))
                heure_arrivee = assign.get('heure_arrivee', assign.get('arrival', 10))
                duree = assign.get('duree', assign.get('duration', 2))
                cout = assign.get('cout', assign.get('cost', 0))
                aircraft = assign.get('aircraft', 'A320')

                # Convertir en float si nécessaire
                if isinstance(heure_depart, str):
                    heure_depart = float(heure_depart)
                if isinstance(heure_arrivee, str):
                    heure_arrivee = float(heure_arrivee)

                # Formater les heures
                def format_hour_decimal(hour):
                    hours = int(hour)
                    minutes = int((hour - hours) * 60)
                    return f"{hours:02d}h{minutes:02d}"

                text += f"""
                <div style='margin: 15px 0; padding: 15px; background-color: #2b2d31; border-radius: 8px; border-left: 4px solid #4F6EF7;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <b style='font-size: 16px;'>✈️ {vol} ({aircraft})</b>
                        <span style='color:#F39C12; font-weight:bold;'>€{cout:,.0f}</span>
                    </div>

                    <div style='margin-top: 10px;'>
                        <div><b>Équipage:</b> 👨‍✈️ {pilote} + 👨‍✈️ {copilote}</div>
                        <div><b>Horaires:</b> 🕐 {format_hour_decimal(heure_depart)} → {format_hour_decimal(heure_arrivee)} (Durée: {duree}h)</div>
                    </div>
                </div>
                """

            text += f"</div>"
        else:
            text += f"<div style='margin: 20px 0; padding: 20px; background-color: #2b2d31; border-radius: 8px; text-align:center;'>"
            text += f"<span style='font-size:24px;'>⚠️</span><br>"
            text += f"<b style='color:#E74C3C;'>Aucune affectation trouvée</b>"
            text += f"</div>"

        self.results_text.setHtml(text)
    def update_graph(self):
        """Mettre à jour le graphique avec les horaires réels"""
        self.ax.clear()

        if not self.assignments:
            # Graphique vide
            self.ax.text(0.5, 0.5, "📊\nAucune donnée",
                         ha='center', va='center', fontsize=14, color='white')
            self.ax.set_facecolor('#2b2d31')
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        else:
            # Trier les vols par heure de départ
            sorted_assignments = sorted(self.assignments,
                                        key=lambda x: x.get('heure_depart', x.get('departure', 0)))

            # Données pour le graphique
            vols = []
            departures = []
            arrivals = []
            durations = []

            for assign in sorted_assignments:
                vols.append(assign.get('vol', assign.get('flight', 'V?')))

                # Récupérer les heures correctement
                heure_depart = assign.get('heure_depart', assign.get('departure', 8))
                heure_arrivee = assign.get('heure_arrivee', assign.get('arrival', 10))
                duree = assign.get('duree', assign.get('duration', 2))

                departures.append(float(heure_depart))
                arrivals.append(float(heure_arrivee))
                durations.append(float(duree))

            # Créer un graphique de Gantt
            y_pos = range(len(vols))
            bar_height = 0.6

            # Barres pour les vols (du départ à l'arrivée)
            bars = self.ax.barh(y_pos, durations, left=departures,
                                height=bar_height, color='#4F6EF7', edgecolor='white', alpha=0.8)

            # Configuration
            self.ax.set_facecolor('#2b2d31')
            self.figure.patch.set_facecolor('#2b2d31')
            self.ax.tick_params(colors='white')

            # Axe Y
            self.ax.set_yticks(y_pos)
            self.ax.set_yticklabels(vols, color='white', fontweight='bold')
            self.ax.set_ylim(-0.5, len(vols) - 0.5)

            # Axe X (heures)
            self.ax.set_xlabel('Heure de la journée', color='white', fontweight='bold')

            # Limites de l'axe X (de 0h à 24h ou selon les vols)
            min_hour = min(departures) - 1
            max_hour = max(arrivals) + 1
            self.ax.set_xlim(max(0, min_hour), min(24, max_hour))

            # Grille horaire
            self.ax.set_xticks(range(0, 25, 2))
            self.ax.set_xticklabels([f'{h:02d}h' for h in range(0, 25, 2)], color='white')
            self.ax.grid(True, axis='x', alpha=0.2, color='white', linestyle='--')

            # Titre
            self.ax.set_title(f'Horaires des Vols Assignés ({len(vols)} vols)',
                              color='white', fontweight='bold', pad=20)

            # Ajouter les heures sur les barres
            for i, (dep, arr, dur, vol) in enumerate(zip(departures, arrivals, durations, vols)):
                # Heure de départ
                self.ax.text(dep + dur / 2, i, f'{dep:05.2f}h-{arr:05.2f}h',
                             ha='center', va='center', color='white', fontsize=9, fontweight='bold')

                # Durée
                self.ax.text(dep + dur / 2, i - 0.25, f'Durée: {dur}h',
                             ha='center', va='center', color='#aaa', fontsize=8)

            # Légende
            self.ax.plot([], [], color='#4F6EF7', linewidth=10, label='Vol')
            self.ax.legend(facecolor='#2b2d31', edgecolor='white',
                           labelcolor='white', loc='upper right')

        self.figure.tight_layout()
        self.canvas.draw()

    def update_empty_plot(self):
        """Afficher un graphique vide"""
        self.ax.clear()

        self.ax.set_facecolor('#2b2d31')

        # Message central
        self.ax.text(0.5, 0.5, "📊\nEn attente de données",
                     ha='center', va='center', fontsize=16, color='white',
                     fontweight='bold', transform=self.ax.transAxes)

        # Sous-titre
        self.ax.text(0.5, 0.4, "Lancez une optimisation pour voir les résultats",
                     ha='center', va='center', fontsize=12, color='#aaa',
                     fontstyle='italic', transform=self.ax.transAxes)

        # Désactiver les axes
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        # Bordures subtiles
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#444')
            spine.set_linewidth(1)

        self.canvas.draw()