
from PyQt5.QtCore import QThread, pyqtSignal
import gurobipy as gp
from gurobipy import GRB
import os

# Ignorer les avertissements de version de licence Gurobi
os.environ['GRB_LICENSE_FILE'] = os.environ.get('GRB_LICENSE_FILE', '')



class GurobiSolver(QThread):
    
    finished_signal = pyqtSignal(dict)
    log_signal = pyqtSignal(str)
    
    def __init__(self, data_model):
        super().__init__()
        self.data = data_model
    
    def run(self):
        """Exécuter l'optimisation"""
        try:
            self.log_signal.emit("Initialisation du solveur Gurobi...")
            results = self.solve()
            self.finished_signal.emit(results)
        except Exception as e:
            self.log_signal.emit(f"Erreur: {str(e)}")
            self.finished_signal.emit({'error': str(e)})
    
    def solve(self):
        """Résoudre le problème d'affectation"""
        flights = self.data.flights
        pilots = self.data.pilots
        copilots = self.data.copilots
        
        # Vérifier les données
        if len(flights) == 0 or len(pilots) == 0 or len(copilots) == 0:
            return {
                'status': -1,
                'status_str': 'ERREUR',
                'message': 'Données insuffisantes',
                'solution': {}
            }
        
        # Créer le modèle
        model = gp.Model("CrewAssignment")
        model.setParam('OutputFlag', 0)
        model.setParam('TimeLimit', 30)
        
        self.log_signal.emit(f"Traitement de {len(flights)} vols, {len(pilots)} pilotes, {len(copilots)} copilotes")
        
        # === 1. CRÉER LES VARIABLES ===
        y_vars = {}  # Variables principales y_{f,p,c}
        
        # Seulement créer des variables pour les combinaisons compatibles
        for f_idx, flight in enumerate(flights):
            for p_idx, pilot in enumerate(pilots):
                for c_idx, copilot in enumerate(copilots):
                    # Vérifier compatibilité
                    compatible = True
                    
                    # Qualifications
                    if flight['aircraft_type'] not in pilot['qualifications']:
                        compatible = False
                    if flight['aircraft_type'] not in copilot['qualifications']:
                        compatible = False
                    
                    # Langues
                    if not all(lang in pilot['languages'] for lang in flight['languages']):
                        compatible = False
                    if not all(lang in copilot['languages'] for lang in flight['languages']):
                        compatible = False
                    
                    if compatible:
                        y_vars[(f_idx, p_idx, c_idx)] = model.addVar(
                            vtype=GRB.BINARY,
                            name=f"y_{flight['id']}_{pilot['name']}_{copilot['name']}"
                        )
        
        if len(y_vars) == 0:
            self.log_signal.emit("⚠️ Aucune combinaison compatible trouvée")
            return self.create_fallback_solution(flights, pilots, copilots)
        
        self.log_signal.emit(f"✅ {len(y_vars)} variables créées")
        
        # === 2. AJOUTER LES CONTRAINTES ===
        
        # Contrainte 1: Chaque vol au plus une équipe
        for f_idx in range(len(flights)):
            vars_for_flight = [v for (f,p,c), v in y_vars.items() if f == f_idx]
            if vars_for_flight:
                model.addConstr(gp.quicksum(vars_for_flight) <= 1, f"vol_{f_idx}")
        
        # Contrainte 2: Pas de chevauchement temporel
        # Calculer les chevauchements
        overlaps = []
        for i in range(len(flights)):
            for j in range(i + 1, len(flights)):
                f1 = flights[i]
                f2 = flights[j]
                # Chevauchement si les horaires se superposent
                if not (f1['arrival'] <= f2['departure'] or f2['arrival'] <= f1['departure']):
                    overlaps.append((i, j))
        
        # Pour chaque pilote, pas deux vols qui se chevauchent
        for p_idx in range(len(pilots)):
            for f1_idx, f2_idx in overlaps:
                vars_f1 = [v for (f,p,c), v in y_vars.items() if f == f1_idx and p == p_idx]
                vars_f2 = [v for (f,p,c), v in y_vars.items() if f == f2_idx and p == p_idx]
                if vars_f1 and vars_f2:
                    model.addConstr(gp.quicksum(vars_f1) + gp.quicksum(vars_f2) <= 1,
                                  f"overlap_p{p_idx}_{f1_idx}_{f2_idx}")
        
        # Même chose pour copilotes
        for c_idx in range(len(copilots)):
            for f1_idx, f2_idx in overlaps:
                vars_f1 = [v for (f,p,c), v in y_vars.items() if f == f1_idx and c == c_idx]
                vars_f2 = [v for (f,p,c), v in y_vars.items() if f == f2_idx and c == c_idx]
                if vars_f1 and vars_f2:
                    model.addConstr(gp.quicksum(vars_f1) + gp.quicksum(vars_f2) <= 1,
                                  f"overlap_c{c_idx}_{f1_idx}_{f2_idx}")
        
        # Contrainte 3: Repos minimal entre vols consécutifs
        min_rest = self.data.min_rest
        for p_idx in range(len(pilots)):
            for i in range(len(flights)):
                for j in range(len(flights)):
                    if i != j:
                        f1 = flights[i]
                        f2 = flights[j]
                        # f2 est après f1
                        if f2['departure'] > f1['arrival']:
                            time_between = f2['departure'] - f1['arrival']
                            if 0 < time_between < min_rest:
                                vars_i = [v for (f,p,c), v in y_vars.items() if f == i and p == p_idx]
                                vars_j = [v for (f,p,c), v in y_vars.items() if f == j and p == p_idx]
                                if vars_i and vars_j:
                                    model.addConstr(gp.quicksum(vars_i) + gp.quicksum(vars_j) <= 1,
                                                  f"rest_p{p_idx}_{i}_{j}")
        
        # Contrainte 4: Heures de vol maximum
        for p_idx, pilot in enumerate(pilots):
            hours_expr = []
            for (f_idx, p, c), var in y_vars.items():
                if p == p_idx:
                    flight = flights[f_idx]
                    hours_expr.append(flight['duration'] * var)
            if hours_expr:
                model.addConstr(gp.quicksum(hours_expr) <= pilot['max_hours'],
                              f"max_hours_p{p_idx}")
        
        for c_idx, copilot in enumerate(copilots):
            hours_expr = []
            for (f_idx, p, c), var in y_vars.items():
                if c == c_idx:
                    flight = flights[f_idx]
                    hours_expr.append(flight['duration'] * var)
            if hours_expr:
                model.addConstr(gp.quicksum(hours_expr) <= copilot['max_hours'],
                              f"max_hours_c{c_idx}")
        
        # Contrainte 5: Forcer au moins une affectation
        if len(y_vars) > 0:
            model.addConstr(gp.quicksum(y_vars.values()) >= 1, "min_one_assignment")
        
        # === 3. DÉFINIR L'OBJECTIF ===
        self.log_signal.emit(f"Définition de l'objectif (λ={self.data.lambda_weight:.2f})...")
        
        # Objectif 1: Maximisation du service (nombre de vols)
        Z1 = gp.quicksum(y_vars.values())
        
        # Objectif 2: Minimisation des coûts
        cost_expr = []
        for (f_idx, p_idx, c_idx), var in y_vars.items():
            flight = flights[f_idx]
            pilot = pilots[p_idx]
            copilot = copilots[c_idx]
            
            # Coût salarial
            salary_cost = (pilot['hourly_cost'] + copilot['hourly_cost']) * flight['duration']
            
            # Coût opérationnel
            op_cost = flight['op_cost']
            
            # Pénalité base
            base_penalty = 0
            if flight['arr_base'] != pilot['base']:
                base_penalty += 1
            if flight['arr_base'] != copilot['base']:
                base_penalty += 1
            base_penalty *= self.data.base_penalty_coeff
            
            total_cost = salary_cost + op_cost + base_penalty
            
            # Pour MAXIMISATION, on veut MINIMISER les coûts
            cost_expr.append(-total_cost * var)
        
        Z2 = gp.quicksum(cost_expr)
        
        # Objectif combiné
        lambda_val = self.data.lambda_weight
        
        if lambda_val == 0:
            # Minimisation pure des coûts
            objective = Z2
        elif lambda_val == 1:
            # Maximisation pure de la couverture
            objective = Z1
        else:
            # Combinaison pondérée
            # Normaliser Z1 (chaque vol vaut environ 1000€)
            weight_per_flight = 1000
            normalized_Z1 = Z1 * weight_per_flight
            objective = lambda_val * normalized_Z1 + (1 - lambda_val) * Z2
        
        model.setObjective(objective, GRB.MAXIMIZE)
        
        # === 4. RÉSOUDRE ===
        self.log_signal.emit("Résolution en cours...")
        model.optimize()
        
        # === 5. EXTRACTION DES RÉSULTATS ===
        results = self.extract_results(model, y_vars, flights, pilots, copilots)
        
        return results

    def extract_results(self, model, y_vars, flights, pilots, copilots):
        """Extraire les résultats"""
        results = {
            'status': model.status,
            'status_str': self.get_status_string(model.status),
            'objective_value': None,
            'solve_time': model.Runtime,
            'solution': {},
            'assignments': [],
            'total_cost': 0,  # AJOUTER CE CHAMP
            'message': ''
        }

        if model.status == GRB.OPTIMAL:
            results['objective_value'] = model.ObjVal

            # Extraire les affectations AVEC COÛTS
            assignments = []
            total_cost = 0

            for (f_idx, p_idx, c_idx), var in y_vars.items():
                if var.X > 0.5:
                    results['solution'][(f_idx, p_idx, c_idx)] = var.X

                    flight = flights[f_idx]
                    pilot = pilots[p_idx]
                    copilot = copilots[c_idx]

                    # Calculer le coût exact
                    salary_cost = (pilot['hourly_cost'] + copilot['hourly_cost']) * flight['duration']
                    op_cost = flight['op_cost']

                    # Pénalité base
                    base_penalty = 0
                    if flight['arr_base'] != pilot['base']:
                        base_penalty += 1
                    if flight['arr_base'] != copilot['base']:
                        base_penalty += 1
                    base_penalty *= self.data.base_penalty_coeff

                    flight_cost = salary_cost + op_cost + base_penalty
                    total_cost += flight_cost

                    assignments.append({
                        'flight': flight['id'],
                        'pilot': pilot['name'],
                        'copilot': copilot['name'],
                        'departure': float(flight['departure']),
                        'arrival': float(flight['arrival']),
                        'duration': float(flight['duration']),
                        'aircraft': flight['aircraft_type'],
                        'cost': flight_cost,
                        'cout': flight_cost,  # Pour compatibilité
                        'vol': flight['id'],  # Pour compatibilité
                        'pilote': pilot['name'],
                        'copilote': copilot['name'],
                        'heure_depart': float(flight['departure']),
                        'heure_arrivee': float(flight['arrival']),
                        'duree': float(flight['duration'])
                    })

            results['assignments'] = assignments
            results['total_cost'] = total_cost  # STOCKER LE COÛT TOTAL
            results['message'] = f"✅ {len(assignments)} affectations trouvées"

        return results

    def calculate_manual_cost(self, flight, pilot, copilot, data_model):
        """Calculer le coût manuellement"""
        try:
            # Coût salarial
            salary_cost = (pilot['hourly_cost'] + copilot['hourly_cost']) * flight['duration']

            # Coût opérationnel
            op_cost = flight.get('op_cost', 500)

            # Pénalité base
            base_penalty = 0
            if flight.get('arr_base') != pilot.get('base'):
                base_penalty += 1
            if flight.get('arr_base') != copilot.get('base'):
                base_penalty += 1

            base_penalty *= data_model.base_penalty_coeff

            total_cost = salary_cost + op_cost + base_penalty

            print(f"DEBUG calculate_manual_cost:")
            print(f"  Salary: {salary_cost}, Op: {op_cost}, Penalty: {base_penalty}")
            print(f"  Total: {total_cost}")

            return total_cost
        except Exception as e:
            print(f"ERROR in calculate_manual_cost: {e}")
            return 0
    
    def get_status_string(self, status):
        """Convertir code statut en texte"""
        if status == GRB.OPTIMAL:
            return 'OPTIMAL'
        elif status == GRB.INFEASIBLE:
            return 'INFAISABLE'
        elif status == GRB.TIME_LIMIT:
            return 'TEMPS_LIMITE'
        else:
            return 'AUTRE'
    
    def create_fallback_solution(self, flights, pilots, copilots):
        """Créer une solution de secours"""
        solution = {}
        assignments = []
        
        # Essayer de créer au moins une affectation
        if flights and pilots and copilots:
            # Prendre le premier vol, premier pilote, premier copilote
            if (flights[0]['aircraft_type'] in pilots[0]['qualifications'] and
                flights[0]['aircraft_type'] in copilots[0]['qualifications']):
                
                solution[(0, 0, 0)] = 1.0
                assignments.append({
                    'flight': flights[0]['id'],
                    'pilot': pilots[0]['name'],
                    'copilot': copilots[0]['name'],
                    'departure': flights[0]['departure'],
                    'arrival': flights[0]['arrival'],
                    'duration': flights[0]['duration'],
                    'aircraft': flights[0]['aircraft_type'],
                    'cost': (pilots[0]['hourly_cost'] + copilots[0]['hourly_cost']) * flights[0]['duration'] + flights[0]['op_cost']
                })
        
        return {
            'status': 2,
            'status_str': 'OPTIMAL (secours)',
            'objective_value': len(solution),
            'solve_time': 0.1,
            'solution': solution,
            'assignments': assignments,
            'message': f"✅ Solution de secours: {len(solution)} affectation(s)"
        }