# main.py
import sys
from PySide6 import QtWidgets, QtGui, QtCore

from gui import BinPackingWindow


def set_dark_theme(app: QtWidgets.QApplication):
    """Applique un thème sombre global à l'application."""
    app.setStyle("Fusion")

    palette = QtGui.QPalette()

    # Couleurs de base
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(40, 40, 40))
    palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(30, 30, 30))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(45, 45, 45))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(45, 45, 45))
    palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)

    # Liens
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))

    # Surbrillance (sélection)
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(70, 120, 200))
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)

    # Désactivé
    disabled_color = QtGui.QColor(120, 120, 120)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, disabled_color)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, disabled_color)

    app.setPalette(palette)

    # StyleSheet pour peaufiner
    app.setStyleSheet("""
        QMainWindow {
            background-color: #282828;
        }
        QTableWidget {
            gridline-color: #505050;
            selection-background-color: #4678C8;
            selection-color: #ffffff;
        }
        QHeaderView::section {
            background-color: #3A3A3A;
            color: #ffffff;
            padding: 4px;
            border: 1px solid #505050;
        }
        QTextEdit {
            background-color: #202020;
            color: #ffffff;
        }
        QPlainTextEdit {
            background-color: #202020;
            color: #ffffff;
        }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background-color: #202020;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        QPushButton {
            background-color: #3A3A3A;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px 10px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #505050;
        }
        QPushButton:pressed {
            background-color: #606060;
        }
    """)


def main():
    app = QtWidgets.QApplication(sys.argv)
    set_dark_theme(app)

    window = BinPackingWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
