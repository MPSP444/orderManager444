from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTableWidget, QTableWidgetItem, QComboBox,
                             QCheckBox, QProgressBar, QTextEdit, QMessageBox,
                             QHeaderView, QSpinBox, QFrame, QListWidget,
                             QLineEdit, QRadioButton, QApplication)
from PyQt5.QtCore import Qt, QTimer, QSettings, QUrl
from PyQt5.QtGui import QColor, QDesktopServices
from datetime import datetime, timedelta, date  # Добавили импорт date
import re
from urllib.parse import quote

from core.database_manager import DatabaseManager
from core.database import Order
from ..message_utils import show_error, show_warning
import uuid
import uuid
import urllib.parse
from reviews_manager.config import SITE_CONFIG
import requests

class MessageTemplateManager:
    """Менеджер шаблонов сообщений"""

    def __init__(self):
        self.settings = QSettings('MPSP', 'MessageTemplates')

    def save_template(self, name, text):
        """Сохранение шаблона"""
        templates = self.settings.value('templates', {})
        if isinstance(templates, dict):
            templates[name] = text
            self.settings.setValue('templates', templates)
            self.settings.sync()

    def get_templates(self):
        """Получение всех шаблонов"""
        templates = self.settings.value('templates', {})
        return templates if isinstance(templates, dict) else {}

    def delete_template(self, name):
        """Удаление шаблона"""
        templates = self.settings.value('templates', {})
        if isinstance(templates, dict) and name in templates:
            del templates[name]
            self.settings.setValue('templates', templates)
            self.settings.sync()


class MessageVariablesHelpDialog(QDialog):
    """Диалоговое окно с информацией о доступных переменных для шаблонов сообщений"""

    def __init__(self, parent=None, view_mode='orders'):
        super().__init__(parent)
        self.view_mode = view_mode
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Помощник по переменным шаблона")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        # Заголовок
        title_label = QLabel("Доступные переменные для шаблона сообщения")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Пояснительный текст
        info_label = QLabel(
            "Используйте эти переменные в тексте шаблона. "
            "При отправке сообщения они будут заменены на соответствующие значения."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Таблица с переменными
        self.variables_table = QTableWidget()
        self.variables_table.setColumnCount(3)
        self.variables_table.setHorizontalHeaderLabels(["Переменная", "Описание", "Пример"])

        # Настройка таблицы
        self.variables_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.variables_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.variables_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)

        self.variables_table.setColumnWidth(0, 200)
        self.variables_table.setColumnWidth(2, 200)

        # Стилизация таблицы
        self.variables_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)

        # Заполняем таблицу в зависимости от режима
        self.fill_variables_table()

        layout.addWidget(self.variables_table)

        # Кнопка "Копировать в буфер обмена"
        copy_row = QHBoxLayout()
        copy_all_btn = QPushButton("📋 Копировать все переменные")
        copy_all_btn.clicked.connect(self.copy_all_variables)
        copy_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        copy_selected_btn = QPushButton("📋 Копировать выбранную")
        copy_selected_btn.clicked.connect(self.copy_selected_variable)
        copy_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)

        copy_row.addWidget(copy_selected_btn)
        copy_row.addWidget(copy_all_btn)
        layout.addLayout(copy_row)

        # Кнопка "Закрыть"
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)

        layout.addWidget(close_btn)

    def fill_variables_table(self):
        """Заполнение таблицы переменными в зависимости от режима отображения"""
        # Общие переменные для обоих режимов
        common_variables = [
            ["{client_name}", "ФИО клиента", "Иванов Иван Иванович"],
            ["{phone}", "Номер телефона клиента", "+7 (999) 123-45-67"],
            ["{days_waiting}", "Количество дней ожидания оплаты", "30"]
        ]

        # Переменные для режима "По заказам"
        order_variables = [
            ["{order_id}", "Номер заказа", "1234"],
            ["{service}", "Название услуги", "Дипломная работа"],
            ["{direction}", "Направление", "Экономика"],
            ["{theme}", "Тема работы", "Анализ экономической эффективности"],
            ["{created_date}", "Дата создания заказа", "01.01.2024"],
            ["{amount}", "Сумма к оплате", "5000.00 ₽"],
            ["{discount}", "Текущая скидка", "10%"],
            ["{discount_start_date}", "Дата начала скидки", "01.01.2024"],
            ["{discount_end_date}", "Дата окончания скидки", "05.01.2024"],
            ["{deadline}", "Срок сдачи", "10 дней"],
            ["{status}", "Статус заказа", "В ожидании оплаты"],
            ["{teacher_name}", "ФИО преподавателя", "Петров П.П."],
            ["{discounted_amount}", "Сумма со скидкой", "4500.00 ₽"]
        ]

        # Переменные для режима "По клиентам"
        client_variables = [
            ["{total_orders}", "Общее количество заказов клиента", "5"],
            ["{waiting_orders}", "Количество заказов в ожидании оплаты", "2"],
            ["{total_amount}", "Общая сумма к оплате", "12000.00 ₽"],
            ["{earliest_date}", "Дата первого заказа", "01.01.2024"],
            ["{latest_date}", "Дата последнего заказа", "15.03.2024"]
        ]

        # Определяем, какие переменные показывать
        variables_to_show = common_variables[:]
        if self.view_mode == 'orders':
            variables_to_show.extend(order_variables)
        else:
            variables_to_show.extend(client_variables)

        # Заполняем таблицу
        self.variables_table.setRowCount(len(variables_to_show))
        for row, (variable, description, example) in enumerate(variables_to_show):
            # Переменная
            var_item = QTableWidgetItem(variable)
            var_item.setTextAlignment(Qt.AlignCenter)
            self.variables_table.setItem(row, 0, var_item)

            # Описание
            desc_item = QTableWidgetItem(description)
            self.variables_table.setItem(row, 1, desc_item)

            # Пример
            example_item = QTableWidgetItem(example)
            example_item.setTextAlignment(Qt.AlignCenter)
            self.variables_table.setItem(row, 2, example_item)

    def copy_all_variables(self):
        """Копирование всех переменных в буфер обмена"""
        variables = []
        for row in range(self.variables_table.rowCount()):
            variables.append(self.variables_table.item(row, 0).text())

        text = "\n".join(variables)
        QApplication.clipboard().setText(text)

        QMessageBox.information(
            self,
            "Копирование",
            "Все переменные скопированы в буфер обмена!"
        )

    def copy_selected_variable(self):
        """Копирование выбранной переменной в буфер обмена"""
        selected_items = self.variables_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Сначала выберите переменную в таблице!"
            )
            return

        # Получаем ряд первого выбранного элемента
        row = selected_items[0].row()
        variable = self.variables_table.item(row, 0).text()

        QApplication.clipboard().setText(variable)

        QMessageBox.information(
            self,
            "Копирование",
            f"Переменная {variable} скопирована в буфер обмена!"
        )

class ReminderHistory:
    """Менеджер истории напоминаний"""

    def __init__(self):
        self.settings = QSettings('MPSP', 'ReminderHistory')

    def add_reminder(self, client_fio, order_id):
        """Добавление записи о напоминании"""
        history = self.settings.value('history', {})
        if not isinstance(history, dict):
            history = {}

        if client_fio not in history:
            history[client_fio] = []

        history[client_fio].append({
            'order_id': order_id,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        self.settings.setValue('history', history)
        self.settings.sync()

    def get_last_reminder(self, client_fio):
        """Получение даты последнего напоминания"""
        history = self.settings.value('history', {})
        if not isinstance(history, dict):
            return None

        if client_fio not in history or not history[client_fio]:
            return None

        last_reminder = history[client_fio][-1]
        return datetime.strptime(last_reminder['date'], '%Y-%m-%d %H:%M:%S')

    def can_send_reminder(self, client_fio):
        """Проверка возможности отправки напоминания"""
        last_reminder = self.get_last_reminder(client_fio)
        if not last_reminder:
            return True

        return (datetime.now() - last_reminder) > timedelta(days=30)


class TemplateManagerDialog(QDialog):
    """Диалог управления шаблонами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.template_manager = MessageTemplateManager()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Управление шаблонами")
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)

        # Список шаблонов
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self.template_selected)
        layout.addWidget(QLabel("Шаблоны:"))
        layout.addWidget(self.template_list)

        # Редактор шаблона
        self.name_edit = QLineEdit()
        self.text_edit = QTextEdit()

        layout.addWidget(QLabel("Название:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Текст:"))
        layout.addWidget(self.text_edit)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self.save_template)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #3d8b40;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.clicked.connect(self.delete_template)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: 1px solid #3d8b40;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # Загружаем существующие шаблоны
        self.load_templates()

    def load_templates(self):
        """Загрузка существующих шаблонов"""
        self.template_list.clear()
        templates = self.template_manager.get_templates()
        for name in templates.keys():
            self.template_list.addItem(name)

    def template_selected(self, current, previous):
        """Обработка выбора шаблона"""
        if current:
            name = current.text()
            templates = self.template_manager.get_templates()
            if name in templates:
                self.name_edit.setText(name)
                self.text_edit.setPlainText(templates[name])

    def save_template(self):
        """Сохранение шаблона"""
        name = self.name_edit.text().strip()
        text = self.text_edit.toPlainText().strip()

        if not name or not text:
            show_warning(self, "Предупреждение",
                         "Необходимо указать название и текст шаблона!")
            return

        self.template_manager.save_template(name, text)
        self.load_templates()

        # Показываем сообщение об успешном сохранении
        QMessageBox.information(self, "Успешно", "Шаблон успешно сохранен!")

        # Устанавливаем результат диалога в Accepted
        self.accept()  # Это важно для правильной работы обновления в главном окне
    def delete_template(self):
        """Удаление шаблона"""
        current = self.template_list.currentItem()
        if current:
            name = current.text()
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Удалить шаблон '{name}'?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.template_manager.delete_template(name)
                self.load_templates()
                self.name_edit.clear()
                self.text_edit.clear()

                # Показываем сообщение об успешном удалении
                QMessageBox.information(self, "Успешно", "Шаблон успешно удален!")
        else:
            show_warning(self, "Предупреждение", "Выберите шаблон для удаления!")


class ReminderHistoryDialog(QDialog):
    """Диалог просмотра истории напоминаний"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reminder_history = ReminderHistory()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("История напоминаний")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Таблица истории
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Клиент", "Заказ", "Дата напоминания", "Следующее возможное"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)

        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 150)

        # Стилизация таблицы
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 6px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)

        layout.addWidget(self.table)

        # Кнопки
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.load_history)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        clear_btn = QPushButton("🗑️ Очистить историю")
        clear_btn.clicked.connect(self.clear_history)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)

        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        # Загружаем историю
        self.load_history()

    def load_history(self):
        """Загрузка истории напоминаний"""
        try:
            history = self.reminder_history.settings.value('history', {})
            if not isinstance(history, dict):
                history = {}

            self.table.setRowCount(0)
            row = 0

            for client, reminders in history.items():
                for reminder in reminders:
                    self.table.insertRow(row)

                    # Клиент
                    self.table.setItem(row, 0, QTableWidgetItem(client))

                    # ID заказа
                    order_id = reminder.get('order_id', 'Н/Д')
                    self.table.setItem(row, 1, QTableWidgetItem(str(order_id)))

                    # Дата напоминания
                    reminder_date = datetime.strptime(
                        reminder['date'], '%Y-%m-%d %H:%M:%S'
                    )
                    next_date = reminder_date + timedelta(days=30)

                    date_item = QTableWidgetItem(
                        reminder_date.strftime('%d.%m.%Y %H:%M')
                    )
                    next_date_item = QTableWidgetItem(
                        next_date.strftime('%d.%m.%Y %H:%M')
                    )

                    # Подсветка дат
                    if datetime.now() < next_date:
                        next_date_item.setBackground(QColor("#ffebee"))  # Красный
                    else:
                        next_date_item.setBackground(QColor("#e8f5e9"))  # Зеленый

                    self.table.setItem(row, 2, date_item)
                    self.table.setItem(row, 3, next_date_item)

                    row += 1

            # Сортировка по дате (по убыванию)
            self.table.sortItems(2, Qt.DescendingOrder)

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при загрузке истории: {str(e)}")

    def clear_history(self):
        """Очистка истории напоминаний"""
        try:
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Вы уверены, что хотите очистить всю историю напоминаний?\n"
                "Это действие нельзя будет отменить.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.reminder_history.settings.remove('history')
                self.reminder_history.settings.sync()
                self.load_history()
                QMessageBox.information(self, "Успешно",
                                        "История напоминаний очищена!")

        except Exception as e:
            show_error(self, "Ошибка",
                       f"Ошибка при очистке истории: {str(e)}")

class MassMessagingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.template_manager = MessageTemplateManager()
        self.reminder_history = ReminderHistory()
        self.selected_orders = []
        self.view_mode = 'orders'  # По умолчанию - режим заказов
        self.setup_ui()
        self.load_orders()
        self.load_templates()

    def setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Массовая рассылка сообщений")
        self.setMinimumSize(1200, 800)

        layout = QVBoxLayout(self)

        # Верхняя панель с фильтрами и режимами отображения
        filter_frame = self.create_filter_panel()
        layout.addWidget(filter_frame)

        # Таблица заказов
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)

        # Панель сообщения
        message_frame = self.create_message_panel()
        layout.addWidget(message_frame)

        # Нижняя панель с кнопками
        buttons_frame = self.create_buttons_panel()
        layout.addWidget(buttons_frame)


    def create_filter_panel(self):
        """Создание панели с фильтрами и режимами отображения"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(frame)

        # Верхний ряд с режимами отображения и периодом
        top_row = QHBoxLayout()

        # Радио-кнопки для выбора режима
        mode_group = QHBoxLayout()
        self.orders_radio = QRadioButton("По заказам")
        self.clients_radio = QRadioButton("По клиентам")
        self.reviews_radio = QRadioButton("Для отзывов")  # Новый радиобаттон
        self.orders_radio.setChecked(True)

        # Стилизация радио-кнопок
        radio_style = """
            QRadioButton {
                background-color: transparent;
                padding: 5px;
                border-radius: 4px;
                font-size: 14px;
            }
            QRadioButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.orders_radio.setStyleSheet(radio_style)
        self.clients_radio.setStyleSheet(radio_style)
        self.reviews_radio.setStyleSheet(radio_style)  # Стиль для нового радиобаттона

        self.orders_radio.toggled.connect(self.on_view_mode_changed)
        self.clients_radio.toggled.connect(self.on_view_mode_changed)
        self.reviews_radio.toggled.connect(self.on_view_mode_changed)  # Подключаем обработчик

        mode_group.addWidget(QLabel("Режим отображения:"))
        mode_group.addWidget(self.orders_radio)
        mode_group.addWidget(self.clients_radio)
        mode_group.addWidget(self.reviews_radio)  # Добавляем новый радиобаттон
        mode_group.addStretch()

        # Фильтр по периоду
        period_layout = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Все заказы",
            "Более 6 месяцев",
            "3-6 месяцев",
            "1-3 месяца",
            "Последний месяц"
        ])
        self.period_combo.currentIndexChanged.connect(self.filter_orders)
        period_layout.addWidget(QLabel("Период:"))
        period_layout.addWidget(self.period_combo)

        # Добавляем верхний ряд
        top_row.addLayout(mode_group)
        top_row.addLayout(period_layout)
        top_row.addStretch()

        # Второй ряд с дополнительными фильтрами
        middle_row = QHBoxLayout()

        # Фильтр по статусу
        status_layout = QHBoxLayout()
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Все статусы",
            "В ожидании оплаты",
            "Новый",
            "В работе",
            "Выполнен",
            "Отменен"
        ])
        self.status_combo.currentIndexChanged.connect(self.filter_orders)
        status_layout.addWidget(QLabel("Статус:"))
        status_layout.addWidget(self.status_combo)

        # Фильтр по полу
        gender_layout = QHBoxLayout()
        self.gender_combo = QComboBox()
        self.gender_combo.addItems([
            "Все клиенты",
            "Мужчины",
            "Женщины"
        ])
        self.gender_combo.currentIndexChanged.connect(self.filter_orders)
        gender_layout.addWidget(QLabel("Пол:"))
        gender_layout.addWidget(self.gender_combo)

        # Добавляем второй ряд
        middle_row.addLayout(status_layout)
        middle_row.addLayout(gender_layout)
        middle_row.addStretch()

        # Третий ряд с кнопками
        button_row = QHBoxLayout()

        # Кнопка истории
        history_btn = QPushButton("📅 История напоминаний")
        history_btn.clicked.connect(self.show_history)
        history_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.load_orders)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        button_row.addStretch()
        button_row.addWidget(history_btn)
        button_row.addWidget(refresh_btn)

        # Добавляем все ряды в основной макет
        layout.addLayout(top_row)
        layout.addLayout(middle_row)
        layout.addLayout(button_row)

        return frame

    # 2. Обновляем метод on_view_mode_changed для обработки нового режима

    def on_view_mode_changed(self):
        """Обработчик изменения режима отображения"""
        old_mode = self.view_mode

        if self.orders_radio.isChecked():
            self.view_mode = 'orders'
        elif self.clients_radio.isChecked():
            self.view_mode = 'clients'
        else:
            self.view_mode = 'reviews'  # Новый режим для отзывов

        self.load_orders()
        self.update_message_template()

        # При переключении в режим отзывов, выбираем соответствующий шаблон
        if self.view_mode == 'reviews' and old_mode != 'reviews':
            review_template_index = self.template_combo.findText("Запрос отзыва")
            if review_template_index >= 0:
                self.template_combo.setCurrentIndex(review_template_index)
                self.load_message_template()

    # 3. Обновляем метод load_orders для поддержки нового режима

    def load_orders(self):
        """Загрузка данных в зависимости от выбранного режима"""
        try:
            self.table.setRowCount(0)
            self.table.setSortingEnabled(False)  # Отключаем сортировку на время загрузки

            # Сбрасываем счетчик выбранных записей
            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText("Выбрано: 0")

            # Определяем статус для фильтрации
            status_filter = self.status_combo.currentText()
            status_condition = None if status_filter == "Все статусы" else status_filter

            with self.db_manager.session_scope() as session:
                # Запрос заказов в зависимости от фильтра статуса
                query = session.query(Order)

                if status_condition:
                    query = query.filter(Order.status == status_condition)

                # В режиме отзывов исключаем отмененные заказы
                if self.view_mode == 'reviews':
                    query = query.filter(Order.status != 'Отменен')

                orders = query.order_by(Order.created_date.desc()).all()

                if self.view_mode == 'orders':
                    self.load_orders_view(orders)
                elif self.view_mode == 'clients':
                    self.load_clients_view(orders)
                else:
                    self.load_reviews_view(orders)  # Новый метод для загрузки в режиме отзывов

            self.table.setSortingEnabled(True)  # Включаем сортировку обратно
            self.filter_orders()  # Применяем дополнительные фильтры (период, пол)
            self.reload_table_checkboxes()
        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")

    def load_reviews_view(self, orders):
        """Загрузка данных в режиме отображения для отзывов"""
        self.table.setHorizontalHeaderLabels([
            "", "Всего заказов", "Клиент", "Кол-во услуг", "Макс. сумма",
            "Дата первого заказа", "Дней с нами", "Телефон", "Услуги", "Предлагали отзыв"
        ])

        current_date = datetime.now()

        # Группируем заказы по клиентам и проверяем наличие сгенерированных ссылок
        clients_data = {}
        clients_with_review_links = set()

        try:
            with self.db_manager.session_scope() as session:
                # Сначала собираем клиентов, которые уже имеют сгенерированную ссылку для отзыва
                clients_with_links_query = session.query(Order.fio.distinct()).filter(
                    Order.review_token.isnot(None),
                    Order.review_token != ''
                )

                for client_row in clients_with_links_query:
                    clients_with_review_links.add(client_row[0])

                print(f"Клиенты с существующими ссылками для отзывов: {len(clients_with_review_links)}")

                # Получаем список всех уникальных клиентов
                unique_clients_query = session.query(Order.fio.distinct()).filter(
                    Order.status != 'Отменен'
                )

                print("Загружаем уникальных клиентов")
                unique_clients = [row[0] for row in unique_clients_query if row[0] not in clients_with_review_links]
                print(f"Загружено {len(unique_clients)} уникальных клиентов")

                # Обрабатываем каждого клиента без ссылок
                for client_fio in unique_clients:
                    # Получаем все заказы клиента (кроме отмененных)
                    client_orders = session.query(Order).filter(
                        Order.fio == client_fio,
                        Order.status != 'Отменен'
                    ).all()

                    # Если нет активных заказов, пропускаем
                    if not client_orders:
                        continue

                    # Подсчитываем уникальные услуги
                    unique_services = set()
                    for co in client_orders:
                        if co.service:
                            unique_services.add(co.service)

                    # Находим заказ с максимальной оплатой
                    max_payment = 0
                    max_payment_order = None

                    for co in client_orders:
                        payment = self.safe_float(co.paid_amount)
                        if payment > max_payment:
                            max_payment = payment
                            max_payment_order = co

                    # Если нет заказов с оплатой, берем первый заказ
                    if not max_payment_order and client_orders:
                        max_payment_order = client_orders[0]
                        max_payment = self.safe_float(max_payment_order.cost)

                    # Находим самый ранний заказ для даты начала сотрудничества
                    earliest_date = None
                    for co in client_orders:
                        if co.created_date:
                            if not earliest_date or co.created_date < earliest_date:
                                earliest_date = co.created_date

                    # Если дата отсутствует, используем текущую дату
                    if not earliest_date:
                        earliest_date = datetime.now().date()

                    # Унифицируем работу с датами - приводим к datetime
                    if isinstance(earliest_date, date):
                        earliest_datetime = datetime.combine(earliest_date, datetime.min.time())
                    else:
                        earliest_datetime = earliest_date

                    # Корректный расчет дней между датами
                    days_with_us = (current_date - earliest_datetime).days

                    # Форматируем дату для отображения
                    date_formatted = earliest_datetime.strftime('%d.%m.%Y')

                    # Создаем строку с услугами
                    services_list = list(unique_services)
                    services_text = ", ".join(services_list[:3])
                    if len(services_list) > 3:
                        services_text += f" и еще {len(services_list) - 3}"

                    # Инициализируем данные клиента
                    clients_data[client_fio] = {
                        'total_orders': len(client_orders),
                        'unique_services': len(unique_services) if unique_services else 1,
                        'max_payment': max_payment if max_payment else 0,
                        'max_payment_order': max_payment_order,
                        'phone': max_payment_order.phone if max_payment_order and max_payment_order.phone else "",
                        'earliest_date': earliest_datetime,
                        'earliest_date_formatted': date_formatted,
                        'days_with_us': days_with_us,
                        'services': services_text or "Не указаны",
                        'all_orders': client_orders  # Сохраняем все заказы для последующего использования
                    }

                # Заполняем таблицу
                row = 0
                for client, data in clients_data.items():
                    # Проверяем наличие данных для отображения
                    if client and data:
                        self.table.insertRow(row)

                        # Создаем чекбокс с явной привязкой к строке
                        checkbox = QCheckBox()
                        checkbox.setChecked(False)
                        checkbox.setEnabled(True)
                        # Используем лямбда-функцию для передачи номера строки в обработчик
                        checkbox.stateChanged.connect(
                            lambda state, r=row: self.on_checkbox_state_changed_reviews(state, r))
                        self.table.setCellWidget(row, 0, checkbox)

                        # Данные клиента
                        self.table.setItem(row, 1, QTableWidgetItem(str(data['total_orders'])))
                        self.table.setItem(row, 2, QTableWidgetItem(client))
                        self.table.setItem(row, 3, QTableWidgetItem(str(data['unique_services'])))
                        self.table.setItem(row, 4, QTableWidgetItem(f"{data['max_payment']:,.2f} ₽"))

                        # Дата первого заказа - используем отформатированную дату
                        self.table.setItem(row, 5, QTableWidgetItem(data['earliest_date_formatted']))

                        # Дней с нами - используем предварительно рассчитанное значение
                        days_item = QTableWidgetItem(str(data['days_with_us']))
                        self.set_days_color(days_item, data['days_with_us'])
                        self.table.setItem(row, 6, days_item)

                        # Телефон
                        self.table.setItem(row, 7, QTableWidgetItem(data['phone'] or ""))

                        # Услуги клиента
                        self.table.setItem(row, 8, QTableWidgetItem(data['services']))

                        # Статус отзыва
                        self.table.setItem(row, 9, QTableWidgetItem("Не предлагали"))

                        row += 1

                print(f"Показано клиентов в таблице: {row} из {len(clients_data)}")

        except Exception as e:
            import traceback
            traceback.print_exc()  # Печатаем полное сообщение об ошибке
            show_error(self, "Ошибка", f"Ошибка при загрузке данных для отзывов: {str(e)}")

    def on_checkbox_state_changed_reviews(self, state, row):
        """Обработчик изменения состояния чекбокса в режиме отзывов"""
        # Обновляем счетчик выбранных записей
        self.update_selected_count()
        print(f"Изменено состояние чекбокса в строке {row} на {state}")


    def safe_float(self, value):
        """Безопасное преобразование в float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                if value.strip() == "Не указано":
                    return 0.0
                # Удаляем запятые и другие символы форматирования
                return float(value.replace(',', '.').replace(' ', '').replace('₽', ''))
            return 0.0
        except (ValueError, TypeError, AttributeError):
            return 0.0

    def load_templates(self):
        """Загрузка списка шаблонов"""
        current_text = self.template_combo.currentText()  # Сохраняем текущий выбор
        self.template_combo.clear()

        # Стандартные шаблоны с примерами
        standard_templates = {
            "Стандартное напоминание": (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть заказ #{order_id} от {created_date} - {service}.\n"
                "Хотели уточнить, актуален ли еще данный заказ?\n\n"
                "Если да, то напоминаем о необходимости внесения оплаты.\n"
                "Сумма к оплате: {amount} ₽\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            ),
            "Короткое напоминание": (
                "Здравствуйте, {client_name}!\n"
                "Напоминаем о заказе #{order_id} - {service}.\n"
                "Сумма к оплате: {amount} ₽\n"
                "Для оплаты: +79066322571"
            ),
            "Предложение скидки": (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть неоплаченный заказ #{order_id} - {service}.\n"
                "Предлагаем специальные условия при оплате в течение 3 дней:\n"
                "- Скидка 10%\n"
                "- Сумма к оплате со скидкой: {amount} ₽\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            ),
            "Групповое напоминание": (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть {total_orders} неоплаченных заказов на общую сумму {total_amount} ₽.\n"
                "Хотели бы уточнить, актуальны ли еще ваши заказы?\n\n"
                "Пожалуйста, не игнорируйте это сообщение! "
                "Нам важно знать ваше решение по заказам.\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            ),
            "Вежливое напоминание": (
                "Добрый день, {client_name}!\n\n"
                "Мы заметили, что заказ #{order_id} ({service}) от {created_date} "
                "все еще ожидает оплаты.\n\n"
                "Сумма к оплате: {amount} ₽\n\n"
                "Если у вас возникли какие-либо вопросы или нужна помощь с оплатой, "
                "пожалуйста, дайте нам знать. Мы всегда готовы помочь!\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            ),
            "Срочное напоминание": (
                "⚠️ Важное уведомление ⚠️\n\n"
                "Уважаемый(ая) {client_name},\n\n"
                "Ваш заказ #{order_id} - {service} требует срочной оплаты.\n"
                "Сумма: {amount} ₽\n\n"
                "Пожалуйста, оплатите заказ в ближайшее время, чтобы избежать его отмены.\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            ),
            # Добавляем новый шаблон для отзывов
            "Запрос отзыва": (
    "🌟 Здравствуйте, {client_name}! 🌟\n\n"
    "Вы с нами уже с {earliest_date}, и за это время оформили {total_orders} заказ(ов). "
    "Спасибо за доверие! 🙏\n\n"
    "Нам очень важно Ваше мнение. Пожалуйста, поделитесь своими впечатлениями о нашей работе, "
    "оставив отзыв по ссылке:\n"
    "👇👇👇\n"
    "{review_link}\n"
    "👆👆👆\n\n"
    "Ваш отзыв поможет нам стать еще лучше! ✨\n\n"
    "С уважением,\n"
    "Команда MPSP 💼"
),
"Короткий запрос отзыва": (
    "👋 Здравствуйте, {client_name}!\n\n"
    "Благодарим вас за сотрудничество с нами! 🤝\n"
    "Пожалуйста, оставьте отзыв о нашей работе по ссылке:\n"
    "⬇️ ⬇️ ⬇️\n"
    "{review_link}\n"
    "⬆️ ⬆️ ⬆️\n\n"
    "Ваше мнение очень важно для нас! 💯"
),
            "Дружеский запрос отзыва": (
                "Привет, {client_name}! 👋\n\n"
                "Ты с нами уже с {earliest_date} - это целых {days_waiting} дней дружбы! 🤗\n"
                "Мы тут подумали... 🤔 А что если ты расскажешь, как тебе с нами работается?\n"
                "Буквально пару слов - хорошо, плохо, что понравилось, а что нет.\n\n"
                "Вот тут можно оставить отзыв 👇👇👇\n"
                "{review_link}\n"
                "☝️ Жми на ссылку! ☝️\n\n"
                "P.S. Мы обещаем не плакать... ну, только если отзыв будет супер-крутой! 😎\n"
                "Твоя команда MPSP 🚀"
            ),
            "Короткий дружеский запрос": (
                "Хей, {client_name}! 👋\n\n"
                "Ты наш клиент уже {days_waiting} дней - круто! 🎉\n"
                "Черкни пару слов о нашей работе:\n"
                "👇\n"
                "{review_link}\n"
                "👆\n\n"
                "Твое мнение реально важно! 💪\n"
                "Команда MPSP ✌️"
            )
        }

        # Добавляем стандартные шаблоны в комбобокс
        for name in standard_templates.keys():
            self.template_combo.addItem(name)

        # Добавляем пользовательские шаблоны
        templates = self.template_manager.get_templates()
        for name in templates.keys():
            if name not in standard_templates:  # Проверяем, чтобы избежать дубликатов
                self.template_combo.addItem(name)

        # Восстанавливаем выбранный шаблон если он еще существует
        index = self.template_combo.findText(current_text)
        if index >= 0:
            self.template_combo.setCurrentIndex(index)
        elif self.template_combo.count() > 0:
            self.template_combo.setCurrentIndex(0)

        # Сохраняем стандартные шаблоны в настройках, если их там нет
        saved_templates = self.template_manager.get_templates()
        for name, text in standard_templates.items():
            if name not in saved_templates:
                self.template_manager.save_template(name, text)

    # 6. Обновляем метод update_message_template для добавления шаблона отзывов

    def update_message_template(self):
        """Обновление шаблона сообщения в зависимости от режима"""
        if self.view_mode == 'orders':
            template = (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть заказ #{order_id} от {created_date} - {service}.\n"
                "Хотели уточнить, актуален ли еще данный заказ?\n\n"
                "Если да, то напоминаем о необходимости внесения оплаты.\n"
                "Сумма к оплате: {amount} ₽\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            )
        elif self.view_mode == 'clients':
            template = (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть {total_orders} неоплаченных заказов на общую сумму {total_amount} ₽.\n"
                "Хотели бы уточнить, актуальны ли еще ваши заказы?\n\n"
                "Пожалуйста, не игнорируйте это сообщение! "
                "Нам важно знать ваше решение по заказам.\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            )
        else:  # Для режима отзывов
            template = (
                "Здравствуйте, {client_name}!\n\n"
                "Вы с нами уже с {earliest_date}, и за это время оформили {total_orders} заказ(ов). "
                "Спасибо за доверие!\n\n"
                "Нам очень важно Ваше мнение. Пожалуйста, поделитесь своими впечатлениями о нашей работе, "
                "оставив отзыв по ссылке:\n"
                "{review_link}\n\n"
                "Ваш отзыв поможет нам стать еще лучше!\n\n"
                "С уважением, команда MPSP"
            )

        self.message_edit.setPlainText(template)

    def generate_review_link(self, data):
        """
        Генерирует короткую ссылку для отзыва клиента

        Args:
            data: Словарь с данными о клиенте и заказе

        Returns:
            Сокращенная ссылка на страницу отзыва
        """
        try:
            # Получаем ID заказа
            order_id = data.get('order_id')
            if not order_id:
                print(f"Ошибка: ID заказа не найден для клиента {data.get('fio', '')}")
                return None

            # Получаем данные из конфигурации
            from reviews_manager.config import SITE_CONFIG

            base_url = SITE_CONFIG.get('base_url', 'https://mpsp.online')
            reviews_page = SITE_CONFIG.get('reviews_page', '/submit-review.html')

            # Получаем данные о заказе
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    print(f"Ошибка: Заказ #{order_id} не найден в базе данных")
                    return None

                # Кодируем параметры для URL
                service_encoded = urllib.parse.quote(order.service or "")
                name_encoded = urllib.parse.quote(order.fio or "")

                # Генерируем уникальный, но короткий токен
                # Используем 8 символов из UUID для краткости
                token = str(uuid.uuid4()).split('-')[0][:8]

                # Сохраняем токен в заказе
                order.review_token = token

                # Добавляем ID клиента в токен для уникальности
                client_token = f"{token}_{order_id}"

                # Параметры для автозаполнения (добавляем статус=1 для автоматического одобрения)
                params = {
                    'token': client_token,
                    'order': order_id,
                    'name': name_encoded,
                    'service': service_encoded,
                    'auto_approve': 1  # Параметр для автоматического одобрения
                }

                # Формируем строку запроса
                query_string = urllib.parse.urlencode(params)

                # Формируем полную ссылку
                full_link = f"{base_url}{reviews_page}?{query_string}"

                # Сокращаем ссылку с помощью встроенного сервиса сокращения
                short_link = self.shorten_url(full_link)

                print(f"Сгенерирована короткая ссылка для отзыва заказа #{order_id}: {short_link}")
                session.commit()

                return short_link if short_link else full_link

        except Exception as e:
            print(f"Ошибка при генерации ссылки для отзыва: {str(e)}")
            return None

    def shorten_url(self, long_url):
        """
        Сокращает URL с помощью различных сервисов

        Args:
            long_url: Исходный длинный URL

        Returns:
            Сокращенный URL или исходный URL в случае ошибки
        """
        try:
            # Метод 1: Через TinyURL API (простой и не требует регистрации)
            import requests

            # Попытка через TinyURL
            tinyurl_api = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
            try:
                response = requests.get(tinyurl_api, timeout=5)
                if response.status_code == 200:
                    return response.text.strip()
            except Exception as e:
                print(f"Ошибка при сокращении через TinyURL: {str(e)}")

            # Метод 2: Через Bitly API (требует API ключ)
            # Раскомментируйте, если у вас есть ключ API Bitly
            # bitly_token = "ВАШ_BITLY_API_КЛЮЧ"  # Замените на ваш ключ API
            # if bitly_token:
            #     try:
            #         headers = {
            #             "Authorization": f"Bearer {bitly_token}",
            #             "Content-Type": "application/json"
            #         }
            #         payload = {
            #             "long_url": long_url,
            #             "domain": "bit.ly"
            #         }
            #         response = requests.post(
            #             "https://api-ssl.bitly.com/v4/shorten",
            #             headers=headers,
            #             json=payload,
            #             timeout=5
            #         )
            #         if response.status_code == 200:
            #             return response.json().get("link")
            #     except Exception as e:
            #         print(f"Ошибка при сокращении через Bitly: {str(e)}")

            # Если все методы не сработали, возвращаем исходный URL
            return long_url

        except Exception as e:
            print(f"Общая ошибка при сокращении URL: {str(e)}")
            return long_url
    def save_review_link_info(self, order_id):
        """Сохраняет информацию о том, что для заказа была сгенерирована ссылка для отзыва"""
        try:
            if not order_id:
                return False

            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if order:
                    # Если у заказа уже есть токен отзыва, используем его
                    # В противном случае, генерируем новый токен и сохраняем
                    if not order.review_token:
                        order.review_token = str(uuid.uuid4())
                    print(f"Сохранена информация о ссылке для отзыва для заказа #{order_id}")
                    return True
            return False

        except Exception as e:
            print(f"Ошибка при сохранении информации о ссылке для отзыва: {str(e)}")
            return False






    def setup_table(self):
        """Настройка таблицы"""
        self.table.setColumnCount(10)  # Увеличиваем количество колонок для статуса

        # Настройка заголовков
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Чекбокс
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # ID/Всего заказов
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Клиент
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Услуга/Заказов в ожидании
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Сумма
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Дата
        header.setSectionResizeMode(6, QHeaderView.Fixed)  # Дней
        header.setSectionResizeMode(7, QHeaderView.Fixed)  # Телефон
        header.setSectionResizeMode(8, QHeaderView.Fixed)  # Статус
        header.setSectionResizeMode(9, QHeaderView.Fixed)  # Последнее напоминание

        # Устанавливаем ширину колонок
        self.table.setColumnWidth(0, 30)  # Чекбокс
        self.table.setColumnWidth(1, 70)  # ID/Всего заказов
        self.table.setColumnWidth(4, 120)  # Сумма
        self.table.setColumnWidth(5, 100)  # Дата
        self.table.setColumnWidth(6, 80)  # Дней
        self.table.setColumnWidth(7, 120)  # Телефон
        self.table.setColumnWidth(8, 120)  # Статус
        self.table.setColumnWidth(9, 150)  # Последнее напоминание

        # Включаем сортировку
        self.table.setSortingEnabled(True)

        # Подключаем обработчик клика по заголовку
        header.sectionClicked.connect(self.on_header_clicked)

        # Стилизация таблицы
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 4px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #e0e0e0;
            }
        """)

        # Добавляем панель с кнопками для выбора всех/ни одного
        self.add_checkbox_controls()

    def add_checkbox_controls(self):
        """Добавление панели с кнопками для управления чекбоксами"""
        # Создаем панель над таблицей
        panel = QFrame(self)
        panel.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #bbdefb;
                border-radius: 4px;
                margin-bottom: 4px;
            }
        """)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(10, 5, 10, 5)

        # Заголовок
        label = QLabel("Управление выбором:")
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)

        # Кнопка "Выбрать все"
        select_all_btn = QPushButton("✓ Выбрать все")
        select_all_btn.setToolTip("Выбрать все видимые записи")
        select_all_btn.clicked.connect(self.select_all_checkboxes)
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(select_all_btn)

        # Кнопка "Снять все"
        unselect_all_btn = QPushButton("✗ Снять все")
        unselect_all_btn.setToolTip("Снять выбор со всех записей")
        unselect_all_btn.clicked.connect(self.unselect_all_checkboxes)
        unselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        layout.addWidget(unselect_all_btn)

        # Кнопка "Инвертировать выбор"
        invert_selection_btn = QPushButton("↺ Инвертировать")
        invert_selection_btn.setToolTip("Инвертировать выбор записей")
        invert_selection_btn.clicked.connect(self.invert_checkboxes)
        invert_selection_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(invert_selection_btn)

        # Кнопка "Выбрать с номерами"
        select_with_phones_btn = QPushButton("📱 Только с номерами")
        select_with_phones_btn.setToolTip("Выбрать только записи с номерами телефонов")
        select_with_phones_btn.clicked.connect(self.select_with_phones)
        select_with_phones_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        layout.addWidget(select_with_phones_btn)

        layout.addStretch()

        # Счетчик выбранных записей
        self.selected_count_label = QLabel("Выбрано: 0")
        self.selected_count_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2196F3;
            }
        """)
        layout.addWidget(self.selected_count_label)

        # Добавляем панель в основной макет, перед таблицей
        index = self.layout().indexOf(self.table)
        self.layout().insertWidget(index, panel)

    def reload_table_checkboxes(self):
        """Перезагружает чекбоксы для всех строк в таблице"""
        try:
            print("Перезагрузка чекбоксов в таблице...")

            for row in range(self.table.rowCount()):
                # Создаем новый чекбокс
                checkbox = QCheckBox()
                checkbox.setChecked(False)
                checkbox.setEnabled(True)

                # Подключаем обработчик события
                checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(state, r))

                # Удаляем старый виджет чекбокса, если он есть
                old_checkbox = self.table.cellWidget(row, 0)
                if old_checkbox:
                    self.table.removeCellWidget(row, 0)

                # Устанавливаем новый чекбокс
                self.table.setCellWidget(row, 0, checkbox)

            print(f"Перезагружено {self.table.rowCount()} чекбоксов")
        except Exception as e:
            print(f"Ошибка при перезагрузке чекбоксов: {e}")

    def on_checkbox_changed(self, state, row):
        """Универсальный обработчик изменения состояния чекбокса"""
        print(f"Изменено состояние чекбокса в строке {row} на {state}")
        self.update_selected_count()

    def select_all_checkboxes(self):
        """Выбор всех видимых записей"""
        # Сначала перезагружаем чекбоксы для надежности
        self.reload_table_checkboxes()

        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if checkbox and isinstance(checkbox, QCheckBox):
                    try:
                        checkbox.setChecked(True)
                        count += 1
                    except Exception as e:
                        print(f"Ошибка при выборе чекбокса в строке {row}: {e}")

        self.update_selected_count()
        QMessageBox.information(self, "Выбор записей", f"Выбрано {count} записей.")
    def unselect_all_checkboxes(self):
        """Снятие выбора со всех записей"""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and isinstance(checkbox, QCheckBox):
                try:
                    checkbox.setChecked(False)
                except Exception as e:
                    print(f"Ошибка при снятии выбора чекбокса в строке {row}: {e}")

        self.update_selected_count()
        QMessageBox.information(self, "Снятие выбора", "Выбор снят со всех записей.")

    def invert_checkboxes(self):
        """Инвертирование выбора записей"""
        count = 0
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if checkbox and isinstance(checkbox, QCheckBox):
                    try:
                        checkbox.setChecked(not checkbox.isChecked())
                        if checkbox.isChecked():
                            count += 1
                    except Exception as e:
                        print(f"Ошибка при инвертировании чекбокса в строке {row}: {e}")

        self.update_selected_count()
        QMessageBox.information(self, "Инвертирование выбора", f"Теперь выбрано {count} записей.")

    def select_with_phones(self):
        """Выбор только записей с номерами телефонов"""
        empty_phone_values = ["", "Не указано", "Нет", "-", "н/д", "N/A"]
        count = 0

        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                phone_item = self.table.item(row, 7)

                if checkbox and isinstance(checkbox, QCheckBox) and phone_item:
                    try:
                        phone = phone_item.text().strip()

                        # Проверяем, есть ли номер телефона
                        has_phone = phone and phone.lower() not in map(str.lower, empty_phone_values)

                        # Устанавливаем чекбокс только если есть номер
                        checkbox.setChecked(bool(has_phone))
                        if has_phone:
                            count += 1
                    except Exception as e:
                        print(f"Ошибка при выборе чекбокса с телефоном в строке {row}: {e}")

        self.update_selected_count()
        QMessageBox.information(self, "Выбор с номерами", f"Выбрано {count} записей с номерами телефонов.")

    def update_selected_count(self):
        """Обновление счетчика выбранных записей"""
        count = 0
        try:
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    checkbox = self.table.cellWidget(row, 0)
                    if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                        count += 1

            if hasattr(self, 'selected_count_label'):
                self.selected_count_label.setText(f"Выбрано: {count}")
        except Exception as e:
            print(f"Ошибка при обновлении счетчика выбранных записей: {e}")



    def create_checkbox_with_event(self, row):
        """Создание чекбокса с обработчиком события для счетчика выбранных записей"""
        checkbox = QCheckBox()
        checkbox.setEnabled(True)  # По умолчанию включен

        # Подключаем обработчик события изменения состояния
        checkbox.stateChanged.connect(self.on_checkbox_state_changed)

        return checkbox

    def on_checkbox_state_changed(self, state):
        """Обработчик изменения состояния чекбокса"""
        # Обновляем счетчик выбранных записей
        self.update_selected_count()


    def on_header_clicked(self, logical_index):
        """Обработчик клика по заголовку таблицы"""
        # Сохраняем состояние чекбоксов перед сортировкой
        checked_rows = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # Сохраняем идентификатор строки (ID или ФИО в зависимости от режима)
                key = self.table.item(row, 2 if self.view_mode == 'clients' else 1).text()
                checked_rows.append(key)

        # Если кликнули по тому же столбцу, меняем порядок
        if self.table.horizontalHeader().sortIndicatorSection() == logical_index:
            order = Qt.DescendingOrder if self.table.horizontalHeader().sortIndicatorOrder() == Qt.AscendingOrder else Qt.AscendingOrder
            self.table.sortItems(logical_index, order)
        else:
            # Если кликнули по новому столбцу, сортируем по возрастанию
            self.table.sortItems(logical_index, Qt.AscendingOrder)

        # Восстанавливаем состояние чекбоксов
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                key = self.table.item(row, 2 if self.view_mode == 'clients' else 1).text()
                checkbox.setChecked(key in checked_rows)



    def load_orders_view(self, orders):
        """Загрузка данных в режиме отображения по заказам"""
        self.table.setHorizontalHeaderLabels([
            "", "ID", "Клиент", "Услуга", "Сумма", "Создан",
            "Дней ожидания", "Телефон", "Статус", "Последнее напоминание"
        ])

        current_date = datetime.now()

        for row, order in enumerate(orders):
            self.table.insertRow(row)

            # Чекбокс
            checkbox = QCheckBox()
            checkbox.setEnabled(self.reminder_history.can_send_reminder(order.fio))
            self.table.setCellWidget(row, 0, checkbox)

            # Остальные данные
            self.table.setItem(row, 1, QTableWidgetItem(str(order.id)))
            self.table.setItem(row, 2, QTableWidgetItem(order.fio))
            self.table.setItem(row, 3, QTableWidgetItem(order.service))
            self.table.setItem(row, 4, QTableWidgetItem(f"{order.remaining_amount:,.2f} ₽"))
            self.table.setItem(row, 5, QTableWidgetItem(
                order.created_date.strftime('%d.%m.%Y')))

            # Конвертируем даты в один формат перед вычислением разницы
            if isinstance(order.created_date, date):
                order_date = datetime.combine(order.created_date, datetime.min.time())
            else:
                order_date = order.created_date

            # Дней в ожидании
            days = (current_date - order_date).days
            days_item = QTableWidgetItem(str(days))
            self.set_days_color(days_item, days)
            self.table.setItem(row, 6, days_item)

            self.table.setItem(row, 7, QTableWidgetItem(order.phone or ""))

            # Статус заказа (новая колонка)
            self.table.setItem(row, 8, QTableWidgetItem(order.status))

            # Последнее напоминание
            last_reminder = self.reminder_history.get_last_reminder(order.fio)
            reminder_text = (last_reminder.strftime('%d.%m.%Y %H:%M')
                             if last_reminder else "Не было")
            self.table.setItem(row, 9, QTableWidgetItem(reminder_text))

    def load_clients_view(self, orders):
        """Загрузка данных в режиме отображения по клиентам"""
        self.table.setHorizontalHeaderLabels([
            "", "Всего заказов", "Клиент", "Заказов в ожидании", "Общая сумма",
            "Дата первого заказа", "Дней ожидания", "Телефон", "Статусы", "Последнее напоминание"
        ])

        current_date = datetime.now()

        # Группируем заказы по клиентам
        clients_data = {}

        try:
            with self.db_manager.session_scope() as session:
                for order in orders:
                    if order.fio not in clients_data:
                        # Статусы, которые считаются активными (исключаем "Выполнен" и "Отказ")
                        active_statuses = ['Новый', 'В работе', 'В ожидании оплаты']

                        # Получаем общее количество заказов клиента (всех статусов)
                        total_orders = session.query(Order).filter(
                            Order.fio == order.fio
                        ).count()

                        # Получаем количество активных заказов
                        active_orders = session.query(Order).filter(
                            Order.fio == order.fio,
                            Order.status.in_(active_statuses)
                        ).count()

                        # Статусы заказов клиента (список уникальных статусов)
                        status_list = [r[0] for r in session.query(Order.status).filter(
                            Order.fio == order.fio
                        ).distinct().all()]

                        status_text = ", ".join(status_list)

                        # Конвертируем дату создания в datetime если это date
                        if isinstance(order.created_date, date):
                            created_datetime = datetime.combine(order.created_date, datetime.min.time())
                        else:
                            created_datetime = order.created_date

                        # Получаем все активные заказы клиента для расчета суммы
                        active_client_orders = session.query(Order).filter(
                            Order.fio == order.fio,
                            Order.status.in_(active_statuses)
                        ).all()

                        # Считаем общую сумму с учетом скидок
                        total_amount = 0
                        for client_order in active_client_orders:
                            # Берем remaining_amount, так как там уже учтена скидка
                            if client_order.remaining_amount is not None:
                                total_amount += client_order.remaining_amount

                        # Инициализируем данные клиента
                        clients_data[order.fio] = {
                            'total_orders': total_orders,
                            'active_orders': active_orders,
                            'phone': order.phone,
                            'earliest_date': created_datetime,
                            'total_amount': total_amount,
                            'status_text': status_text
                        }
                    else:
                        # Обновляем дату если текущий заказ раньше
                        if isinstance(order.created_date, date):
                            order_datetime = datetime.combine(order.created_date, datetime.min.time())
                        else:
                            order_datetime = order.created_date

                        if order_datetime < clients_data[order.fio]['earliest_date']:
                            clients_data[order.fio]['earliest_date'] = order_datetime

            # Заполняем таблицу
            for row, (client, data) in enumerate(clients_data.items()):
                self.table.insertRow(row)

                # Чекбокс
                checkbox = self.create_checkbox_with_event(row)
                checkbox.setEnabled(self.reminder_history.can_send_reminder(client))
                self.table.setCellWidget(row, 0, checkbox)

                # Данные клиента
                self.table.setItem(row, 1, QTableWidgetItem(str(data['total_orders'])))
                self.table.setItem(row, 2, QTableWidgetItem(client))
                self.table.setItem(row, 3, QTableWidgetItem(str(data['active_orders'])))
                self.table.setItem(row, 4, QTableWidgetItem(f"{data['total_amount']:,.2f} ₽"))
                self.table.setItem(row, 5, QTableWidgetItem(
                    data['earliest_date'].strftime('%d.%m.%Y')))

                # Дней в ожидании
                days = (current_date - data['earliest_date']).days
                days_item = QTableWidgetItem(str(days))
                self.set_days_color(days_item, days)
                self.table.setItem(row, 6, days_item)

                self.table.setItem(row, 7, QTableWidgetItem(data['phone'] or ""))

                # Статусы заказов
                self.table.setItem(row, 8, QTableWidgetItem(data['status_text']))

                # Последнее напоминание
                last_reminder = self.reminder_history.get_last_reminder(client)
                reminder_text = (last_reminder.strftime('%d.%m.%Y %H:%M')
                                 if last_reminder else "Не было")
                self.table.setItem(row, 9, QTableWidgetItem(reminder_text))

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при загрузке данных клиентов: {str(e)}")

    def set_days_color(self, item, days):
        """Установка цвета ячейки в зависимости от количества дней"""
        if days > 180:
            item.setBackground(QColor("#ffebee"))  # Красный
        elif days > 90:
            item.setBackground(QColor("#fff3e0"))  # Оранжевый
        elif days > 30:
            item.setBackground(QColor("#fff8e1"))  # Желтый
        else:
            item.setBackground(QColor("#e8f5e9"))  # Зеленый

    def start_sending(self):
        """Начало процесса рассылки"""
        try:
            self.selected_data = self.get_selected_data()

            if not self.selected_data:
                show_warning(self, "Предупреждение", "Не выбрано ни одного получателя!")
                return

            # Проверяем количество выбранных получателей
            if len(self.selected_data) > 20:
                reply = QMessageBox.question(
                    self,
                    "Подтверждение",
                    f"Вы выбрали {len(self.selected_data)} получателей.\n"
                    "Рекомендуется отправлять не более 20 сообщений за раз.\n"
                    "Хотите продолжить?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

            # Инициализируем список для пропущенных из-за отсутствия телефона записей
            self.skipped_phones = []

            # Подготовка к отправке
            self.current_index = 0
            self.send_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(len(self.selected_data))
            self.progress_bar.setValue(0)

            # Запускаем отправку
            self.send_next_message()

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при начале рассылки: {str(e)}")
            self.send_btn.setEnabled(True)
            self.progress_bar.setVisible(False)

    def format_string_safe(self, template, replacements):
        """Безопасное форматирование строки с заменой переменных"""
        result = template

        # Находим все переменные в шаблоне {name}
        pattern = r'\{([^{}]+)\}'
        variables = re.findall(pattern, template)

        # Заменяем каждую переменную на соответствующее значение
        for var in variables:
            placeholder = f'{{{var}}}'
            if var in replacements:
                result = result.replace(placeholder, str(replacements[var]))
            else:
                # Оставляем переменную без изменений, если для нее нет значения
                print(f"Предупреждение: переменная {var} не найдена в данных")

        return result


    def sending_completed(self):
        """Завершение процесса рассылки"""
        self.send_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Подсчет пропущенных записей из-за отсутствия телефона
        skipped_records = 0
        if hasattr(self, 'skipped_phones'):
            skipped_records = len(self.skipped_phones)

        # Создаем подробное сообщение
        message = (
            f"Рассылка завершена!\n\n"
            f"Обработано получателей: {self.current_index} из {len(self.selected_data)}\n"
        )

        # Если были записи без телефонов
        if hasattr(self, 'skipped_phones') and self.skipped_phones:
            message += f"\nПропущено записей без номера телефона: {skipped_records}\n"

            # Если пропущенных не слишком много, можно показать их
            if skipped_records <= 5:
                message += "\nПропущенные клиенты:"
                for fio in self.skipped_phones:
                    message += f"\n- {fio}"

        # Показываем отчет
        QMessageBox.information(
            self,
            "Готово",
            message
        )

        # Очищаем переменные для следующей рассылки
        if hasattr(self, 'skipped_phones'):
            del self.skipped_phones

    def filter_orders(self):
        """Фильтрация заказов по выбранным критериям"""
        try:
            # Получаем значения фильтров
            period = self.period_combo.currentText()
            status = self.status_combo.currentText()
            gender = self.gender_combo.currentText()

            now = datetime.now()

            for row in range(self.table.rowCount()):
                # Получаем данные для фильтрации
                days_item = self.table.item(row, 6)
                fio_item = self.table.item(row, 2)

                if not days_item or not fio_item:
                    continue

                days = int(days_item.text())
                fio = fio_item.text()

                # Фильтр по периоду
                show_by_period = True
                if period == "Более 6 месяцев":
                    show_by_period = days > 180
                elif period == "3-6 месяцев":
                    show_by_period = 90 <= days <= 180
                elif period == "1-3 месяца":
                    show_by_period = 30 <= days < 90
                elif period == "Последний месяц":
                    show_by_period = days < 30

                # Фильтр по полу (на основе окончания фамилии)
                show_by_gender = True
                if gender == "Мужчины":
                    # Проверяем, что фамилия заканчивается на "ов", "ев", "ин", "ын"
                    show_by_gender = any(fio.lower().split()[0].endswith(end) for end in ["ов", "ев", "ин", "ын"])
                elif gender == "Женщины":
                    # Проверяем, что фамилия заканчивается на "ва", "на", "ая"
                    show_by_gender = any(fio.lower().split()[0].endswith(end) for end in ["ва", "на", "ая", "ая"])

                # Фильтр по статусу
                show_by_status = True
                if status != "Все статусы" and self.view_mode == 'orders':
                    status_col = 8  # Предполагаем, что статус находится в 8-й колонке в режиме заказов
                    status_item = self.table.item(row, status_col)
                    if status_item:
                        show_by_status = status_item.text() == status

                # Комбинируем все условия
                show_row = show_by_period and show_by_gender and show_by_status

                self.table.setRowHidden(row, not show_row)

            # Обновляем доступность чекбоксов для видимых строк
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    checkbox = self.table.cellWidget(row, 0)
                    if checkbox:
                        fio = self.table.item(row, 2).text()
                        checkbox.setEnabled(self.reminder_history.can_send_reminder(fio))

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при фильтрации заказов: {str(e)}")
    def create_message_panel(self):
        """Создание панели с сообщением"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(frame)

        # Шаблоны сообщений
        template_layout = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.currentIndexChanged.connect(self.load_message_template)

        manage_templates_btn = QPushButton("✏️ Управление шаблонами")
        manage_templates_btn.clicked.connect(self.show_template_manager)
        manage_templates_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)

        # Кнопка помощника по переменным
        help_btn = QPushButton("❓ Помощник по переменным")
        help_btn.clicked.connect(self.show_variables_help)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)

        template_layout.addWidget(QLabel("Шаблон:"))
        template_layout.addWidget(self.template_combo)
        template_layout.addWidget(manage_templates_btn)
        template_layout.addWidget(help_btn)
        template_layout.addStretch()

        # Текст сообщения
        self.message_edit = QTextEdit()
        self.message_edit.setMinimumHeight(150)
        self.message_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout.addLayout(template_layout)
        layout.addWidget(QLabel("Текст сообщения:"))
        layout.addWidget(self.message_edit)

        return frame

    def show_variables_help(self):
        """Показать окно помощника по переменным"""
        dialog = MessageVariablesHelpDialog(self, self.view_mode)
        dialog.exec_()

    def create_buttons_panel(self):
        """Создание панели с кнопками управления"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        layout = QHBoxLayout(frame)

        # Настройки отправки
        settings_layout = QVBoxLayout()
        delay_layout = QHBoxLayout()
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 60)
        self.delay_spin.setValue(5)
        self.delay_spin.setStyleSheet("""
            QSpinBox {
                padding: 4px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
        """)

        delay_layout.addWidget(QLabel("Задержка между отправками (сек):"))
        delay_layout.addWidget(self.delay_spin)

        # Добавляем чек-бокс для пропуска записей без номера телефона
        checkbox_layout = QHBoxLayout()
        self.skip_empty_phone_checkbox = QCheckBox("Пропускать записи без номера телефона")
        self.skip_empty_phone_checkbox.setChecked(True)  # По умолчанию включено
        self.skip_empty_phone_checkbox.setToolTip(
            "Когда включено, записи с пустыми номерами или значениями 'Не указано', "
            "'Нет', '-' и подобными будут автоматически пропущены при рассылке"
        )
        self.skip_empty_phone_checkbox.setStyleSheet("""
            QCheckBox {
                padding: 4px;
            }
            QCheckBox:hover {
                background-color: #e0e0e0;
                border-radius: 4px;
            }
        """)
        checkbox_layout.addWidget(self.skip_empty_phone_checkbox)

        settings_layout.addLayout(delay_layout)
        settings_layout.addLayout(checkbox_layout)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
            }
        """)

        # Кнопки действий
        buttons_layout = QVBoxLayout()
        self.send_btn = QPushButton("📱 Начать рассылку")
        self.send_btn.clicked.connect(self.start_sending)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)

        buttons_layout.addWidget(self.send_btn)
        buttons_layout.addWidget(close_btn)

        # Добавляем элементы на панель
        layout.addLayout(settings_layout)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        layout.addLayout(buttons_layout)

        return frame
    def show_template_manager(self):
        """Показ окна управления шаблонами"""
        dialog = TemplateManagerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_templates()  # Обновляем список шаблонов
            self.load_message_template()  # Загружаем текст выбранного шаблона
    def show_history(self):
        """Показ окна истории напоминаний"""
        dialog = ReminderHistoryDialog(self)
        dialog.exec_()


    def load_message_template(self):
        """Загрузка текста выбранного шаблона"""
        template_name = self.template_combo.currentText()
        message = ""  # Добавляем значение по умолчанию

        # Проверяем пользовательские шаблоны
        templates = self.template_manager.get_templates()
        if template_name in templates:
            message = templates[template_name]

        # Стандартные шаблоны
        elif template_name == "Стандартное напоминание":
            message = (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть заказ #{order_id} от {created_date} - {service}.\n"
                "Хотели уточнить, актуален ли еще данный заказ?\n\n"
                "Если да, то напоминаем о необходимости внесения оплаты.\n"
                "Сумма к оплате: {amount} ₽\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            )
        elif template_name == "Короткое напоминание":
            message = (
                "Здравствуйте, {client_name}!\n"
                "Напоминаем о заказе #{order_id} - {service}.\n"
                "Сумма к оплате: {amount} ₽\n"
                "Для оплаты: +79066322571"
            )
        elif template_name == "Предложение скидки":
            message = (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть неоплаченный заказ #{order_id} - {service}.\n"
                "Предлагаем специальные условия при оплате в течение 3 дней:\n"
                "- Скидка 10%\n"
                "- Сумма к оплате со скидкой: {discounted_amount} ₽\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            )
        else:
            # Если шаблон не найден, используем стандартный
            message = (
                "Здравствуйте, {client_name}!\n\n"
                "У вас есть заказ #{order_id}.\n"
                "Сумма к оплате: {amount} ₽\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571"
            )

        self.message_edit.setPlainText(message)
    def get_selected_orders(self):
        """Получение выбранных заказов"""
        selected = []
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):
                checkbox = self.table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    order_data = {
                        'id': int(self.table.item(row, 1).text()),
                        'fio': self.table.item(row, 2).text(),
                        'service': self.table.item(row, 3).text(),
                        'amount': float(
                            self.table.item(row, 4).text().replace('₽', '').replace(' ', '').replace(',', '')),
                        'created_date': self.table.item(row, 5).text(),
                        'phone': self.table.item(row, 7).text()
                    }
                    selected.append(order_data)
        return selected

    def get_selected_data(self):
        """Получение выбранных данных в зависимости от режима отображения"""
        selected = []
        skip_empty_phone = self.skip_empty_phone_checkbox.isChecked()
        empty_phone_values = ["", "Не указано", "Нет", "-", "н/д", "N/A"]

        # Подсчитаем общее количество выбранных строк для диагностики
        total_selected = 0
        skipped_counts = {"no_phone": 0, "other_reasons": 0}

        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and isinstance(checkbox, QCheckBox) and checkbox.isChecked() and not self.table.isRowHidden(
                    row):
                total_selected += 1

                try:
                    phone_cell = self.table.item(row, 7)
                    phone = phone_cell.text().strip() if phone_cell else ""

                    # Проверяем, нужно ли пропускать запись с пустым телефоном
                    if skip_empty_phone and (not phone or phone.lower() in map(str.lower, empty_phone_values)):
                        fio = self.table.item(row, 2).text()
                        print(f"Пропускаем запись в строке {row} для клиента {fio} из-за отсутствия номера телефона")
                        skipped_counts["no_phone"] += 1

                        # Сохраняем информацию о пропущенной записи
                        if not hasattr(self, 'skipped_phones'):
                            self.skipped_phones = []
                        self.skipped_phones.append(fio)

                        continue

                    if self.view_mode == 'orders':
                        # Обработка строки для режима заказов
                        amount_text = self.table.item(row, 4).text().replace('₽', '').replace(' ', '').replace(',', '')
                        order_data = {
                            'id': int(self.table.item(row, 1).text()),
                            'fio': self.table.item(row, 2).text(),
                            'service': self.table.item(row, 3).text(),
                            'amount': float(amount_text),
                            'created_date': self.table.item(row, 5).text(),
                            'phone': phone
                        }
                        selected.append(order_data)
                    elif self.view_mode == 'clients':
                        # Обработка строки для режима клиентов
                        amount_text = self.table.item(row, 4).text().replace('₽', '').replace(' ', '').replace(',', '')
                        order_data = {
                            'fio': self.table.item(row, 2).text(),
                            'total_orders': int(self.table.item(row, 1).text()),
                            'waiting_orders': int(self.table.item(row, 3).text()),
                            'total_amount': float(amount_text),
                            'earliest_date': self.table.item(row, 5).text(),
                            'phone': phone
                        }
                        selected.append(order_data)
                    else:  # Режим отзывов
                        # Получаем FIO клиента
                        fio = self.table.item(row, 2).text()

                        # Получаем дополнительные данные из таблицы
                        try:
                            total_orders = int(self.table.item(row, 1).text())
                            unique_services = int(self.table.item(row, 3).text())
                            max_payment_text = self.table.item(row, 4).text().replace('₽', '').replace(' ', '').replace(
                                ',', '')
                            max_payment = float(max_payment_text)
                            earliest_date = self.table.item(row, 5).text()
                            days_with_us = int(self.table.item(row, 6).text())

                            # Поиск базовой информации о заказе
                            with self.db_manager.session_scope() as session:
                                # Получаем последний заказ клиента
                                best_order = session.query(Order).filter(
                                    Order.fio == fio,
                                    Order.status != 'Отменен'
                                ).order_by(Order.paid_amount.desc()).first()

                                # Если не найден заказ с оплатой, берем любой заказ
                                if not best_order:
                                    best_order = session.query(Order).filter(
                                        Order.fio == fio,
                                        Order.status != 'Отменен'
                                    ).first()

                                if best_order:
                                    order_data = {
                                        'fio': fio,
                                        'order_id': best_order.id,
                                        'service': best_order.service or "Не указано",
                                        'total_orders': total_orders,
                                        'earliest_date': earliest_date,
                                        'days_with_us': days_with_us,  # Добавляем корректно рассчитанное значение
                                        'phone': phone,
                                        'mode': 'reviews'  # Метка режима отзывов
                                    }

                                    selected.append(order_data)
                                else:
                                    print(f"Не найдено заказов для клиента {fio}")
                                    skipped_counts["other_reasons"] += 1
                        except Exception as e:
                            print(f"Ошибка при обработке строки {row} для клиента {fio}: {e}")
                            skipped_counts["other_reasons"] += 1
                            continue

                except (ValueError, AttributeError) as e:
                    print(f"Ошибка при обработке строки {row}: {e}")
                    skipped_counts["other_reasons"] += 1
                    continue

        print(f"Всего выбрано строк: {total_selected}")
        print(f"Добавлено получателей: {len(selected)}")
        print(f"Пропущено из-за отсутствия телефона: {skipped_counts['no_phone']}")
        print(f"Пропущено по другим причинам: {skipped_counts['other_reasons']}")

        return selected

    def send_next_message(self):
        """Отправка следующего сообщения"""
        try:
            if self.current_index >= len(self.selected_data):
                self.sending_completed()
                return

            data = self.selected_data[self.current_index]

            # Проверка наличия телефона
            phone = data.get('phone', '').strip()
            empty_phone_values = ["", "Не указано", "Нет", "-", "н/д", "N/A"]

            if not phone or phone.lower() in map(str.lower, empty_phone_values):
                print(f"Пропускаем запись для клиента {data.get('fio', '')} из-за отсутствия номера телефона")
                self.current_index += 1
                self.send_next_message()
                return

            message = self.message_edit.toPlainText()

            try:
                # Обработка в зависимости от режима
                if data.get('mode') == 'reviews':  # Режим отзывов
                    # Генерируем ссылку для отзыва
                    review_link = self.generate_review_link(data)

                    if not review_link:
                        print(f"Не удалось сгенерировать ссылку для отзыва для клиента {data['fio']}")
                        self.current_index += 1
                        self.send_next_message()
                        return

                    # Подготавливаем данные для форматирования с корректными значениями
                    replacements = {
                        'client_name': data['fio'],
                        'total_orders': str(data['total_orders']),
                        'earliest_date': data['earliest_date'],
                        'days_waiting': str(data['days_with_us']),  # Используем предварительно рассчитанное значение
                        'review_link': review_link,
                        'phone': phone
                    }

                    # Форматируем сообщение с помощью функции format_string_safe
                    message = self.format_string_safe(message, replacements)
                elif self.view_mode == 'orders':
                    # Код для режима заказов
                    order_id = data.get('id', 0)

                    # Используем сессию для получения свежего объекта Order
                    with self.db_manager.session_scope() as session:
                        order = None
                        if order_id > 0:
                            order = session.query(Order).get(order_id)

                        # Базовые переменные
                        replacements = {
                            'client_name': data['fio'],
                            'order_id': str(data.get('id', '')),
                            'service': data.get('service', ''),
                            'amount': f"{data.get('amount', 0):,.2f}",
                            'created_date': data.get('created_date', ''),
                            'phone': phone,
                            'discounted_amount': f"{data.get('amount', 0):,.2f}",
                            'discount': "0%",
                            'theme': "Не указана",
                            'direction': "Не указано",
                            'deadline': "Не указан",
                            'status': "Неизвестен",
                            'teacher_name': "Не указан",
                            'discount_start_date': "Не установлена",
                            'discount_end_date': "Не установлена"
                        }

                        # Если заказ найден, добавляем данные из объекта заказа
                        if order:
                            # Расчет скидки
                            if 'amount' in data and order.discount:
                                try:
                                    discount_str = order.discount.strip('%')
                                    discount = float(discount_str) / 100
                                    discounted_amount = data['amount'] * (1 - discount)
                                    replacements['discounted_amount'] = f"{discounted_amount:,.2f}"
                                except (ValueError, AttributeError):
                                    pass

                            # Даты скидок
                            if order.discount_start_date:
                                replacements['discount_start_date'] = order.discount_start_date.strftime('%d.%m.%Y')

                            if order.discount_end_date:
                                replacements['discount_end_date'] = order.discount_end_date.strftime('%d.%m.%Y')

                            # Другие поля заказа
                            replacements['discount'] = order.discount or "0%"
                            replacements['theme'] = order.theme or "Не указана"
                            replacements['direction'] = order.direction or "Не указано"
                            replacements['deadline'] = order.deadline or "Не указан"
                            replacements['status'] = order.status or "Неизвестен"
                            replacements['teacher_name'] = order.teacher_name or "Не указан"

                    # Добавляем количество дней в ожидании
                    if 'created_date' in data:
                        try:
                            created_date = datetime.strptime(data['created_date'], '%d.%m.%Y')
                            days_waiting = (datetime.now() - created_date).days
                            replacements['days_waiting'] = str(days_waiting)
                        except (ValueError, TypeError):
                            replacements['days_waiting'] = "0"

                    # Форматируем сообщение
                    message = self.format_string_safe(message, replacements)

                else:  # Режим клиентов
                    # Код для режима клиентов
                    replacements = {
                        'client_name': data['fio'],
                        'total_orders': str(data.get('total_orders', 0)),
                        'waiting_orders': str(data.get('waiting_orders', 0)),
                        'total_amount': f"{data.get('total_amount', 0):,.2f}",
                        'phone': phone,
                        'earliest_date': data.get('earliest_date', '')
                    }

                    # Расчет дней ожидания с первого заказа
                    if 'earliest_date' in data:
                        try:
                            earliest_date = datetime.strptime(data['earliest_date'], '%d.%m.%Y')
                            days_waiting = (datetime.now() - earliest_date).days
                            replacements['days_waiting'] = str(days_waiting)
                        except (ValueError, TypeError):
                            replacements['days_waiting'] = "0"

                    # Форматируем сообщение
                    message = self.format_string_safe(message, replacements)

            except KeyError as e:
                print(f"Ошибка форматирования сообщения: {e}")
                message = f"Ошибка форматирования сообщения. Отсутствует переменная {e}"
            except Exception as e:
                print(f"Неизвестная ошибка при форматировании сообщения: {e}")
                self.current_index += 1
                self.send_next_message()
                return

            # Отправляем сообщение
            if self.send_whatsapp_message(phone, message):
                # Сохраняем информацию о напоминании, если это не режим отзывов
                if self.view_mode != 'reviews':
                    self.reminder_history.add_reminder(
                        data['fio'],
                        data.get('id', 0) if self.view_mode == 'orders' else 0
                    )
                # Если это режим отзывов, сохраняем отметку о генерации ссылки
                elif data.get('mode') == 'reviews' and 'order_id' in data:
                    self.save_review_link_info(data['order_id'])

                # Обновляем прогресс
                self.progress_bar.setValue(self.current_index + 1)

                # Планируем следующую отправку
                self.current_index += 1
                QTimer.singleShot(
                    self.delay_spin.value() * 1000,
                    self.send_next_message
                )
            else:
                reply = QMessageBox.question(
                    self,
                    "Ошибка отправки",
                    f"Ошибка при отправке сообщения клиенту {data['fio']}.\n"
                    "Продолжить рассылку?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    self.current_index += 1
                    self.send_next_message()
                else:
                    self.sending_completed()

        except Exception as e:
            # Обработка общих исключений
            print(f"Общая ошибка при отправке сообщения: {str(e)}")
            show_error(self, "Ошибка", f"Ошибка при отправке сообщения: {str(e)}")
            self.sending_completed()
    def send_whatsapp_message(self, phone, message):
        """Отправка сообщения в WhatsApp"""
        try:
            if not phone:
                return False

            # Форматируем номер телефона
            phone = re.sub(r'[^\d]', '', phone)
            if phone.startswith('8'):
                phone = '7' + phone[1:]
            elif not phone.startswith('7'):
                phone = '7' + phone

            # Формируем URL для WhatsApp используя api.whatsapp.com вместо wa.me
            url = f"https://api.whatsapp.com/send?phone={phone}&text={quote(message)}"

            # Открываем WhatsApp
            QDesktopServices.openUrl(QUrl(url))
            return True

        except Exception as e:
            print(f"Ошибка отправки WhatsApp: {e}")
            return False



