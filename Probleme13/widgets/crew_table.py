"""
CrewTableWidget - Widget pour saisir les données des équipages
"""
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class CrewTableWidget(QWidget):
    """Widget pour saisir les données des équipages"""
    
    def __init__(self, data_model, is_pilots=True):
        super().__init__()
        self.data = data_model
        self.is_pilots = is_pilots
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Barre d'outils
        toolbar = QHBoxLayout()
        add_btn = QPushButton(f"Ajouter un {'pilote' if self.is_pilots else 'copilote'}")
        add_btn.clicked.connect(self.add_row)
        del_btn = QPushButton("Supprimer la ligne")
        del_btn.clicked.connect(self.delete_row)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(del_btn)
        toolbar.addStretch()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        headers = ["ID", "Nom", "Qualifications", "Langues", "Coût/H", 
                  "Base", "Heures Min", "Heures Max"]
        self.table.setHorizontalHeaderLabels(headers)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(8):
            item = QTableWidgetItem("")
            self.table.setItem(row, col, item)
    
    def delete_row(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
    
    def save_to_model(self):
        """Sauvegarder les données dans le modèle"""
        if self.is_pilots:
            self.data.pilots.clear()
            add_func = self.data.add_pilot
        else:
            self.data.copilots.clear()
            add_func = self.data.add_copilot
        
        for row in range(self.table.rowCount()):
            try:
                crew_id = self.table.item(row, 0).text()
                name = self.table.item(row, 1).text()
                qualifications = self.table.item(row, 2).text().split(',')
                languages = self.table.item(row, 3).text().split(',')
                hourly_cost = float(self.table.item(row, 4).text())
                base = self.table.item(row, 5).text()
                min_hours = float(self.table.item(row, 6).text())
                max_hours = float(self.table.item(row, 7).text())
                
                add_func(crew_id, name, qualifications, languages,
                        hourly_cost, base, min_hours, max_hours)
            except:
                pass
    
    def load_from_model(self):
        """Charger les données depuis le modèle dans la table"""
        self.table.setRowCount(0)
        
        crew_list = self.data.pilots if self.is_pilots else self.data.copilots
        
        for crew in crew_list:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(crew['id']))
            self.table.setItem(row, 1, QTableWidgetItem(crew['name']))
            self.table.setItem(row, 2, QTableWidgetItem(','.join(crew['qualifications'])))
            self.table.setItem(row, 3, QTableWidgetItem(','.join(crew['languages'])))
            self.table.setItem(row, 4, QTableWidgetItem(str(crew['hourly_cost'])))
            self.table.setItem(row, 5, QTableWidgetItem(crew['base']))
            self.table.setItem(row, 6, QTableWidgetItem(str(crew['min_hours'])))
            self.table.setItem(row, 7, QTableWidgetItem(str(crew['max_hours'])))