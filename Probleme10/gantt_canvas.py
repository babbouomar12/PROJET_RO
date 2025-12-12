from typing import Dict, Tuple

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor


class GanttCanvas(FigureCanvasQTAgg):
    def __init__(self, parent: QWidget = None):
        fig = Figure()
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

        # Couleurs dark pour la figure
        fig.patch.set_facecolor("#151515")
        self.ax.set_facecolor("#151515")

    def plot_schedule(
        self,
        nb_machines: int,
        machines: Dict[Tuple[int, int], int],
        durations: Dict[Tuple[int, int], float],
        schedule: Dict[Tuple[int, int], float]
    ):
        """
        Trace un diagramme de Gantt :
        - Axe X = temps
        - Axe Y = machines
        - Chaque barre = un test d'une éolienne sur une machine
        """
        self.ax.clear()
        self.ax.set_facecolor("#151515")

        bar_colors = ["#4ECCA3", "#3E9EFF", "#FFB347", "#FF6F61", "#BD93F9"]

        for idx, ((j, o), start) in enumerate(schedule.items()):
            m_id = machines[(j, o)]
            dur = durations[(j, o)]
            y = m_id

            color = bar_colors[idx % len(bar_colors)]

            self.ax.barh(
                y=y,
                width=dur,
                left=start,
                height=0.7,
                color=color,
                edgecolor="#111111"
            )

            label = f"E{j+1}-T{o+1}"
            self.ax.text(
                start + dur / 2,
                y,
                label,
                ha="center",
                va="center",
                fontsize=8,
                color="#FFFFFF"
            )

        self.ax.set_xlabel("Temps", color="#DDDDDD")
        self.ax.set_ylabel("Machines", color="#DDDDDD")
        self.ax.set_yticks(range(1, nb_machines + 1))
        self.ax.set_yticklabels(
            [f"M{m}" for m in range(1, nb_machines + 1)],
            color="#DDDDDD"
        )

        self.ax.tick_params(axis="x", colors="#BBBBBB")
        self.ax.tick_params(axis="y", colors="#BBBBBB")

        self.ax.grid(
            True,
            axis="x",
            linestyle="--",
            linewidth=0.5,
            color="#333333",
            alpha=0.7
        )

        for spine in self.ax.spines.values():
            spine.set_color("#555555")

        self.figure.tight_layout()
        self.draw()
