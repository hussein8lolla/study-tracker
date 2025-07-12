import os
import sqlite3
import psycopg2
from psycopg2 import pool
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
from flask_session import Session
import bcrypt
from datetime import datetime

UPLOAD_FOLDER = 'Uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app_flask = Flask(__name__)
app_flask.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app_flask.config['SESSION_TYPE'] = 'filesystem'
app_flask.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app_flask.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session expires after 1 hour
Session(app_flask)

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, DATABASE_URL)
    USE_POSTGRES = True
else:
    DATABASE = 'study_tracker.db'
    USE_POSTGRES = False

def get_db_connection():
    if USE_POSTGRES:
        return db_pool.getconn()
    else:
        return sqlite3.connect(DATABASE)

def release_db_connection(conn):
    if USE_POSTGRES:
        db_pool.putconn(conn)
    else:
        conn.close()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id SERIAL PRIMARY KEY,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            duration INTEGER NOT NULL,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            row_span INTEGER DEFAULT 1,
            col_span INTEGER DEFAULT 1,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            day TEXT NOT NULL,
            text TEXT NOT NULL,
            completed BOOLEAN DEFAULT FALSE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_log (
            id SERIAL PRIMARY KEY,
            points INTEGER NOT NULL,
            log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = %s' if USE_POSTGRES else 'SELECT COUNT(*) FROM users WHERE username = ?', ("shahenda",))
    if cursor.fetchone()[0] == 0:
        hashed_password = bcrypt.hashpw("shahenda@HUSSEIN8".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO users (name, username, password) VALUES (%s, %s, %s)' if USE_POSTGRES else 'INSERT INTO users (name, username, password) VALUES (?, ?, ?)',
                       ("Shahenda", "shahenda", hashed_password))
    conn.commit()
    release_db_connection(conn)

def login_required(f):
    def wrap(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app_flask.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            if not username or not password:
                return render_template('login.html', error="يجب إدخال اسم المستخدم وكلمة المرور")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, password FROM users WHERE username = %s' if USE_POSTGRES else 'SELECT id, password FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            release_db_connection(conn)
            if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
                session['logged_in'] = True
                session['user_id'] = user[0]
                session.permanent = True
                return redirect(url_for('web_index'))
            else:
                return render_template('login.html', error="بيانات الدخول غير صحيحة")
        return render_template('login.html', error=None)
    except Exception as e:
        print(f"خطأ: {e}")
        return render_template('login.html', error="حدث خطأ غير متوقع")

@app_flask.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app_flask.route('/')
@login_required
def web_index():
    user_id = session.get('user_id')
    days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']
    hours = [f"{h}:00" for h in range(7, 24)]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM schedule WHERE user_id = %s' if USE_POSTGRES else 'SELECT * FROM schedule WHERE user_id = ?', (user_id,))
    lectures = cursor.fetchall()
    schedule = [[None for _ in range(len(hours))] for _ in range(len(days))]
    for lecture in lectures:
        day = lecture[1]
        storage_time = lecture[2]
        display_time = storage_time[1:] if storage_time.startswith('0') else storage_time
        if display_time not in hours:
            continue
        day_idx = days.index(day)
        time_idx = hours.index(display_time)
        row_span = lecture[6] or 1
        col_span = lecture[7] or 1
        for i in range(row_span):
            for j in range(col_span):
                if i == 0 and j == 0:
                    schedule[day_idx][time_idx] = {
                        'name': lecture[4],
                        'color': lecture[5],
                        'row_span': row_span,
                        'col_span': col_span
                    }
                else:
                    if time_idx + j < len(hours) and day_idx + i < len(days):
                        schedule[day_idx + i][time_idx + j] = 'merged'
    cursor.execute('SELECT * FROM tasks WHERE user_id = %s' if USE_POSTGRES else 'SELECT * FROM tasks WHERE user_id = ?', (user_id,))
    tasks = cursor.fetchall()
    today = datetime.now()
    arabic_days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    day_name = arabic_days[today.weekday()]
    date_str = f"{day_name} - {today.strftime('%d/%m/%Y')}"
    release_db_connection(conn)
    return render_template('index.html', days=days, hours=hours, schedule=schedule, tasks=tasks, date_str=date_str)

@app_flask.route('/files')
@login_required
def list_files():
    user_id = session.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM files WHERE user_id = %s' if USE_POSTGRES else 'SELECT * FROM files WHERE user_id = ?', (user_id,))
    files = cursor.fetchall()
    release_db_connection(conn)
    return render_template('files.html', files=files)

@app_flask.route('/Uploads/<filename>')
@login_required
def download_file(filename):
    try:
        return send_from_directory(app_flask.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        return "الملف غير موجود", 404

@app_flask.route('/update_task', methods=['POST'])
@login_required
def web_update_task():
    user_id = session.get('user_id')
    task_id = request.json.get('id')
    completed = request.json.get('completed')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET completed = %s, last_updated = CURRENT_TIMESTAMP WHERE id = %s AND user_id = %s' if USE_POSTGRES else 'UPDATE tasks SET completed = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?',
                   (completed, task_id, user_id) if USE_POSTGRES else (1 if completed else 0, task_id, user_id))
    conn.commit()
    release_db_connection(conn)
    return jsonify(success=True)

if __name__ == '__main__':
    init_db()
    app_flask.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))