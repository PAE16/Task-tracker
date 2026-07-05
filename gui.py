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

from theme import apply_theme, theme_data, resolve_theme, THEME_MODES, get_active_theme_mode, detect_system_theme

from database import (
    get_all_tasks, get_all_projects, get_all_assignees,
    add_task, update_task, delete_task, get_analytics_data
)
from charts import (
    AssigneeLoadChart, OverdueByProjectChart, AvgTimeByPriorityChart,
    StatusDistributionChart, ClosedTasksTimelineChart, ForecastChart
)


class ThemeDialog(QDialog):
    """Диалог выбора режима оформления приложения."""

    def __init__(self, current_mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Тема приложения")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel("Выберите режим темы")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        layout.addWidget(title)

        hint = QLabel("Системный режим подстраивается под тему macOS или Windows.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color: {theme_data(resolve_theme(current_mode))['muted']};")
        layout.addWidget(hint)

        self.button_group = QButtonGroup(self)
        self.system_radio = QRadioButton("Как в системе")
        self.light_radio = QRadioButton("Светлая")
        self.dark_radio = QRadioButton("Тёмная")

        self.button_group.addButton(self.system_radio)
        self.button_group.addButton(self.light_radio)
        self.button_group.addButton(self.dark_radio)

        layout.addWidget(self.system_radio)
        layout.addWidget(self.light_radio)
        layout.addWidget(self.dark_radio)

        if current_mode == "dark":
            self.dark_radio.setChecked(True)
        elif current_mode == "light":
            self.light_radio.setChecked(True)
        else:
            self.system_radio.setChecked(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_mode(self):
        if self.dark_radio.isChecked():
            return "dark"
        if self.light_radio.isChecked():
            return "light"
        return "system"


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


class CreateTaskDialog(StyledPopupDialog):
    """Попап для создания новой задачи."""

    def __init__(self, parent=None):
        super().__init__("Создание задачи", parent, min_size=(520, 520))
        self._build_content()

    def _build_content(self):
        layout = QVBoxLayout(self.content_page)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QVBoxLayout()
        form.setSpacing(10)

        self.project_create = QComboBox()
        self.description_create = QLineEdit()
        self.description_create.setPlaceholderText("Описание задачи")
        self.assignee_create = QLineEdit()
        self.assignee_create.setPlaceholderText("ФИО исполнителя")
        self.priority_create = QComboBox()
        self.priority_create.addItems(["Low", "Medium", "High", "Critical"])
        self.status_create = QComboBox()
        self.status_create.addItems(["To Do", "In Progress", "Done"])
        self.deadline_create = QDateEdit()
        self.deadline_create.setCalendarPopup(True)
        self.deadline_create.setDate(QDate.currentDate().addDays(7))

        fields = [
            ("Проект", self.project_create),
            ("Описание", self.description_create),
            ("Исполнитель", self.assignee_create),
            ("Приоритет", self.priority_create),
            ("Статус", self.status_create),
            ("Дедлайн", self.deadline_create),
        ]

        for label_text, widget in fields:
            form.addWidget(QLabel(label_text))
            form.addWidget(widget)

        layout.addLayout(form)

        buttons_row = QHBoxLayout()
        create_button = QPushButton("Создать задачу")
        create_button.clicked.connect(self._create_task)
        buttons_row.addWidget(create_button)
        buttons_row.addStretch()
        layout.addLayout(buttons_row)
        layout.addStretch()

    def refresh_sources(self):
        parent = self.parent_window
        self.project_create.clear()
        for project in parent.projects:
            self.project_create.addItem(project["name"], project["id"])
        self.status_create.setCurrentIndex(0)

    def _create_task(self):
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
        self.theme_mode = str(self.settings.value("appearance/theme", "system"))
        self.resolved_theme = resolve_theme(self.theme_mode)

        self.setWindowTitle("Task Tracker")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)

        self._build_menu()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(14)
        self.main_layout.setContentsMargins(16, 16, 16, 16)

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

        self.theme_watch_timer = QTimer(self)
        self.theme_watch_timer.setInterval(5000)
        self.theme_watch_timer.timeout.connect(self._sync_system_theme)
        self.theme_watch_timer.start()

    def _build_menu(self):
        """Создать меню настроек."""
        menu = self.menuBar().addMenu("Настройки")
        theme_action = QAction("Тема приложения...", self)
        theme_action.triggered.connect(self.show_theme_dialog)
        menu.addAction(theme_action)

    def _build_header(self):
        """Заголовок приложения."""
        header = QFrame()
        header.setObjectName("headerCard")
        header.setMinimumHeight(118)
        shadow = QGraphicsDropShadowEffect(header)
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 30))
        header.setGraphicsEffect(shadow)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 20, 22, 20)
        header_layout.setSpacing(14)

        text_block = QVBoxLayout()
        text_block.setSpacing(4)

        title = QLabel("Task Tracker")
        title.setObjectName("heroTitle")
        title.setFont(QFont(self.font().family(), 22, QFont.Bold))
        text_block.addWidget(title)

        header_layout.addLayout(text_block)
        header_layout.addStretch()

        self.theme_badge = QLabel("Minimal")
        self.theme_badge.setObjectName("themeBadge")
        header_layout.addWidget(self.theme_badge, 0, Qt.AlignVCenter)

        theme_button = QPushButton("Theme")
        theme_button.setProperty("variant", "secondary")
        theme_button.clicked.connect(self.show_theme_dialog)
        header_layout.addWidget(theme_button, 0, Qt.AlignVCenter)

        self.create_btn = QPushButton("Create")
        self.create_btn.setProperty("variant", "primary")
        self.create_btn.clicked.connect(lambda: self.show_controls_section(0))
        header_layout.addWidget(self.create_btn, 0, Qt.AlignVCenter)

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setProperty("variant", "secondary")
        self.filter_btn.clicked.connect(lambda: self.show_controls_section(1))
        header_layout.addWidget(self.filter_btn, 0, Qt.AlignVCenter)

        self.analytics_btn = QPushButton("Insights")
        self.analytics_btn.setProperty("variant", "secondary")
        self.analytics_btn.clicked.connect(lambda: self.show_controls_section(2))
        header_layout.addWidget(self.analytics_btn, 0, Qt.AlignVCenter)

        self._update_theme_badge()

        self.main_layout.addWidget(header)

    def _update_theme_badge(self):
        label_map = {
            "system": "Тема: как в системе",
            "light": "Тема: светлая",
            "dark": "Тема: тёмная",
        }
        current = self.theme_mode if self.theme_mode in THEME_MODES else "system"
        self.theme_badge.setText(label_map.get(current, "Тема: как в системе"))

    def show_theme_dialog(self):
        """Открывает диалог настроек внешнего вида."""
        dialog = ThemeDialog(self.theme_mode, self)
        if dialog.exec_():
            self.apply_theme_mode(dialog.selected_mode())

    def apply_theme_mode(self, mode):
        """Применяет и сохраняет выбранный режим темы."""
        self.theme_mode = mode
        self.resolved_theme = apply_theme(self.app, mode)
        self.settings.setValue("appearance/theme", mode)
        self._refresh_section_styles()
        self._update_theme_badge()
        self.statusBar().showMessage(f"Тема: {self.theme_badge.text()}", 3000)

    def _current_colors(self):
        """Возвращает цвета для текущей темы."""
        return theme_data(self.resolved_theme)

    def _group_box_style(self, accent_color):
        """Генерирует карточный стиль для секций."""
        colors = self._current_colors()
        return f"""
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
                color: {accent_color};
            }}
        """

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

    def _refresh_section_styles(self):
        """Переустанавливает инлайн-стили после смены темы."""
        for dialog in (self.create_dialog, self.filter_dialog, self.analytics_popup):
            dialog.apply_theme()
        self._update_table_theme()

    def _sync_system_theme(self):
        """Синхронизирует UI с системной темой при режиме system."""
        if self.theme_mode != "system":
            return

        system_theme = detect_system_theme()
        if system_theme != self.resolved_theme:
            self.resolved_theme = apply_theme(self.app, "system")
            self._refresh_section_styles()
            self._update_theme_badge()
            self.statusBar().showMessage(f"Тема: {self.theme_badge.text()}", 3000)

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
        self.task_group.setStyleSheet(self._group_box_style(colors["accent"]))
        self.task_group.setObjectName("dashboardCard")
        shadow = QGraphicsDropShadowEffect(self.task_group)
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 24))
        self.task_group.setGraphicsEffect(shadow)
        layout = QVBoxLayout()

        self.task_table = QTableWidget()
        self.task_table.setColumnCount(10)
        self.task_table.setHorizontalHeaderLabels([
            "ID", "Проект", "Описание", "Исполнитель", "Приоритет",
            "Статус", "Создано", "Дедлайн", "Завершено", "Действия"
        ])
        header = self.task_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setStretchLastSection(False)
        header.setCascadingSectionResizes(True)
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

        layout.addWidget(self.task_table)

        btn_layout = QHBoxLayout()

        delete_btn = QPushButton("Удалить выбранную")
        delete_btn.setProperty("variant", "secondary")
        delete_btn.setStyleSheet(self._button_style("danger"))
        delete_btn.clicked.connect(self.delete_selected_task)
        btn_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setProperty("variant", "primary")
        refresh_btn.setStyleSheet(self._button_style("primary"))
        refresh_btn.clicked.connect(self.refresh_data)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.task_group.setLayout(layout)
        self.main_layout.addWidget(self.task_group, stretch=1)

    def _update_table_theme(self):
        """Refresh the inline table styling after a theme change."""
        if not hasattr(self, "task_table"):
            return
        colors = self._current_colors()
        
        # Обновить стиль QGroupBox
        if hasattr(self, "task_group"):
            self.task_group.setStyleSheet(self._group_box_style(colors["accent"]))
        
        # Обновить стиль таблицы
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

            edit_btn = QPushButton("Редактировать")
            edit_btn.setProperty("variant", "secondary")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['accent']};
                    color: #ffffff;
                    padding: 4px 10px;
                    border-radius: 999px;
                    font-size: 10px;
                    border: none;
                }}
                QPushButton:hover {{ background-color: {colors['accent_hover']}; }}
            """)
            edit_btn.clicked.connect(lambda checked, rid=row_idx: self._open_edit_dialog(rid))
            
            complete_btn = QPushButton("✓")
            complete_btn.setProperty("variant", "secondary")
            complete_btn.setFixedWidth(32)
            complete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['chart_green']};
                    color: #ffffff;
                    padding: 4px 6px;
                    border-radius: 999px;
                    font-size: 10px;
                    border: none;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: #059669; }}
            """)
            complete_btn.clicked.connect(lambda checked, tid=task["id"]: self._mark_task_complete(tid))
            
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            btn_layout.setSpacing(2)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(complete_btn)
            self.task_table.setCellWidget(row_idx, 9, btn_container)

        self._update_table_theme()

    def on_cell_double_clicked(self, index):
        """Обработка двойного клика для редактирования ячейки."""
        row = index.row()
        col = index.column()
        
        # Пропустить колонку действий (кнопки)
        if col == 9:
            return
        
        task_id = self.tasks[row]["id"]

        editable_cols = {2: "description", 3: "assignee", 4: "priority", 5: "status", 7: "deadline"}

        if col not in editable_cols:
            return

        field = editable_cols[col]
        
        # Получить текущее значение из ячейки
        item = self.task_table.item(row, col)
        if item is None:
            return
        
        current_text = item.text()

        if field in ("priority", "status"):
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Изменить {field}")
            layout = QVBoxLayout()
            combo = QComboBox()
            if field == "priority":
                combo.addItems(["Low", "Medium", "High", "Critical"])
            else:
                combo.addItems(["To Do", "In Progress", "Done"])
            combo.setCurrentText(current_text)
            layout.addWidget(combo)
            btn = QPushButton("Сохранить")
            btn.clicked.connect(dialog.accept)
            layout.addWidget(btn)
            dialog.setLayout(layout)
            if dialog.exec_():
                update_task(task_id, field, combo.currentText())
                self.apply_filters()
        elif field == "deadline":
            dialog = QDialog(self)
            dialog.setWindowTitle("Изменить дедлайн")
            layout = QVBoxLayout()
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            if current_text:
                date_edit.setDate(QDate.fromString(current_text, "yyyy-MM-dd"))
            else:
                date_edit.setDate(QDate.currentDate())
            layout.addWidget(date_edit)
            btn = QPushButton("Сохранить")
            btn.clicked.connect(dialog.accept)
            layout.addWidget(btn)
            dialog.setLayout(layout)
            if dialog.exec_():
                update_task(task_id, field, date_edit.date().toString("yyyy-MM-dd"))
                self.apply_filters()
        else:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Изменить {field}")
            layout = QVBoxLayout()
            line_edit = QLineEdit(current_text)
            layout.addWidget(line_edit)
            btn = QPushButton("Сохранить")
            btn.clicked.connect(dialog.accept)
            layout.addWidget(btn)
            dialog.setLayout(layout)
            if dialog.exec_():
                update_task(task_id, field, line_edit.text())
                self.apply_filters()

    def add_new_task(self):
        """Открывает попап создания задачи."""
        self.show_controls_section(0)

    def _mark_task_complete(self, task_id):
        """Отметить задачу как завершённую."""
        update_task(task_id, "status", "Done")
        self.apply_filters()

    def _open_edit_dialog(self, row_idx):
        """Открыть диалог редактирования всей задачи."""
        if row_idx < 0 or row_idx >= len(self.tasks):
            return
        
        task = self.tasks[row_idx]
        task_id = task["id"]
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактировать задачу #{task_id}")
        dialog.setMinimumWidth(450)
        layout = QVBoxLayout()
        
        # Проект
        layout.addWidget(QLabel("Проект:"))
        project_combo = QComboBox()
        for project in self.projects:
            project_combo.addItem(project["name"], project["id"])
        project_combo.setCurrentIndex(project_combo.findData(task["project_id"]))
        layout.addWidget(project_combo)
        
        # Описание
        layout.addWidget(QLabel("Описание:"))
        desc_edit = QLineEdit(task["description"])
        layout.addWidget(desc_edit)
        
        # Исполнитель
        layout.addWidget(QLabel("Исполнитель:"))
        assignee_edit = QLineEdit(task["assignee"])
        layout.addWidget(assignee_edit)
        
        # Приоритет
        layout.addWidget(QLabel("Приоритет:"))
        priority_combo = QComboBox()
        priority_combo.addItems(["Low", "Medium", "High", "Critical"])
        priority_combo.setCurrentText(task["priority"])
        layout.addWidget(priority_combo)
        
        # Статус
        layout.addWidget(QLabel("Статус:"))
        status_combo = QComboBox()
        status_combo.addItems(["To Do", "In Progress", "Done"])
        status_combo.setCurrentText(task["status"])
        layout.addWidget(status_combo)
        
        # Дедлайн
        layout.addWidget(QLabel("Дедлайн:"))
        deadline_edit = QDateEdit()
        deadline_edit.setCalendarPopup(True)
        if task["deadline"]:
            deadline_edit.setDate(QDate.fromString(task["deadline"], "yyyy-MM-dd"))
        layout.addWidget(deadline_edit)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        def save_changes():
            update_task(task_id, "project_id", project_combo.currentData())
            update_task(task_id, "description", desc_edit.text())
            update_task(task_id, "assignee", assignee_edit.text())
            update_task(task_id, "priority", priority_combo.currentText())
            update_task(task_id, "status", status_combo.currentText())
            update_task(task_id, "deadline", deadline_edit.date().toString("yyyy-MM-dd"))
            dialog.accept()
        
        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)
        
        dialog.setLayout(layout)
        if dialog.exec_():
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
