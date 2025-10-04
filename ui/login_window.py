from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                            QLineEdit, QPushButton, QCompleter, QMessageBox,
                            QLabel)
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtGui import QFont
from database.db import SessionLocal
from database.models import User
from .registration_window import RegistrationWindow
from datetime import datetime
import sys

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f6f7;
            }
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton#loginButton {
                background-color: #4a90e2;
                color: white;
                border: none;
            }
            QPushButton#loginButton:hover {
                background-color: #357abd;
            }
            QPushButton#registerButton {
                background-color: #f5f6f7;
                color: #4a90e2;
                border: 1px solid #4a90e2;
            }
            QPushButton#registerButton:hover {
                background-color: #e8e9ea;
            }
        """)

        # Создаем основной layout с отступами
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("Вход в систему")
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Поля ввода с подписями
        name_label = QLabel("ФИО:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Введите ФИО")
        self.setup_name_completer()

        password_label = QLabel("Пароль:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        layout.addWidget(name_label)
        layout.addWidget(self.name_input)
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)

        # Создаем кнопки с отступом между ними
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.login_button = QPushButton("Войти")
        self.login_button.setObjectName("loginButton")

        self.register_button = QPushButton("Создать пользователя")
        self.register_button.setObjectName("registerButton")

        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)

        layout.addLayout(button_layout)

        # Подключаем обработчики событий
        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.show_registration)

        # Загружаем последнего пользователя и устанавливаем фокус на поле пароля
        self.load_last_user()
        self.password_input.setFocus()

    def setup_name_completer(self):
        """Настройка автодополнения для поля ФИО"""
        db = SessionLocal()
        users = db.query(User.full_name).all()
        names = [user[0] for user in users]
        completer = QCompleter(names, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)  # Добавляем поиск по подстроке
        self.name_input.setCompleter(completer)
        db.close()

    def load_last_user(self):
        """Загрузка последнего успешно вошедшего пользователя"""
        try:
            with open("last_user.txt", "r") as f:
                last_user = f.read().strip()
                if last_user:
                    self.name_input.setText(last_user)
        except FileNotFoundError:
            pass

    def save_last_user(self, username):
        """Сохранение последнего успешно вошедшего пользователя"""
        with open("last_user.txt", "w") as f:
            f.write(username)

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Завершаем работу приложения
        QCoreApplication.quit()
        # Принудительно завершаем процесс
        sys.exit(0)
        event.accept()
    def login(self):
        """Обработка входа в систему"""
        full_name = self.name_input.text()
        password = self.password_input.text()

        if not full_name or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        db = SessionLocal()
        user = db.query(User).filter(User.full_name == full_name).first()

        if user and user.password == password:  # В реальном приложении нужно сравнивать хеши
            user.last_login = datetime.now()
            db.commit()
            self.save_last_user(full_name)
            db.close()
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные данные для входа")

        db.close()

    def show_registration(self):
        """Показ окна регистрации"""
        self.registration_window = RegistrationWindow()
        self.registration_window.show()