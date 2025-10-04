"""
Интеграция модуля управления отзывами и контактами с основным приложением
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QTimer, QSettings

# Импортируем модуль управления отзывами


def add_reviews_button(main_window):
    """
    Добавляет кнопку управления отзывами и контактами в панель инструментов главного окна

    Args:
        main_window: Экземпляр главного окна приложения
    """
    try:
        # Создаем кнопку для панели инструментов
        reviews_button = QPushButton("🌟 Управление отзывами")
        reviews_button.setToolTip("Управление отзывами и контактными формами")
        reviews_button.clicked.connect(lambda: show_reviews_manager(main_window))

        # Добавляем кнопку в тулбар
        if hasattr(main_window, 'toolbar'):
            # Добавляем сепаратор перед кнопкой
            main_window.toolbar.addSeparator()
            main_window.toolbar.addWidget(reviews_button)

            # Запускаем проверку наличия новых отзывов и контактов
            setup_notifications_checker(main_window)
        else:
            print("Предупреждение: toolbar не найден в главном окне")

    except Exception as e:
        print(f"Ошибка при добавлении кнопки управления отзывами: {e}")


def show_reviews_manager(parent=None):
    """
    Открывает окно управления отзывами и контактами

    Args:
        parent: Родительское окно
    """
    try:
        # Проверяем доступность сервера БД перед открытием окна
        from reviews_manager.db_check import check_db_connection

        if not check_db_connection():
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                parent,
                "Проблема с подключением к БД",
                "Не удается подключиться к базе данных отзывов. "
                "Хотите продолжить в ограниченном режиме?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.No:
                return

        # Создаем и показываем окно управления отзывами
        from reviews_manager.reviews_manager_app import ReviewsManagerApp
        reviews_window = ReviewsManagerApp(parent)
        reviews_window.show()

        # Сохраняем ссылку на окно в родительском окне для предотвращения закрытия сборщиком мусора
        if parent:
            if not hasattr(parent, 'reviews_window'):
                parent.reviews_window = reviews_window
            else:
                parent.reviews_window = reviews_window

    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(
            parent,
            "Ошибка",
            f"Не удалось открыть окно управления отзывами: {str(e)}"
        )

def setup_notifications_checker(main_window):
    """
    Настраивает периодическую проверку новых отзывов и контактов

    Args:
        main_window: Экземпляр главного окна приложения
    """
    try:
        # Проверяем наличие таймера
        if not hasattr(main_window, 'reviews_check_timer'):
            # Создаем таймер для проверки новых отзывов/контактов
            main_window.reviews_check_timer = QTimer(main_window)
            main_window.reviews_check_timer.timeout.connect(lambda: check_new_items(main_window))

            # Запускаем проверку каждые 5 минут (300000 мс)
            main_window.reviews_check_timer.start(300000)

            # Инициализируем счетчики
            main_window.new_reviews_count = 0
            main_window.new_contacts_count = 0

    except Exception as e:
        print(f"Ошибка при настройке проверки уведомлений: {e}")


def check_new_items(main_window):
    """
    Проверяет наличие новых отзывов и контактов

    Args:
        main_window: Экземпляр главного окна приложения
    """
    try:
        # В реальном приложении здесь будет код для проверки новых отзывов и контактов
        # Например, запрос к базе данных или API

        # Для демонстрации используем фиктивные данные или временно закомментируем код
        import mysql.connector
        from reviews_manager.config import DB_CONFIG, DB_TABLES

        # Исправляем настройки подключения к БД (используем домен вместо localhost)
        try:
            from reviews_manager.config import DB_CONFIG
            db_config = DB_CONFIG.copy()
        except ImportError:
            db_config = {
                'host': 'mpsp.online',
                'user': 'u3054108_Mukam1',
                'password': 'vYL-f2w-cNk-fuJ',
                'database': 'u3054108_reviews_db',
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
        db_config['host'] = 'mpsp.online'

        # Получаем время последней проверки из настроек
        settings = QSettings("OrderManager", "ReviewsNotifications")
        last_check = settings.value("last_check", None)

        # Устанавливаем соединение с БД
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        # Проверяем новые отзывы
        new_reviews_count = 0
        new_contacts_count = 0

        if last_check:
            # Конвертируем строку в объект datetime, если необходимо
            if isinstance(last_check, str):
                from datetime import datetime
                try:
                    last_check = datetime.strptime(last_check, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    last_check = None

            if last_check:
                # Формируем запросы на проверку новых записей
                reviews_table = DB_TABLES['reviews']['name']
                contacts_table = DB_TABLES['contacts']['name']

                # Запрос для подсчета новых отзывов
                query = f"""
                    SELECT COUNT(*) as count 
                    FROM {reviews_table} 
                    WHERE date > %s AND status = 'pending'
                """
                cursor.execute(query, (last_check,))
                result = cursor.fetchone()
                if result:
                    new_reviews_count = result['count']

                # Запрос для подсчета новых контактов
                query = f"""
                    SELECT COUNT(*) as count 
                    FROM {contacts_table} 
                    WHERE date > %s AND status = 'new'
                """
                cursor.execute(query, (last_check,))
                result = cursor.fetchone()
                if result:
                    new_contacts_count = result['count']

        # Закрываем соединение
        cursor.close()
        connection.close()

        # Сохраняем текущее время как время последней проверки
        from datetime import datetime
        now = datetime.now()
        settings.setValue("last_check", now.strftime("%Y-%m-%d %H:%M:%S"))

        # Обновляем счетчики в главном окне
        main_window.new_reviews_count = new_reviews_count
        main_window.new_contacts_count = new_contacts_count

        # Показываем уведомление, если есть новые элементы
        total_new = new_reviews_count + new_contacts_count
        if total_new > 0:
            # Обновляем текст кнопки
            update_reviews_button_text(main_window, new_reviews_count, new_contacts_count)

            # Показываем уведомление
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(
                    f"Получено {new_reviews_count} новых отзывов и {new_contacts_count} новых контактов",
                    5000  # Показываем на 5 секунд
                )

    except Exception as e:
        print(f"Ошибка при проверке новых элементов: {e}")


def update_reviews_button_text(main_window, reviews_count=0, contacts_count=0):
    """
    Обновляет текст кнопки управления отзывами с индикатором новых элементов

    Args:
        main_window: Экземпляр главного окна приложения
        reviews_count: Количество новых отзывов
        contacts_count: Количество новых контактов
    """
    try:
        # Находим кнопку в тулбаре
        if hasattr(main_window, 'toolbar'):
            for i in range(main_window.toolbar.layout().count()):
                widget = main_window.toolbar.layout().itemAt(i).widget()
                if isinstance(widget, QPushButton) and "Управление отзывами" in widget.text():
                    # Формируем новый текст кнопки
                    button_text = "🌟 Управление отзывами"

                    # Добавляем индикатор, если есть новые элементы
                    total_new = reviews_count + contacts_count
                    if total_new > 0:
                        button_text = f"🌟 Управление отзывами 🔔({total_new})"

                    # Обновляем текст кнопки
                    widget.setText(button_text)

                    # Обновляем подсказку
                    tooltip = "Управление отзывами и контактными формами"
                    if reviews_count > 0 or contacts_count > 0:
                        tooltip += f"\n\nНовые элементы: {total_new}"
                        if reviews_count > 0:
                            tooltip += f"\n- Отзывы: {reviews_count}"
                        if contacts_count > 0:
                            tooltip += f"\n- Контакты: {contacts_count}"

                    widget.setToolTip(tooltip)
                    break

    except Exception as e:
        print(f"Ошибка при обновлении текста кнопки: {e}")


# Дополнительные функции для интеграции

def initialize_reviews_module(main_window):
    """
    Инициализирует модуль управления отзывами

    Args:
        main_window: Экземпляр главного окна приложения
    """
    try:
        print("Начинаем инициализацию модуля управления отзывами в initialize_reviews_module")
        # Проверяем, есть ли у главного окна атрибут toolbar
        if not hasattr(main_window, 'toolbar'):
            print("Предупреждение: атрибут 'toolbar' не найден в главном окне")
            return False

        # Добавляем кнопку в главное окно
        add_reviews_button(main_window)

        # Запускаем первую проверку новых элементов с задержкой
        QTimer.singleShot(5000, lambda: check_new_items(main_window))

        print("Модуль управления отзывами успешно инициализирован")
        return True

    except Exception as e:
        print(f"Ошибка при инициализации модуля управления отзывами: {e}")
        import traceback
        traceback.print_exc()
        return False