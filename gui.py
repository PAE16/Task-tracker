"""Графический интерфейс приложения Task Tracker.

Содержит основное окно, диалоги и таблицу задач. Построен на PyQt5.
Классы отвечают за: диалоги создания/фильтрации, главный QMainWindow
и отрисовку таблицы + вызов аналитики.
"""
from PyQt5.QtWidgets import (
    QAction, QAbstractItemView, QButtonGroup, QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFrame, QGridLayout, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QRadioButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, QTimer, QEasingCurve, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QColor, QBrush, QPalette

from theme import apply_theme, theme_data, resolve_theme

from database import (
    get_all_tasks, get_all_projects, get_all_assignees,
    add_task, update_task, delete_task, get_analytics_data
)
from charts import (
    AssigneeLoadChart, OverdueByProjectChart, AvgTimeByPriorityChart,
    StatusDistributionChart, ClosedTasksTimelineChart, ForecastChart
)




class StyledPopupDialog(QDialog):
    """Базовый тематический попап с анимацией появления."""

    def __init__(self, title, parent=None, min_size=(520, 480)):
        super().__init__(parent)
        self.parent_window = parent
        self.setWindowTitle(title)
        self.setMinimumSize(*min_size)
        self.setModal(False)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self._open_animation = None
        self._geometry_animation = None

        self.root_layout = QVBoxLayout(self)
        self.root_layout.setSpacing(12)
        self.root_layout.setContentsMargins(14, 14, 14, 14)

        self._build_header(title)
        self.content_page = QWidget()
        self.content_page.setObjectName("dialogContent")
        self.root_layout.addWidget(self.content_page)
        self.apply_theme()

    def _current_colors(self):
        return theme_data(self.parent_window.resolved_theme)

    def _button_style(self):
        colors = self._current_colors()
        return f"""
            QPushButton {{
                background-color: {colors['surface_alt']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_soft']};
            }}
        """

    def _build_header(self, title):
        header_row = QHBoxLayout()
        header_label = QLabel(title)
        header_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        header_row.addWidget(header_label)
        header_row.addStretch()

        close_button = QPushButton("✕")
        close_button.setFixedWidth(44)
        close_button.clicked.connect(self.close)
        header_row.addWidget(close_button)

        self.root_layout.addLayout(header_row)
        self.close_button = close_button

    def apply_theme(self):
        colors = self._current_colors()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['window']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 20px;
            }}
            QLabel {{
                color: {colors['text']};
            }}
            QPushButton {{
                background-color: {colors['surface_alt']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {colors['accent_soft']};
            }}
            QPushButton#closeButton {{
                min-width: 44px;
            }}
            QLineEdit, QComboBox, QDateEdit {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 10px;
                padding: 7px 10px;
            }}
        """)
        self.close_button.setStyleSheet(self._button_style())
        self.close_button.setObjectName("closeButton")
        self.content_page.setStyleSheet(f"""
            QWidget#dialogContent {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: 16px;
            }}
            QWidget#dialogContent QLabel {{
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                color: {colors['text']};
            }}
        """)

    def present(self):
        """Показать попап с аккуратной анимацией появления."""
        self.show()
        self.raise_()
        self.activateWindow()
        self._animate_open()

    def _animate_open(self):
        base_geometry = self.geometry()
        if base_geometry.isNull():
            return

        start_geometry = QRect(base_geometry.x(), base_geometry.y() - 12, base_geometry.width(), base_geometry.height())
        self.setGeometry(start_geometry)
        self.setWindowOpacity(0.0)

        self._geometry_animation = QPropertyAnimation(self, b"geometry", self)
        self._geometry_animation.setDuration(180)
        self._geometry_animation.setEasingCurve(QEasingCurve.OutCubic)
        self._geometry_animation.setStartValue(start_geometry)
        self._geometry_animation.setEndValue(base_geometry)

        self._open_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._open_animation.setDuration(180)
        self._open_animation.setStartValue(0.0)
        self._open_animation.setEndValue(1.0)
        self._open_animation.setEasingCurve(QEasingCurve.OutCubic)

        self._geometry_animation.start()
        self._open_animation.start()


class CompactEditDialog(QDialog):
    """Компактное окно редактирования задачи (два столбца)."""

    def __init__(self, title, fields_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(380)
        self.setMaximumWidth(450)
        self.fields = {}
        self._build_ui(fields_data)

    def _build_ui(self, fields_data):
        """Создать интерфейс с двухколонным макетом."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        # Основная сетка (две колонки: название | значение)
        grid = QGridLayout()
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setSpacing(6)
        grid.setColumnMinimumWidth(0, 100)

        row = 0
        for field_name, widget in fields_data:
            label = QLabel(field_name + ":")
            label.setStyleSheet("font-weight: 600; color: #555;")
            label.setFixedWidth(90)
            grid.addWidget(label, row, 0)
            grid.addWidget(widget, row, 1)
            self.fields[field_name] = widget
            row += 1

        layout.addLayout(grid)
        layout.addSpacing(6)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        ok_btn = QPushButton("OK")
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_values(self):
        """Получить значения всех полей."""
        return {name: widget for name, widget in self.fields.items()}


class CreateTaskDialog(StyledPopupDialog):
    """Попап для создания новой задачи (компактный стиль)."""

    def __init__(self, parent=None):
        super().__init__("Новая задача", parent, min_size=(420, 320))
        self._build_content()

    def _build_content(self):
        """Компактная форма создания задачи."""
        layout = QVBoxLayout(self.content_page)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Две колонки
        grid = QGridLayout()
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setSpacing(6)
        grid.setColumnMinimumWidth(0, 90)

        # Проект
        grid.addWidget(QLabel("Проект:"), 0, 0)
        self.project_create = QComboBox()
        grid.addWidget(self.project_create, 0, 1)

        # Описание (важное поле, полная ширина)
        grid.addWidget(QLabel("Описание:"), 1, 0)
        self.description_create = QLineEdit()
        self.description_create.setPlaceholderText("Обязательно")
        grid.addWidget(self.description_create, 1, 1)

        # Исполнитель
        grid.addWidget(QLabel("Исполнитель:"), 2, 0)
        self.assignee_create = QLineEdit()
        self.assignee_create.setPlaceholderText("Обязательно")
        grid.addWidget(self.assignee_create, 2, 1)

        # Приоритет
        grid.addWidget(QLabel("Приоритет:"), 3, 0)
        self.priority_create = QComboBox()
        self.priority_create.addItems(["Low", "Medium", "High", "Critical"])
        grid.addWidget(self.priority_create, 3, 1)

        # Статус
        grid.addWidget(QLabel("Статус:"), 4, 0)
        self.status_create = QComboBox()
        self.status_create.addItems(["To Do", "In Progress", "Done"])
        grid.addWidget(self.status_create, 4, 1)

        # Дедлайн
        grid.addWidget(QLabel("Дедлайн:"), 5, 0)
        self.deadline_create = QDateEdit()
        self.deadline_create.setCalendarPopup(True)
        self.deadline_create.setDate(QDate.currentDate().addDays(7))
        grid.addWidget(self.deadline_create, 5, 1)

        layout.addLayout(grid)
        layout.addSpacing(4)

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        create_button = QPushButton("Создать")
        create_button.setMinimumWidth(100)
        create_button.clicked.connect(self._create_task)
        btn_layout.addStretch()
        btn_layout.addWidget(create_button)
        layout.addLayout(btn_layout)

    def refresh_sources(self):
        """Обновить список проектов."""
        parent = self.parent_window
        self.project_create.clear()
        for project in parent.projects:
            self.project_create.addItem(project["name"], project["id"])
        self.status_create.setCurrentIndex(0)

    def _create_task(self):
        """Сохранить новую задачу."""
        parent = self.parent_window
        project_id = self.project_create.currentData()
        description = self.description_create.text().strip()
        assignee = self.assignee_create.text().strip()
        priority = self.priority_create.currentText()
        status = self.status_create.currentText()
        deadline = self.deadline_create.date().toString("yyyy-MM-dd")

        if not description or not assignee:
            QMessageBox.warning(self, "Ошибка", "Заполните описание и исполнителя!")
            return

        parent.create_task_from_values(project_id, description, assignee, priority, status, deadline)
        self.description_create.clear()
        self.assignee_create.clear()


class FilterDialog(StyledPopupDialog):
    """Попап для фильтрации задач."""

    def __init__(self, parent=None):
        super().__init__("Фильтрация задач", parent, min_size=(520, 480))
        self._build_content()

    def _build_content(self):
        layout = QVBoxLayout(self.content_page)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        self.filter_search = QLineEdit()
        self.filter_search.setPlaceholderText("Описание или исполнитель")
        self.assignee_filter = QComboBox()
        self.assignee_filter.addItem("Все")
        self.filter_status = QComboBox()
        self.filter_status.addItems(["Все", "To Do", "In Progress", "Done"])
        self.filter_priority = QComboBox()
        self.filter_priority.addItems(["Все", "Low", "Medium", "High", "Critical"])
        self.project_filter = QComboBox()
        self.project_filter.addItem("Все")

        fields = [
            ("Поиск", self.filter_search),
            ("Исполнитель", self.assignee_filter),
            ("Статус", self.filter_status),
            ("Приоритет", self.filter_priority),
            ("Проект", self.project_filter),
        ]

        for label_text, widget in fields:
            layout.addWidget(QLabel(label_text))
            layout.addWidget(widget)

        buttons_row = QHBoxLayout()
        apply_button = QPushButton("Применить")
        apply_button.clicked.connect(self._apply_filters)
        buttons_row.addWidget(apply_button)

        reset_button = QPushButton("Сбросить")
        reset_button.clicked.connect(self._reset_filters)
        buttons_row.addWidget(reset_button)
        buttons_row.addStretch()
        layout.addLayout(buttons_row)
        layout.addStretch()

    def refresh_sources(self):
        parent = self.parent_window
        filters = dict(getattr(parent, "current_filters", {}))

        self.project_filter.clear()
        self.project_filter.addItem("Все")
        for project in parent.projects:
            self.project_filter.addItem(project["name"], project["id"])

        self.assignee_filter.clear()
        self.assignee_filter.addItem("Все")
        self.assignee_filter.addItems(parent.assignees)

        self.filter_search.setText(filters.get("search", ""))
        self.filter_status.setCurrentIndex(0)
        self.filter_priority.setCurrentIndex(0)
        self.project_filter.setCurrentIndex(0)
        self.assignee_filter.setCurrentIndex(0)

        if "status" in filters:
            index = self.filter_status.findText(filters["status"])
            if index >= 0:
                self.filter_status.setCurrentIndex(index)
        if "priority" in filters:
            index = self.filter_priority.findText(filters["priority"])
            if index >= 0:
                self.filter_priority.setCurrentIndex(index)
        if "assignee" in filters:
            index = self.assignee_filter.findText(filters["assignee"])
            if index >= 0:
                self.assignee_filter.setCurrentIndex(index)
        if "project_id" in filters:
            index = self.project_filter.findData(filters["project_id"])
            if index >= 0:
                self.project_filter.setCurrentIndex(index)

    def _apply_filters(self):
        parent = self.parent_window
        filters = {}
        search_text = self.filter_search.text().strip()
        if search_text:
            filters["search"] = search_text
        if self.assignee_filter.currentIndex() > 0:
            filters["assignee"] = self.assignee_filter.currentText()
        if self.filter_status.currentIndex() > 0:
            filters["status"] = self.filter_status.currentText()
        if self.filter_priority.currentIndex() > 0:
            filters["priority"] = self.filter_priority.currentText()
        if self.project_filter.currentIndex() > 0:
            filters["project_id"] = self.project_filter.currentData()
        parent.apply_filters(filters)

    def _reset_filters(self):
        self.filter_search.clear()
        self.assignee_filter.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)
        self.filter_priority.setCurrentIndex(0)
        self.project_filter.setCurrentIndex(0)
        self.parent_window.apply_filters({})


class AnalyticsPopupDialog(StyledPopupDialog):
    """Окно аналитики и отчётов."""

    def __init__(self, parent=None):
        super().__init__("Аналитика и отчёты", parent, min_size=(720, 560))
        self._build_content()

    def _build_content(self):
        layout = QVBoxLayout(self.content_page)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        grid = QGridLayout()
        grid.setSpacing(10)
        analytics_buttons = [
            ("Загруженность\nисполнителей", self.parent_window.show_assignee_load),
            ("Просроченные\nпо проектам", self.parent_window.show_overdue_by_project),
            ("Среднее время\nпо приоритетам", self.parent_window.show_avg_time_by_priority),
            ("Распределение\nпо статусам", self.parent_window.show_status_distribution),
            ("Закрытые задачи\nпо времени", self.parent_window.show_closed_timeline),
            ("Прогноз на\n2 недели", self.parent_window.show_forecast),
        ]
        for index, (text, handler) in enumerate(analytics_buttons):
            button = QPushButton(text)
            button.setMinimumHeight(60)
            button.clicked.connect(handler)
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()

class TaskTrackerApp(QMainWindow):
    """Главное окно приложения Task Tracker."""

    def __init__(self, app, settings):
        super().__init__()
        self.app = app
        self.settings = settings
        self.theme_mode = str(self.settings.value("appearance/theme", "light"))  # Светлая тема по умолчанию
        self.resolved_theme = resolve_theme(self.theme_mode)

        self.setWindowTitle("Task Tracker")
        self.setMinimumSize(1200, 800)  # Минимальный размер адаптивен
        self.resize(1600, 1000)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(14, 12, 14, 12)

        # Инициализация атрибутов
        self.tasks = []
        self.projects = []
        self.assignees = []
        self.current_filters = {}

        self._build_header()
        self.create_dialog = CreateTaskDialog(self)
        self.filter_dialog = FilterDialog(self)
        self.analytics_popup = AnalyticsPopupDialog(self)
        self._build_task_table()

        self.statusBar().showMessage("Готово")
        self.refresh_data()

    def _build_header(self):
        """Заголовок приложения (компактный и адаптивный)."""
        header = QFrame()
        header.setObjectName("headerCard")
        header.setMinimumHeight(64)
        header.setMaximumHeight(80)
        shadow = QGraphicsDropShadowEffect(header)
        shadow.setBlurRadius(6)
        shadow.setOffset(0, 1)
        shadow.setColor(QColor(0, 0, 0, 15))
        header.setGraphicsEffect(shadow)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 10, 12, 10)
        header_layout.setSpacing(12)

        title = QLabel("Task Tracker")
        title.setObjectName("heroTitle")
        title.setFont(QFont(self.font().family(), 14, QFont.Bold))
        title.setMinimumWidth(120)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Кнопки действий (без переключения темы)
        self.create_btn = QPushButton("Create")
        self.create_btn.setProperty("variant", "primary")
        self.create_btn.setMinimumWidth(80)
        self.create_btn.clicked.connect(lambda: self.show_controls_section(0))
        header_layout.addWidget(self.create_btn)

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setProperty("variant", "secondary")
        self.filter_btn.setMinimumWidth(80)
        self.filter_btn.clicked.connect(lambda: self.show_controls_section(1))
        header_layout.addWidget(self.filter_btn)

        self.analytics_btn = QPushButton("Insights")
        self.analytics_btn.setProperty("variant", "secondary")
        self.analytics_btn.setMinimumWidth(80)
        self.analytics_btn.clicked.connect(lambda: self.show_controls_section(2))
        header_layout.addWidget(self.analytics_btn)

        header_layout.addSpacing(12)

        # Кнопки действий над таблицей
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setProperty("variant", "secondary")
        self.edit_btn.setMinimumWidth(80)
        self.edit_btn.clicked.connect(self.edit_selected_task)
        header_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setProperty("variant", "secondary")
        self.delete_btn.setMinimumWidth(80)
        self.delete_btn.clicked.connect(self.delete_selected_task)
        header_layout.addWidget(self.delete_btn)

        self.main_layout.addWidget(header)

    def _current_colors(self):
        """Возвращает цвета для текущей темы."""
        return theme_data(self.resolved_theme)

    def _button_style(self, variant="soft"):
        """Генерирует стили для кнопок в теме."""
        colors = self._current_colors()
        if variant == "primary":
            background = colors["accent"]
            hover = colors["accent_hover"]
            border = colors["accent"]
            text = colors["selection_text"]
        elif variant == "danger":
            background = colors["chart_red"]
            hover = colors["chart_red"]
            border = colors["chart_red"]
            text = colors["selection_text"]
        elif variant == "success":
            background = colors["chart_green"]
            hover = colors["chart_green"]
            border = colors["chart_green"]
            text = colors["selection_text"]
        else:
            background = colors["surface_alt"]
            hover = colors["accent_soft"]
            border = colors["border"]
            text = colors["text"]

        return f"""
            QPushButton {{
                background-color: {background};
                color: {text};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {colors['selection']};
            }}
        """


    def show_controls_section(self, index):
        """Открывает запрошенный всплывающий диалог."""
        if index == 0:
            self.create_dialog.refresh_sources()
            self.create_dialog.present()
        elif index == 1:
            self.filter_dialog.refresh_sources()
            self.filter_dialog.present()
        else:
            self.analytics_popup.present()

    def create_task_from_values(self, project_id, description, assignee, priority, status, deadline):
        """Создаёт задачу и обновляет видимые данные."""
        add_task(project_id, description, assignee, priority, status, deadline)
        QMessageBox.information(self, "Успех", "Задача добавлена!")
        self.refresh_data()

    def _build_task_table(self):
        """Таблица задач с более плотной и современной визуальной подачей."""
        colors = self._current_colors()
        self.task_group = QGroupBox("Список задач")
        self.task_group.setStyleSheet(f"""
            QGroupBox {{
                background-color: {colors['surface']};
                color: {colors['text']};
                border: 1px solid {colors['border']};
                border-radius: 16px;
                margin-top: 12px;
                padding-top: 14px;
                font-weight: 600;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
                color: {colors['accent']};
            }}
        """)
        self.task_group.setObjectName("dashboardCard")
        shadow = QGraphicsDropShadowEffect(self.task_group)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 24))
        self.task_group.setGraphicsEffect(shadow)
        layout = QVBoxLayout()

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(9)
        self.task_table.setHorizontalHeaderLabels([
            "ID", "Проект", "Описание", "Исполнитель", "Приоритет",
            "Статус", "Создано", "Дедлайн", "Завершено"
        ])
        header = self.task_table.horizontalHeader()
        # Включить интерактивное изменение размеров колонок
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # ID
        header.setSectionResizeMode(1, QHeaderView.Interactive)  # Проект
        header.setSectionResizeMode(2, QHeaderView.Stretch)      # Описание
        header.setSectionResizeMode(3, QHeaderView.Stretch)      # Исполнитель
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # Приоритет
        header.setSectionResizeMode(5, QHeaderView.Interactive)  # Статус
        header.setSectionResizeMode(6, QHeaderView.Interactive)  # Создано
        header.setSectionResizeMode(7, QHeaderView.Interactive)  # Дедлайн
        header.setSectionResizeMode(8, QHeaderView.Interactive)  # Завершено
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setStretchLastSection(False)
        header.setCascadingSectionResizes(True)
        # Подключить сортировку при клике на заголовок
        header.sectionClicked.connect(self.sort_table_by_column)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.verticalHeader().setDefaultSectionSize(34)
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setSelectionMode(QTableWidget.SingleSelection)
        self.task_table.setAlternatingRowColors(True)
        self.task_table.setShowGrid(False)
        self.task_table.setWordWrap(False)
        self.task_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.task_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.task_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.task_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['surface']};
                alternate-background-color: {colors['surface_alt']};
                border: 1px solid {colors['border']};
                gridline-color: {colors['border']};
                font-size: 12px;
                color: {colors['text']};
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {colors['selection']};
                color: {colors['selection_text']};
            }}
            QHeaderView::section {{
                background-color: {colors['surface_alt']};
                color: {colors['text']};
                padding: 5px 8px;
                font-weight: 700;
                border: none;
                border-bottom: 1px solid {colors['border']};
            }}
        """)
        self.task_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.task_table.doubleClicked.connect(self.on_cell_double_clicked)
        
        # Инициализировать переменные для сортировки
        self.sort_column = None
        self.sort_ascending = True

        layout.addWidget(self.task_table)

        self.task_group.setLayout(layout)
        self.main_layout.addWidget(self.task_group, stretch=1)


    def refresh_data(self):
        """Обновить все данные в интерфейсе."""
        self.projects = get_all_projects()
        self.assignees = get_all_assignees()

        self.create_dialog.refresh_sources()
        self.filter_dialog.refresh_sources()

        self.apply_filters(self.current_filters)

    def apply_filters(self, filters=None):
        """Применить фильтры к таблице задач."""
        if filters is not None:
            self.current_filters = dict(filters)

        self.tasks = get_all_tasks(self.current_filters)
        self.populate_table()

    def reset_filters(self):
        """Сбросить все фильтры."""
        self.current_filters = {}
        if hasattr(self, "filter_dialog"):
            self.filter_dialog._reset_filters()
        else:
            self.apply_filters({})

    def populate_table(self):
        """Заполнить таблицу задачами."""
        colors = self._current_colors()
        self.task_table.setRowCount(len(self.tasks))
        self.task_table.setAlternatingRowColors(True)

        priority_colors = {
            "Low": QColor(colors["chart_green"]),
            "Medium": QColor(colors["chart_orange"]),
            "High": QColor(colors["chart_purple"]),
            "Critical": QColor(colors["chart_red"]),
        }

        status_colors = {
            "To Do": QColor(colors["chart_blue"]),
            "In Progress": QColor(colors["chart_orange"]),
            "Done": QColor(colors["chart_green"]),
        }

        def make_badge_widget(text, background_color):
            bg = background_color if isinstance(background_color, QColor) else QColor(background_color)
            text_color = "#ffffff" if bg.lightness() < 150 else colors["text"]

            wrapper = QWidget()
            wrapper.setStyleSheet("background: transparent;")
            wrapper_layout = QHBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(6, 3, 6, 3)
            wrapper_layout.setSpacing(0)

            badge = QLabel(text)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg.name()};
                    color: {text_color};
                    border-radius: 999px;
                    padding: 4px 10px;
                    font-size: 10px;
                    font-weight: 700;
                }}
            """)
            wrapper_layout.addStretch(1)
            wrapper_layout.addWidget(badge, 0, Qt.AlignCenter)
            wrapper_layout.addStretch(1)
            return wrapper

        for row_idx, task in enumerate(self.tasks):
            item = QTableWidgetItem(str(task["id"]))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.task_table.setItem(row_idx, 0, item)

            item = QTableWidgetItem(task["project_name"])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self.task_table.setItem(row_idx, 1, item)

            item = QTableWidgetItem(task["description"])
            self.task_table.setItem(row_idx, 2, item)

            item = QTableWidgetItem(task["assignee"])
            self.task_table.setItem(row_idx, 3, item)

            self.task_table.setCellWidget(
                row_idx,
                4,
                make_badge_widget(task["priority"], priority_colors.get(task["priority"], colors["surface_alt"])),
            )
            self.task_table.setCellWidget(
                row_idx,
                5,
                make_badge_widget(task["status"], status_colors.get(task["status"], colors["surface_alt"])),
            )

            item = QTableWidgetItem(task["created_at"])
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.task_table.setItem(row_idx, 6, item)

            item = QTableWidgetItem(task["deadline"] or "")
            item.setTextAlignment(Qt.AlignCenter)
            self.task_table.setItem(row_idx, 7, item)

            item = QTableWidgetItem(task["completed_at"] or "")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignCenter)
            self.task_table.setItem(row_idx, 8, item)

    def sort_table_by_column(self, column):
        """Сортировать таблицу по выбранной колонке.
        
        При клике на ту же колонку - меняется направление сортировки (возрастание/убывание).
        """
        # Определить направление сортировки
        if self.sort_column == column:
            # Если кликаем на ту же колонку - переключаем направление
            self.sort_ascending = not self.sort_ascending
        else:
            # Новая колонка - сортируем по возрастанию
            self.sort_ascending = True
            self.sort_column = column
        
        # Словарь соответствия индексов колонок ключам в словаре задачи
        column_keys = {
            0: "id",
            1: "project_name",
            2: "description",
            3: "assignee",
            4: "priority",
            5: "status",
            6: "created_at",
            7: "deadline",
            8: "completed_at",
        }
        
        if column >= len(column_keys) or column_keys[column] is None:
            return
        
        sort_key = column_keys[column]
        
        # Специальная сортировка для приоритетов
        if sort_key == "priority":
            priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
            self.tasks.sort(
                key=lambda t: priority_order.get(t.get(sort_key, ""), 999),
                reverse=not self.sort_ascending
            )
        # Специальная сортировка для статусов
        elif sort_key == "status":
            status_order = {"Done": 0, "In Progress": 1, "To Do": 2}
            self.tasks.sort(
                key=lambda t: status_order.get(t.get(sort_key, ""), 999),
                reverse=not self.sort_ascending
            )
        # Обычная сортировка для остальных
        else:
            self.tasks.sort(
                key=lambda t: str(t.get(sort_key, "")).lower(),
                reverse=not self.sort_ascending
            )
        
        # Перерисовать таблицу
        self.populate_table()

    def on_cell_double_clicked(self, index):
        """Обработка двойного клика для открытия полного редактора задачи."""
        row = index.row()
        
        if row < 0 or row >= len(self.tasks):
            return
        
        task_id = self.tasks[row]["id"]
        self._open_full_edit_dialog(task_id)

    def _open_full_edit_dialog(self, task_id):
        """Открыть полный диалог редактирования задачи."""
        # Найти задачу по ID
        task = None
        for t in self.tasks:
            if t["id"] == task_id:
                task = t
                break
        
        if not task:
            QMessageBox.warning(self, "Ошибка", "Задача не найдена!")
            return
        
        # Создать поля для редактирования
        # Проект
        project_combo = QComboBox()
        for project in self.projects:
            project_combo.addItem(project["name"], project["id"])
            if project["id"] == task.get("project_id"):
                project_combo.setCurrentIndex(project_combo.count() - 1)
        
        # Описание
        description_edit = QLineEdit()
        description_edit.setText(task.get("description", ""))
        
        # Исполнитель
        assignee_edit = QLineEdit()
        assignee_edit.setText(task.get("assignee", ""))
        
        # Приоритет
        priority_combo = QComboBox()
        priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        priority_combo.setCurrentText(task.get("priority", "Low"))
        
        # Статус
        status_combo = QComboBox()
        status_combo.addItems(["To Do", "In Progress", "Done"])
        status_combo.setCurrentText(task.get("status", "To Do"))
        
        # Дедлайн
        deadline_edit = QDateEdit()
        deadline_edit.setCalendarPopup(True)
        if task.get("deadline"):
            deadline_edit.setDate(QDate.fromString(task["deadline"], "yyyy-MM-dd"))
        else:
            deadline_edit.setDate(QDate.currentDate().addDays(7))
        
        # Создать диалог
        fields_data = [
            ("Проект", project_combo),
            ("Описание", description_edit),
            ("Исполнитель", assignee_edit),
            ("Приоритет", priority_combo),
            ("Статус", status_combo),
            ("Дедлайн", deadline_edit),
        ]
        
        dialog = CompactEditDialog(f"Редактирование задачи #{task_id}", fields_data, self)
        
        if dialog.exec_() == QDialog.Accepted:
            # Сохранить изменения
            updates = {
                "project_id": project_combo.currentData(),
                "description": description_edit.text(),
                "assignee": assignee_edit.text(),
                "priority": priority_combo.currentText(),
                "status": status_combo.currentText(),
                "deadline": deadline_edit.date().toString("yyyy-MM-dd"),
            }
            
            # Проверить что обязательные поля заполнены
            if not updates["description"].strip() or not updates["assignee"].strip():
                QMessageBox.warning(self, "Ошибка", "Описание и исполнитель обязательны!")
                return
            
            # Применить обновления
            for field, value in updates.items():
                update_task(task_id, field, value)
            
            QMessageBox.information(self, "Успех", "Задача обновлена!")
            self.apply_filters()

    def add_new_task(self):
        """Открывает попап создания задачи."""
        self.show_controls_section(0)

    def _mark_task_complete(self, task_id):
        """Отметить задачу как завершённую."""
        update_task(task_id, "status", "Done")
        self.apply_filters()

    def _open_edit_dialog(self, row_idx):
        """Открыть компактный диалог редактирования задачи."""
        if row_idx < 0 or row_idx >= len(self.tasks):
            return
        
        task = self.tasks[row_idx]
        task_id = task["id"]
        
        # Создаём виджеты
        project_combo = QComboBox()
        for project in self.projects:
            project_combo.addItem(project["name"], project["id"])
        project_combo.setCurrentIndex(project_combo.findData(task["project_id"]))
        
        desc_edit = QLineEdit(task["description"])
        assignee_edit = QLineEdit(task["assignee"])
        
        priority_combo = QComboBox()
        priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        priority_combo.setCurrentText(task["priority"])
        
        status_combo = QComboBox()
        status_combo.addItems(["To Do", "In Progress", "Done"])
        status_combo.setCurrentText(task["status"])
        
        deadline_edit = QDateEdit()
        deadline_edit.setCalendarPopup(True)
        if task["deadline"]:
            deadline_edit.setDate(QDate.fromString(task["deadline"], "yyyy-MM-dd"))
        
        # Создаём компактный диалог
        fields = [
            ("Проект", project_combo),
            ("Описание", desc_edit),
            ("Исполнитель", assignee_edit),
            ("Приоритет", priority_combo),
            ("Статус", status_combo),
            ("Дедлайн", deadline_edit),
        ]
        
        dialog = CompactEditDialog(f"Редактировать задачу #{task_id}", fields, self)
        
        if dialog.exec_() == QDialog.Accepted:
            # Сохранить изменения
            update_task(task_id, "project_id", project_combo.currentData())
            update_task(task_id, "description", desc_edit.text())
            update_task(task_id, "assignee", assignee_edit.text())
            update_task(task_id, "priority", priority_combo.currentText())
            update_task(task_id, "status", status_combo.currentText())
            update_task(task_id, "deadline", deadline_edit.date().toString("yyyy-MM-dd"))
            self.apply_filters()

    def delete_selected_task(self):
        """Удалить выбранную задачу."""
        selected = self.task_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите задачу для удаления!")
            return

        row = selected[0].row()
        task_id = self.tasks[row]["id"]
        self.delete_task_by_id(task_id)

    def edit_selected_task(self):
        """Редактировать выбранную задачу."""
        selected = self.task_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Внимание", "Выберите задачу для редактирования!")
            return

        row = selected[0].row()
        task_id = self.tasks[row]["id"]
        self._open_full_edit_dialog(task_id)

    def delete_task_by_id(self, task_id):
        """Удалить задачу по ID."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Подтверждение")
        msg_box.setText(f"Удалить задачу #{task_id}?")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        # Применить палитру для правильного отображения иконки в тёмной теме
        colors = self._current_colors()
        palette = msg_box.palette()
        palette.setColor(QPalette.WindowText, QColor(colors['text']))
        palette.setColor(QPalette.Window, QColor(colors['window']))
        palette.setColor(QPalette.ButtonText, QColor(colors['text']))
        msg_box.setPalette(palette)
        
        reply = msg_box.exec_()
        if reply == QMessageBox.Yes:
            delete_task(task_id)
            self.apply_filters()

    # === Аналитика ===

    def show_assignee_load(self):
        """Показать график загруженности исполнителей."""
        data = get_analytics_data()["assignee_load"]
        chart = AssigneeLoadChart(data, self)
        chart.exec_()

    def show_overdue_by_project(self):
        """Показать график просроченных задач по проектам."""
        data = get_analytics_data()["overdue_by_project"]
        chart = OverdueByProjectChart(data, self)
        chart.exec_()

    def show_avg_time_by_priority(self):
        """Показать график среднего времени выполнения по приоритетам."""
        data = get_analytics_data()["avg_time_by_priority"]
        chart = AvgTimeByPriorityChart(data, self)
        chart.exec_()

    def show_status_distribution(self):
        """Показать круговую диаграмму распределения по статусам."""
        data = get_analytics_data()["status_distribution"]
        chart = StatusDistributionChart(data, self)
        chart.exec_()

    def show_closed_timeline(self):
        """Показать график закрытых задач по времени."""
        data = get_analytics_data()
        chart = ClosedTasksTimelineChart(data["closed_by_week"], data["closed_by_month"], self)
        chart.exec_()

    def show_forecast(self):
        """Показать прогноз выполнения задач на 2 недели."""
        data = get_analytics_data()
        chart = ForecastChart(data["closed_by_week"], self)
        chart.exec_()
