import sys
from typing import Dict, Tuple

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QSpinBox, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView, QStyleFactory, QSplitter, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QAbstractAnimation
from PySide6.QtGui import QPalette, QColor, QFont, QIcon
from PySide6.QtWidgets import QStyle


import gurobipy as gp
from gurobipy import GRB

# Matplotlib pour le diagramme de Gantt (timeline)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


# ---------- Résolution du Job Shop (PLNE) ----------

def solve_jobshop(
    nb_jobs: int,
    nb_ops: int,
    nb_machines: int,
    machines: Dict[Tuple[int, int], int],
    durations: Dict[Tuple[int, int], float]
):

    m = gp.Model("JobShop_Eoliennes")

    operations = list(durations.keys())
    H = sum(durations.values())  # horizon max

    # Variables S_{j,o} (temps de début)
    S = {
        (j, o): m.addVar(lb=0.0, name=f"S_{j}_{o}")
        for (j, o) in operations
    }

    # Makespan
    Cmax = m.addVar(lb=0.0, name="Cmax")

    # Variables binaires pour l'ordre sur une même machine
    X = {}
    for i in range(len(operations)):
        for k in range(i + 1, len(operations)):
            (j1, o1) = operations[i]
            (j2, o2) = operations[k]
            if machines[(j1, o1)] == machines[(j2, o2)]:
                X[(j1, o1, j2, o2)] = m.addVar(
                    vtype=GRB.BINARY,
                    name=f"x_{j1}_{o1}_{j2}_{o2}"
                )

    m.update()

    # 1) Précédence : ordre des tests sur chaque éolienne
    for j in range(nb_jobs):
        for o in range(nb_ops - 1):
            m.addConstr(
                S[(j, o + 1)] >= S[(j, o)] + durations[(j, o)],
                name=f"prec_{j}_{o}"
            )

    # 2) Non-chevauchement sur une même machine
    for (j1, o1, j2, o2), x_var in X.items():
        # (j1,o1) avant (j2,o2)
        m.addConstr(
            S[(j1, o1)] + durations[(j1, o1)]
            <= S[(j2, o2)] + H * (1 - x_var),
            name=f"mach1_{j1}_{o1}_{j2}_{o2}"
        )
        # (j2,o2) avant (j1,o1)
        m.addConstr(
            S[(j2, o2)] + durations[(j2, o2)]
            <= S[(j1, o1)] + H * x_var,
            name=f"mach2_{j1}_{o1}_{j2}_{o2}"
        )

    # 3) Définition de Cmax = max des fins
    for j in range(nb_jobs):
        last_op = nb_ops - 1
        m.addConstr(
            Cmax >= S[(j, last_op)] + durations[(j, last_op)],
            name=f"cmax_{j}"
        )

    # Objectif
    m.setObjective(Cmax, GRB.MINIMIZE)
    m.setParam("OutputFlag", 0)

    m.optimize()

    if m.status != GRB.OPTIMAL:
        raise RuntimeError(f"Solution non optimale, status = {m.status}")

    cmax_val = Cmax.X
    schedule = {(j, o): S[(j, o)].X for (j, o) in operations}
    return cmax_val, schedule


# ---------- Canvas Matplotlib pour la timeline ----------

class GanttCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

        # Couleurs dark pour la figure
        fig.patch.set_facecolor("#151515")
        self.ax.set_facecolor("#151515")

    def plot_schedule(
        self,
        nb_machines: int,
        machines: Dict[Tuple[int, int], int],
        durations: Dict[Tuple[int, int], float],
        schedule: Dict[Tuple[int, int], float]
    ):
        """
        Trace un diagramme de Gantt :
        - Axe X = temps
        - Axe Y = machines
        - Chaque barre = un test d'une éolienne sur une machine
        """
        self.ax.clear()
        self.ax.set_facecolor("#151515")

        # Couleurs sobres pour les barres
        bar_colors = ["#4ECCA3", "#3E9EFF", "#FFB347", "#FF6F61", "#BD93F9"]

        for idx, ((j, o), start) in enumerate(schedule.items()):
            m_id = machines[(j, o)]      # machine utilisée
            dur = durations[(j, o)]      # durée
            y = m_id                     # position verticale = machine

            color = bar_colors[idx % len(bar_colors)]

            # Barre horizontale (timeline)
            self.ax.barh(
                y=y,
                width=dur,
                left=start,
                height=0.7,
                color=color,
                edgecolor="#111111"
            )

            # Label sur la barre : E{éolienne}-T{test}
            label = f"E{j+1}-T{o+1}"
            self.ax.text(
                start + dur / 2,
                y,
                label,
                ha="center",
                va="center",
                fontsize=8,
                color="#FFFFFF"
            )

        self.ax.set_xlabel("Temps", color="#DDDDDD")
        self.ax.set_ylabel("Machines", color="#DDDDDD")
        self.ax.set_yticks(range(1, nb_machines + 1))
        self.ax.set_yticklabels([f"M{m}" for m in range(1, nb_machines + 1)], color="#DDDDDD")

        # Couleurs des ticks
        self.ax.tick_params(axis="x", colors="#BBBBBB")
        self.ax.tick_params(axis="y", colors="#BBBBBB")

        # Grille subtile
        self.ax.grid(
            True,
            axis="x",
            linestyle="--",
            linewidth=0.5,
            color="#333333",
            alpha=0.7
        )

        # Spines
        for spine in self.ax.spines.values():
            spine.set_color("#555555")

        self.figure.tight_layout()
        self.draw()

class NeonButton(QPushButton):
    """Bouton avec effet néon + animation hover."""

    def __init__(self, text="", accent_color="#5C8CFF", parent=None):
        super().__init__(text, parent)

        self.accent_color = QColor(accent_color)

        # Effet d'ombre portée pour le glow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(8)
        self.shadow.setColor(self.accent_color)
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        # Animation du blur -> glow plus fort au survol
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
        self.anim.setDuration(200)
        self.anim.setStartValue(8)
        self.anim.setEndValue(24)

    def enterEvent(self, event):
        self.anim.setDirection(QAbstractAnimation.Forward)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.setDirection(QAbstractAnimation.Backward)
        self.anim.start()
        super().leaveEvent(event)





class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ordonnancement des tests sur les éoliennes - Job Shop (PLNE)")
        self.resize(1300, 750)

        self._setup_app_style()

        self.machines_data: Dict[Tuple[int, int], int] = {}
        self.durations_data: Dict[Tuple[int, int], float] = {}

        # ---------- Widgets de paramètres ----------
        self.spin_jobs = QSpinBox()
        self.spin_jobs.setRange(1, 50)
        self.spin_jobs.setValue(3)
        self.spin_jobs.setFixedWidth(90)
        self.spin_jobs.setToolTip("Nombre d'éoliennes (jobs) à planifier.")

        self.spin_ops = QSpinBox()
        self.spin_ops.setRange(1, 20)
        self.spin_ops.setValue(3)
        self.spin_ops.setFixedWidth(90)
        self.spin_ops.setToolTip("Nombre de tests (opérations) par éolienne.")

        self.spin_machines = QSpinBox()
        self.spin_machines.setRange(1, 20)
        self.spin_machines.setValue(3)
        self.spin_machines.setFixedWidth(90)
        self.spin_machines.setToolTip("Nombre de machines disponibles pour les tests.")

        # ---------- Boutons néon + icônes ----------
        self.btn_generate = NeonButton("  Générer les tableaux", accent_color="#4ECCA3")
        self.btn_generate.setObjectName("secondaryButton")
        self.btn_generate.setToolTip("Créer / réinitialiser les tableaux de machines et de durées.")
        self.btn_generate.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))

        self.btn_solve = NeonButton("  Résoudre avec Gurobi", accent_color="#FFB347")
        self.btn_solve.setObjectName("primaryButton")
        self.btn_solve.setToolTip("Lancer la résolution du Job Shop avec Gurobi.")
        self.btn_solve.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

        # ---------- Tables ----------
        self.table_machines = QTableWidget()
        self.table_durations = QTableWidget()

        self.table_results = QTableWidget()
        self.table_results.setColumnCount(5)
        self.table_results.setHorizontalHeaderLabels(
            ["Éolienne (j)", "Test (o)", "Machine", "Début S_{j,o}", "Durée p_{j,o}"]
        )
        self.table_results.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_results.setAlternatingRowColors(True)

        # ---------- Label Cmax ----------
        self.label_obj = QLabel("Cmax (makespan global) : -")
        self.label_obj.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_obj.setObjectName("cmaxLabel")

        # ---------- Timeline ----------
        self.gantt_canvas = GanttCanvas()

        # ---------- Construction de l'UI ----------
        self._build_ui()

        # ---------- Connexions ----------
        self.btn_generate.clicked.connect(self.generate_tables)
        self.btn_solve.clicked.connect(self.launch_solver)

        self.generate_tables()


    def _setup_app_style(self):
        QApplication.setStyle(QStyleFactory.create("Fusion"))

        palette = QPalette()

        bg_window = QColor(10, 12, 20)
        bg_base = QColor(18, 20, 30, 220)      # semi-transparent = effet verre
        bg_alt = QColor(24, 26, 38, 230)
        text_color = QColor(235, 235, 245)
        disabled_text = QColor(120, 120, 135)
        highlight = QColor(92, 140, 255)

        palette.setColor(QPalette.Window, bg_window)
        palette.setColor(QPalette.WindowText, text_color)
        palette.setColor(QPalette.Base, bg_base)
        palette.setColor(QPalette.AlternateBase, bg_alt)
        palette.setColor(QPalette.ToolTipBase, bg_base)
        palette.setColor(QPalette.ToolTipText, text_color)
        palette.setColor(QPalette.Text, text_color)
        palette.setColor(QPalette.PlaceholderText, disabled_text)
        palette.setColor(QPalette.Button, QColor(32, 34, 48, 230))
        palette.setColor(QPalette.ButtonText, text_color)
        palette.setColor(QPalette.Highlight, highlight)
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        QApplication.setPalette(palette)

        font = QFont("Segoe UI", 9)
        QApplication.setFont(font)

        # --- Stylesheet : glassmorphism / néon ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #050713,
                    stop:0.5 #070A18,
                    stop:1 #050713
                );
            }

            QLabel {
                font-size: 12px;
                color: #E5E7F5;
            }

            QLabel#sectionCaption {
                font-size: 11px;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: #8D93B8;
            }

            QLabel#cmaxLabel {
                font-size: 15px;
                font-weight: 700;
                color: #FFFFFF;
            }

            QGroupBox {
                font-weight: 600;
                font-size: 12px;
                border: 1px solid rgba(255,255,255,0.05);
                border-radius: 18px;
                margin-top: 16px;
                background: rgba(18, 21, 32, 0.72);
                /* faux effet verre */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 3px 10px;
                background-color: transparent;
                color: #F5F7FF;
            }

            QFrame#cardFrame {
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.04);
                background-color: rgba(18, 20, 30, 0.78);
            }

            QPushButton {
                border-radius: 999px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: 600;
                color: #F5F5FF;
            }

            QPushButton#primaryButton {
                border: 1px solid rgba(255, 179, 71, 0.9);
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFB347,
                    stop:1 #FF7B54
                );
            }
            QPushButton#primaryButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #FFC262,
                    stop:1 #FF8B62
                );
            }

            QPushButton#secondaryButton {
                border: 1px solid rgba(78, 204, 163, 0.8);
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #263644,
                    stop:1 #1F2833
                );
                color: #E8FFF7;
            }
            QPushButton#secondaryButton:hover {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2E4354,
                    stop:1 #232E3B
                );
            }

            QPushButton:disabled {
                background-color: #3A3F55;
                border-color: #3A3F55;
                color: #888EA8;
            }

            QSpinBox {
                padding: 4px 8px;
                background-color: rgba(15, 17, 26, 0.9);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 10px;
                color: #F0F0F5;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: transparent;
                border: none;
                width: 16px;
            }

            QHeaderView::section {
                background-color: rgba(39, 43, 63, 0.9);
                padding: 6px 8px;
                border: 0px;
                border-right: 1px solid rgba(255,255,255,0.04);
                font-weight: 600;
                font-size: 11px;
                color: #E5E5EA;
            }

            QTableWidget {
                gridline-color: rgba(255,255,255,0.06);
                selection-background-color: rgba(92, 140, 255, 0.9);
                selection-color: white;
                alternate-background-color: rgba(18, 22, 35, 0.9);
                background-color: transparent;
                color: #F0F0F5;
            }

            QTableWidget QTableCornerButton::section {
                background-color: rgba(39, 43, 63, 0.9);
                border: 0px;
            }

            QScrollBar:vertical, QScrollBar:horizontal {
                background: rgba(10, 12, 20, 0.7);
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: rgba(76, 82, 112, 0.9);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: rgba(110, 118, 155, 0.95);
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                background: none;
                border: none;
                width: 0px;
                height: 0px;
            }

            QSplitter::handle {
                background-color: rgba(32, 35, 52, 0.8);
            }
            QSplitter::handle:hover {
                background-color: rgba(45, 49, 72, 0.9);
            }
        """)


    def _build_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)
        main_widget.setLayout(main_layout)

        # ---------- Bandeau supérieur : paramètres + actions ----------
        params_group = QGroupBox("Paramètres du problème")
        params_group_layout = QHBoxLayout()
        params_group_layout.setContentsMargins(14, 10, 14, 10)
        params_group_layout.setSpacing(20)
        params_group.setLayout(params_group_layout)

        # Bloc paramètres (éoliennes, opérations, machines)
        params_block = QWidget()
        params_block_layout = QGridLayout()
        params_block_layout.setContentsMargins(0, 0, 0, 0)
        params_block_layout.setHorizontalSpacing(18)
        params_block_layout.setVerticalSpacing(4)
        params_block.setLayout(params_block_layout)

        label_jobs = QLabel("Nombre d'éoliennes")
        label_ops = QLabel("Tests par éolienne")
        label_machs = QLabel("Nombre de machines")

        params_block_layout.addWidget(label_jobs, 0, 0)
        params_block_layout.addWidget(self.spin_jobs, 1, 0)
        params_block_layout.addWidget(label_ops, 0, 1)
        params_block_layout.addWidget(self.spin_ops, 1, 1)
        params_block_layout.addWidget(label_machs, 0, 2)
        params_block_layout.addWidget(self.spin_machines, 1, 2)

        params_group_layout.addWidget(params_block, stretch=3)

        # Bloc boutons (génération / résolution)
        btn_block = QWidget()
        btn_block_layout = QHBoxLayout()
        btn_block_layout.setContentsMargins(0, 0, 0, 0)
        btn_block_layout.setSpacing(10)
        btn_block.setLayout(btn_block_layout)

        btn_block_layout.addStretch()
        btn_block_layout.addWidget(self.btn_generate)
        btn_block_layout.addWidget(self.btn_solve)

        params_group_layout.addWidget(btn_block, stretch=2)

        main_layout.addWidget(params_group)

        # ---------- Splitter principal : saisie (milieu) / résultats (bas) ----------
        main_splitter = QSplitter(Qt.Vertical)
        main_splitter.setChildrenCollapsible(False)

        # ----- Groupe saisie -----
        inputs_group = QGroupBox("Saisie des données")
        inputs_layout = QHBoxLayout()
        inputs_layout.setContentsMargins(10, 8, 10, 10)
        inputs_layout.setSpacing(12)
        inputs_group.setLayout(inputs_layout)

        self._style_table(self.table_machines)
        self._style_table(self.table_durations)

        inputs_layout.addWidget(
            self._wrap_with_label("Machines m_{j,o}", self.table_machines),
            stretch=1
        )
        inputs_layout.addWidget(
            self._wrap_with_label("Durées p_{j,o}", self.table_durations),
            stretch=1
        )

        # ----- Groupe résultats + timeline -----
        results_group = QGroupBox("Résultats et timeline")
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(10, 8, 10, 10)
        results_layout.setSpacing(8)
        results_group.setLayout(results_layout)

        # Bandeau Cmax
        results_header = QWidget()
        results_header_layout = QHBoxLayout()
        results_header_layout.setContentsMargins(0, 0, 0, 2)
        results_header_layout.setSpacing(10)
        results_header.setLayout(results_header_layout)

        cmax_caption = QLabel("Analyse de l'ordonnancement")
        cmax_caption.setObjectName("sectionCaption")

        results_header_layout.addWidget(cmax_caption)
        results_header_layout.addStretch()
        results_header_layout.addWidget(self.label_obj)

        results_layout.addWidget(results_header)

        # Splitter horizontal pour tableau détaillé et Gantt
        results_splitter = QSplitter(Qt.Horizontal)
        results_splitter.setChildrenCollapsible(False)

        self._style_table(self.table_results)

        detailed_frame = self._wrap_with_label("Solution détaillée", self.table_results)
        gantt_frame = self._wrap_with_label("Diagramme de Gantt (temps / machines)", self.gantt_canvas)

        results_splitter.addWidget(detailed_frame)
        results_splitter.addWidget(gantt_frame)

        results_splitter.setStretchFactor(0, 3)
        results_splitter.setStretchFactor(1, 4)

        results_layout.addWidget(results_splitter)

        # Ajouter groupes au splitter principal
        main_splitter.addWidget(inputs_group)
        main_splitter.addWidget(results_group)

        main_splitter.setStretchFactor(0, 3)  # saisie
        main_splitter.setStretchFactor(1, 4)  # résultats

        main_layout.addWidget(main_splitter, stretch=1)

    def _style_table(self, table: QTableWidget):
        table.setAlternatingRowColors(True)
        table.setShowGrid(True)
        table.verticalHeader().setDefaultSectionSize(26)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setWordWrap(False)
        table.horizontalHeader().setHighlightSections(False)
        table.verticalHeader().setVisible(True)

    def _wrap_with_label(self, text, widget):
        container = QFrame()
        container.setObjectName("cardFrame")
        v = QVBoxLayout()
        v.setContentsMargins(10, 8, 10, 10)
        v.setSpacing(6)
        label = QLabel(text)
        label.setStyleSheet("font-weight: 600; color: #F0F0F5; font-size: 12px;")
        v.addWidget(label)
        v.addWidget(widget)
        container.setLayout(v)
        return container

    # ---------- Génération des tableaux ----------

    def generate_tables(self):
        nb_jobs = self.spin_jobs.value()
        nb_ops = self.spin_ops.value()
        nb_machines = self.spin_machines.value()

        # Machines
        self.table_machines.setRowCount(nb_jobs)
        self.table_machines.setColumnCount(nb_ops)
        self.table_machines.setHorizontalHeaderLabels(
            [f"Test {o+1}" for o in range(nb_ops)]
        )
        self.table_machines.setVerticalHeaderLabels(
            [f"Éolienne {j+1}" for j in range(nb_jobs)]
        )

        for j in range(nb_jobs):
            for o in range(nb_ops):
                item = QTableWidgetItem()
                default_machine = (o % nb_machines) + 1
                item.setText(str(default_machine))
                item.setTextAlignment(Qt.AlignCenter)
                self.table_machines.setItem(j, o, item)

        self.table_machines.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_machines.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Durées
        self.table_durations.setRowCount(nb_jobs)
        self.table_durations.setColumnCount(nb_ops)
        self.table_durations.setHorizontalHeaderLabels(
            [f"Test {o+1}" for o in range(nb_ops)]
        )
        self.table_durations.setVerticalHeaderLabels(
            [f"Éolienne {j+1}" for j in range(nb_jobs)]
        )

        for j in range(nb_jobs):
            for o in range(nb_ops):
                item = QTableWidgetItem()
                item.setText("1.0")
                item.setTextAlignment(Qt.AlignCenter)
                self.table_durations.setItem(j, o, item)

        self.table_durations.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_durations.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    # ---------- Résolution ----------

    def launch_solver(self):
        nb_jobs = self.spin_jobs.value()
        nb_ops = self.spin_ops.value()
        nb_machines = self.spin_machines.value()

        machines = {}
        durations = {}

        try:
            for j in range(nb_jobs):
                for o in range(nb_ops):
                    item_m = self.table_machines.item(j, o)
                    item_p = self.table_durations.item(j, o)

                    if item_m is None or item_m.text().strip() == "":
                        raise ValueError(f"Machine manquante pour (éolienne {j+1}, test {o+1})")
                    if item_p is None or item_p.text().strip() == "":
                        raise ValueError(f"Durée manquante pour (éolienne {j+1}, test {o+1})")

                    m_val = int(item_m.text())
                    p_val = float(item_p.text())

                    if not (1 <= m_val <= nb_machines):
                        raise ValueError(
                            f"Machine {m_val} invalide pour (éolienne {j+1}, test {o+1}) "
                            f"(doit être entre 1 et {nb_machines})."
                        )
                    if p_val <= 0:
                        raise ValueError(
                            f"Durée {p_val} invalide pour (éolienne {j+1}, test {o+1}) "
                            "(doit être > 0)."
                        )

                    machines[(j, o)] = m_val
                    durations[(j, o)] = p_val

        except ValueError as e:
            QMessageBox.warning(self, "Erreur de saisie", str(e))
            return

        self.machines_data = machines
        self.durations_data = durations

        try:
            cmax, schedule = solve_jobshop(nb_jobs, nb_ops, nb_machines, machines, durations)
        except Exception as e:
            QMessageBox.critical(self, "Erreur de résolution", str(e))
            return

        # Cmax
        self.label_obj.setText(f"Cmax (makespan global) : {cmax:.2f}")

        # Tableau des résultats
        self.table_results.setRowCount(len(schedule))
        for row, ((j, o), start) in enumerate(sorted(schedule.items())):
            m_id = self.machines_data[(j, o)]
            dur = self.durations_data[(j, o)]
            self.table_results.setItem(row, 0, QTableWidgetItem(str(j + 1)))
            self.table_results.setItem(row, 1, QTableWidgetItem(str(o + 1)))
            self.table_results.setItem(row, 2, QTableWidgetItem(str(m_id)))
            self.table_results.setItem(row, 3, QTableWidgetItem(f"{start:.2f}"))
            self.table_results.setItem(row, 4, QTableWidgetItem(f"{dur:.2f}"))

        # Timeline (diagramme de Gantt)
        self.gantt_canvas.plot_schedule(nb_machines, self.machines_data, self.durations_data, schedule)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
