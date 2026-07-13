
"""Модуль работы с базой данных SQLite.

Кратко: создаёт/инициализирует локальную БД, наполняет тестовыми данными
и предоставляет простые CRUD- и аналитические функции для задач.
"""
import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")
ALLOWED_UPDATE_FIELDS = {"description", "assignee", "priority", "status", "deadline", "project_id"}


def get_connection():
    """Получить соединение с БД."""
    # Возвращает sqlite3.Connection с row_factory для удобного доступа по ключу
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Инициализация базы данных и создание таблиц."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            manager TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            assignee TEXT NOT NULL,
            priority TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High', 'Critical')),
            status TEXT NOT NULL CHECK(status IN ('To Do', 'In Progress', 'Done')),
            created_at TEXT NOT NULL,
            deadline TEXT,
            completed_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def seed_data():
    """Заполнение тестовыми данными, если таблицы пустые."""
    # Добавляет проекты и набор случайных задач только при пустой БД.
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    projects = [
        ("E-commerce Platform", "Алексей Иванов"),
        ("Mobile Banking App", "Мария Петрова"),
        ("CRM System", "Дмитрий Сидоров"),
        ("Data Warehouse", "Анна Козлова"),
        ("AI Chatbot", "Сергей Новиков"),
        ("Cloud Migration", "Ольга Морозова"),
        ("Security Audit", "Иван Волков"),
        ("API Gateway", "Елена Соколова"),
        ("DevOps Dashboard", "Андрей Лебедев"),
        ("ML Pipeline", "Наталья Попова"),
        ("IoT Platform", "Виктор Кузнецов"),
        ("Blockchain Wallet", "Михаил Смирнов"),
    ]

    cursor.executemany("INSERT INTO projects (name, manager) VALUES (?, ?)", projects)
    conn.commit()

    cursor.execute("SELECT id FROM projects")
    project_ids = [row["id"] for row in cursor.fetchall()]

    assignees = [
        "Иван Сидоров", "Мария Кузнецова", "Алексей Петров", "Ольга Новикова",
        "Дмитрий Волков", "Анна Смирнова", "Сергей Попов", "Елена Морозова",
        "Андрей Лебедев", "Наталья Соколова", "Виктор Иванов", "Михаил Козлов"
    ]

    priorities = ["Low", "Medium", "High", "Critical"]
    statuses = ["To Do", "In Progress", "Done"]

    task_templates = [
        "Разработать модуль авторизации",
        "Настроить CI/CD pipeline",
        "Оптимизировать запросы к БД",
        "Написать unit-тесты",
        "Обновить документацию API",
        "Интегрировать платёжную систему",
        "Настроить мониторинг",
        "Реализовать кэширование",
        "Провести security review",
        "Обновить зависимости",
        "Настроить логирование",
        "Реализовать пагинацию",
        "Добавить валидацию форм",
        "Оптимизировать frontend",
        "Настроить резервное копирование",
        "Реализовать поиск",
        "Добавить фильтры",
        "Настроить email-уведомления",
        "Реализовать экспорт данных",
        "Провести нагрузочное тестирование",
        "Обновить UI компоненты",
        "Настроить SSO",
        "Реализовать WebSocket",
        "Добавить rate limiting",
        "Настроить Docker",
        "Реализовать миграции БД",
        "Добавить мультиязычность",
        "Настроить CDN",
        "Реализовать push-уведомления",
        "Обновить политику безопасности",
        "Настроить Grafana dashboards",
        "Реализовать OAuth2",
        "Добавить 2FA",
        "Настроить Kafka",
        "Реализовать event sourcing",
        "Обновить ORM",
        "Настроить ELK stack",
        "Реализовать CQRS",
        "Добавить GraphQL",
        "Настроить Vault",
        "Реализовать feature flags",
        "Обновить React до v19",
        "Настроить Kubernetes",
        "Реализовать микросервисы",
        "Добавить circuit breaker",
        "Настроить Jaeger tracing",
        "Реализовать graceful shutdown",
        "Обновить Python до 3.13",
        "Настроить Terraform",
        "Реализовать blue-green deployment",
        "Добавить health checks",
        "Настроить Prometheus",
        "Реализовать retry logic",
        "Обновить SSL-сертификаты",
        "Настроить WAF",
        "Реализовать audit log",
    ]

    random.seed(42)
    base_date = datetime(2025, 1, 1)

    tasks_data = []
    for i in range(80):
        created_at = base_date + timedelta(days=random.randint(0, 180))
        deadline = created_at + timedelta(days=random.randint(3, 30))
        status = random.choice(statuses)
        completed_at = None
        if status == "Done":
            completed_at = created_at + timedelta(days=random.randint(1, 28))
            if completed_at > datetime.now():
                completed_at = datetime.now() - timedelta(days=random.randint(1, 7))
        elif status == "In Progress":
            if random.random() < 0.3:
                completed_at = datetime.now() - timedelta(days=random.randint(1, 5))
                status = "Done"

        tasks_data.append((
            random.choice(project_ids),
            task_templates[i % len(task_templates)] + f" #{i+1}",
            random.choice(assignees),
            random.choice(priorities),
            status,
            created_at.strftime("%Y-%m-%d"),
            deadline.strftime("%Y-%m-%d"),
            completed_at.strftime("%Y-%m-%d") if completed_at else None
        ))

    cursor.executemany("""
        INSERT INTO tasks (project_id, description, assignee, priority, status, created_at, deadline, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, tasks_data)

    conn.commit()
    conn.close()
    print("База данных инициализирована и заполнена тестовыми данными.")


# === CRUD операции ===

def get_all_tasks(filters=None):
    """Получить все задачи с опциональной фильтрацией."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT t.*, p.name as project_name
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE 1=1
    """
    params = []

    if filters:
        # Собираем WHERE по частям, чтобы не плодить кучу почти одинаковых запросов.
        if filters.get("assignee"):
            query += " AND t.assignee = ?"
            params.append(filters["assignee"])
        if filters.get("status"):
            query += " AND t.status = ?"
            params.append(filters["status"])
        if filters.get("priority"):
            query += " AND t.priority = ?"
            params.append(filters["priority"])
        if filters.get("project_id"):
            query += " AND t.project_id = ?"
            params.append(filters["project_id"])
        if filters.get("search"):
            query += " AND (t.description LIKE ? OR t.assignee LIKE ?)"
            params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

    query += " ORDER BY t.created_at DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_projects():
    """Получить все проекты."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_assignees():
    """Получить список всех исполнителей."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT assignee FROM tasks ORDER BY assignee")
    rows = cursor.fetchall()
    conn.close()
    return [row["assignee"] for row in rows]


def add_task(project_id, description, assignee, priority, status, deadline):
    """Добавить новую задачу."""
    conn = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d")
    completed_at = None
    if status == "Done":
        # Если создаём задачу сразу как Done, сразу проставляем completed_at.
        completed_at = created_at

    cursor.execute("""
        INSERT INTO tasks (project_id, description, assignee, priority, status, created_at, deadline, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (project_id, description, assignee, priority, status, created_at, deadline, completed_at))

    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return task_id


def update_task(task_id, field, value):
    """Обновить поле задачи."""
    if field not in ALLOWED_UPDATE_FIELDS:
        raise ValueError(f"Unsupported task field: {field}")

    conn = get_connection()
    cursor = conn.cursor()

    if field == "status" and value == "Done":
        # Переход в Done: фиксируем дату закрытия.
        cursor.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
                       (value, datetime.now().strftime("%Y-%m-%d"), task_id))
    elif field == "status" and value != "Done":
        # Вернули задачу из Done — очищаем дату закрытия.
        cursor.execute("UPDATE tasks SET status = ?, completed_at = NULL WHERE id = ?",
                       (value, task_id))
    else:
        cursor.execute(f"UPDATE tasks SET {field} = ? WHERE id = ?", (value, task_id))

    conn.commit()
    conn.close()


def delete_task(task_id):
    """Удалить задачу."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_analytics_data():
    """Получить данные для аналитики."""
    conn = get_connection()
    cursor = conn.cursor()

    # Отдаём уже посчитанные агрегаты, чтобы UI просто рисовал графики.
    # Загруженность исполнителей
    cursor.execute("""
        SELECT assignee, COUNT(*) as count FROM tasks GROUP BY assignee ORDER BY count DESC
    """)
    assignee_load = [(row["assignee"], row["count"]) for row in cursor.fetchall()]

    # Просроченные задачи по проектам
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT p.name, COUNT(*) as count
        FROM tasks t
        JOIN projects p ON t.project_id = p.id
        WHERE t.deadline < ? AND t.status != 'Done'
        GROUP BY p.name
        ORDER BY count DESC
    """, (today,))
    overdue_by_project = [(row["name"], row["count"]) for row in cursor.fetchall()]

    # Среднее время выполнения по приоритетам
    cursor.execute("""
        SELECT priority,
               AVG(JULIANDAY(completed_at) - JULIANDAY(created_at)) as avg_days
        FROM tasks
        WHERE status = 'Done' AND completed_at IS NOT NULL
        GROUP BY priority
    """)
    avg_time_by_priority = [(row["priority"], row["avg_days"]) for row in cursor.fetchall()]

    # Распределение по статусам
    cursor.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
    status_distribution = [(row["status"], row["count"]) for row in cursor.fetchall()]

    # Закрытые задачи по неделям
    cursor.execute("""
        SELECT strftime('%Y-W%W', completed_at) as week, COUNT(*) as count
        FROM tasks
        WHERE status = 'Done' AND completed_at IS NOT NULL
        GROUP BY week
        ORDER BY week
    """)
    closed_by_week = [(row["week"], row["count"]) for row in cursor.fetchall()]

    # Закрытые задачи по месяцам
    cursor.execute("""
        SELECT strftime('%Y-%m', completed_at) as month, COUNT(*) as count
        FROM tasks
        WHERE status = 'Done' AND completed_at IS NOT NULL
        GROUP BY month
        ORDER BY month
    """)
    closed_by_month = [(row["month"], row["count"]) for row in cursor.fetchall()]

    conn.close()
    return {
        "assignee_load": assignee_load,
        "overdue_by_project": overdue_by_project,
        "avg_time_by_priority": avg_time_by_priority,
        "status_distribution": status_distribution,
        "closed_by_week": closed_by_week,
        "closed_by_month": closed_by_month,
    }
