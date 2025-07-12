import os
import shutil
import sys
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
                             QHeaderView, QPushButton, QVBoxLayout, QWidget, QLabel,
                             QHBoxLayout, QColorDialog, QMessageBox, QSplitter,
                             QListWidget, QListWidgetItem, QInputDialog, QStyledItemDelegate,
                             QLineEdit, QComboBox, QStatusBar, QFileDialog, QMenu)
from PyQt6.QtCore import Qt, QSize, QDate, QTimer
from PyQt6.QtGui import QColor, QFont, QAction
import bcrypt

DATABASE = 'study_tracker.db'
UPLOAD_FOLDER = 'Uploads'

def init_db():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY,
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
            id INTEGER PRIMARY KEY,
            day TEXT NOT NULL,
            text TEXT NOT NULL,
            completed BOOLEAN DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_log (
            id INTEGER PRIMARY KEY,
            points INTEGER NOT NULL,
            log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ("shahenda",))
    if cursor.fetchone()[0] == 0:
        hashed_password = bcrypt.hashpw("shahenda@HUSSEIN8".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO users (name, username, password) VALUES (?, ?, ?)',
                       ("Shahenda", "shahenda", hashed_password))
    conn.commit()
    conn.close()

class TaskListWidgetItem(QListWidgetItem):
    def __init__(self, task_id, text, day, completed=False, parent=None):
        super().__init__(text, parent)
        self.task_id = task_id
        self.day = day
        self.is_completed = completed
        self.setFont(QFont("Arial", 12))
        self.setSizeHint(QSize(0, 40))

class TaskDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        list_widget = self.parent()
        item = list_widget.item(index.row())
        if not item:
            return
        if item.is_completed:
            painter.fillRect(option.rect, QColor(46, 204, 113, 100))
            painter.setPen(QColor(0, 0, 0))
        else:
            painter.fillRect(option.rect, QColor(231, 76, 60, 100))
            painter.setPen(QColor(255, 255, 255))
        text_rect = option.rect.adjusted(40, 0, -40, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, item.text())
        delete_rect = option.rect.adjusted(option.rect.width() - 40, 0, -10, 0)
        painter.setBrush(QColor(192, 57, 43))
        painter.drawRect(delete_rect)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(delete_rect, Qt.AlignmentFlag.AlignCenter, "X")
        edit_rect = option.rect.adjusted(option.rect.width() - 80, 0, -50, 0)
        painter.setBrush(QColor(241, 196, 15))
        painter.drawRect(edit_rect)
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(edit_rect, Qt.AlignmentFlag.AlignCenter, "✎")
        day_rect = option.rect.adjusted(10, 0, -90, 0)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(day_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"[{item.day}]")

class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("تسجيل الدخول")
        self.setGeometry(400, 200, 400, 300)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        title_label = QLabel("تسجيل الدخول")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; color: #f39c12; font-weight: bold; margin: 15px;")
        self.layout.addWidget(title_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setStyleSheet("padding: 10px; border-radius: 5px;")
        self.layout.addWidget(self.username_input)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 10px; border-radius: 5px;")
        self.layout.addWidget(self.password_input)
        self.login_btn = QPushButton("تسجيل الدخول")
        self.login_btn.setStyleSheet("background-color: #3498db; color: white; padding: 10px; border-radius: 5px;")
        self.login_btn.clicked.connect(self.login)
        self.layout.addWidget(self.login_btn)
        self.new_user_btn = QPushButton("مستخدم جديد")
        self.new_user_btn.setStyleSheet("background-color: #2ecc71; color: white; padding: 10px; border-radius: 5px;")
        self.new_user_btn.clicked.connect(self.add_new_user)
        self.layout.addWidget(self.new_user_btn)
        self.manage_users_btn = QPushButton("إدارة المستخدمين")
        self.manage_users_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px; border-radius: 5px;")
        self.manage_users_btn.clicked.connect(self.show_user_management)
        self.layout.addWidget(self.manage_users_btn)
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c; font-size: 14px; text-align: center;")
        self.layout.addWidget(self.error_label)

    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            self.main_window = StudyScheduleApp(username)
            self.main_window.show()
            self.close()
        else:
            self.error_label.setText("اسم المستخدم أو كلمة المرور غير صحيحة")

    def add_new_user(self):
        name, ok1 = QInputDialog.getText(self, "إضافة مستخدم جديد", "أدخل الاسم:")
        if not ok1 or not name.strip():
            return
        username, ok2 = QInputDialog.getText(self, "إضافة مستخدم جديد", "أدخل اسم المستخدم:")
        if not ok2 or not username.strip():
            return
        password, ok3 = QInputDialog.getText(self, "إضافة مستخدم جديد", "أدخل كلمة المرور:", QLineEdit.EchoMode.Password)
        if not ok3 or not password.strip():
            return
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', (username,))
        if cursor.fetchone()[0] > 0:
            self.error_label.setText("اسم المستخدم موجود بالفعل، اختر اسمًا آخر")
            conn.close()
            return
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('INSERT INTO users (name, username, password) VALUES (?, ?, ?)', (name, username, hashed_password))
        conn.commit()
        conn.close()
        self.error_label.setText("تم إضافة المستخدم بنجاح")

    def show_user_management(self):
        self.user_management_window = UserManagementWindow(self)
        self.user_management_window.show()

class UserManagementWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إدارة المستخدمين")
        self.setGeometry(450, 250, 500, 400)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.users_list = QListWidget()
        self.load_users()
        self.layout.addWidget(self.users_list)
        self.delete_user_btn = QPushButton("مسح المستخدم المحدد")
        self.delete_user_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px;")
        self.delete_user_btn.clicked.connect(self.delete_selected_user)
        self.layout.addWidget(self.delete_user_btn)

    def load_users(self):
        self.users_list.clear()
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, username FROM users')
        users = cursor.fetchall()
        conn.close()
        for user in users:
            user_id, name, username = user
            item_text = f"ID: {user_id} | Name: {name} | Username: {username}"
            item = QListWidgetItem(item_text)
            self.users_list.addItem(item)

    def delete_selected_user(self):
        selected_item = self.users_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد مستخدم للمسح")
            return
        user_id = int(selected_item.text().split("|")[0].replace("ID: ", "").strip())
        reply = QMessageBox.question(self, "تأكيد المسح", f"هل أنت متأكد إنك عايز تمسح المستخدم (ID: {user_id})؟",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            cursor.execute('DELETE FROM schedule WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM tasks WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM files WHERE user_id = ?', (user_id,))
            cursor.execute('DELETE FROM points_log WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            self.load_users()
            QMessageBox.information(self, "نجاح", "تم مسح المستخدم بنجاح")

class StudyScheduleApp(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("Study Schedule Manager")
        self.setGeometry(100, 100, 1400, 800)
        self.username = username
        self.user_id = self.get_user_id()
        self.days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"]
        self.hours = [f"{h}:00" for h in range(7, 24)]
        if "7:00" not in self.hours:
            self.hours.insert(0, "7:00")
        self.setup_ui()
        self.load_data()
        self.setup_timer()

    def get_user_id(self):
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (self.username,))
        user_id = cursor.fetchone()
        conn.close()
        return user_id[0] if user_id else None

    def normalize_time(self, time_str, for_display=True):
        try:
            time_str = str(time_str).strip().replace(" ", "").replace(":", "")
            if len(time_str) <= 2:
                hours = int(time_str)
            else:
                if len(time_str) == 3:
                    hours = int(time_str[0])
                elif len(time_str) == 4:
                    if time_str.startswith('0'):
                        hours = int(time_str[1])
                    else:
                        hours = int(time_str[:2])
                else:
                    hours = int(time_str[:2])
            if hours < 7 or hours >= 24:
                raise ValueError("الوقت خارج النطاق المسموح (7-23)")
            return f"{hours}:00" if for_display else f"{hours:02d}:00"
        except Exception as e:
            print(f"تحذير: تنسيق الوقت غير صحيح '{time_str}': {str(e)}")
            return "7:00" if for_display else "07:00"

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.setup_header()
        self.setup_upload_button()
        self.setup_main_content()
        self.setup_points_section()
        self.setup_footer()

    def setup_header(self):
        title_label = QLabel("Study Schedule Manager")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 28px; color: #f39c12; font-weight: bold; margin: 15px;")
        self.layout.addWidget(title_label)
        self.date_label = QLabel()
        self.update_date()
        self.date_label.setStyleSheet("font-size: 16px; color: #ecf0f1;")
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.date_label)

    def setup_upload_button(self):
        self.upload_btn = QPushButton("رفع ملف PDF")
        self.upload_btn.setStyleSheet("background-color: #e67e22;")
        self.upload_btn.clicked.connect(self.upload_pdf)
        self.layout.addWidget(self.upload_btn)
        self.clear_files_btn = QPushButton("مسح الملفات")
        self.clear_files_btn.setStyleSheet("background-color: #e74c3c;")
        self.clear_files_btn.clicked.connect(self.clear_files)
        self.layout.addWidget(self.clear_files_btn)

    def setup_main_content(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.layout.addWidget(self.splitter, 1)
        self.setup_schedule_table()
        self.setup_tasks_section()

    def setup_schedule_table(self):
        self.table = QTableWidget(len(self.days), len(self.hours))
        self.table.setMinimumHeight(500)
        self.table.setVerticalHeaderLabels(self.days)
        self.table.setHorizontalHeaderLabels(self.hours)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ContiguousSelection)
        self.table.cellDoubleClicked.connect(self.edit_lecture)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.splitter.addWidget(self.table)

    def setup_tasks_section(self):
        tasks_container = QWidget()
        tasks_layout = QVBoxLayout(tasks_container)
        tasks_container.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 10px;")
        tasks_label = QLabel("قائمة المهام اليومية")
        tasks_label.setStyleSheet("font-size: 18px; color: #f1c40f; font-weight: bold;")
        tasks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tasks_layout.addWidget(tasks_label)
        self.setup_task_input(tasks_layout)
        self.setup_tasks_list(tasks_layout)
        self.setup_task_buttons(tasks_layout)
        self.splitter.addWidget(tasks_container)
        self.splitter.setSizes([900, 400])

    def setup_task_input(self, layout):
        task_form_layout = QHBoxLayout()
        self.new_task_text = QLineEdit()
        self.new_task_text.setPlaceholderText("أدخل مهمة جديدة...")
        task_form_layout.addWidget(self.new_task_text)
        self.new_task_day = QComboBox()
        self.new_task_day.addItems(["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "عام"])
        task_form_layout.addWidget(self.new_task_day)
        self.add_task_btn = QPushButton("إضافة")
        self.add_task_btn.setStyleSheet("background-color: #2ecc71;")
        self.add_task_btn.clicked.connect(self.add_new_task)
        task_form_layout.addWidget(self.add_task_btn)
        layout.addLayout(task_form_layout)

    def setup_tasks_list(self, layout):
        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("""
            QListWidget { background-color: #2c3e50; border-radius: 8px; padding: 10px; }
            QListWidget::item { border-bottom: 1px solid #7f8c8d; padding: 8px; }
            QListWidget::item:selected { background-color: #3498db; }
        """)
        self.tasks_list.setItemDelegate(TaskDelegate(self.tasks_list))
        self.tasks_list.itemClicked.connect(self.handle_task_click)
        layout.addWidget(self.tasks_list, 1)

    def setup_task_buttons(self, layout):
        task_controls = QHBoxLayout()
        self.clear_tasks_btn = QPushButton("حذف المهام المكتملة")
        self.clear_tasks_btn.setStyleSheet("background-color: #e74c3c;")
        self.clear_tasks_btn.clicked.connect(self.clear_completed_tasks)
        task_controls.addWidget(self.clear_tasks_btn)
        self.refresh_tasks_btn = QPushButton("تحديث البيانات")
        self.refresh_tasks_btn.setStyleSheet("background-color: #9b59b6;")
        self.refresh_tasks_btn.clicked.connect(self.load_data)
        task_controls.addWidget(self.refresh_tasks_btn)
        layout.addLayout(task_controls)

    def setup_points_section(self):
        points_container = QWidget()
        points_layout = QVBoxLayout(points_container)
        points_container.setStyleSheet("background-color: #34495e; border-radius: 10px; padding: 10px;")
        self.points_label = QLabel("نقاطك: 0")
        self.points_label.setStyleSheet("font-size: 18px; color: #f1c40f; font-weight: bold; text-align: center;")
        self.points_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        points_layout.addWidget(self.points_label)
        self.weekly_message = QLabel("")
        self.weekly_message.setStyleSheet("font-size: 14px; color: #e74c3c; text-align: center;")
        self.weekly_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        points_layout.addWidget(self.weekly_message)
        input_layout = QHBoxLayout()
        self.points_input = QLineEdit()
        self.points_input.setPlaceholderText("أدخل النقاط")
        self.points_input.setStyleSheet("background-color: #ecf0f1; border-radius: 5px; padding: 5px;")
        input_layout.addWidget(self.points_input)
        add_points_btn = QPushButton("إضافة النقاط")
        add_points_btn.setStyleSheet("background-color: #2ecc71; color: white; border-radius: 5px; padding: 5px;")
        add_points_btn.clicked.connect(self.add_points_manually)
        input_layout.addWidget(add_points_btn)
        points_layout.addLayout(input_layout)
        reset_points_btn = QPushButton("تحديث النقاط (إعادة تعيين)")
        reset_points_btn.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 5px; padding: 5px;")
        reset_points_btn.clicked.connect(self.reset_points)
        points_layout.addWidget(reset_points_btn)
        self.splitter.addWidget(points_container)
        self.splitter.setSizes([900, 400, 200])

    def setup_footer(self):
        self.save_btn = QPushButton("حفظ كل التغييرات")
        self.save_btn.setStyleSheet("background-color: #3498db;")
        self.save_btn.clicked.connect(self.save_all_data)
        self.layout.addWidget(self.save_btn)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def show_context_menu(self, pos):
        try:
            item = self.table.itemAt(pos)
            if not item:
                return
            menu = QMenu(self)
            merge_action = QAction("دمج الخلايا", self)
            merge_action.triggered.connect(self.merge_selected_cells)
            menu.addAction(merge_action)
            unmerge_action = QAction("إلغاء الدمج", self)
            unmerge_action.triggered.connect(self.unmerge_cells)
            menu.addAction(unmerge_action)
            menu.exec(self.table.viewport().mapToGlobal(pos))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء عرض القائمة: {str(e)}")

    def merge_selected_cells(self):
        try:
            selected_ranges = self.table.selectedRanges()
            if not selected_ranges:
                QMessageBox.warning(self, "تحذير", "الرجاء تحديد خلايا لدمجها")
                return
            range_obj = selected_ranges[0]
            row = range_obj.topRow()
            column = range_obj.leftColumn()
            row_count = range_obj.rowCount()
            column_count = range_obj.columnCount()
            if row_count == 1 and column_count == 1:
                QMessageBox.warning(self, "تحذير", "لا يمكن دمج خلية واحدة")
                return
            text, ok = QInputDialog.getText(self, "إدخال محاضرة", "أدخل اسم المحاضرة المدمجة:", text="")
            if not ok or not text.strip():
                return
            color = QColorDialog.getColor()
            if not color.isValid():
                return
            self.table.setSpan(row, column, row_count, column_count)
            item = self.table.item(row, column)
            if not item:
                item = QTableWidgetItem()
                self.table.setItem(row, column, item)
            item.setText(text)
            item.setBackground(color)
            item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            day = self.days[row]
            start_time_display = self.hours[column]
            start_time_storage = self.normalize_time(start_time_display, for_display=False)
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            start_index = column
            end_index = column + column_count - 1
            times_to_delete = [self.normalize_time(self.hours[i], for_display=False) for i in range(start_index, end_index + 1)]
            cursor.execute('''
                DELETE FROM schedule 
                WHERE day = ? AND start_time IN ({seq}) AND user_id = ?
            '''.format(seq=','.join(['?']*len(times_to_delete))), [day] + times_to_delete + [self.user_id])
            cursor.execute('''
                INSERT INTO schedule (day, start_time, duration, name, color, row_span, col_span, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (day, start_time_storage, column_count, text, color.name(), row_count, column_count, self.user_id))
            conn.commit()
            conn.close()
            self.status_bar.showMessage("تم دمج الخلايا بنجاح", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء دمج الخلايا: {str(e)}")

    def unmerge_cells(self):
        try:
            selected_ranges = self.table.selectedRanges()
            if not selected_ranges:
                QMessageBox.warning(self, "تحذير", "الرجاء تحديد خلية مدمجة لإلغاء الدمج")
                return
            range_obj = selected_ranges[0]
            row = range_obj.topRow()
            column = range_obj.leftColumn()
            item = self.table.item(row, column)
            if not item or (self.table.rowSpan(row, column) == 1 and self.table.columnSpan(row, column) == 1):
                QMessageBox.warning(self, "تحذير", "الخلية المحددة ليست مدمجة")
                return
            row_span = self.table.rowSpan(row, column)
            col_span = self.table.columnSpan(row, column)
            self.table.setSpan(row, column, 1, 1)
            for i in range(row, row + row_span):
                for j in range(column, column + col_span):
                    if i != row or j != column:
                        cell_item = self.table.item(i, j)
                        if cell_item and cell_item.text() == "":
                            self.table.removeCellWidget(i, j)
            day = self.days[row]
            start_time = self.hours[column]
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM schedule WHERE day = ? AND start_time = ? AND user_id = ?',
                          (day, start_time, self.user_id))
            if item.text():
                cursor.execute('''
                    INSERT INTO schedule (day, start_time, duration, name, color, row_span, col_span, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (day, start_time, 1, item.text(), item.background().color().name(), 1, 1, self.user_id))
            conn.commit()
            conn.close()
            self.status_bar.showMessage("تم إلغاء الدمج بنجاح", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إلغاء الدمج: {str(e)}")

    def upload_pdf(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "اختر ملف PDF", "", "PDF Files (*.pdf)")
            if file_path:
                filename = os.path.basename(file_path)
                destination = os.path.join(UPLOAD_FOLDER, filename)
                shutil.copy(file_path, destination)
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                relative_path = os.path.join("Uploads", filename)
                cursor.execute(
                    'INSERT INTO files (filename, filepath, upload_date, user_id) VALUES (?, ?, CURRENT_TIMESTAMP, ?)',
                    (filename, relative_path, self.user_id))
                conn.commit()
                conn.close()
                self.status_bar.showMessage(f"تم رفع الملف {filename} بنجاح", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء رفع الملف: {str(e)}")

    def clear_files(self):
        try:
            reply = QMessageBox.question(
                self, "تأكيد المسح",
                "هل أنت متأكد أنك تريد مسح جميع الملفات؟ لن يمكن استعادتها!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                for filename in os.listdir(UPLOAD_FOLDER):
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM files WHERE user_id = ?', (self.user_id,))
                conn.commit()
                conn.close()
                self.status_bar.showMessage("تم مسح جميع الملفات بنجاح", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء مسح الملفات: {str(e)}")

    def edit_lecture(self, row, column):
        try:
            name, ok = QInputDialog.getText(self, "إدخال محاضرة", "أدخل اسم المحاضرة:", text="")
            if not ok or not name.strip():
                return
            color = QColorDialog.getColor()
            if not color.isValid():
                return
            day = self.days[row]
            start_time_display = self.hours[column]
            start_time_storage = self.normalize_time(start_time_display, for_display=False)
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM schedule 
                WHERE day = ? AND start_time = ? AND user_id = ?
            ''', (day, start_time_storage, self.user_id))
            cursor.execute('''
                INSERT INTO schedule (day, start_time, duration, name, color, row_span, col_span, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (day, start_time_storage, 1, name, color.name(), 1, 1, self.user_id))
            conn.commit()
            conn.close()
            item = self.table.item(row, column)
            if not item:
                item = QTableWidgetItem()
                self.table.setItem(row, column, item)
            item.setText(name)
            item.setBackground(color)
            item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            self.status_bar.showMessage("تم إضافة المحاضرة بنجاح", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إضافة المحاضرة: {str(e)}")

    def add_points_manually(self):
        try:
            points = int(self.points_input.text().strip())
            if points <= 0:
                self.status_bar.showMessage("من فضلك أدخل عددًا موجبًا", 3000)
                return
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO points_log (points, user_id, log_date) 
                VALUES (?, ?, datetime('now'))
            ''', (points, self.user_id))
            conn.commit()
            conn.close()
            self.points_input.clear()
            self.update_points()
            self.status_bar.showMessage(f"تم إضافة {points} نقاط بنجاح", 3000)
        except ValueError:
            self.status_bar.showMessage("أدخل رقمًا صحيحًا فقط", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إضافة النقاط: {str(e)}")

    def reset_points(self):
        try:
            reply = QMessageBox.question(
                self, "تأكيد إعادة التعيين",
                "هل أنت متأكد أنك تريد إعادة تعيين النقاط إلى الصفر؟",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                conn = sqlite3.connect(DATABASE)
                cursor = conn.cursor()
                cursor.execute('INSERT INTO points_log (points, user_id) VALUES (?, ?)', (0, self.user_id))
                conn.commit()
                conn.close()
                self.update_points()
                self.status_bar.showMessage("تم إعادة تعيين النقاط إلى الصفر", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إعادة تعيين النقاط: {str(e)}")

    def update_points(self):
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(points) FROM points_log WHERE user_id = ?', (self.user_id,))
            total_points = cursor.fetchone()[0] or 0
            cursor.execute('''
                SELECT points, log_date 
                FROM points_log 
                WHERE user_id = ? 
                ORDER BY log_date DESC 
                LIMIT 1
            ''', (self.user_id,))
            last_record = cursor.fetchone()
            if last_record:
                last_points = last_record[0]
                last_date = last_record[1]
                self.points_label.setText(f"نقاطك: {last_points} (آخر تحديث: {last_date})")
            else:
                self.points_label.setText(f"نقاطك: {total_points}")
            conn.close()
            self.check_weekly_status(total_points)
        except Exception as e:
            print(f"خطأ في تحديث النقاط: {e}")

    def check_weekly_status(self, total_points):
        current_time = datetime.now()
        if current_time.weekday() == 5 and current_time.hour == 0 and current_time.minute == 0:
            if total_points < 30:
                self.weekly_message.setText("مفيش خروج")
            else:
                self.weekly_message.setText("خروج عادي")

    def handle_task_click(self, item):
        pos = self.tasks_list.viewport().mapFromGlobal(self.cursor().pos())
        index = self.tasks_list.indexAt(pos)
        if not index.isValid():
            return
        item_rect = self.tasks_list.visualRect(index)
        delete_rect = item_rect.adjusted(item_rect.width() - 40, 0, -10, 0)
        if delete_rect.contains(pos):
            self.delete_task(item)
            return
        edit_rect = item_rect.adjusted(item_rect.width() - 80, 0, -50, 0)
        if edit_rect.contains(pos):
            self.edit_task(item)
            return
        self.toggle_task_status(item)

    def toggle_task_status(self, item):
        item.is_completed = not item.is_completed
        self.tasks_list.viewport().update()
        self.update_task_in_db(item)

    def edit_task(self, item):
        new_text, ok = QInputDialog.getText(self, "تعديل المهمة", "أدخل النص الجديد:", text=item.text())
        if ok and new_text:
            item.setText(new_text)
            self.tasks_list.viewport().update()
            self.update_task_in_db(item)

    def delete_task(self, item):
        row = self.tasks_list.row(item)
        self.tasks_list.takeItem(row)
        self.delete_task_from_db(item)

    def add_new_task(self):
        task_text = self.new_task_text.text().strip()
        if not task_text:
            QMessageBox.warning(self, "تحذير", "الرجاء إدخال نص للمهمة")
            return
        day = self.new_task_day.currentText()
        task_id = self.add_task_to_db(task_text, day)
        if task_id:
            item = TaskListWidgetItem(task_id, task_text, day)
            self.tasks_list.addItem(item)
            self.new_task_text.clear()

    def clear_completed_tasks(self):
        for i in range(self.tasks_list.count() - 1, -1, -1):
            item = self.tasks_list.item(i)
            if item and item.is_completed:
                self.tasks_list.takeItem(i)
                self.delete_task_from_db(item)

    def save_all_data(self):
        self.save_tasks_to_db()
        self.status_bar.showMessage("تم حفظ جميع التغييرات في قاعدة البيانات", 3000)

    def save_tasks_to_db(self):
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE user_id = ?', (self.user_id,))
            for i in range(self.tasks_list.count()):
                item = self.tasks_list.item(i)
                cursor.execute('''
                    INSERT INTO tasks (id, day, text, completed, user_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (item.task_id, item.day, item.text(), 1 if item.is_completed else 0, self.user_id))
            conn.commit()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء حفظ المهام: {str(e)}")

    def add_task_to_db(self, text, day):
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            valid_days = ["السبت", "الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "عام"]
            if day not in valid_days:
                day = "عام"
            cursor.execute('''
                INSERT INTO tasks (day, text, user_id) VALUES (?, ?, ?)
            ''', (day, text, self.user_id))
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return task_id
        except Exception as e:
            print(f"Error adding task to DB: {e}")
            return None

    def update_task_in_db(self, item):
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE tasks SET text = ?, completed = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?
            ''', (item.text(), 1 if item.is_completed else 0, item.task_id, self.user_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating task in DB: {e}")

    def delete_task_from_db(self, item):
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (item.task_id, self.user_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error deleting task from DB: {e}")

    def setup_timer(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_weekly_status)
        self.update_timer.start(60000)
        self.points_timer = QTimer()
        self.points_timer.timeout.connect(self.update_points)
        self.points_timer.start(300000)

    def update_date(self):
        today = QDate.currentDate()
        days = ["الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
        day_name = days[today.dayOfWeek() - 1]
        date_text = f"{day_name}، {today.toString('dd/MM/yyyy')}"
        self.date_label.setText(date_text)

    def load_data(self):
        try:
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM schedule WHERE user_id = ?', (self.user_id,))
            lectures = cursor.fetchall()
            self.table.clearSpans()
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if not item:
                        item = QTableWidgetItem()
                        self.table.setItem(row, col, item)
                    item.setText("")
                    item.setBackground(QColor(255, 255, 255))
            for lecture in lectures:
                try:
                    day = lecture[1]
                    start_time = self.normalize_time(lecture[2], for_display=True)
                    if start_time not in self.hours:
                        print(f"تحذير: الوقت {start_time} غير موجود في قائمة الساعات")
                        continue
                    name = lecture[4]
                    color = QColor(lecture[5])
                    row_span = lecture[6] or 1
                    col_span = lecture[7] or 1
                    day_index = self.days.index(day)
                    time_index = self.hours.index(start_time)
                    self.table.setSpan(day_index, time_index, row_span, col_span)
                    item = self.table.item(day_index, time_index)
                    if not item:
                        item = QTableWidgetItem()
                        self.table.setItem(day_index, time_index, item)
                    item.setText(name)
                    item.setBackground(color)
                    item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
                except ValueError as e:
                    print(f"تحذير: خطأ في تحميل المحاضرة - {e}")
                    continue
            cursor.execute('SELECT * FROM tasks WHERE user_id = ?', (self.user_id,))
            tasks = cursor.fetchall()
            self.tasks_list.clear()
            for task in tasks:
                task_id = task[0]
                day = task[1]
                text = task[2]
                completed = bool(task[3])
                item = TaskListWidgetItem(task_id, text, day, completed)
                self.tasks_list.addItem(item)
            conn.close()
            self.status_bar.showMessage("تم تحميل البيانات بنجاح", 3000)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"لا يمكن تحميل البيانات: {str(e)}")

if __name__ == '__main__':
    init_db()
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())