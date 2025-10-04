"""
Файл инициализации модуля управления отзывами и контактами
"""

# Глобальные переменные модуля
__version__ = "1.0.0"
__author__ = "MPSP Team"

def init_reviews_module(main_window):
    """
    Инициализация модуля управления отзывами в основном приложении

    Args:
        main_window: Экземпляр главного окна приложения
    """
    try:
        # Импортируем функцию инициализации здесь, чтобы избежать циклических импортов
        from .reviews_integration import initialize_reviews_module

        # Инициализируем модуль
        return initialize_reviews_module(main_window)
    except Exception as e:
        print(f"Ошибка в init_reviews_module: {e}")
        import traceback
        traceback.print_exc()
        return False

# При импорте пакета выводим информационное сообщение
print(f"Модуль управления отзывами версии {__version__} загружен")