import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QDialog, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QToolBar, QWidget, QDoubleValidator)
from PyQt5.QtCore import Qt, QSettings
from datetime import datetime

# Импортируем наши модули
from path_manager import PathManager, PathManagerDialog
from excel_manager import ExcelManager, ExcelWriteErrorDialog


# Имитация класса базы данных для примера
class Order:
    """Класс для имитации заказа из базы данных"""

    def __init__(self, id, fio, group, service, cost, paid_amount=0):
        self.id = id
        self.fio = fio
        self.group = group
        self.service = service
        self.cost = cost
        self.paid_amount = paid_amount
        self.remaining_amount = cost - paid_amount
        self.status = "Новый"
        self.discount = None
        self.created_date = datetime.now().date()


# Имитация менеджера базы данных
class DatabaseManager:
    """Класс для имитации менеджера базы данных"""

    def __init__(self):
        self.orders = [
            Order(1, "Иванов Иван", "ПИ-101", "Курсовая работа", 5000, 0),
            Order(2, "Петров Петр", "ИС-202", "Дипломная работа", 12000, 5000),
            Order(3, "Сидоров Сидор", "МО-303", "Расчетная работа", 3000, 3000)
        ]

    def session_scope(self):
        """Имитация менеджера контекста для сессии"""

        class SessionContext:
            def __init__(self, manager):
                self.manager = manager

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

            def query(self, cls):
                class Query:
                    def __init__(self, objects):
                        self.objects = objects

                    def get(self, id):
                        for obj in self.objects:
                            if obj.id == id:
                                return obj
                        return None

                return Query(self.manager.orders)

        return SessionContext(self)


# Имитация менеджера состояния
class StateManager:
    """Класс для имитации менеджера состояния"""

    def __init__(self):
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def notify_all(self):
        for observer in self.observers:
            if hasattr(observer, 'update_data'):
                observer.update_data()


# Класс окна оплаты
class PaymentWindow(QDialog):
    """Окно внесения оплаты"""

    def __init__(self, parent=None, order=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.state_manager = StateManager()

        if order:
            self.original_order_id = order.id
        else:
            # Для демонстрации используем первый заказ
            self.original_order_id = 1

        try:
            self.load_order_data()
            self.setup_ui()

            # Интеграция с менеджером путей
            self.integrate_path_manager()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка инициализации окна: {str(e)}")

    def load_order_data(self):
        """Загрузка данных заказа"""
        with self.db_manager.session_scope() as session:
            order = session.query(Order).get(self.original_order_id)
            if not order:
                raise ValueError(f"Заказ с ID {self.original_order_id} не найден")

            # Сохраняем данные
            self.current_data = {
                'id': order.id,
                'fio': order.fio,
                'group': order.group,
                'service': order.service,
                'cost': float(order.cost) if order.cost not in (None, 'Не указано') else 0.0,
                'paid_amount': float(order.paid_amount) if order.paid_amount not in (None, 'Не указано') else 0.0,
                'discount': order.discount if order.discount not in (None, 'Не указано') else None,
                'status': order.status
            }

            # Рассчитываем суммы
            self.discount_amount = 0
            self.discounted_total = self.current_data['cost']
            self.remaining = max(0, self.discounted_total - self.current_data['paid_amount'])

    def setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Внесение оплаты")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout(self)

        # Информация о заказе
        info_group = QVBoxLayout()
        self.fio_label = QLabel(f"ФИО: {self.current_data['fio']}")
        self.group_label = QLabel(f"Группа: {self.current_data['group']}")
        self.service_label = QLabel(f"Услуга: {self.current_data['service']}")
        self.cost_label = QLabel(f"Стоимость: {self.current_data['cost']:.2f} руб.")
        self.paid_label = QLabel(f"Уже оплачено: {self.current_data['paid_amount']:.2f} руб.")
        self.remaining_label = QLabel(f"Осталось: {self.remaining:.2f} руб.")

        if self.current_data['discount']:
            self.discount_label = QLabel(f"Скидка: {self.current_data['discount']}")
            self.discounted_cost_label = QLabel(f"Сумма со скидкой: {self.discounted_total:.2f} руб.")
            info_group.addWidget(self.discount_label)
            info_group.addWidget(self.discounted_cost_label)

        for label in [self.fio_label, self.group_label, self.service_label,
                      self.cost_label, self.paid_label, self.remaining_label]:
            info_group.addWidget(label)

        layout.addLayout(info_group)

        # Поле для ввода суммы
        payment_layout = QHBoxLayout()
        self.payment_label = QLabel("Сумма оплаты:")
        self.payment_input = QLineEdit()
        self.payment_input.setPlaceholderText("Введите сумму")
        validator = QDoubleValidator(0, 999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.payment_input.setValidator(validator)

        # Кнопка заполнения остатка
        self.fill_remaining_btn = QPushButton("Заполнить остаток")
        self.fill_remaining_btn.clicked.connect(self.fill_remaining_amount)
        self.fill_remaining_btn.setObjectName("fill_remaining_btn")

        payment_layout.addWidget(self.payment_label)
        payment_layout.addWidget(self.payment_input)
        payment_layout.addWidget(self.fill_remaining_btn)

        layout.addLayout(payment_layout)

        # Кнопки управления
        self.buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_payment)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        self.buttons_layout.addWidget(self.save_btn)
        self.buttons_layout.addWidget(self.cancel_btn)
        layout.addLayout(self.buttons_layout)

    def integrate_path_manager(self):
        """Интегрирует функциональность менеджера путей"""
        # Создаем кнопку для настройки путей
        settings_btn = QPushButton("⚙️ Настройки")

        # Создаем меню для кнопки
        from PyQt5.QtWidgets import QMenu, QAction
        settings_menu = QMenu(self)

        # Действие для управления путями
        path_action = settings_menu.addAction("📁 Управление путями")
        path_action.triggered.connect(lambda: self.show_path_manager())

        # Действие для тестирования подключения к Excel
        test_excel_action = settings_menu.addAction("🔄 Проверить Excel")
        test_excel_action.triggered.connect(lambda: self.test_excel_connection())

        # Устанавливаем меню для кнопки
        settings_btn.setMenu(settings_menu)

        # Добавляем кнопку в интерфейс окна оплаты
        self.buttons_layout.addWidget(settings_btn)

    def show_path_manager(self):
        """Показывает диалог управления путями"""
        dialog = PathManagerDialog(self)
        dialog.exec_()

    def test_excel_connection(self):
        """Проверяет подключение к Excel"""
        path_manager = PathManager()
        excel_path = path_manager.get_path('payment_excel')

        if not excel_path:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Путь к Excel-файлу платежей не указан.\n"
                "Пожалуйста, укажите путь в настройках."
            )
            return

        excel_manager = ExcelManager(self)
        success, message = excel_manager.test_excel_connection(excel_path)

        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def fill_remaining_amount(self):
        """Заполнение оставшейся суммы"""
        self.payment_input.setText(str(self.remaining))

    def save_payment(self):
        """Сохранение оплаты"""
        try:
            if not self.validate_payment():
                return False

            payment_amount = float(self.payment_input.text())

            with self.db_manager.session_scope() as session:
                # Получаем свежую версию заказа
                order = session.query(Order).get(self.original_order_id)
                if not order:
                    QMessageBox.warning(self, "Ошибка", "Заказ не найден")
                    return False

                # Обновляем данные заказа
                order.paid_amount = (order.paid_amount or 0) + payment_amount
                order.remaining_amount = self.discounted_total - order.paid_amount

                # Сохраняем дату при любой оплате
                order.payment_date = datetime.now().date()

                # Обновляем статус
                if order.remaining_amount <= 0:
                    order.status = 'Выполнен'
                elif order.remaining_amount > 0 and order.status != 'В работе':
                    order.status = 'В ожидании оплаты'

                # Добавляем запись в Excel
                self.add_excel_record(order, payment_amount)

                # Уведомляем об изменениях
                self.state_manager.notify_all()

                QMessageBox.information(self, "Успех", "Оплата успешно внесена!")
                self.accept()
                return True

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении оплаты: {str(e)}")
            return False

    def add_excel_record(self, order, payment_amount):
        """Добавляет запись в Excel после успешного внесения платежа"""
        try:
            # Создаем менеджер для работы с Excel
            excel_manager = ExcelManager(self)

            # Подготавливаем данные для записи
            payment_data = {
                'date': datetime.now(),
                'client': order.fio,
                'service': order.service,
                'amount': payment_amount
            }

            # Добавляем запись в Excel
            excel_manager.add_payment_to_excel(payment_data)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"Ошибка при добавлении записи в Excel: {str(e)}"
            )

    def validate_payment(self):
        """Проверка валидности платежа"""
        try:
            if not self.payment_input.text():
                raise ValueError("Введите сумму оплаты")

            payment_amount = float(self.payment_input.text())
            if payment_amount <= 0:
                raise ValueError("Сумма оплаты должна быть больше 0")

            if payment_amount > self.remaining:
                raise ValueError("Сумма оплаты превышает остаток")

            return True
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return False


# Класс главного окна приложения
class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.state_manager = StateManager()
        self.state_manager.add_observer(self)
        self.initUI()

    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle('Система управления заказами')
        self.setGeometry(100, 100, 800, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Создаем тулбар
        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        # Кнопки
        new_payment_btn = QPushButton("💰 Внести оплату")
        new_payment_btn.clicked.connect(self.show_payment_window)
        self.toolbar.addWidget(new_payment_btn)

        path_manager_btn = QPushButton("📁 Управление путями")
        path_manager_btn.clicked.connect(self.show_path_manager)
        self.toolbar.addWidget(path_manager_btn)

        # Таблица заказов
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['ID', 'ФИО', 'Группа', 'Услуга', 'Сумма'])
        self.load_data()

        main_layout.addWidget(self.table)

    def load_data(self):
        """Загрузка данных в таблицу"""
        with self.db_manager.session_scope() as session:
            orders = session.query(Order).get_all()

            self.table.setRowCount(len(orders))
            for row, order in enumerate(orders):
                self.table.setItem(row, 0, QTableWidgetItem(str(order.id)))
                self.table.setItem(row, 1, QTableWidgetItem(order.fio))
                self.table.setItem(row, 2, QTableWidgetItem(order.group))
                self.table.setItem(row, 3, QTableWidgetItem(order.service))
                self.table.setItem(row, 4, QTableWidgetItem(f"{order.cost:.2f}"))

        self.table.resizeColumnsToContents()

    def show_payment_window(self):
        """Показ окна внесения оплаты"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            order_id = int(self.table.item(current_row, 0).text())

            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if order:
                    dialog = PaymentWindow(self, order)
                    if dialog.exec_() == QDialog.Accepted:
                        self.load_data()
        else:
            QMessageBox.warning(self, "Предупреждение", "Выберите заказ для внесения оплаты")

    def show_path_manager(self):
        """Показ окна управления путями"""
        dialog = PathManagerDialog(self)
        dialog.exec_()

    def update_data(self):
        """Обновление данных"""
        self.load_data()


# Добавляем методы для имитации полной функциональности DatabaseManager
def get_all(self):
    return self.objects


DatabaseManager.session_scope().query(Order).get_all = get_all


# Основная функция для запуска приложения
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()