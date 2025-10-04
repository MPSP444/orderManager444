import sys

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QTableWidget, QTableWidgetItem,
                             QSplitter, QTextEdit, QPushButton, QLabel,
                             QComboBox, QMessageBox, QApplication, QHeaderView,
                             QCheckBox, QLineEdit,
                             QGroupBox, QFormLayout, QSpinBox, QMenu, QAction,
                             QToolBar)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QColor, QCursor
import mysql.connector
from datetime import datetime
# Импортируем конфигурацию
from reviews_manager.config import DB_TABLES
from PyQt5.QtCore import QThread, pyqtSignal

# В начало файла reviews_manager_app.py добавить:
try:
    from reviews_manager.config import DB_CONFIG, DB_TABLES, ADMIN_USERNAME, ADMIN_PASSWORD
except ImportError:
    # Определяем конфигурацию вручную, если импорт не удался
    DB_CONFIG = {
        'host': 'mpsp.online',
        'user': 'u3054108_Mukam1',
        'password': 'vYL-f2w-cNk-fuJ',
        'database': 'u3054108_reviews_db',
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }

    DB_TABLES = {
        'reviews': {
            'name': 'reviews',
        },
        'contacts': {
            'name': 'contacts',
        }
    }

    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'mpsp2023admin'

class DBConnectionThread(QThread):
    connection_success = pyqtSignal(object)  # Сигнал с объектом соединения
    connection_error = pyqtSignal(str)  # Сигнал с текстом ошибки

    def __init__(self, config):
        super().__init__()
        # Убедимся, что конфигурация содержит правильные параметры для MySQL 5.7
        self.config = config.copy()
        if 'collation' not in self.config:
            self.config['collation'] = 'utf8mb4_unicode_ci'

    def run(self):
        try:
            import mysql.connector

            # Пробуем подключиться с указанными параметрами
            try:
                connection = mysql.connector.connect(**self.config)
                self.connection_success.emit(connection)
            except mysql.connector.errors.DatabaseError as e:
                # Если ошибка из-за сопоставления, попробуем с другими параметрами
                if "Unknown collation" in str(e):
                    print("Пробуем подключиться с измененными параметрами из-за ошибки сопоставления")
                    config_mod = self.config.copy()
                    config_mod['charset'] = 'utf8'  # Используем простой utf8
                    if 'collation' in config_mod:
                        del config_mod['collation']

                    connection = mysql.connector.connect(**config_mod)
                    self.connection_success.emit(connection)
                else:
                    raise e

        except Exception as e:
            self.connection_error.emit(str(e))

class ReviewsManagerApp(QMainWindow):
    """Основное окно для управления отзывами и контактами"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Защита от ошибок при инициализации
        try:
            # Настройка окна
            self.setWindowTitle("Управление отзывами и контактами")
            self.setMinimumSize(1200, 800)

            # Инициализация UI (вызываем перед подключением к БД)
            self.setup_ui()

            # Инициализация БД (теперь уже после UI)
            self.init_database()

            # Загрузка данных при старте (только если БД успешно инициализирована)
            if hasattr(self, 'db_connection') and hasattr(self, 'cursor'):
                self.load_reviews()
                self.load_contacts()
            else:
                print("Предупреждение: БД не инициализирована, данные не загружены")

            # Установка таймера обновления
            self.update_timer = QTimer(self)
            self.update_timer.timeout.connect(self.check_for_updates)
            self.update_timer.start(60000)  # Проверка каждую минуту

        except Exception as e:
            print(f"Ошибка при инициализации ReviewsManagerApp: {e}")
            import traceback
            traceback.print_exc()
            # Показываем сообщение об ошибке в интерфейсе
            QMessageBox.critical(
                self,
                "Ошибка инициализации",
                f"Не удалось инициализировать менеджер отзывов: {str(e)}"
            )

    def init_database(self):
        """Инициализация подключения к базе данных"""
        try:
            # Исправляем импорт и параметр хоста
            try:
                from reviews_manager.config import DB_CONFIG
                db_config = DB_CONFIG.copy()
            except ImportError:
                # Если импорт не удался, создаем конфигурацию вручную
                db_config = {
                    'host': 'mpsp.online',
                    'user': 'u3054108_Mukam1',
                    'password': 'vYL-f2w-cNk-fuJ',
                    'database': 'u3054108_reviews_db',
                    'charset': 'utf8mb4',
                    'collation': 'utf8mb4_unicode_ci'
                }

            print(f"Инициализация БД с параметрами: {db_config}")

            # Создаем и запускаем поток подключения
            self.connection_thread = DBConnectionThread(db_config)
            self.connection_thread.connection_success.connect(self.on_connection_success)
            self.connection_thread.connection_error.connect(self.on_connection_error)
            self.connection_thread.start()

            # Показываем сообщение о подключении
            self.statusBar().showMessage("Подключение к базе данных...")

        except Exception as e:
            print(f"Ошибка при инициализации подключения к БД: {e}")
            import traceback
            traceback.print_exc()

            # Устанавливаем флаги, чтобы приложение работало в ограниченном режиме
            self.db_connection = None
            self.cursor = None
            self.statusBar().showMessage("Ошибка подключения к БД. Работа в ограниченном режиме.")


    def on_connection_success(self, connection):
        """Обработка успешного подключения к БД"""
        self.db_connection = connection
        self.cursor = self.db_connection.cursor(dictionary=True)
        self.statusBar().showMessage("Подключение к базе данных установлено")
        print("Подключение к базе данных успешно установлено")

        # Загружаем данные
        self.load_reviews()
        self.load_contacts()

    def on_connection_error(self, error_message):
        """Обработка ошибки подключения к БД"""
        from PyQt5.QtWidgets import QMessageBox
        print(f"Ошибка подключения к базе данных: {error_message}")

        QMessageBox.critical(
            self,
            "Ошибка подключения",
            f"Не удалось подключиться к базе данных: {error_message}\n\n"
            "Модуль управления отзывами будет работать в ограниченном режиме."
        )

        # Устанавливаем флаг, что соединение недоступно
        self.db_connection = None
        self.cursor = None
    def setup_ui(self):
        """Настройка интерфейса"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout(central_widget)

        # Создаем вкладки
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)

        # Создаем вкладку отзывов
        self.reviews_tab = self.create_reviews_tab()
        self.tabs.addTab(self.reviews_tab, "🌟 Отзывы")

        # Создаем вкладку контактов
        self.contacts_tab = self.create_contacts_tab()
        self.tabs.addTab(self.contacts_tab, "📞 Контакты")

        # Создаем вкладку SQL-запросов
        self.sql_tab = self.create_sql_tab()
        self.tabs.addTab(self.sql_tab, "🗃️ SQL-запросы")

        # Создаем вкладку настроек
        self.settings_tab = self.create_settings_tab()
        self.tabs.addTab(self.settings_tab, "⚙️ Настройки")

        # Добавляем вкладки к основному layout
        main_layout.addWidget(self.tabs)

        # Создаем статусную строку
        self.statusBar().showMessage("Готово к работе")

        # Создаем панель инструментов
        self.create_toolbar()

    def create_reviews_tab(self):
        """Создание вкладки для управления отзывами"""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Создаем сплиттер для разделения списка и деталей
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель - список отзывов
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Инструменты фильтрации
        filter_group = QGroupBox("Фильтры")
        filter_layout = QHBoxLayout()

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Все статусы", "Ожидает модерации", "Одобрено", "Отклонено"])
        self.status_filter.currentIndexChanged.connect(self.apply_filters)

        self.rating_filter = QComboBox()
        self.rating_filter.addItems(["Все рейтинги", "5 звезд", "4 звезды", "3 звезды", "2 звезды", "1 звезда"])
        self.rating_filter.currentIndexChanged.connect(self.apply_filters)

        filter_layout.addWidget(QLabel("Статус:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Рейтинг:"))
        filter_layout.addWidget(self.rating_filter)
        filter_group.setLayout(filter_layout)

        left_layout.addWidget(filter_group)

        # Поле поиска
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск отзывов...")
        self.search_input.textChanged.connect(self.search_reviews)
        search_button = QPushButton("🔍")
        search_button.clicked.connect(lambda: self.search_reviews(self.search_input.text()))

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        left_layout.addLayout(search_layout)

        # Таблица отзывов
        self.reviews_table = QTableWidget()
        self.reviews_table.setColumnCount(5)
        self.reviews_table.setHorizontalHeaderLabels(["ID", "Имя", "Услуга", "Рейтинг", "Статус"])
        self.reviews_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.reviews_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.reviews_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reviews_table.clicked.connect(self.show_review_details)

        left_layout.addWidget(self.reviews_table)

        # Кнопки пакетных операций
        batch_group = QGroupBox("Пакетные операции")
        batch_layout = QHBoxLayout()

        approve_batch_btn = QPushButton("✅ Одобрить выбранные")
        approve_batch_btn.clicked.connect(self.approve_selected_reviews)

        reject_batch_btn = QPushButton("❌ Отклонить выбранные")
        reject_batch_btn.clicked.connect(self.reject_selected_reviews)

        delete_batch_btn = QPushButton("🗑️ Удалить выбранные")
        delete_batch_btn.clicked.connect(self.delete_selected_reviews)

        batch_layout.addWidget(approve_batch_btn)
        batch_layout.addWidget(reject_batch_btn)
        batch_layout.addWidget(delete_batch_btn)
        batch_group.setLayout(batch_layout)

        left_layout.addWidget(batch_group)

        # Правая панель - детали отзыва
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Заголовок детали отзыва
        self.review_detail_title = QLabel("Детали отзыва")
        self.review_detail_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        right_layout.addWidget(self.review_detail_title)

        # Информация о клиенте
        client_group = QGroupBox("Информация о клиенте")
        client_layout = QFormLayout()

        self.detail_client_name = QLabel("")
        self.detail_client_order = QLabel("")
        self.detail_service = QLabel("")
        self.detail_date = QLabel("")

        client_layout.addRow("Имя:", self.detail_client_name)
        client_layout.addRow("Номер заказа:", self.detail_client_order)
        client_layout.addRow("Услуга:", self.detail_service)
        client_layout.addRow("Дата:", self.detail_date)

        client_group.setLayout(client_layout)
        right_layout.addWidget(client_group)

        # Текст отзыва
        review_group = QGroupBox("Текст отзыва")
        review_layout = QVBoxLayout()

        self.detail_rating = QLabel("★★★★★")
        self.detail_rating.setStyleSheet("font-size: 24pt; color: gold;")

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)

        review_layout.addWidget(self.detail_rating)
        review_layout.addWidget(self.detail_text)
        review_group.setLayout(review_layout)

        right_layout.addWidget(review_group)

        # Управление отзывом
        management_group = QGroupBox("Управление отзывом")
        management_layout = QVBoxLayout()

        # Статус
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Статус:"))

        self.detail_status = QComboBox()
        self.detail_status.addItems(["Ожидает модерации", "Одобрено", "Отклонено"])
        status_layout.addWidget(self.detail_status)

        update_status_btn = QPushButton("Обновить статус")
        update_status_btn.clicked.connect(self.update_review_status)
        status_layout.addWidget(update_status_btn)

        management_layout.addLayout(status_layout)

        # Ответ на отзыв
        response_layout = QVBoxLayout()
        response_layout.addWidget(QLabel("Ответ на отзыв:"))

        self.detail_response = QTextEdit()
        response_layout.addWidget(self.detail_response)

        # Шаблоны ответов
        templates_layout = QHBoxLayout()
        templates_layout.addWidget(QLabel("Шаблон:"))

        self.response_template = QComboBox()
        self.response_template.addItems([
            "Выберите шаблон",
            "Благодарность за положительный отзыв",
            "Ответ на критику",
            "Извинения за проблему",
            "Стандартный ответ"
        ])
        self.response_template.currentIndexChanged.connect(self.apply_response_template)

        templates_layout.addWidget(self.response_template)
        response_layout.addLayout(templates_layout)

        # Кнопки действий с ответом
        response_buttons = QHBoxLayout()

        save_response_btn = QPushButton("💾 Сохранить ответ")
        save_response_btn.clicked.connect(self.save_review_response)

        send_response_btn = QPushButton("📤 Отправить ответ")
        send_response_btn.clicked.connect(self.send_review_response)

        response_buttons.addWidget(save_response_btn)
        response_buttons.addWidget(send_response_btn)
        response_layout.addLayout(response_buttons)

        management_layout.addLayout(response_layout)

        # Кнопки реакций и удаления
        actions_layout = QHBoxLayout()

        like_btn = QPushButton("👍 Like")
        like_btn.clicked.connect(lambda: self.update_review_reaction(1, 0))

        dislike_btn = QPushButton("👎 Dislike")
        dislike_btn.clicked.connect(lambda: self.update_review_reaction(0, 1))

        delete_btn = QPushButton("🗑️ Удалить отзыв")
        delete_btn.clicked.connect(self.delete_current_review)

        actions_layout.addWidget(like_btn)
        actions_layout.addWidget(dislike_btn)
        actions_layout.addWidget(delete_btn)
        management_layout.addLayout(actions_layout)

        management_group.setLayout(management_layout)
        right_layout.addWidget(management_group)

        # Добавляем панели к сплиттеру
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Устанавливаем начальные размеры сплиттера (40% / 60%)
        splitter.setSizes([400, 600])

        # Добавляем сплиттер в layout вкладки
        layout.addWidget(splitter)

        return tab

    def create_contacts_tab(self):
        """Создание вкладки для управления контактами"""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Создаем сплиттер для разделения списка и деталей
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель - список контактов
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Фильтры для контактов
        filter_group = QGroupBox("Фильтры")
        filter_layout = QHBoxLayout()

        self.contact_status_filter = QComboBox()
        self.contact_status_filter.addItems(["Все статусы", "Новые", "В обработке", "Завершенные", "Отклоненные"])
        self.contact_status_filter.currentIndexChanged.connect(self.apply_contact_filters)

        filter_layout.addWidget(QLabel("Статус:"))
        filter_layout.addWidget(self.contact_status_filter)
        filter_group.setLayout(filter_layout)

        left_layout.addWidget(filter_group)

        # Поле поиска
        search_layout = QHBoxLayout()
        self.contact_search_input = QLineEdit()
        self.contact_search_input.setPlaceholderText("Поиск контактов...")
        self.contact_search_input.textChanged.connect(self.search_contacts)
        search_button = QPushButton("🔍")
        search_button.clicked.connect(lambda: self.search_contacts(self.contact_search_input.text()))

        search_layout.addWidget(self.contact_search_input)
        search_layout.addWidget(search_button)
        left_layout.addLayout(search_layout)

        # Таблица контактов
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(5)
        self.contacts_table.setHorizontalHeaderLabels(["ID", "Имя", "Email", "Дата", "Статус"])
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.contacts_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.contacts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contacts_table.clicked.connect(self.show_contact_details)

        left_layout.addWidget(self.contacts_table)

        # Кнопки пакетных операций
        batch_group = QGroupBox("Пакетные операции")
        batch_layout = QHBoxLayout()

        process_batch_btn = QPushButton("✅ Обработать выбранные")
        process_batch_btn.clicked.connect(self.process_selected_contacts)

        reject_batch_btn = QPushButton("❌ Отклонить выбранные")
        reject_batch_btn.clicked.connect(self.reject_selected_contacts)

        delete_batch_btn = QPushButton("🗑️ Удалить выбранные")
        delete_batch_btn.clicked.connect(self.delete_selected_contacts)

        batch_layout.addWidget(process_batch_btn)
        batch_layout.addWidget(reject_batch_btn)
        batch_layout.addWidget(delete_batch_btn)
        batch_group.setLayout(batch_layout)

        left_layout.addWidget(batch_group)

        # Правая панель - детали контакта
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Заголовок детали контакта
        self.contact_detail_title = QLabel("Детали контакта")
        self.contact_detail_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        right_layout.addWidget(self.contact_detail_title)

        # Информация о контакте
        contact_group = QGroupBox("Информация")
        contact_layout = QFormLayout()

        self.detail_contact_name = QLabel("")
        self.detail_contact_email = QLabel("")
        self.detail_contact_phone = QLabel("")
        self.detail_contact_date = QLabel("")

        contact_layout.addRow("Имя:", self.detail_contact_name)
        contact_layout.addRow("Email:", self.detail_contact_email)
        contact_layout.addRow("Телефон:", self.detail_contact_phone)
        contact_layout.addRow("Дата:", self.detail_contact_date)

        contact_group.setLayout(contact_layout)
        right_layout.addWidget(contact_group)

        # Сообщение контакта
        message_group = QGroupBox("Сообщение")
        message_layout = QVBoxLayout()

        self.detail_contact_message = QTextEdit()
        self.detail_contact_message.setReadOnly(True)

        message_layout.addWidget(self.detail_contact_message)
        message_group.setLayout(message_layout)

        right_layout.addWidget(message_group)

        # Управление контактом
        management_group = QGroupBox("Управление")
        management_layout = QVBoxLayout()

        # Статус контакта
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Статус:"))

        self.detail_contact_status = QComboBox()
        self.detail_contact_status.addItems(["Новый", "В обработке", "Завершен", "Отклонен"])
        status_layout.addWidget(self.detail_contact_status)

        update_status_btn = QPushButton("Обновить статус")
        update_status_btn.clicked.connect(self.update_contact_status)
        status_layout.addWidget(update_status_btn)

        management_layout.addLayout(status_layout)

        # Кнопки действий
        actions_layout = QHBoxLayout()

        email_btn = QPushButton("📧 Отправить Email")
        email_btn.clicked.connect(self.send_email_to_contact)

        delete_btn = QPushButton("🗑️ Удалить контакт")
        delete_btn.clicked.connect(self.delete_current_contact)

        actions_layout.addWidget(email_btn)
        actions_layout.addWidget(delete_btn)
        management_layout.addLayout(actions_layout)

        management_group.setLayout(management_layout)
        right_layout.addWidget(management_group)

        # Добавляем панели к сплиттеру
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # Устанавливаем начальные размеры сплиттера (40% / 60%)
        splitter.setSizes([400, 600])

        # Добавляем сплиттер в layout вкладки
        layout.addWidget(splitter)

        return tab

    def create_sql_tab(self):
        """Создание вкладки для выполнения SQL-запросов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Верхняя панель - ввод SQL запроса
        query_group = QGroupBox("SQL-запрос")
        query_layout = QVBoxLayout()

        self.sql_query_edit = QTextEdit()
        self.sql_query_edit.setPlaceholderText("Введите SQL запрос...")
        query_layout.addWidget(self.sql_query_edit)

        # Кнопки выполнения и шаблонов
        buttons_layout = QHBoxLayout()

        execute_btn = QPushButton("▶️ Выполнить")
        execute_btn.clicked.connect(self.execute_sql_query)

        clear_btn = QPushButton("🧹 Очистить")
        clear_btn.clicked.connect(self.clear_sql_query)

        templates_label = QLabel("Шаблоны:")

        self.sql_templates = QComboBox()
        self.sql_templates.addItems([
            "Выберите шаблон",
            "SELECT * FROM reviews LIMIT 100",
            "SELECT * FROM contacts LIMIT 100",
            "SELECT COUNT(*) FROM reviews GROUP BY status",
            "SELECT COUNT(*) FROM contacts GROUP BY status",
            "CREATE TABLE (пример)"
        ])
        self.sql_templates.currentIndexChanged.connect(self.apply_sql_template)

        buttons_layout.addWidget(execute_btn)
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(templates_label)
        buttons_layout.addWidget(self.sql_templates)

        query_layout.addLayout(buttons_layout)
        query_group.setLayout(query_layout)

        layout.addWidget(query_group)

        # Нижняя панель - результаты запроса
        results_group = QGroupBox("Результаты")
        results_layout = QVBoxLayout()

        self.sql_results_table = QTableWidget()
        self.sql_results_table.setSelectionBehavior(QTableWidget.SelectRows)

        self.sql_error_label = QLabel("")
        self.sql_error_label.setStyleSheet("color: red;")

        results_layout.addWidget(self.sql_results_table)
        results_layout.addWidget(self.sql_error_label)

        results_group.setLayout(results_layout)

        layout.addWidget(results_group)
        layout.setStretch(0, 1)  # 1/3 для ввода запроса
        layout.setStretch(1, 2)  # 2/3 для результатов

        return tab

    def create_settings_tab(self):
        """Создание вкладки для настроек приложения"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Настройки базы данных
        db_group = QGroupBox("Настройки базы данных")
        db_layout = QFormLayout()

        self.db_host = QLineEdit(DB_CONFIG['host'])
        self.db_user = QLineEdit(DB_CONFIG['user'])
        self.db_password = QLineEdit(DB_CONFIG['password'])
        self.db_password.setEchoMode(QLineEdit.Password)
        self.db_name = QLineEdit(DB_CONFIG['database'])

        db_layout.addRow("Хост:", self.db_host)
        db_layout.addRow("Пользователь:", self.db_user)
        db_layout.addRow("Пароль:", self.db_password)
        db_layout.addRow("База данных:", self.db_name)

        # Тест соединения
        test_btn = QPushButton("🔄 Проверить соединение")
        test_btn.clicked.connect(self.test_database_connection)
        db_layout.addRow("", test_btn)

        db_group.setLayout(db_layout)
        layout.addWidget(db_group)

        # Настройки интерфейса
        ui_group = QGroupBox("Настройки интерфейса")
        ui_layout = QFormLayout()

        self.refresh_interval = QSpinBox()
        self.refresh_interval.setMinimum(10)
        self.refresh_interval.setMaximum(3600)
        self.refresh_interval.setValue(60)
        self.refresh_interval.setSuffix(" сек")

        ui_layout.addRow("Интервал обновления:", self.refresh_interval)

        # Настройки уведомлений
        self.show_notifications = QCheckBox("Включить уведомления о новых отзывах и контактах")
        self.show_notifications.setChecked(True)
        ui_layout.addRow("", self.show_notifications)

        # Звуковые уведомления
        self.sound_notifications = QCheckBox("Включить звуковые уведомления")
        self.sound_notifications.setChecked(True)
        ui_layout.addRow("", self.sound_notifications)

        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)

        # Настройки ответов
        responses_group = QGroupBox("Настройки шаблонов ответов")
        responses_layout = QVBoxLayout()

        # Таблица шаблонов
        self.templates_table = QTableWidget()
        self.templates_table.setColumnCount(2)
        self.templates_table.setHorizontalHeaderLabels(["Название", "Текст"])
        self.templates_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

        # Добавляем несколько стандартных шаблонов
        self.templates_table.setRowCount(4)

        templates = [
            ("Благодарность за положительный отзыв",
             "Спасибо за ваш положительный отзыв! Мы очень рады, что вы остались довольны нашими услугами. Будем рады видеть вас снова!"),
            ("Ответ на критику",
             "Благодарим вас за отзыв и обратную связь. Мы ценим ваше мнение и работаем над улучшением наших услуг. Приносим извинения за доставленные неудобства."),
            ("Извинения за проблему",
             "Приносим искренние извинения за возникшие проблемы. Мы уже разбираемся с ситуацией и сделаем всё возможное, чтобы решить вопрос в кратчайшие сроки."),
            ("Стандартный ответ",
             "Благодарим вас за обращение. Ваше мнение очень важно для нас. Мы обязательно учтем ваши пожелания в нашей дальнейшей работе.")
        ]

        for i, (name, text) in enumerate(templates):
            self.templates_table.setItem(i, 0, QTableWidgetItem(name))
            self.templates_table.setItem(i, 1, QTableWidgetItem(text))

        responses_layout.addWidget(self.templates_table)

        # Кнопки для управления шаблонами
        templates_buttons = QHBoxLayout()

        add_template_btn = QPushButton("➕ Добавить шаблон")
        add_template_btn.clicked.connect(self.add_response_template_row)

        delete_template_btn = QPushButton("➖ Удалить шаблон")
        delete_template_btn.clicked.connect(self.delete_response_template_row)

        save_templates_btn = QPushButton("💾 Сохранить шаблоны")
        save_templates_btn.clicked.connect(self.save_response_templates)

        templates_buttons.addWidget(add_template_btn)
        templates_buttons.addWidget(delete_template_btn)
        templates_buttons.addWidget(save_templates_btn)

        responses_layout.addLayout(templates_buttons)
        responses_group.setLayout(responses_layout)

        layout.addWidget(responses_group)

        # Кнопки сохранения настроек
        buttons_layout = QHBoxLayout()

        save_settings_btn = QPushButton("💾 Сохранить настройки")
        save_settings_btn.clicked.connect(self.save_settings)

        reset_settings_btn = QPushButton("🔄 Сбросить настройки")
        reset_settings_btn.clicked.connect(self.reset_settings)

        buttons_layout.addWidget(save_settings_btn)
        buttons_layout.addWidget(reset_settings_btn)

        layout.addLayout(buttons_layout)

        return tab

    def create_toolbar(self):
        """Создание панели инструментов"""
        toolbar = QToolBar("Панель инструментов")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # Кнопка обновления
        refresh_action = QAction("🔄 Обновить", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # Кнопка экспорта
        export_action = QAction("📤 Экспорт", self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)

        # Кнопка импорта
        import_action = QAction("📥 Импорт", self)
        import_action.triggered.connect(self.import_data)
        toolbar.addAction(import_action)

        toolbar.addSeparator()

        # Кнопка справки
        help_action = QAction("❓ Справка", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)

    # === Методы для работы с отзывами ===

    def load_reviews(self):
        """Загрузка отзывов из базы данных"""
        try:
            if not hasattr(self, 'cursor') or not self.db_connection.is_connected():
                self.init_database()

            # Получаем таблицу отзывов
            reviews_table = DB_TABLES['reviews']['name']

            # Формируем SQL-запрос
            query = f"SELECT * FROM {reviews_table} ORDER BY date DESC"

            # Выполняем запрос
            self.cursor.execute(query)
            reviews = self.cursor.fetchall()

            # Заполняем таблицу
            self.reviews_table.setRowCount(0)  # Очищаем таблицу

            for row, review in enumerate(reviews):
                self.reviews_table.insertRow(row)

                # ID
                id_item = QTableWidgetItem(str(review['id']))
                id_item.setData(Qt.UserRole, review['id'])  # Сохраняем ID для использования в дальнейшем
                self.reviews_table.setItem(row, 0, id_item)

                # Имя
                name_item = QTableWidgetItem(review['name'])
                self.reviews_table.setItem(row, 1, name_item)

                # Услуга
                service_item = QTableWidgetItem(review['service'])
                self.reviews_table.setItem(row, 2, service_item)

                # Рейтинг (звезды)
                rating = review['rating']
                rating_item = QTableWidgetItem("★" * rating + "☆" * (5 - rating))
                rating_item.setData(Qt.UserRole, rating)  # Сохраняем числовое значение
                self.reviews_table.setItem(row, 3, rating_item)

                # Статус
                status_item = QTableWidgetItem(review['status'])

                # Цветовое выделение в зависимости от статуса
                if review['status'] == 'approved' or review['status'] == 'Одобрено':
                    status_item.setBackground(QColor(200, 255, 200))  # Светло-зеленый
                elif review['status'] == 'pending' or review['status'] == 'Ожидает модерации':
                    status_item.setBackground(QColor(255, 255, 200))  # Светло-желтый
                elif review['status'] == 'rejected' or review['status'] == 'Отклонено':
                    status_item.setBackground(QColor(255, 200, 200))  # Светло-красный

                self.reviews_table.setItem(row, 4, status_item)

            # Обновляем интерфейс
            self.reviews_table.resizeColumnsToContents()
            self.statusBar().showMessage(f"Загружено {len(reviews)} отзывов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки данных",
                f"Не удалось загрузить отзывы: {e}"
            )

    def show_review_details(self):
        """Отображение деталей выбранного отзыва"""
        # Получаем выбранную строку
        row = self.reviews_table.currentRow()
        if row < 0:
            return

        # Получаем ID отзыва
        review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

        try:
            # Получаем данные отзыва из БД
            reviews_table = DB_TABLES['reviews']['name']
            query = f"SELECT * FROM {reviews_table} WHERE id = %s"
            self.cursor.execute(query, (review_id,))
            review = self.cursor.fetchone()

            if not review:
                return

            # Заполняем поля деталей
            self.review_detail_title.setText(f"Отзыв #{review['id']}")
            self.detail_client_name.setText(review['name'])
            self.detail_client_order.setText(review['order_id'] if review['order_id'] else 'Не указано')
            self.detail_service.setText(review['service'])

            # Форматируем дату
            if isinstance(review['date'], datetime):
                formatted_date = review['date'].strftime("%d.%m.%Y %H:%M:%S")
            else:
                formatted_date = str(review['date'])
            self.detail_date.setText(formatted_date)

            # Рейтинг
            rating = review['rating']
            self.detail_rating.setText("★" * rating + "☆" * (5 - rating))

            # Текст отзыва
            self.detail_text.setText(review['text'] if review['text'] else '')

            # Статус
            status_index = 0
            status = review['status']
            if status == 'approved' or status == 'Одобрено':
                status_index = 1
            elif status == 'rejected' or status == 'Отклонено':
                status_index = 2
            self.detail_status.setCurrentIndex(status_index)

            # Ответ на отзыв
            self.detail_response.setText(review['response'] if review['response'] else '')

            # Сбрасываем шаблон ответа
            self.response_template.setCurrentIndex(0)

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить детали отзыва: {e}"
            )

    def apply_filters(self):
        """Применение фильтров к списку отзывов"""
        try:
            # Получаем выбранные фильтры
            status_filter = self.status_filter.currentText()
            rating_filter = self.rating_filter.currentText()

            # Формируем условия SQL-запроса
            conditions = []
            params = []

            if status_filter != "Все статусы":
                # Преобразуем статус для SQL-запроса
                status_map = {
                    "Ожидает модерации": "pending",
                    "Одобрено": "approved",
                    "Отклонено": "rejected"
                }
                db_status = status_map.get(status_filter, status_filter)
                conditions.append("status = %s")
                params.append(db_status)

            if rating_filter != "Все рейтинги":
                # Извлекаем числовое значение из строки типа "5 звезд"
                rating = int(rating_filter.split()[0])
                conditions.append("rating = %s")
                params.append(rating)

            # Формируем SQL-запрос
            reviews_table = DB_TABLES['reviews']['name']
            query = f"SELECT * FROM {reviews_table}"

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY date DESC"

            # Выполняем запрос
            self.cursor.execute(query, params)
            reviews = self.cursor.fetchall()

            # Обновляем таблицу
            self.reviews_table.setRowCount(0)

            for row, review in enumerate(reviews):
                self.reviews_table.insertRow(row)

                # ID
                id_item = QTableWidgetItem(str(review['id']))
                id_item.setData(Qt.UserRole, review['id'])
                self.reviews_table.setItem(row, 0, id_item)

                # Имя
                name_item = QTableWidgetItem(review['name'])
                self.reviews_table.setItem(row, 1, name_item)

                # Услуга
                service_item = QTableWidgetItem(review['service'])
                self.reviews_table.setItem(row, 2, service_item)

                # Рейтинг
                rating = review['rating']
                rating_item = QTableWidgetItem("★" * rating + "☆" * (5 - rating))
                rating_item.setData(Qt.UserRole, rating)
                self.reviews_table.setItem(row, 3, rating_item)

                # Статус
                status_item = QTableWidgetItem(review['status'])

                # Цветовое выделение
                if review['status'] == 'approved' or review['status'] == 'Одобрено':
                    status_item.setBackground(QColor(200, 255, 200))
                elif review['status'] == 'pending' or review['status'] == 'Ожидает модерации':
                    status_item.setBackground(QColor(255, 255, 200))
                elif review['status'] == 'rejected' or review['status'] == 'Отклонено':
                    status_item.setBackground(QColor(255, 200, 200))

                self.reviews_table.setItem(row, 4, status_item)

            # Обновляем статусную строку
            self.statusBar().showMessage(f"Найдено {len(reviews)} отзывов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка фильтрации",
                f"Не удалось применить фильтры: {e}"
            )

    def search_reviews(self, text):
        """Поиск отзывов по тексту"""
        try:
            if not text.strip():
                # Если поле поиска пустое, просто обновляем данные
                self.load_reviews()
                return

            # Формируем SQL-запрос с поиском
            reviews_table = DB_TABLES['reviews']['name']
            search_pattern = f"%{text}%"

            query = f"""
                SELECT * FROM {reviews_table} 
                WHERE name LIKE %s 
                OR service LIKE %s 
                OR text LIKE %s 
                OR order_id LIKE %s
                ORDER BY date DESC
            """

            # Выполняем запрос
            self.cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            reviews = self.cursor.fetchall()

            # Обновляем таблицу
            self.reviews_table.setRowCount(0)

            for row, review in enumerate(reviews):
                self.reviews_table.insertRow(row)

                # ID
                id_item = QTableWidgetItem(str(review['id']))
                id_item.setData(Qt.UserRole, review['id'])
                self.reviews_table.setItem(row, 0, id_item)

                # Имя
                name_item = QTableWidgetItem(review['name'])
                self.reviews_table.setItem(row, 1, name_item)

                # Услуга
                service_item = QTableWidgetItem(review['service'])
                self.reviews_table.setItem(row, 2, service_item)

                # Рейтинг
                rating = review['rating']
                rating_item = QTableWidgetItem("★" * rating + "☆" * (5 - rating))
                rating_item.setData(Qt.UserRole, rating)
                self.reviews_table.setItem(row, 3, rating_item)

                # Статус
                status_item = QTableWidgetItem(review['status'])

                # Цветовое выделение
                if review['status'] == 'approved' or review['status'] == 'Одобрено':
                    status_item.setBackground(QColor(200, 255, 200))
                elif review['status'] == 'pending' or review['status'] == 'Ожидает модерации':
                    status_item.setBackground(QColor(255, 255, 200))
                elif review['status'] == 'rejected' or review['status'] == 'Отклонено':
                    status_item.setBackground(QColor(255, 200, 200))

                self.reviews_table.setItem(row, 4, status_item)

            # Обновляем статусную строку
            self.statusBar().showMessage(f"Найдено {len(reviews)} отзывов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка поиска",
                f"Не удалось выполнить поиск: {e}"
            )

    def apply_response_template(self):
        """Применение шаблона ответа"""
        template_index = self.response_template.currentIndex()
        if template_index == 0:
            return  # Не выбран шаблон

        # Получаем текст шаблона
        template_text = ""
        for row in range(self.templates_table.rowCount()):
            if self.templates_table.item(row, 0).text() == self.response_template.currentText():
                template_text = self.templates_table.item(row, 1).text()
                break

        # Если шаблон не найден в таблице, используем стандартные шаблоны
        if not template_text:
            templates = [
                "Спасибо за ваш положительный отзыв! Мы очень рады, что вы остались довольны нашими услугами. Будем рады видеть вас снова!",
                "Благодарим вас за отзыв и обратную связь. Мы ценим ваше мнение и работаем над улучшением наших услуг. Приносим извинения за доставленные неудобства.",
                "Приносим искренние извинения за возникшие проблемы. Мы уже разбираемся с ситуацией и сделаем всё возможное, чтобы решить вопрос в кратчайшие сроки.",
                "Благодарим вас за обращение. Ваше мнение очень важно для нас. Мы обязательно учтем ваши пожелания в нашей дальнейшей работе."
            ]

            if template_index <= len(templates):
                template_text = templates[template_index - 1]

        # Персонализируем шаблон
        client_name = self.detail_client_name.text().strip()
        if client_name:
            # Добавляем обращение по имени
            if "!" in template_text and not template_text.startswith(f"{client_name},"):
                template_text = f"{client_name}, " + template_text[0].lower() + template_text[1:]
            else:
                template_text = f"{client_name}, " + template_text

        # Устанавливаем текст в поле ответа
        self.detail_response.setText(template_text)

    def update_review_status(self):
        """Обновление статуса отзыва"""
        # Получаем выбранную строку
        row = self.reviews_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите отзыв для обновления статуса")
            return

        # Получаем ID отзыва
        review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

        # Получаем новый статус
        status_index = self.detail_status.currentIndex()
        status_map = ["pending", "approved", "rejected"]
        new_status = status_map[status_index]

        try:
            # Обновляем статус в БД
            reviews_table = DB_TABLES['reviews']['name']
            query = f"UPDATE {reviews_table} SET status = %s WHERE id = %s"
            self.cursor.execute(query, (new_status, review_id))
            self.db_connection.commit()

            # Обновляем отображение в таблице
            status_item = QTableWidgetItem(new_status)

            # Цветовое выделение
            if new_status == 'approved':
                status_item.setBackground(QColor(200, 255, 200))
            elif new_status == 'pending':
                status_item.setBackground(QColor(255, 255, 200))
            elif new_status == 'rejected':
                status_item.setBackground(QColor(255, 200, 200))

            self.reviews_table.setItem(row, 4, status_item)

            # Уведомление об успехе
            self.statusBar().showMessage(f"Статус отзыва #{review_id} изменен на {new_status}")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                f"Не удалось обновить статус отзыва: {e}"
            )

    def save_review_response(self):
        """Сохранение ответа на отзыв"""
        # Получаем выбранную строку
        row = self.reviews_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите отзыв для сохранения ответа")
            return

        # Получаем ID отзыва
        review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

        # Получаем текст ответа
        response_text = self.detail_response.toPlainText().strip()

        try:
            # Обновляем ответ в БД
            reviews_table = DB_TABLES['reviews']['name']
            query = f"UPDATE {reviews_table} SET response = %s WHERE id = %s"
            self.cursor.execute(query, (response_text, review_id))
            self.db_connection.commit()

            # Уведомление об успехе
            self.statusBar().showMessage(f"Ответ на отзыв #{review_id} сохранен")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка сохранения",
                f"Не удалось сохранить ответ на отзыв: {e}"
            )

    def send_review_response(self):
        """Отправка ответа на отзыв (сохранение + отправка)"""
        # Сначала сохраняем ответ
        self.save_review_response()

        # Получаем выбранную строку
        row = self.reviews_table.currentRow()
        if row < 0:
            return

        # Получаем ID отзыва
        review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

        # В реальном приложении здесь был бы код для отправки ответа
        # Например, вызов API или отправка email

        # Уведомляем пользователя
        QMessageBox.information(
            self,
            "Отправка ответа",
            f"Ответ на отзыв #{review_id} успешно отправлен клиенту"
        )

    def update_review_reaction(self, likes, dislikes):
        """Обновление реакций (лайки/дизлайки) на отзыв"""
        # Получаем выбранную строку
        row = self.reviews_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите отзыв для обновления реакций")
            return

        # Получаем ID отзыва
        review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

        try:
            # Получаем текущие значения реакций
            reviews_table = DB_TABLES['reviews']['name']
            query = f"SELECT likes, dislikes FROM {reviews_table} WHERE id = %s"
            self.cursor.execute(query, (review_id,))
            result = self.cursor.fetchone()

            if not result:
                return

            current_likes = result['likes'] or 0
            current_dislikes = result['dislikes'] or 0

            # Обновляем значения
            new_likes = current_likes + likes
            new_dislikes = current_dislikes + dislikes

            # Обновляем в БД
            query = f"UPDATE {reviews_table} SET likes = %s, dislikes = %s WHERE id = %s"
            self.cursor.execute(query, (new_likes, new_dislikes, review_id))
            self.db_connection.commit()

            # Уведомление об успехе
            if likes > 0:
                self.statusBar().showMessage(f"Лайк добавлен к отзыву #{review_id}. Текущее количество: {new_likes}")
            else:
                self.statusBar().showMessage(
                    f"Дизлайк добавлен к отзыву #{review_id}. Текущее количество: {new_dislikes}")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                f"Не удалось обновить реакции: {e}"
            )

    def delete_current_review(self):
        """Удаление текущего отзыва"""
        # Получаем выбранную строку
        row = self.reviews_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите отзыв для удаления")
            return

        # Получаем ID отзыва
        review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить отзыв #{review_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            # Удаляем отзыв из БД
            reviews_table = DB_TABLES['reviews']['name']
            query = f"DELETE FROM {reviews_table} WHERE id = %s"
            self.cursor.execute(query, (review_id,))
            self.db_connection.commit()

            # Удаляем строку из таблицы
            self.reviews_table.removeRow(row)

            # Очищаем детали отзыва
            self.review_detail_title.setText("Детали отзыва")
            self.detail_client_name.setText("")
            self.detail_client_order.setText("")
            self.detail_service.setText("")
            self.detail_date.setText("")
            self.detail_rating.setText("★★★★★")
            self.detail_text.setText("")
            self.detail_response.setText("")

            # Уведомление об успехе
            self.statusBar().showMessage(f"Отзыв #{review_id} удален")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка удаления",
                f"Не удалось удалить отзыв: {e}"
            )

    # === Методы для работы с контактами ===

    def load_contacts(self):
        """Загрузка контактов из базы данных"""
        try:
            if not hasattr(self, 'cursor') or not self.db_connection.is_connected():
                self.init_database()

            # Получаем таблицу контактов
            contacts_table = DB_TABLES['contacts']['name']

            # Формируем SQL-запрос
            query = f"SELECT * FROM {contacts_table} ORDER BY date DESC"

            # Выполняем запрос
            self.cursor.execute(query)
            contacts = self.cursor.fetchall()

            # Заполняем таблицу
            self.contacts_table.setRowCount(0)  # Очищаем таблицу

            for row, contact in enumerate(contacts):
                self.contacts_table.insertRow(row)

                # ID
                id_item = QTableWidgetItem(str(contact['id']))
                id_item.setData(Qt.UserRole, contact['id'])
                self.contacts_table.setItem(row, 0, id_item)

                # Имя
                name_item = QTableWidgetItem(contact['name'])
                self.contacts_table.setItem(row, 1, name_item)

                # Email
                email_item = QTableWidgetItem(contact['email'])
                self.contacts_table.setItem(row, 2, email_item)

                # Дата
                if isinstance(contact['date'], datetime):
                    date_str = contact['date'].strftime("%d.%m.%Y %H:%M")
                else:
                    date_str = str(contact['date'])
                date_item = QTableWidgetItem(date_str)
                self.contacts_table.setItem(row, 3, date_item)

                # Статус
                status_item = QTableWidgetItem(contact['status'])

                # Цветовое выделение в зависимости от статуса
                if contact['status'] == 'new' or contact['status'] == 'Новый':
                    status_item.setBackground(QColor(255, 255, 200))  # Светло-желтый
                elif contact['status'] == 'in_progress' or contact['status'] == 'В обработке':
                    status_item.setBackground(QColor(200, 200, 255))  # Светло-синий
                elif contact['status'] == 'completed' or contact['status'] == 'Завершен':
                    status_item.setBackground(QColor(200, 255, 200))  # Светло-зеленый
                elif contact['status'] == 'rejected' or contact['status'] == 'Отклонен':
                    status_item.setBackground(QColor(255, 200, 200))  # Светло-красный

                self.contacts_table.setItem(row, 4, status_item)

            # Обновляем интерфейс
            self.contacts_table.resizeColumnsToContents()
            self.statusBar().showMessage(f"Загружено {len(contacts)} контактов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка загрузки данных",
                f"Не удалось загрузить контакты: {e}"
            )

    def show_contact_details(self):
        """Отображение деталей выбранного контакта"""
        # Получаем выбранную строку
        row = self.contacts_table.currentRow()
        if row < 0:
            return

        # Получаем ID контакта
        contact_id = self.contacts_table.item(row, 0).data(Qt.UserRole)

        try:
            # Получаем данные контакта из БД
            contacts_table = DB_TABLES['contacts']['name']
            query = f"SELECT * FROM {contacts_table} WHERE id = %s"
            self.cursor.execute(query, (contact_id,))
            contact = self.cursor.fetchone()

            if not contact:
                return

            # Заполняем поля деталей
            self.contact_detail_title.setText(f"Контакт #{contact['id']}")
            self.detail_contact_name.setText(contact['name'])
            self.detail_contact_email.setText(contact['email'])
            self.detail_contact_phone.setText(contact['phone'] if contact['phone'] else 'Не указано')

            # Форматируем дату
            if isinstance(contact['date'], datetime):
                formatted_date = contact['date'].strftime("%d.%m.%Y %H:%M:%S")
            else:
                formatted_date = str(contact['date'])
            self.detail_contact_date.setText(formatted_date)

            # Сообщение
            self.detail_contact_message.setText(contact['message'] if contact['message'] else '')

            # Статус
            status_index = 0
            status = contact['status']
            if status == 'in_progress' or status == 'В обработке':
                status_index = 1
            elif status == 'completed' or status == 'Завершен':
                status_index = 2
            elif status == 'rejected' or status == 'Отклонен':
                status_index = 3
            self.detail_contact_status.setCurrentIndex(status_index)

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить детали контакта: {e}"
            )

    def apply_contact_filters(self):
        """Применение фильтров к списку контактов"""
        try:
            # Получаем выбранные фильтры
            status_filter = self.contact_status_filter.currentText()

            # Формируем условия SQL-запроса
            conditions = []
            params = []

            if status_filter != "Все статусы":
                # Преобразуем статус для SQL-запроса
                status_map = {
                    "Новые": "new",
                    "В обработке": "in_progress",
                    "Завершенные": "completed",
                    "Отклоненные": "rejected"
                }
                db_status = status_map.get(status_filter, status_filter)
                conditions.append("status = %s")
                params.append(db_status)

            # Формируем SQL-запрос
            contacts_table = DB_TABLES['contacts']['name']
            query = f"SELECT * FROM {contacts_table}"

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY date DESC"

            # Выполняем запрос
            self.cursor.execute(query, params)
            contacts = self.cursor.fetchall()

            # Обновляем таблицу
            self.contacts_table.setRowCount(0)

            for row, contact in enumerate(contacts):
                self.contacts_table.insertRow(row)

                # ID
                id_item = QTableWidgetItem(str(contact['id']))
                id_item.setData(Qt.UserRole, contact['id'])
                self.contacts_table.setItem(row, 0, id_item)

                # Имя
                name_item = QTableWidgetItem(contact['name'])
                self.contacts_table.setItem(row, 1, name_item)

                # Email
                email_item = QTableWidgetItem(contact['email'])
                self.contacts_table.setItem(row, 2, email_item)

                # Дата
                if isinstance(contact['date'], datetime):
                    date_str = contact['date'].strftime("%d.%m.%Y %H:%M")
                else:
                    date_str = str(contact['date'])
                date_item = QTableWidgetItem(date_str)
                self.contacts_table.setItem(row, 3, date_item)

                # Статус
                status_item = QTableWidgetItem(contact['status'])

                # Цветовое выделение
                if contact['status'] == 'new' or contact['status'] == 'Новый':
                    status_item.setBackground(QColor(255, 255, 200))
                elif contact['status'] == 'in_progress' or contact['status'] == 'В обработке':
                    status_item.setBackground(QColor(200, 200, 255))
                elif contact['status'] == 'completed' or contact['status'] == 'Завершен':
                    status_item.setBackground(QColor(200, 255, 200))
                elif contact['status'] == 'rejected' or contact['status'] == 'Отклонен':
                    status_item.setBackground(QColor(255, 200, 200))

                self.contacts_table.setItem(row, 4, status_item)

            # Обновляем статусную строку
            self.statusBar().showMessage(f"Найдено {len(contacts)} контактов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка фильтрации",
                f"Не удалось применить фильтры: {e}"
            )

    def search_contacts(self, text):
        """Поиск контактов по тексту"""
        try:
            if not text.strip():
                # Если поле поиска пустое, просто обновляем данные
                self.load_contacts()
                return

            # Формируем SQL-запрос с поиском
            contacts_table = DB_TABLES['contacts']['name']
            search_pattern = f"%{text}%"

            query = f"""
                SELECT * FROM {contacts_table} 
                WHERE name LIKE %s 
                OR email LIKE %s 
                OR phone LIKE %s 
                OR message LIKE %s
                ORDER BY date DESC
            """

            # Выполняем запрос
            self.cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            contacts = self.cursor.fetchall()

            # Обновляем таблицу
            self.contacts_table.setRowCount(0)

            for row, contact in enumerate(contacts):
                self.contacts_table.insertRow(row)

                # ID
                id_item = QTableWidgetItem(str(contact['id']))
                id_item.setData(Qt.UserRole, contact['id'])
                self.contacts_table.setItem(row, 0, id_item)

                # Имя
                name_item = QTableWidgetItem(contact['name'])
                self.contacts_table.setItem(row, 1, name_item)

                # Email
                email_item = QTableWidgetItem(contact['email'])
                self.contacts_table.setItem(row, 2, email_item)

                # Дата
                if isinstance(contact['date'], datetime):
                    date_str = contact['date'].strftime("%d.%m.%Y %H:%M")
                else:
                    date_str = str(contact['date'])
                date_item = QTableWidgetItem(date_str)
                self.contacts_table.setItem(row, 3, date_item)

                # Статус
                status_item = QTableWidgetItem(contact['status'])

                # Цветовое выделение
                if contact['status'] == 'new' or contact['status'] == 'Новый':
                    status_item.setBackground(QColor(255, 255, 200))
                elif contact['status'] == 'in_progress' or contact['status'] == 'В обработке':
                    status_item.setBackground(QColor(200, 200, 255))
                elif contact['status'] == 'completed' or contact['status'] == 'Завершен':
                    status_item.setBackground(QColor(200, 255, 200))
                elif contact['status'] == 'rejected' or contact['status'] == 'Отклонен':
                    status_item.setBackground(QColor(255, 200, 200))

                self.contacts_table.setItem(row, 4, status_item)

            # Обновляем статусную строку
            self.statusBar().showMessage(f"Найдено {len(contacts)} контактов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка поиска",
                f"Не удалось выполнить поиск: {e}"
            )

    def update_contact_status(self):
        """Обновление статуса контакта"""
        # Получаем выбранную строку
        row = self.contacts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите контакт для обновления статуса")
            return

        # Получаем ID контакта
        contact_id = self.contacts_table.item(row, 0).data(Qt.UserRole)

        # Получаем новый статус
        status_index = self.detail_contact_status.currentIndex()
        status_map = ["new", "in_progress", "completed", "rejected"]
        new_status = status_map[status_index]

        try:
            # Обновляем статус в БД
            contacts_table = DB_TABLES['contacts']['name']
            query = f"UPDATE {contacts_table} SET status = %s WHERE id = %s"
            self.cursor.execute(query, (new_status, contact_id))
            self.db_connection.commit()

            # Обновляем отображение в таблице
            status_item = QTableWidgetItem(new_status)

            # Цветовое выделение
            if new_status == 'new':
                status_item.setBackground(QColor(255, 255, 200))
            elif new_status == 'in_progress':
                status_item.setBackground(QColor(200, 200, 255))
            elif new_status == 'completed':
                status_item.setBackground(QColor(200, 255, 200))
            elif new_status == 'rejected':
                status_item.setBackground(QColor(255, 200, 200))

            self.contacts_table.setItem(row, 4, status_item)

            # Уведомление об успехе
            self.statusBar().showMessage(f"Статус контакта #{contact_id} изменен на {new_status}")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                f"Не удалось обновить статус контакта: {e}"
            )

    def send_email_to_contact(self):
        """Отправка сообщения контакту через WhatsApp или Email"""
        # Получаем выбранную строку
        row = self.contacts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите контакт для отправки сообщения")
            return

        # Получаем контактные данные
        email = self.detail_contact_email.text()
        phone = self.detail_contact_phone.text().replace(' ', '').replace('-', '').replace('+', '')
        name = self.detail_contact_name.text()

        if not email and not phone:
            QMessageBox.warning(self, "Предупреждение",
                                "У выбранного контакта отсутствует email и телефон")
            return

        # Создаем диалог выбора способа связи
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
        from PyQt5.QtCore import Qt

        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите способ связи")
        dialog.setFixedWidth(400)

        layout = QVBoxLayout(dialog)

        # Добавляем заголовок
        title = QLabel("Выберите способ связи с клиентом:")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(title)

        # Информация о контакте
        contact_info = QLabel(f"Имя: {name}")
        layout.addWidget(contact_info)

        buttons_layout = QHBoxLayout()

        # Кнопка WhatsApp
        whatsapp_btn = QPushButton("WhatsApp")
        whatsapp_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
        """)

        # Кнопка Email
        email_btn = QPushButton("Email")
        email_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                border-radius: 4px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0D47A1;
            }
        """)

        # Отключаем кнопки, если нет соответствующих данных
        if not phone:
            whatsapp_btn.setEnabled(False)
            whatsapp_btn.setToolTip("Нет номера телефона")

        if not email:
            email_btn.setEnabled(False)
            email_btn.setToolTip("Нет адреса электронной почты")

        buttons_layout.addWidget(whatsapp_btn)
        buttons_layout.addWidget(email_btn)

        # Кнопка отмены
        cancel_btn = QPushButton("Отмена")

        layout.addLayout(buttons_layout)
        layout.addWidget(cancel_btn)

        # Настраиваем обработчики событий
        cancel_btn.clicked.connect(dialog.reject)

        # Функция для отправки сообщения через WhatsApp
        def open_whatsapp():
            try:
                import webbrowser

                # Формируем текст сообщения
                message = f"Здравствуйте, {name}! Вы оставляли заявку на нашем сайте. Чем я могу вам помочь?"

                # Очищаем телефон от всех нецифровых символов
                import re
                clean_phone = re.sub(r'\D', '', phone)

                # Проверяем, что номер не начинается с 8, если начинается, меняем на 7
                if clean_phone.startswith('8') and len(clean_phone) == 11:
                    clean_phone = '7' + clean_phone[1:]

                # Исправленный способ формирования URL для WhatsApp
                # Не используем URL-кодирование, т.к. WhatsApp Web API может некорректно его обрабатывать
                url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={message}"

                # Выводим URL для отладки
                print(f"Opening WhatsApp URL: {url}")

                webbrowser.open(url)
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть WhatsApp: {str(e)}")

        # Функция для отправки Email
        def open_email():
            try:
                import webbrowser
                import urllib.parse

                # Формируем тему и текст письма с новой подписью
                subject = "Ответ на ваше обращение"
                body = f"""Здравствуйте, {name}!

    Спасибо за ваше обращение. Мы получили вашу заявку и готовы ответить на ваши вопросы.

    С уважением,
    Гурбанмырадов Мукам Ровшенович и его команда поддержки ООО MPSP 2017-2025"""

                # URL-encode темы и текста
                encoded_subject = urllib.parse.quote(subject)
                encoded_body = urllib.parse.quote(body)

                # Открываем почтовый клиент с предзаполненными полями
                url = f"mailto:{email}?subject={encoded_subject}&body={encoded_body}"
                webbrowser.open(url)
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть почтовый клиент: {str(e)}")

        # Связываем функции с кнопками
        whatsapp_btn.clicked.connect(open_whatsapp)
        email_btn.clicked.connect(open_email)

        # Показываем диалог
        dialog.exec_()
    def delete_current_contact(self):
        """Удаление текущего контакта"""
        # Получаем выбранную строку
        row = self.contacts_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Предупреждение", "Выберите контакт для удаления")
            return

        # Получаем ID контакта
        contact_id = self.contacts_table.item(row, 0).data(Qt.UserRole)

        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить контакт #{contact_id}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            # Удаляем контакт из БД
            contacts_table = DB_TABLES['contacts']['name']
            query = f"DELETE FROM {contacts_table} WHERE id = %s"
            self.cursor.execute(query, (contact_id,))
            self.db_connection.commit()

            # Удаляем строку из таблицы
            self.contacts_table.removeRow(row)

            # Очищаем детали контакта
            self.contact_detail_title.setText("Детали контакта")
            self.detail_contact_name.setText("")
            self.detail_contact_email.setText("")
            self.detail_contact_phone.setText("")
            self.detail_contact_date.setText("")
            self.detail_contact_message.setText("")

            # Уведомление об успехе
            self.statusBar().showMessage(f"Контакт #{contact_id} удален")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка удаления",
                f"Не удалось удалить контакт: {e}"
            )

    def process_selected_contacts(self):
        """Перевод выбранных контактов в статус 'В обработке'"""
        # Получаем выбранные строки
        selected_rows = set()
        for item in self.contacts_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите контакты для обработки")
            return

        try:
            contacts_table = DB_TABLES['contacts']['name']

            for row in selected_rows:
                # Получаем ID контакта
                contact_id = self.contacts_table.item(row, 0).data(Qt.UserRole)

                # Обновляем статус в БД
                query = f"UPDATE {contacts_table} SET status = 'in_progress' WHERE id = %s"
                self.cursor.execute(query, (contact_id,))

                # Обновляем отображение в таблице
                status_item = QTableWidgetItem("in_progress")
                status_item.setBackground(QColor(200, 200, 255))
                self.contacts_table.setItem(row, 4, status_item)

            # Фиксируем транзакцию
            self.db_connection.commit()

            # Уведомление об успехе
            self.statusBar().showMessage(f"{len(selected_rows)} контактов переведено в статус 'В обработке'")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                f"Не удалось обновить статус контактов: {e}"
            )

    def reject_selected_contacts(self):
        """Отклонение выбранных контактов"""
        # Получаем выбранные строки
        selected_rows = set()
        for item in self.contacts_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите контакты для отклонения")
            return

        try:
            contacts_table = DB_TABLES['contacts']['name']

            for row in selected_rows:
                # Получаем ID контакта
                contact_id = self.contacts_table.item(row, 0).data(Qt.UserRole)

                # Обновляем статус в БД
                query = f"UPDATE {contacts_table} SET status = 'rejected' WHERE id = %s"
                self.cursor.execute(query, (contact_id,))

                # Обновляем отображение в таблице
                status_item = QTableWidgetItem("rejected")
                status_item.setBackground(QColor(255, 200, 200))
                self.contacts_table.setItem(row, 4, status_item)

            # Фиксируем транзакцию
            self.db_connection.commit()

            # Уведомление об успехе
            self.statusBar().showMessage(f"{len(selected_rows)} контактов отклонено")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                f"Не удалось отклонить контакты: {e}"
            )

    def delete_selected_reviews(self):
        """Удаление выбранных отзывов"""
        # Получаем выбранные строки
        selected_rows = set()
        for item in self.reviews_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите отзывы для удаления")
            return

        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить {len(selected_rows)} отзывов?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            reviews_table = DB_TABLES['reviews']['name']

            # Сортируем строки в обратном порядке, чтобы не сбивалась индексация при удалении
            for row in sorted(selected_rows, reverse=True):
                # Получаем ID отзыва
                review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

                # Удаляем отзыв из БД
                query = f"DELETE FROM {reviews_table} WHERE id = %s"
                self.cursor.execute(query, (review_id,))

                # Удаляем строку из таблицы
                self.reviews_table.removeRow(row)

            # Фиксируем транзакцию
            self.db_connection.commit()

            # Очищаем детали отзыва, если текущий отзыв был удален
            if self.reviews_table.currentRow() < 0:
                self.review_detail_title.setText("Детали отзыва")
                self.detail_client_name.setText("")
                self.detail_client_order.setText("")
                self.detail_service.setText("")
                self.detail_date.setText("")
                self.detail_rating.setText("★★★★★")
                self.detail_text.setText("")
                self.detail_response.setText("")

            # Уведомление об успехе
            self.statusBar().showMessage(f"Удалено {len(selected_rows)} отзывов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка удаления",
                f"Не удалось удалить отзывы: {e}"
            )

    def delete_selected_contacts(self):
        """Удаление выбранных контактов"""
        # Получаем выбранные строки
        selected_rows = set()
        for item in self.contacts_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите контакты для удаления")
            return

        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите удалить {len(selected_rows)} контактов?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        try:
            contacts_table = DB_TABLES['contacts']['name']

            # Сортируем строки в обратном порядке, чтобы не сбивалась индексация при удалении
            for row in sorted(selected_rows, reverse=True):
                # Получаем ID контакта
                contact_id = self.contacts_table.item(row, 0).data(Qt.UserRole)

                # Удаляем контакт из БД
                query = f"DELETE FROM {contacts_table} WHERE id = %s"
                self.cursor.execute(query, (contact_id,))

                # Удаляем строку из таблицы
                self.contacts_table.removeRow(row)

            # Фиксируем транзакцию
            self.db_connection.commit()

            # Очищаем детали контакта, если текущий контакт был удален
            if self.contacts_table.currentRow() < 0:
                self.contact_detail_title.setText("Детали контакта")
                self.detail_contact_name.setText("")
                self.detail_contact_email.setText("")
                self.detail_contact_phone.setText("")
                self.detail_contact_date.setText("")
                self.detail_contact_message.setText("")

            # Уведомление об успехе
            self.statusBar().showMessage(f"Удалено {len(selected_rows)} контактов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка удаления",
                f"Не удалось удалить контакты: {e}"
            )
    def approve_selected_reviews(self):
        """Одобрение выбранных отзывов"""
        # Получаем выбранные строки
        selected_rows = set()
        for item in self.reviews_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите отзывы для одобрения")
            return

        try:
            reviews_table = DB_TABLES['reviews']['name']

            for row in selected_rows:
                # Получаем ID отзыва
                review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

                # Обновляем статус в БД
                query = f"UPDATE {reviews_table} SET status = 'approved' WHERE id = %s"
                self.cursor.execute(query, (review_id,))

                # Обновляем отображение в таблице
                status_item = QTableWidgetItem("approved")
                status_item.setBackground(QColor(200, 255, 200))
                self.reviews_table.setItem(row, 4, status_item)

            # Фиксируем транзакцию
            self.db_connection.commit()

            # Уведомление об успехе
            self.statusBar().showMessage(f"Одобрено {len(selected_rows)} отзывов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                f"Не удалось одобрить отзывы: {e}"
            )

    def reject_selected_reviews(self):
        """Отклонение выбранных отзывов"""
        # Получаем выбранные строки
        selected_rows = set()
        for item in self.reviews_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Выберите отзывы для отклонения")
            return

        try:
            reviews_table = DB_TABLES['reviews']['name']

            for row in selected_rows:
                # Получаем ID отзыва
                review_id = self.reviews_table.item(row, 0).data(Qt.UserRole)

                # Обновляем статус в БД
                query = f"UPDATE {reviews_table} SET status = 'rejected' WHERE id = %s"
                self.cursor.execute(query, (review_id,))

                # Обновляем отображение в таблице
                status_item = QTableWidgetItem("rejected")
                status_item.setBackground(QColor(255, 200, 200))
                self.reviews_table.setItem(row, 4, status_item)

            # Фиксируем транзакцию
            self.db_connection.commit()

            # Уведомление об успехе
            self.statusBar().showMessage(f"Отклонено {len(selected_rows)} отзывов")

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка обновления",
                f"Не удалось отклонить отзывы: {e}"
            )


    def execute_sql_query(self):
        """Выполнение SQL-запроса"""
        # Получаем текст запроса
        query = self.sql_query_edit.toPlainText().strip()
        if not query:
            QMessageBox.warning(self, "Предупреждение", "Введите SQL-запрос")
            return

        try:
            # Очищаем предыдущие результаты и ошибки
            self.sql_results_table.setRowCount(0)
            self.sql_results_table.setColumnCount(0)
            self.sql_error_label.setText("")

            # Выполняем запрос
            self.cursor.execute(query)

            # Проверяем тип запроса
            if query.strip().upper().startswith(("SELECT", "SHOW")):
                # Получаем результаты запроса
                results = self.cursor.fetchall()

                if not results:
                    self.sql_error_label.setText("Запрос выполнен успешно. Нет данных для отображения.")
                    return

                # Настраиваем таблицу для отображения результатов
                columns = results[0].keys()
                self.sql_results_table.setColumnCount(len(columns))
                self.sql_results_table.setHorizontalHeaderLabels(columns)

                # Заполняем таблицу данными
                for row, data in enumerate(results):
                    self.sql_results_table.insertRow(row)
                    for col, column in enumerate(columns):
                        value = data[column]

                        # Форматируем значение для отображения
                        if value is None:
                            display_value = "NULL"
                        elif isinstance(value, datetime):
                            display_value = value.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            display_value = str(value)

                        item = QTableWidgetItem(display_value)
                        self.sql_results_table.setItem(row, col, item)

                # Настраиваем отображение таблицы
                self.sql_results_table.resizeColumnsToContents()
                self.statusBar().showMessage(f"Запрос выполнен успешно. Получено {len(results)} записей.")
            else:
                # Для запросов, которые не возвращают данные (INSERT, UPDATE, DELETE и т.д.)
                self.db_connection.commit()
                rows_affected = self.cursor.rowcount
                self.sql_error_label.setText(f"Запрос выполнен успешно. Затронуто строк: {rows_affected}")
                self.statusBar().showMessage(f"Запрос выполнен успешно. Затронуто строк: {rows_affected}")

        except mysql.connector.Error as e:
            # Отображаем ошибку
            self.sql_error_label.setText(f"Ошибка выполнения запроса: {e}")
            self.statusBar().showMessage("Ошибка выполнения запроса")

    def clear_sql_query(self):
        """Очистка поля SQL-запроса"""
        self.sql_query_edit.clear()

    def apply_sql_template(self):
        """Применение шаблона SQL-запроса"""
        template_index = self.sql_templates.currentIndex()
        if template_index == 0:
            return  # Не выбран шаблон

        # Получаем текст шаблона
        templates = [
            "",  # Пустой шаблон для "Выберите шаблон"
            f"SELECT * FROM {DB_TABLES['reviews']['name']} LIMIT 100",
            f"SELECT * FROM {DB_TABLES['contacts']['name']} LIMIT 100",
            f"SELECT status, COUNT(*) as count FROM {DB_TABLES['reviews']['name']} GROUP BY status",
            f"SELECT status, COUNT(*) as count FROM {DB_TABLES['contacts']['name']} GROUP BY status",
            """CREATE TABLE example_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP
)"""
        ]

        # Устанавливаем выбранный шаблон
        if template_index < len(templates):
            self.sql_query_edit.setText(templates[template_index])

        # === Методы для работы с настройками ===

    def test_database_connection(self):
        """Проверка соединения с базой данных"""
        try:
            # Получаем данные из полей формы
            host = self.db_host.text().strip()
            user = self.db_user.text().strip()
            password = self.db_password.text()
            database = self.db_name.text().strip()

            # Проверяем обязательные поля
            if not host or not user or not database:
                QMessageBox.warning(self, "Предупреждение", "Заполните все обязательные поля")
                return

            # Пытаемся установить соединение
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )

            if connection.is_connected():
                server_info = connection.get_server_info()
                cursor = connection.cursor()
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()[0]

                QMessageBox.information(
                    self,
                    "Успешное подключение",
                    f"Подключение к базе данных успешно установлено!\n\n"
                    f"Сервер MySQL: {server_info}\n"
                    f"База данных: {db_name}"
                )

                # Закрываем соединение
                cursor.close()
                connection.close()

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка подключения",
                f"Не удалось подключиться к базе данных:\n\n{e}"
            )

    def add_response_template_row(self):
        """Добавление новой строки в таблицу шаблонов ответов"""
        row = self.templates_table.rowCount()
        self.templates_table.insertRow(row)
        self.templates_table.setItem(row, 0, QTableWidgetItem("Новый шаблон"))
        self.templates_table.setItem(row, 1, QTableWidgetItem("Текст шаблона"))

    def delete_response_template_row(self):
        """Удаление выбранной строки из таблицы шаблонов ответов"""
        row = self.templates_table.currentRow()
        if row >= 0:
            self.templates_table.removeRow(row)

    def save_response_templates(self):
        """Сохранение шаблонов ответов"""
        # В реальном приложении здесь был бы код для сохранения шаблонов в БД или файл
        # Для демонстрации просто показываем сообщение
        QMessageBox.information(
            self,
            "Сохранение шаблонов",
            "Шаблоны ответов успешно сохранены"
        )

        # Обновляем список шаблонов в комбобоксе
        self.response_template.clear()
        self.response_template.addItem("Выберите шаблон")

        for row in range(self.templates_table.rowCount()):
            template_name = self.templates_table.item(row, 0).text()
            self.response_template.addItem(template_name)

    def save_settings(self):
        """Сохранение настроек приложения"""
        # Получаем данные из полей формы
        db_settings = {
            'host': self.db_host.text().strip(),
            'user': self.db_user.text().strip(),
            'password': self.db_password.text(),
            'database': self.db_name.text().strip(),
            'charset': 'utf8mb4'
        }

        # Проверяем обязательные поля
        if not db_settings['host'] or not db_settings['user'] or not db_settings['database']:
            QMessageBox.warning(self, "Предупреждение", "Заполните все обязательные поля настроек базы данных")
            return

        # Обновляем настройки
        global DB_CONFIG
        DB_CONFIG.update(db_settings)

        # Обновляем интервал обновления
        refresh_interval = self.refresh_interval.value()
        self.update_timer.setInterval(refresh_interval * 1000)

        # Сохраняем настройки в файл конфигурации
        # В реальном приложении здесь был бы код для сохранения настроек

        QMessageBox.information(
            self,
            "Сохранение настроек",
            "Настройки успешно сохранены"
        )

        # Переподключаемся к базе данных с новыми настройками
        try:
            if hasattr(self, 'db_connection') and self.db_connection.is_connected():
                self.cursor.close()
                self.db_connection.close()

            self.init_database()
            self.load_reviews()
            self.load_contacts()

        except mysql.connector.Error as e:
            QMessageBox.critical(
                self,
                "Ошибка подключения",
                f"Не удалось подключиться к базе данных с новыми настройками:\n\n{e}"
            )

    def reset_settings(self):
        """Сброс настроек к значениям по умолчанию"""
        # Запрашиваем подтверждение
        reply = QMessageBox.question(
            self,
            "Подтверждение сброса",
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            return

        # Сбрасываем настройки БД
        self.db_host.setText('mpsp.online')
        self.db_user.setText(DB_CONFIG['user'])
        self.db_password.setText(DB_CONFIG['password'])
        self.db_name.setText(DB_CONFIG['database'])

        # Сбрасываем интервал обновления
        self.refresh_interval.setValue(60)

        # Сбрасываем настройки уведомлений
        self.show_notifications.setChecked(True)
        self.sound_notifications.setChecked(True)

        # Сбрасываем шаблоны ответов
        self.templates_table.setRowCount(4)

        templates = [
            ("Благодарность за положительный отзыв",
             "Спасибо за ваш положительный отзыв! Мы очень рады, что вы остались довольны нашими услугами. Будем рады видеть вас снова!"),
            ("Ответ на критику",
             "Благодарим вас за отзыв и обратную связь. Мы ценим ваше мнение и работаем над улучшением наших услуг. Приносим извинения за доставленные неудобства."),
            ("Извинения за проблему",
             "Приносим искренние извинения за возникшие проблемы. Мы уже разбираемся с ситуацией и сделаем всё возможное, чтобы решить вопрос в кратчайшие сроки."),
            ("Стандартный ответ",
             "Благодарим вас за обращение. Ваше мнение очень важно для нас. Мы обязательно учтем ваши пожелания в нашей дальнейшей работе.")
        ]

        for i, (name, text) in enumerate(templates):
            self.templates_table.setItem(i, 0, QTableWidgetItem(name))
            self.templates_table.setItem(i, 1, QTableWidgetItem(text))

        QMessageBox.information(
            self,
            "Сброс настроек",
            "Настройки успешно сброшены к значениям по умолчанию"
        )

        # === Общие методы ===

    def refresh_data(self):
        """Обновление данных"""
        current_tab = self.tabs.currentIndex()

        if current_tab == 0:  # Вкладка отзывов
            self.load_reviews()
        elif current_tab == 1:  # Вкладка контактов
            self.load_contacts()

        self.statusBar().showMessage("Данные обновлены")

    def check_for_updates(self):
        """Проверка наличия новых данных"""
        try:
            if not hasattr(self, 'cursor') or not self.db_connection.is_connected():
                self.init_database()

            # Проверяем наличие новых отзывов
            if hasattr(self, 'last_review_check'):
                reviews_table = DB_TABLES['reviews']['name']

                query = f"""
                            SELECT COUNT(*) as count FROM {reviews_table} 
                            WHERE date > %s
                        """

                self.cursor.execute(query, (self.last_review_check,))
                result = self.cursor.fetchone()

                if result and result['count'] > 0:
                    # Уведомляем о новых отзывах
                    if self.show_notifications.isChecked():
                        QMessageBox.information(
                            self,
                            "Новые отзывы",
                            f"Получено {result['count']} новых отзывов"
                        )

                    # Обновляем данные, если открыта вкладка отзывов
                    if self.tabs.currentIndex() == 0:
                        self.load_reviews()

            # Проверяем наличие новых контактов
            if hasattr(self, 'last_contact_check'):
                contacts_table = DB_TABLES['contacts']['name']

                query = f"""
                            SELECT COUNT(*) as count FROM {contacts_table} 
                            WHERE date > %s
                        """

                self.cursor.execute(query, (self.last_contact_check,))
                result = self.cursor.fetchone()

                if result and result['count'] > 0:
                    # Уведомляем о новых контактах
                    if self.show_notifications.isChecked():
                        QMessageBox.information(
                            self,
                            "Новые контакты",
                            f"Получено {result['count']} новых контактных запросов"
                        )

                    # Обновляем данные, если открыта вкладка контактов
                    if self.tabs.currentIndex() == 1:
                        self.load_contacts()

            # Обновляем время последней проверки
            now = datetime.now()
            self.last_review_check = now
            self.last_contact_check = now

        except mysql.connector.Error as e:
            # Тихая обработка ошибки для фоновой проверки
            print(f"Ошибка при проверке обновлений: {e}")

    def export_data(self):
        """Экспорт данных"""
        # Создаем меню экспорта
        export_menu = QMenu(self)

        export_reviews_csv = QAction("📊 Экспорт отзывов в CSV", self)
        export_reviews_csv.triggered.connect(lambda: self.export_to_csv('reviews'))

        export_contacts_csv = QAction("📊 Экспорт контактов в CSV", self)
        export_contacts_csv.triggered.connect(lambda: self.export_to_csv('contacts'))

        export_menu.addAction(export_reviews_csv)
        export_menu.addAction(export_contacts_csv)

        # Показываем меню
        export_menu.exec_(QCursor.pos())

    def export_to_csv(self, table_type):
        """Экспорт данных в CSV-файл"""
        try:
            if table_type == 'reviews':
                table_name = DB_TABLES['reviews']['name']
                file_prefix = "reviews"
            else:
                table_name = DB_TABLES['contacts']['name']
                file_prefix = "contacts"

            # Получаем данные
            query = f"SELECT * FROM {table_name}"
            self.cursor.execute(query)
            data = self.cursor.fetchall()

            if not data:
                QMessageBox.warning(self, "Предупреждение", "Нет данных для экспорта")
                return

            # Запрашиваем путь сохранения
            from PyQt5.QtWidgets import QFileDialog

            file_name = f"{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как CSV", file_name, "CSV файлы (*.csv)"
            )

            if not file_path:
                return

            # Записываем данные в CSV
            import csv

            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Используем первую запись для получения имен полей
                fieldnames = data[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Записываем заголовки
                writer.writeheader()

                # Записываем данные
                for row in data:
                    writer.writerow(row)

            QMessageBox.information(
                self,
                "Экспорт завершен",
                f"Данные успешно экспортированы в файл:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Не удалось экспортировать данные:\n\n{e}"
            )

    def import_data(self):
        """Импорт данных"""
        # Создаем меню импорта
        import_menu = QMenu(self)

        import_reviews_csv = QAction("📥 Импорт отзывов из CSV", self)
        import_reviews_csv.triggered.connect(lambda: self.import_from_csv('reviews'))

        import_contacts_csv = QAction("📥 Импорт контактов из CSV", self)
        import_contacts_csv.triggered.connect(lambda: self.import_from_csv('contacts'))

        import_menu.addAction(import_reviews_csv)
        import_menu.addAction(import_contacts_csv)

        # Показываем меню
        import_menu.exec_(QCursor.pos())

    def import_from_csv(self, table_type):
        """Импорт данных из CSV-файла"""
        # В реальном приложении здесь был бы код для импорта данных
        # Для демонстрации просто показываем сообщение

        QMessageBox.information(
            self,
            "Импорт данных",
            f"Функция импорта {table_type} из CSV будет реализована в будущих версиях"
        )

    def show_help(self):
        """Отображение справки"""
        help_text = """
        <h2>Справка по использованию</h2>

        <h3>Общие сведения</h3>
        <p>Данное приложение предназначено для управления отзывами и контактными запросами с сайта.</p>

        <h3>Вкладка "Отзывы"</h3>
        <p>Позволяет просматривать, модерировать и отвечать на отзывы клиентов.</p>
        <ul>
            <li><b>Фильтрация:</b> Используйте фильтры для отображения отзывов по статусу и рейтингу.</li>
            <li><b>Поиск:</b> Введите текст для поиска по имени, услуге или тексту отзыва.</li>
            <li><b>Управление:</b> Выберите отзыв для просмотра деталей и изменения статуса.</li>
            <li><b>Пакетные операции:</b> Выберите несколько отзывов для одновременного изменения статуса или удаления.</li>
        </ul>

        <h3>Вкладка "Контакты"</h3>
        <p>Позволяет управлять контактными запросами от клиентов.</p>
        <ul>
            <li><b>Фильтрация:</b> Используйте фильтры для отображения контактов по статусу.</li>
            <li><b>Поиск:</b> Введите текст для поиска по имени, email или тексту сообщения.</li>
            <li><b>Управление:</b> Выберите контакт для просмотра деталей и изменения статуса.</li>
            <li><b>Пакетные операции:</b> Выберите несколько контактов для одновременного изменения статуса или удаления.</li>
        </ul>

        <h3>Вкладка "SQL-запросы"</h3>
        <p>Позволяет выполнять произвольные SQL-запросы к базе данных.</p>
        <ul>
            <li><b>Выполнение запросов:</b> Введите SQL-запрос и нажмите "Выполнить".</li>
            <li><b>Шаблоны:</b> Используйте готовые шаблоны для быстрого создания запросов.</li>
        </ul>

        <h3>Вкладка "Настройки"</h3>
        <p>Позволяет настроить параметры подключения к базе данных и другие настройки.</p>
        <ul>
            <li><b>База данных:</b> Настройте параметры подключения к базе данных.</li>
            <li><b>Интерфейс:</b> Настройте интервал обновления и уведомления.</li>
            <li><b>Шаблоны ответов:</b> Управляйте шаблонами ответов на отзывы.</li>
        </ul>

        <h3>Горячие клавиши</h3>
        <ul>
            <li><b>F5:</b> Обновить данные</li>
            <li><b>Ctrl+Tab:</b> Переключение между вкладками</li>
            <li><b>Delete:</b> Удалить выбранный элемент</li>
        </ul>
        """

        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton

        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Справка")
        help_dialog.setMinimumSize(700, 500)

        layout = QVBoxLayout(help_dialog)

        help_browser = QTextBrowser()
        help_browser.setHtml(help_text)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(help_dialog.accept)

        layout.addWidget(help_browser)
        layout.addWidget(close_button)

        help_dialog.exec_()

    # Функция для создания и запуска приложения
def run_reviews_manager():
    app = QApplication(sys.argv)
    window = ReviewsManagerApp()
    window.show()
    sys.exit(app.exec_())

# Если файл запускается как самостоятельный скрипт
if __name__ == "__main__":
    run_reviews_manager()