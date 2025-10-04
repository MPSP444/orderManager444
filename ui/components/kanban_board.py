from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QScrollArea, QPushButton, QLineEdit, QDialog, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor

from core.database_manager import DatabaseManager
from .order_card import OrderCard  # Исправлен импорт
from datetime import datetime, timedelta, date
from .virtualized_column import VirtualizedKanbanColumn
# Импорты для работы с базой данных
from sqlalchemy import or_, and_, cast, String, func
from core.database import Order, init_database
from sqlalchemy import text, or_, cast, String
from sqlalchemy import func, or_, cast, String, text as sql_text

from ..message_utils import show_error
from ui.windows.reminder_dialog import ReminderDialog
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QAction


class NotificationButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("🔔")
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 20px;
                background: #2196F3;
                color: white;
                min-width: 45px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        self.notifications = []
        self.menu = QMenu(self)
        self.setMenu(self.menu)

        # Добавляем счетчик уведомлений
        self.notification_count = QLabel("0", self)
        self.notification_count.setStyleSheet("""
            QLabel {
                background: red;
                color: white;
                border-radius: 10px;
                padding: 2px 5px;
                margin: 2px;
            }
        """)
        self.notification_count.hide()

    def add_notification(self, order_data):
        # Проверяем, нет ли уже такого заказа
        if not any(n['id'] == order_data['id'] for n in self.notifications):
            self.notifications.append(order_data)

            # Создаем действие в меню
            action = QAction(f"Заказ #{order_data['id']} - {order_data['fio']}", self)
            action.triggered.connect(lambda: self.show_notification_dialog(order_data))
            self.menu.addAction(action)

            # Обновляем счетчик
            self.notification_count.setText(str(len(self.notifications)))
            self.notification_count.show()

            # Обновляем стиль кнопки
            if self.notifications:
                self.setStyleSheet("""
                    QPushButton {
                        padding: 8px 15px;
                        border: none;
                        border-radius: 20px;
                        background: #f44336;
                        color: white;
                    }
                    QPushButton:hover {
                        background: #d32f2f;
                    }
                """)

    def clear_notifications(self):
        self.notifications.clear()
        self.menu.clear()
        self.notification_count.hide()
        self.setStyleSheet(self._default_style)

    def show_notification_dialog(self, order_data):
        dialog = ReminderDialog(order_data, self)
        dialog.exec_()


class KanbanBoard(QWidget):
    """Канбан-доска для управления заказами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.orders_cache = {}  # Кэш заказов по статусам
        self.cache_timestamp = None  # Время последнего обновления кэша
        self.cache_lifetime = timedelta(minutes=5)  # Время жизни кэша
        self.current_search_query = ""
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(300000)
        self.initUI()
        self.check_reminders()

    def initUI(self):
        """Инициализация интерфейса доски"""
        main_layout = QVBoxLayout(self)
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

        mass_message_btn = QPushButton("📱 Массовая рассылка")
        mass_message_btn.clicked.connect(self.show_mass_messaging)
        mass_message_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 20px;
                background: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        top_panel.addWidget(mass_message_btn)
        self.notification_btn = NotificationButton(self)
        top_panel.addWidget(self.notification_btn)
        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.loadOrders)
        refresh_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 20px;
                background: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        top_panel.addWidget(refresh_btn)

        main_layout.addLayout(top_panel)

        # Контейнер для колонок
        columns_container = QWidget()
        self.columns_layout = QHBoxLayout(columns_container)
        self.columns_layout.setSpacing(10)
        self.columns_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем колонки
        self.columns = {}
        columns_data = [
            ("🆕 Новые", "Новый"),
            ("⚙️ В работе", "В работе"),
            ("⏳ Ожидают оплаты", "В ожидании оплаты"),
            ("✅ Выполнены", "Выполнен"),
            ("❌ Отменены", "Отказ")
        ]

        for title, status in columns_data:
            column = VirtualizedKanbanColumn(title, status)  # Используем виртуализированную версию
            column.status_changed.connect(self.on_status_changed)
            self.columns[status] = column
            self.columns_layout.addWidget(column)

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
        self.loadOrders()

    def is_cache_valid(self):
        """Проверка актуальности кэша"""
        if not self.cache_timestamp:
            return False
        return datetime.now() - self.cache_timestamp < self.cache_lifetime

    def show_mass_messaging(self):
        """Показ окна массовой рассылки"""
        from ui.windows.mass_messaging import MassMessagingDialog
        dialog = MassMessagingDialog(self)
        dialog.exec_()

    def check_reminders(self):
        try:
            with self.db_manager.session_scope() as session:
                current_date = datetime.now()
                two_months_ago = current_date - timedelta(days=60)

                # Получаем заказы старше 2 месяцев, которые не выполнены и не отменены
                orders = session.query(Order).filter(
                    and_(
                        Order.created_date <= two_months_ago,
                        Order.status.in_(['В ожидании оплаты', 'В работе', 'Новый']),
                        Order.remaining_amount > 0
                    )
                ).all()

                settings = QSettings('MPSP', 'OrderReminders')
                notification_button = self.notification_btn

                for order in orders:
                    client_key = f"client_{order.fio}"
                    if settings.value(f"{client_key}/reminders_disabled", False, type=bool):
                        continue

                    order_key = f"order_{order.id}"
                    next_reminder_str = settings.value(f"{order_key}/next_reminder")

                    if next_reminder_str:
                        next_reminder = datetime.strptime(next_reminder_str, '%Y-%m-%d %H:%M:%S')
                        if current_date < next_reminder:
                            continue

                    # Получаем точное время до истечения скидки
                    if order.discount_end_date:
                        end_date = order.discount_end_date
                        if isinstance(end_date, str):
                            end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
                        elif isinstance(end_date, date):
                            end_date = datetime.combine(end_date, datetime.min.time())

                        time_diff = end_date - current_date
                        total_seconds = int(time_diff.total_seconds())

                        if total_seconds > 0:
                            days = total_seconds // (24 * 3600)
                            remaining_seconds = total_seconds % (24 * 3600)
                            hours = remaining_seconds // 3600
                            minutes = (remaining_seconds % 3600) // 60

                            time_str = f"{days}д {hours}ч {minutes}м"
                        else:
                            time_str = "срок истёк"

                    # Создаем данные для уведомления
                    order_data = {
                        'id': order.id,
                        'fio': order.fio,
                        'service': order.service,
                        'created_date': order.created_date,
                        'remaining_amount': order.remaining_amount,
                        'phone': order.phone,
                        'status': order.status,
                        'time_remaining': time_str if 'time_str' in locals() else None
                    }

                    # Добавляем уведомление
                    notification_button.add_notification(order_data)

        except Exception as e:
            print(f"Ошибка при проверке напоминаний: {e}")



    def show_reminder(self, order):
        """Показ окна напоминания"""
        try:
            # Преобразуем заказ в словарь для передачи в диалог
            order_data = {
                'id': order.id,
                'fio': order.fio,
                'service': order.service,
                'created_date': order.created_date,
                'remaining_amount': order.remaining_amount,
                'phone': order.phone,
                'status': order.status
            }

            # Создаем и показываем диалог
            dialog = ReminderDialog(order_data, self)
            dialog.exec_()

        except Exception as e:
            print(f"Ошибка при показе напоминания: {e}")
    def on_status_changed(self, order_id, new_status, old_status=None):
        """Обработка изменения статуса заказа"""
        try:
            self.setUpdatesEnabled(False)
            # Получаем затронутые статусы
            affected_statuses = set()
            if old_status:
                affected_statuses.add(old_status)
            affected_statuses.add(new_status)

            # Обновляем соответствующие колонки с полными данными
            with self.db_manager.session_scope() as session:
                # Получаем заказ и обновляем его скидку
                order = session.query(Order).get(order_id)
                if order:
                    # Проверяем и обновляем скидку при необходимости
                    if new_status == 'Выполнен':
                        # Проверяем была ли оплата в срок
                        if order.payment_date and order.discount_end_date:
                            if order.payment_date <= order.discount_end_date.date():
                                # Сохраняем скидку
                                pass
                            else:
                                # Обнуляем скидку если оплата была после срока
                                order.discount = "0%"
                                order.discount_start_date = None
                                order.discount_end_date = None
                    else:
                        # Для других статусов проверяем не истекла ли скидка
                        order.check_discount_expiration()

                    session.commit()

                # Обновляем все затронутые колонки
                for status in affected_statuses:
                    if status in self.columns:
                        orders = self.db_manager.get_orders_by_status([status])
                        self.columns[status].update_orders(orders)

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при обновлении колонок: {str(e)}")
        finally:
            self.setUpdatesEnabled(True)

    def update_cache(self):
        """Обновление кэша"""
        try:
            with self.db_manager.session_scope() as session:
                orders = session.query(Order).with_entities(
                    Order.id, Order.fio, Order.group, Order.service,
                    Order.deadline, Order.cost, Order.paid_amount,
                    Order.remaining_amount, Order.discount, Order.status
                ).order_by(Order.created_date.desc()).all()

                # Группируем заказы по статусам
                self.orders_cache.clear()
                for order in orders:
                    if order.status not in self.orders_cache:
                        self.orders_cache[order.status] = []
                    self.orders_cache[order.status].append(order)

                self.cache_timestamp = datetime.now()
        except Exception as e:
            print(f"Ошибка при обновлении кэша: {e}")

    def get_orders_for_status(self, status):
        """Получение заказов для статуса с использованием кэша"""
        if not self.is_cache_valid():
            self.update_cache()
        return self.orders_cache.get(status, [])

    def loadOrders(self):
        """Загрузка заказов с учетом текущего поиска и обновлением скидок"""
        try:
            self.setUpdatesEnabled(False)

            # Если есть активный поиск, используем его
            if self.current_search_query:
                self.search_orders(self.current_search_query)
                return

            # Очищаем колонки
            for column in self.columns.values():
                column.clear()

            with self.db_manager.session_scope() as session:
                # Получаем все заказы
                all_orders = session.query(Order).all()
                now = datetime.now()

                for order in all_orders:
                    try:
                        # Проверяем и обновляем скидки
                        if order.discount and order.discount != "0%" and order.discount != "Не указано":
                            if order.discount_end_date:
                                if isinstance(order.discount_end_date, date):
                                    end_date = datetime.combine(order.discount_end_date, datetime.min.time())
                                else:
                                    end_date = order.discount_end_date

                                # Для выполненных заказов проверяем дату оплаты
                                if order.status == 'Выполнен' and order.payment_date:
                                    payment_date = order.payment_date
                                    if isinstance(payment_date, str):
                                        payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
                                    elif isinstance(payment_date, date):
                                        payment_date = datetime.combine(payment_date, datetime.min.time())

                                    if payment_date > end_date:
                                        order.discount = "0%"
                                        order.discount_start_date = None
                                        order.discount_end_date = None
                                        session.commit()

                                # Для остальных заказов проверяем текущее время
                                elif now > end_date:
                                    order.discount = "0%"
                                    order.discount_start_date = None
                                    order.discount_end_date = None
                                    session.commit()

                        # Устанавливаем даты для заказов в ожидании оплаты
                        if (order.status == 'В ожидании оплаты' and
                                order.discount and
                                order.discount != "0%" and
                                order.discount != "Не указано" and
                                not order.discount_start_date and
                                not order.discount_end_date):
                            order.discount_start_date = now
                            order.discount_end_date = now + timedelta(days=4)
                            session.commit()

                    except Exception as e:
                        print(f"Ошибка при проверке заказа #{order.id}: {e}")

                # Загружаем актуальные данные
                orders = session.query(Order).with_entities(
                    Order.id, Order.fio, Order.group, Order.service,
                    Order.deadline, Order.cost, Order.paid_amount,
                    Order.remaining_amount, Order.discount, Order.status,
                    Order.login, Order.theme, Order.comment, Order.phone,
                    Order.teacher_name, Order.website, Order.password,
                    Order.teacher_email, Order.discount_start_date,
                    Order.discount_end_date, Order.payment_date,
                    Order.created_date
                ).order_by(Order.created_date.desc()).all()

                # Группируем по статусам и добавляем информацию о просрочке
                orders_by_status = {}
                for order in orders:
                    order_dict = order._asdict()

                    # Определяем, в какую колонку поместить заказ
                    display_status = order_dict['status']

                    # Если статус "Переделка", помещаем в колонку "В работе"
                    if display_status == 'Переделка':
                        display_status = 'В работе'

                    # Добавляем информацию о днях ожидания для статуса "В ожидании оплаты"
                    if order_dict['status'] == 'В ожидании оплаты' and order_dict['created_date']:
                        created_date = order_dict['created_date']
                        if isinstance(created_date, date):
                            created_date = datetime.combine(created_date, datetime.min.time())
                        days_waiting = (now.date() - created_date.date()).days
                        order_dict['days_waiting'] = days_waiting

                    # Проверяем просрочку и статус скидки
                    if order_dict['discount_end_date']:
                        end_date = order_dict['discount_end_date']
                        if isinstance(end_date, date):
                            end_date = datetime.combine(end_date, datetime.min.time())

                        if order_dict['status'] == 'Выполнен' and order_dict['payment_date']:
                            payment_date = order_dict['payment_date']
                            if isinstance(payment_date, date):
                                payment_datetime = datetime.combine(payment_date, datetime.min.time())
                            else:
                                payment_datetime = payment_date
                            time_diff = end_date - payment_datetime
                        else:
                            time_diff = end_date - now

                        if time_diff.total_seconds() < 0:
                            order_dict['is_overdue'] = True
                            order_dict['overdue_days'] = abs(time_diff.days)
                            order_dict['overdue_hours'] = abs(time_diff.seconds // 3600)
                        else:
                            order_dict['is_overdue'] = False
                            order_dict['remaining_days'] = time_diff.days
                            order_dict['remaining_hours'] = time_diff.seconds // 3600

                    # Добавляем заказ в соответствующую группу
                    if display_status not in orders_by_status:
                        orders_by_status[display_status] = []
                    orders_by_status[display_status].append(order_dict)

                # Обновляем колонки
                for status, column in self.columns.items():
                    if status in orders_by_status:
                        column.update_orders(orders_by_status[status])

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при загрузке заказов: {str(e)}")
        finally:
            self.setUpdatesEnabled(True)
            self.update()

    def _get_button_style(self):
        """Стиль для кнопок"""
        return """
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 20px;
                background: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """
    def update_specific_columns(self, order, old_status, new_status):
        """Обновление только затронутых колонок"""
        try:
            self.setUpdatesEnabled(False)
            affected_statuses = {old_status, new_status}

            with self.db_manager.session_scope() as session:
                for status in affected_statuses:
                    if status in self.columns:
                        # Получаем заказы для конкретного статуса
                        orders = session.query(Order).with_entities(
                            Order.id, Order.fio, Order.group, Order.service,
                            Order.deadline, Order.cost, Order.paid_amount,
                            Order.remaining_amount, Order.discount, Order.status
                        ).filter(
                            Order.status == status
                        ).order_by(Order.created_date.desc()).all()

                        # Преобразуем результаты в словари
                        orders_data = [order._asdict() for order in orders]

                        # Обновляем колонку
                        self.columns[status].update_orders(orders_data)

        except Exception as e:
            print(f"Ошибка при обновлении колонок: {e}")
        finally:
            self.setUpdatesEnabled(True)
            self.update()

    def clear_all_columns(self):
        """Очищает содержимое всех колонок на канбан-доске."""
        for column in self.columns.values():
            column.clear()

    def order_to_dict(order):
        """Преобразует объект Order в словарь"""
        return {
            "id": order.id,
            "fio": order.fio,
            "group": order.group,
            "service": order.service,
            "deadline": order.deadline,
            "cost": order.cost,
            "paid_amount": order.paid_amount,
            "remaining_amount": order.remaining_amount,
            "discount": order.discount,
            "status": order.status
        }

    def setupUpdateTimer(self):
        """Настройка таймера автообновления с оптимизацией"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(lambda: self.loadOrders())
        # Увеличиваем интервал обновления для снижения нагрузки
        self.update_timer.start(600000)

    def cleanup(self):
        """Очистка ресурсов при закрытии"""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()

    def search_orders(self, text_query):
        """Поиск с использованием Python-фильтрации"""
        try:
            self.current_search_query = text_query.strip()
            with self.db_manager.session_scope() as session:
                if not text_query.strip():
                    self.loadOrders()
                    return

                # Получаем все заказы с полными данными
                all_orders = self.db_manager.get_orders_by_status()
                search_text = text_query.strip().lower()

                # Фильтруем заказы на стороне Python
                filtered_orders = [
                    order for order in all_orders if
                    search_text in order['fio'].lower() or
                    search_text in str(order['id']) or
                    search_text in order['group'].lower() or
                    search_text in order['service'].lower()
                ]

                # Группируем результаты по статусам для канбан-доски
                orders_by_status = {}
                for order in filtered_orders:
                    if order['status'] not in orders_by_status:
                        orders_by_status[order['status']] = []
                    orders_by_status[order['status']].append(order)

                # Обновляем колонки канбан-доски
                for column in self.columns.values():
                    column.clear()

                for status, column in self.columns.items():
                    if status in orders_by_status:
                        column.update_orders(orders_by_status[status])

        except Exception as e:
            print(f'Ошибка при поиске: {e}')



