"""
Styles - Définition des styles et palettes pour l'interface
"""
from PyQt5.QtGui import QPalette, QColor


def create_modern_palette():
    """Créer une palette de couleurs moderne"""
    palette = QPalette()
    
    # Couleurs principales
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(233, 231, 227))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(0, 0, 255))
    palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    return palette


def get_stylesheet():
    """Retourner la feuille de style CSS pour l'application"""
    return """
    QMainWindow {
        background-color: #f0f0f0;
    }
    
    QTabWidget::pane {
        border: 1px solid #c0c0c0;
        background-color: white;
    }
    
    QTabBar::tab {
        background-color: #e0e0e0;
        padding: 8px;
        margin-right: 2px;
    }
    
    QTabBar::tab:selected {
        background-color: white;
        font-weight: bold;
    }
    
    QGroupBox {
        font-weight: bold;
        border: 2px solid #c0c0c0;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
    
    QTableWidget {
        gridline-color: #d0d0d0;
        selection-background-color: #4ca6ff;
    }
    
    QTableWidget::item {
        padding: 5px;
    }
    
    QHeaderView::section {
        background-color: #e8e8e8;
        padding: 5px;
        border: 1px solid #d0d0d0;
        font-weight: bold;
    }
    
    QTextEdit {
        border: 1px solid #c0c0c0;
        border-radius: 3px;
        padding: 5px;
    }
    
    QPushButton {
        padding: 8px 15px;
        border-radius: 4px;
        border: 1px solid #c0c0c0;
        font-weight: bold;
    }
    
    QPushButton:hover {
        background-color: #e8e8e8;
    }
    
    QPushButton:pressed {
        background-color: #d0d0d0;
    }
    
    QDoubleSpinBox, QSpinBox {
        padding: 5px;
        border: 1px solid #c0c0c0;
        border-radius: 3px;
    }
    
    QSlider::groove:horizontal {
        height: 8px;
        background: #d0d0d0;
        border-radius: 4px;
    }
    
    QSlider::handle:horizontal {
        background: #4ca6ff;
        width: 18px;
        margin: -5px 0;
        border-radius: 9px;
    }
    """