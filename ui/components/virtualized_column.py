from datetime import datetime, timedelta, date

from PyQt5.QtWidgets import (QListView, QStyledItemDelegate, QVBoxLayout,
                             QWidget, QLabel, QFrame, QHBoxLayout, QDialog, QSizePolicy, QComboBox)
from PyQt5.QtCore import (QAbstractListModel, Qt, QSize, QModelIndex,
                          pyqtSignal, QPoint, QMimeData, QTimer)
from PyQt5.QtGui import QDrag, QPainter, QRegion, QPixmap, QContextMenuEvent

from core import DatabaseManager, Order
from .order_card import OrderCard
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (QStyledItemDelegate, QApplication)
from PyQt5.QtCore import Qt, QSize, QEvent
from PyQt5.QtGui import QDrag, QPixmap

from PyQt5.QtCore import QAbstractListModel, Qt, QMimeData
from PyQt5.QtGui import QDrag
from PyQt5.QtCore import QEvent

from ui.message_utils import show_error, show_warning
from ui.windows.payment_window import PaymentWindow
from PyQt5.QtWidgets import QToolTip
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QToolTip, QStyle, QStyleOptionViewItem
from PyQt5.QtCore import Qt, QEvent
from ui.message_utils import show_error
import os
import subprocess
from PyQt5.QtCore import QSettings


class OrdersModel(QAbstractListModel):
    def __init__(self, orders=None):
        super().__init__()
        self._orders = orders or []

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role == Qt.UserRole and 0 <= index.row() < len(self._orders):
            return self._orders[index.row()]

        return None

    def rowCount(self, index):
        return len(self._orders)

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        return default_flags | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction

    def canDropMimeData(self, data, action, row, column, parent):
        if not data.hasText():
            return False
        try:
            # Проверяем, что текст можно преобразовать в id заказа
            int(data.text())
            return True
        except ValueError:
            return False

    def dropMimeData(self, data, action, row, column, parent):
        if not self.canDropMimeData(data, action, row, column, parent):
            return False

        if action == Qt.IgnoreAction:
            return True

        return True  # Фактическая обработка происходит в колонке

    def supportedDragActions(self):
        return Qt.MoveAction

    def mimeTypes(self):
        return ['text/plain']

    def mimeData(self, indexes):
        if not indexes:
            return None

        mime_data = QMimeData()
        if len(indexes) > 0:
            index = indexes[0]
            if index.isValid() and index.row() < len(self._orders):
                order_data = self._orders[index.row()]
                mime_data.setText(str(order_data['id']))
        return mime_data

    def setOrders(self, orders):
        """Обновление списка заказов"""
        self.beginResetModel()
        self._orders = orders
        self.endResetModel()

    def getOrder(self, row):
        """Получение заказа по индексу"""
        if 0 <= row < len(self._orders):
            return self._orders[row]
        return None

    def removeOrder(self, row):
        """Удаление заказа по индексу"""
        if 0 <= row < len(self._orders):
            self.beginRemoveRows(self.createIndex(0, 0), row, row)
            del self._orders[row]
            self.endRemoveRows()
            return True
        return False

    def addOrder(self, order):
        """Добавление нового заказа"""
        self.beginInsertRows(self.createIndex(0, 0), len(self._orders), len(self._orders))
        self._orders.append(order)
        self.endInsertRows()

    def clear(self):
        """Очистка модели"""
        self.beginResetModel()
        self._orders = []
        self.endResetModel()

    def updateOrder(self, order_id, new_data):
        """Обновление данных заказа"""
        for i, order in enumerate(self._orders):
            if order['id'] == order_id:
                self._orders[i].update(new_data)
                self.dataChanged.emit(
                    self.index(i, 0),
                    self.index(i, 0),
                    [Qt.UserRole]
                )
                return True
        return False


class OrderCardDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.card_size = QSize(315, 225)
        self.margin = QSize(8, 8)
        self.drag_start_position = None
        self.current_tooltip_index = None

    def createEditor(self, parent, option, index):
        return None  # Отключаем редактирование

    def helpEvent(self, event, view, option, index):
        """Обработка события для отображения подсказки"""
        if not event or not view or not index.isValid():
            return False

        # Получаем данные заказа
        order_data = index.data(Qt.UserRole)
        if not order_data:
            try:
                with DatabaseManager().session_scope() as session:
                    order_id = index.data(Qt.DisplayRole)
                    if order_id:
                        order = session.query(Order).get(order_id)
                        if order:
                            order_data = order.to_dict()
            except Exception as e:
                print(f"Ошибка при получении данных заказа: {e}")
                return False

        if not order_data:
            return False

        # Проверяем, находится ли мышь над элементом
        if not option.rect.contains(event.pos()):
            return False

        # Форматируем даты
        created_date = order_data.get('created_date')
        payment_date = order_data.get('payment_date')
        discount_start = order_data.get('discount_start_date')
        discount_end = order_data.get('discount_end_date')

        # Проверяем и форматируем даты
        try:
            # Форматирование даты создания
            if isinstance(created_date, str):
                created_date_str = created_date
            elif created_date:
                if isinstance(created_date, datetime):
                    created_date_str = created_date.strftime("%d.%m.%Y %H:%M")
                else:
                    created_date_str = str(created_date)
            else:
                created_date_str = "Не указана"

            # Форматирование даты оплаты
            if isinstance(payment_date, str):
                payment_date_str = payment_date
            elif payment_date:
                if isinstance(payment_date, datetime):
                    payment_date_str = payment_date.strftime("%d.%m.%Y %H:%M")
                else:
                    payment_date_str = str(payment_date)
            else:
                payment_date_str = "Не указана"

            # Форматирование дат скидки
            if discount_start:
                if isinstance(discount_start, str):
                    discount_start_str = discount_start
                elif isinstance(discount_start, datetime):
                    discount_start_str = discount_start.strftime("%d.%m.%Y %H:%M")
                else:
                    discount_start_str = str(discount_start)
            else:
                discount_start_str = "Не указана"

            if discount_end:
                if isinstance(discount_end, str):
                    discount_end_str = discount_end
                elif isinstance(discount_end, datetime):
                    discount_end_str = discount_end.strftime("%d.%m.%Y %H:%M")
                else:
                    discount_end_str = str(discount_end)
            else:
                discount_end_str = "Не указана"

        except Exception as e:
            print(f"Ошибка при форматировании дат: {e}")
            created_date_str = str(created_date) if created_date else "Не указана"
            payment_date_str = str(payment_date) if payment_date else "Не указана"
            discount_start_str = str(discount_start) if discount_start else "Не указана"
            discount_end_str = str(discount_end) if discount_end else "Не указана"

        # Формируем HTML для подсказки
        tooltip_text = f"""
        <div style='background-color: white; 
                    padding: 10px; 
                    border: 1px solid #ccc; 
                    border-radius: 4px;
                    min-width: 200px;
                    font-family: "Segoe UI", Arial, sans-serif;'>
            <p style='margin: 4px 0;'><b>📋 Номер заказа:</b> #{order_data.get('id', 'Н/Д')}</p>
            <p style='margin: 4px 0;'><b>👤 ФИО:</b> {order_data.get('fio', 'Не указано')}</p>
            <p style='margin: 4px 0;'><b>👥 Группа:</b> {order_data.get('group', 'Не указана')}</p>
            <p style='margin: 4px 0;'><b>🔑 Логин:</b> {order_data.get('login', 'Не указан')}</p>
            <p style='margin: 4px 0;'><b>🌐 Сайт:</b> {order_data.get('website', 'Не указан')}</p>
            <p style='margin: 4px 0;'><b>📝 Тема:</b> {order_data.get('theme', 'Не указана')}</p>
            <p style='margin: 4px 0;'><b>💬 Комментарии:</b> {order_data.get('comment', 'Нет комментариев')}</p>
            <p style='margin: 4px 0;'><b>📞 Телефон:</b> {order_data.get('phone', 'Не указан')}</p>
            <p style='margin: 4px 0;'><b>👨‍🏫 Преподаватель:</b> {order_data.get('teacher_name', 'Не указан')}</p>
            <p style='margin: 4px 0;'><b>📧 Email преподавателя:</b> {order_data.get('teacher_email', 'Не указан')}</p>
            <p style='margin: 4px 0;'><b>📅 Дата создания:</b> {created_date_str}</p>
            <p style='margin: 4px 0;'><b>💰 Дата оплаты:</b> {payment_date_str}</p>
            <p style='margin: 4px 0;'><b>⏰ Начало скидки:</b> {discount_start_str}</p>
            <p style='margin: 4px 0;'><b>⌛ Окончание скидки:</b> {discount_end_str}</p>
        </div>
        """

        # Показываем подсказку
        QToolTip.showText(event.globalPos(), tooltip_text, view, option.rect)
        return True
    def paint(self, painter, option, index):
        order_data = index.data(Qt.UserRole)
        if not order_data:
            return

        painter.save()

        # Отрисовка карточки
        card = OrderCard(order_data)
        card.resize(self.card_size)

        # Смещение для отрисовки
        painter.translate(option.rect.topLeft())

        # Отрисовка с учетом региона
        region = QRegion(0, 0, self.card_size.width(), self.card_size.height())
        card.render(painter, sourceRegion=region)

        painter.restore()

    def sizeHint(self, option, index):
        return self.card_size + self.margin

    def editorEvent(self, event, model, option, index):
        """Обработка всех событий взаимодействия"""
        # Получаем данные заказа
        order_data = model.data(index, Qt.UserRole)
        if not order_data:
            return False

        # Обработка правого клика - контекстное меню
        if (event.type() == QEvent.MouseButtonPress and
                event.button() == Qt.RightButton):
            # Создаем временную карточку для показа меню
            temp_card = OrderCard(order_data, parent=self.parent())
            # Преобразуем координаты события
            context_event = QContextMenuEvent(
                QContextMenuEvent.Mouse,
                event.pos(),
                event.globalPos()
            )
            # Показываем контекстное меню
            temp_card.contextMenuEvent(context_event)
            return True

        # Обработка начала перетаскивания
        elif (event.type() == QEvent.MouseButtonPress and
              event.button() == Qt.LeftButton):
            self.drag_start_position = event.pos()
            return True

        # Обработка перетаскивания
        elif (event.type() == QEvent.MouseMove and
              event.buttons() & Qt.LeftButton and
              self.drag_start_position is not None):
            # Проверяем минимальное расстояние для начала перетаскивания
            distance = (event.pos() - self.drag_start_position).manhattanLength()
            if distance >= QApplication.startDragDistance():
                drag = QDrag(self.parent())
                mime_data = QMimeData()
                mime_data.setText(str(order_data['id']))
                drag.setMimeData(mime_data)

                # Создаем превью для перетаскивания
                pixmap = self.create_drag_preview(order_data)
                drag.setPixmap(pixmap)
                drag.setHotSpot(event.pos() - option.rect.topLeft())

                # Запускаем операцию перетаскивания
                drag.exec_(Qt.MoveAction)
                self.drag_start_position = None
                return True

        # Обработка двойного клика с Control
        elif (event.type() == QEvent.MouseButtonDblClick and
              event.button() == Qt.LeftButton and
              event.modifiers() & Qt.ControlModifier):
            try:
                self.open_client_folder(order_data['fio'])
                return True
            except Exception as e:
                show_error(self.parent(), "Ошибка", f"Ошибка при открытии папки: {str(e)}")
                return False

        return super().editorEvent(event, model, option, index)

    def create_drag_preview(self, order_data):
        """Создание превью для перетаскивания"""
        # Создаем временную карточку
        temp_card = OrderCard(order_data)
        temp_card.resize(self.card_size)

        # Создаем изображение карточки
        pixmap = QPixmap(self.card_size)
        pixmap.fill(Qt.transparent)

        # Рисуем карточку на изображении с эффектом прозрачности
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)
        temp_card.render(painter)
        painter.end()

        return pixmap

    def open_client_folder(self, client_fio):
        """Открытие папки клиента"""
        import os
        import subprocess

        try:
            # Создаём путь к папке клиента
            base_path = os.path.expanduser('D:\\Users\\mgurbanmuradov\\Documents\\Общая')
            client_folder = os.path.join(base_path, client_fio)

            # Создаём папку, если она не существует
            os.makedirs(client_folder, exist_ok=True)

            # Открываем папку
            if os.name == 'nt':  # Windows
                os.startfile(client_folder)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', client_folder])

        except Exception as e:
            raise Exception(f"Не удалось открыть папку клиента: {str(e)}")

    def createDragPixmap(self, order_data):
        """Создание превью для перетаскивания"""
        temp_card = OrderCard(order_data)
        temp_card.resize(self.card_size)

        pixmap = QPixmap(self.card_size)
        pixmap.fill(Qt.transparent)

        # Добавляем эффект прозрачности для превью
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)
        temp_card.render(painter)
        painter.end()

        return pixmap


class VirtualizedKanbanColumn(QFrame):
    status_changed = pyqtSignal(int, str, str)
    COLUMN_WIDTH = 340

    SORT_OPTIONS = [
        ("По умолчанию", None),
        ("По скидке ↑", "discount_asc"),
        ("По скидке ↓", "discount_desc"),
        ("По дате создания ↑", "date_asc"),
        ("По дате создания ↓", "date_desc"),
        ("По сумме ↑", "amount_asc"),
        ("По сумме ↓", "amount_desc"),
        ("По сроку ↑", "deadline_asc"),
        ("По сроку ↓", "deadline_desc"),
        ("По услуге А-Я", "service_asc"),
        ("По услуге Я-А", "service_desc"),
        ("По группе А-Я", "group_asc"),
        ("По группе Я-А", "group_desc"),
        ("По остатку ↑", "remaining_asc"),
        ("По остатку ↓", "remaining_desc"),
        ("По дате оплаты ↑", "payment_date_asc"),
        ("По дате оплаты ↓", "payment_date_desc"),
    ]
    COLUMN_STYLES = {
        'Новый': {
            'bg': '#FFFFFF',
            'header_bg': '#E3F2FD',
            'border': '#2196F3',
            'count_bg': '#1976D2',
            'title_color': '#1565C0'
        },
        'В работе': {
            'bg': '#FFFFFF',
            'header_bg': '#FFF3E0',
            'border': '#FF9800',
            'count_bg': '#F57C00',
            'title_color': '#E65100'
        },
        'Переделка': {
            'bg': '#FFFFFF',
            'header_bg': '#F3E5F5',
            'border': '#9C27B0',
            'count_bg': '#7B1FA2',
            'title_color': '#6A1B9A'
        },
        'В ожидании оплаты': {
            'bg': '#FFFFFF',
            'header_bg': '#FFEBEE',
            'border': '#F44336',
            'count_bg': '#D32F2F',
            'title_color': '#C62828'
        },
        'Выполнен': {
            'bg': '#FFFFFF',
            'header_bg': '#E8F5E9',
            'border': '#4CAF50',
            'count_bg': '#388E3C',
            'title_color': '#2E7D32'
        },
        'Отказ': {
            'bg': '#FFFFFF',
            'header_bg': '#ECEFF1',
            'border': '#B0BEC5',
            'count_bg': '#78909C',
            'title_color': '#546E7A'
        }
    }

    # Стили для разных периодов ожидания оплаты
    WAITING_PERIOD_STYLES = {
        'normal': {  # до 30 дней
            'bg': '#FFEBEE',
            'border': '#F44336',
            'text': '#C62828'
        },
        'medium': {  # 30-180 дней
            'bg': '#FFE0B2',
            'border': '#FF7043',
            'text': '#D84315'
        },
        'long': {  # более 180 дней
            'bg': '#FFCDD2',
            'border': '#E53935',
            'text': '#B71C1C'
        }
    }
    def __init__(self, title, status, parent=None):
        super().__init__(parent)
        self.title = title
        self.status = status
        self.db_manager = DatabaseManager()
        self.settings = QSettings('MPSP', 'KanbanApp')
        # Загружаем сохраненную сортировку для данного статуса
        self.current_sort = self.settings.value(f'sort_order_{self.status}', None)

        self.setAcceptDrops(True)  # Включаем прием перетаскивания для всей колонки

        # Определяем базовые стили для всех статусов
        self.base_style = {
            'bg': '#FFFFFF',
            'header_bg': '#FAFAFA',
            'border': '#CCCCCC',
            'count_bg': '#999999',
            'title_color': '#2A2A2A',
            'title_font': '"Georgia", serif',
            'title_size': '18px',
            'title_weight': '600',
            'amount_bg': '#F8F8F8'
        }

        # Объединяем с специфичными стилями для статуса
        status_styles = {
            'Новый': {
                'border': '#90CAF9',
                'count_bg': '#1976D2',
                'header_bg': '#E3F2FD'
            },
            'В работе': {
                'border': '#FFB74D',
                'count_bg': '#F57C00',
                'header_bg': '#FFF8E1'
            },
            'В ожидании оплаты': {
                'border': '#EF9A9A',
                'count_bg': '#D32F2F',
                'header_bg': '#FFEBEE'
            },
            'Выполнен': {
                'border': '#A5D6A7',
                'count_bg': '#388E3C',
                'header_bg': '#E8F5E9'
            },
            'Отказ': {
                'border': '#B0BEC5',
                'count_bg': '#616161',
                'header_bg': '#ECEFF1'
            }
        }

        # Обновляем базовый стиль специфичными значениями для текущего статуса
        if status in status_styles:
            self.base_style.update(status_styles[status])

        self.setup_ui()

        # Настраиваем ListView
        self.list_view.setAcceptDrops(False)  # Отключаем прием перетаскивания для ListView
        self.list_view.viewport().setAcceptDrops(False)
        self.list_view.setDropIndicatorShown(False)
        self.list_view.setDragEnabled(True)  # Оставляем возможность начать перетаскивание

    def dragEnterEvent(self, event):
        """Обработка входа при перетаскивании"""
        if event.mimeData().hasText():
            try:
                order_id = int(event.mimeData().text())
                with self.db_manager.session_scope() as session:
                    order = session.query(Order).get(order_id)
                    if order and order.status != self.status:
                        self.setStyleSheet(f"""
                            QFrame {{
                                background-color: {self.base_style['header_bg']};
                                border: 2px dashed {self.base_style['border']};
                                border-radius: 8px;
                                margin: 0px;
                                min-width: {self.COLUMN_WIDTH}px;
                                max-width: {self.COLUMN_WIDTH}px;
                                padding: 0px;
                            }}

                            QWidget#header {{
                                background-color: #F9FAFB;
                                border: none;
                                border-top-left-radius: 14px;
                                border-top-right-radius: 14px;
                                padding: 5px;
                                min-width: {self.COLUMN_WIDTH - 8}px;
                                max-width: {self.COLUMN_WIDTH - 8}px;
                            }}

                            QLabel#title {{
                                color: #374151;
                                font-size: 16px;
                                font-family: "Segoe UI", "Arial", sans-serif;
                                font-weight: 600;
                                letter-spacing: 0.05em;
                                min-width: 200px;
                                max-width: 200px;
                            }}

                            QLabel#counter {{
                                background-color: {self.base_style['count_bg']};
                                color: white;
                                font-size: 14px;
                                font-weight: 500;
                                border-radius: 4px;
                                min-width: 40px;
                                max-width: 40px;
                                min-height: 20px;
                                max-height: 20px;
                                qproperty-alignment: AlignCenter;
                                margin: 2px;
                            }}

                            QLabel#amount {{
                                color: #6B7280;
                                font-size: 14px;
                                font-weight: 400;
                                margin-top: 2px;
                                padding-left: 2px;
                                min-width: {self.COLUMN_WIDTH - 40}px;
                                max-width: {self.COLUMN_WIDTH - 40}px;
                            }}

                            QLabel#underline {{
                                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 transparent,
                                            stop:0.4 transparent,
                                            stop:0.5 {self.base_style['border']},
                                            stop:0.6 transparent,
                                            stop:1 transparent);
                                min-height: 3px;
                                max-height: 3px;
                                min-width: {self.COLUMN_WIDTH - 40}px;
                                max-width: {self.COLUMN_WIDTH - 40}px;
                                margin-top: 1px;
                            }}
                        """)
                        event.accept()
                        return
            except (ValueError, Exception) as e:
                print(f"Ошибка при обработке dragEnter: {e}")
        event.ignore()

    def dragMoveEvent(self, event):
        """Разрешаем перемещение над всей колонкой"""
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Возвращаем обычный стиль при выходе из зоны"""
        # Восстанавливаем базовый стиль для колонки с фиксированными размерами
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.base_style['bg']};
                border: 2px solid {self.base_style['border']};
                border-radius: 8px;
                margin: 0px;
                min-width: {self.COLUMN_WIDTH}px;
                max-width: {self.COLUMN_WIDTH}px;
                padding: 0px;
            }}

            QWidget#header {{
                background-color: #F9FAFB;
                border: none;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                padding: 5px;
                min-width: {self.COLUMN_WIDTH - 8}px;
                max-width: {self.COLUMN_WIDTH - 8}px;
            }}

            QLabel#title {{
                color: #374151;
                font-size: 16px;
                font-family: "Segoe UI", "Arial", sans-serif;
                font-weight: 600;
                letter-spacing: 0.05em;
                min-width: 200px;
                max-width: 200px;
            }}

            QLabel#counter {{
                background-color: {self.base_style['count_bg']};
                color: white;
                font-size: 14px;
                font-weight: 500;
                border-radius: 4px;
                min-width: 40px;
                max-width: 40px;
                min-height: 20px;
                max-height: 20px;
                qproperty-alignment: AlignCenter;
                margin: 2px;
            }}

            QLabel#amount {{
                color: #6B7280;
                font-size: 14px;
                font-weight: 400;
                margin-top: 2px;
                padding-left: 2px;
                min-width: {self.COLUMN_WIDTH - 40}px;
                max-width: {self.COLUMN_WIDTH - 40}px;
            }}

            QLabel#underline {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 transparent,
                            stop:0.4 transparent,
                            stop:0.5 {self.base_style['border']},
                            stop:0.6 transparent,
                            stop:1 transparent);
                min-height: 3px;
                max-height: 3px;
                min-width: {self.COLUMN_WIDTH - 40}px;
                max-width: {self.COLUMN_WIDTH - 40}px;
                margin-top: 1px;
            }}
        """)

    def dropEvent(self, event):
        """Обработка сброса карточки"""
        try:
            order_id = int(event.mimeData().text())

            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    event.ignore()
                    return

                old_status = order.status

                # Если перетаскиваем в ту же колонку - игнорируем
                if old_status == self.status:
                    event.ignore()
                    return

                # Проверка для статуса "Выполнен"
                if self.status == 'Выполнен':
                    remaining = order.recalculate_remaining()
                    if remaining > 0:
                        payment_window = PaymentWindow(self, order)
                        result = payment_window.exec_()

                        if result != QDialog.Accepted:
                            event.ignore()
                            return

                        # Получаем свежую копию заказа после оплаты
                        order = session.query(Order).get(order_id)
                        if not order:
                            event.ignore()
                            return

                        remaining = order.recalculate_remaining()
                        if remaining > 0:
                            show_warning(self, "Предупреждение",
                                         "Невозможно изменить статус на 'Выполнен'. Остались неоплаченные суммы.")
                            event.ignore()
                            return

                # Меняем статус
                order.status = self.status
                session.commit()

                event.accept()
                self.status_changed.emit(order_id, self.status, old_status)

                # Обновляем отображение всех колонок
                parent = self.parent()
                while parent and not hasattr(parent, 'loadOrders'):
                    parent = parent.parent()
                if parent:
                    parent.loadOrders()

        except ValueError:
            event.ignore()
        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")
            event.ignore()
        finally:
            # Восстанавливаем стиль
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.base_style['bg']};
                    border: 2px solid {self.base_style['border']};
                    border-radius: 8px;
                    min-width: {self.COLUMN_WIDTH}px;
                    max-width: {self.COLUMN_WIDTH}px;
                }}
            """)

    def create_list_view(self):
        """Создание списка карточек с плавной прокруткой"""
        list_view = QListView()

        # Базовые настройки отображения
        list_view.setViewMode(QListView.ListMode)
        list_view.setSpacing(8)
        list_view.setUniformItemSizes(True)
        list_view.setSelectionMode(QListView.NoSelection)
        list_view.setContextMenuPolicy(Qt.CustomContextMenu)

        # Настройки перетаскивания
        list_view.setDragEnabled(True)
        list_view.setAcceptDrops(True)
        list_view.setDragDropMode(QListView.DragDrop)

        # Настройки отслеживания мыши
        list_view.setMouseTracking(True)
        list_view.viewport().setMouseTracking(True)
        list_view.setAttribute(Qt.WA_Hover, True)
        list_view.viewport().setAttribute(Qt.WA_Hover, True)
        list_view.setToolTipDuration(-1)

        # Настройки прокрутки
        list_view.setVerticalScrollMode(QListView.ScrollPerPixel)
        list_view.verticalScrollBar().setSingleStep(15)  # Минимальный шаг прокрутки
        list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        list_view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Настройка анимации прокрутки
        list_view.setProperty("scrollMode", "animated")
        list_view.setProperty("scrollStepFactor", 0.05)  # Плавность прокрутки

        # Настройка стилей
        list_view.setStyleSheet("""
            QListView {
                background-color: transparent;
                border: none;
                padding: 0px;
                outline: none;
            }

            QListView::item {
                background-color: transparent;
                padding: 0px;
                margin: 4px 0px;
            }

            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }

            QScrollBar::handle:vertical {
                background: #a0a0a0;
                min-height: 30px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background: #808080;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }

            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical {
                background: none;
            }
        """)

        # Настройка модели и делегата
        self.delegate = OrderCardDelegate(list_view)
        list_view.setItemDelegate(self.delegate)
        self.model = OrdersModel()
        list_view.setModel(self.model)

        # Доработка плавности прокрутки через настройку таймера
        list_view.scrollTimer = QTimer()
        list_view.scrollTimer.setInterval(16)  # ~60 FPS
        list_view.scrollTimer.timeout.connect(lambda: list_view.viewport().update())
        list_view.scrollTimer.start()

        return list_view

    def get_status_style(self, status):
        """Получение стилей для конкретного статуса"""
        status_styles = {
            'Новый': {
                'border': '#90CAF9',
                'count_bg': '#1976D2',
                'header_bg': '#FAFAFA'
            },
            'В работе': {
                'border': '#FFB74D',
                'count_bg': '#F57C00',
                'header_bg': '#FFF8E1'
            },
            'В ожидании оплаты': {
                'border': '#EF9A9A',
                'count_bg': '#D32F2F',
                'header_bg': '#FFEBEE'
            },
            'Выполнен': {
                'border': '#A5D6A7',
                'count_bg': '#388E3C',
                'header_bg': '#E8F5E9'
            },
            'Отказ': {
                'border': '#B0BEC5',
                'count_bg': '#616161',
                'header_bg': '#ECEFF1'
            }
        }
        return status_styles.get(status, {})

    def setup_ui(self):
        """Настройка интерфейса колонки"""
        # Применяем стиль колонки
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.base_style['bg']};
                border: 2px solid {self.base_style['border']};
                border-radius: 8px;
                margin: 0px;
                min-width: 340px;
                max-width: 340px;
                padding: 0px;
            }}
        """)

        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Создаем заголовок
        header = self.create_header()
        main_layout.addWidget(header)

        # Создаем список карточек
        self.list_view = self.create_list_view()
        main_layout.addWidget(self.list_view)

    def create_header(self):
        """Создание заголовка колонки с добавлением комбо-бокса"""
        header = QWidget()
        header.setObjectName("header")
        header.setFixedWidth(self.COLUMN_WIDTH - 8)

        # Определяем стили для разных статусов
        status_styles = {
            'В ожидании оплаты': {
                'bg': '#FFEBEE',  # Светло-розовый фон
                'border': '#EF9A9A',
                'count_bg': '#D32F2F'
            },
            'Новый': {
                'bg': '#E3F2FD',  # Светло-голубой фон
                'border': '#90CAF9',
                'count_bg': '#1976D2'
            },
            'В работе': {
                'bg': '#FFF8E1',  # Светло-оранжевый фон
                'border': '#FFB74D',
                'count_bg': '#F57C00'
            },
            'Выполнен': {
                'bg': '#E8F5E9',  # Светло-зеленый фон
                'border': '#A5D6A7',
                'count_bg': '#388E3C'
            },
            'Отказ': {
                'bg': '#ECEFF1',  # Светло-серый фон
                'border': '#B0BEC5',
                'count_bg': '#616161'
            }
        }

        # Получаем стили для текущего статуса
        current_style = status_styles.get(self.status, status_styles['Отказ'])
        bg_color = current_style['bg']
        status_color = current_style['count_bg']

        header.setStyleSheet(f"""
            QWidget#header {{
                background-color: {bg_color};
                border: none;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                padding: 5px;
                min-width: {self.COLUMN_WIDTH - 15}px;
                max-width: {self.COLUMN_WIDTH - 8}px;
            }}

            QLabel#title {{
                color: #374151;
                font-size: 17px;
                font-family: "Segoe UI", "Arial", sans-serif;
                font-weight: 650;
                border: none;
                letter-spacing: 0.05em;
                min-width: 220px;
                max-width: 220px;
                background: transparent;
            }}

            QLabel#counter {{
                background-color: {status_color};
                color: white;
                font-size: 16px;

                font-weight: 500;
                border-radius: 4px;
                min-width: 40px;
                max-width: 40px;
                min-height: 20px;
                max-height: 20px;
                qproperty-alignment: AlignCenter;
                margin: 2px;
            }}

            QComboBox {{
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 4px;
                padding: 2px 8px;
                min-width: 120px;
                max-width: 120px;
                font-size: 12px;
                color: #374151;
            }}

            QComboBox:hover {{
                border-color: {status_color};
            }}

            QLabel#amount {{
                color: #6B7280;
                font-size: 14px;
                border: none;
                font-weight: 400;
                margin-top: 2px;
                padding-left: 2px;
                min-width: {self.COLUMN_WIDTH - 40}px;
                max-width: {self.COLUMN_WIDTH - 40}px;
                background: transparent;
            }}

            QLabel#underline {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                            stop:0 transparent,
                            stop:0.4 transparent,
                            stop:0.5 {status_color},
                            stop:0.6 transparent,
                            stop:1 transparent);
                min-height: 3px;
                border: none;
                max-height: 3px;
                min-width: {self.COLUMN_WIDTH - 40}px;
                max-width: {self.COLUMN_WIDTH - 40}px;
                margin-top: 1px;
            }}
        """)

        # Остальной код метода create_header остается без изменений...

        # Layout заголовка с фиксированными размерами
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(15, 9, 15, 9)
        header_layout.setSpacing(0)

        # Верхняя строка с фиксированными размерами
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(8)

        # Заголовок колонки
        title_label = QLabel(self.title)
        title_label.setObjectName("title")
        title_label.setFixedWidth(200)

        # Счётчик
        self.counter_label = QLabel("0")
        self.counter_label.setObjectName("counter")
        self.counter_label.setFixedSize(40, 20)

        top_row.addWidget(title_label)
        top_row.addStretch()
        top_row.addWidget(self.counter_label)

        # Подчеркивание с фиксированной шириной
        underline = QLabel()
        underline.setObjectName("underline")
        underline.setFixedWidth(self.COLUMN_WIDTH - 40)

        # Нижняя строка для суммы/остатка и комбо-бокса
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 4, 0, 4)
        bottom_row.setSpacing(8)

        # Сумма/остаток с фиксированной шириной
        self.amount_label = QLabel()
        self.amount_label.setObjectName("amount")

        # Создаем и настраиваем комбо-бокс
        self.sort_combo = QComboBox()
        self.sort_combo.setFixedSize(120, 24)

        # Добавляем опции сортировки
        for text, value in self.SORT_OPTIONS:
            self.sort_combo.addItem(text, value)
        self.sort_combo.currentIndexChanged.connect(self.on_sort_changed)
        # Устанавливаем сохраненную сортировку
        if self.current_sort:
            for i in range(self.sort_combo.count()):
                if self.sort_combo.itemData(i) == self.current_sort:
                    self.sort_combo.setCurrentIndex(i)
                    break
        # Добавляем виджеты в нижнюю строку
        bottom_row.addWidget(self.amount_label)
        bottom_row.addStretch()
        bottom_row.addWidget(self.sort_combo)

        # Добавляем все элементы в layout заголовка
        header_layout.addLayout(top_row)
        header_layout.addWidget(underline)
        header_layout.addLayout(bottom_row)

        return header

    def on_sort_changed(self, index):
        """Обработчик изменения сортировки"""
        sort_value = self.sort_combo.currentData()
        if sort_value:
            # Сохраняем выбранную сортировку
            self.current_sort = sort_value
            self.settings.setValue(f'sort_order_{self.status}', sort_value)
            self.settings.sync()  # Принудительно сохраняем настройки
            self.sort_orders(sort_value)

    def sort_orders(self, sort_key):
        """Сортировка заказов"""
        if not hasattr(self, 'model') or not self.model._orders:
            return

        orders = self.model._orders.copy()

        def get_sort_value(order, key_prefix):
            try:
                if key_prefix == 'discount':
                    discount = order.get('discount', '0%')
                    if isinstance(discount, str):
                        return float(discount.strip('%') or 0)
                    return float(discount or 0)
                elif key_prefix == 'date':
                    return self.safe_convert_to_datetime(order.get('created_date'))
                elif key_prefix == 'amount':
                    return float(order.get('cost') or 0)
                elif key_prefix == 'deadline':
                    return str(order.get('deadline') or '')
                elif key_prefix == 'service':
                    return str(order.get('service') or '').lower()
                elif key_prefix == 'group':
                    return str(order.get('group') or '').lower()
                elif key_prefix == 'remaining':
                    return float(order.get('remaining_amount') or 0)
                elif key_prefix == 'payment_date':
                    return self.safe_convert_to_datetime(order.get('payment_date'))
                return ''
            except Exception:
                if key_prefix in ['discount', 'amount', 'remaining']:
                    return 0.0
                elif key_prefix in ['date', 'payment_date']:
                    return datetime.min
                return ''

        key_prefix = sort_key.rsplit('_', 1)[0]
        is_ascending = sort_key.endswith('_asc')

        orders.sort(
            key=lambda x: get_sort_value(x, key_prefix),
            reverse=not is_ascending
        )

        self.model.setOrders(orders)
        self.list_view.viewport().update()


    def update_orders(self, orders):
        """Обновление списка заказов"""
        try:
            self.setUpdatesEnabled(False)

            # Преобразуем данные заказов
            orders_data = []
            now = datetime.now()

            for order in orders:
                # Проверяем, является ли order словарем или объектом Order
                if isinstance(order, dict):
                    order_dict = order
                else:
                    order_dict = {
                        'id': order.id,
                        'fio': order.fio,
                        'group': order.group,
                        'service': order.service,
                        'deadline': order.deadline,
                        'cost': order.cost,
                        'paid_amount': order.paid_amount,
                        'remaining_amount': order.remaining_amount,
                        'discount': order.discount,
                        'status': order.status,
                        'login': order.login,
                        'theme': order.theme,
                        'comment': order.comment,
                        'phone': order.phone,
                        'teacher_name': order.teacher_name,
                        'website': order.website,
                        'password': order.password,
                        'teacher_email': order.teacher_email,
                        'discount_end_date': order.discount_end_date if hasattr(order, 'discount_end_date') else None,
                        'discount_start_date': order.discount_start_date if hasattr(order,
                                                                                    'discount_start_date') else None,
                        'payment_date': order.payment_date if hasattr(order, 'payment_date') else None,
                        'created_date': order.created_date if hasattr(order, 'created_date') else None
                    }

                orders_data.append(order_dict)

            # Обновляем модель
            self.model.setOrders(orders_data)

            # Применяем сохраненную сортировку
            if self.current_sort:
                self.sort_orders(self.current_sort)

            # Обновляем счетчик
            self.counter_label.setText(str(len(orders_data)))

            # Обновляем сумму/остаток
            if self.status == 'Выполнен':
                total = sum(order.get('paid_amount', 0) for order in orders_data)
                self.amount_label.setText(f"Оплачено: {total:,.0f} ₽")
            else:
                total = sum(order.get('remaining_amount', 0) for order in orders_data)
                self.amount_label.setText(f"Остаток: {total:,.0f} ₽")

            # Обновляем layout
            self.list_view.doItemsLayout()

        except Exception as e:
            print(f"Ошибка при обновлении заказов: {e}")
        finally:
            self.setUpdatesEnabled(True)

    def clear_sort_settings(self):
        """Очистка настроек сортировки"""
        self.settings.remove(f'sort_order_{self.status}')
        self.settings.sync()
        self.current_sort = None
        self.sort_combo.setCurrentIndex(0)

    def safe_convert_to_datetime(self, value):
        """Безопасное преобразование значения в datetime"""
        if value is None:
            return datetime.min
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, datetime.min.time())
        if isinstance(value, str):
            try:
                return datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                try:
                    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return datetime.min
        return datetime.min

    def clear(self):
        """Очистка списка заказов"""
        if hasattr(self, 'model'):
            self.model.clear()
        self.counter_label.setText("0")
        self.amount_label.setText("Остаток: 0 ₽")

    def listview_dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def listview_dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.accept()
        else:
            event.ignore()

    def listview_dropEvent(self, event):
        try:
            order_id = int(event.mimeData().text())

            with DatabaseManager().session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order or order.status == self.status:
                    event.ignore()
                    return

                # Проверка для статуса "Выполнен"
                if self.status == 'Выполнен':
                    # Проверяем оплату с учетом скидки
                    remaining = order.recalculate_remaining()

                    if remaining > 0:
                        # Показываем окно оплаты
                        from ui.windows.payment_window import PaymentWindow
                        payment_window = PaymentWindow(self, order)
                        result = payment_window.exec_()

                        if result != QDialog.Accepted:
                            event.ignore()
                            return

                        # Перечитываем заказ после оплаты
                        session.refresh(order)
                        remaining = order.recalculate_remaining()

                        if remaining > 0:
                            from ui.message_utils import show_warning
                            show_warning(self, "Предупреждение",
                                         "Невозможно изменить статус на 'Выполнен'. Остались неоплаченные суммы.")
                            event.ignore()
                            return

                # Если все проверки пройдены - принимаем
                event.accept()
                self.status_changed.emit(order_id, self.status, self.old_status)

        except ValueError:
            event.ignore()
