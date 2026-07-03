from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from datetime import datetime, date
import sqlite3
import os
import csv
import io
import tempfile

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'

# Путь к базе данных
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tracker.db')

def get_db():
    """Создает подключение к базе данных"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Инициализация базы данных и создание таблиц"""
    if not os.path.exists(DATABASE):
        conn = get_db()
        cursor = conn.cursor()
        
        # Создание таблицы Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('Менеджер', 'Исполнитель'))
            )
        ''')
        
        # Создание таблицы Projects
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                manager_id INTEGER NOT NULL,
                FOREIGN KEY (manager_id) REFERENCES Users (id) ON DELETE CASCADE
            )
        ''')
        
        # Создание таблицы Tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                performer_id INTEGER,
                priority TEXT NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
                status TEXT NOT NULL DEFAULT 'To Do' CHECK (status IN ('To Do', 'In Progress', 'Done')),
                created_at DATE NOT NULL DEFAULT (date('now')),
                deadline DATE,
                finished_at DATE,
                FOREIGN KEY (project_id) REFERENCES Projects (id) ON DELETE CASCADE,
                FOREIGN KEY (performer_id) REFERENCES Users (id) ON DELETE SET NULL
            )
        ''')
        
        # Добавление тестовых данных
        cursor.execute("INSERT INTO Users (name, role) VALUES ('Иванов Иван Иванович', 'Менеджер')")
        cursor.execute("INSERT INTO Users (name, role) VALUES ('Петров Петр Петрович', 'Исполнитель')")
        cursor.execute("INSERT INTO Users (name, role) VALUES ('Сидорова Анна Михайловна', 'Исполнитель')")
        cursor.execute("INSERT INTO Users (name, role) VALUES ('Козлов Дмитрий Александрович', 'Менеджер')")
        
        cursor.execute("INSERT INTO Projects (title, manager_id) VALUES ('Разработка CRM системы', 1)")
        cursor.execute("INSERT INTO Projects (title, manager_id) VALUES ('Мобильное приложение', 4)")
        
        cursor.execute('''
            INSERT INTO Tasks (project_id, description, performer_id, priority, status, deadline) 
            VALUES (1, 'Создать базу данных', 2, 'High', 'To Do', '2024-03-15')
        ''')
        cursor.execute('''
            INSERT INTO Tasks (project_id, description, performer_id, priority, status, deadline) 
            VALUES (1, 'Разработать интерфейс', 3, 'Medium', 'In Progress', '2024-03-20')
        ''')
        cursor.execute('''
            INSERT INTO Tasks (project_id, description, performer_id, priority, status, deadline) 
            VALUES (2, 'Дизайн главного экрана', 2, 'Low', 'To Do', '2024-04-01')
        ''')
        
        conn.commit()
        conn.close()

# Инициализация базы данных при запуске
init_db()

@app.route('/')
def index():
    """Главная страница со всеми задачами"""
    conn = get_db()
    
    # Получаем все задачи с связанными данными
    tasks = conn.execute('''
        SELECT 
            t.id,
            t.description,
            t.priority,
            t.status,
            t.created_at,
            t.deadline,
            t.finished_at,
            p.title as project_title,
            p.id as project_id,
            u.name as performer_name,
            m.name as manager_name
        FROM Tasks t
        JOIN Projects p ON t.project_id = p.id
        LEFT JOIN Users u ON t.performer_id = u.id
        JOIN Users m ON p.manager_id = m.id
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    # Получаем список всех пользователей для форм
    users = conn.execute('SELECT * FROM Users ORDER BY name').fetchall()
    managers = conn.execute('SELECT * FROM Users WHERE role = "Менеджер" ORDER BY name').fetchall()
    performers = conn.execute('SELECT * FROM Users WHERE role = "Исполнитель" ORDER BY name').fetchall()
    projects = conn.execute('SELECT * FROM Projects ORDER BY title').fetchall()
    
    conn.close()
    return render_template('index.html', 
                         tasks=tasks, 
                         users=users, 
                         managers=managers, 
                         performers=performers, 
                         projects=projects,
                         today=date.today())

@app.route('/add_project', methods=['POST'])
def add_project():
    """Добавление нового проекта"""
    title = request.form.get('title')
    manager_id = request.form.get('manager_id')
    
    if title and manager_id:
        conn = get_db()
        conn.execute('INSERT INTO Projects (title, manager_id) VALUES (?, ?)', 
                    (title, manager_id))
        conn.commit()
        conn.close()
        flash('Проект успешно добавлен!', 'success')
    else:
        flash('Заполните все поля!', 'danger')
    
    return redirect(url_for('index'))

@app.route('/add_task', methods=['POST'])
def add_task():
    """Добавление новой задачи"""
    project_id = request.form.get('project_id')
    description = request.form.get('description')
    performer_id = request.form.get('performer_id') or None
    priority = request.form.get('priority')
    deadline = request.form.get('deadline') or None
    
    if project_id and description and priority:
        conn = get_db()
        conn.execute('''
            INSERT INTO Tasks (project_id, description, performer_id, priority, status, deadline) 
            VALUES (?, ?, ?, ?, 'To Do', ?)
        ''', (project_id, description, performer_id, priority, deadline))
        conn.commit()
        conn.close()
        flash('Задача успешно добавлена!', 'success')
    else:
        flash('Заполните обязательные поля!', 'danger')
    
    return redirect(url_for('index'))

@app.route('/update_task_status/<int:task_id>', methods=['POST'])
def update_task_status(task_id):
    """Обновление статуса задачи"""
    new_status = request.form.get('status')
    
    if new_status:
        conn = get_db()
        
        if new_status == 'Done':
            conn.execute('''
                UPDATE Tasks 
                SET status = ?, finished_at = date('now') 
                WHERE id = ?
            ''', (new_status, task_id))
        else:
            conn.execute('''
                UPDATE Tasks 
                SET status = ?, finished_at = NULL 
                WHERE id = ?
            ''', (new_status, task_id))
        
        conn.commit()
        conn.close()
        flash(f'Статус задачи обновлен на "{new_status}"', 'success')
    
    return redirect(url_for('index'))

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    """Редактирование задачи"""
    conn = get_db()
    
    if request.method == 'POST':
        performer_id = request.form.get('performer_id') or None
        deadline = request.form.get('deadline') or None
        description = request.form.get('description')
        priority = request.form.get('priority')
        
        conn.execute('''
            UPDATE Tasks 
            SET performer_id = ?, deadline = ?, description = ?, priority = ? 
            WHERE id = ?
        ''', (performer_id, deadline, description, priority, task_id))
        conn.commit()
        conn.close()
        flash('Задача успешно обновлена!', 'success')
        return redirect(url_for('index'))
    
    task = conn.execute('''
        SELECT t.*, p.title as project_title
        FROM Tasks t
        JOIN Projects p ON t.project_id = p.id
        WHERE t.id = ?
    ''', (task_id,)).fetchone()
    
    performers = conn.execute('SELECT * FROM Users WHERE role = "Исполнитель"').fetchall()
    conn.close()
    
    return render_template('edit_task.html', task=task, performers=performers)

@app.route('/delete_task/<int:task_id>')
def delete_task(task_id):
    """Удаление задачи"""
    conn = get_db()
    conn.execute('DELETE FROM Tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()
    flash('Задача удалена!', 'warning')
    return redirect(url_for('index'))

@app.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    """Удаление проекта"""
    conn = get_db()
    conn.execute('DELETE FROM Projects WHERE id = ?', (project_id,))
    conn.commit()
    conn.close()
    flash('Проект и все связанные задачи удалены!', 'warning')
    return redirect(url_for('index'))

@app.route('/filter_tasks')
def filter_tasks():
    """Фильтрация задач"""
    performer_id = request.args.get('performer_id')
    priority = request.args.get('priority')
    status = request.args.get('status')
    
    query = '''
        SELECT 
            t.id,
            t.description,
            t.priority,
            t.status,
            t.created_at,
            t.deadline,
            t.finished_at,
            p.title as project_title,
            p.id as project_id,
            u.name as performer_name,
            m.name as manager_name
        FROM Tasks t
        JOIN Projects p ON t.project_id = p.id
        LEFT JOIN Users u ON t.performer_id = u.id
        JOIN Users m ON p.manager_id = m.id
        WHERE 1=1
    '''
    params = []
    
    if performer_id:
        query += ' AND t.performer_id = ?'
        params.append(performer_id)
    if priority:
        query += ' AND t.priority = ?'
        params.append(priority)
    if status:
        query += ' AND t.status = ?'
        params.append(status)
    
    query += ' ORDER BY t.created_at DESC'
    
    conn = get_db()
    tasks = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify([dict(task) for task in tasks])

# ========== НОВЫЕ МАРШРУТЫ ДЛЯ ЭКСПОРТА И ИМПОРТА ==========

@app.route('/export/csv')
def export_csv():
    """Экспорт всех задач в CSV файл"""
    conn = get_db()
    
    # Получаем все задачи с полной информацией
    tasks = conn.execute('''
        SELECT 
            t.id,
            p.title as project_title,
            t.description,
            COALESCE(u.name, 'Не назначен') as performer_name,
            t.priority,
            t.status,
            t.created_at,
            t.deadline,
            t.finished_at,
            m.name as manager_name
        FROM Tasks t
        JOIN Projects p ON t.project_id = p.id
        LEFT JOIN Users u ON t.performer_id = u.id
        JOIN Users m ON p.manager_id = m.id
        ORDER BY t.id
    ''').fetchall()
    
    conn.close()
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки колонок
    writer.writerow([
        'ID задачи', 
        'Проект', 
        'Описание', 
        'Исполнитель', 
        'Приоритет', 
        'Статус', 
        'Дата создания', 
        'Дедлайн', 
        'Дата завершения',
        'Менеджер проекта'
    ])
    
    # Данные
    for task in tasks:
        writer.writerow([
            task['id'],
            task['project_title'],
            task['description'],
            task['performer_name'],
            task['priority'],
            task['status'],
            task['created_at'],
            task['deadline'] if task['deadline'] else '',
            task['finished_at'] if task['finished_at'] else '',
            task['manager_name']
        ])
    
    # Подготавливаем ответ
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),  # UTF-8 с BOM для корректного открытия в Excel
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=tasks_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

@app.route('/export/projects_csv')
def export_projects_csv():
    """Экспорт проектов в CSV файл"""
    conn = get_db()
    
    projects = conn.execute('''
        SELECT 
            p.id,
            p.title,
            u.name as manager_name,
            COUNT(t.id) as task_count,
            SUM(CASE WHEN t.status = 'Done' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(CASE WHEN t.status != 'Done' THEN 1 ELSE 0 END) as active_tasks
        FROM Projects p
        JOIN Users u ON p.manager_id = u.id
        LEFT JOIN Tasks t ON p.id = t.project_id
        GROUP BY p.id, p.title, u.name
        ORDER BY p.id
    ''').fetchall()
    
    conn.close()
    
    # Создаем CSV в памяти
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'ID проекта',
        'Название проекта',
        'Менеджер',
        'Всего задач',
        'Завершенных задач',
        'Активных задач'
    ])
    
    # Данные
    for project in projects:
        writer.writerow([
            project['id'],
            project['title'],
            project['manager_name'],
            project['task_count'],
            project['completed_tasks'],
            project['active_tasks']
        ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=projects_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

@app.route('/import/csv', methods=['POST'])
def import_csv():
    """Импорт задач из CSV файла"""
    if 'file' not in request.files:
        flash('Файл не выбран!', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Файл не выбран!', 'danger')
        return redirect(url_for('index'))
    
    if not file.filename.endswith('.csv'):
        flash('Пожалуйста, загрузите файл в формате CSV!', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Читаем CSV файл
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        csv_reader = csv.DictReader(stream)
        
        conn = get_db()
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Начинаем со 2 строки (1 - заголовки)
            try:
                # Проверяем обязательные поля
                if 'Проект' not in row or 'Описание' not in row:
                    flash('Неверный формат CSV файла. Требуются колонки: "Проект", "Описание"', 'danger')
                    return redirect(url_for('index'))
                
                project_title = row.get('Проект', '').strip()
                description = row.get('Описание', '').strip()
                performer_name = row.get('Исполнитель', '').strip()
                priority = row.get('Приоритет', 'Medium').strip()
                status = row.get('Статус', 'To Do').strip()
                deadline = row.get('Дедлайн', '').strip()
                
                if not project_title or not description:
                    errors.append(f'Строка {row_num}: пропущены обязательные поля')
                    continue
                
                # Проверяем приоритет
                if priority not in ['Low', 'Medium', 'High']:
                    priority = 'Medium'
                
                # Проверяем статус
                if status not in ['To Do', 'In Progress', 'Done']:
                    status = 'To Do'
                
                # Находим или создаем проект
                project = conn.execute(
                    'SELECT id FROM Projects WHERE title = ?', 
                    (project_title,)
                ).fetchone()
                
                if not project:
                    # Если проект не существует, создаем с первым доступным менеджером
                    manager = conn.execute(
                        'SELECT id FROM Users WHERE role = "Менеджер" LIMIT 1'
                    ).fetchone()
                    
                    if manager:
                        cursor = conn.execute(
                            'INSERT INTO Projects (title, manager_id) VALUES (?, ?)',
                            (project_title, manager['id'])
                        )
                        project_id = cursor.lastrowid
                    else:
                        errors.append(f'Строка {row_num}: нет доступных менеджеров для создания проекта')
                        continue
                else:
                    project_id = project['id']
                
                # Находим исполнителя по имени, если указан
                performer_id = None
                if performer_name and performer_name != 'Не назначен':
                    performer = conn.execute(
                        'SELECT id FROM Users WHERE name = ? AND role = "Исполнитель"',
                        (performer_name,)
                    ).fetchone()
                    
                    if not performer:
                        # Создаем нового исполнителя
                        cursor = conn.execute(
                            'INSERT INTO Users (name, role) VALUES (?, "Исполнитель")',
                            (performer_name,)
                        )
                        performer_id = cursor.lastrowid
                    else:
                        performer_id = performer['id']
                
                # Определяем finished_at
                finished_at = None
                if status == 'Done':
                    finished_at = date.today().isoformat()
                
                # Вставляем задачу
                conn.execute('''
                    INSERT INTO Tasks (
                        project_id, description, performer_id, 
                        priority, status, deadline, finished_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    project_id, description, performer_id,
                    priority, status, 
                    deadline if deadline else None,
                    finished_at
                ))
                
                imported_count += 1
                
            except Exception as e:
                errors.append(f'Строка {row_num}: ошибка обработки - {str(e)}')
                continue
        
        conn.commit()
        conn.close()
        
        if imported_count > 0:
            flash(f'Успешно импортировано задач: {imported_count}', 'success')
        
        if errors:
            for error in errors[:5]:  # Показываем первые 5 ошибок
                flash(error, 'warning')
            if len(errors) > 5:
                flash(f'... и еще {len(errors) - 5} ошибок', 'warning')
        
    except Exception as e:
        flash(f'Ошибка при импорте файла: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/export/all_data_csv')
def export_all_data_csv():
    """Экспорт всех данных (пользователи, проекты, задачи) в CSV"""
    conn = get_db()
    
    # Создаем временный файл для ZIP архива с несколькими CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Секция пользователей
    writer.writerow(['=== ПОЛЬЗОВАТЕЛИ ==='])
    writer.writerow(['ID', 'ФИО', 'Роль'])
    
    users = conn.execute('SELECT * FROM Users ORDER BY id').fetchall()
    for user in users:
        writer.writerow([user['id'], user['name'], user['role']])
    
    writer.writerow([])  # Пустая строка для разделения
    
    # Секция проектов
    writer.writerow(['=== ПРОЕКТЫ ==='])
    writer.writerow(['ID', 'Название', 'ID менеджера', 'Менеджер'])
    
    projects = conn.execute('''
        SELECT p.id, p.title, p.manager_id, u.name as manager_name
        FROM Projects p
        JOIN Users u ON p.manager_id = u.id
        ORDER BY p.id
    ''').fetchall()
    
    for project in projects:
        writer.writerow([
            project['id'], 
            project['title'], 
            project['manager_id'],
            project['manager_name']
        ])
    
    writer.writerow([])
    
    # Секция задач
    writer.writerow(['=== ЗАДАЧИ ==='])
    writer.writerow([
        'ID', 'ID проекта', 'Проект', 'Описание', 'ID исполнителя',
        'Исполнитель', 'Приоритет', 'Статус', 'Создана', 'Дедлайн', 'Завершена'
    ])
    
    tasks = conn.execute('''
        SELECT 
            t.id, t.project_id, p.title as project_title,
            t.description, t.performer_id, 
            COALESCE(u.name, 'Не назначен') as performer_name,
            t.priority, t.status, t.created_at, t.deadline, t.finished_at
        FROM Tasks t
        JOIN Projects p ON t.project_id = p.id
        LEFT JOIN Users u ON t.performer_id = u.id
        ORDER BY t.id
    ''').fetchall()
    
    for task in tasks:
        writer.writerow([
            task['id'], task['project_id'], task['project_title'],
            task['description'], task['performer_id'] or '',
            task['performer_name'], task['priority'], task['status'],
            task['created_at'], task['deadline'] or '', task['finished_at'] or ''
        ])
    
    conn.close()
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=all_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

@app.route('/download_template')
def download_template():
    """Скачивание шаблона CSV для импорта задач"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Заголовки с примерами
    writer.writerow([
        'Проект', 
        'Описание', 
        'Исполнитель', 
        'Приоритет', 
        'Статус', 
        'Дедлайн'
    ])
    
    # Примеры данных
    writer.writerow([
        'Разработка CRM системы',
        'Создать API для авторизации',
        'Петров Петр Петрович',
        'High',
        'To Do',
        '2024-04-15'
    ])
    
    writer.writerow([
        'Мобильное приложение',
        'Разработать дизайн главного экрана',
        'Сидорова Анна Михайловна',
        'Medium',
        'In Progress',
        '2024-04-20'
    ])
    
    writer.writerow([
        'Разработка CRM системы',
        'Написать документацию',
        'Не назначен',
        'Low',
        'To Do',
        ''
    ])
    
    output.seek(0)
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=import_template.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)