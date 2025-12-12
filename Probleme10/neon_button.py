from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import QPropertyAnimation, QAbstractAnimation
from PySide6.QtGui import QColor


class NeonButton(QPushButton):
    """Bouton avec effet néon + animation hover."""

    def __init__(self, text: str = "", accent_color: str = "#5C8CFF", parent=None):
        super().__init__(text, parent)

        self.accent_color = QColor(accent_color)

        # Effet d'ombre portée pour le glow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(8)
        self.shadow.setColor(self.accent_color)
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        # Animation du blur -> glow plus fort au survol
        self.anim = QPropertyAnimation(self.shadow, b"blurRadius", self)
        self.anim.setDuration(200)
        self.anim.setStartValue(8)
        self.anim.setEndValue(24)

    def enterEvent(self, event):
        self.anim.setDirection(QAbstractAnimation.Forward)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.setDirection(QAbstractAnimation.Backward)
        self.anim.start()
        super().leaveEvent(event)
