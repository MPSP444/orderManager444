import time
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt

class PerformanceManager:
    """Менеджер для отслеживания производительности"""
    def __init__(self):
        self._measurements = {}
        self._start_times = {}

    def startMeasurement(self, name):
        """Начало измерения времени операции"""
        import time
        self._start_times[name] = time.time()

    def endMeasurement(self, name):
        """Окончание измерения времени операции"""
        import time
        if name in self._start_times:
            duration = time.time() - self._start_times[name]
            self._measurements[name] = duration
            del self._start_times[name]
            return duration * 1000  # Возвращаем в миллисекундах
        return 0

    def getMeasurement(self, name):
        """Получение результата измерения"""
        return self._measurements.get(name, 0)

    def clearMeasurements(self):
        """Очистка всех измерений"""
        self._measurements.clear()
        self._start_times.clear()
class ResourceManager:
    """Менеджер ресурсов для кэширования и управления памятью"""

    def __init__(self):
        self._cache = {}
        self._cache_size = 0
        self._max_cache_size = 50 * 1024 * 1024  # 50 MB по умолчанию
        self._cache_timeout = 300  # 5 минут

    def setMaxCacheSize(self, size_mb):
        """Установка максимального размера кэша в мегабайтах"""
        self._max_cache_size = size_mb * 1024 * 1024
        self._cleanCache()  # Очищаем кэш если превышен новый размер
    def addToCache(self, key: str, data: Any, size: Optional[int] = None):
        """Добавление данных в кэш"""
        if size is None:
            size = self._estimateSize(data)

        if self._cache_size + size > self._max_cache_size:
            self._cleanCache()

        if size <= self._max_cache_size:
            self._cache[key] = {
                'data': data,
                'size': size,
                'timestamp': time.time()
            }
            self._cache_size += size
            return True
        return False

    def getFromCache(self, key: str):
        """Получение данных из кэша"""
        if key in self._cache:
            item = self._cache[key]
            if time.time() - item['timestamp'] < self._cache_timeout:
                item['timestamp'] = time.time()  # Обновляем время последнего доступа
                return item['data']
            else:
                self.removeFromCache(key)
        return None

    def removeFromCache(self, key: str):
        """Удаление данных из кэша"""
        if key in self._cache:
            self._cache_size -= self._cache[key]['size']
            del self._cache[key]

    def clearCache(self):
        """Полная очистка кэша"""
        self._cache.clear()
        self._cache_size = 0

    def _cleanCache(self):
        """Очистка устаревших данных"""
        current_time = time.time()
        keys_to_remove = [
            key for key, item in self._cache.items()
            if current_time - item['timestamp'] > self._cache_timeout
        ]
        for key in keys_to_remove:
            self.removeFromCache(key)

    def _estimateSize(self, data: Any) -> int:
        """Оценка размера данных"""
        import sys
        try:
            return sys.getsizeof(data)
        except:
            return 1024  # 1KB по умолчанию

    def getCacheTimeout(self):
        """Получение времени жизни кэша"""
        return self._cache_timeout

    def setCacheTimeout(self, timeout: int):
        """Установка времени жизни кэша"""
        self._cache_timeout = timeout

class UIManager:
    """Менеджер для управления обновлениями UI"""
    def __init__(self):
        self._update_queue = []

    def scheduleUpdate(self, widget, update_type, data):
        """Планирование обновления UI"""
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._performUpdate(widget, update_type, data))

    def _performUpdate(self, widget, update_type, data):
        """Выполнение обновления UI"""
        try:
            if hasattr(widget, f'handle_{update_type}'):
                getattr(widget, f'handle_{update_type}')(data)
        except Exception as e:
            print(f"Ошибка при обновлении UI: {e}")

class OptimizationManager:
    def __init__(self):
        self._cache = {}
        self._cache_size = 0
        self._max_cache_size = 50 * 1024 * 1024
        self._virtualization_managers = {}
        self._enabled = True
        self._last_cleanup = time.time()
        self._cleanup_interval = 300
        self.performance = PerformanceManager()
        self.resources = ResourceManager()
        self.ui = UIManager()  # Добавляем UI менеджер

    def _estimate_card_size(self, data):
        """Оценка размера данных карточки"""
        import sys
        try:
            # Базовый размер для структуры карточки
            base_size = 1024  # 1KB базовый размер

            # Если это список карточек
            if isinstance(data, list):
                total_size = base_size
                for card_data in data:
                    total_size += self._estimate_single_card_size(card_data)
                return total_size
            else:
                return self._estimate_single_card_size(data)

        except Exception as e:
            print(f"Ошибка при оценке размера карточки: {e}")
            return base_size

    def _estimate_single_card_size(self, card_data):
        """Оценка размера данных одной карточки"""
        import sys
        try:
            size = 0
            # Учитываем размер каждого поля
            for key, value in card_data.items():
                size += sys.getsizeof(str(key))
                size += sys.getsizeof(str(value))
            return size
        except:
            return 1024  # 1KB по умолчанию
    def cleanup(self):
        """Очистка ресурсов"""
        self.resources.clearCache()
        self._virtualization_managers.clear()
    def setup_kanban_optimization(self, board):
        """Настройка оптимизации для канбан-доски"""
        # Настройка кэширования
        self.setMaxCacheSize(50)  # 50MB для кэша

        # Настройка виртуализации для колонок
        for column in [board.novye_column, board.v_rabote_column,
                       board.ozhidayut_oplaty_column, board.vypolneny_column,
                       board.otmeneny_column]:
            if column:
                scroll_area = column.findChild(QScrollArea)
                if scroll_area:
                    self.setup_column_optimization(column, scroll_area)

    def setup_column_optimization(self, column, scroll_area):
        """Настройка оптимизации для колонки"""
        # Настройка прокрутки
        if hasattr(scroll_area.verticalScrollBar(), 'setSingleStep'):
            scroll_area.verticalScrollBar().setSingleStep(10)  # Устанавливаем плавность прокрутки
        if hasattr(scroll_area.horizontalScrollBar(), 'setSingleStep'):
            scroll_area.horizontalScrollBar().setSingleStep(10)

        # Оптимизация отрисовки
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Добавляем виртуализацию для колонки
        self._virtualization_managers[id(column)] = ScrollVirtualization(scroll_area)
    def setMaxCacheSize(self, size_mb: int):
        """Установка максимального размера кэша"""
        self._max_cache_size = size_mb * 1024 * 1024
        self._cleanup_cache()

    def addToCache(self, key: str, data: Any, size: Optional[int] = None):
        """Добавление данных в кэш"""
        if not self._enabled:
            return False

        try:
            # Вычисляем размер данных, если не указан
            if size is None:
                size = self._estimateSize(data)

            # Проверяем, поместятся ли данные в кэш
            if size > self._max_cache_size:
                return False

            # Освобождаем место, если необходимо
            if self._cache_size + size > self._max_cache_size:
                if not self._reduceCache(size):
                    return False

            # Добавляем данные в кэш
            self._cache[key] = {
                'data': data,
                'size': size,
                'timestamp': time.time(),
                'access_count': 0
            }
            self._cache_size += size
            return True

        except Exception as e:
            print(f"Ошибка при добавлении в кэш: {e}")
            return False

    def getFromCache(self, key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        if not self._enabled or key not in self._cache:
            return None

        # Обновляем статистику использования
        self._cache[key]['access_count'] += 1
        self._cache[key]['timestamp'] = time.time()

        return self._cache[key]['data']

    def removeFromCache(self, key: str):
        """Удаление данных из кэша"""
        if key in self._cache:
            self._cache_size -= self._cache[key]['size']
            del self._cache[key]

    def _cleanup_cache(self):
        """Очистка устаревших данных из кэша"""
        current_time = time.time()

        # Проверяем необходимость очистки
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        self._last_cleanup = current_time

        # Удаляем устаревшие записи
        keys_to_remove = []
        for key, data in self._cache.items():
            if current_time - data['timestamp'] > self._cleanup_interval:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            self.removeFromCache(key)

    def _reduceCache(self, needed_size: int) -> bool:
        """Освобождение места в кэше"""
        if needed_size > self._max_cache_size:
            return False

        # Сортируем записи по времени последнего доступа и количеству обращений
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: (x[1]['timestamp'], x[1]['access_count'])
        )

        # Удаляем записи, пока не освободится достаточно места
        freed_space = 0
        for key, data in sorted_entries:
            if self._cache_size - freed_space + needed_size <= self._max_cache_size:
                break
            freed_space += data['size']
            self.removeFromCache(key)

        return True

    def _estimateSize(self, data: Any) -> int:
        """Оценка размера данных"""
        import sys
        try:
            return sys.getsizeof(data)
        except:
            return 1024  # 1KB по умолчанию


class ScrollVirtualization:
    """Класс для управления виртуализацией прокрутки"""

    def __init__(self, scroll_area: QScrollArea):
        self.scroll_area = scroll_area
        self.card_height = 215  # Стандартная высота карточки
        self.visible_cards = set()
        self.all_cards = []

    def setCardHeight(self, height: int):
        """Установка высоты карточки"""
        self.card_height = height
        self.updateVisibleCards()

    def updateVisibleCards(self):
        """Обновление списка видимых карточек"""
        if not self.scroll_area or not self.scroll_area.widget():
            return

        viewport = self.scroll_area.viewport()
        scroll_pos = self.scroll_area.verticalScrollBar().value()
        viewport_height = viewport.height()

        # Определяем видимую область
        visible_top = scroll_pos
        visible_bottom = scroll_pos + viewport_height

        # Обновляем видимость карточек
        new_visible = set()
        for card in self.all_cards:
            card_pos = card.pos().y()
            card_visible = (card_pos + self.card_height > visible_top and
                            card_pos < visible_bottom)

            if card_visible:
                new_visible.add(card)
                if card not in self.visible_cards:
                    card.show()
            else:
                card.hide()

        self.visible_cards = new_visible

    def addCard(self, card):
        """Добавление карточки в список"""
        self.all_cards.append(card)
        self.updateVisibleCards()

    def removeCard(self, card):
        """Удаление карточки из списка"""
        if card in self.all_cards:
            self.all_cards.remove(card)
        if card in self.visible_cards:
            self.visible_cards.remove(card)

    def clear(self):
        """Очистка всех списков"""
        self.all_cards.clear()
        self.visible_cards.clear()