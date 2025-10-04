# ui/windows/state_manager.py

from typing import List, Callable
from PyQt5.QtCore import QObject, pyqtSignal


class StateManager(QObject):
    state_changed = pyqtSignal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Инициализация менеджера состояний"""
        super().__init__()
        self.observers: List[Callable] = []

    def add_observer(self, observer: Callable):
        """Добавление наблюдателя"""
        if observer not in self.observers:
            self.observers.append(observer)

    def remove_observer(self, observer: Callable):
        """Удаление наблюдателя"""
        if observer in self.observers:
            self.observers.remove(observer)

    def notify_all(self):
        """Уведомление всех наблюдателей"""
        self.state_changed.emit()
        for observer in self.observers:
            if hasattr(observer, 'update_data'):
                try:
                    observer.update_data()
                except Exception as e:
                    print(f"Ошибка при обновлении {observer}: {e}")