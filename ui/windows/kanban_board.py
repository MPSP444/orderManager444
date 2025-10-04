from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QScrollArea, QPushButton, QMenu,
                             QDialog, QLineEdit, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint, QTimer
from PyQt5.QtGui import QDrag, QColor, QPainter, QPen, QFont
from datetime import datetime, timedelta
import os
import json

from core.database import Order
from core.database_manager import DatabaseManager
from .state_manager import StateManager
from .payment_window import PaymentWindow
from .new_order_window import NewOrderWindow
from .client_info_window import ClientInfoWindow
from .detailed_info_window import DetailedInfoWindow
from .order_info_window import OrderInfoWindow
from ui.message_utils import show_question
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor


# Цвета для статусов
STATUS_COLORS = {
    'Новый': '#3498db',
    'В работе': '#f39c12',
    'В ожидании оплаты': '#e74c3c',
    'Выполнен': '#2ecc71',
    'Отказ': '#95a5a6'
}


class OrderCard(QWidget):
    """Карточка заказа"""
    drag_started = pyqtSignal(dict)  # Сигнал начала перетаскивания
    status_changed = pyqtSignal(int, str)  # Сигнал изменения статуса

    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.order_data = order_data
        self.initUI()
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)

    def initUI(self):
        """Инициализация интерфейса карточки"""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)

        # Устанавливаем фиксированные размеры карточки
        self.setFixedWidth(200)
        self.setMinimumHeight(120)

        # Верхняя часть: ФИО и ID
        top_layout = QHBoxLayout()
        name_label = QLabel(self.order_data['fio'])
        name_label.setStyleSheet("""
            color: #0b5394; 
            font-weight: bold;
            font-size: 13px;
        """)
        id_label = QLabel(f"#{self.order_data['id']}")
        id_label.setStyleSheet("color: #666; font-size: 12px;")
        id_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top_layout.addWidget(name_label, stretch=1)  # Растягиваем имя
        top_layout.addWidget(id_label)
        layout.addLayout(top_layout)

        # Группа
        group_layout = QHBoxLayout()
        group_label = QLabel("Группа:")
        group_label.setStyleSheet("color: #666; font-size: 12px;")
        group_value = QLabel(self.order_data['group'])
        group_value.setStyleSheet("color: #666; font-size: 12px;")
        group_layout.addWidget(group_label)
        group_layout.addWidget(group_value)
        group_layout.addStretch()
        layout.addLayout(group_layout)

        # Услуга
        service_layout = QHBoxLayout()
        service_label = QLabel("Услуга:")
        service_label.setStyleSheet("color: #666; font-size: 12px;")
        service_value = QLabel(self.order_data['service'])
        service_value.setStyleSheet("color: #666; font-size: 12px;")
        service_value.setWordWrap(True)
        service_layout.addWidget(service_label)
        service_layout.addWidget(service_value)
        service_layout.addStretch()
        layout.addLayout(service_layout)

        # Срок
        if self.order_data.get('deadline'):
            remaining_layout = QHBoxLayout()
            clock_label = QLabel("🕒")
            remaining_text = QLabel(f"Осталось: {self.order_data['deadline']}")
            remaining_text.setStyleSheet("color: #f39c12; font-size: 12px;")
            remaining_layout.addWidget(clock_label)
            remaining_layout.addWidget(remaining_text)
            remaining_layout.addStretch()
            layout.addLayout(remaining_layout)

        # Стоимость
        cost_layout = QHBoxLayout()
        cost_value = QLabel(f"{self.order_data['cost']:.0f}₽")
        cost_value.setStyleSheet("font-size: 12px; font-weight: bold; color: #666;")
        paid_label = QLabel(f"Оплачено: {self.order_data.get('paid_amount', 0):.0f}₽")
        paid_label.setStyleSheet("font-size: 12px; color: #27ae60;")
        paid_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        cost_layout.addWidget(cost_value)
        cost_layout.addStretch()
        cost_layout.addWidget(paid_label)
        layout.addLayout(cost_layout)

        # Остаток
        if self.order_data.get('remaining_amount', 0) > 0:
            remaining_layout = QHBoxLayout()
            remaining_label = QLabel("Остаток:")
            remaining_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
            remaining_value = QLabel(f"{self.order_data.get('remaining_amount', 0):.0f}₽")
            remaining_value.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")
            remaining_layout.addWidget(remaining_label)
            remaining_layout.addWidget(remaining_value)
            remaining_layout.addStretch()
            layout.addLayout(remaining_layout)

        # Нижняя панель (скидка и статус)
        bottom_layout = QHBoxLayout()

        # Скидка если есть
        if self.order_data.get('discount'):
            discount_label = QLabel(f"🎁 {self.order_data['discount']}")
            discount_label.setStyleSheet("""
                color: #e67e22;
                font-size: 12px;
                background-color: #fff3cd;
                padding: 2px 4px;
                border-radius: 3px;
            """)
            bottom_layout.addWidget(discount_label)

        # Статус
        status_text = "✓ Выполнен" if self.order_data['status'] == 'Выполнен' else self.order_data['status']
        status_label = QLabel(status_text)
        if self.order_data['status'] == 'Выполнен':
            status_color = "#27ae60"  # Зеленый для выполненных
        else:
            status_color = "#666"  # Серый для остальных
        status_label.setStyleSheet(f"""
            color: {status_color};
            font-size: 12px;
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        """)
        bottom_layout.addWidget(status_label)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

        # Добавляем растягивающийся элемент в конец
        layout.addStretch()

        # Стиль всей карточки
        bg_color = "#f8fef9" if self.order_data['status'] == 'Выполнен' else "#ffffff"
        border_color = "#c8e6c9" if self.order_data['status'] == 'Выполнен' else "#e0e0e0"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 6px;
            }}
            QLabel {{
                border: none;
                background-color: transparent;
            }}
        """)

        # Устанавливаем тень
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
    def create_payment_progress(self):
        """Создание прогресс-бара оплаты"""
        progress = QWidget()
        progress.setFixedHeight(5)
        paid = self.order_data.get('paid_amount', 0)
        total = self.order_data['cost']

        if total > 0:
            progress_percent = min((paid / total) * 100, 100)
        else:
            progress_percent = 0

        progress.paintEvent = lambda e: self.paint_progress(progress, progress_percent)
        return progress

    def paint_progress(self, widget, percent):
        """Отрисовка прогресс-бара"""
        painter = QPainter(widget)
        painter.setRenderHint(QPainter.Antialiasing)

        # Фон
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 50))
        painter.drawRoundedRect(0, 0, widget.width(), widget.height(), 2, 2)

        # Прогресс
        if percent > 0:
            width = int((widget.width() * percent) / 100)
            painter.setBrush(QColor(255, 255, 255))
            painter.drawRoundedRect(0, 0, width, widget.height(), 2, 2)

        painter.end()

    def contextMenuEvent(self, event):
        """Обработка контекстного меню"""
        menu = QMenu(self)

        # Редактирование
        edit_action = menu.addAction("✏️ Редактировать")
        edit_action.triggered.connect(self.edit_order)

        # Оплата
        payment_action = menu.addAction("💰 Внести оплату")
        payment_action.triggered.connect(self.add_payment)

        # Новый заказ
        new_order_action = menu.addAction("📝 Новый заказ клиенту")
        new_order_action.triggered.connect(self.create_new_order)

        # Статусы
        status_menu = menu.addMenu("🔄 Сменить статус")
        statuses = {
            "🆕 Новый": "Новый",
            "⚙️ В работе": "В работе",
            "⏳ В ожидании оплаты": "В ожидании оплаты",
            "✅ Выполнен": "Выполнен",
            "❌ Отказ": "Отказ"
        }

        for label, status in statuses.items():
            action = status_menu.addAction(label)
            action.triggered.connect(lambda x, s=status: self.change_status(s))

        # Комментарии
        comments_menu = menu.addMenu("💬 Комментарии")
        comments_menu.addAction("➕ Добавить комментарий").triggered.connect(self.add_comment)
        comments_menu.addAction("👁️ Просмотр комментариев").triggered.connect(self.view_comments)

        # Печать
        print_menu = menu.addMenu("🖨️ Печать")
        print_menu.addAction("📄 Квитанция").triggered.connect(self.print_receipt)
        print_menu.addAction("🧾 Чек").triggered.connect(self.print_check)

        # Информация
        info_menu = menu.addMenu("ℹ️ Информация")
        info_menu.addAction("👤 О клиенте").triggered.connect(self.show_client_info)
        info_menu.addAction("📋 О заказе").triggered.connect(self.show_order_info)
        info_menu.addAction("📊 Подробная информация").triggered.connect(self.show_detailed_info)

        # Папка
        open_folder_action = menu.addAction("📁 Открыть папку")
        open_folder_action.triggered.connect(self.open_folder)

        menu.addSeparator()

        # Отмена и удаление
        cancel_action = menu.addAction("⛔ Отменить заказ")
        cancel_action.triggered.connect(self.cancel_order)
        delete_action = menu.addAction("🗑️ Удалить")
        delete_action.triggered.connect(self.delete_order)

        menu.exec_(event.globalPos())

    def mousePressEvent(self, event):
        """Обработка нажатия мыши"""
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()

            # Сериализуем данные заказа
            order_data = {
                'id': self.order_data['id'],
                'status': self.order_data['status']
            }
            mime.setText(json.dumps(order_data))

            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)

            # Испускаем сигнал о начале перетаскивания
            self.drag_started.emit(self.order_data)

    def edit_order(self):
        """Редактирование заказа"""
        dialog = NewOrderWindow(self, order_id=self.order_data['id'])
        dialog.exec_()

    def add_payment(self):
        """Добавление оплаты"""
        dialog = PaymentWindow(self, order_id=self.order_data['id'])
        dialog.exec_()

    def create_new_order(self):
        """Создание нового заказа для клиента"""
        dialog = NewOrderWindow(self)
        dialog.fio_input.setText(self.order_data['fio'])
        dialog.group_input.setText(self.order_data['group'])
        dialog.exec_()

    def change_status(self, new_status):
        """Изменение статуса заказа"""
        db_manager = DatabaseManager()
        try:
            with db_manager.session_scope() as session:
                order = session.query(Order).get(self.order_data['id'])
                if order:
                    order.status = new_status
                    session.commit()
                    self.status_changed.emit(self.order_data['id'], new_status)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")

    def show_client_info(self):
        """Показ информации о клиенте"""
        dialog = ClientInfoWindow(self, client_fio=self.order_data['fio'])
        dialog.exec_()

    def show_order_info(self):
        """Показ информации о заказе"""
        dialog = OrderInfoWindow(self, order_id=self.order_data['id'])
        dialog.exec_()

    def show_detailed_info(self):
        """Показ подробной информации"""
        dialog = DetailedInfoWindow(self, client_fio=self.order_data['fio'])
        dialog.exec_()

    def open_folder(self):
        """Открытие папки заказа"""
        try:
            base_path = r"D:\Users\mgurbanmuradov\Documents\Общая"
            client_path = os.path.join(base_path, self.order_data['fio'])
            service_path = os.path.join(client_path, self.order_data['service'])

            os.makedirs(service_path, exist_ok=True)
            os.startfile(service_path)
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Ошибка при открытии папки: {str(e)}")


class KanbanColumn(QWidget):
    """Оптимизированная колонка канбан-доски"""
    status_changed = pyqtSignal(int, str)

    def __init__(self, title, status, parent=None):
        super().__init__(parent)
        self.title = title
        self.status = status
        self.cached_cards = {}  # Кэш карточек
        self.initUI()
        self.setAcceptDrops(True)

    def initUI(self):
        """Инициализация интерфейса колонки"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Фиксированная ширина колонки с учетом размера карточек
        self.setFixedWidth(220)  # 200px ширина карточки + отступы

        # Заголовок колонки
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #2c3e50;
            font-weight: bold;
            font-size: 14px;
            padding: 8px;
            background-color: white;
            border-bottom: 2px solid #e0e0e0;
        """)
        layout.addWidget(title_label)

        # Контейнер для карточек
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 3px;
            }
        """)

        cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(cards_widget)
        self.cards_layout.setSpacing(6)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.cards_layout.addStretch()

        scroll.setWidget(cards_widget)
        layout.addWidget(scroll)
    def dragEnterEvent(self, event):
        """Оптимизированная обработка начала перетаскивания"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                }
            """)

    def dragLeaveEvent(self, event):
        """Оптимизированная обработка выхода перетаскивания"""
        self.setStyleSheet("")
        event.accept()

    def dropEvent(self, event):
        """Оптимизированная обработка сброса карточки"""
        try:
            data = json.loads(event.mimeData().text())
            order_id = data['id']
            old_status = data['status']

            if old_status != self.status and order_id not in self.cached_cards:
                self.status_changed.emit(order_id, self.status)

            event.acceptProposedAction()

        except Exception as e:
            print(f"Ошибка при перетаскивании: {str(e)}")

    def update_counter(self):
        """Обновление счетчика заказов"""
        count = 0
        for i in range(self.cards_layout.count()):
            if self.cards_layout.itemAt(i).widget():
                count += 1
        self.counter_label.setText(f"{count} заказов")



    def dragEnterEvent(self, event):
        """Обработка начала перетаскивания"""
        if event.mimeData().hasText():
            event.accept()
            self.setStyleSheet("""
                QWidget {
                    background-color: #e3f2fd;
                    border-radius: 8px;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Обработка выхода перетаскивания за пределы"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        event.accept()

    def dropEvent(self, event):
        """Обработка сброса карточки"""
        try:
            # Восстанавливаем стиль
            self.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    border-radius: 8px;
                }
            """)

            # Получаем данные
            data = json.loads(event.mimeData().text())
            order_id = data['id']
            old_status = data['status']

            # Проверяем валидность перемещения
            if not self.validate_status_change(old_status, self.status, order_id):
                event.ignore()
                return

            # Меняем статус
            self.status_changed.emit(order_id, self.status)
            event.accept()

        except Exception as e:
            print(f"Ошибка при перемещении карточки: {e}")
            event.ignore()

    def validate_status_change(self, old_status, new_status, order_id):
        """Проверка валидности смены статуса"""
        db_manager = DatabaseManager()

        try:
            with db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    return False

                # Проверяем возможность перемещения в "Выполнен"
                if new_status == "Выполнен" and order.remaining_amount > 0:
                    QMessageBox.warning(
                        self,
                        "Предупреждение",
                        "Нельзя переместить заказ в 'Выполнен' при наличии задолженности"
                    )
                    return False

                # Нельзя перемещать отмененные заказы
                if old_status == "Отказ":
                    QMessageBox.warning(
                        self,
                        "Предупреждение",
                        "Нельзя изменить статус отмененного заказа"
                    )
                    return False

                return True

        except Exception as e:
            print(f"Ошибка при проверке валидности: {e}")
            return False



class KanbanBoard(QWidget):
    """Канбан-доска для управления заказами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.state_manager = StateManager()
        self.state_manager.add_observer(self)
        self.initUI()
        self.setupUpdateTimer()

    def initUI(self):
        """Инициализация интерфейса доски"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Верхняя панель с поиском
        top_panel = QHBoxLayout()

        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по заказам...")
        self.search_input.textChanged.connect(self.search_orders)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 20px;
                background: white;
                min-width: 300px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        top_panel.addWidget(self.search_input)
        top_panel.addStretch()

        # Добавляем верхнюю панель в основной layout
        main_layout.addLayout(top_panel)

        # Контейнер для колонок
        columns_container = QWidget()
        columns_layout = QHBoxLayout(columns_container)
        columns_layout.setSpacing(10)
        columns_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем колонки
        self.columns = {}
        columns_data = [
            ("Новые", "Новый"),
            ("В работе", "В работе"),
            ("Ожидают оплаты", "В ожидании оплаты"),
            ("Выполнены", "Выполнен"),
            ("Отменены", "Отказ")
        ]

        for title, status in columns_data:
            column = KanbanColumn(title, status)
            column.status_changed.connect(self.on_status_changed)
            self.columns[status] = column
            columns_layout.addWidget(column)

        # Создаем scroll area для горизонтальной прокрутки
        scroll = QScrollArea()
        scroll.setWidget(columns_container)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f5f5;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 8px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                min-width: 50px;
                border-radius: 4px;
            }
        """)

        main_layout.addWidget(scroll)

        # Загружаем заказы
        self.loadOrders()
    def setupUpdateTimer(self):
        """Настройка автоматического обновления"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.loadOrders)
        self.update_timer.start(300000)  # Обновление каждые 5 минут

    def loadOrders(self):
        """Загрузка заказов"""
        try:
            with self.db_manager.session_scope() as session:
                # Получаем все заказы
                orders = session.query(Order).order_by(Order.created_date.desc()).all()

                # Очищаем колонки
                for column in self.columns.values():
                    while column.cards_layout.count() > 0:
                        item = column.cards_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()

                # Распределяем заказы по колонкам
                for order in orders:
                    if order.status in self.columns:
                        card = OrderCard(order.to_dict())
                        card.status_changed.connect(self.on_status_changed)

                        # Добавляем карточку в соответствующую колонку
                        self.columns[order.status].cards_layout.addWidget(card)

                # Обновляем счетчики
                for column in self.columns.values():
                    column.update_counter()

        except Exception as e:
            print(f"Ошибка при загрузке заказов: {e}")
    def createOptimizedCard(self, order):
        """Оптимизированное создание карточки заказа"""
        try:
            # Конвертируем данные заказа в словарь
            order_data = {
                'id': order.id,
                'fio': order.fio,
                'group': order.group,
                'service': order.service,
                'deadline': order.deadline,
                'cost': order.cost,
                'paid_amount': order.paid_amount or 0,
                'remaining_amount': order.remaining_amount or 0,
                'discount': order.discount,
                'status': order.status
            }

            # Создаем карточку с оптимизированными данными
            card = OrderCard(order_data)
            card.status_changed.connect(self.on_status_changed)
            return card

        except Exception as e:
            print(f"Ошибка при создании карточки: {str(e)}")
            return None

    def search_orders(self, text):
        """Оптимизированный поиск по заказам"""
        try:
            # Блокируем обновление UI на время поиска
            self.setUpdatesEnabled(False)

            search_text = text.lower().strip()

            with self.db_manager.session_scope() as session:
                # Базовый запрос
                query = session.query(Order)

                # Применяем фильтр только если есть текст поиска
                if search_text:
                    query = query.filter(
                        Order.fio.ilike(f"%{search_text}%") |
                        Order.group.ilike(f"%{search_text}%") |
                        Order.service.ilike(f"%{search_text}%")
                    )

                # Получаем отфильтрованные заказы
                orders = query.order_by(Order.created_date.desc()).all()

                # Очищаем колонки
                self.clearColumns()

                # Группируем заказы по статусам
                orders_by_status = {}
                for order in orders:
                    if order.status not in orders_by_status:
                        orders_by_status[order.status] = []
                    orders_by_status[order.status].append(order)

                # Обновляем каждую колонку
                for status, column in self.columns.items():
                    status_orders = orders_by_status.get(status, [])

                    # Обновляем счётчик
                    count_text = f"{len(status_orders)} заказов"
                    column.counter_label.setText(count_text)

                    # Добавляем карточки
                    for order in status_orders:
                        card = self.createOptimizedCard(order)
                        if card:
                            column.cards_layout.insertWidget(
                                column.cards_layout.count() - 1,
                                card
                            )

        except Exception as e:
            print(f"Ошибка при поиске: {str(e)}")
        finally:
            self.setUpdatesEnabled(True)  # Разблокируем обновление UI
            self.update()  # Принудительно обновляем виджет

    def clearColumns(self):
        """Оптимизированная очистка колонок"""
        try:
            for column in self.columns.values():
                # Удаляем все виджеты, кроме последнего (растягивающегося элемента)
                while column.cards_layout.count() > 1:
                    item = column.cards_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                column.update()

        except Exception as e:
            print(f"Ошибка при очистке колонок: {str(e)}")

    def on_status_changed(self, order_id, new_status):
        """Оптимизированная обработка изменения статуса"""
        try:
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if order:
                    order.status = new_status
                    session.commit()

                    # Обновляем только затронутые колонки
                    QTimer.singleShot(100, self.loadOrders)

        except Exception as e:
            print(f"Ошибка при изменении статуса: {str(e)}")

    def setupUpdateTimer(self):
        """Настройка таймера обновления"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.loadOrders)
        # Обновление каждые 5 минут
        self.update_timer.start(300000)

    def clearColumns(self):
        """Очистка всех колонок"""
        for column in self.columns.values():
            while column.cards_layout.count() > 1:  # Оставляем растягивающийся элемент
                item = column.cards_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

    def search_orders(self, text):
        """Поиск заказов"""
        text = text.lower()
        try:
            with self.db_manager.session_scope() as session:
                query = session.query(Order)

                if text:
                    query = query.filter(
                        (Order.fio.ilike(f"%{text}%")) |
                        (Order.group.ilike(f"%{text}%")) |
                        (Order.service.ilike(f"%{text}%"))
                    )

                orders = query.all()
                self.clearColumns()

                for order in orders:
                    card = OrderCard(order.to_dict())
                    card.status_changed.connect(self.on_status_changed)

                    if order.status in self.columns:
                        self.columns[order.status].cards_layout.insertWidget(
                            self.columns[order.status].cards_layout.count() - 1,
                            card
                        )

                # Обновляем счетчики
                for column in self.columns.values():
                    column.update_counter()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при поиске: {str(e)}")

    def on_status_changed(self, order_id, new_status):
        """Обработка изменения статуса"""
        try:
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if order:
                    old_status = order.status
                    order.status = new_status
                    session.commit()

                    # Обновляем доску
                    self.loadOrders()

                    # Уведомляем об изменении
                    self.state_manager.notify_all()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")

    def showSettings(self):
        """Показ окна настроек"""
        from .settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec_()

    def cleanup(self):
        """Очистка ресурсов при закрытии"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()