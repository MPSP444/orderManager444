from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit,
                             QPushButton, QMessageBox, QLabel)
from database.db import SessionLocal
from database.models import User
from .admin_confirm_dialog import AdminConfirmDialog


class RegistrationWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация нового пользователя")
        self.setMinimumWidth(300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Создаем поля ввода
        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("ФИО")

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Номер телефона")

        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Должность")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Создаем кнопку регистрации
        self.register_button = QPushButton("Зарегистрировать")

        # Добавляем виджеты на форму
        layout.addWidget(QLabel("ФИО:"))
        layout.addWidget(self.full_name_input)
        layout.addWidget(QLabel("Телефон:"))
        layout.addWidget(self.phone_input)
        layout.addWidget(QLabel("Должность:"))
        layout.addWidget(self.position_input)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.register_button)

        # Подключаем обработчик
        self.register_button.clicked.connect(self.register_user)

    def register_user(self):
        """Регистрация нового пользователя"""
        # Проверяем заполнение всех полей
        if not all([self.full_name_input.text(), self.phone_input.text(),
                    self.position_input.text(), self.password_input.text()]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        # Показываем диалог подтверждения админа
        admin_dialog = AdminConfirmDialog()
        if admin_dialog.exec_() == QDialog.Accepted:
            # Создаем нового пользователя
            db = SessionLocal()
            try:
                new_user = User(
                    full_name=self.full_name_input.text(),
                    phone=self.phone_input.text(),
                    position=self.position_input.text(),
                    password=self.password_input.text()  # В реальном приложении нужно хешировать
                )
                db.add(new_user)
                db.commit()
                QMessageBox.information(self, "Успех", "Пользователь успешно зарегистрирован")
                self.close()
            except Exception as e:
                db.rollback()
                QMessageBox.warning(self, "Ошибка", f"Ошибка при регистрации: {str(e)}")
            finally:
                db.close()