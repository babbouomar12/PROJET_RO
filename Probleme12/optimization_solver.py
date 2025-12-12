"""
Module pour les modèles d'optimisation PL et PLNE avec Gurobi
Contient la logique de résolution des problèmes de capacité réseau
"""

import gurobipy as gp
from gurobipy import GRB


def solve_capacity_pl(nodes, links, demands):
    """Résolution du problème d'optimisation de capacité en PL (variables continues)."""
    model = gp.Model("Capacity_Upgrade_PL")
    model.setParam('OutputFlag', 0)
    link_ids = list(links.keys())
    demand_ids = list(range(len(demands)))
    
    # Variables de décision
    x = model.addVars(link_ids, name="x", lb=0)
    f = model.addVars(link_ids, demand_ids, name="f", lb=0)
    
    # Fonction objectif
    model.setObjective(gp.quicksum(links[l]["cost"] * x[l] for l in link_ids), GRB.MINIMIZE)
    
    # Contraintes de conservation du flux
    for k in demand_ids:
        src, dst, d_k = demands[k]["src"], demands[k]["dst"], demands[k]["d"]
        for n in nodes:
            flow_expr = gp.quicksum(f[l, k] for l in link_ids if links[l]["src"] == n) - \
                        gp.quicksum(f[l, k] for l in link_ids if links[l]["dst"] == n)
            if n == src: 
                model.addConstr(flow_expr == d_k)
            elif n == dst: 
                model.addConstr(flow_expr == -d_k)
            else: 
                model.addConstr(flow_expr == 0)
    
    # Contraintes de capacité
    for l in link_ids:
        model.addConstr(gp.quicksum(f[l, k] for k in demand_ids) <= links[l]["C0"] + x[l])
    
    # Résolution
    model.optimize()
    
    # Résultats
    if model.status == GRB.OPTIMAL:
        return model.objVal, {l: x[l].X for l in link_ids}, {(l, k): f[l, k].X for l, k in f}, "Optimal"
    return None, None, None, GRB.StatusMessage.get(model.status, "Unknown")


def solve_capacity_plne(nodes, links, demands, modules):
    """
    Résolution du problème d'optimisation de capacité en PLNE avec modules discrets.
    """
    
    # Initialisation du modèle
    model = gp.Model("Capacity_Upgrade_PLNE")
    model.setParam('OutputFlag', 0)
    
    print(links)
    link_ids = list(links.keys())
    demand_ids = list(range(len(demands)))
    module_types = list(modules.keys())
    
    # Variables de décision
    y = model.addVars(link_ids, module_types, name="y", vtype=GRB.INTEGER, lb=0)
    f = model.addVars(link_ids, demand_ids, name="f", lb=0)
    
    # Fonction objectif: minimiser le coût total d'installation
    obj_expr = gp.quicksum(
        links[l]["cost"] * modules[m]["capacity"] * modules[m]["cost_factor"] * y[l, m]
        for l in link_ids for m in module_types
    )
    model.setObjective(obj_expr, GRB.MINIMIZE)
    
    # Contraintes de conservation du flux
    for k in demand_ids:
        src, dst, d_k = demands[k]["src"], demands[k]["dst"], demands[k]["d"]
        
        for n in nodes:
            flow_expr = gp.quicksum(f[l, k] for l in link_ids if links[l]["src"] == n) - \
                        gp.quicksum(f[l, k] for l in link_ids if links[l]["dst"] == n)
            
            if n == src: 
                model.addConstr(flow_expr == d_k)
            elif n == dst: 
                model.addConstr(flow_expr == -d_k)
            else: 
                model.addConstr(flow_expr == 0)
    
    # Contraintes de capacité
    for l in link_ids:
        capacity_added = gp.quicksum(modules[m]["capacity"] * y[l, m] for m in module_types)
        model.addConstr(
            gp.quicksum(f[l, k] for k in demand_ids) <= links[l]["C0"] + capacity_added
        )
    
    # Résolution
    model.optimize()
    
    # Extraction des résultats
    if model.status == GRB.OPTIMAL:
        x_equiv = {}
        y_values = {}
        
        for l in link_ids:
            x_equiv[l] = sum(modules[m]["capacity"] * y[l, m].X for m in module_types)
            for m in module_types:
                y_values[(l, m)] = y[l, m].X
        
        return model.objVal, x_equiv, {(l, k): f[l, k].X for l, k in f}, "Optimal", y_values
    
    return None, None, None, GRB.StatusMessage.get(model.status, "Unknown"), None
