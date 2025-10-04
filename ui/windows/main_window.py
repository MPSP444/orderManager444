import base64

from google.auth.transport import requests

from core.database import init_database
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QInputDialog, QAction, QDialogButtonBox, QFormLayout
import os
from datetime import datetime
from PyQt5.QtWidgets import (QFileDialog)
import json
from ui.components.kanban_board import KanbanBoard
from .discount_manager import DiscountManager
from ..buttons import *
from .new_order_window import NewOrderWindow
from core.database import Order
from core.database_manager import DatabaseManager
from .state_manager import StateManager
from .payment_window import PaymentWindow
from ui.message_utils import show_error
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QTableWidget, QToolBar,
                             QDialog, QTableWidgetItem, QMessageBox, QMenu)
from PyQt5.QtCore import Qt
from ui.styles import MAIN_THEME
from PyQt5.QtWidgets import QLineEdit, QLabel
from sqlalchemy import or_, cast, String
from ui.windows.path_settings import PathSettingsDialog
from PyQt5.QtCore import QSettings
from reviews_manager import init_reviews_module


import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        print("MainWindow.__init__ - начало")
        try:
            # Инициализация базы данных и менеджеров
            self.db_manager = DatabaseManager()
            print("Database manager инициализирован")

            # Инициализируем менеджер отзывов как None, он будет создан при необходимости
            self.review_manager = None

            self.state_manager = StateManager()
            print("State manager инициализирован")

            self.state_manager.add_observer(self)
            print("Observer добавлен")

            # Настройка горячих клавиш
            self.setupShortcuts()
            print("Горячие клавиши настроены")

            # Инициализация UI
            self.initUI()
            print("UI инициализирован")

            # Инициализируем модуль управления отзывами ПОСЛЕ основного UI
            # Эта часть будет выполнена только если инициализация UI прошла успешно
            # и self.tabs существует
            if hasattr(self, 'tabs'):
                try:
                    from reviews_manager import init_reviews_module
                    print("Начинаем инициализацию модуля управления отзывами")
                    init_reviews_module(self)
                    print("Модуль управления отзывами успешно инициализирован")
                except Exception as e:
                    print(f"Ошибка при инициализации модуля управления отзывами: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("Предупреждение: атрибут 'tabs' не найден, модуль управления отзывами не инициализирован")

        except Exception as e:
            print(f"Ошибка в MainWindow.__init__: {e}")
            import traceback
            traceback.print_exc()

        print("MainWindow.__init__ - конец")

        # Устанавливаем таймеры обновления после инициализации всех компонентов
        QTimer.singleShot(1000, lambda: self.setupUpdateTimer() if hasattr(self, 'setupUpdateTimer') else None)
    def initUI(self):
        """Инициализация пользовательского интерфейса"""
        # Настройка основного окна
        self.setWindowTitle('Система управления заказами')
        self.setGeometry(100, 100, 1200, 800)

        # Создаем центральный виджет и главный layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Создаем тулбар
        self.createToolBar()

        # Создаем и настраиваем табы
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Инициализируем вкладку заказов
        self.init_orders_tab()

        # Вкладка Kanban
        self.kanban_tab = QWidget()
        kanban_layout = QVBoxLayout(self.kanban_tab)
        kanban_layout.setContentsMargins(0, 0, 0, 0)
        kanban_layout.setSpacing(0)
        self.kanban_board = KanbanBoard(parent=self)
        kanban_layout.addWidget(self.kanban_board)

        # Вкладка "Справочник услуг"
        from .service_catalog.main_catalog_window import ServiceCatalogWindow
        self.catalog_tab = ServiceCatalogWindow()

        # Добавляем вкладки в таб-виджет
        self.tabs.addTab(self.orders_tab, "📝 Все заказы")
        self.tabs.addTab(self.kanban_tab, "📋 Kanban")
        self.tabs.addTab(self.catalog_tab, "📚 Справочник услуг")

        # Добавляем вкладки в главный layout
        main_layout.addWidget(self.tabs)

        # Создаем и настраиваем статусную строку
        self.statusBar().showMessage('Готово к работе')

        # Применяем главную тему
        self.setStyleSheet(MAIN_THEME)

        # Настраиваем контекстное меню для таблицы
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        # Восстанавливаем сохраненные настройки окна
        settings = QSettings("OrderManager", "MainWindow")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

        # Восстанавливаем последнюю активную вкладку
        last_tab = settings.value("lastTab", 0, type=int)
        if last_tab < self.tabs.count():
            self.tabs.setCurrentIndex(last_tab)

        self.load_data()

        # Настраиваем таймер обновления
        self.setupUpdateTimer()

        # Устанавливаем фокус на поле поиска
        if hasattr(self, 'search_input'):
            self.search_input.setFocus()

    def test_github_token(self, token):
        """Проверка валидности токена GitHub"""
        try:
            import requests
            headers = {"Authorization": f"token {token}"}
            response = requests.get("https://api.github.com/user", headers=headers)

            if response.status_code == 200:
                user_data = response.json()
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Токен действителен! Авторизован как: {user_data.get('login')}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    f"Токен недействителен или не имеет необходимых прав. Код: {response.status_code}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при проверке токена: {str(e)}")



    def init_orders_tab(self):
        """Инициализация вкладки со всеми заказами"""
        # Создаем вкладку
        self.orders_tab = QWidget()

        # Создаем основной layout для вкладки
        orders_layout = QVBoxLayout()

        # Создаем и добавляем поисковую панель
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите ФИО или номер заказа")
        self.search_input.textChanged.connect(self.search_orders)
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 15px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()

        # Добавляем поисковую панель в основной layout
        orders_layout.addLayout(search_layout)

        # Добавляем кнопки фильтров
        filters_layout = self.setup_filters()
        orders_layout.addLayout(filters_layout)

        # Создаем и добавляем таблицу
        self.table = QTableWidget()
        self.table.setObjectName("mainTable")
        self.init_table()
        orders_layout.addWidget(self.table)

        # Устанавливаем layout для вкладки
        self.orders_tab.setLayout(orders_layout)

    def setup_filters(self):
        """Настройка кнопок фильтрации"""
        filters_layout = QHBoxLayout()

        # Создаем все кнопки фильтров
        self.all_clients_btn = AllClientsButton()
        self.all_clients_btn.clicked.connect(lambda: self.apply_filter('all'))

        self.new_orders_filter_btn = NewOrdersButton()
        self.new_orders_filter_btn.clicked.connect(lambda: self.apply_filter('new'))

        self.in_progress_btn = InProgressButton()
        self.in_progress_btn.clicked.connect(lambda: self.apply_filter('in_progress'))

        self.paid_orders_btn = PaidOrdersButton()
        self.paid_orders_btn.clicked.connect(lambda: self.apply_filter('paid'))

        self.debtors_btn = DebtorsButton()
        self.debtors_btn.clicked.connect(lambda: self.apply_filter('debtors'))

        self.completed_btn = CompletedOrdersButton()
        self.completed_btn.clicked.connect(lambda: self.apply_filter('completed'))

        self.waiting_payment_btn = WaitingPaymentButton()
        self.waiting_payment_btn.clicked.connect(lambda: self.apply_filter('waiting'))

        self.canceled_btn = CanceledOrdersButton()
        self.canceled_btn.clicked.connect(lambda: self.apply_filter('canceled'))

        self.unique_clients_btn = UniqueClientsButton()
        self.unique_clients_btn.clicked.connect(self.load_unique_clients)

        # Добавляем кнопки в layout
        filters_layout.addWidget(self.unique_clients_btn)
        filters_layout.addWidget(self.all_clients_btn)
        filters_layout.addWidget(self.new_orders_filter_btn)
        filters_layout.addWidget(self.in_progress_btn)
        filters_layout.addWidget(self.paid_orders_btn)
        filters_layout.addWidget(self.debtors_btn)
        filters_layout.addWidget(self.completed_btn)
        filters_layout.addWidget(self.waiting_payment_btn)
        filters_layout.addWidget(self.canceled_btn)

        # Обновляем счетчики на кнопках
        self.update_filter_counts()

        return filters_layout

    # В методе setupUpdateTimer класса MainWindow добавим:
    def setupUpdateTimer(self):
        """Настройка таймера обновления данных"""
        # Проверяем, не создан ли уже таймер
        if hasattr(self, 'discount_timer'):
            return
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.refreshData)

        # Добавим таймер для проверки скидок
        self.discount_timer = QTimer(self)
        self.discount_timer.timeout.connect(self.check_discounts)
        self.discount_timer.start(360000)  # Проверка каждый час

    def check_discounts(self):
        """Проверка и обновление скидок"""
        try:
            print("=== Начало проверки скидок ===")
            with self.db_manager.session_scope() as session:
                upcoming = DiscountManager.get_upcoming_expirations(session)
                print(f"Получено заказов со скидками: {len(upcoming) if upcoming else 0}")

                if upcoming:
                    message = "Скоро истекут скидки:\n"
                    processed_orders = set()

                    for order in upcoming:
                        print(f"Обработка заказа ID: {order.id}, ФИО: {order.fio}")
                        if order.id in processed_orders:
                            print(f"Заказ {order.id} уже обработан, пропускаем")
                            continue

                        now = datetime.now()
                        time_diff = order.discount_end_date - now
                        time_str = f"{time_diff.days}д {time_diff.seconds // 3600}ч {(time_diff.seconds % 3600) // 60}м"

                        message += f"• Заказ #{order.id} - {order.fio}\n"
                        message += f"  Скидка {order.discount} истекает через {time_str}\n"
                        processed_orders.add(order.id)
                        print(f"Заказ {order.id} добавлен в уведомление")

                    if processed_orders:
                        print(f"Показываем уведомление для {len(processed_orders)} заказов")
                        print("Сообщение:", message)
                        QMessageBox.warning(self, "Уведомление о скидках", message)

            print("=== Конец проверки скидок ===")

        except Exception as e:
            print(f"Ошибка при проверке скидок: {str(e)}")
            show_error(self, "Ошибка", f"Ошибка при проверке скидок: {str(e)}")


    def refreshData(self):
        """Обновление данных по таймеру"""
        if not hasattr(self, 'is_refreshing') or not self.is_refreshing:
            try:
                self.is_refreshing = True
                self.load_data()  # Перезагружаем данные

                # Обновляем канбан если находимся на его вкладке
                if hasattr(self, 'kanban_board') and self.tabs.currentWidget() == self.kanban_tab:
                    self.kanban_board.loadOrders()

            finally:
                self.is_refreshing = False

    def setupShortcuts(self):
        """Настройка горячих клавиш"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence

        shortcuts = [
            (QKeySequence("Ctrl+N"), self.showNewOrderDialog),
            (QKeySequence("Ctrl+K"), lambda: self.tabs.setCurrentWidget(self.kanban_tab)),
            (QKeySequence("Ctrl+T"), lambda: self.tabs.setCurrentWidget(self.orders_tab)),
            (QKeySequence("Ctrl+R"), self.refreshCurrentTab),
            (QKeySequence("Ctrl+F"), self.focusSearch),
            (QKeySequence("Ctrl+B"), self.createBackup),
            (QKeySequence("Ctrl+Return"), self.open_selected_folder),
            (QKeySequence("Ctrl+E"), self.edit_selected_order),
            (QKeySequence("Ctrl+Q"), self.cancel_selected_order),
            (QKeySequence("Ctrl+O"), self.add_payment_selected)
        ]

        for key, callback in shortcuts:
            QShortcut(key, self).activated.connect(callback)

    def refreshCurrentTab(self):
        """Обновление текущей вкладки"""
        current_tab = self.tabs.currentWidget()
        if current_tab == self.kanban_tab:
            self.kanban_board.loadOrders()
        elif current_tab == self.orders_tab:
            self.load_data()

    def focusSearch(self):
        """Фокус на поле поиска"""
        if hasattr(self, 'search_input'):
            self.search_input.setFocus()

    def createBackup(self):
        """Создание резервной копии"""
        self.create_backup()
    def on_tab_changed(self, index):
        """Обработчик смены вкладки"""
        try:
            current_tab = self.tabs.widget(index)

            # Если это вкладка с Kanban доской
            if current_tab == self.kanban_tab:
                # Обновляем данные в канбан-борде
                if hasattr(self, 'kanban_board'):
                    self.kanban_board.loadOrders()

        except Exception as e:
            print(f"Ошибка при обновлении вкладки: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении вкладки: {str(e)}")

    def update_data(self):
        """Обновление данных при изменении состояния"""
        print("Обновление данных в главном окне")

        # Обновляем канбан если находимся на вкладке канбана
        if hasattr(self, 'kanban_board') and self.tabs.currentWidget() == self.kanban_tab:
            self.kanban_board.loadOrders()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        try:
            # Очищаем ресурсы канбан-борда если он существует
            if hasattr(self, 'kanban_board'):
                self.kanban_board.cleanup()

            # Сохраняем настройки
            settings = QSettings("OrderManager", "MainWindow")
            settings.setValue("geometry", self.saveGeometry())
            settings.setValue("windowState", self.saveState())
            settings.setValue("lastTab", self.tabs.currentIndex())

            event.accept()

        except Exception as e:
            print(f"Ошибка при закрытии окна: {e}")
            event.accept()



    def showEvent(self, event):
        """Обработка показа окна"""
        super().showEvent(event)

        try:
            # Загружаем сохраненные настройки
            settings = QSettings("OrderManager", "MainWindow")

            # Восстанавливаем геометрию окна
            if settings.value("geometry"):
                self.restoreGeometry(settings.value("geometry"))

            # Восстанавливаем состояние окна
            if settings.value("windowState"):
                self.restoreState(settings.value("windowState"))

            # Восстанавливаем последнюю активную вкладку
            last_tab = settings.value("lastTab", 0, type=int)
            if last_tab < self.tabs.count():
                self.tabs.setCurrentIndex(last_tab)

            # Загружаем данные для текущей вкладки
            self.on_tab_changed(self.tabs.currentIndex())

        except Exception as e:
            print(f"Ошибка при показе окна: {e}")
    def load_data(self, filter_condition=None):
        """Загрузка данных в таблицу"""
        try:
            # Загружаем настройки колонок
            with open('column_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)

            visible_columns = [col for col, enabled in settings.items() if enabled]

            self.table.setColumnCount(len(visible_columns))
            self.table.setHorizontalHeaderLabels(visible_columns)

            # Получаем данные через DatabaseManager
            with self.db_manager.session_scope() as session:
                query = session.query(Order)

                if filter_condition is not None:
                    query = query.filter(filter_condition)

                orders = query.all()

                self.table.setRowCount(0)
                self.table.setRowCount(len(orders))

                for row, order in enumerate(orders):
                    for col, column_name in enumerate(visible_columns):
                        attr_name = self.column_to_attr(column_name)
                        value = getattr(order, attr_name, '')

                        # Форматирование значения
                        if value is None:
                            formatted_value = ''
                        elif isinstance(value, (int, float)):
                            formatted_value = f"{value:,.2f}" if isinstance(value, float) else str(value)
                        elif isinstance(value, datetime):
                            formatted_value = value.strftime('%d.%m.%Y')
                        else:
                            formatted_value = str(value)

                        item = QTableWidgetItem(formatted_value)
                        item.setData(Qt.UserRole, order.id)

                        if isinstance(value, (int, float)):
                            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                        self.table.setItem(row, col, item)

            self.table.resizeColumnsToContents()
            self.update_filter_counts()

        except Exception as e:
            show_error(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')


    def edit_order(self, row):
        """Редактирование заказа"""
        try:
            order_id = self.table.item(row, 0).data(Qt.UserRole)

            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if order:
                    dialog = NewOrderWindow(self, order=order)
                    if dialog.exec_() == QDialog.Accepted:
                        # Обновление произойдет через StateManager
                        self.state_manager.notify_all()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при редактировании: {str(e)}")

    def add_payment(self, row):
        """Внесение оплаты"""
        try:
            order_id = self.table.item(row, 0).data(Qt.UserRole)

            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if order:
                    session.refresh(order)  # Обновляем данные заказа
                    dialog = PaymentWindow(self, order=order)
                    if dialog.exec_() == QDialog.Accepted:
                        # Обновление произойдет через StateManager
                        self.state_manager.notify_all()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при внесении оплаты: {str(e)}")
    def search_orders(self, text):
        """Поиск заказов"""
        try:
            with self.db_manager.session_scope() as session:
                if not text.strip():
                    self.load_data()
                    return

                search_pattern = f"%{text.strip()}%"

                query = session.query(Order).filter(
                    or_(
                        Order.fio.ilike(search_pattern),
                        Order.group.ilike(search_pattern),
                        cast(Order.id, String).ilike(search_pattern),
                        Order.phone.ilike(search_pattern),
                        Order.teacher_name.ilike(search_pattern),
                        Order.service.ilike(search_pattern)
                    )
                )

                orders = query.all()
                self.update_table_with_orders(orders)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске: {str(e)}")

    def update_table_with_orders(self, orders):
        """Обновление таблицы результатами"""
        try:
            with open('column_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            visible_columns = [col for col, enabled in settings.items() if enabled]

            self.table.setRowCount(0)
            self.table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                for col, column_name in enumerate(visible_columns):
                    attr_name = self.column_to_attr(column_name)
                    value = getattr(order, attr_name, '')

                    if value is None:
                        formatted_value = ''
                    elif isinstance(value, (int, float)):
                        formatted_value = f"{value:,.2f}" if isinstance(value, float) else str(value)
                    else:
                        formatted_value = str(value)

                    item = QTableWidgetItem(formatted_value)
                    item.setData(Qt.UserRole, order.id)
                    self.table.setItem(row, col, item)

            self.update_filter_counts()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении таблицы: {str(e)}")


    def fill_fields(self, order):
        """Заполнение полей данными заказа"""
        self.fio_input.setText(order.fio)
        self.group_input.setText(order.group)
        self.services_combo.setCurrentText(order.service)
        self.direction_input.setText(order.direction)
        self.theme_input.setText(order.theme)
        self.quantity_spin.setValue(order.quantity or 1)
        self.login_input.setText(order.login)
        self.password_input.setText(order.password)
        self.website_input.setText(order.website)
        self.cost_spin.setValue(order.cost or 0)
        self.prepay_spin.setValue(order.paid_amount or 0)
        self.discount_combo.setCurrentText(order.discount or '0%')
        self.phone_input.setText(order.phone)
        self.teacher_input.setText(order.teacher_name)
        self.teacher_email_input.setText(order.teacher_email)
        self.comment_text.setText(order.comment)
        if order.deadline:
            index = self.deadline_combo.findText(order.deadline)
            if index >= 0:
                self.deadline_combo.setCurrentIndex(index)



    def showImportDialog(self):
        """Открывает диалог импорта Excel"""
        print("Метод showImportDialog вызван!")
        from ui.windows.excel_preview import ExcelPreviewDialog  # Изменили импорт
        dialog = ExcelPreviewDialog(self)
        dialog.exec_()

    def init_table(self):
        """Инициализация таблицы с данными"""
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)  # Включаем поддержку контекстного меню
        self.table.customContextMenuRequested.connect(self.show_context_menu)  # Подключаем обработчик
        self.update_table_columns()
        return self.table

    def setup_shortcuts(self):
        """Настройка горячих клавиш"""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence

        # Ctrl+N - Новый заказ
        new_order_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_order_shortcut.activated.connect(self.showNewOrderDialog)

        # Ctrl+Enter - Открытие папки
        open_folder_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        open_folder_shortcut.activated.connect(self.open_selected_folder)

        # Ctrl+E - Редактирование заказа
        edit_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        edit_shortcut.activated.connect(self.edit_selected_order)

        # Ctrl+Q - Отмена заказа
        cancel_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        cancel_shortcut.activated.connect(self.cancel_selected_order)

        # Ctrl+O - Внесение оплаты
        payment_shortcut = QShortcut(QKeySequence("Ctrl+O"), self)
        payment_shortcut.activated.connect(self.add_payment_selected)

    def open_selected_folder(self):
        """Открытие папки выбранного заказа"""
        if not self.table:
            return

        current_row = self.table.currentRow()
        if current_row >= 0:
            try:
                # Получаем ID заказа
                order_id = self.table.item(current_row, 0).data(Qt.UserRole)
                session = init_database()
                order = session.query(Order).filter(Order.id == order_id).first()

                if order:
                    # Базовый путь к папкам клиентов
                    base_path = r"D:\Users\mgurbanmuradov\Documents\Общая"
                    client_path = os.path.join(base_path, order.fio)
                    works_path = os.path.join(client_path, "Работы")
                    service_path = os.path.join(works_path, order.service)

                    # Создаем папки если их нет
                    os.makedirs(service_path, exist_ok=True)
                    os.startfile(service_path)

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии папки: {str(e)}")
            finally:
                if session:
                    session.close()

    def edit_selected_order(self):
        """Редактирование выбранного заказа"""
        if not self.table:
            return

        current_row = self.table.currentRow()
        if current_row >= 0:
            self.edit_order(current_row)

    def cancel_selected_order(self):
        """Отмена выбранного заказа"""
        if not self.table:
            return

        current_row = self.table.currentRow()
        if current_row >= 0:
            self.cancel_order(current_row)

    def add_payment_selected(self):
        """Внесение оплаты для выбранного заказа"""
        if not self.table:
            return

        current_row = self.table.currentRow()
        if current_row >= 0:
            self.add_payment(current_row)


    def show_context_menu(self, position):
        menu = QMenu()

        # Получаем выбранную строку
        row = self.table.rowAt(position.y())
        if row >= 0:
            self.table.selectRow(row)

            # Существующие пункты меню
            edit_action = menu.addAction("✏️ Редактировать")
            payment_action = menu.addAction("💰 Внести оплату")
            status_action = menu.addAction("🔄 Сменить статус")

            menu.addSeparator()
            info_menu = menu.addMenu("ℹ️ Информация")
            client_info_action = info_menu.addAction("👤 Информация о клиенте")
            order_info_action = info_menu.addAction("📋 Информация о заказе")
            detailed_info_action = info_menu.addAction("📊 Подробная информация")
            # Добавляем пункт для отзывов
            menu.addSeparator()
            review_action = menu.addAction("🌟 Отправить ссылку для отзыва")
            # Добавляем новый пункт меню
            menu.addSeparator()
            open_folder_action = menu.addAction("📁 Открыть папку")

            menu.addSeparator()
            cancel_action = menu.addAction("⛔ Отменить заказ")
            delete_action = menu.addAction("❌ Удалить")

            action = menu.exec_(self.table.viewport().mapToGlobal(position))

            if action == edit_action:
                self.edit_order(row)
            elif action == payment_action:
                self.add_payment(row)
            elif action == status_action:
                self.change_status(row)
            elif action == client_info_action:
                self.show_client_info(row)
            elif action == cancel_action:
                self.cancel_order(row)
            elif action == delete_action:
                self.delete_order(row)
            elif action == order_info_action:
                self.show_order_info(row)
            elif action == detailed_info_action:
                self.show_detailed_info(row)
            elif action == open_folder_action:
                self.open_client_folder(row)
            elif action == review_action:
                self.generate_review_link_for_order(row)

    def generate_review_link_for_order(self, row):
        """Генерация и отправка ссылки для отзыва"""
        try:
            order_id = self.table.item(row, 0).data(Qt.UserRole)
            session = init_database()
            try:
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    # Проверяем, что заказ в статусе "Выполнен"
                    if order.status != 'Выполнен':
                        reply = QMessageBox.question(
                            self,
                            "Подтверждение",
                            f"Заказ #{order.id} не отмечен как выполненный. Отметить как выполненный и создать ссылку для отзыва?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes
                        )

                        if reply == QMessageBox.Yes:
                            order.status = 'Выполнен'
                            session.commit()
                        else:
                            return

                    # Инициализируем менеджер отзывов, если он не был инициализирован
                    if self.review_manager is None:
                        self.init_review_manager()

                    if self.review_manager is None:
                        raise Exception("Не удалось инициализировать менеджер отзывов")

                    # Генерируем ссылку
                    review_link = self.review_manager.generate_review_link(
                        order_id=order.id,
                        service_name=order.service,
                        client_name=order.fio
                    )

                    # Показываем диалог с ссылкой
            finally:
                session.close()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось создать ссылку для отзыва: {str(e)}"
            )

    def open_client_folder(self, row):
        """Открытие папки клиента"""
        try:
            # Получаем данные заказа
            order_id = self.table.item(row, 0).data(Qt.UserRole)
            session = init_database()
            order = session.query(Order).filter(Order.id == order_id).first()

            if order:
                # Базовый путь к папкам клиентов
                base_path = r"D:\Users\mgurbanmuradov\Documents\Общая"

                # Создаем путь к папке клиента
                client_path = os.path.join(base_path, order.fio)
                works_path = os.path.join(client_path, "Работы")
                service_path = os.path.join(works_path, order.service)

                # Проверяем существование папок и создаем их при необходимости
                os.makedirs(service_path, exist_ok=True)

                # Открываем папку
                os.startfile(service_path)

            session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии папки: {str(e)}")
    def show_detailed_info(self, row):
        """Показ подробной информации о клиенте"""
        try:
            # Получаем ID заказа
            item = self.table.item(row, 0)
            if not item:
                raise ValueError("Не удалось получить данные выбранной строки")

            order_id = item.data(Qt.UserRole)
            if not order_id:
                raise ValueError("Не удалось получить ID заказа")

            # Получаем заказ из базы
            session = init_database()
            try:
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    from .detailed_info_window import DetailedInfoWindow
                    dialog = DetailedInfoWindow(self, client_fio=order.fio)
                    dialog.exec_()
            finally:
                session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении подробной информации: {str(e)}")
    def show_client_info(self, row):
        """Показ информации о клиенте"""
        try:
            # Получаем ID заказа
            item = self.table.item(row, 0)
            if not item:
                raise ValueError("Не удалось получить данные выбранной строки")

            order_id = item.data(Qt.UserRole)
            if not order_id:
                raise ValueError("Не удалось получить ID заказа")

            # Получаем данные клиента из базы
            session = init_database()
            try:
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    from .client_info_window import ClientInfoWindow
                    dialog = ClientInfoWindow(self, client_fio=order.fio)
                    dialog.exec_()
            finally:
                session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении информации о клиенте: {str(e)}")
            print(f"Ошибка при получении информации о клиенте: {e}")  # Для отладки

    def show_order_info(self, row):
        """Показ информации о заказе"""
        try:
            # Получаем ID заказа
            item = self.table.item(row, 0)
            if not item:
                raise ValueError("Не удалось получить данные выбранной строки")

            order_id = item.data(Qt.UserRole)
            if not order_id:
                raise ValueError("Не удалось получить ID заказа")

            # Получаем заказ из базы
            session = init_database()
            try:
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    from .order_info_window import OrderInfoWindow
                    dialog = OrderInfoWindow(self, order=order)
                    dialog.exec_()
            finally:
                session.close()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении информации о заказе: {str(e)}")

    def change_status(self, row):
        try:
            order_id = self.table.item(row, 0).data(Qt.UserRole)
            session = init_database()
            try:
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    # Показываем диалог выбора статуса
                    statuses = ['Новый', 'В работе', 'В ожидании оплаты', 'Выполнен', 'Отказ']
                    status, ok = QInputDialog.getItem(
                        self, "Изменение статуса",
                        "Выберите новый статус:",
                        statuses, 0, False
                    )

                    if ok and status:
                        old_status = order.status
                        order.status = status

                        # При изменении статуса обновляем даты скидки
                        if status == 'В ожидании оплаты':
                            order.update_discount_dates()

                        # Если статус изменен на "Выполнен", предлагаем создать ссылку для отзыва
                        if status == 'Выполнен' and old_status != 'Выполнен':
                            self.offer_review_link(order)

                        session.commit()
                        self.load_data()
            finally:
                session.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")

    def configure_reviews_manager(self):
        """Настройка менеджера отзывов"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Настройки менеджера отзывов")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Загружаем текущие настройки
        settings = QSettings("OrderManager", "ReviewsManager")
        mysql_host = settings.value("mysql_host", "localhost")
        mysql_user = settings.value("mysql_user", "u3054108_Mukam1")
        mysql_password = settings.value("mysql_password", "vYL-f2w-cNk-fuJ")
        mysql_database = settings.value("mysql_database", "u3054108_reviews_db")

        # Создаем поля для ввода настроек MySQL
        form_layout = QFormLayout()

        host_input = QLineEdit(mysql_host)
        form_layout.addRow("Хост MySQL:", host_input)

        user_input = QLineEdit(mysql_user)
        form_layout.addRow("Пользователь:", user_input)

        password_input = QLineEdit(mysql_password)
        password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Пароль:", password_input)

        database_input = QLineEdit(mysql_database)
        form_layout.addRow("База данных:", database_input)

        layout.addLayout(form_layout)

        # Кнопка тестирования соединения
        test_btn = QPushButton("Проверить соединение")
        test_btn.clicked.connect(lambda: self.test_mysql_connection(
            host_input.text(),
            user_input.text(),
            password_input.text(),
            database_input.text()
        ))
        layout.addWidget(test_btn)

        # Кнопки OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.save_mysql_settings(
            host_input.text(),
            user_input.text(),
            password_input.text(),
            database_input.text(),
            dialog
        ))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()




    def get_selected_order_id(self):
        """Получение ID выбранного заказа"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите заказ для редактирования")
            return None

        row = self.table.currentRow()
        # Получаем ID заказа из данных таблицы
        order_id = self.table.item(row, 0).data(Qt.UserRole)  # Будем хранить ID в UserRole
        return order_id



    def cancel_order(self, row):
        """Отмена заказа"""
        reply = QMessageBox.question(self, 'Подтверждение',
                                     'Вы уверены, что хотите отменить этот заказ?',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            session = init_database()
            try:
                order_id = self.table.item(row, 0).data(Qt.UserRole)
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    order.status = 'Отказ'
                    session.commit()
                    self.load_data()
            finally:
                session.close()

    def delete_order(self, row):
        """Удаление заказа"""
        reply = QMessageBox.question(self, 'Подтверждение',
                                     'Вы уверены, что хотите удалить этот заказ?',
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            session = init_database()
            try:
                order_id = self.table.item(row, 0).data(Qt.UserRole)
                order = session.query(Order).filter(Order.id == order_id).first()
                if order:
                    session.delete(order)
                    session.commit()
                    self.load_data()
            finally:
                session.close()

    def update_table_columns(self):
        """Обновление колонок таблицы согласно сохраненным настройкам"""
        try:
            # Загружаем сохраненные настройки колонок
            with open('column_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)

            # Получаем список выбранных колонок
            columns = [col for col, enabled in settings.items() if enabled]

            # Устанавливаем количество колонок
            self.table.setColumnCount(len(columns))
            # Устанавливаем заголовки
            self.table.setHorizontalHeaderLabels(columns)

        except FileNotFoundError:
            # Если файл настроек не найден, показываем все колонки
            columns = ['ФИО', 'Группа', 'Услуги', 'СТОИМОСТЬ', 'Статус']  # базовые колонки
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)

    def showColumnSettings(self):
        """Показ диалога настройки колонок"""
        from .column_settings import ColumnSettingsDialog
        dialog = ColumnSettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_table_columns()  # Обновляем таблицу после изменения настроек



    def column_to_attr(self, column_name):
        """Преобразование названия колонки в имя атрибута"""
        mapping = {
            'ФИО': 'fio',
            'Группа': 'group',
            'Услуги': 'service',
            'Направление': 'direction',
            'Тема': 'theme',
            'Кол-во': 'quantity',
            'Логин': 'login',
            'Пароль': 'password',
            'Сайт': 'website',
            'СТОИМОСТЬ': 'cost',
            'Оплатил': 'paid_amount',
            'Осталось': 'remaining_amount',
            'Общая сумма': 'total_amount',
            'ФИО ПРЕПОДАВАТЕЛЯ': 'teacher_name',
            'ПОЧТА ПРЕПОДАВАТЕЛЯ': 'teacher_email',
            'Телефон': 'phone',
            'Дата': 'created_date',
            'Срок': 'deadline',
            'Дата Оплаты': 'payment_date',
            'Комментарий': 'comment',
            'Статус': 'status',
            'Скидка': 'discount'
        }
        return mapping.get(column_name, column_name.lower())
    def update_table_columns(self):
        """Обновление колонок таблицы согласно сохраненным настройкам"""
        try:
            with open('column_settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)

            columns = [col for col, enabled in settings.items() if enabled]

            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)

            # Загружаем данные после обновления колонок
            self.load_data()

        except FileNotFoundError:
            columns = ['ФИО', 'Группа', 'Услуги', 'СТОИМОСТЬ', 'Статус']
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.load_data()

    def createToolBar(self):
        """Создание панели инструментов"""
        # Создаем тулбар
        self.toolbar = QToolBar()
        self.toolbar.setObjectName("mainToolBar")  # Добавляем это
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        # Кнопка нового заказа
        new_order_btn = QPushButton("📝 Новый заказ")
        new_order_btn.clicked.connect(self.showNewOrderDialog)
        self.toolbar.addWidget(new_order_btn)
        self.toolbar.addSeparator()

        # Кнопка статистики
        stats_btn = QPushButton("📊 Статистика")
        stats_btn.clicked.connect(self.showStatistics)
        self.toolbar.addWidget(stats_btn)





        # Остальные кнопки...
        loyalty_btn = QPushButton("💎 Система лояльности")
        loyalty_btn.clicked.connect(self.showLoyaltySystem)
        self.toolbar.addWidget(loyalty_btn)

        import_btn = QPushButton("📥 Импорт Excel")
        import_btn.clicked.connect(self.showImportDialog)
        self.toolbar.addWidget(import_btn)
        self.toolbar.addSeparator()

        export_btn = QPushButton("📤 Экспорт")
        export_btn.clicked.connect(self.showExportDialog)
        self.toolbar.addWidget(export_btn)

        columns_btn = QPushButton("⚙️ Настройка колонок")
        columns_btn.clicked.connect(self.showColumnSettings)
        self.toolbar.addWidget(columns_btn)
        self.toolbar.addSeparator()

        # Кнопка настройки путей
        path_manager_btn = QPushButton("📁 Управление путями")
        path_manager_btn.clicked.connect(self.showPathManager)
        self.toolbar.addWidget(path_manager_btn)

        # Добавляем кнопку выбора темы
        theme_menu = QMenu()
        theme_menu.addAction("🌞 Светлая тема").triggered.connect(lambda: self.changeTheme("light"))
        theme_menu.addAction("🌙 Темная тема").triggered.connect(lambda: self.changeTheme("dark"))
        theme_menu.addAction("🌊 Синий градиент").triggered.connect(lambda: self.changeTheme("blue_gradient"))
        theme_menu.addAction("🍇 Элегантный фиолетовый").triggered.connect(lambda: self.changeTheme("elegant_purple"))
        theme_menu.addAction("🌿 Современный зеленый").triggered.connect(lambda: self.changeTheme("modern_green"))
        theme_menu.addAction("🍊 Мягкий оранжевый").triggered.connect(lambda: self.changeTheme("soft_orange"))
        theme_menu.addAction("🌫️ Минималистичный серый").triggered.connect(lambda: self.changeTheme("minimal_gray"))
        theme_menu.addAction("✨ Улучшенный минимализм").triggered.connect(lambda: self.changeTheme("minimal_enhanced"))

        theme_btn = QPushButton("🎨 Тема")
        theme_btn.setMenu(theme_menu)
        self.toolbar.addWidget(theme_btn)
        self.toolbar.addSeparator()

        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.load_data)
        self.toolbar.addWidget(refresh_btn)
        self.toolbar.addSeparator()

        help_btn = QPushButton("❓ Справка")
        help_btn.clicked.connect(self.show_help)
        help_btn.setToolTip("Информация о программе и горячих клавишах")
        self.toolbar.addWidget(help_btn)

        # Применяем стили для тулбара
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 5px;
            }

            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
            }

            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.1);
            }

            QToolBar::separator {
                width: 2px;
                margin: 5px;
                background-color: #ecf0f1;
                border-radius: 1px;
            }
        """)

    def show_help(self):
        """Показ окна справки"""
        from .help_window import HelpWindow
        help_dialog = HelpWindow(self)
        help_dialog.exec_()
    def showServiceCatalog(self):
        """Открытие окна справочника услуг"""
        from ui.windows.service_catalog.main_catalog_window import ServiceCatalogWindow
        dialog = ServiceCatalogWindow(self)
        dialog.exec_()
    def showLoyaltySystem(self):
        """Открытие окна системы лояльности"""
        from ui.windows.loyalty_system import LoyaltySystem
        dialog = LoyaltySystem(self)
        dialog.exec_()
    def showStatistics(self):
        """Открытие окна статистики"""
        from ui.windows.statistics_window import StatisticsWindow
        dialog = StatisticsWindow(self)
        dialog.exec_()


    def changeTheme(self, theme_name):
        """Изменение темы приложения"""
        from ui.windows.themes import (LIGHT_THEME, DARK_THEME,
                                             BLUE_GRADIENT_THEME, ELEGANT_PURPLE_THEME,
                                             MODERN_GREEN_THEME, SOFT_ORANGE_THEME,
                                             MINIMAL_GRAY_THEME, MINIMAL_ENHANCED_THEME)

        themes = {
            "light": LIGHT_THEME,
            "dark": DARK_THEME,
            "blue_gradient": BLUE_GRADIENT_THEME,
            "elegant_purple": ELEGANT_PURPLE_THEME,
            "modern_green": MODERN_GREEN_THEME,
            "soft_orange": SOFT_ORANGE_THEME,
            "minimal_gray": MINIMAL_GRAY_THEME,
            "minimal_enhanced": MINIMAL_ENHANCED_THEME
        }

        # Применяем выбранную тему
        selected_theme = themes.get(theme_name, LIGHT_THEME)
        self.setStyleSheet(selected_theme)

        # Сохраняем выбор темы
        settings = QSettings("OrderManager", "Settings")
        settings.setValue("theme", theme_name)

        # Обновляем интерфейс
        self.update()


    def showPathManager(self):
        from ui.windows.path_manager import PathManagerDialog
        dialog = PathManagerDialog(self)
        dialog.exec_()
    def showPathSettings(self):
        """Открытие окна настройки путей"""
        try:
            dialog = PathSettingsDialog(self)
            dialog.exec_()
        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при открытии настроек путей: {str(e)}")
    def showExportDialog(self):
        """Показ диалога экспорта данных"""
        from PyQt5.QtWidgets import QMenu, QAction

        menu = QMenu(self)
        export_excel = QAction("📊 Экспорт в Excel", self)
        export_excel.triggered.connect(self.export_to_excel)

        export_backup = QAction("💾 Создать резервную копию", self)
        export_backup.triggered.connect(self.create_backup)

        menu.addAction(export_excel)
        menu.addAction(export_backup)

        # Показываем меню под кнопкой
        button = self.sender()
        menu.exec_(button.mapToGlobal(button.rect().bottomLeft()))

    def export_to_excel(self):
        """Экспорт данных в Excel"""
        try:
            import pandas as pd
            from datetime import datetime

            # Используем DatabaseManager для получения данных
            with self.db_manager.session_scope() as session:
                orders = session.query(Order).all()

                # Расширенный список полей для экспорта
                data = []
                for order in orders:
                    data.append({
                        'ID': order.id,
                        'ФИО': order.fio,
                        'Группа': order.group,
                        'Услуга': order.service,
                        'Направление': order.direction,
                        'Тема': order.theme,
                        'Количество': order.quantity,
                        'Логин': order.login,
                        'Пароль': order.password,
                        'Сайт': order.website,
                        'Стоимость': order.cost,
                        'Оплачено': order.paid_amount,
                        'Остаток': order.remaining_amount,
                        'Общая сумма': order.total_amount,
                        'Скидка': order.discount,
                        'Дата начала скидки': order.discount_start_date.strftime(
                            '%d.%m.%Y %H:%M:%S') if order.discount_start_date else None,
                        'Дата окончания скидки': order.discount_end_date.strftime(
                            '%d.%m.%Y %H:%M:%S') if order.discount_end_date else None,
                        'ФИО преподавателя': order.teacher_name,
                        'Email преподавателя': order.teacher_email,
                        'Телефон': order.phone,
                        'Дата создания': order.created_date,
                        'Срок сдачи': order.deadline,
                        'Дата оплаты': order.payment_date,
                        'Комментарий': order.comment,
                        'Статус': order.status
                    })

                df = pd.DataFrame(data)

                # Запрос пути сохранения
                file_name = f"Экспорт_заказов_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Сохранить экспорт",
                    file_name,
                    "Excel files (*.xlsx)"
                )

                if file_path:
                    # Создаем writer с настройками
                    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
                    df.to_excel(writer, sheet_name='Заказы', index=False)

                    # Получаем workbook и worksheet
                    workbook = writer.book
                    worksheet = writer.sheets['Заказы']

                    # Форматы для разных типов данных
                    money_format = workbook.add_format({
                        'num_format': '#,##0.00 ₽',
                        'align': 'right'
                    })
                    date_format = workbook.add_format({
                        'num_format': 'dd.mm.yyyy',
                        'align': 'center'
                    })
                    datetime_format = workbook.add_format({
                        'num_format': 'dd.mm.yyyy hh:mm:ss',
                        'align': 'center'
                    })
                    text_format = workbook.add_format({
                        'text_wrap': True,
                        'align': 'left',
                        'valign': 'top'
                    })
                    header_format = workbook.add_format({
                        'bold': True,
                        'text_wrap': True,
                        'valign': 'top',
                        'fg_color': '#D7E4BC',
                        'border': 1
                    })

                    # Применяем форматы к заголовкам
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, header_format)

                    # Применяем форматы к колонкам
                    money_columns = ['K', 'L', 'M', 'N']  # Стоимость, Оплачено, Остаток, Общая сумма
                    date_columns = ['T', 'V']  # Дата создания, Дата оплаты
                    datetime_columns = ['P', 'Q']  # Даты скидок
                    text_columns = ['E', 'F', 'W']  # Направление, Тема, Комментарий

                    # Применяем форматы и устанавливаем ширину колонок
                    for i, col in enumerate(df.columns):
                        col_letter = chr(65 + i) if i < 26 else chr(64 + i // 26) + chr(65 + (i % 26))

                        # Определяем максимальную ширину колонки
                        max_length = max(
                            df[col].astype(str).apply(len).max(),
                            len(col)
                        ) + 2

                        # Ограничиваем максимальную ширину
                        col_width = min(max_length, 50)
                        worksheet.set_column(i, i, col_width)

                        # Применяем форматы в зависимости от типа данных
                        if col_letter in money_columns:
                            worksheet.set_column(i, i, col_width, money_format)
                        elif col_letter in date_columns:
                            worksheet.set_column(i, i, col_width, date_format)
                        elif col_letter in datetime_columns:
                            worksheet.set_column(i, i, col_width, datetime_format)
                        elif col_letter in text_columns:
                            worksheet.set_column(i, i, col_width, text_format)

                    # Добавляем фильтры
                    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)

                    # Закрепляем заголовки
                    worksheet.freeze_panes(1, 0)

                    # Сохраняем файл
                    writer.close()

                    QMessageBox.information(self, "Успех", "Данные успешно экспортированы!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте: {str(e)}")

    def create_backup(self):
        """Создание резервной копии базы данных"""
        try:
            import shutil
            from datetime import datetime

            # Запрашиваем путь сохранения
            file_name = f"Backup_DB_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить резервную копию",
                file_name,
                "Database files (*.db)"
            )

            if file_path:
                # Копируем файл базы данных
                shutil.copy2('orders.db', file_path)
                QMessageBox.information(self, "Успех", "Резервная копия создана!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании резервной копии: {str(e)}")
    def loadTheme(self):
        """Загрузка сохраненной темы"""
        settings = QSettings("OrderManager", "Settings")
        theme_name = settings.value("theme", "light")
        self.changeTheme(theme_name)

    def setup_filters(self):
        """Настройка фильтров и поиска"""
        # Создаем основной контейнер для всех фильтров
        filters_container = QVBoxLayout()

        # Создаем layout для поиска
        search_layout = QHBoxLayout()
        search_label = QLabel("🔍 Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите ФИО или номер заказа")
        self.search_input.textChanged.connect(self.search_orders)
        self.search_input.setMinimumWidth(200)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 5px 10px;
                border: 1px solid #ddd;
                border-radius: 15px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addStretch()  # Добавляем растяжку справа

        buttons_layout = QHBoxLayout()

        # Создаем все кнопки фильтров
        self.all_clients_btn = AllClientsButton()
        self.all_clients_btn.clicked.connect(lambda: self.apply_filter('all'))

        self.new_orders_filter_btn = NewOrdersButton()
        self.new_orders_filter_btn.clicked.connect(lambda: self.apply_filter('new'))

        self.in_progress_btn = InProgressButton()
        self.in_progress_btn.clicked.connect(lambda: self.apply_filter('in_progress'))

        self.paid_orders_btn = PaidOrdersButton()
        self.paid_orders_btn.clicked.connect(lambda: self.apply_filter('paid'))

        self.debtors_btn = DebtorsButton()
        self.debtors_btn.clicked.connect(lambda: self.apply_filter('debtors'))

        self.completed_btn = CompletedOrdersButton()
        self.completed_btn.clicked.connect(lambda: self.apply_filter('completed'))

        self.waiting_payment_btn = WaitingPaymentButton()
        self.waiting_payment_btn.clicked.connect(lambda: self.apply_filter('waiting'))

        self.canceled_btn = CanceledOrdersButton()
        self.canceled_btn.clicked.connect(lambda: self.apply_filter('canceled'))

        self.unique_clients_btn = UniqueClientsButton()
        self.unique_clients_btn.clicked.connect(self.load_unique_clients)

        # Обновляем количество записей
        self.update_filter_counts()

        # Создаем layout и добавляем все кнопки
        filters_layout = QHBoxLayout()
        filters_layout.addWidget(self.unique_clients_btn)
        filters_layout.addWidget(self.all_clients_btn)
        filters_layout.addWidget(self.new_orders_filter_btn)
        filters_layout.addWidget(self.in_progress_btn)
        filters_layout.addWidget(self.paid_orders_btn)
        filters_layout.addWidget(self.debtors_btn)
        filters_layout.addWidget(self.completed_btn)
        filters_layout.addWidget(self.waiting_payment_btn)
        filters_layout.addWidget(self.canceled_btn)

        return filters_layout



    def apply_filter(self, filter_type):
        """Применение фильтра"""
        from core.database import Order


        filters = {
            'all': None,  # Все заказы
            'new': Order.status == 'Новый',
            'in_progress': Order.status == 'В работе',
            'paid': Order.paid_amount > 0,
            'debtors': Order.remaining_amount > 0,
            'completed': Order.status == 'Выполнен',
            'waiting': Order.status == 'В ожидании оплаты',
            'canceled': Order.status == 'Отказ'
        }

        filter_condition = filters[filter_type]
        self.load_data(filter_condition)
    def showNewOrderDialog(self):
        """Открытие окна создания нового заказа"""
        from .new_order_window import NewOrderWindow
        dialog = NewOrderWindow(self)
        if dialog.exec_() == QDialog.Accepted:
            # После успешного создания заказа обновляем таблицу
            self.load_data()
    def load_unique_clients(self):
        """Загрузка списка уникальных клиентов"""
        print("Загружаем уникальных клиентов")  # Отладка
        from sqlalchemy import func
        from core.database import Order

        session = init_database()

        try:
            # Получаем уникальных клиентов и количество их заказов
            clients = session.query(
                Order.fio,
                Order.phone,
                Order.group,
                func.count(Order.id).label('total_orders'),
                func.sum(Order.cost).label('total_cost'),
                func.max(Order.created_date).label('last_order_date')
            ).group_by(Order.fio, Order.phone, Order.group).all()

            # Настраиваем колонки для отображения
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels([
                'ФИО', 'Телефон', 'Группа',
                'Количество заказов', 'Общая сумма', 'Последний заказ'
            ])

            # Заполняем таблицу
            self.table.setRowCount(len(clients))
            for row, client in enumerate(clients):
                self.table.setItem(row, 0, QTableWidgetItem(str(client.fio)))
                self.table.setItem(row, 1, QTableWidgetItem(str(client.phone or 'Не указано')))
                self.table.setItem(row, 2, QTableWidgetItem(str(client.group or 'Не указано')))
                self.table.setItem(row, 3, QTableWidgetItem(str(client.total_orders)))
                self.table.setItem(row, 4, QTableWidgetItem(f"{client.total_cost or 0:,.2f}"))
                self.table.setItem(row, 5, QTableWidgetItem(
                    client.last_order_date.strftime('%Y-%m-%d') if client.last_order_date else 'Не указано'
                ))

            print(f"Загружено {len(clients)} уникальных клиентов")  # Отладка

        except Exception as e:
            print(f"Ошибка при загрузке клиентов: {e}")  # Отладка
            QMessageBox.critical(self, 'Ошибка', f'Ошибка загрузки данных: {str(e)}')
        finally:
            session.close()

    def update_filter_counts(self):
        """Обновление счетчиков для каждого фильтра"""
        from core.database import init_database, Order

        session = init_database()
        try:
            # Получаем количество записей для каждого фильтра
            all_count = session.query(Order).count()
            new_count = session.query(Order).filter(Order.status == 'Новый').count()
            in_progress_count = session.query(Order).filter(Order.status == 'В работе').count()
            paid_count = session.query(Order).filter(Order.paid_amount > 0).count()
            debtors_count = session.query(Order).filter(Order.remaining_amount > 0).count()
            completed_count = session.query(Order).filter(Order.status == 'Выполнен').count()
            waiting_count = session.query(Order).filter(Order.status == 'В ожидании оплаты').count()
            canceled_count = session.query(Order).filter(Order.status == 'Отказ').count()

            # Обновляем текст кнопок
            self.all_clients_btn.setText(f"👥 Все клиенты ({all_count})")
            self.new_orders_filter_btn.setText(f"🆕 Новые ({new_count})")  # Изменили имя кнопки
            self.in_progress_btn.setText(f"🔄 В работе ({in_progress_count})")
            self.paid_orders_btn.setText(f"✅ Оплаченные ({paid_count})")
            self.debtors_btn.setText(f"⚠️ Должники ({debtors_count})")
            self.completed_btn.setText(f"✔️ Выполненные ({completed_count})")
            self.waiting_payment_btn.setText(f"⏳ В ожидании оплаты ({waiting_count})")
            self.canceled_btn.setText(f"❌ Отмененные ({canceled_count})")

        finally:
            session.close()

