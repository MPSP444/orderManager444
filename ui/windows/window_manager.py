# ui/windows/window_manager.py
from PyQt5.QtWidgets import QDialog
from .new_order_window import NewOrderWindow


class OrderWindowManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = OrderWindowManager()
        return cls._instance

    def __init__(self):
        self._windows = {}  # Словарь для хранения окон

    def show_order_window(self, parent, order=None, existing_order_data=None):
        """Показ окна заказа"""
        # Создаем уникальный ключ для окна
        window_key = id(parent)

        # Проверяем, существует ли уже окно для этого родителя
        if window_key in self._windows and self._windows[window_key].isVisible():
            self._windows[window_key].raise_()
            self._windows[window_key].activateWindow()
            return

        # Создаем новое окно
        window = NewOrderWindow(parent, order)
        window.setMinimumWidth(900)
        window.setMinimumHeight(800)

        # Центрируем окно
        parent_geometry = parent.window().frameGeometry()
        x = int(parent_geometry.center().x() - 450)
        y = int(parent_geometry.center().y() - 400)
        window.move(x, y)

        # Заполняем данные если нужно
        if existing_order_data:
            window.fill_fields(existing_order_data)

        # Сохраняем окно в словаре
        self._windows[window_key] = window

        # Подключаем обработчик закрытия
        window.finished.connect(lambda: self._cleanup_window(window_key))

        # Показываем окно модально
        return window.exec_()

    def _cleanup_window(self, window_key):
        """Очистка окна при закрытии"""
        if window_key in self._windows:
            self._windows[window_key].deleteLater()
            del self._windows[window_key]

    def cleanup_all(self):
        """Очистка всех окон"""
        for window in self._windows.values():
            window.close()
            window.deleteLater()
        self._windows.clear()