# solver.py
from typing import List, Dict, Tuple, Optional
from PySide6 import QtCore
import math

try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    gp = None
    GRB = None

Voyage = Dict  # pour lisibilité


def solve_bin_packing_trips_exact(
    materials: List[Dict],
    weight_cap: float,
    volume_cap: float,
    incompat_pairs: Optional[List[Tuple[str, str]]] = None,
) -> Tuple[str, List[Voyage]]:
    """
    Bin Packing 2D (poids + volume) - Modèle exact PLNE (Gurobi).
    - x[m,j] : quantité (entier)
    - y[j]   : voyage utilisé (binaire)
    - z[m,j] : présence matériau m dans voyage j (binaire) pour incompatibilités
    """

    if gp is None:
        return (
            "Erreur: gurobipy n'est pas installé. Installe-le avec 'pip install gurobipy'.",
            []
        )

    mats = [m for m in materials if int(m.get("quantity", 0)) > 0]
    if not mats:
        return ("Aucune unité de matériau à charger.", [])

    names = [m["name"] for m in mats]
    weights = [float(m["weight"]) for m in mats]
    volumes = [float(m["volume"]) for m in mats]
    quantities = [int(m["quantity"]) for m in mats]

    M = len(mats)
    total_units = sum(quantities)

    total_weight = sum(w * q for w, q in zip(weights, quantities))
    total_volume = sum(v * q for v, q in zip(volumes, quantities))

    lb_weight = total_weight / weight_cap if weight_cap > 0 else 0
    lb_volume = total_volume / volume_cap if volume_cap > 0 else 0
    _lb_trips = max(1, math.ceil(max(lb_weight, lb_volume)))

    # borne supérieure : au pire 1 unité par voyage
    num_trips = total_units

    # Incompatibilités -> indices
    inc_idx_pairs: List[Tuple[int, int]] = []
    if incompat_pairs:
        name_to_idx = {n: i for i, n in enumerate(names)}
        for a, b in incompat_pairs:
            if a in name_to_idx and b in name_to_idx and a != b:
                i = name_to_idx[a]
                j = name_to_idx[b]
                if i != j:
                    inc_idx_pairs.append((i, j))

    # Protection licence/temps : limiter la taille du modèle
    # variables ~ M*num_trips + num_trips (+ M*num_trips si incompat)
    est_vars = (M * num_trips + num_trips) + (M * num_trips if inc_idx_pairs else 0)
    if est_vars > 5000:
        return (
            "Instance trop grande pour le modèle exact (limite variables). "
            "Réduis les quantités (ex: regrouper unités) ou diminue la borne J.",
            []
        )

    model = gp.Model("bin_packing_trips_2d_exact")
    model.Params.OutputFlag = 0

    materials_idx = range(M)
    trips_idx = range(num_trips)

    # Variables
    x = model.addVars(M, num_trips, vtype=GRB.INTEGER, name="x")  # quantités
    y = model.addVars(num_trips, vtype=GRB.BINARY, name="y")      # voyage utilisé

    # Demandes
    for m in materials_idx:
        model.addConstr(
            gp.quicksum(x[m, j] for j in trips_idx) == quantities[m],
            name=f"demand_{m}"
        )

    # Capacités poids + volume
    for j in trips_idx:
        model.addConstr(
            gp.quicksum(weights[m] * x[m, j] for m in materials_idx) <= weight_cap * y[j],
            name=f"cap_weight_{j}"
        )
        model.addConstr(
            gp.quicksum(volumes[m] * x[m, j] for m in materials_idx) <= volume_cap * y[j],
            name=f"cap_volume_{j}"
        )

    # Incompatibilités (optionnel)
    if inc_idx_pairs:
        z = model.addVars(M, num_trips, vtype=GRB.BINARY, name="z")

        for m in materials_idx:
            max_q = quantities[m]
            for j in trips_idx:
                model.addConstr(x[m, j] <= max_q * z[m, j], name=f"link_{m}_{j}")

        for (a, b) in inc_idx_pairs:
            for j in trips_idx:
                model.addConstr(z[a, j] + z[b, j] <= 1, name=f"inc_{a}_{b}_{j}")

    # Objectif : minimiser le nombre de voyages
    model.setObjective(gp.quicksum(y[j] for j in trips_idx), GRB.MINIMIZE)

    try:
        model.optimize()
    except gp.GurobiError as e:
        return (f"Erreur Gurobi: {str(e)}", [])

    if model.Status != GRB.OPTIMAL:
        return (f"Pas de solution optimale (statut={model.Status}).", [])

    # Construire la liste des voyages utilisés
    voyages: List[Voyage] = []
    for j in trips_idx:
        if y[j].X <= 0.5:
            continue

        total_w = 0.0
        total_v = 0.0
        mats_list = []

        for m in materials_idx:
            qty = int(round(x[m, j].X))
            if qty <= 0:
                continue

            w_tot = qty * weights[m]
            v_tot = qty * volumes[m]
            total_w += w_tot
            total_v += v_tot

            mats_list.append({
                "name": names[m],
                "quantity": qty,
                "weight": w_tot,
                "volume": v_tot
            })

        voyages.append({
            "trip_index": j,
            "total_weight": total_w,
            "total_volume": total_v,
            "materials": mats_list
        })

    msg = f"Solution optimale trouvée. Nombre minimal de voyages: {len(voyages)}"
    return msg, voyages


class BinPackingSolverThread(QtCore.QThread):
    """Thread Qt : exécute uniquement le solveur exact Gurobi."""
    result_ready = QtCore.Signal(str, list)

    def __init__(
        self,
        materials: List[Dict],
        weight_cap: float,
        volume_cap: float,
        incompat_pairs: Optional[List[Tuple[str, str]]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.materials = materials
        self.weight_cap = weight_cap
        self.volume_cap = volume_cap
        self.incompat_pairs = incompat_pairs or []

    def run(self):
        try:
            msg, voyages = solve_bin_packing_trips_exact(
                self.materials,
                self.weight_cap,
                self.volume_cap,
                self.incompat_pairs
            )
            self.result_ready.emit(msg, voyages)
        except Exception as e:
            self.result_ready.emit(f"Erreur inattendue: {str(e)}", [])
