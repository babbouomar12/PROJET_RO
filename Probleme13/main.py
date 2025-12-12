# main.py
"""
Point d'entrée principal
"""
import sys
from ui.main_window import MainWindow
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

PRIMARY_COLOR = "#4F6EF7"
ACCENT_COLOR = "#2ECC71"
BACKGROUND_DARK = "#1E1E1E"
TEXT_LIGHT = "#f0f0f0"
FONT_FAMILY = "Segoe UI"

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    print("Current style:", app.style().objectName())
    

    # Palette sombre
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor("#1e1f22"))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor("#2b2d31"))
    dark_palette.setColor(QPalette.AlternateBase, QColor("#35373b"))
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor("#2b2d31"))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.Highlight, QColor(PRIMARY_COLOR))
    dark_palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(dark_palette)


    # StyleSheet moderne global
    app.setStyleSheet(f"""
        QWidget {{
            font-family: {FONT_FAMILY};
            font-size: 14px;
            color: {TEXT_LIGHT};
        }}
        QMainWindow {{
            background-color: {BACKGROUND_DARK};
        }}
        QTabWidget::pane {{
            border: 1px solid #444;
            background: {BACKGROUND_DARK};
        }}
        QTabBar::tab {{
            background: #2b2d31;
            padding: 10px 18px;
            border-radius: 6px;
            margin-right: 4px;
        }}
        QTabBar::tab:selected {{
            background: {PRIMARY_COLOR};
            color: white;
        }}
        QPushButton {{
            background-color: {PRIMARY_COLOR};
            border: none;
            padding: 10px 16px;
            border-radius: 6px;
            font-weight: bold;
            color: white;
        }}
        QPushButton:hover {{
            background-color: #6d88ff;
        }}
        QPushButton:disabled {{
            background-color: #555;
            color: #aaa;
        }}
        QSpinBox, QSlider, QLineEdit, QTextEdit {{
            background-color: #2b2d31;
            border: 1px solid #555;
            border-radius: 4px;
            padding: 4px;
        }}
        QTextEdit#logConsole {{
            background-color: #111;
            border-radius: 6px;
            font-family: Consolas, monospace;
        }}
        QTableView {{
            gridline-color: #444;
            background-color: #2b2d31;
            alternate-background-color: #35373b;
            border: 1px solid #444;
        }}
        QHeaderView::section {{
            background-color: #3a3c40;
            color: #f0f0f0;
            padding: 6px;
            border: none;
        }}
        QSlider::groove:horizontal {{
            border: 1px solid #555;
            height: 6px;
            background: #3a3c40;
            margin: 0px;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {ACCENT_COLOR};
            border: 1px solid #444;
            width: 16px;
            margin: -5px 0;
            border-radius: 8px;
        }}
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())