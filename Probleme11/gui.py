# gui.py
from typing import List, Dict, Tuple
from PySide6 import QtWidgets

from solver import BinPackingSolverThread

# Types de plateformes (capacités poids + volume)
PLATFORM_TYPES = {
    "Petite plateforme":   {"weight_cap": 1000.0, "volume_cap": 10.0},
    "Plateforme moyenne":  {"weight_cap": 2000.0, "volume_cap": 20.0},
    "Grande plateforme":   {"weight_cap": 3000.0, "volume_cap": 30.0},
}

# Coût par voyage selon la plateforme
PLATFORM_COST = {
    "Petite plateforme": 50,   # TND
    "Plateforme moyenne": 80,
    "Grande plateforme": 120,
}


class BinPackingWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Optimisation des voyages - Chargement d'équipements sur plateformes (Gurobi)")
        self.resize(1100, 700)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(main_layout)

        self.last_materials: List[Dict] = []
        self.solver_thread = None

        # ---------- Paramètres généraux ----------
        top_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(top_layout)

        top_layout.addWidget(QtWidgets.QLabel("Nombre de matériaux :"))
        self.spin_nb_materials = QtWidgets.QSpinBox()
        self.spin_nb_materials.setMinimum(1)
        self.spin_nb_materials.setMaximum(50)
        self.spin_nb_materials.setValue(9)  # affiche 9 par défaut
        top_layout.addWidget(self.spin_nb_materials)

        top_layout.addWidget(QtWidgets.QLabel("Type de plateforme :"))
        self.combo_platform = QtWidgets.QComboBox()
        self.combo_platform.addItems(list(PLATFORM_TYPES.keys()))
        top_layout.addWidget(self.combo_platform)

        top_layout.addStretch()

        # ---------- Capacités ----------
        cap_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(cap_layout)

        cap_layout.addWidget(QtWidgets.QLabel("Capacité poids / voyage (kg) :"))
        self.spin_weight_cap = QtWidgets.QDoubleSpinBox()
        self.spin_weight_cap.setDecimals(2)
        self.spin_weight_cap.setMinimum(0.01)
        self.spin_weight_cap.setMaximum(1e9)
        cap_layout.addWidget(self.spin_weight_cap)

        cap_layout.addWidget(QtWidgets.QLabel("Capacité volume / voyage (m³) :"))
        self.spin_volume_cap = QtWidgets.QDoubleSpinBox()
        self.spin_volume_cap.setDecimals(2)
        self.spin_volume_cap.setMinimum(0.01)
        self.spin_volume_cap.setMaximum(1e9)
        cap_layout.addWidget(self.spin_volume_cap)

        self.btn_resize = QtWidgets.QPushButton("Mettre à jour la table")
        cap_layout.addWidget(self.btn_resize)

        cap_layout.addStretch()

        self._update_capacities_from_platform()

        # ---------- Table des matériaux ----------
        self.table_materials = QtWidgets.QTableWidget()
        self.table_materials.setColumnCount(4)
        self.table_materials.setHorizontalHeaderLabels(
            ["Matériau", "Poids/unité (kg)", "Volume/unité (m³)", "Quantité"]
        )
        main_layout.addWidget(self.table_materials)

        self._resize_table(self.spin_nb_materials.value())
        self.table_materials.horizontalHeader().setStretchLastSection(True)
        self.table_materials.resizeColumnsToContents()

        # ---------- Incompatibilités ----------
        inc_group = QtWidgets.QGroupBox("Contraintes d'incompatibilité (optionnel)")
        inc_layout = QtWidgets.QVBoxLayout()
        inc_group.setLayout(inc_layout)

        inc_layout.addWidget(QtWidgets.QLabel(
            "Paires incompatibles (une par ligne) au format :\n"
            "MatériauA, MatériauB\n\n"
            "Exemple:\n"
            "Fenêtres, Poutres"
        ))

        self.text_incompat = QtWidgets.QPlainTextEdit()
        inc_layout.addWidget(self.text_incompat)
        main_layout.addWidget(inc_group)

        # ---------- Boutons ----------
        btn_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(btn_layout)

        self.btn_solve = QtWidgets.QPushButton("Optimiser les voyages (Gurobi)")
        btn_layout.addWidget(self.btn_solve)

        self.btn_clear = QtWidgets.QPushButton("Effacer les résultats")
        btn_layout.addWidget(self.btn_clear)

        btn_layout.addStretch()

        # ---------- Résultats ----------
        self.text_result = QtWidgets.QTextEdit()
        self.text_result.setReadOnly(True)
        main_layout.addWidget(self.text_result)

        # Connexions
        self.btn_resize.clicked.connect(self.on_resize_clicked)
        self.spin_nb_materials.valueChanged.connect(self.on_nb_materials_changed)
        self.btn_solve.clicked.connect(self.on_solve_clicked)
        self.btn_clear.clicked.connect(self.on_clear_clicked)
        self.combo_platform.currentTextChanged.connect(self.on_platform_type_changed)

    # ==============================
    # Capacités plateforme
    # ==============================
    def _update_capacities_from_platform(self):
        platform_name = self.combo_platform.currentText()
        caps = PLATFORM_TYPES.get(platform_name)
        if caps:
            self.spin_weight_cap.setValue(caps["weight_cap"])
            self.spin_volume_cap.setValue(caps["volume_cap"])

    def on_platform_type_changed(self, _text):
        self._update_capacities_from_platform()

    # ==============================
    # Table matériaux
    # ==============================
    def _resize_table(self, n_rows: int):
        default_names = [
            "Poutres",
            "Briques",
            "Sacs de ciment",
            "Fer à béton",
            "Bois",
            "Tuiles",
            "Carreaux",
            "Fenêtres",
            "Portes",
        ]

        defaults = {
            0: ("30", "15", "0"),   # Poutres
            1: ("3",  "2",  "0"),   # Briques
            2: ("5",  "10", "0"),   # Sacs de ciment
            3: ("7",  "3",  "0"),   # Fer à béton
            4: ("20", "12", "0"),   # Bois
            5: ("4",  "6",  "0"),   # Tuiles
            6: ("2",  "1",  "0"),   # Carreaux
            7: ("50", "8",  "0"),   # Fenêtres
            8: ("80", "15", "0"),   # Portes
        }

        current_rows = self.table_materials.rowCount()

        if n_rows > current_rows:
            for _ in range(n_rows - current_rows):
                row = self.table_materials.rowCount()
                self.table_materials.insertRow(row)

                name = default_names[row] if row < len(default_names) else f"Matériau {row + 1}"
                self.table_materials.setItem(row, 0, QtWidgets.QTableWidgetItem(name))

                w, v, q = defaults.get(row, ("1", "1", "0"))
                self.table_materials.setItem(row, 1, QtWidgets.QTableWidgetItem(w))
                self.table_materials.setItem(row, 2, QtWidgets.QTableWidgetItem(v))
                self.table_materials.setItem(row, 3, QtWidgets.QTableWidgetItem(q))

        elif n_rows < current_rows:
            for _ in range(current_rows - n_rows):
                self.table_materials.removeRow(self.table_materials.rowCount() - 1)

        self.table_materials.resizeColumnsToContents()

    def on_resize_clicked(self):
        self._resize_table(self.spin_nb_materials.value())

    def on_nb_materials_changed(self, value):
        self._resize_table(value)

    def on_clear_clicked(self):
        self.text_result.clear()

    # ==============================
    # Collecte matériaux
    # ==============================
    def _collect_materials(self) -> List[Dict]:
        materials = []
        rows = self.table_materials.rowCount()

        for row in range(rows):
            name_item = self.table_materials.item(row, 0)
            name = name_item.text().strip() if name_item else f"Matériau {row + 1}"
            if not name:
                name = f"Matériau {row + 1}"

            w_item = self.table_materials.item(row, 1)
            v_item = self.table_materials.item(row, 2)
            q_item = self.table_materials.item(row, 3)

            if not (w_item and v_item and q_item):
                continue

            try:
                weight = float(w_item.text())
                volume = float(v_item.text())
                quantity = int(q_item.text())
            except ValueError:
                continue

            if weight <= 0 or volume <= 0 or quantity <= 0:
                continue

            materials.append({
                "name": name,
                "weight": weight,
                "volume": volume,
                "quantity": quantity
            })

        return materials

    def _collect_incompatibilities(self) -> List[Tuple[str, str]]:
        text = self.text_incompat.toPlainText()
        pairs: List[Tuple[str, str]] = []

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) != 2:
                continue
            a, b = parts
            if a and b and a != b:
                pairs.append((a, b))

        return pairs

    # ==============================
    # Résolution
    # ==============================
    def on_solve_clicked(self):
        weight_cap = float(self.spin_weight_cap.value())
        volume_cap = float(self.spin_volume_cap.value())
        materials = self._collect_materials()
        incompat_pairs = self._collect_incompatibilities()

        if weight_cap <= 0 or volume_cap <= 0:
            QtWidgets.QMessageBox.warning(
                self, "Erreur", "Les capacités doivent être strictement positives."
            )
            return

        if not materials:
            QtWidgets.QMessageBox.warning(
                self, "Erreur",
                "Aucun matériau valide (poids>0, volume>0, quantité>0)."
            )
            return

        self.last_materials = materials

        self.text_result.append("=== Lancement de l'optimisation des voyages (Méthode exacte – Gurobi) ===")
        self.btn_solve.setEnabled(False)

        self.solver_thread = BinPackingSolverThread(
            materials,
            weight_cap,
            volume_cap,
            incompat_pairs=incompat_pairs
        )
        self.solver_thread.result_ready.connect(self.on_solver_finished)
        self.solver_thread.start()

    def on_solver_finished(self, status_message: str, voyages: List[Dict]):
        self.btn_solve.setEnabled(True)

        self.text_result.append(status_message)
        self.text_result.append("")

        if not voyages:
            self.text_result.append("=== Fin de la résolution ===\n")
            return

        materials = self.last_materials or []
        total_units = sum(m["quantity"] for m in materials)
        nb_voyages = len(voyages)

        weight_cap = float(self.spin_weight_cap.value())
        volume_cap = float(self.spin_volume_cap.value())

        total_weight_used = sum(v["total_weight"] for v in voyages)
        total_volume_used = sum(v["total_volume"] for v in voyages)

        avg_weight = (total_weight_used / (nb_voyages * weight_cap)) if weight_cap > 0 else 0.0
        avg_volume = (total_volume_used / (nb_voyages * volume_cap)) if volume_cap > 0 else 0.0

        platform_name = self.combo_platform.currentText()
        cost_per_trip = PLATFORM_COST.get(platform_name, 0)
        total_cost = nb_voyages * cost_per_trip

        self.text_result.append("📌 Résumé global :")
        self.text_result.append(f"• Total unités transportées : {total_units}")
        self.text_result.append(f"• Nombre de voyages : {nb_voyages}")
        self.text_result.append(f"• Remplissage moyen : {avg_weight*100:.1f}% (poids), {avg_volume*100:.1f}% (volume)")
        self.text_result.append(f"• Coût par voyage : {cost_per_trip} TND")
        self.text_result.append(f"💰 Coût total : {total_cost} TND")
        self.text_result.append("")

        voyages_sorted = sorted(voyages, key=lambda v: v["trip_index"])

        for k, v in enumerate(voyages_sorted, start=1):
            self.text_result.append(
                f"Voyage {k} (Poids = {v['total_weight']:.2f} / {weight_cap:.2f} kg, "
                f"Volume = {v['total_volume']:.2f} / {volume_cap:.2f} m³) :"
            )

            mats_list = v.get("materials", [])
            if not mats_list:
                self.text_result.append("   (aucun matériau)")
            else:
                for mat in mats_list:
                    self.text_result.append(
                        f"   - {mat['quantity']} x {mat['name']} "
                        f"(Poids total = {mat['weight']:.2f} kg, Volume total = {mat['volume']:.2f} m³)"
                    )
            self.text_result.append("")

        self.text_result.append("=== Fin de la résolution ===\n")
