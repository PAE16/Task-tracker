
"""Модуль для создания графиков и диаграмм.

Содержит окна с Matplotlib для визуализации аналитики.
Каждый класс строит диалог с канвой (FigureCanvas) для интеграции в Qt.
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from theme import theme_data, get_active_theme_mode


def _apply_axis_theme(ax, colors):
    """Применяет тему приложения к оси Matplotlib."""
    # Применяет цвета осей и сетки в соответствии с темой приложения (светлая/тёмная).
    ax.set_facecolor(colors["chart_axes"])
    ax.figure.set_facecolor(colors["chart_bg"])
    ax.tick_params(colors=colors["chart_text"])
    ax.xaxis.label.set_color(colors["chart_text"])
    ax.yaxis.label.set_color(colors["chart_text"])
    ax.title.set_color(colors["chart_text"])
    for spine in ax.spines.values():
        spine.set_color(colors["border"])
    ax.grid(True, color=colors["chart_grid"], alpha=0.6, linestyle="--", linewidth=0.8)
    ax.set_axisbelow(True)


class ChartWindow(QDialog):
    """Базовое окно для отображения графиков."""
    # Небольшая обёртка: создаёт `Figure` и `FigureCanvas`, настраивает стиль.
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        self.setWindowFlags(self.windowFlags() | Qt.Window)

        colors = theme_data(get_active_theme_mode())
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['chart_bg']};
                color: {colors['chart_text']};
            }}
            QLabel {{
                color: {colors['chart_text']};
            }}
            QPushButton {{
                color: {colors['chart_text']};
                padding: 6px 12px;
                background-color: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_soft']};
            }}
        """)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.figure.set_facecolor(colors["chart_bg"])
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


class AssigneeLoadChart(ChartWindow):
    """Гистограмма загруженности исполнителей."""

    def __init__(self, data, parent=None):
        super().__init__("Загруженность исполнителей", parent)
        ax = self.figure.add_subplot(111)
        colors = theme_data(get_active_theme_mode())
        _apply_axis_theme(ax, colors)

        names = [d[0] for d in data]
        counts = [d[1] for d in data]

        bars = ax.barh(names, counts, color=colors["chart_blue"])
        ax.set_xlabel("Количество задач")
        ax.set_title("Количество задач на исполнителя")
        ax.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(count), va="center", fontsize=9, color=colors["chart_text"])

        self.figure.tight_layout()
        self.canvas.draw()


class OverdueByProjectChart(ChartWindow):
    """Гистограмма просроченных задач по проектам."""

    def __init__(self, data, parent=None):
        super().__init__("Просроченные задачи по проектам", parent)
        ax = self.figure.add_subplot(111)
        colors = theme_data(get_active_theme_mode())
        _apply_axis_theme(ax, colors)

        if not data:
            ax.text(0.5, 0.5, "Нет просроченных задач", ha="center", va="center", fontsize=14,
                    color=colors["chart_text"])
            self.canvas.draw()
            return

        names = [d[0] for d in data]
        counts = [d[1] for d in data]

        bars = ax.barh(names, counts, color=colors["chart_red"] )
        ax.set_xlabel("Количество просроченных задач")
        ax.set_title("Просроченные задачи по проектам")
        ax.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(count), va="center", fontsize=9, color=colors["chart_text"])

        self.figure.tight_layout()
        self.canvas.draw()


class AvgTimeByPriorityChart(ChartWindow):
    """Гистограмма среднего времени выполнения по приоритетам."""

    def __init__(self, data, parent=None):
        super().__init__("Среднее время выполнения по приоритетам", parent)
        ax = self.figure.add_subplot(111)
        colors = theme_data(get_active_theme_mode())
        _apply_axis_theme(ax, colors)

        if not data:
            ax.text(0.5, 0.5, "Нет данных о завершённых задачах", ha="center", va="center", fontsize=14,
                    color=colors["chart_text"])
            self.canvas.draw()
            return

        priorities = [d[0] for d in data]
        avg_days = [round(d[1], 1) if d[1] else 0 for d in data]

        priority_colors = {"Low": colors["chart_green"], "Medium": colors["chart_orange"], "High": colors["chart_purple"], "Critical": colors["chart_red"]}
        bar_colors = [priority_colors.get(p, colors["chart_blue"]) for p in priorities]

        bars = ax.bar(priorities, avg_days, color=bar_colors)
        ax.set_ylabel("Среднее количество дней")
        ax.set_title("Среднее время выполнения задачи по приоритету")

        for bar, days in zip(bars, avg_days):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f"{days} дн.", ha="center", fontsize=10, color=colors["chart_text"])

        self.figure.tight_layout()
        self.canvas.draw()


class StatusDistributionChart(ChartWindow):
    """Круговая диаграмма распределения задач по статусам."""

    def __init__(self, data, parent=None):
        super().__init__("Распределение задач по статусам", parent)
        ax = self.figure.add_subplot(111)
        colors = theme_data(get_active_theme_mode())
        _apply_axis_theme(ax, colors)

        labels = [d[0] for d in data]
        sizes = [d[1] for d in data]

        status_colors = {"To Do": colors["chart_muted"], "In Progress": colors["chart_blue"], "Done": colors["chart_green"]}
        pie_colors = [status_colors.get(l, colors["chart_purple"]) for l in labels]

        explode = [0.05 if l == "Done" else 0 for l in labels]

        ax.pie(
            sizes, labels=labels, autopct="%1.1f%%", startangle=90,
            colors=pie_colors, explode=explode, shadow=True,
            textprops={"color": colors["chart_text"]}
        )
        ax.set_title("Распределение задач по статусам")

        self.figure.tight_layout()
        self.canvas.draw()


class ClosedTasksTimelineChart(ChartWindow):
    """График закрытых задач по времени (недели/месяцы) с прогнозом."""

    def __init__(self, week_data, month_data, parent=None):
        super().__init__("Закрытые задачи по времени", parent)

        # Добавляем переключатель недели/месяцы
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Период:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["По неделям", "По месяцам"])
        self.period_combo.currentIndexChanged.connect(self.update_chart)
        top_layout.addWidget(self.period_combo)
        top_layout.addStretch()

        self.layout().insertLayout(0, top_layout)

        self.week_data = week_data
        self.month_data = month_data
        self.update_chart()

    def update_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        colors = theme_data(get_active_theme_mode())
        _apply_axis_theme(ax, colors)

        if self.period_combo.currentIndex() == 0:
            data = self.week_data
            title = "Закрытые задачи по неделям"
            xlabel = "Неделя"
        else:
            data = self.month_data
            title = "Закрытые задачи по месяцам"
            xlabel = "Месяц"

        if not data:
            ax.text(0.5, 0.5, "Нет данных о закрытых задачах", ha="center", va="center", fontsize=14,
                    color=colors["chart_text"])
            self.canvas.draw()
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        ax.plot(labels, values, marker="o", linewidth=2, markersize=6, color=colors["chart_blue"], label="Фактические данные")
        ax.fill_between(range(len(labels)), values, alpha=0.25, color=colors["chart_blue"])

        # Прогноз
        if len(values) >= 2:
            forecast_x, forecast_y = self._calculate_forecast(values)
            if forecast_x:
                all_x = list(range(len(labels))) + forecast_x
                ax.plot(all_x[-len(forecast_x):], forecast_y, marker="s", linewidth=2,
                        markersize=6, color=colors["chart_red"], linestyle="--", label="Прогноз")
                for fx, fy in zip(forecast_x, forecast_y):
                    ax.scatter(fx, fy, color=colors["chart_red"], s=80, zorder=5)
                    ax.annotate(f"{fy:.0f}", (fx, fy), textcoords="offset points",
                                xytext=(0, 10), ha="center", fontsize=9, color=colors["chart_red"])

        ax.set_xlabel(xlabel)
        ax.set_ylabel("Количество закрытых задач")
        ax.set_title(title)
        legend = ax.legend(facecolor=colors["chart_bg"], edgecolor=colors["border"])
        for text in legend.get_texts():
            text.set_color(colors["chart_text"])

        # Поворот меток оси X
        if len(labels) > 6:
            ax.tick_params(axis="x", rotation=45)

        self.figure.tight_layout()
        self.canvas.draw()

    def _calculate_forecast(self, values):
        """Простая линейная регрессия для прогноза."""
        n = len(values)
        if n < 2:
            return [], []

        x = np.array(range(n))
        y = np.array(values, dtype=float)

        # Линейная регрессия
        slope, intercept = np.polyfit(x, y, 1)

        # Прогноз на 2 периода вперёд
        forecast_x = [n, n + 1]
        forecast_y = [max(0, slope * fx + intercept) for fx in forecast_x]

        return forecast_x, forecast_y


class ForecastChart(ChartWindow):
    """Окно с детальным прогнозом выполнения задач."""

    def __init__(self, week_data, parent=None):
        super().__init__("Прогноз выполнения задач", parent)
        ax = self.figure.add_subplot(111)
        colors = theme_data(get_active_theme_mode())
        _apply_axis_theme(ax, colors)

        if len(week_data) < 2:
            ax.text(0.5, 0.5, "Недостаточно данных для прогноза", ha="center", va="center", fontsize=14,
                    color=colors["chart_text"])
            self.canvas.draw()
            return

        labels = [d[0] for d in week_data]
        values = [d[1] for d in week_data]
        n = len(values)

        x = np.array(range(n))
        y = np.array(values, dtype=float)

        # Линейная регрессия
        slope, intercept = np.polyfit(x, y, 1)

        # Прогноз на 2 недели
        forecast_x = [n, n + 1]
        forecast_y = [max(0, slope * fx + intercept) for fx in forecast_x]

        # Линия тренда
        trend_x = np.linspace(0, n + 1, 100)
        trend_y = slope * trend_x + intercept

        ax.plot(range(n), values, marker="o", linewidth=2, markersize=8,
                color=colors["chart_blue"], label="Исторические данные")
        ax.plot(trend_x, trend_y, color=colors["chart_purple"], linestyle="-", alpha=0.7, label="Тренд")
        ax.plot(forecast_x, forecast_y, marker="s", linewidth=2, markersize=8,
                color=colors["chart_red"], linestyle="--", label="Прогноз (2 недели)")

        for fx, fy in zip(forecast_x, forecast_y):
            ax.scatter(fx, fy, color=colors["chart_red"], s=100, zorder=5)
            ax.annotate(f"{fy:.1f}", (fx, fy), textcoords="offset points",
                        xytext=(0, 12), ha="center", fontsize=10, color=colors["chart_red"], fontweight="bold")

        ax.set_xlabel("Неделя")
        ax.set_ylabel("Количество закрытых задач")
        ax.set_title(f"Прогноз: ~{sum(forecast_y):.0f} задач за следующие 2 недели")
        legend = ax.legend(facecolor=colors["chart_bg"], edgecolor=colors["border"])
        for text in legend.get_texts():
            text.set_color(colors["chart_text"])

        all_x = list(range(n)) + forecast_x
        all_labels = labels + ["Неделя+1", "Неделя+2"]
        ax.set_xticks(all_x)
        ax.set_xticklabels(all_labels, rotation=45 if len(labels) > 6 else 0)

        # Добавляем текстовое описание
        ax.text(0.02, 0.98,
                f"Скорость закрытия: {slope:.2f} задач/неделя\\n"
                f"Прогноз на неделю {n+1}: {forecast_y[0]:.1f}\\n"
                f"Прогноз на неделю {n+2}: {forecast_y[1]:.1f}",
                transform=ax.transAxes, fontsize=10, verticalalignment="top",
                color=colors["chart_text"],
                bbox=dict(boxstyle="round", facecolor=colors["chart_bg"], edgecolor=colors["border"], alpha=0.9))

        self.figure.tight_layout()
        self.canvas.draw()
