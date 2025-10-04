from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLineEdit,
                             QPushButton, QMessageBox, QLabel)
from database.db import SessionLocal
from database.models import User
from PyQt5.QtGui import QIcon

class AdminConfirmDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Подтверждение администратора")
        self.setMinimumWidth(250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Создаем поля ввода
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин администратора")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль администратора")
        self.password_input.setEchoMode(QLineEdit.Password)

        # Создаем кнопку подтверждения
        self.confirm_button = QPushButton("Подтвердить")

        # Добавляем виджеты на форму
        layout.addWidget(QLabel("Логин администратора:"))
        layout.addWidget(self.login_input)
        layout.addWidget(QLabel("Пароль администратора:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_button)

        # Подключаем обработчик
        self.confirm_button.clicked.connect(self.verify_admin)

    def verify_admin(self):
        """Проверка учетных данных администратора"""
        login = self.login_input.text()
        password = self.password_input.text()

        if not login or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        db = SessionLocal()
        admin = db.query(User).filter(
            User.full_name == login,
            User.password == password,  # В реальном приложении нужно сравнивать хеши
            User.is_admin == True
        ).first()

        db.close()

        if admin:
            self.accept()  # Закрываем диалог с положительным результатом
        else:
            error_text = (
                "Неверные данные для входа!\n\n"
                "Для получения доступа обратитесь к администратору:\n"
                "• Гурбанмурадов Мукам (ООО MPSP)\n\n"
                "Контакты:\n"
                "• ВКонтакте: Gurbanmyradov99\n"
                "• WhatsApp: +79066322571"
            )

            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Ошибка авторизации")
            msg.setText(error_text)
            msg.setStyleSheet("""
                    QMessageBox {
                        background-color: #f5f6f7;
                    }
                    QLabel {
                        min-width: 400px;
                        font-size: 13px;
                    }
                    QPushButton {
                        padding: 6px 20px;
                        border-radius: 4px;
                        background-color: #4a90e2;
                        color: white;
                        border: none;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #357abd;
                    }
                """)
            msg.exec_()