import sys
import os
import math
import random
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QVBoxLayout, 
                             QWidget, QLabel, QTableWidget, QPushButton, QHBoxLayout, 
                             QHeaderView, QTextEdit, QGraphicsView, QGraphicsScene, 
                             QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsSimpleTextItem,
                             QComboBox, QTableWidgetItem, QGraphicsItem)
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter, QPolygonF
import networkx as nx

# ==========================================
# STYLESHEET
# ==========================================

GRAPH_STYLESHEET = """
QMainWindow {
    background-color: #1e1e2e;
    color: #cdd6f4;
}
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
QTabWidget::pane {
    border: 1px solid #313244;
    background: #1e1e2e;
}
QTabBar::tab {
    background: #313244;
    color: #a6adc8;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
}
QTableWidget {
    background-color: #181825;
    border: 1px solid #313244;
    gridline-color: #45475a;
    color: #cdd6f4;
}
QHeaderView::section {
    background-color: #313244;
    color: #cdd6f4;
    padding: 5px;
    border: none;
    font-weight: bold;
}
QPushButton {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    border: none;
}
QPushButton:hover {
    background-color: #b4befe;
}
QPushButton#solveBtn {
    background-color: #a6e3a1; /* Green */
    color: #1e1e2e;
}
QPushButton#solveBtn:hover {
    background-color: #94e2d5;
}
QTextEdit {
    background-color: #181825;
    border: 1px solid #313244;
    color: #cdd6f4;
    font-family: 'Consolas', monospace;
}
QLabel {
    color: #cdd6f4;
    font-weight: bold;
    margin-bottom: 5px;
}
"""

# ==========================================
# MODEL CLASSES
# ==========================================

class FlowModel:
    def __init__(self):
        self.arcs = []
        # Explicit mock data for demo if empty
        self.mock_init()

    def mock_init(self):
        # Demo data: Simple flow network with mixed Water/Gas
        self.add_arc("S", "A", 10, 2, "Eau")
        self.add_arc("S", "B", 8, 4, "Gaz")
        self.add_arc("A", "B", 5, 1, "Eau")
        self.add_arc("A", "T", 7, 6, "Gaz")
        self.add_arc("B", "T", 6, 3, "Eau")

    def add_arc(self, source, target, capacity, cost, type="Eau"):
        self.arcs.append({
            "source": source,
            "target": target,
            "capacity": int(capacity),
            "cost": float(cost),
            "type": type
        })
    
    def clear(self):
        self.arcs = []

    def get_nodes(self):
        nodes = set()
        for arc in self.arcs:
            nodes.add(arc['source'])
            nodes.add(arc['target'])
        return sorted(list(nodes))

class GurobiSolver:
    def solve(self, model_data):
        # Mock Solver Logic similar to Min Cost Flow
        total_cost = 0
        flows = {}
        
        # Simple heuristic for mock result: saturate cheapest paths
        # This is NOT a real solver, just for UI demonstration
        print("Solving with Mock Logic...")
        
        for arc in model_data.arcs:
            # Fake logic: sending 50% capacity flow
            flow = arc['capacity'] * 0.5 
            flows[f"{arc['source']}->{arc['target']}"] = flow
            total_cost += flow * arc['cost']
            
        return {
            "status": "Optimal",
            "objective": total_cost,
            "flows": flows
        }

# ==========================================
# GUI WIDGETS
# ==========================================

class DataInputWidget(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Configuration du Réseau")
        title.setStyleSheet("font-size: 18px; color: #89b4fa;")
        layout.addWidget(title)
        
        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Source", "Destination", "Capacité", "Coût Unit.", "Type"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
        # Control Bar
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton(" Ajouter un Arc")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        
        self.clear_btn = QPushButton("Effacer Tout")
        self.clear_btn.setStyleSheet("background-color: #f38ba8; color: #1e1e2e;")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        
        self.solve_btn = QPushButton(" Calculer Flux Optimal")
        self.solve_btn.setObjectName("solveBtn") # For specific styling
        self.solve_btn.setCursor(Qt.PointingHandCursor)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.solve_btn)
        
        layout.addLayout(btn_layout)
        
        # Connections
        self.add_btn.clicked.connect(self.add_default_row)
        self.clear_btn.clicked.connect(self.clear_table)
        
        # Init table with model data
        self.refresh_from_model()

    def add_default_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Add ComboBox for Type
        combo = QComboBox()
        combo.addItems(["Eau", "Gaz"])
        self.table.setCellWidget(row, 4, combo)
    
    def clear_table(self):
        self.table.setRowCount(0)
        self.model.clear()

    def refresh_from_model(self):
        self.table.setRowCount(0)
        for arc in self.model.arcs:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(arc['source'])))
            self.table.setItem(row, 1, QTableWidgetItem(str(arc['target'])))
            self.table.setItem(row, 2, QTableWidgetItem(str(arc['capacity'])))
            self.table.setItem(row, 3, QTableWidgetItem(str(arc['cost'])))
            
            combo = QComboBox()
            combo.addItems(["Eau", "Gaz"])
            combo.setCurrentText(arc.get('type', "Eau"))
            self.table.setCellWidget(row, 4, combo)

    def save_to_model(self):
        self.model.clear()
        for row in range(self.table.rowCount()):
            s = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            t = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            cap = self.table.item(row, 2).text() if self.table.item(row, 2) else "0"
            cost = self.table.item(row, 3).text() if self.table.item(row, 3) else "0"
            
            combo = self.table.cellWidget(row, 4)
            arc_type = combo.currentText() if combo else "Eau"
            
            if s and t:
                self.model.add_arc(s, t, cap, cost, arc_type)

                self.model.add_arc(s, t, cap, cost, arc_type)

class ArrowArc(QGraphicsLineItem):
    def __init__(self, source_node, target_node, cost, arc_type):
        super().__init__()
        self.source = source_node
        self.target = target_node
        self.cost = cost
        
        # Color
        if arc_type == "Gaz":
            self.color = QColor("#fab387")
        else:
            self.color = QColor("#89b4fa")
            
        self.setPen(QPen(self.color, 3))
        self.setZValue(-1)
        
        # Text Label
        self.label = QGraphicsSimpleTextItem(f"{cost}$")
        self.label.setBrush(QBrush(QColor("#a6e3a1")))
        self.label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        
        self.update_position()

    def update_position(self):
        line = QLineF(self.source.scenePos(), self.target.scenePos())
        self.setLine(line)
        
        # Update Label Position
        mid = line.center()
        self.label.setPos(mid.x(), mid.y())

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        
        # Draw ArrowHead
        line = self.line()
        if line.length() == 0: return
        
        # Vector
        v = line.p2() - line.p1()
        length = math.sqrt(v.x()**2 + v.y()**2)
        if length == 0: return

        # Normalize
        norm_x = v.x() / length
        norm_y = v.y() / length
        
        # Arrow config
        arrow_size = 15
        offset = 20 # Offset from center of node (radius)
        
        # Point at edge of target node
        end_x = line.p2().x() - norm_x * offset
        end_y = line.p2().y() - norm_y * offset
        
        p2 = QPointF(end_x, end_y)
        
        # Arrow points
        # Rotate -150 and +150 degrees
        angle = math.atan2(norm_y, norm_x)
        arrow_p1 = p2 - QPointF(math.cos(angle + math.pi/6) * arrow_size, 
                                math.sin(angle + math.pi/6) * arrow_size)
        arrow_p2 = p2 - QPointF(math.cos(angle - math.pi/6) * arrow_size, 
                                math.sin(angle - math.pi/6) * arrow_size)
        
        arrow_head = QPolygonF([p2, arrow_p1, arrow_p2])
        
        painter.setBrush(QBrush(self.color))
        painter.drawPolygon(arrow_head)

class DraggableNode(QGraphicsEllipseItem):
    def __init__(self, name, rect):
        super().__init__(rect)
        self.name = name
        self.setBrush(QBrush(QColor("#89b4fa")))
        self.setPen(QPen(Qt.NoPen))
        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemSendsGeometryChanges)
        
        self.edges = []
        
        # Label
        self.text = QGraphicsSimpleTextItem(name, self)
        self.text.setBrush(QBrush(QColor("#1e1e2e")))
        self.text.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        # Center text
        r = self.rect()
        b = self.text.boundingRect()
        self.text.setPos(r.x() + r.width()/2 - b.width()/2, 
                         r.y() + r.height()/2 - b.height()/2)

    def add_edge(self, edge):
        self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setBackgroundBrush(QBrush(QColor("#181825")))
        
        layout.addWidget(self.view)
        
    def draw_graph(self, model):
        self.scene.clear()
        nodes = model.get_nodes()
        if not nodes:
            return

        # NetworkX Layout for better positioning
        try:
            G = nx.DiGraph()
            G.add_nodes_from(nodes)
            for arc in model.arcs:
                G.add_edge(arc['source'], arc['target'])
            
            # Spring Layout
            pos = nx.spring_layout(G, scale=200, seed=42)
            
            # Scale and Center (networkx is -1 to 1)
            # We map to e.g. 0,0 center with 200 scale
            # No manual mapping needed if we just use pos directly * scale
            
        except Exception as e:
            print(f"NetworkX error: {e}, using Circle Layout")
            # Fallback Circle Layout
            center_x, center_y = 0, 0
            radius = 200
            angle_step = 2 * math.pi / len(nodes)
            pos = {}
            for i, node_name in enumerate(nodes):
                angle = i * angle_step
                pos[node_name] = (radius * math.cos(angle), radius * math.sin(angle))
        
        node_items = {}
        
        # 1. Create Nodes
        for node_name in nodes:
            x, y = pos[node_name]
            # Convert numpy types if any
            x = float(x) if hasattr(x, "item") else x * 200 if 'networkx' in sys.modules else x
            y = float(y) if hasattr(y, "item") else y * 200 if 'networkx' in sys.modules else y
            
            # Correction: spring_layout returns dict of coords. 
            # If standard circle fallback, x,y are already scaled.
            # If networkx, they are usually small floats. I multiply by 200 above.
            
            node_item = DraggableNode(node_name, QRectF(-20, -20, 40, 40))
            node_item.setPos(x, y)
            self.scene.addItem(node_item)
            node_items[node_name] = node_item
            
        # 2. Create Arcs
        for arc in model.arcs:
             if arc['source'] in node_items and arc['target'] in node_items:
                source_item = node_items[arc['source']]
                target_item = node_items[arc['target']]
                
                edge = ArrowArc(source_item, target_item, arc['cost'], arc.get('type', 'Eau'))
                self.scene.addItem(edge)
                self.scene.addItem(edge.label)
                
                source_item.add_edge(edge)
                target_item.add_edge(edge)

        # 3. Fit in View / Set Scene Rect
        items_rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(items_rect.adjusted(-50, -50, 50, 50))

class SimpleBarChart(QWidget):
    def __init__(self):
        super().__init__()
        self.data_items = [] # (label, value, max_value, color)
        self.setMinimumHeight(250)
        self.setStyleSheet("background-color: #181825; border-radius: 8px;")

    def set_data(self, flows, model):
        self.data_items = []
        for arc in model.arcs:
            key = f"{arc['source']}->{arc['target']}"
            if key in flows:
                flow_val = flows[key]
                cap = arc['capacity']
                
                # Determine color based on usage
                ratio = flow_val / cap if cap > 0 else 0
                
                # Base color from type
                if arc.get('type') == 'Gaz':
                    bar_color = QColor("#fab387")
                else:
                    bar_color = QColor("#89b4fa")
                
                # Darken if full
                if ratio >= 1.0:
                    bar_color = bar_color.darker(120)

                self.data_items.append({
                    "label": key,
                    "value": flow_val,
                    "max": cap,
                    "color": bar_color
                })
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor("#181825"))
        
        if not self.data_items:
            painter.setPen(QColor("#a6adc8"))
            painter.drawText(self.rect(), Qt.AlignCenter, "Aucune donnée de flux")
            return

        # Layout metrics
        margin_x = 40
        margin_y = 20
        bar_height = 20
        spacing = 15
        
        current_y = margin_y
        w = self.width() - 2 * margin_x
        max_val_display = max([d['max'] for d in self.data_items]) if self.data_items else 1 
        
        for item in self.data_items:
            # Draw Label
            painter.setPen(QColor("#cdd6f4"))
            painter.drawText(10, current_y + 15, item['label'])
            
            # Draw Background Bar (Capacity)
            bar_rect = QRectF(margin_x + 60, current_y, w - 80, bar_height)
            painter.setBrush(QBrush(QColor("#313244")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(bar_rect, 4, 4)
            
            # Draw Foreground Bar (Flow)
            pct = item['value'] / max_val_display
            fill_width = bar_rect.width() * pct
            fill_rect = QRectF(margin_x + 60, current_y, fill_width, bar_height)
            painter.setBrush(QBrush(item['color']))
            painter.drawRoundedRect(fill_rect, 4, 4)
            
            # Draw Text Value
            val_text = f"{item['value']:.1f} / {item['max']}"
            painter.setPen(QColor("#a6adc8"))
            painter.drawText(bar_rect.right() + 10, current_y + 15, val_text)
            
            current_y += bar_height + spacing

class ResultsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Rapport d'Optimisation")
        title.setStyleSheet("font-size: 18px; color: #a6e3a1;")
        layout.addWidget(title)
        
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        self.results_area.setMaximumHeight(150)
        layout.addWidget(self.results_area)
        
        # Chart
        self.chart = SimpleBarChart()
        layout.addWidget(self.chart)
        layout.addStretch()
        
    def display_results(self, result, model=None):
        html = f"""
        <h2 style='color: #89b4fa'>Statut: {result['status']}</h2>
        <h3 style='color: #a6e3a1'>Coût Total: {result['objective']} $</h3>
        """
        self.results_area.setHtml(html)
        
        if model:
            self.chart.set_data(result['flows'], model)

# ==========================================
# MAIN WINDOW
# ==========================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flux Cout Minimal - Édition Intégrale")
        self.resize(1200, 850)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("OPTIMISEUR DE FLUX")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px; spacing: 20px; color: #cdd6f4;")
        layout.addWidget(header)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Init Model
        self.model = FlowModel()
        self.solver = GurobiSolver()
        
        # Init Widgets
        self.data_input = DataInputWidget(self.model)
        self.graph_widget = GraphWidget()
        self.results_widget = ResultsWidget()
        
        # Add Tabs
        self.tabs.addTab(self.data_input, "1. Définition du Réseau")
        self.tabs.addTab(self.graph_widget, "2. Visualisation")
        self.tabs.addTab(self.results_widget, "3. Résultats")
        
        # Signals
        self.data_input.solve_btn.clicked.connect(self.run_optimization)
        self.tabs.currentChanged.connect(self.on_tab_change)

    def on_tab_change(self, index):
        if index == 1: # Validation/Graph Tab
            self.data_input.save_to_model()
            self.graph_widget.draw_graph(self.model)

    def run_optimization(self):
        self.data_input.save_to_model()
        results = self.solver.solve(self.model)
        self.results_widget.display_results(results, self.model)
        self.tabs.setCurrentIndex(2) # Switch to results

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    app = QApplication(sys.argv)
    app.setStyleSheet(GRAPH_STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()