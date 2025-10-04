from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox,QWidget,QApplication,QStatusBar)
from PyQt5.QtCore import Qt
from core.database import init_database, Order
from PyQt5.QtCore import QTimer
DIALOG_STYLE = """
    QDialog {
        background-color: white;
        margin: 10px;
    }
    QLabel {
        color: #333333;
        font-size: 12px;
    }
    QPushButton {
        color: #333333;
        background-color: #e8e8e8;
        border: 1px solid #cccccc;
        padding: 5px 10px;
        border-radius: 3px;
        min-width: 30px;
    }
    QPushButton:hover {
        background-color: #d0d0d0;
        border: 1px solid #999999;
    }
    QGroupBox {
        color: #2196F3;
        font-weight: bold;
        font-size: 13px;
        padding-top: 15px;
        margin-top: 10px;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        background-color: white;
    }
"""
class OrderInfoWindow(QDialog):
    def __init__(self, parent=None, order=None):
        super().__init__(parent)
        self.order = order
        self.status_label = None  # Добавляем атрибут для статуса
        self.initUI()

    def create_info_row(self, label_text, value, copy_enabled=True):
        """Создание строки с информацией и кнопкой копирования"""
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(5, 2, 5, 2)  # Добавляем отступы
        layout.setSpacing(10)  # Увеличиваем расстояние между элементами

        # Метка
        label = QLabel(f"{label_text}:")
        label.setMinimumWidth(150)
        label.setStyleSheet("color: #666666; font-weight: bold;")  # Делаем метки более заметными
        layout.addWidget(label)

        # Значение
        value_label = QLabel(str(value))
        value_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        value_label.setStyleSheet("color: #333333;")  # Темный цвет для значений
        layout.addWidget(value_label)

        if copy_enabled:
            # Кнопка копирования
            copy_btn = QPushButton("📋")
            copy_btn.setToolTip("Копировать")
            copy_btn.setMinimumWidth(40)  # Увеличиваем ширину кнопки
            copy_btn.setMinimumHeight(25)  # Увеличиваем высоту кнопки
            copy_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 3px;
                    color: #333333;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                }
            """)
            copy_btn.clicked.connect(lambda: self.copy_to_clipboard(str(value)))
            layout.addWidget(copy_btn)
        else:
            layout.addSpacing(40)

        layout.addStretch()
        return row_widget
    def copy_to_clipboard(self, text):
        """Копирование текста в буфер обмена"""
        QApplication.clipboard().setText(text)
        # Показываем сообщение в статус-лейбле
        self.show_status_message("Скопировано в буфер обмена")

    def show_status_message(self, message, timeout=2000):
        """Показ временного сообщения"""
        self.status_label.setText(message)
        # Сбрасываем текст через timeout миллисекунд
        QTimer.singleShot(timeout, lambda: self.status_label.setText(""))

    def initUI(self):
        self.setWindowTitle(f"Информация о заказе №{self.order.id}")
        self.setGeometry(300, 300, 600, 400)

        # Определяем стили заранее
        BUTTON_STYLE = """
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """

        STATUS_LABEL_STYLE = """
            QLabel {
                color: #2196F3;
                padding: 5px;
                font-weight: bold;
            }
        """

        # Создаем основной layout
        layout = QVBoxLayout(self)

        # 1. Создаем основную группу
        main_group = QGroupBox("Основная информация")
        main_layout = QVBoxLayout()

        main_layout.addWidget(self.create_info_row("ФИО клиента", self.order.fio))
        main_layout.addWidget(self.create_info_row("Группа", self.order.group))
        main_layout.addWidget(self.create_info_row("Телефон", self.order.phone or 'Не указан'))
        main_layout.addWidget(self.create_info_row("Услуга", self.order.service))
        main_layout.addWidget(self.create_info_row("Тема", self.order.theme or 'Не указана'))
        main_layout.addWidget(self.create_info_row("Направление", self.order.direction or 'Не указано'))
        main_layout.addWidget(self.create_info_row("Количество", self.order.quantity))

        main_group.setLayout(main_layout)

        # 2. Создаем группу финансов
        finance_group = QGroupBox("Финансовая информация")
        finance_layout = QVBoxLayout()

        finance_layout.addWidget(self.create_info_row("Стоимость", f"{self.order.cost} руб."))
        finance_layout.addWidget(self.create_info_row("Оплачено", f"{self.order.paid_amount} руб."))
        finance_layout.addWidget(self.create_info_row("Остаток", f"{self.order.remaining_amount} руб."))
        finance_layout.addWidget(self.create_info_row("Скидка", self.order.discount or '0%'))

        finance_group.setLayout(finance_layout)

        # 3. Создаем группу учетных данных
        access_group = QGroupBox("Учетные данные")
        access_layout = QVBoxLayout()

        access_layout.addWidget(self.create_info_row("Логин", self.order.login or 'Не указан'))
        access_layout.addWidget(self.create_info_row("Пароль", self.order.password or 'Не указан'))
        access_layout.addWidget(self.create_info_row("Сайт", self.order.website or 'Не указан'))

        access_group.setLayout(access_layout)

        # 4. Создаем кнопки
        copy_all_btn = QPushButton("📋 Копировать всё")
        copy_all_btn.clicked.connect(self.copy_all_data)
        copy_all_btn.setMinimumHeight(30)
        copy_all_btn.setStyleSheet(BUTTON_STYLE)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setMinimumHeight(30)
        close_btn.setStyleSheet(BUTTON_STYLE)

        # 5. Создаем статус лейбл
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(STATUS_LABEL_STYLE)

        # 6. Настраиваем отступы для групп
        for group in [main_group, finance_group, access_group]:
            group.layout().setSpacing(8)
            group.layout().setContentsMargins(10, 15, 10, 10)

        # 7. Добавляем все элементы в основной layout
        layout.addWidget(main_group)
        layout.addWidget(finance_group)
        layout.addWidget(access_group)
        layout.addWidget(self.status_label)

        # Добавляем кнопки в отдельный layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(copy_all_btn)
        buttons_layout.addWidget(close_btn)
        layout.addLayout(buttons_layout)

        # Настраиваем отступы основного layout
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

    def copy_all_data(self):
        """Копирование всех данных заказа"""
        all_info = f"""Информация о заказе №{self.order.id}

Основная информация:
ФИО: {self.order.fio}
Группа: {self.order.group}
Телефон: {self.order.phone or 'Не указан'}
Услуга: {self.order.service}
Тема: {self.order.theme or 'Не указана'}
Направление: {self.order.direction or 'Не указано'}
Количество: {self.order.quantity}

Финансовая информация:
Стоимость: {self.order.cost} руб.
Оплачено: {self.order.paid_amount} руб.
Остаток: {self.order.remaining_amount} руб.
Скидка: {self.order.discount or '0%'}

Учетные данные:
Логин: {self.order.login or 'Не указан'}
Пароль: {self.order.password or 'Не указан'}
Сайт: {self.order.website or 'Не указан'}"""

        self.copy_to_clipboard(all_info)
