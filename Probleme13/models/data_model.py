# models/data_model.py
"""
DataModel - Gestion des données avec un bon exemple
"""
import json


class DataModel:
    """Classe pour gérer toutes les données du problème"""
    
    def __init__(self):
        self.clear()
    
    def clear(self):
        """Réinitialiser toutes les données"""
        self.flights = []
        self.pilots = []
        self.copilots = []
        
        # Paramètres généraux
        self.min_rest = 8  # heures de repos minimum
        self.base_penalty_coeff = 100  # pénalité pour base différente
        self.lambda_weight = 0.5  # poids pour l'objectif combiné (0=coûts, 1=couverture)
        
        # Résultats
        self.solution = None
        self.objective_value = None
        self.status = None
        self.solve_time = None
    
    def add_flight(self, flight_id, departure, arrival, duration, 
                   aircraft_type, dep_base, arr_base, languages, op_cost):
        """Ajouter un vol"""
        self.flights.append({
            'id': flight_id,
            'departure': departure,
            'arrival': arrival,
            'duration': duration,
            'aircraft_type': aircraft_type,
            'dep_base': dep_base,
            'arr_base': arr_base,
            'languages': languages,
            'op_cost': op_cost
        })
    
    def add_pilot(self, pilot_id, name, qualifications, languages, 
                  hourly_cost, base, min_hours, max_hours):
        """Ajouter un pilote"""
        self.pilots.append({
            'id': pilot_id,
            'name': name,
            'qualifications': qualifications,
            'languages': languages,
            'hourly_cost': hourly_cost,
            'base': base,
            'min_hours': min_hours,
            'max_hours': max_hours
        })
    
    def add_copilot(self, copilot_id, name, qualifications, languages,
                    hourly_cost, base, min_hours, max_hours):
        """Ajouter un copilote"""
        self.copilots.append({
            'id': copilot_id,
            'name': name,
            'qualifications': qualifications,
            'languages': languages,
            'hourly_cost': hourly_cost,
            'base': base,
            'min_hours': min_hours,
            'max_hours': max_hours
        })
    
    def to_dict(self):
        """Convertir le modèle en dictionnaire pour sérialisation"""
        return {
            'flights': self.flights,
            'pilots': self.pilots,
            'copilots': self.copilots,
            'parameters': {
                'min_rest': self.min_rest,
                'base_penalty_coeff': self.base_penalty_coeff,
                'lambda_weight': self.lambda_weight
            }
        }
    
    def from_dict(self, data):
        """Charger le modèle depuis un dictionnaire"""
        self.clear()
        
        # Paramètres
        params = data.get('parameters', {})
        self.min_rest = params.get('min_rest', 8)
        self.base_penalty_coeff = params.get('base_penalty_coeff', 100)
        self.lambda_weight = params.get('lambda_weight', 0.5)
        
        # Vols
        for flight in data.get('flights', []):
            self.add_flight(**flight)
        
        # Pilotes
        for pilot in data.get('pilots', []):
            self.add_pilot(**pilot)
        
        # Copilotes
        for copilot in data.get('copilotes', data.get('copilots', [])):
            self.add_copilot(**copilot)
    
    def save_to_file(self, filename):
        """Sauvegarder le modèle dans un fichier JSON"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def load_from_file(self, filename):
        """Charger le modèle depuis un fichier JSON"""
        with open(filename, 'r') as f:
            data = json.load(f)
        self.from_dict(data)
    
    def load_example_data(self):
        """Charger un bon exemple de données compatibles"""
        self.clear()
        
        # Types d'avion
        aircraft_types = ['A320', 'B737']
        
        # Bases
        bases = ['CDG', 'ORY', 'MRS']
        
        # Langues
        languages = ['FR', 'EN']
        
        # ========== VOLS ==========
        # Tous les vols sont conçus pour être compatibles avec au moins un équipage
        
        # Vol 1: A320, parle FR, CDG -> MRS
        self.add_flight('AF1001', 8, 10, 2, 'A320', 'CDG', 'MRS', ['FR'], 500)
        
        # Vol 2: A320, parle FR, ORY -> CDG
        self.add_flight('AF1002', 11, 13, 2, 'A320', 'ORY', 'CDG', ['FR'], 550)
        
        # Vol 3: B737, parle EN, CDG -> ORY
        self.add_flight('AF1003', 14, 16, 2, 'B737', 'CDG', 'ORY', ['EN'], 600)
        
        # Vol 4: A320, parle FR+EN, MRS -> CDG
        self.add_flight('AF1004', 17, 19, 2, 'A320', 'MRS', 'CDG', ['FR', 'EN'], 650)
        
        # ========== PILOTES ==========
        # Chaque pilote peut faire au moins un vol
        
        # Pilote 1: Qualifié A320, parle FR, basé CDG
        self.add_pilot('P001', 'Jean Martin', ['A320'], ['FR'], 150, 'CDG', 0, 100)
        
        # Pilote 2: Qualifié A320+B737, parle FR+EN, basé ORY
        self.add_pilot('P002', 'Pierre Dubois', ['A320', 'B737'], ['FR', 'EN'], 160, 'ORY', 0, 100)
        
        # Pilote 3: Qualifié B737, parle EN, basé MRS
        self.add_pilot('P003', 'John Smith', ['B737'], ['EN'], 155, 'MRS', 0, 100)
        
        # ========== COPILOTES ==========
        # Chaque copilote peut faire au moins un vol
        
        # Copilote 1: Qualifié A320, parle FR, basé CDG
        self.add_copilot('C001', 'Marie Lambert', ['A320'], ['FR'], 120, 'CDG', 0, 90)
        
        # Copilote 2: Qualifié A320+B737, parle FR+EN, basé ORY
        self.add_copilot('C002', 'Sophie Bernard', ['A320', 'B737'], ['FR', 'EN'], 125, 'ORY', 0, 90)
        
        # Copilote 3: Qualifié B737, parle EN, basé MRS
        self.add_copilot('C003', 'Emma Wilson', ['B737'], ['EN'], 130, 'MRS', 0, 90)