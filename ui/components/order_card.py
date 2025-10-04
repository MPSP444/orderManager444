import traceback
from datetime import datetime, date, timedelta, time
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint, Qt
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                           QProgressBar, QSizePolicy, QGraphicsOpacityEffect,
                           QApplication, QGraphicsDropShadowEffect, QMenu,
                           QDialog, QTextEdit, QTextBrowser, QPushButton,
                           QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QColor
from reportlab.lib.units import mm
from datetime import datetime, timedelta
from ui.message_utils import show_error
from ui.windows.new_order_window import NewOrderWindow
from ui.windows.client_info_window import DIALOG_STYLE
from PyQt5.QtWidgets import (QMenu, QDialog, QMessageBox)
from PyQt5.QtCore import Qt
from core.database_manager import DatabaseManager
from core.database import Order
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices
from urllib.parse import quote
import re
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel, QMenu,
                           QProgressBar, QSizePolicy, QGraphicsOpacityEffect,
                           QApplication, QGraphicsDropShadowEffect, QDialog,
                           QTextEdit, QTextBrowser, QPushButton, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt5.QtGui import QDrag, QPainter, QColor

from core.database_manager import DatabaseManager
from core.database import Order
from ui.message_utils import show_error, show_warning
from ui.windows.payment_window import PaymentWindow
from ui.windows.reminder_dialog import ReminderDialog
from ui.windows.window_manager import OrderWindowManager
from ui.windows.client_info_window import ClientInfoWindow
from ui.windows.order_info_window import OrderInfoWindow
from ui.windows.detailed_info_window import DetailedInfoWindow
from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                           QProgressBar, QSizePolicy, QGraphicsOpacityEffect,
                           QApplication, QGraphicsDropShadowEffect, QMenu,
                           QDialog, QTextEdit, QTextBrowser, QPushButton,
                           QMessageBox, QFileDialog)  # Добавлен QFileDialog
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, timedelta
from ui.windows.client_statistics_window import ClientStatisticsWindow
import urllib.parse
import uuid
import requests
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices


class OrderCard(QFrame):
    status_changed = pyqtSignal(int, str, str)

    STATUS_STYLES = {
        'Новый': {
            'bg': '#E3F2FD',
            'border': '#2196F3',
            'text': '#1565C0',
        },
        'В работе': {
            'bg': '#FFF3E0',
            'border': '#FF9800',
            'text': '#E65100',
        },
        'Переделка': {
            'bg': '#F3E5F5',
            'border': '#9C27B0',
            'text': '#6A1B9A',
        },
        'В ожидании оплаты': {
            'bg': '#FFEBEE',
            'border': '#F44336',
            'text': '#C62828',
        },
        'Выполнен': {
            'bg': '#E8F5E9',
            'border': '#4CAF50',
            'text': '#2E7D32',
        },
        'Отказ': {
            'bg': '#EFEBE9',
            'border': '#757575',
            'text': '#424242',
        }
    }

    # Стили для разных периодов ожидания оплаты
    WAITING_PERIOD_STYLES = {
        'normal': {
            'bg': '#FFEBEE',
            'border': '#F44336',
            'text': '#C62828',
        },
        'medium': {  # 1-6 месяцев
            'bg': '#FFE0B2',
            'border': '#FF7043',
            'text': '#D84315',
        },
        'long': {  # более 6 месяцев
            'bg': '#FFCDD2',
            'border': '#E53935',
            'text': '#B71C1C',
        }
    }

    def __init__(self, order_data, parent=None):
        """Инициализация карточки заказа"""
        super().__init__(parent)
        self.order_data = order_data
        self.drag_start_position = None
        self.setAttribute(Qt.WA_Hover, True)
        self.setMouseTracking(True)
        self.installEventFilter(self)
        self.setFocusPolicy(Qt.StrongFocus)
        self.order = None
        self.status = order_data['status']
        self.setContextMenuPolicy(Qt.DefaultContextMenu)

        # Получаем базовый стиль для статуса
        if self.status == 'Переделка':
            self.style = self.STATUS_STYLES['Переделка']
        elif self.status == 'В ожидании оплаты':
            # Проверяем длительность ожидания
            if 'created_date' in order_data:
                created_date = order_data['created_date']
                if isinstance(created_date, str):
                    try:
                        created_date = datetime.strptime(created_date, '%d.%m.%Y')
                    except ValueError:
                        try:
                            created_date = datetime.strptime(created_date, '%Y-%m-%d')
                        except ValueError:
                            created_date = None
                elif isinstance(created_date, date):
                    created_date = datetime.combine(created_date, datetime.min.time())

                if created_date:
                    days_waiting = (datetime.now().date() - created_date.date()).days
                    if days_waiting > 180:  # более 6 месяцев
                        self.style = self.WAITING_PERIOD_STYLES['long']
                    elif days_waiting > 30:  # более 1 месяца
                        self.style = self.WAITING_PERIOD_STYLES['medium']
                    else:
                        self.style = self.STATUS_STYLES[self.status]
                else:
                    self.style = self.STATUS_STYLES[self.status]
            else:
                self.style = self.STATUS_STYLES[self.status]
        else:
            self.style = self.STATUS_STYLES.get(self.status, self.STATUS_STYLES['Отказ'])

        # Расчет суммы с учетом скидки
        self.cost = order_data['cost']
        self.discount = order_data.get('discount', '')
        self.paid_amount = order_data.get('paid_amount', 0)

        # Расчет итоговой суммы с учетом скидки
        if self.discount:
            try:
                discount_percent = float(self.discount.strip('%'))
                self.discount_amount = self.cost * (discount_percent / 100)
                self.final_cost = self.cost - self.discount_amount
            except (ValueError, TypeError):
                self.final_cost = self.cost
        else:
            self.final_cost = self.cost

        # Расчет корректного остатка
        self.remaining = max(0, self.final_cost - self.paid_amount)

        # Установка фиксированных размеров
        self.setFixedWidth(315)
        self.setFixedHeight(225)

        # Инициализация интерфейса
        self.setup_ui()

    def get_card_style(self):
        """Определение стиля карточки с учетом статуса и времени ожидания"""
        base_style = self.STATUS_STYLES.get(self.status, self.STATUS_STYLES['Отказ'])

        # Проверяем специальные условия для статуса "В ожидании оплаты"
        if self.status == 'В ожидании оплаты' and 'created_date' in self.order_data:
            created_date = self.order_data['created_date']

            # Преобразуем дату создания в datetime если нужно
            if isinstance(created_date, str):
                created_date = datetime.strptime(created_date, '%d.%m.%Y')

            # Вычисляем разницу в днях
            days_waiting = (datetime.now().date() - created_date.date()).days

            # Определяем стиль в зависимости от длительности ожидания
            if days_waiting > 180:  # более 6 месяцев
                return self.WAITING_PERIOD_STYLES['long']
            elif days_waiting > 30:  # более 1 месяца
                return self.WAITING_PERIOD_STYLES['medium']

        return base_style
    def mousePressEvent(self, event):
        """Тестовая функция для проверки кликов"""
        super().mousePressEvent(event)

    def _refresh_kanban(self):
        """Обновление канбан-доски"""
        try:
            # Ищем родительский компонент KanbanBoard
            parent = self
            while parent is not None:
                if hasattr(parent, 'loadOrders'):
                    parent.loadOrders()
                    break
                parent = parent.parent()
        except Exception as e:
            print(f"Ошибка при обновлении канбан-доски: {e}")


    def extend_discount(self):
        """Продление срока действия скидки"""
        try:
            with DatabaseManager().session_scope() as session:
                order = session.query(Order).get(self.order_data['id'])
                if not order:
                    show_error(self, "Ошибка", "Заказ не найден")
                    return

                if not order.discount or order.discount == "0%" or order.discount == "Не указано":
                    show_error(self, "Ошибка", "У заказа нет активной скидки")
                    return

                # Устанавливаем новые даты
                now = datetime.now()
                order.discount_start_date = now
                order.discount_end_date = now + timedelta(days=4)
                session.commit()

                QMessageBox.information(
                    self,
                    "Успех",
                    f"Срок скидки продлен до {order.discount_end_date.strftime('%d.%m.%Y %H:%M')}"
                )

                # Обновляем отображение
                parent = self
                while parent and not hasattr(parent, 'loadOrders'):
                    parent = parent.parent()
                if parent:
                    parent.loadOrders()

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при продлении скидки: {str(e)}")

    def check_dates_and_set_text(self, end_date, now, remaining_label):
        """Проверка дат и установка текста"""
        try:
            # Преобразуем end_date в datetime если нужно, сохраняя точное время
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
            elif isinstance(end_date, date) and not isinstance(end_date, datetime):
                end_date = datetime.combine(end_date, datetime.min.time())

            # Вычисляем разницу времени
            time_diff = end_date - now

            # Точный расчет часов и дней
            total_seconds = int(time_diff.total_seconds())
            days = total_seconds // (24 * 3600)  # Целые дни
            remaining_seconds = total_seconds % (24 * 3600)  # Оставшиеся секунды
            hours = remaining_seconds // 3600  # Часы из оставшихся секунд

            # Форматируем текст
            if time_diff.total_seconds() <= 0:
                remaining_text = "⚠️ Срок истёк"
                remaining_label.setStyleSheet("""
                    color: #FF0000;
                    font-weight: bold;
                    font-size: 14px;
                    margin-left: 20px;
                """)
            else:
                remaining_text = f"{days}д {hours}ч"
                remaining_label.setStyleSheet("""
                    color: #FF5722;
                    font-weight: bold;
                    font-size: 14px;
                    margin-left: 20px;
                """)

            return remaining_text, "orange"

        except Exception as e:
            print(f"DEBUG: ERROR occurred: {str(e)}")
            print(f"DEBUG: Error traceback: ", traceback.format_exc())
            return "-", "gray"

    def setup_ui(self):
        """Настройка интерфейса карточки"""
        # Применяем стиль карточки
        self.setStyleSheet(f"""
            OrderCard {{
                background-color: {self.style['bg']};
                border: 1px solid {self.style['border']};
                border-radius: 4px;
                margin: 0px;
                padding: 0px;
            }}
            QLabel {{
                color: #212121;
                background: transparent;
                font-size: 14px;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Верхний блок (ФИО и номер)
        header_frame = self.create_header_frame()
        main_layout.addWidget(header_frame)

        # Основная информация
        info_container = QFrame()
        info_container.setStyleSheet("QFrame { background: transparent; border: none; }")

        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Группа
        group_layout = QHBoxLayout()
        group_label = QLabel("👥 Группа:")
        group_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        group_value = QLabel(self.order_data['group'])
        group_value.setStyleSheet("font-size: 14px;")
        group_layout.addWidget(group_label)
        group_layout.addWidget(group_value)
        group_layout.addStretch()
        info_layout.addLayout(group_layout)

        # Услуга
        service_layout = QHBoxLayout()
        service_label = QLabel("📝 Услуга:")
        service_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        service_value = QLabel(self.order_data['service'])
        service_value.setStyleSheet("font-size: 14px;")
        service_layout.addWidget(service_label)
        service_layout.addWidget(service_value)
        service_layout.addStretch()
        info_layout.addLayout(service_layout)

        # Сроки
        deadline_layout = QHBoxLayout()
        deadline_text = QLabel("⏰ Срок:")
        deadline_text.setStyleSheet("font-weight: bold; font-size: 14px;")
        deadline_value = QLabel(self.order_data.get('deadline', 'Не указан'))
        deadline_value.setStyleSheet("font-size: 14px;")

        deadline_layout.addWidget(deadline_text)
        deadline_layout.addWidget(deadline_value)

        # Оставшееся время скидки
        remaining_label = QLabel()
        remaining_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            margin-left: 20px;
        """)

        # Проверяем наличие скидки
        has_discount = (self.order_data.get('discount') and
                        self.order_data['discount'] != "0%" and
                        self.order_data['discount'] != "Не указано")

        if has_discount:
            end_date = self.order_data.get('discount_end_date')
            if end_date:
                now = datetime.now()

                # Преобразуем end_date в datetime если нужно
                if isinstance(end_date, str):
                    try:
                        end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            end_date = datetime.strptime(end_date, '%Y-%m-%d')
                        except ValueError:
                            end_date = now - timedelta(days=1)  # Считаем срок истекшим
                elif isinstance(end_date, date) and not isinstance(end_date, datetime):
                    end_date = datetime.combine(end_date, datetime.min.time())

                # Если статус "Выполнен", проверяем дату оплаты
                if self.status == 'Выполнен' and self.order_data.get('payment_date'):
                    payment_date = self.order_data['payment_date']

                    # Преобразуем payment_date в datetime если нужно
                    if isinstance(payment_date, str):
                        try:
                            payment_date = datetime.strptime(payment_date, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            try:
                                payment_date = datetime.strptime(payment_date, '%Y-%m-%d')
                            except ValueError:
                                payment_date = None
                    elif isinstance(payment_date, date) and not isinstance(payment_date, datetime):
                        payment_date = datetime.combine(payment_date, datetime.min.time())

                    if payment_date:
                        if end_date > payment_date:
                            # Скидка была действительна на момент оплаты
                            time_diff = end_date - payment_date
                            days = time_diff.days
                            hours = time_diff.seconds // 3600
                            remaining_label.setText(f"✅ Оплачено со скидкой (оставалось {days}д {hours}ч)")
                            remaining_label.setStyleSheet("""
                                color: #4CAF50;
                                font-weight: bold;
                                font-size: 14px;
                                margin-left: 20px;
                            """)
                        else:
                            # Скидка истекла на момент оплаты
                            remaining_label.setText("⚠️ Оплачено после истечения скидки")
                            remaining_label.setStyleSheet("""
                                color: #FF9800;
                                font-weight: bold;
                                font-size: 14px;
                                margin-left: 20px;
                            """)
                else:
                    # Обычная логика для невыполненных заказов
                    time_diff = end_date - now

                    # Проверяем, истек ли срок
                    if time_diff.total_seconds() <= 0:
                        remaining_label.setText("⚠️ Срок истёк")
                        remaining_label.setStyleSheet("""
                            color: #FF0000;
                            font-weight: bold;
                            font-size: 14px;
                            margin-left: 20px;
                        """)
                    else:
                        days = time_diff.days
                        hours = time_diff.seconds // 3600
                        remaining_label.setText(f"⏳ Осталось: {days}д {hours}ч")
                        remaining_label.setStyleSheet("""
                            color: #FF5722;
                            font-weight: bold;
                            font-size: 14px;
                            margin-left: 20px;
                        """)
            else:
                remaining_label.setText("⏳ Срок не указан")
                remaining_label.setStyleSheet("""
                    color: #9E9E9E;
                    font-weight: bold;
                    font-size: 14px;
                    margin-left: 20px;
                """)
        else:
            remaining_label.setText("📝 Нет скидки")
            remaining_label.setStyleSheet("""
                color: #9E9E9E;
                font-weight: bold;
                font-size: 14px;
                margin-left: 20px;
            """)

        deadline_layout.addStretch()
        deadline_layout.addWidget(remaining_label)

        info_layout.addLayout(deadline_layout)

        # Стоимость и оплата
        cost_layout = QHBoxLayout()
        cost = self.order_data['cost']
        paid = self.order_data.get('paid_amount', 0)

        cost_label = QLabel(f"💰 {cost:,.0f}₽")
        cost_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        paid_label = QLabel(f"✅ Оплачено: {paid:,.0f}₽")
        paid_label.setStyleSheet("font-size: 14px;")

        cost_layout.addWidget(cost_label)
        cost_layout.addStretch()
        cost_layout.addWidget(paid_label)
        info_layout.addLayout(cost_layout)

        # Остаток
        if self.remaining > 0:
            remaining_layout = QHBoxLayout()
            remaining_label = QLabel(f"⚠️ Остаток: {self.remaining:,.0f}₽")
            remaining_label.setStyleSheet("""
                font-weight: bold;
                font-size: 14px;
                color: #F44336;
            """)
            remaining_layout.addWidget(remaining_label)
            remaining_layout.addStretch()
            info_layout.addLayout(remaining_layout)

        main_layout.addWidget(info_container)

        # Прогресс-бар
        if cost > 0:
            progress = QProgressBar(self)
            if self.order_data.get('discount'):
                try:
                    discount_percent = float(self.order_data['discount'].strip('%'))
                    discounted_cost = cost * (1 - discount_percent / 100)
                    percentage = min(100, int((paid / discounted_cost) * 100))
                except (ValueError, TypeError):
                    percentage = min(100, int((paid / cost) * 100))
            else:
                percentage = min(100, int((paid / cost) * 100))

            progress.setValue(percentage)
            progress.setTextVisible(False)
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {self.style['border']};
                    background-color: white;
                    height: 4px;
                    border-radius: 2px;
                    margin-top: 4px;
                    margin-bottom: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {self.style['border']};
                    border-radius: 2px;
                }}
            """)
            main_layout.addWidget(progress)

        # Нижний блок с скидкой и статусом
        footer_frame = self.create_footer_frame()
        main_layout.addWidget(footer_frame)

    def create_header_frame(self):
        """Создание заголовка карточки"""
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {self.style['border']};
                border-radius: 4px;
                background-color: {self.style['bg']};
                margin: 0px;
                padding: 0px;
            }}
            QLabel {{
                border: none;
                background: transparent;
                color: {self.style['text']};
                font-weight: bold;
                font-size: 16px;
            }}
        """)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 4, 8, 4)
        header_layout.setSpacing(4)

        # ФИО
        fio_label = QLabel(self.order_data['fio'])

        # Номер заказа
        number_label = QLabel(f"#{self.order_data['id']}")

        header_layout.addWidget(fio_label)
        header_layout.addStretch()
        header_layout.addWidget(number_label)

        return header_frame


    def create_info_container(self):
        """Создание контейнера с основной информацией"""
        info_container = QFrame()
        info_container.setStyleSheet("QFrame { background: transparent; border: none; }")

        info_layout = QVBoxLayout(info_container)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # Добавляем информацию (группа, услуга и т.д.)
        self.add_info_row(info_layout, "👥 Группа:", self.order_data['group'])
        self.add_info_row(info_layout, "📝 Услуга:", self.order_data['service'])
        self.add_info_row(info_layout, "⏰ Срок:", self.order_data.get('deadline', 'Не указан'))

        # Стоимость и оплата
        cost_layout = QHBoxLayout()
        cost = self.order_data.get('cost', 0)
        paid = self.order_data.get('paid_amount', 0)

        cost_label = QLabel(f"💰 {cost:,.0f}₽")
        cost_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        paid_label = QLabel(f"✅ Оплачено: {paid:,.0f}₽")
        paid_label.setStyleSheet("font-size: 14px;")

        cost_layout.addWidget(cost_label)
        cost_layout.addStretch()
        cost_layout.addWidget(paid_label)
        info_layout.addLayout(cost_layout)

        return info_container

    def add_info_row(self, layout, label_text, value_text):
        """Добавление строки с информацией"""
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        value = QLabel(str(value_text))
        value.setStyleSheet("font-size: 14px;")

        row_layout.addWidget(label)
        row_layout.addWidget(value)
        row_layout.addStretch()
        layout.addLayout(row_layout)

    def create_progress_bar(self):
        """Создание прогресс-бара"""
        progress = QProgressBar(self)
        cost = self.order_data.get('cost', 0)
        paid = self.order_data.get('paid_amount', 0)

        if self.order_data.get('discount'):
            try:
                discount_percent = float(self.order_data['discount'].strip('%'))
                discounted_cost = cost * (1 - discount_percent / 100)
                percentage = min(100, int((paid / discounted_cost) * 100))
            except (ValueError, TypeError):
                percentage = min(100, int((paid / cost) * 100))
        else:
            percentage = min(100, int((paid / cost) * 100))

        progress.setValue(percentage)
        progress.setTextVisible(False)
        progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.style['border']};
                background-color: white;
                height: 4px;
                border-radius: 2px;
                margin-top: 4px;
                margin-bottom: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {self.style['border']};
                border-radius: 2px;
            }}
        """)

        return progress

    def create_footer_frame(self):
        """Создание нижнего блока карточки"""
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"""
            QFrame {{
                border: 1px solid {self.style['border']};
                border-radius: 4px;
                background-color: {self.style['bg']};
                margin: 0px;
                padding: 0px;
            }}
            QLabel {{
                border: none;
                background: transparent;
                color: {self.style['text']};
                font-weight: bold;
                font-size: 14px;
            }}
        """)

        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(8, 4, 8, 4)
        footer_layout.setSpacing(4)

        # Скидка
        if self.order_data.get('discount'):
            discount_value = "0%" if self.order_data['discount'] == "Не указано" else self.order_data['discount']
            discount_label = QLabel(f"🏷️ {discount_value}")
            footer_layout.addWidget(discount_label)

        footer_layout.addStretch()

        # Статус и дни ожидания
        status_container = QHBoxLayout()

        # Если статус "В ожидании оплаты", добавляем количество дней
        if self.status == 'В ожидании оплаты' and 'created_date' in self.order_data:
            try:
                created_date = self.order_data['created_date']
                current_date = datetime.now().date()

                # Преобразование даты в зависимости от её типа
                if isinstance(created_date, str):
                    try:
                        created_date = datetime.strptime(created_date, '%d.%m.%Y').date()
                    except ValueError:
                        try:
                            created_date = datetime.strptime(created_date, '%Y-%m-%d').date()
                        except ValueError:
                            print(f"Неподдерживаемый формат даты: {created_date}")
                            created_date = None
                elif isinstance(created_date, datetime):
                    created_date = created_date.date()
                elif isinstance(created_date, date):
                    pass
                else:
                    created_date = None

                if created_date:
                    days_waiting = (current_date - created_date).days

                    # Определяем цвет в зависимости от длительности ожидания
                    if days_waiting > 180:  # более 6 месяцев
                        text_color = "#B71C1C"  # тёмно-красный
                    elif days_waiting > 30:  # более месяца
                        text_color = "#D84315"  # оранжевый
                    else:
                        text_color = self.style['text']

                    # Создаем текст статуса с днями
                    status_text = f"{self.status} ({days_waiting}д)"
                    status_label = QLabel(status_text)
                    status_label.setStyleSheet(f"color: {text_color};")
                    status_container.addWidget(status_label)
                else:
                    status_label = QLabel(self.status)
                    status_container.addWidget(status_label)

            except Exception as e:
                print(f"Ошибка при обработке даты: {e}")
                status_label = QLabel(self.status)
                status_container.addWidget(status_label)
        else:
            # Для остальных статусов просто показываем статус
            status_label = QLabel(self.status)
            status_container.addWidget(status_label)

        footer_layout.addLayout(status_container)

        return footer_frame

    def format_remaining_time(self, end_date):
        """Форматирование оставшегося времени"""
        now = datetime.now()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

        time_diff = end_date - now

        if time_diff.days > 0:
            return f"{time_diff.days}д"
        else:
            hours = time_diff.seconds // 3600
            if hours > 0:
                return f"{hours}ч"
            else:
                minutes = (time_diff.seconds % 3600) // 60
                return f"{minutes}м"

    def mouseDoubleClickEvent(self, event):
        """Обработка двойного клика"""
        if event.modifiers() & Qt.ControlModifier:
            self.open_client_folder()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def show_reminder_dialog(self):
        """Показ окна напоминания по требованию"""
        try:
            dialog = ReminderDialog(self.order_data, self)
            dialog.exec_()
        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при показе напоминания: {str(e)}")

    def contextMenuEvent(self, event):
        """Обработка контекстного меню"""
        try:
            menu = QMenu(self)
            if not self.parent():
                return

            # Основные действия
            new_order_action = menu.addAction('📝 Новый заказ клиенту')
            edit_action = menu.addAction('✏️ Редактировать')
            payment_action = menu.addAction('💰 Внести оплату')

            # Подменю быстрой смены статуса
            status_menu = menu.addMenu('🔄 Сменить статус')
            status_actions = {
                'Новый': status_menu.addAction('🆕 Новый'),
                'В работе': status_menu.addAction('⚙️ В работе'),
                'Переделка': status_menu.addAction('🔄 Переделка'),
                'В ожидании оплаты': status_menu.addAction('⏳ Ожидает оплаты'),
                'Выполнен': status_menu.addAction('✅ Выполнен'),
                'Отказ': status_menu.addAction('❌ Отменен')
            }
            discount_menu = menu.addMenu('🏷️ Управление скидкой')
            extend_discount_action = discount_menu.addAction('⏰ Продлить срок скидки')
            discount_info_action = discount_menu.addAction('📅 Информация о скидке')

            menu.addSeparator()

            # Комментарии и напоминания
            reminders_menu = menu.addMenu('🔔 Напоминания')
            remind_debt_action = reminders_menu.addAction('💰 Напомнить о долге')
            remind_total_debt_action = reminders_menu.addAction('💸 Напомнить об общем долге')
            remind_thanks_action = reminders_menu.addAction('🙏 Отправить благодарность')
            remind_follow_action = reminders_menu.addAction('📱 Написать "Как дела?"')
            remind_discount_action = reminders_menu.addAction('⏰ Напомнить о сроке скидки')
            remind_all_discounts_action = reminders_menu.addAction('💰 Напомнить об общих скидках')
            remind_discount_details_action = reminders_menu.addAction('📊 Детали всех скидок')
            show_reminder_action = reminders_menu.addAction('📅 Показать напоминание')
            show_reminder_action.triggered.connect(self.show_reminder_dialog)
            # Добавляем новый пункт для отправки запроса на отзыв
            review_action = menu.addAction('⭐ Отправить запрос на отзыв')
            # Комментарии
            add_comment_action = menu.addAction('✍️ Добавить комментарий')
            view_comments_action = menu.addAction('💭 Просмотр комментариев')
            menu.addSeparator()

            # Файлы и папки
            files_menu = menu.addMenu('📁 Файлы')
            open_folder_action = files_menu.addAction('📂 Открыть папку клиента')
            create_folder_action = files_menu.addAction('📁 Создать папку клиента')
            open_works_action = files_menu.addAction('📝 Открыть папку с работами')
            menu.addSeparator()

            # Печать документов
            print_menu = menu.addMenu('🖨️ Печать документов')
            print_receipt_action = print_menu.addAction('🧾 Кассовый чек')
            print_invoice_action = print_menu.addAction('📄 Квитанция')
            print_contract_action = print_menu.addAction('📋 Договор')
            menu.addSeparator()

            # Информация
            info_menu = menu.addMenu('ℹ️ Информация')
            client_info_action = info_menu.addAction('👤 Информация о клиенте')
            order_info_action = info_menu.addAction('📋 Информация о заказе')
            detailed_info_action = info_menu.addAction('📊 Подробная информация')
            client_history_action = info_menu.addAction('📜 История клиента')
            # Добавляем новое подменю для статистики и аналитики
            analytics_menu = menu.addMenu('📊 Статистика и аналитика')
            show_statistics_action = analytics_menu.addAction('📈 Показать статистику')
            show_analysis_action = analytics_menu.addAction('📊 Анализ заказов')
            show_predictions_action = analytics_menu.addAction('🔮 Прогнозы')
            # Показываем меню и получаем выбранное действие
            action = menu.exec_(event.globalPos())

            if action:
                with DatabaseManager().session_scope() as session:
                    order = session.query(Order).get(self.order_data['id'])
                    if not order:
                        show_error(self, "Ошибка", "Заказ не найден")
                        return

                    self.order = order

                    # Обработка быстрой смены статуса
                    for status, status_action in status_actions.items():
                        if action == status_action:
                            try:
                                old_status = order.status

                                # Проверка для статуса "Выполнен"
                                if status == 'Выполнен':
                                    remaining = order.recalculate_remaining()
                                    if remaining > 0:
                                        payment_window = PaymentWindow(self, order)
                                        result = payment_window.exec_()
                                        if result != QDialog.Accepted:
                                            return
                                        session.refresh(order)
                                        remaining = order.recalculate_remaining()
                                        if remaining > 0:
                                            show_warning(self, "Предупреждение",
                                                         "Невозможно изменить статус на 'Выполнен'. Остались неоплаченные суммы.")
                                            return

                                # Меняем статус
                                order.status = status
                                session.commit()

                                # Используем все три параметра в сигнале
                                self.status_changed.emit(order.id, status, old_status)

                                # Обновляем канбан-доску
                                self._refresh_kanban()
                                return
                            except Exception as e:
                                show_error(self, "Ошибка", f"Ошибка при смене статуса: {str(e)}")
                                return

                    if action == new_order_action:
                        existing_data = {
                            'fio': order.fio,
                            'group': order.group,
                            'phone': order.phone or '',
                            'teacher_name': order.teacher_name or '',
                            'teacher_email': order.teacher_email or '',
                            'login': order.login or '',
                            'password': order.password or '',
                            'website': order.website or ''
                        }
                        if OrderWindowManager.get_instance().show_order_window(
                                self.window(), None, existing_data) == QDialog.Accepted:
                            self._refresh_kanban()

                    elif action == edit_action:
                        if OrderWindowManager.get_instance().show_order_window(
                                self.window(), order) == QDialog.Accepted:
                            self._refresh_kanban()

                    elif action == payment_action:
                        payment_window = PaymentWindow(self, order=order)
                        if payment_window.exec_() == QDialog.Accepted:
                            self._refresh_kanban()

                    elif action == remind_debt_action:
                        self.show_debt_reminder()
                    elif action == remind_total_debt_action:
                        self.show_total_debt_reminder()
                    elif action == remind_thanks_action:
                        self.show_thanks_message()
                    elif action == remind_follow_action:
                        self.show_follow_up_message()
                    elif action == remind_discount_action:
                        self.show_discount_reminder()
                        return
                    elif action == extend_discount_action:
                        self.extend_discount()
                    elif action == discount_info_action:
                        self.show_discount_info()
                    elif action == remind_all_discounts_action:
                        self.show_all_discounts_reminder()
                    elif action == remind_discount_details_action:
                        self.show_detailed_discounts_info()


                    elif action == add_comment_action:
                        self.add_comment()
                    elif action == view_comments_action:
                        self.view_comments()
                    elif action == open_folder_action:
                        self.open_client_folder()
                    elif action == create_folder_action:
                        self.create_client_folder()
                    elif action == open_works_action:
                        self.open_works_folder()

                    elif action == print_receipt_action:
                        self.print_receipt()
                    elif action == print_invoice_action:
                        self.print_invoice()
                    elif action == print_contract_action:
                        self.print_contract()
                    elif action == client_info_action:
                        dialog = ClientInfoWindow(self, client_fio=order.fio)
                        dialog.exec_()
                    elif action == order_info_action:
                        dialog = OrderInfoWindow(self, order=order)
                        dialog.exec_()
                    elif action == detailed_info_action:
                        dialog = DetailedInfoWindow(self, client_fio=order.fio)
                        dialog.exec_()
                    elif action == client_history_action:
                        self.show_client_history()
                    elif action == review_action:
                        self.send_review_request()
                    # После последнего elif добавьте:
                    elif action == show_statistics_action:
                        self.show_statistics_window()
                    elif action == show_analysis_action:
                        self.show_statistics_window(tab_index=1)  # Переключится на вкладку анализа
                    elif action == show_predictions_action:
                        self.show_statistics_window(tab_index=4)  # Переключится на вкладку прогнозов

        except Exception as e:
            show_error(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    def show_all_discounts_reminder(self):
        """Показ всех скидок с напоминанием"""
        try:
            with DatabaseManager().session_scope() as session:
                client_orders = session.query(Order).filter(
                    Order.fio == self.order_data['fio'],
                    Order.status.in_(['В работе', 'В ожидании оплаты']),
                    Order.remaining_amount > 0
                ).all()

                if not client_orders:
                    QMessageBox.information(self, "Информация", "Нет активных заказов с неоплаченными суммами")
                    return

                total_original = sum(order.cost for order in client_orders)
                total_discounted = 0
                total_paid = sum(order.paid_amount for order in client_orders)
                total_savings = 0

                for order in client_orders:
                    if order.discount and order.discount != "0%" and order.discount != "Не указано":
                        try:
                            discount_percent = float(order.discount.strip('%'))
                            discounted_cost = order.cost * (1 - discount_percent / 100)
                            total_discounted += discounted_cost
                            total_savings += (order.cost - discounted_cost)
                        except (ValueError, TypeError):
                            total_discounted += order.cost
                    else:
                        total_discounted += order.cost

                # Расчет оставшейся суммы к оплате с учетом уже оплаченного
                remaining_to_pay = total_discounted - total_paid

                message = (
                    f"Здравствуйте, {self.order_data['fio']}!\n\n"
                    f"У вас есть {len(client_orders)} активных заказов:\n"
                    f"Общая стоимость: {total_original:,.2f} ₽\n"
                    f"С учетом всех скидок: {total_discounted:,.2f} ₽\n"
                    f"К оплате осталось: {remaining_to_pay:,.2f} ₽\n"
                    f"Ваша экономия: {total_savings:,.2f} ₽"
                )

                # Находим все заказы с истекающими скидками
                now = datetime.now()
                expiring_orders = []

                for order in client_orders:
                    if (order.discount_end_date and
                            order.discount and
                            order.discount != "0%" and
                            order.discount != "Не указано"):

                        # Преобразуем end_date в datetime с сохранением точного времени
                        if isinstance(order.discount_end_date, str):
                            discount_end = datetime.strptime(order.discount_end_date, '%Y-%m-%d %H:%M:%S')
                        elif isinstance(order.discount_end_date, date):
                            # Извлекаем точное время из даты окончания
                            discount_end_str = str(order.discount_end_date)
                            if ' ' in discount_end_str:
                                try:
                                    # Пытаемся получить точное время из строки
                                    _, time_str = discount_end_str.split(' ')
                                    hour, minute = map(int, time_str.split(':')[:2])
                                    discount_end = datetime.combine(order.discount_end_date, time(hour, minute))
                                except (ValueError, IndexError):
                                    discount_end = datetime.combine(order.discount_end_date, time(18, 0))
                            else:
                                discount_end = datetime.combine(order.discount_end_date, time(18, 0))
                        else:
                            discount_end = order.discount_end_date

                        time_diff = discount_end - now

                        if time_diff.total_seconds() > 0:
                            total_hours = time_diff.total_seconds() / 3600
                            days = int(total_hours // 24)
                            hours = int(total_hours % 24)

                            try:
                                discount_percent = float(order.discount.strip('%'))
                                potential_loss = order.cost * (discount_percent / 100)
                                expiring_orders.append((order, time_diff, potential_loss))
                            except (ValueError, TypeError):
                                continue

                if expiring_orders:
                    # Сортируем по времени до истечения
                    expiring_orders.sort(key=lambda x: x[1])

                    # Получаем информацию о первом (ближайшем) заказе
                    nearest_order, time_diff, _ = expiring_orders[0]

                    # Расчет времени так же, как в show_discount_reminder
                    total_hours = time_diff.total_seconds() / 3600
                    days = int(total_hours // 24)
                    hours = int(total_hours % 24)

                    # Добавляем заголовок с информацией о ближайшей скидке
                    message += (
                        f"\n\n⚠️ Ближайшая скидка заканчивается через {days}д {hours}ч\n"
                    )

                    # Добавляем информацию о всех заказах со скидками
                    for order, time_diff, loss in expiring_orders:
                        message += f"(заказ #{order.id} - {order.service})\n"
                        message += f"При неоплате вы потеряете {loss:,.2f} ₽\n"

                message += (
                    "\n\nДля оплаты:\n"
                    "💳 Сбербанк: +79066322571\n"
                    "📱 WhatsApp: +79066322571"
                )

                # Показываем диалог
                dialog = QDialog(self)
                dialog.setWindowTitle("Информация о заказах")
                dialog.setFixedWidth(450)
                layout = QVBoxLayout(dialog)

                text_edit = QTextEdit()
                text_edit.setPlainText(message)
                text_edit.setReadOnly(True)
                layout.addWidget(text_edit)

                button_layout = QHBoxLayout()
                copy_btn = QPushButton("📋 Копировать")
                whatsapp_btn = QPushButton("📱 Отправить в WhatsApp")
                close_btn = QPushButton("❌ Закрыть")

                button_layout.addWidget(copy_btn)
                button_layout.addWidget(whatsapp_btn)
                button_layout.addWidget(close_btn)
                layout.addLayout(button_layout)

                copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(message))
                whatsapp_btn.clicked.connect(lambda: self.send_to_whatsapp(message))
                close_btn.clicked.connect(dialog.close)

                dialog.exec_()

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при создании напоминания: {str(e)}")

    def show_detailed_discounts_info(self):
        """Показ детальной информации о всех скидках"""
        try:
            with DatabaseManager().session_scope() as session:
                client_orders = session.query(Order).filter(
                    Order.fio == self.order_data['fio'],
                    Order.status.in_(['Новый', 'В работе', 'В ожидании оплаты'])
                ).all()

                if not client_orders:
                    QMessageBox.information(self, "Информация", "Нет активных заказов")
                    return

                dialog = QDialog(self)
                dialog.setWindowTitle(f"Детальная информация о заказах")
                layout = QVBoxLayout(dialog)

                text_browser = QTextBrowser()

                # Формируем HTML и простой текст отдельно для разных форматов
                html_content = f"""
                <h2>Информация о заказах</h2>
                <div style='background-color: #f5f5f5; padding: 10px; border-radius: 5px;'>
                    <p><b>ФИО:</b> {self.order_data['fio']}</p>
                    <p><b>Группа:</b> {self.order_data['group']}</p>
                </div>
                <hr>
                """

                # Для WhatsApp и PDF используем plain text
                plain_text = f"""Информация о заказах

    ФИО: {self.order_data['fio']}
    Группа: {self.order_data['group']}

    """
                total_original = 0
                total_with_discount = 0

                # Информация о каждом заказе
                for order in client_orders:
                    original_cost = order.cost or 0
                    total_original += original_cost
                    current_cost = original_cost

                    discount_info_html = ""
                    discount_info_text = ""

                    if order.discount and order.discount != "0%" and order.discount != "Не указано":
                        try:
                            discount_percent = float(order.discount.strip('%'))
                            current_cost = original_cost * (1 - discount_percent / 100)

                            discount_info_html = f"<br>Скидка: {order.discount}"
                            discount_info_text = f"\nСкидка: {order.discount}"

                            if order.discount_end_date:
                                end_date_str = order.discount_end_date.strftime('%d.%m.%Y %H:%M')
                                time_diff = order.discount_end_date - datetime.now()
                                if time_diff.total_seconds() > 0:
                                    days = time_diff.days
                                    hours = time_diff.seconds // 3600
                                    discount_info_html += f"""
                                    <br>Срок действия до: {end_date_str}
                                    <br>Осталось: {days}д {hours}ч
                                    """
                                    discount_info_text += f"""
    Срок действия до: {end_date_str}
    Осталось: {days}д {hours}ч"""

                        except (ValueError, TypeError):
                            current_cost = original_cost

                    total_with_discount += current_cost

                    html_content += f"""
                    <div style='margin-bottom: 20px;'>
                        <b>Заказ #{order.id}</b> - {order.service}
                        <br>Статус: {order.status}
                        <br>Стоимость: {original_cost:,.2f} ₽
                        {discount_info_html}
                        <br>К оплате: {current_cost:,.2f} ₽
                    </div>
                    <hr>
                    """

                    plain_text += f"""
    Заказ #{order.id} - {order.service}
    Статус: {order.status}
    Стоимость: {original_cost:,.2f} ₽{discount_info_text}
    К оплате: {current_cost:,.2f} ₽
    """

                # Общая информация
                total_savings = total_original - total_with_discount
                summary_html = f"""
                <div style='background-color: #e8f5e9; padding: 10px; border-radius: 5px; margin-top: 20px;'>
                    <h3>Итого:</h3>
                    <p><b>Общая стоимость:</b> {total_original:,.2f} ₽</p>
                    <p><b>К оплате с учетом всех скидок:</b> {total_with_discount:,.2f} ₽</p>
                    <p><b>Ваша экономия при оплате со скидками:</b> {total_savings:,.2f} ₽</p>
                </div>
                """

                summary_text = f"""
    Итого:
    Общая стоимость: {total_original:,.2f} ₽
    К оплате с учетом всех скидок: {total_with_discount:,.2f} ₽
    Ваша экономия при оплате со скидками: {total_savings:,.2f} ₽

    Для оплаты:
    💳 Сбербанк: +79066322571
    📱 WhatsApp: +79066322571
    """

                html_content += summary_html
                plain_text += summary_text

                text_browser.setHtml(html_content)
                layout.addWidget(text_browser)

                # Кнопки
                button_layout = QHBoxLayout()

                copy_btn = QPushButton("📋 Копировать")
                save_pdf_btn = QPushButton("📑 Сохранить PDF")
                whatsapp_btn = QPushButton("📱 Отправить в WhatsApp")
                close_btn = QPushButton("Закрыть")

                button_layout.addWidget(copy_btn)
                button_layout.addWidget(save_pdf_btn)
                button_layout.addWidget(whatsapp_btn)
                button_layout.addWidget(close_btn)
                layout.addLayout(button_layout)

                # Обработчики кнопок
                copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(plain_text))

                save_pdf_btn.clicked.connect(lambda: self.save_orders_to_pdf(
                    self.order_data['fio'],
                    client_orders,
                    total_original,
                    total_with_discount,
                    total_savings
                ))

                whatsapp_btn.clicked.connect(lambda: self.send_to_whatsapp(plain_text))
                close_btn.clicked.connect(dialog.close)

                dialog.setMinimumSize(600, 400)
                dialog.exec_()

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при получении информации о заказах: {str(e)}")

    def save_orders_to_pdf(self, client_name, orders, total_original, total_with_discount, total_savings):
        """Сохранение информации о заказах в PDF"""
        try:
            file_name = f"Заказы_{client_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет",
                file_name,
                "PDF files (*.pdf)"
            )

            if file_path:
                # Регистрируем шрифт
                try:
                    pdfmetrics.registerFont(TTFont('Courier', 'C:\\Windows\\Fonts\\cour.ttf'))
                except:
                    pdfmetrics.registerFont(TTFont('Courier', '/usr/share/fonts/TTF/DejaVuSansMono.ttf'))

                # Создаем документ
                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=(210 * mm, 297 * mm),  # A4
                    rightMargin=25 * mm,
                    leftMargin=25 * mm,
                    topMargin=10 * mm,
                    bottomMargin=10 * mm
                )

                elements = []

                # Стили
                text_style = ParagraphStyle(
                    'CustomText',
                    fontName='Courier',
                    fontSize=12,
                    leading=14,
                    alignment=1
                )

                # Заголовок
                elements.append(Paragraph("ИНФОРМАЦИЯ О ЗАКАЗАХ", text_style))
                elements.append(Paragraph("-" * 50, text_style))

                # Дата и информация о клиенте
                elements.append(Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}", text_style))
                elements.append(Paragraph("-" * 50, text_style))
                elements.append(Paragraph(f"Клиент: {client_name}", text_style))
                elements.append(Paragraph(f"Группа: {self.order_data['group']}", text_style))
                elements.append(Paragraph("-" * 50, text_style))

                # Информация о заказах
                for order in orders:
                    original_cost = order.cost or 0
                    current_cost = original_cost

                    # Создаем таблицу для каждого заказа
                    order_data = [
                        ["ЗАКАЗ №:", str(order.id)],
                        ["Услуга:", order.service],
                        ["Статус:", order.status],
                        ["Стоимость:", f"{original_cost:,.2f} ₽"]
                    ]

                    if order.discount and order.discount != "0%" and order.discount != "Не указано":
                        try:
                            discount_percent = float(order.discount.strip('%'))
                            current_cost = original_cost * (1 - discount_percent / 100)

                            order_data.append(["Скидка:", order.discount])

                            if order.discount_end_date:
                                end_date_str = order.discount_end_date.strftime('%d.%m.%Y %H:%M')
                                time_diff = order.discount_end_date - datetime.now()
                                if time_diff.total_seconds() > 0:
                                    days = time_diff.days
                                    hours = time_diff.seconds // 3600
                                    order_data.append(["Срок скидки до:", end_date_str])
                                    order_data.append(["Осталось:", f"{days}д {hours}ч"])

                        except (ValueError, TypeError):
                            current_cost = original_cost

                    order_data.append(["К оплате:", f"{current_cost:,.2f} ₽"])

                    # Создаем таблицу с более компактными размерами
                    table = Table(order_data, colWidths=[35 * mm, 95 * mm])
                    table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, -1), 'Courier', 12),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # Правое выравнивание для названий
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Левое выравнивание для значений
                        ('TOPPADDING', (0, 0), (-1, -1), 1),  # Уменьшенный отступ сверху
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),  # Уменьшенный отступ снизу
                        ('LEFTPADDING', (0, 0), (0, -1), 5),  # Уменьшенный отступ слева для первой колонки
                        ('RIGHTPADDING', (0, 0), (0, -1), 5),  # Уменьшенный отступ справа для первой колонки
                        ('LEFTPADDING', (1, 0), (1, -1), 5),  # Уменьшенный отступ слева для второй колонки
                        ('RIGHTPADDING', (1, 0), (1, -1), 5),  # Уменьшенный отступ справа для второй колонки
                    ]))

                    elements.append(table)
                    elements.append(Paragraph("-" * 50, text_style))

                # Итоговая информация
                totals_data = [
                    ["ИТОГО:", ""],
                    ["Общая стоимость:", f"{total_original:,.2f} ₽"],
                    ["К оплате со скидками:", f"{total_with_discount:,.2f} ₽"],
                    ["Ваша экономия:", f"{total_savings:,.2f} ₽"]
                ]

                totals_table = Table(totals_data, colWidths=[35 * mm, 95 * mm])
                totals_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Courier', 12),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('TOPPADDING', (0, 0), (-1, -1), 1),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                    ('LEFTPADDING', (0, 0), (0, -1), 5),
                    ('RIGHTPADDING', (0, 0), (0, -1), 5),
                    ('LEFTPADDING', (1, 0), (1, -1), 5),
                    ('RIGHTPADDING', (1, 0), (1, -1), 5),
                ]))

                elements.append(totals_table)
                elements.append(Paragraph("-" * 50, text_style))

                # Информация для оплаты
                elements.append(Paragraph("ДЛЯ ОПЛАТЫ:", text_style))
                elements.append(Paragraph("Сбербанк: +79066322571", text_style))
                elements.append(Paragraph("WhatsApp: +79066322571", text_style))
                elements.append(Paragraph("-" * 50, text_style))

                # Подписи
                signature_data = [
                    ["Подпись:", "_________________"],
                    ["Дата:", "_________________"]
                ]

                signature_table = Table(signature_data, colWidths=[35 * mm, 95 * mm])
                signature_table.setStyle(TableStyle([
                    ('FONT', (0, 0), (-1, -1), 'Courier', 12),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('LEFTPADDING', (0, 0), (0, -1), 5),
                    ('RIGHTPADDING', (0, 0), (0, -1), 5),
                    ('LEFTPADDING', (1, 0), (1, -1), 5),
                    ('RIGHTPADDING', (1, 0), (1, -1), 5),
                ]))

                elements.append(signature_table)

                # Создаем документ
                doc.build(elements)
                QMessageBox.information(self, "Успех", "PDF-файл успешно создан!")

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при создании PDF: {str(e)}")


    def show_discount_info(self):
        """Показ информации о скидке"""
        try:
            with DatabaseManager().session_scope() as session:
                order = session.query(Order).get(self.order_data['id'])
                if not order:
                    show_error(self, "Ошибка", "Заказ не найден")
                    return

                discount_info = f"Информация о скидке для заказа #{order.id}\n\n"

                if not order.discount or order.discount == "0%" or order.discount == "Не указано":
                    discount_info += "У заказа нет активной скидки"
                else:
                    discount_info += f"Размер скидки: {order.discount}\n"
                    if order.discount_start_date:
                        discount_info += f"Дата начала: {order.discount_start_date.strftime('%d.%m.%Y %H:%M')}\n"
                    if order.discount_end_date:
                        discount_info += f"Дата окончания: {order.discount_end_date.strftime('%d.%m.%Y %H:%M')}\n"

                    # Проверяем осталось ли время
                    if order.discount_end_date:
                        now = datetime.now()
                        time_diff = order.discount_end_date - now
                        if time_diff.total_seconds() > 0:
                            days = time_diff.days
                            hours = time_diff.seconds // 3600
                            discount_info += f"\nОсталось времени: {days} дней {hours} часов"
                        else:
                            discount_info += "\nСрок действия скидки истек"

                QMessageBox.information(self, "Информация о скидке", discount_info)

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при получении информации о скидке: {str(e)}")

    def show_discount_reminder(self):
        """Показ окна напоминания об истечении срока скидки"""
        try:
            # Проверяем наличие дат скидки
            if not hasattr(self, 'order_data') or not self.order_data.get('discount_end_date'):
                QMessageBox.warning(self, "Предупреждение", "У заказа не установлен срок скидки")
                return

            # Получаем и преобразуем даты
            end_date = self.order_data['discount_end_date']

            # Если end_date уже datetime, используем его как есть
            if isinstance(end_date, datetime):
                # Не преобразовываем, используем как есть
                pass
            elif isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
            elif isinstance(end_date, date):
                end_date = datetime.combine(end_date, time(15, 37, 53))  # используем оригинальное время

            now = datetime.now()
            time_diff = end_date - now

            if time_diff.total_seconds() <= 0:
                QMessageBox.warning(self, "Предупреждение", "Срок скидки уже истек")
                return

            # Преобразуем разницу во времени в часы, округляя до ближайшего часа
            total_hours = time_diff.total_seconds() / 3600

            # Рассчитываем дни и оставшиеся часы
            days = int(total_hours) // 24
            hours = int(total_hours) % 24
            minutes = int((total_hours * 60) % 60)


            # Расчет сумм
            base_cost = float(self.order_data['cost'])  # Исходная стоимость
            paid_amount = float(self.order_data.get('paid_amount', 0))  # Уже оплачено
            remaining_without_discount = base_cost - paid_amount  # Остаток без скидки

            # Расчет суммы со скидкой
            discount_percent = float(self.order_data['discount'].strip('%'))
            discounted_total = base_cost * (1 - discount_percent / 100)  # Полная сумма со скидкой
            remaining_with_discount = discounted_total - paid_amount  # Остаток со скидкой

            savings = remaining_without_discount - remaining_with_discount  # Экономия

            # Формируем сообщение
            message = (
                f"Уважаемый(ая) {self.order_data['fio']}!\n\n"
                f"Напоминаем, что по заказу #{self.order_data['id']} "
                f"({self.order_data['service']}) у вас действует скидка {self.order_data['discount']}.\n\n"
                f"До истечения срока скидки осталось: {days}д {hours}ч {minutes}м\n\n"
                f"К оплате со скидкой: {remaining_with_discount:,.2f} ₽\n"
                f"К оплате без скидки: {remaining_without_discount:,.2f} ₽\n"
                f"Ваша экономия: {savings:,.2f} ₽\n\n"
                f"Рекомендуем внести оплату до истечения срока действия скидки "
                f"({end_date.strftime('%d.%m.%Y %H:%M')}), "
                f"чтобы сохранить возможность оплаты со скидкой.\n\n"
                "Для оплаты:\n"
                "💳 Сбербанк: +79066322571\n"
                "📱 WhatsApp: +79066322571\n\n"
                "С уважением,\n"
                "Гурбанмурадов Мукам\n"
                "ООО MPSP"
            )

            # Создаем диалоговое окно
            dialog = QDialog(self)
            dialog.setWindowTitle("Напоминание о скидке")
            layout = QVBoxLayout(dialog)

            # Поле с текстом сообщения
            text_edit = QTextEdit()
            text_edit.setPlainText(message)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            # Кнопки действий
            button_layout = QHBoxLayout()

            copy_btn = QPushButton("📋 Копировать")
            whatsapp_btn = QPushButton("📱 Отправить в WhatsApp")
            close_btn = QPushButton("❌ Закрыть")

            button_layout.addWidget(copy_btn)
            button_layout.addWidget(whatsapp_btn)
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)

            # Обработчики кнопок
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(message))
            whatsapp_btn.clicked.connect(lambda: self.send_to_whatsapp(message))
            close_btn.clicked.connect(dialog.close)

            dialog.setMinimumWidth(500)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании напоминания: {str(e)}")

    def print_receipt(self):
        """Печать кассового чека прямо из карточки заказа"""
        try:
            with DatabaseManager().session_scope() as session:
                # Получаем свежую копию заказа
                order = session.query(Order).get(self.order_data['id'])

                # Создаем имя файла
                file_name = f"Чек_{order.fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Сохранить чек",
                    file_name,
                    "PDF files (*.pdf)"
                )

                if file_path:
                    # Импортируем необходимые модули для PDF
                    from reportlab.lib import colors
                    from reportlab.lib.units import mm
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont

                    # Регистрируем шрифт
                    try:
                        pdfmetrics.registerFont(TTFont('Courier', 'C:\\Windows\\Fonts\\cour.ttf'))
                    except:
                        pdfmetrics.registerFont(TTFont('Courier', '/usr/share/fonts/TTF/DejaVuSansMono.ttf'))

                    # Создаем документ
                    doc = SimpleDocTemplate(
                        file_path,
                        pagesize=(140 * mm, 280 * mm),
                        rightMargin=5 * mm,
                        leftMargin=5 * mm,
                        topMargin=5 * mm,
                        bottomMargin=5 * mm
                    )

                    elements = []

                    # Стили
                    title_style = ParagraphStyle(
                        'CashTitle',
                        fontName='Courier',
                        fontSize=20,
                        alignment=1,
                        spaceAfter=4 * mm,
                        leading=24
                    )

                    text_style = ParagraphStyle(
                        'CashText',
                        fontName='Courier',
                        fontSize=14,
                        leading=16,
                        alignment=1
                    )

                    # Заголовок
                    elements.append(Paragraph("КАССОВЫЙ ЧЕК", title_style))
                    elements.append(Paragraph("ООО MPSP", text_style))
                    elements.append(Paragraph(f"Тел: +7 906 632-25-71", text_style))
                    elements.append(Paragraph("-" * 42, text_style))

                    # Дата и время
                    current_time = datetime.now().strftime('%d-%m-%Y %H:%M')
                    elements.append(Paragraph(f"Дата: {current_time}", text_style))
                    elements.append(Paragraph("-" * 42, text_style))

                    # Информация о заказе
                    data = [
                        ["ФИО:", order.fio],
                        ["Группа:", order.group],
                        ["Дата заказа:",
                         order.created_date.strftime('%d-%m-%Y') if order.created_date else 'Не указано'],
                        ["Срок:", order.deadline or 'Не указано'],
                        ["Услуга:", order.service],
                        ["Скидка:", f"{order.discount}" if order.discount else "Не указано"],
                        ["Стоимость:", f"{order.cost:,.2f} ₽"],
                        ["Оплачено:", f"{order.paid_amount:,.2f} ₽"],
                        ["Остаток:", f"{order.remaining_amount:,.2f} ₽"],
                        ["Статус:", order.status]
                    ]

                    # Создаем таблицу
                    table = Table(data, colWidths=[40 * mm, 90 * mm])
                    table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, -1), 'Courier', 14),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                    ]))

                    elements.append(table)
                    elements.append(Paragraph("-" * 42, text_style))

                    # Итоги
                    total_data = [
                        ["ИТОГО:", f"{order.cost:,.2f} ₽"],
                        ["Оплачено:", f"{order.paid_amount:,.2f} ₽"],
                        ["Остаток:", f"{order.remaining_amount:,.2f} ₽"]
                    ]

                    total_table = Table(total_data, colWidths=[70 * mm, 60 * mm])
                    total_table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, -1), 'Courier', 16),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ]))

                    elements.append(total_table)
                    elements.append(Paragraph("-" * 42, text_style))

                    # Информация для оплаты
                    elements.append(Paragraph("ДЛЯ ОПЛАТЫ:", text_style))
                    elements.append(Paragraph("Сбербанк: +79066322571", text_style))
                    elements.append(Paragraph("WhatsApp: +79066322571", text_style))
                    elements.append(Paragraph("-" * 42, text_style))

                    # Подписи
                    signature_data = [
                        ["Подпись:", "_________________"],
                        ["Дата:", "_________________"]
                    ]

                    signature_table = Table(signature_data, colWidths=[40 * mm, 90 * mm])
                    signature_table.setStyle(TableStyle([
                        ('FONT', (0, 0), (-1, -1), 'Courier', 14),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ]))

                    elements.append(signature_table)

                    # Создаем документ
                    doc.build(elements)
                    QMessageBox.information(self, "Успех", "Чек успешно создан!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании чека: {str(e)}")

    def print_invoice(self):
        """Создание PDF квитанции прямо из карточки заказа"""
        try:
            with DatabaseManager().session_scope() as session:
                # Получаем свежую копию заказа
                order = session.query(Order).get(self.order_data['id'])

                # Создаем имя файла
                file_name = f"Квитанция_{order.fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Сохранить квитанцию",
                    file_name,
                    "PDF files (*.pdf)"
                )

                if file_path:
                    from reportlab.lib import colors
                    from reportlab.lib.pagesizes import letter
                    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
                    from reportlab.lib.units import inch

                    # Регистрируем шрифт Arial
                    try:
                        pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
                    except:
                        pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/TTF/DejaVuSans.ttf'))

                    doc = SimpleDocTemplate(
                        file_path,
                        pagesize=letter,
                        rightMargin=30,
                        leftMargin=30,
                        topMargin=30,
                        bottomMargin=30
                    )

                    elements = []
                    styles = getSampleStyleSheet()

                    # Создаем стили
                    title_style = ParagraphStyle(
                        'CustomTitle',
                        parent=styles['Heading1'],
                        fontSize=16,
                        spaceAfter=30,
                        alignment=1,
                        fontName='Arial'
                    )

                    normal_style = ParagraphStyle(
                        'CustomNormal',
                        parent=styles['Normal'],
                        fontSize=12,
                        fontName='Arial'
                    )

                    # Заголовок квитанции
                    elements.append(Paragraph("Квитанция об оплате", title_style))
                    elements.append(Spacer(1, 20))

                    # Данные квитанции
                    receipt_data = [
                        ["Номер квитанции:", datetime.now().strftime('%Y%m%d%H%M%S')],
                        ["Дата:", datetime.now().strftime('%d.%m.%Y %H:%M')],
                        ["ФИО клиента:", order.fio],
                        ["Группа:", order.group],
                        ["Телефон:", order.phone or "Не указан"],
                        ["Тема:", order.theme or "Не указано"],
                        ["Услуга:", order.service],
                        ["Стоимость:", f"{order.cost:,.2f} ₽"],
                        ["Оплачено:", f"{order.paid_amount:,.2f} ₽"],
                        ["Остаток:", f"{order.remaining_amount:,.2f} ₽"],
                        ["Статус:", order.status]
                    ]

                    # Создаем таблицу с данными квитанции
                    table = Table(receipt_data, colWidths=[150, 300])
                    table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ]))

                    elements.append(table)
                    elements.append(Spacer(1, 40))

                    # Подпись
                    signature_data = [
                        ["Подпись оператора:", "_________________"],
                        ["Подпись клиента:", "_________________"]
                    ]
                    signature_table = Table(signature_data, colWidths=[150, 300])
                    signature_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
                    ]))
                    elements.append(signature_table)

                    # Добавляем информацию о компании
                    company_style = ParagraphStyle(
                        'Company',
                        parent=styles['Normal'],
                        fontSize=14,
                        alignment=1,
                        spaceAfter=10,
                        fontName='Arial'
                    )

                    elements.append(Spacer(1, 20))
                    elements.append(Paragraph("-" * 100, company_style))
                    elements.append(Spacer(1, 20))

                    elements.append(Paragraph("ООО MPSP", company_style))
                    elements.append(Paragraph("WhatsApp: +79066322571", company_style))
                    elements.append(Paragraph("Для перевода: +79066322571 Сбербанк", company_style))

                    # Строим документ
                    doc.build(elements)
                    QMessageBox.information(self, "Успех", "Квитанция успешно создана!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании квитанции: {str(e)}")

    def show_total_debt_reminder(self):
        """Показ окна напоминания об общем долге с учетом скидок"""
        try:
            with DatabaseManager().session_scope() as session:
                # Получаем все заказы клиента с долгами, кроме отмененных
                client_orders = session.query(Order).filter(
                    Order.fio == self.order.fio,
                    ~Order.status.in_(['Отменен', 'Отказ'])
                ).all()

                # Считаем общий долг с учетом скидок
                total_debt = 0
                orders_with_debt = []  # Список для хранения деталей о заказах с долгами

                for order in client_orders:
                    # Расчет фактической стоимости с учетом скидки
                    actual_cost = order.cost
                    if order.discount and order.discount != "Не указано" and order.discount != "0%":
                        try:
                            discount_percent = float(order.discount.strip('%'))
                            actual_cost = order.cost * (1 - discount_percent / 100)
                        except (ValueError, AttributeError):
                            pass

                    # Расчет реального долга
                    remaining_debt = max(0, actual_cost - order.paid_amount)

                    if remaining_debt > 0:
                        total_debt += remaining_debt
                        orders_with_debt.append({
                            'id': order.id,
                            'service': order.service,
                            'debt': remaining_debt,
                            'deadline': order.deadline or 'Не указан'
                        })

                if total_debt > 0:
                    # Формируем детальное описание долгов
                    debt_details = "\nПодробности по заказам:\n"
                    for order_info in orders_with_debt:
                        debt_details += (f"Заказ №{order_info['id']} - {order_info['service']}\n"
                                         f"Остаток: {order_info['debt']:,.2f} руб.\n"
                                         f"Срок: {order_info['deadline']}\n")

                    message = (f"Уважаемый(ая) {self.order.fio}!\n\n"
                               f"Напоминаем, что у вас есть неоплаченные заказы "
                               f"на общую сумму {total_debt:,.2f} руб.\n"
                               f"{debt_details}\n"
                               "Для оплаты вы можете использовать:\n"
                               "💳 Сбербанк: +79066322571\n"
                               "📱 WhatsApp: +79066322571\n\n"
                               "С уважением,\nГурбанмурадов Мукам\nООО MPSP")

                    self.show_message_dialog("Напоминание об общем долге", message)
                else:
                    QMessageBox.information(
                        self,
                        "Информация",
                        "У клиента нет неоплаченных заказов с учетом всех скидок."
                    )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании напоминания: {str(e)}")


    def closeEvent(self, event):
        OrderWindowManager.get_instance().cleanup_all()
        super().closeEvent(event)

    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QEvent.HoverEnter:
                # Формируем текст подсказки
                tooltip_text = f"""
                <div style='background-color: {self.style['bg']}; 
                            padding: 10px; 
                            border: 1px solid {self.style['border']}; 
                            border-radius: 4px;'>
                    <p><b>Номер заказа:</b> #{self.order_data['id']}</p>
                    <p><b>ФИО:</b> {self.order_data['fio']}</p>
                    <p><b>Логин:</b> {self.order_data.get('login', 'Не указан 11')}</p>
                    <p><b>Тема:</b> {self.order_data.get('theme', 'Не указана')}</p>
                    <p><b>Комментарии:</b> {self.order_data.get('comment', 'Нет комментариев')}</p>
                </div>
                """

                # Устанавливаем подсказку
                self.setToolTip(tooltip_text)

            elif event.type() == QEvent.HoverLeave:
                # Убираем подсказку при уходе мыши
                self.setToolTip("")

        return super().eventFilter(obj, event)


    def show_thanks_message(self):
        """Показ окна благодарственного сообщения"""
        message = (f"Уважаемый(ая) {self.order.fio}!\n\n"
                   f"Благодарим вас за обращение в нашу компанию. "
                   f"Надеемся, что качество нашей работы вас полностью устроило.\n\n"
                   f"Будем рады видеть вас снова!\n\n"
                   "С уважением,\nГурбанмурадов Мукам\n ООО ""MPSP""")

        self.show_message_dialog("Благодарственное сообщение", message)

    def show_follow_up_message(self):
        """Показ окна сообщения о том, как дела"""
        message = (f"Здравствуйте, {self.order.fio}!\n\n"
                   f"Как у вас дела? Хотели уточнить, всё ли в порядке с выполненной работой?\n"
                   f"Если есть какие-то вопросы или пожелания, будем рады помочь.\n\n"
                   "С уважением,\nГурбанмурадов Мукам\n ООО ""MPSP""")

        self.show_message_dialog("Уточняющее сообщение", message)

    def show_message_dialog(self, title, message):
        """Общий метод для показа диалога с сообщением"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setPlainText(message)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        button_layout = QHBoxLayout()

        copy_btn = QPushButton("📋 Копировать")
        whatsapp_btn = QPushButton("📱 Отправить в WhatsApp")
        close_btn = QPushButton("❌ Закрыть")

        button_layout.addWidget(copy_btn)
        button_layout.addWidget(whatsapp_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        def send_whatsapp():
            try:
                if not self.order.phone:
                    QMessageBox.warning(dialog, "Предупреждение", "У клиента не указан номер телефона!")
                    return

                phone = self.order.phone.strip()
                # Форматируем номер телефона
                phone = re.sub(r'[^\d]', '', phone)
                if phone.startswith('8'):
                    phone = '7' + phone[1:]
                elif not phone.startswith('7'):
                    phone = '7' + phone

                # Формируем URL для WhatsApp
                url = f"https://wa.me/{phone}?text={quote(message)}"
                QDesktopServices.openUrl(QUrl(url))
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка отправки сообщения: {str(e)}")

        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(message))
        whatsapp_btn.clicked.connect(send_whatsapp)
        close_btn.clicked.connect(dialog.close)

        dialog.setMinimumWidth(400)
        dialog.exec_()

    def open_client_folder(self):
        """Открытие папки клиента"""
        import os
        import subprocess
        try:
            # Создаём путь к папке клиента
            base_path = os.path.expanduser('D:\\Users\\mgurbanmuradov\\Documents\\Общая')
            client_folder = os.path.join(base_path, self.order_data['fio'])

            # Создаём папку, если она не существует
            os.makedirs(client_folder, exist_ok=True)

            # Открываем папку
            if os.name == 'nt':  # Windows
                os.startfile(client_folder)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', client_folder])

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при открытии папки: {str(e)}")

    def create_client_folder(self):
        """Создание структуры папок для клиента"""
        import os
        try:
            # Базовый путь
            base_path = os.path.expanduser('D:\\Users\\mgurbanmuradov\\Documents\\Общая')
            client_folder = os.path.join(base_path, self.order.fio)

            # Создаём основные папки
            folders = [
                "Документы",
                "Работы",
                "Черновики",
                "Материалы"
            ]

            for folder in folders:
                folder_path = os.path.join(client_folder, folder)
                os.makedirs(folder_path, exist_ok=True)

            QMessageBox.information(self, "Успех", "Структура папок создана успешно")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании папок: {str(e)}")

    def open_works_folder(self):
        """Открытие папки с работами клиента"""
        import os
        import subprocess
        try:
            base_path = os.path.expanduser('D:\\Users\\mgurbanmuradov\\Documents\\Общая')
            works_folder = os.path.join(base_path, self.order.fio, "Работы")

            # Создаём папку, если она не существует
            os.makedirs(works_folder, exist_ok=True)

            # Открываем папку
            if os.name == 'nt':  # Windows
                os.startfile(works_folder)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', works_folder])

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при открытии папки: {str(e)}")

    def show_client_history(self):
        """Показ истории заказов клиента"""
        try:
            with DatabaseManager().session_scope() as session:
                orders = session.query(Order).filter(
                    Order.fio == self.order.fio
                ).order_by(Order.created_date.desc()).all()

                dialog = QDialog(self)
                dialog.setWindowTitle(f"История заказов - {self.order.fio}")
                layout = QVBoxLayout(dialog)

                text_browser = QTextBrowser()
                html_content = f"<h2>История заказов {self.order.fio}</h2>"

                for order in orders:
                    html_content += f"""
                    <p><b>Заказ #{order.id}</b></p>
                    <ul>
                        <li>Услуга: {order.service}</li>
                        <li>Дата: {order.created_date.strftime('%d.%m.%Y')}</li>
                        <li>Статус: {order.status}</li>
                        <li>Стоимость: {order.cost:.2f} руб.</li>
                        <li>Оплачено: {order.paid_amount:.2f} руб.</li>
                        <li>Остаток: {order.remaining_amount:.2f} руб.</li>
                    </ul>
                    <hr>
                    """

                text_browser.setHtml(html_content)
                layout.addWidget(text_browser)

                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(dialog.close)
                layout.addWidget(close_btn)

                dialog.setMinimumSize(500, 400)
                dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при получении истории: {str(e)}")

    def print_contract(self):
        """Создание и печать договора"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from datetime import datetime
            from PyQt5.QtWidgets import QFileDialog

            # Регистрируем шрифт
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
            except:
                pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/TTF/DejaVuSans.ttf'))

            # Создаем имя файла
            file_name = f"Договор_{self.order.fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить договор",
                file_name,
                "PDF files (*.pdf)"
            )

            if file_path:
                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=A4,
                    rightMargin=72,
                    leftMargin=72,
                    topMargin=72,
                    bottomMargin=72
                )

                # Создаем стили
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontName='Arial',
                    fontSize=14,
                    spaceAfter=30,
                    alignment=1
                )

                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontName='Arial',
                    fontSize=12,
                    spaceBefore=6,
                    spaceAfter=6
                )

                elements = []

                # Заголовок договора
                elements.append(Paragraph("ДОГОВОР НА ОКАЗАНИЕ УСЛУГ", title_style))
                elements.append(Paragraph(f"№ {self.order.id}", title_style))
                elements.append(Paragraph(
                    f"г. Акдепе                                                                           {datetime.now().strftime('%d.%m.%Y')}",
                    normal_style))
                elements.append(Spacer(1, 20))

                # Текст договора
                contract_text = f"""
                Общество с ограниченной ответственностью "MPSP", именуемое в дальнейшем «Исполнитель», 
                в лице директора Гурбанмурадова М.Р., действующего на основании Устава, с одной стороны, 
                и {self.order.fio}, именуемый(ая) в дальнейшем «Заказчик», с другой стороны, 
                заключили настоящий Договор о нижеследующем:

                1. ПРЕДМЕТ ДОГОВОРА
                1.1. Исполнитель обязуется оказать услуги по {self.order.service}, 
                а Заказчик обязуется принять и оплатить эти услуги.

                2. СТОИМОСТЬ УСЛУГ И ПОРЯДОК РАСЧЕТОВ
                2.1. Стоимость услуг составляет {self.order.cost:,.2f} рублей.
                2.2. Оплата производится в следующем порядке:
                    - Предоплата в размере {self.order.paid_amount:,.2f} рублей
                    - Оставшаяся сумма {self.order.remaining_amount:,.2f} рублей оплачивается после выполнения работы

                3. СРОКИ ВЫПОЛНЕНИЯ
                3.1. Срок выполнения работ: {self.order.deadline}
                4. РЕКВИЗИТЫ И ПОДПИСИ СТОРОН
                """

                # Добавляем текст договора
                for paragraph in contract_text.split('\n'):
                    elements.append(Paragraph(paragraph.strip(), normal_style))

                elements.append(Spacer(1, 20))

                # Создаем таблицу для реквизитов и подписей
                signature_data = [
                    ['Исполнитель:', 'Заказчик:'],
                    ['ООО "MPSP"', self.order.fio],
                    ['Тел: +7 906 632-25-71', f'Тел: {self.order.phone or "_______________"}'],
                    ['Адрес: г. Акдепе', f'Группа: {self.order.group}'],

                    ['', ''],  # Пустая строка для отступа
                    ['__________________', '__________________'],
                    ['М.Р. Гурбанмурадов', self.order.fio]
                ]

                # Создаем таблицу
                signature_table = Table(signature_data, colWidths=[doc.width / 2.2] * 2)
                signature_table.setStyle(TableStyle([
                    # Выравнивание текста
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Левая колонка - по левому краю
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # Правая колонка - по левому краю

                    # Отступы внутри ячеек
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),

                    # Шрифт
                    ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),

                    # Выделение заголовков (используем просто Arial, так как Arial-Bold не зарегистрирован)
                    ('FONTSIZE', (0, 0), (1, 0), 13),  # Немного увеличиваем размер для заголовков

                    # Без границ
                    ('GRID', (0, 0), (-1, -1), 0, colors.white),

                    # Отступ перед линиями для подписи
                    ('TOPPADDING', (0, 6), (-1, 6), 30),
                ]))

                elements.append(signature_table)

                # Строим документ
                doc.build(elements)
                QMessageBox.information(self, "Успех", "Договор успешно создан!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании договора: {str(e)}")

    def create_new_order_for_client(self):
        """Создание нового заказа для текущего клиента"""
        try:
            # Получаем данные существующего заказа
            existing_order_data = None
            with DatabaseManager().session_scope() as session:
                current_order = session.query(Order).get(self.order_data['id'])
                if current_order:
                    existing_order_data = {
                        'fio': current_order.fio,
                        'group': current_order.group,
                        'phone': current_order.phone or '',
                        'teacher_name': current_order.teacher_name or '',
                        'teacher_email': current_order.teacher_email or '',
                        'login': current_order.login or '',
                        'password': current_order.password or '',
                        'website': current_order.website or ''
                    }
                else:
                    raise ValueError("Заказ не найден")

            # Создаем новое окно заказа
            dialog = NewOrderWindow(self, None)

            # Устанавливаем фиксированные размеры окна
            dialog.setMinimumWidth(900)
            dialog.setMinimumHeight(800)

            # Центрируем окно относительно основного окна приложения
            if self.window():
                center = self.window().frameGeometry().center()
                # Округляем координаты до целых чисел
                x = int(center.x() - dialog.width() // 2)
                y = int(center.y() - dialog.height() // 2)
                dialog.move(x, y)

            # Если есть данные предыдущего заказа - заполняем поля
            if existing_order_data:
                dialog.fio_input.setText(existing_order_data['fio'])
                dialog.group_input.setText(existing_order_data['group'])
                dialog.phone_input.setText(existing_order_data['phone'])
                dialog.teacher_input.setText(existing_order_data['teacher_name'])
                dialog.teacher_email_input.setText(existing_order_data['teacher_email'])
                dialog.login_input.setText(existing_order_data['login'])
                dialog.password_input.setText(existing_order_data['password'])
                dialog.website_input.setText(existing_order_data['website'])

                # Вызываем обработчик изменения ФИО для загрузки информации о клиенте
                dialog.on_fio_changed(existing_order_data['fio'])

            # Показываем диалог
            if dialog.exec_() == QDialog.Accepted:
                # Обновляем канбан-доску
                parent = self
                while parent is not None:
                    if hasattr(parent, 'loadOrders'):
                        parent.loadOrders()
                        break
                    parent = parent.parent()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании заказа: {str(e)}")

    def show_debt_reminder(self):
        """Показ окна напоминания о долге"""
        try:
            if not hasattr(self, 'order') or not self.order:
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Напоминание о долге")
            layout = QVBoxLayout(dialog)

            # Информация о долге
            info_label = QLabel(f"Клиент: {self.order.fio}\n"
                                f"Сумма долга: {self.order.remaining_amount:.2f} руб.")
            layout.addWidget(info_label)

            # Поле для сообщения
            message_edit = QTextEdit()
            default_message = (f"Уважаемый(ая) {self.order.fio}!\n\n"
                               f"Напоминаем о необходимости оплаты задолженности "
                               f"по заказу №{self.order.id} в размере {self.order.remaining_amount:.2f} руб.\n\n"
                               "Для оплаты:\n"
                               "💳 Сбербанк: +79066322571\n"
                               "📱 WhatsApp: +79066322571\n\n"
                               "С уважением,\nГурбанмурадов Мукам\nООО MPSP")
            message_edit.setText(default_message)
            layout.addWidget(message_edit)

            # Кнопки
            button_layout = QHBoxLayout()

            copy_btn = QPushButton("📋 Копировать")
            whatsapp_btn = QPushButton("📱 Отправить в WhatsApp")
            close_btn = QPushButton("❌ Закрыть")

            button_layout.addWidget(copy_btn)
            button_layout.addWidget(whatsapp_btn)
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)

            # Обработчики
            def copy_to_clipboard():
                QApplication.clipboard().setText(message_edit.toPlainText())
                QMessageBox.information(dialog, "Успех", "Текст скопирован в буфер обмена")

            def send_to_whatsapp():
                if not self.order.phone:
                    QMessageBox.warning(dialog, "Предупреждение", "У клиента не указан номер телефона!")
                    return

                phone = re.sub(r'[^\d]', '', self.order.phone)
                if phone.startswith('8'):
                    phone = '7' + phone[1:]
                elif not phone.startswith('7'):
                    phone = '7' + phone

                message = quote(message_edit.toPlainText())
                url = f"https://wa.me/{phone}?text={message}"
                QDesktopServices.openUrl(QUrl(url))

            copy_btn.clicked.connect(copy_to_clipboard)
            whatsapp_btn.clicked.connect(send_to_whatsapp)
            close_btn.clicked.connect(dialog.close)

            dialog.setMinimumWidth(400)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании напоминания: {str(e)}")

    def on_status_changed(self, order_id, new_status, old_status=None):
        try:
            if self and self.parent():  # Проверяем существование объекта и родителя
                self.parent().parent().parent().parent().loadOrders()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении статуса: {str(e)}")

    def add_comment(self):
        """Добавление комментария к заказу"""
        if not hasattr(self, 'order') or not self.order:
            return

        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление комментария")
        layout = QVBoxLayout(dialog)

        # Поле для комментария
        comment_edit = QTextEdit()
        if self.order.comment:
            comment_edit.setText(self.order.comment)
        layout.addWidget(comment_edit)

        # Кнопки
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        def save_comment():
            try:
                with DatabaseManager().session_scope() as session:
                    order = session.query(Order).get(self.order.id)
                    if order:
                        order.comment = comment_edit.toPlainText()
                        session.commit()
                        QMessageBox.information(dialog, "Успех", "Комментарий сохранен")
                        dialog.accept()
            except Exception as e:
                QMessageBox.critical(dialog, "Ошибка", f"Ошибка при сохранении комментария: {str(e)}")

        save_btn.clicked.connect(save_comment)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.setMinimumWidth(400)
        dialog.exec_()

    def send_review_request(self):
        """Генерация и отправка ссылки для отзыва"""
        try:
            if not self.order:
                show_error(self, "Ошибка", "Информация о заказе недоступна")
                return

            # Проверяем статус заказа
            if self.order.status != 'Выполнен':
                show_warning(self, "Предупреждение", "Отзыв можно запросить только для выполненных заказов")
                return

            # Проверяем, есть ли номер телефона
            if not self.order.phone:
                reply = QMessageBox.question(
                    self,
                    "Отсутствует номер телефона",
                    "У клиента не указан номер телефона. Хотите ввести его сейчас?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    phone, ok = QInputDialog.getText(
                        self,
                        "Ввод номера телефона",
                        "Введите номер телефона клиента:"
                    )
                    if ok and phone:
                        # Сохраняем новый номер телефона
                        with DatabaseManager().session_scope() as session:
                            updated_order = session.query(Order).get(self.order.id)
                            if updated_order:
                                updated_order.phone = phone
                                session.commit()
                                self.order.phone = phone
                    else:
                        show_warning(self, "Предупреждение", "Без номера телефона невозможно отправить сообщение")
                        return
                else:
                    show_warning(self, "Предупреждение", "Без номера телефона невозможно отправить сообщение")
                    return

            with DatabaseManager().session_scope() as session:
                # Проверяем, есть ли уже сгенерированная ссылка для отзыва
                order = session.query(Order).get(self.order.id)
                review_link = ""

                if order.review_token:
                    # Если токен уже существует, формируем ссылку заново
                    print(f"У заказа #{order.id} уже есть токен для отзыва: {order.review_token}")

                    # Кодируем параметры для URL
                    service_encoded = urllib.parse.quote(order.service)
                    name_encoded = urllib.parse.quote(order.fio)

                    # Формируем ссылку
                    # Получаем данные из конфигурации
                    from reviews_manager.config import SITE_CONFIG
                    base_url = SITE_CONFIG.get('base_url', 'https://mpsp.online')
                    reviews_page = SITE_CONFIG.get('reviews_page', '/submit-review.html')

                    # Формируем полную ссылку
                    review_link = f"{base_url}{reviews_page}?token={order.review_token}&order={order.id}&service={service_encoded}&name={name_encoded}"

                else:
                    # Генерируем новый токен и ссылку
                    token = str(uuid.uuid4())
                    order.review_token = token
                    session.commit()

                    # Кодируем параметры для URL
                    service_encoded = urllib.parse.quote(order.service)
                    name_encoded = urllib.parse.quote(order.fio)

                    # Формируем ссылку
                    # Получаем данные из конфигурации
                    from reviews_manager.config import SITE_CONFIG
                    base_url = SITE_CONFIG.get('base_url', 'https://mpsp.online')
                    reviews_page = SITE_CONFIG.get('reviews_page', '/submit-review.html')

                    # Формируем полную ссылку
                    review_link = f"{base_url}{reviews_page}?token={token}&order={order.id}&service={service_encoded}&name={name_encoded}"
                    print(f"Создана новая ссылка для отзыва для заказа #{order.id}")

                # Сокращаем ссылку
                shortened_link = self.shorten_url(review_link)
                if not shortened_link:
                    shortened_link = review_link

                # Создаем диалог для выбора типа сообщения
                template_msg = QMessageBox()
                template_msg.setWindowTitle("Выбор шаблона")
                template_msg.setText("Выберите шаблон для запроса отзыва:")

                formal_btn = template_msg.addButton("Формальный", QMessageBox.ActionRole)
                friendly_btn = template_msg.addButton("Дружелюбный", QMessageBox.ActionRole)
                short_btn = template_msg.addButton("Короткий", QMessageBox.ActionRole)
                cancel_btn = template_msg.addButton("Отмена", QMessageBox.RejectRole)

                template_msg.exec_()

                # Определяем дату первого заказа и количество заказов
                earliest_date = order.created_date
                total_orders = 1

                # Получаем все заказы клиента для определения первого заказа и общего количества
                client_orders = session.query(Order).filter(Order.fio == order.fio).all()
                if client_orders:
                    total_orders = len(client_orders)
                    for client_order in client_orders:
                        if client_order.created_date and (
                                not earliest_date or client_order.created_date < earliest_date):
                            earliest_date = client_order.created_date

                # Форматируем дату для отображения
                earliest_date_str = earliest_date.strftime('%d.%m.%Y') if earliest_date else "недавно"

                # Вычисляем количество дней сотрудничества
                days_waiting = 0
                if earliest_date:
                    days_waiting = (datetime.now().date() - earliest_date).days if isinstance(earliest_date,
                                                                                              date) else 0

                # Определяем выбранный шаблон
                if template_msg.clickedButton() == formal_btn:
                    message = (
                        "🌟 Здравствуйте, {client_name}! 🌟\n\n"
                        "Вы с нами уже с {earliest_date}, и за это время оформили {total_orders} заказ(ов). "
                        "Спасибо за доверие! 🙏\n\n"
                        "Нам очень важно Ваше мнение. Пожалуйста, поделитесь своими впечатлениями о нашей работе, "
                        "оставив отзыв по ссылке:\n"
                        "👇👇👇\n"
                        "{review_link}\n"
                        "👆👆👆\n\n"
                        "Ваш отзыв поможет нам стать еще лучше! ✨\n\n"
                        "С уважением,\n"
                        "Команда MPSP 💼"
                    )
                elif template_msg.clickedButton() == friendly_btn:
                    message = (
                        "Привет, {client_name}! 👋\n\n"
                        "Ты с нами уже с {earliest_date} - это целых {days_waiting} дней дружбы! 🤗\n"
                        "Мы тут подумали... 🤔 А что если ты расскажешь, как тебе с нами работается?\n"
                        "Буквально пару слов - хорошо, плохо, что понравилось, а что нет.\n\n"
                        "Вот тут можно оставить отзыв 👇👇👇\n"
                        "{review_link}\n"
                        "☝️ Жми на ссылку! ☝️\n\n"
                        "P.S. Мы обещаем не плакать... ну, только если отзыв будет супер-крутой! 😎\n"
                        "Твоя команда MPSP 🚀"
                    )
                elif template_msg.clickedButton() == short_btn:
                    message = (
                        "Хей, {client_name}! 👋\n\n"
                        "Ты наш клиент уже {days_waiting} дней - круто! 🎉\n"
                        "Черкни пару слов о нашей работе:\n"
                        "👇\n"
                        "{review_link}\n"
                        "👆\n\n"
                        "Твое мнение реально важно! 💪\n"
                        "Команда MPSP ✌️"
                    )
                else:
                    # Пользователь нажал отмена
                    return

                # Заменяем переменные в сообщении
                message = message.format(
                    client_name=order.fio,
                    earliest_date=earliest_date_str,
                    total_orders=total_orders,
                    days_waiting=days_waiting,
                    review_link=shortened_link
                )

                # Отправляем сообщение в WhatsApp
                self.send_to_whatsapp(message)

                QMessageBox.information(self, "Успех", "Запрос на отзыв успешно отправлен!")

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при отправке запроса на отзыв: {str(e)}")

    def shorten_url(self, url):
        """Сокращение URL с использованием API сервиса"""
        try:
            # Здесь вы можете использовать различные API для сокращения URL
            # Например, TinyURL, Bitly и т.д.
            # Для демонстрации мы просто возвращаем исходный URL

            # Пример использования TinyURL API (бесплатный, без требования ключа)
            import requests
            response = requests.get(f"https://tinyurl.com/api-create.php?url={url}")
            if response.status_code == 200:
                return response.text
            else:
                print(f"Ошибка при сокращении URL: {response.status_code}")
                return url
        except Exception as e:
            print(f"Ошибка при сокращении URL: {str(e)}")
            return url

    def send_to_whatsapp(self, message):
        """Отправка сообщения в WhatsApp"""
        try:
            if not self.order or not self.order.phone:
                show_warning(self, "Предупреждение", "У клиента не указан номер телефона!")
                return False

            # Форматируем номер телефона
            phone = re.sub(r'[^\d]', '', self.order.phone)
            if phone.startswith('8'):
                phone = '7' + phone[1:]
            elif not phone.startswith('7'):
                phone = '7' + phone

            # Формируем URL для WhatsApp используя api.whatsapp.com вместо wa.me
            url = f"https://api.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(message)}"

            # Открываем WhatsApp в браузере
            QDesktopServices.openUrl(QUrl(url))
            return True

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка отправки сообщения: {str(e)}")
            return False


    def view_comments(self):
        """Просмотр комментариев и тем заказа"""
        if not hasattr(self, 'order') or not self.order:
            return

        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle("Комментарии и тема заказа")
        layout = QVBoxLayout(dialog)

        # Информация о заказе
        info_text = (f"<h3>Информация о заказе №{self.order.id}</h3>"
                     f"<p><b>Клиент:</b> {self.order.fio}</p>"
                     f"<p><b>Услуга:</b> {self.order.service}</p>"
                     f"<p><b>Тема:</b> {self.order.theme or 'Не указана'}</p>"
                     f"<h4>Комментарии:</h4>"
                     f"<p>{self.order.comment or 'Комментариев нет'}</p>")

        text_browser = QTextBrowser()
        text_browser.setHtml(info_text)
        layout.addWidget(text_browser)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)

        dialog.setMinimumSize(500, 400)
        dialog.exec_()

    def show_statistics_window(self, tab_index=0):
        """Показ окна статистики клиента"""
        try:
            if not hasattr(self, 'order') or not self.order:
                return

            from ui.windows.client_statistics_window import ClientStatisticsWindow
            with DatabaseManager().session_scope() as session:
                # Создаем окно без привязки к родителю
                stats_window = ClientStatisticsWindow(session, self.order.fio)
                # Устанавливаем нужную вкладку
                stats_window.tabs.setCurrentIndex(tab_index)
                # Используем exec_ вместо show для модального окна
                stats_window.exec_()
        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при открытии статистики: {str(e)}")
    def mouseMoveEvent(self, event):
        """Обработка перемещения мыши для начала drag & drop"""
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.drag_start_position:
            return

        # Проверяем минимальное расстояние для начала перетаскивания
        distance = (event.pos() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        # Создаем Drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.order_data['id']))
        drag.setMimeData(mime_data)

        # Создаем превью карточки с эффектом прозрачности
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        painter = QPainter(pixmap)
        painter.setOpacity(0.7)
        painter.end()

        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)

        # Добавляем эффект прозрачности при перетаскивании
        opacity_effect = QGraphicsOpacityEffect()
        opacity_effect.setOpacity(0.7)
        self.setGraphicsEffect(opacity_effect)

        # Выполняем операцию перетаскивания
        result = drag.exec_(Qt.MoveAction)

        # Восстанавливаем эффект тени
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)


class HeaderFrame(QFrame):
    """Верхняя рамка для ФИО и номера заказа"""

    def __init__(self, fio, order_id, style, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # ФИО слева
        fio_label = QLabel(fio)
        fio_label.setStyleSheet(f"""
            color: {style['text']}; 
            font-weight: bold;
            font-size: 14px;
        """)

        # Номер заказа справа
        order_number = QLabel(f"#{order_id}")
        order_number.setStyleSheet(f"""
            color: {style['text']};
            font-size: 14px;
        """)

        layout.addWidget(fio_label)
        layout.addStretch()
        layout.addWidget(order_number)


class FooterFrame(QFrame):
    """Нижняя рамка для скидки и статуса"""

    def __init__(self, discount, status, style, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Скидка слева
        if discount:
            discount_label = QLabel(f"% {discount}")
            discount_label.setStyleSheet(f"""
                color: {style['text']}; 
                font-weight: bold;
                font-size: 13px;
            """)
            layout.addWidget(discount_label)

        layout.addStretch()

        # Статус справа
        status_label = QLabel(status)
        status_label.setStyleSheet(f"""
            color: {style['text']}; 
            font-weight: bold;
            font-size: 13px;
        """)
        layout.addWidget(status_label)