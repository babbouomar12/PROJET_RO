"""
Module de l'interface graphique pour l'optimisation de capacité réseau
Contient tous les composants UI : NodeItem, LinkItem, TopologyScene, MainWindow
"""

import sys
import math
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsSimpleTextItem,
    QDockWidget, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QDoubleSpinBox, QPushButton, QLabel, QMessageBox,
    QTableWidget, QTableWidgetItem, QFileDialog, QComboBox, QSpinBox,
    QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, QPointF, QThread, Signal
from PySide6.QtGui import QPen, QBrush, QColor

# Importer les fonctions de résolution
from .optimization_solver import solve_capacity_pl, solve_capacity_plne


# ============================================================================
# COMPOSANTS GRAPHIQUES
# ============================================================================

class NodeItem(QGraphicsEllipseItem):
    """Représente un nœud graphique dans la scène"""
    RADIUS = 25  # Rayon des cercles de nœud (augmenté pour meilleure visibilité)

    def __init__(self, name, pos):
        # Initialise le cercle du nœud
        super().__init__(-self.RADIUS, -self.RADIUS, 2 * self.RADIUS, 2 * self.RADIUS)
        # Style visuel moderne avec dégradé
        from PySide6.QtGui import QRadialGradient
        gradient = QRadialGradient(0, 0, self.RADIUS)
        gradient.setColorAt(0, QColor("#5DADE2"))
        gradient.setColorAt(1, QColor("#2E86C1"))
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(QColor("#1B4F72"), 2.5))
        # Comportement du nœud
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        # Propriétés du nœud
        self.name = name
        self.links = []
        # Étiquette du nœud avec police améliorée
        from PySide6.QtGui import QFont
        self.text_item = QGraphicsSimpleTextItem(name, self)
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        self.text_item.setFont(font)
        self.text_item.setBrush(QBrush(Qt.GlobalColor.white))
        self.text_item.setPos(-self.text_item.boundingRect().width() / 2, 
                              -self.text_item.boundingRect().height() / 2)
        self.setPos(pos)
        self.setToolTip(f"Nœud {name}")

    def itemChange(self, change, value):
        """Met à jour les liens lorsque le nœud est déplacé et gère la sélection"""
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            for link in self.links:
                link.update_geometry()
        elif change == QGraphicsEllipseItem.GraphicsItemChange.ItemSelectedHasChanged:
            from PySide6.QtGui import QRadialGradient
            if value:  # Sélectionné
                gradient = QRadialGradient(0, 0, self.RADIUS)
                gradient.setColorAt(0, QColor("#F39C12"))
                gradient.setColorAt(1, QColor("#D68910"))
                self.setBrush(QBrush(gradient))
                self.setPen(QPen(QColor("#9C640C"), 3))
            else:  # Non sélectionné
                gradient = QRadialGradient(0, 0, self.RADIUS)
                gradient.setColorAt(0, QColor("#5DADE2"))
                gradient.setColorAt(1, QColor("#2E86C1"))
                self.setBrush(QBrush(gradient))
                self.setPen(QPen(QColor("#1B4F72"), 2.5))
        return super().itemChange(change, value)


class LinkItem(QGraphicsLineItem):
    """Représente un lien graphique entre deux nœuds"""
    
    def __init__(self, source, dest):
        super().__init__()
        self.source = source
        self.dest = dest
        self.source.links.append(self)
        self.dest.links.append(self)
        # Propriétés pour le problème d'optimisation
        self.capacity = 0.0
        self.cost = 0.0
        self.added_capacity = 0.0
        # Style visuel moderne du lien
        pen = QPen(QColor("#34495E"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.setPen(pen)
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable, True)
        # Étiquette du lien
        from PySide6.QtGui import QFont
        self.label = QGraphicsSimpleTextItem(self)
        font = QFont("Consolas", 9)
        self.label.setFont(font)
        self.label.setBrush(QBrush(QColor("#2C3E50")))
        self.setToolTip("Lien - Cliquez pour modifier les propriétés")
        self.update_geometry()

    def update_geometry(self):
        """Met à jour la géométrie et l'étiquette du lien"""
        line = self.dest.pos() - self.source.pos()
        length = math.hypot(line.x(), line.y())
        if length == 0: return
        offset = NodeItem.RADIUS + 6.0
        p1 = self.source.pos() + line / length * offset
        p2 = self.dest.pos() - line / length * offset
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        mid_point = (p1 + p2) / 2
        self.label.setPos(mid_point)
        self.label.setText(f"C0={self.capacity:.1f}, x={self.added_capacity:.1f}, c={self.cost:.1f}")

    def set_capacity(self, cap):
        """Met à jour la capacité et l'affichage"""
        self.capacity = cap
        self.update_geometry()

    def set_cost(self, cost):
        """Met à jour le coût et l'affichage"""
        self.cost = cost
        self.update_geometry()

    def set_added_capacity(self, x):
        """Met à jour la capacité ajoutée et l'affichage"""
        self.added_capacity = x
        self.update_geometry()

    def itemChange(self, change, value):
        """Change la couleur du lien lorsqu'il est sélectionné"""
        if change == QGraphicsLineItem.GraphicsItemChange.ItemSelectedHasChanged:
            pen = self.pen()
            if value:
                pen.setColor(QColor("#E74C3C"))
                pen.setWidth(4)
                self.label.setBrush(QBrush(QColor("#C0392B")))
            else:
                pen.setColor(QColor("#34495E"))
                pen.setWidth(3)
                self.label.setBrush(QBrush(QColor("#2C3E50")))
            self.setPen(pen)
        return super().itemChange(change, value)


class TopologyScene(QGraphicsScene):
    """Scène graphique personnalisée pour gérer les clics"""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        # Fond moderne avec dégradé subtil
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, 600)
        gradient.setColorAt(0, QColor("#ECF0F1"))
        gradient.setColorAt(1, QColor("#D5DBDB"))
        self.setBackgroundBrush(QBrush(gradient))

    def mousePressEvent(self, event):
        self.main_window.handle_scene_click(event)
        super().mousePressEvent(event)


# ============================================================================
# THREAD DE RÉSOLUTION
# ============================================================================

class SolverThread(QThread):
    """Thread pour exécuter la résolution en arrière-plan (non-bloquant)"""
    
    # Signaux pour communiquer avec l'interface
    solution_ready = Signal(object, object, object, str, object)
    error_occurred = Signal(str)
    progress_update = Signal(str)
    
    def __init__(self, nodes, links, demands, solver_type="PL", modules=None):
        super().__init__()
        self.nodes = nodes
        self.links = links
        self.demands = demands
        self.solver_type = solver_type
        self.modules = modules
    
    def run(self):
        """Exécute la résolution dans le thread"""
        try:
            self.progress_update.emit("Initialisation du modèle Gurobi...")
            
            if self.solver_type == "PL":
                self.progress_update.emit("Résolution PL en cours...")
                obj, x, f, status = solve_capacity_pl(self.nodes, self.links, self.demands)
                y = None
            else:  # PLNE
                self.progress_update.emit("Résolution PLNE en cours...")
                obj, x, f, status, y = solve_capacity_plne(self.nodes, self.links, self.demands, self.modules)
            
            if status == "Optimal":
                self.progress_update.emit("Solution optimale trouvée!")
                self.solution_ready.emit(obj, x, f, status, y)
            else:
                self.error_occurred.emit(f"Statut: {status}")
        except Exception as e:
            self.error_occurred.emit(f"Erreur: {str(e)}")


# ============================================================================
# FENÊTRE PRINCIPALE
# ============================================================================

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Optimisation de Capacité Réseau - Dimensionnement Énergétique")
        self.resize(1500, 850)
        
        # Style professionnel corporate sobre
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAFAFA;
            }
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: 1px solid #546E7A;
                padding: 8px 16px;
                font-size: 9pt;
                font-weight: normal;
                min-height: 26px;
            }
            QPushButton:hover {
                background-color: #546E7A;
                border: 1px solid #455A64;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #9E9E9E;
            }
            QLabel {
                color: #424242;
                font-size: 9pt;
            }
            QDockWidget {
                background-color: #F5F5F5;
                border: 1px solid #DADADA;
            }
            QDockWidget::title {
                background-color: #E0E0E0;
                color: #424242;
                padding: 8px;
                font-weight: normal;
                font-size: 9pt;
                border-bottom: 1px solid #BDBDBD;
            }
            QTableWidget {
                gridline-color: #E0E0E0;
                background-color: white;
                border: 1px solid #DADADA;
                selection-background-color: #607D8B;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 5px 8px;
                color: #212121;
            }
            QTableWidget::item:selected {
                background-color: #607D8B;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #EEEEEE;
                color: #212121;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                padding: 6px 8px;
                border: none;
                border-right: 1px solid #BDBDBD;
                border-bottom: 1px solid #BDBDBD;
                font-weight: normal;
                color: #424242;
                font-size: 9pt;
            }
            QDoubleSpinBox, QComboBox {
                padding: 5px 8px;
                border: 1px solid #BDBDBD;
                background-color: white;
                min-height: 22px;
                font-size: 9pt;
                color: #212121;
            }
            QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #607D8B;
            }
            QDoubleSpinBox:hover, QComboBox:hover {
                border: 1px solid #757575;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #212121;
                selection-background-color: #607D8B;
                selection-color: white;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #BDBDBD;
                padding: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 9pt;
                color: #212121;
            }
            QProgressBar {
                border: 1px solid #BDBDBD;
                text-align: center;
                background-color: #E0E0E0;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #607D8B;
            }
            QScrollBar:vertical {
                border: none;
                background: #F5F5F5;
                width: 14px;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #9E9E9E;
            }
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #212121;
                background-color: white;
            }
            QMessageBox QPushButton {
                background-color: #607D8B;
                color: white;
                min-width: 80px;
            }
        """)
        
        # État de l'application
        self.mode = "select"
        self.node_counter = 0
        self.pending_link_start = None
        self.solver_thread = None
        
        # Modules de capacité pour PLNE
        self.modules = {
            "10G": {"capacity": 10, "cost_factor": 1.0},
            "40G": {"capacity": 40, "cost_factor": 0.9},
            "100G": {"capacity": 100, "cost_factor": 0.8}
        }
        
        # Scène et vue graphique
        self.scene = TopologyScene(self)
        self.scene.setSceneRect(-500, -350, 1000, 700)
        self.view = QGraphicsView(self.scene)
        from PySide6.QtGui import QPainter
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setCentralWidget(self.view)
        
        # Panneau latéral
        self.create_side_panel()
        
        # Barre de statut
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #263238;
                color: #ECEFF1;
                font-weight: 500;
                padding: 6px 12px;
                font-size: 9.5pt;
            }
        """)
        self.status_bar.showMessage("Prêt", 0)
        
        # Connecter le signal de sélection
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def create_side_panel(self):
        """Crée le panneau latéral avec les outils et les propriétés"""
        dock = QDockWidget("Panneau de Contrôle", self)
        dock.setMinimumWidth(340)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Fonction pour créer les séparateurs de section
        def create_section_label(text):
            label = QLabel(text)
            label.setStyleSheet("""
                font-size: 8.5pt;
                font-weight: bold;
                color: #424242;
                background-color: #E0E0E0;
                padding: 4px 6px;
                border-bottom: 1px solid #BDBDBD;
            """)
            return label
        
        # Section: Outils
        layout.addWidget(create_section_label("Outils"))
        
        tools_layout = QHBoxLayout()
        btn_add_node = QPushButton("+ Nœud")
        btn_add_node.setToolTip("Ajouter un nœud")
        btn_add_node.clicked.connect(lambda: self.set_mode("add_node"))
        btn_add_link = QPushButton("+ Lien")
        btn_add_link.setToolTip("Ajouter un lien")
        btn_add_link.clicked.connect(lambda: self.set_mode("add_link"))
        tools_layout.addWidget(btn_add_node)
        tools_layout.addWidget(btn_add_link)
        layout.addLayout(tools_layout)
        
        # Fichiers
        files_layout = QHBoxLayout()
        btn_save = QPushButton("Enregistrer")
        btn_save.clicked.connect(self.save_topology)
        btn_load = QPushButton("Charger")
        btn_load.clicked.connect(self.load_topology)
        btn_reset = QPushButton("Réinitialiser")
        btn_reset.clicked.connect(self.reset_all)
        files_layout.addWidget(btn_save)
        files_layout.addWidget(btn_load)
        files_layout.addWidget(btn_reset)
        layout.addLayout(files_layout)
        
        examples_layout = QHBoxLayout()
        btn_example = QPushButton("Exemple")
        btn_example.clicked.connect(self.load_example)
        btn_fail_example = QPushButton("Infais.")
        btn_fail_example.clicked.connect(self.load_infeasible_example)
        examples_layout.addWidget(btn_example)
        examples_layout.addWidget(btn_fail_example)
        layout.addLayout(examples_layout)
        
        # Section: Propriétés du lien
        layout.addWidget(create_section_label("Propriétés du Lien"))
        
        self.link_properties = QWidget()
        link_form = QFormLayout(self.link_properties)
        link_form.setSpacing(4)
        link_form.setContentsMargins(0, 0, 0, 0)
        link_form.setVerticalSpacing(4)
        
        self.capacity_input = QDoubleSpinBox()
        self.capacity_input.setRange(0, 10000)
        self.capacity_input.setSuffix(" Gbit/s")
        self.capacity_input.setToolTip("Capacité actuelle de la liaison")
        self.capacity_input.valueChanged.connect(self.update_link_capacity)
        link_form.addRow("Capacité initiale C₀:", self.capacity_input)
        
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setRange(0, 10000)
        self.cost_input.setSuffix(" k€/Gbit/s")
        self.cost_input.setToolTip("Coût pour ajouter 1 Gbit/s")
        self.cost_input.valueChanged.connect(self.update_link_cost)
        link_form.addRow("Coût unitaire c:", self.cost_input)
        
        self.link_properties.setVisible(True)
        layout.addWidget(self.link_properties)
        
        # Section: Demandes de trafic
        layout.addWidget(create_section_label("Demandes de Trafic"))
        
        # Tableau pour les demandes de trafic
        self.demands_table = QTableWidget(0, 3)
        self.demands_table.setHorizontalHeaderLabels(["Source", "Dest.", "Débit"])
        self.demands_table.setAlternatingRowColors(True)
        self.demands_table.horizontalHeader().setStretchLastSection(True)
        self.demands_table.setMaximumHeight(120)
        layout.addWidget(self.demands_table)
        
        btn_add_demand = QPushButton("Ajouter Demande")
        btn_add_demand.clicked.connect(self.add_demand_row)
        layout.addWidget(btn_add_demand)
        
        # Section: Optimisation
        layout.addWidget(create_section_label("Optimisation"))
        
        layout.addWidget(QLabel("Type de modèle:"))
        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["PL (Continu)", "PLNE (Modules discrets)"])
        layout.addWidget(self.solver_combo)
        
        self.btn_solve = QPushButton("RÉSOUDRE")
        self.btn_solve.setStyleSheet("""
            QPushButton {
                background-color: #546E7A;
                font-weight: bold;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        self.btn_solve.clicked.connect(self.solve)
        layout.addWidget(self.btn_solve)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setMaximumHeight(18)
        layout.addWidget(self.progress_bar)
        
        # Label de statut
        self.status_label = QLabel("")
        self.status_label.setMaximumHeight(16)
        layout.addWidget(self.status_label)
        
        # Section: Résultats
        layout.addWidget(create_section_label("Résultats"))
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(120)
        layout.addWidget(self.results_text)
        
        dock.setWidget(container)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def set_mode(self, mode):
        """Change le mode de l'application"""
        self.mode = mode
        if self.pending_link_start:
            self.pending_link_start.setBrush(QBrush(Qt.GlobalColor.white))
            self.pending_link_start = None

    def handle_scene_click(self, event):
        """Gère les clics sur la scène"""
        pos = event.scenePos()
        if self.mode == "add_node":
            self.node_counter += 1
            node = NodeItem(f"N{self.node_counter}", pos)
            self.scene.addItem(node)
            self.set_mode("select")
        elif self.mode == "add_link":
            item = self.scene.itemAt(pos, self.view.transform())
            if isinstance(item, NodeItem):
                if not self.pending_link_start:
                    self.pending_link_start = item
                    item.setBrush(QBrush(Qt.GlobalColor.yellow))
                else:
                    if item != self.pending_link_start:
                        self.scene.addItem(LinkItem(self.pending_link_start, item))
                    self.set_mode("select")

    def add_demand_row(self):
        """Ajoute une ligne au tableau des demandes"""
        row_count = self.demands_table.rowCount()
        self.demands_table.insertRow(row_count)
    
    def reset_all(self):
        """Réinitialise complètement la topologie et la matrice de trafic"""
        reply = QMessageBox.question(
            self, 
            "Confirmation", 
            "Voulez-vous vraiment tout réinitialiser?\nToutes les données seront perdues.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Effacer la scène
            self.scene.clear()
            # Effacer le tableau des demandes
            self.demands_table.setRowCount(0)
            # Réinitialiser le compteur de nœuds
            self.node_counter = 0
            # Effacer les résultats
            self.results_text.clear()
            self.status_label.setText("")
            # Remettre le mode sélection
            self.set_mode("select")
            QMessageBox.information(self, "Réinitialisation", "Topologie et matrice de trafic réinitialisées.")

    def on_selection_changed(self):
        """Gère la sélection d'éléments dans la scène"""
        try:
            selected_items = self.scene.selectedItems()
            if len(selected_items) == 1 and isinstance(selected_items[0], LinkItem):
                link = selected_items[0]
                self.capacity_input.blockSignals(True)
                self.cost_input.blockSignals(True)
                self.capacity_input.setValue(link.capacity)
                self.cost_input.setValue(link.cost)
                self.capacity_input.blockSignals(False)
                self.cost_input.blockSignals(False)
            else:
                self.capacity_input.blockSignals(True)
                self.cost_input.blockSignals(True)
                self.capacity_input.setValue(0)
                self.cost_input.setValue(0)
                self.capacity_input.blockSignals(False)
                self.cost_input.blockSignals(False)
        except RuntimeError:
            pass

    def update_link_capacity(self):
        """Met à jour la capacité du lien sélectionné"""
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 1 and isinstance(selected_items[0], LinkItem):
            selected_items[0].set_capacity(self.capacity_input.value())

    def update_link_cost(self):
        """Met à jour le coût du lien sélectionné"""
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 1 and isinstance(selected_items[0], LinkItem):
            selected_items[0].set_cost(self.cost_input.value())

    def solve(self):
        """Lance la résolution du problème"""
        if self.solver_thread and self.solver_thread.isRunning():
            QMessageBox.warning(self, "Calcul en cours", "Veuillez attendre la fin de la résolution actuelle.")
            return
        
        # Récupère les données de la scène
        nodes = [item.name for item in self.scene.items() if isinstance(item, NodeItem)]
        links_data = {}
        for item in self.scene.items():
            if isinstance(item, LinkItem):
                src, dst = item.source.name, item.dest.name
                links_data[f"{src}->{dst}"] = {"src": src, "dst": dst, "C0": item.capacity, "cost": item.cost}
                links_data[f"{dst}->{src}"] = {"src": dst, "dst": src, "C0": item.capacity, "cost": item.cost}
        
        demands_data = []
        for row in range(self.demands_table.rowCount()):
            try:
                src_item = self.demands_table.item(row, 0)
                dst_item = self.demands_table.item(row, 1)
                demand_item = self.demands_table.item(row, 2)
                if src_item and dst_item and demand_item:
                    demands_data.append({
                        "src": src_item.text(),
                        "dst": dst_item.text(),
                        "d": float(demand_item.text())
                    })
            except (ValueError, AttributeError):
                pass

        # Validation
        if not nodes:
            QMessageBox.warning(self, "Erreur", "Aucun nœud dans le réseau.")
            return
        if not links_data:
            QMessageBox.warning(self, "Erreur", "Aucun lien dans le réseau.")
            return
        if not demands_data:
            QMessageBox.warning(self, "Erreur", "Aucune demande de trafic définie.")
            return
        
        # Déterminer le type de solveur
        solver_type = "PL" if self.solver_combo.currentIndex() == 0 else "PLNE"
        
        # Créer et démarrer le thread
        self.solver_thread = SolverThread(nodes, links_data, demands_data, solver_type, self.modules)
        self.solver_thread.solution_ready.connect(self.handle_solution)
        self.solver_thread.error_occurred.connect(self.handle_error)
        self.solver_thread.progress_update.connect(self.update_progress)
        self.solver_thread.finished.connect(self.solver_finished)
        
        self.btn_solve.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.results_text.clear()
        self.status_label.setText("Résolution en cours...")
        
        self.solver_thread.start()
    
    def update_progress(self, message):
        """Met à jour le statut de progression"""
        self.status_label.setText(message)
    
    def handle_solution(self, obj, x, f, status, y):
        """Gère une solution réussie"""
        total_capacity_added = sum(x.values())
        
        result_text = f"=== SOLUTION OPTIMALE ===\n\n"
        result_text += f"Coût Total: {obj:.2f} k€\n"
        result_text += f"Capacité totale ajoutée: {total_capacity_added:.2f} Gbit/s\n\n"
        
        result_text += "--- Capacités ajoutées par lien ---\n"
        for link_id, cap in sorted(x.items()):
            if cap > 0.01:
                result_text += f"{link_id}: +{cap:.2f} Gbit/s\n"
        
        if y:
            result_text += "\n--- Modules installés (PLNE) ---\n"
            for link_id in sorted(x.keys()):
                modules_installed = []
                for mod_type in self.modules.keys():
                    count = int(y.get((link_id, mod_type), 0))
                    if count > 0:
                        modules_installed.append(f"{count}x{mod_type}")
                if modules_installed:
                    result_text += f"{link_id}: {', '.join(modules_installed)}\n"
        
        self.results_text.setText(result_text)
        self.status_label.setText("✓ Solution optimale trouvée!")
        
        # Mettre à jour la visualisation
        for item in self.scene.items():
            if isinstance(item, LinkItem):
                src, dst = item.source.name, item.dest.name
                added_cap = x.get(f"{src}->{dst}", 0) + x.get(f"{dst}->{src}", 0)
                item.set_added_capacity(added_cap)
    
    def handle_error(self, error_msg):
        """Gère une erreur"""
        QMessageBox.critical(self, "Erreur de Résolution", f"Impossible de résoudre le problème:\n{error_msg}")
        self.results_text.setText(f"ERREUR: {error_msg}")
        self.status_label.setText("✗ Erreur de résolution")
    
    def solver_finished(self):
        """Appelé quand le thread se termine"""
        self.btn_solve.setEnabled(True)
        self.progress_bar.setVisible(False)
    
    def save_topology(self):
        """Sauvegarde la topologie dans un fichier JSON"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder la topologie", "", "JSON Files (*.json)")
        if not file_path:
            return
        
        nodes_data = [{"name": item.name, "pos": [item.pos().x(), item.pos().y()]}
                      for item in self.scene.items() if isinstance(item, NodeItem)]
        
        links_data = [{"src": link.source.name, "dst": link.dest.name,
                       "capacity": link.capacity, "cost": link.cost}
                      for link in self.scene.items() if isinstance(link, LinkItem)]
        
        demands_data = []
        for r in range(self.demands_table.rowCount()):
            try:
                src_item = self.demands_table.item(r, 0)
                dst_item = self.demands_table.item(r, 1)
                demand_item = self.demands_table.item(r, 2)
                if src_item and dst_item and demand_item:
                    demands_data.append({
                        "src": src_item.text(),
                        "dst": dst_item.text(),
                        "d": float(demand_item.text())
                    })
            except (ValueError, AttributeError):
                pass
        
        topology = {"nodes": nodes_data, "links": links_data, "demands": demands_data}
        
        try:
            with open(file_path, 'w') as f:
                json.dump(topology, f, indent=4)
            QMessageBox.information(self, "Succès", "Topologie sauvegardée avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder: {e}")
    
    def load_example(self):
        """Charge l'exemple de base A-B-C-D avec les paramètres spécifiés"""
        # Effacer la scène actuelle
        self.scene.clear()
        self.demands_table.setRowCount(0)
        self.node_counter = 0
        
        # Créer les nœuds A, B, C, D en ligne
        nodes = {}
        node_names = ['A', 'B', 'C', 'D']
        for i, name in enumerate(node_names):
            pos = QPointF(-150 + i * 100, 0)
            node = NodeItem(name, pos)
            self.scene.addItem(node)
            nodes[name] = node
        
        # Créer les liens avec les capacités et coûts spécifiés
        # Lien A-B: C0=10 Gbit/s, c=5 €/Gbit/s
        link_ab = LinkItem(nodes['A'], nodes['B'])
        link_ab.set_capacity(10.0)
        link_ab.set_cost(5.0)
        self.scene.addItem(link_ab)
        
        # Lien B-C: C0=8 Gbit/s, c=8 €/Gbit/s
        link_bc = LinkItem(nodes['B'], nodes['C'])
        link_bc.set_capacity(8.0)
        link_bc.set_cost(8.0)
        self.scene.addItem(link_bc)
        
        # Lien C-D: C0=12 Gbit/s, c=4 €/Gbit/s
        link_cd = LinkItem(nodes['C'], nodes['D'])
        link_cd.set_capacity(12.0)
        link_cd.set_cost(4.0)
        self.scene.addItem(link_cd)
        
        # Ajouter une demande exemple: A -> D avec 15 Gbit/s
        self.add_demand_row()
        item_a = QTableWidgetItem('A')
        item_a.setForeground(QBrush(QColor("#212121")))
        item_d = QTableWidgetItem('D')
        item_d.setForeground(QBrush(QColor("#212121")))
        item_15 = QTableWidgetItem('15')
        item_15.setForeground(QBrush(QColor("#212121")))
        self.demands_table.setItem(0, 0, item_a)
        self.demands_table.setItem(0, 1, item_d)
        self.demands_table.setItem(0, 2, item_15)
        
        QMessageBox.information(self, "Exemple chargé", 
            "Exemple A-B-C-D chargé avec succès!\n\n"
            "Liens:\n"
            "• A-B: C₀=10 Gbit/s, c=5 €/Gbit/s\n"
            "• B-C: C₀=8 Gbit/s, c=8 €/Gbit/s\n"
            "• C-D: C₀=12 Gbit/s, c=4 €/Gbit/s\n\n"
            "Demande: A → D : 15 Gbit/s")
    
    def load_infeasible_example(self):
        """Charge un exemple qui échouera (topologie déconnectée)"""
        # Effacer la scène actuelle
        self.scene.clear()
        self.demands_table.setRowCount(0)
        self.node_counter = 0
        
        # Créer deux groupes de nœuds DÉCONNECTÉS
        nodes = {}
        
        # Groupe 1: A et B (en haut à gauche)
        nodes['A'] = NodeItem('A', QPointF(-150, -50))
        nodes['B'] = NodeItem('B', QPointF(-50, -50))
        self.scene.addItem(nodes['A'])
        self.scene.addItem(nodes['B'])
        
        # Groupe 2: C et D (en bas à droite, SÉPARÉS)
        nodes['C'] = NodeItem('C', QPointF(50, 50))
        nodes['D'] = NodeItem('D', QPointF(150, 50))
        self.scene.addItem(nodes['C'])
        self.scene.addItem(nodes['D'])
        
        # Créer seulement des liens INTERNES aux groupes
        # Lien A-B (groupe 1)
        link_ab = LinkItem(nodes['A'], nodes['B'])
        link_ab.set_capacity(100.0)
        link_ab.set_cost(1.0)
        self.scene.addItem(link_ab)
        
        # Lien C-D (groupe 2)
        link_cd = LinkItem(nodes['C'], nodes['D'])
        link_cd.set_capacity(100.0)
        link_cd.set_cost(1.0)
        self.scene.addItem(link_cd)
        
        # PAS DE LIEN entre les groupes !
        
        # Ajouter une demande IMPOSSIBLE: A -> D (pas de chemin!)
        self.add_demand_row()
        item_a = QTableWidgetItem('A')
        item_a.setForeground(QBrush(QColor("#212121")))
        item_d = QTableWidgetItem('D')
        item_d.setForeground(QBrush(QColor("#212121")))
        item_50 = QTableWidgetItem('50')
        item_50.setForeground(QBrush(QColor("#212121")))
        self.demands_table.setItem(0, 0, item_a)
        self.demands_table.setItem(0, 1, item_d)
        self.demands_table.setItem(0, 2, item_50)
        
        QMessageBox.warning(self, "Exemple Infaisable", 
            "⚠️ Exemple de topologie DÉCONNECTÉE !\n\n"
            "Groupes séparés:\n"
            "• Groupe 1: A ←→ B\n"
            "• Groupe 2: C ←→ D\n\n"
            "❌ Demande impossible: A → D (50 Gbit/s)\n\n"
            "Il n'existe AUCUN chemin entre A et D.\n"
            "Le solveur retournera 'INFEASIBLE'.")
    
    def load_topology(self):
        """Charge une topologie depuis un fichier JSON"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Charger une topologie", "", "JSON Files (*.json)")
        if not file_path:
            return
        
        try:
            with open(file_path, 'r') as f:
                topology = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger: {e}")
            return
        
        self.scene.clear()
        self.demands_table.setRowCount(0)
        self.node_counter = 0
        
        node_items = {}
        max_node_num = 0
        for node_data in topology.get("nodes", []):
            name = node_data["name"]
            pos = QPointF(*node_data["pos"])
            node = NodeItem(name, pos)
            self.scene.addItem(node)
            node_items[name] = node
            
            if name.startswith("N") and name[1:].isdigit():
                num = int(name[1:])
                if num > max_node_num:
                    max_node_num = num
        self.node_counter = max_node_num
        
        for link_data in topology.get("links", []):
            src_node = node_items.get(link_data["src"])
            dst_node = node_items.get(link_data["dst"])
            if src_node and dst_node:
                link = LinkItem(src_node, dst_node)
                link.set_capacity(link_data.get("capacity", 0.0))
                link.set_cost(link_data.get("cost", 0.0))
                self.scene.addItem(link)
        
        for demand_data in topology.get("demands", []):
            self.add_demand_row()
            row = self.demands_table.rowCount() - 1
            item_src = QTableWidgetItem(demand_data["src"])
            item_src.setForeground(QBrush(QColor("#212121")))
            item_dst = QTableWidgetItem(demand_data["dst"])
            item_dst.setForeground(QBrush(QColor("#212121")))
            item_d = QTableWidgetItem(str(demand_data["d"]))
            item_d.setForeground(QBrush(QColor("#212121")))
            self.demands_table.setItem(row, 0, item_src)
            self.demands_table.setItem(row, 1, item_dst)
            self.demands_table.setItem(row, 2, item_d)
