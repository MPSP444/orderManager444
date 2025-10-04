from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QWidget)
from PyQt5.QtCore import Qt
from sqlalchemy import func
from core.database import init_database, Order

DIALOG_STYLE = """
    QDialog {
        background-color: white;
        margin: 10px;
    }
    QLabel {
        color: #333333;
        font-size: 12px;
    }
    QPushButton {
        color: #333333;
        background-color: #e8e8e8;
        border: 1px solid #cccccc;
        padding: 5px 10px;
        border-radius: 3px;
        min-width: 30px;
    }
    QPushButton:hover {
        background-color: #d0d0d0;
        border: 1px solid #999999;
    }
    QGroupBox {
        color: #2196F3;
        font-weight: bold;
        font-size: 13px;
        padding-top: 15px;
        margin-top: 10px;
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
        background-color: white;
    }
"""


class ClientInfoWindow(QDialog):
    def __init__(self, parent=None, client_fio=None):
        super().__init__(parent)
        self.client_fio = client_fio
        self.session = init_database()
        self.initUI()
        self.setStyleSheet(DIALOG_STYLE)

    def create_info_row(self, label_text, value):
        """Создание строки с информацией"""
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(5, 2, 5, 2)

        # Метка
        label = QLabel(f"{label_text}:")
        label.setMinimumWidth(150)
        label.setStyleSheet("color: #666666; font-weight: bold;")
        layout.addWidget(label)

        # Значение
        value_label = QLabel(str(value))
        value_label.setStyleSheet("color: #333333;")
        layout.addWidget(value_label)

        layout.addStretch()
        return row_widget

    def initUI(self):
        self.setWindowTitle(f"Информация о клиенте: {self.client_fio}")
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Основная информация
        main_group = QGroupBox("👤 Основная информация")
        main_layout = QVBoxLayout()

        client_data = self.get_client_data()
        if client_data:
            main_layout.addWidget(self.create_info_row("ФИО", client_data['fio']))
            main_layout.addWidget(self.create_info_row("Группа", client_data['group']))
            main_layout.addWidget(self.create_info_row("Телефон", client_data['phone']))

        main_group.setLayout(main_layout)
        layout.addWidget(main_group)

        # Статистика заказов
        stats_group = QGroupBox("📊 Статистика заказов")
        stats_layout = QVBoxLayout()

        if client_data:
            stats_layout.addWidget(self.create_info_row("Всего заказов", client_data['total_orders']))
            stats_layout.addWidget(self.create_info_row("Общая сумма", f"{client_data['total_cost']:.2f} руб."))
            stats_layout.addWidget(self.create_info_row("Оплачено", f"{client_data['total_paid']:.2f} руб."))
            stats_layout.addWidget(self.create_info_row("Остаток", f"{client_data['total_remaining']:.2f} руб."))
            stats_layout.addWidget(self.create_info_row("Средний чек", f"{client_data['average_cost']:.2f} руб."))

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Дополнительная информация
        additional_group = QGroupBox("ℹ️ Дополнительная информация")
        additional_layout = QVBoxLayout()

        if client_data:
            additional_layout.addWidget(self.create_info_row("Последний заказ", client_data['last_order_date']))
            additional_layout.addWidget(
                self.create_info_row("Статус последнего заказа", client_data['last_order_status']))
            additional_layout.addWidget(self.create_info_row("Скидки", client_data['discounts']))

        additional_group.setLayout(additional_layout)
        layout.addWidget(additional_group)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)

        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        close_btn.clicked.connect(self.close)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def get_client_data(self):
        """Получение данных о клиенте"""
        try:
            # Получаем последний заказ клиента для основной информации
            last_order = self.session.query(Order).filter(
                Order.fio == self.client_fio
            ).order_by(Order.created_date.desc()).first()

            if not last_order:
                return None

            # Получаем статистику
            stats = self.session.query(
                func.count(Order.id).label('total_orders'),
                func.sum(Order.cost).label('total_cost'),
                func.sum(Order.paid_amount).label('total_paid'),
                func.sum(Order.remaining_amount).label('total_remaining')
            ).filter(Order.fio == self.client_fio).first()

            # Собираем скидки
            discounts = set()
            orders = self.session.query(Order).filter(Order.fio == self.client_fio).all()
            for order in orders:
                if order.discount:
                    discounts.add(order.discount)

            return {
                'fio': last_order.fio,
                'group': last_order.group or 'Не указана',
                'phone': last_order.phone or 'Не указан',
                'total_orders': stats.total_orders,
                'total_cost': stats.total_cost or 0,
                'total_paid': stats.total_paid or 0,
                'total_remaining': stats.total_remaining or 0,
                'average_cost': (stats.total_cost / stats.total_orders) if stats.total_orders > 0 else 0,
                'last_order_date': last_order.created_date.strftime(
                    '%d.%m.%Y') if last_order.created_date else 'Не указана',
                'last_order_status': last_order.status,
                'discounts': ', '.join(discounts) if discounts else 'Не использовались'
            }

        except Exception as e:
            print(f"Ошибка при получении данных о клиенте: {e}")
            return None
