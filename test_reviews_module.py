"""
Тестовый скрипт для проверки модуля отзывов
"""

def test_db_connection():
    """Тестирование подключения к базе данных отзывов"""
    try:
        # Проверяем наличие файла config.py
        import os
        root_config = os.path.exists('config.py')
        module_config = os.path.exists('reviews_manager/config.py')

        print(f"Файл config.py в корне проекта: {'Найден' if root_config else 'Не найден'}")
        print(f"Файл config.py в папке reviews_manager: {'Найден' if module_config else 'Не найден'}")

        # Пробуем импортировать конфигурацию
        try:
            from config import DB_CONFIG
            print("Импорт DB_CONFIG из корня проекта успешен")
        except ImportError:
            print("Не удалось импортировать DB_CONFIG из корня проекта")

            try:
                from reviews_manager.config import DB_CONFIG
                print("Импорт DB_CONFIG из reviews_manager успешен")
            except ImportError:
                print("Не удалось импортировать DB_CONFIG из reviews_manager")

        # Проверяем подключение
        from reviews_manager.db_check import check_db_connection

        print("\nНачинаем проверку подключения к БД отзывов...")
        result = check_db_connection()

        if result:
            print("Подключение к БД успешно!")
        else:
            print("Не удалось подключиться к БД.")

    except Exception as e:
        print(f"Ошибка при проверке подключения: {e}")
        import traceback
        traceback.print_exc()

def test_imports():
    """Тестирование импортов модуля отзывов"""
    try:
        print("Проверка импорта init_reviews_module...")
        from reviews_manager import init_reviews_module
        print("Успешно импортирован init_reviews_module")

        print("Проверка импорта ReviewsManagerApp...")
        from reviews_manager.reviews_manager_app import ReviewsManagerApp
        print("Успешно импортирован ReviewsManagerApp")

    except Exception as e:
        print(f"Ошибка при импорте модулей: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Тестирование модуля управления отзывами ===")
    test_imports()
    print("\n")
    test_db_connection()
    print("=== Тестирование завершено ===")