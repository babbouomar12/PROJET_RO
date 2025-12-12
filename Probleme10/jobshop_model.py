from typing import Dict, Tuple
import gurobipy as gp
from gurobipy import GRB


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
