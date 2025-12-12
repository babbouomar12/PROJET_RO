"""
FlightTableWidget - Widget pour saisir les données des vols
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class FlightTableWidget(QWidget):
    """Widget pour saisir les données des vols"""
    
    def __init__(self, data_model):
        super().__init__()
        self.data = data_model
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Barre d'outils
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Ajouter un vol")
        add_btn.clicked.connect(self.add_row)
        del_btn = QPushButton("Supprimer la ligne")
        del_btn.clicked.connect(self.delete_row)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(del_btn)
        toolbar.addStretch()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        headers = ["ID", "Départ", "Arrivée", "Durée", "Type Avion", 
                  "Base Départ", "Base Arrivée", "Langues", "Coût Op."]
        self.table.setHorizontalHeaderLabels(headers)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        # Remplir avec des valeurs par défaut
        for col in range(9):
            item = QTableWidgetItem("")
            self.table.setItem(row, col, item)
    
    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
    
    def save_to_model(self):
        """Sauvegarder les données dans le modèle"""
        self.data.flights.clear()
        
        for row in range(self.table.rowCount()):
            try:
                flight_id = self.table.item(row, 0).text()
                departure = float(self.table.item(row, 1).text())
                arrival = float(self.table.item(row, 2).text())
                duration = float(self.table.item(row, 3).text())
                aircraft_type = self.table.item(row, 4).text()
                dep_base = self.table.item(row, 5).text()
                arr_base = self.table.item(row, 6).text()
                languages = self.table.item(row, 7).text().split(',')
                op_cost = float(self.table.item(row, 8).text())
                
                self.data.add_flight(flight_id, departure, arrival, duration,
                                   aircraft_type, dep_base, arr_base, 
                                   languages, op_cost)
            except:
                pass  # Ignorer les lignes incomplètes
    
    def load_from_model(self):
        """Charger les données depuis le modèle dans la table"""
        self.table.setRowCount(0)
        
        for flight in self.data.flights:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(flight['id']))
            self.table.setItem(row, 1, QTableWidgetItem(str(flight['departure'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(flight['arrival'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(flight['duration'])))
            self.table.setItem(row, 4, QTableWidgetItem(flight['aircraft_type']))
            self.table.setItem(row, 5, QTableWidgetItem(flight['dep_base']))
            self.table.setItem(row, 6, QTableWidgetItem(flight['arr_base']))
            self.table.setItem(row, 7, QTableWidgetItem(','.join(flight['languages'])))
            self.table.setItem(row, 8, QTableWidgetItem(str(flight['op_cost'])))