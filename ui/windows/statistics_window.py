# statistics_window.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QLabel, QTableWidget, QTableWidgetItem, QGroupBox,
                             QWidget, QPushButton,QFileDialog,QDateEdit,QMessageBox, QHeaderView)

from core.database import init_database, Order

from PyQt5.QtGui import QColor
from sqlalchemy import func, desc
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QLabel, QWidget,QGridLayout, QScrollArea, QPushButton,
                           QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtCore import QDate
from sqlalchemy import and_
import pandas as pd
from datetime import datetime

class StatisticsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = init_database()

        # Загружаем сохраненные размеры окна
        settings = QSettings("OrderManager", "Statistics")
        self.resize(
            settings.value("window_size/width", 1200, type=int),
            settings.value("window_size/height", 800, type=int)
        )

        # Включаем возможность изменения размера окна
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint
        )

        self.initUI()

    def initUI(self):
        self.setWindowTitle("📊 Статистика")

        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Панель управления размером
        size_control = QHBoxLayout()

        # Кнопка максимального размера
        maximize_btn = QPushButton("🔲 На весь экран")
        maximize_btn.clicked.connect(self.toggleMaximize)
        maximize_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        size_control.addWidget(maximize_btn)

        # Кнопки предустановленных размеров
        size_btn_1 = QPushButton("1200x800")
        size_btn_2 = QPushButton("1400x900")
        size_btn_3 = QPushButton("1600x1000")

        for btn, size in [(size_btn_1, (1200, 800)),
                          (size_btn_2, (1400, 900)),
                          (size_btn_3, (1600, 1000))]:
            btn.clicked.connect(lambda checked, s=size: self.resize(*s))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
            size_control.addWidget(btn)

        size_control.addStretch()
        main_layout.addLayout(size_control)

        # Добавляем скроллируемую область для основного контента
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Создаем вкладки
        tabs = QTabWidget()

        # Добавляем все вкладки...
        top_clients_tab = self.createTopClientsTab()
        tabs.addTab(top_clients_tab, "👥 Топ клиенты")

        profit_tab = self.createProfitTab()
        tabs.addTab(profit_tab, "💰 Отчет о прибыли")

        analysis_tab = self.createDetailedAnalysisTab()
        tabs.addTab(analysis_tab, "📈 Детальный анализ")

        services_tab = self.createServicesAnalysisTab()
        tabs.addTab(services_tab, "🌟 Анализ услуг")

        content_layout.addWidget(tabs)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def toggleMaximize(self):
        """Переключение полноэкранного режима"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def resizeEvent(self, event):
        """Сохранение размеров окна при изменении"""
        settings = QSettings("OrderManager", "Statistics")
        settings.setValue("window_size/width", event.size().width())
        settings.setValue("window_size/height", event.size().height())
        super().resizeEvent(event)

    def createTopClientsTab(self):
        """Создание вкладки с топ клиентами"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Заголовок
        title = QLabel("🏆 Топ 10 клиентов")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Создаем виджет для прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)  # Отступ между карточками

        # Получаем данные по количеству заказов
        top_by_orders = (
            self.session.query(
                Order.fio,
                func.count(Order.id).label('order_count'),
                func.sum(Order.cost).label('total_cost'),
                (func.sum(Order.cost) / func.count(Order.id)).label('avg_cost')
            )
            .group_by(Order.fio)
            .order_by(desc('order_count'))
            .limit(10)
            .all()
        )

        # Получаем данные по общей сумме
        top_by_amount = (
            self.session.query(
                Order.fio,
                func.sum(Order.cost).label('total_cost'),
                func.count(Order.id).label('order_count'),
                (func.sum(Order.cost) / func.count(Order.id)).label('avg_cost')
            )
            .group_by(Order.fio)
            .order_by(desc('total_cost'))
            .limit(10)
            .all()
        )

        # Создаем две колонки
        columns_widget = QWidget()
        columns_layout = QHBoxLayout(columns_widget)

        # Колонка "По количеству заказов"
        orders_column = QWidget()
        orders_layout = QVBoxLayout(orders_column)

        orders_title = QLabel("По количеству заказов")
        orders_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        orders_layout.addWidget(orders_title)

        for i, client in enumerate(top_by_orders):
            card = self.createClientCard(
                position=i + 1,
                name=client.fio,
                orders=client.order_count,
                total=client.total_cost,
                average=client.avg_cost
            )
            orders_layout.addWidget(card)

        columns_layout.addWidget(orders_column)

        # Колонка "По общей сумме"
        amount_column = QWidget()
        amount_layout = QVBoxLayout(amount_column)

        amount_title = QLabel("По общей сумме")
        amount_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        amount_layout.addWidget(amount_title)

        for i, client in enumerate(top_by_amount):
            card = self.createClientCard(
                position=i + 1,
                name=client.fio,
                orders=client.order_count,
                total=client.total_cost,
                average=client.avg_cost
            )
            amount_layout.addWidget(card)

        columns_layout.addWidget(amount_column)
        scroll_layout.addWidget(columns_widget)

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return tab_widget

    def createClientCard(self, position, name, orders, total, average):
        """Создание карточки клиента"""
        card = QWidget()

        # Определяем медали и цвета
        medal_style = {
            1: ("🥇", "#FFD700"),
            2: ("🥈", "#C0C0C0"),
            3: ("🥉", "#CD7F32")
        }.get(position, (f"#{position}", "#FFFFFF"))

        medal, color = medal_style

        card.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 8px;
                padding: 5px;
                margin: 3px;
            }}
            QLabel {{
                color: #2c3e50;
                background-color: transparent;
                font-size: 14px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        # Заголовок
        header = QHBoxLayout()
        position_label = QLabel(medal)
        position_label.setStyleSheet("font-size: 16px;")
        name_label = QLabel(name)
        name_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        header.addWidget(position_label)
        header.addWidget(name_label)
        header.addStretch()
        layout.addLayout(header)

        # Информация
        layout.addWidget(QLabel(f"📊 Заказов: {orders}"))
        layout.addWidget(QLabel(f"💰 Сумма: {total:,.0f} ₽"))
        layout.addWidget(QLabel(f"📈 Средний: {average:,.0f} ₽"))

        # Тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setXOffset(2)
        shadow.setYOffset(2)
        shadow.setColor(QColor("#cccccc"))
        card.setGraphicsEffect(shadow)

        return card
    def createFinancialTab(self):
        """Создание вкладки с финансовой статистикой"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Общая статистика
        summary_group = QGroupBox("Общая финансовая статистика")
        summary_layout = QVBoxLayout()

        # Получаем данные
        stats = self.session.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.cost).label('total_revenue'),
            func.sum(Order.paid_amount).label('total_paid'),
            func.avg(Order.cost).label('avg_order_cost')
        ).first()

        # Создаем метки с информацией
        summary_layout.addWidget(QLabel(f"Всего заказов: {stats.total_orders}"))
        summary_layout.addWidget(QLabel(f"Общая выручка: {stats.total_revenue:.2f} ₽"))
        summary_layout.addWidget(QLabel(f"Оплачено: {stats.total_paid:.2f} ₽"))
        summary_layout.addWidget(QLabel(f"Средний чек: {stats.avg_order_cost:.2f} ₽"))

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Добавляем React компонент для графиков
        layout.addWidget(QLabel("Графики:"))

        return widget

    def createServicesTab(self):
        """Создание вкладки со статистикой по услугам"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Таблица популярных услуг
        services_group = QGroupBox("Популярные услуги")
        services_layout = QVBoxLayout()

        services_table = QTableWidget()
        services_table.setColumnCount(4)
        services_table.setHorizontalHeaderLabels([
            "Услуга", "Количество заказов", "Общая сумма", "Средняя стоимость"
        ])

        # Получаем данные
        services_stats = (
            self.session.query(
                Order.service,
                func.count(Order.id).label('order_count'),
                func.sum(Order.cost).label('total_cost'),
                (func.sum(Order.cost) / func.count(Order.id)).label('avg_cost')
            )
            .group_by(Order.service)
            .order_by(desc('order_count'))
            .all()
        )

        services_table.setRowCount(len(services_stats))
        for i, service in enumerate(services_stats):
            services_table.setItem(i, 0, QTableWidgetItem(service.service))
            services_table.setItem(i, 1, QTableWidgetItem(str(service.order_count)))
            services_table.setItem(i, 2, QTableWidgetItem(f"{service.total_cost:.2f} ₽"))
            services_table.setItem(i, 3, QTableWidgetItem(f"{service.avg_cost:.2f} ₽"))

        services_layout.addWidget(services_table)
        services_group.setLayout(services_layout)
        layout.addWidget(services_group)

        return widget

    def createProfitTab(self):
        """Создание вкладки отчета о прибыли"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        layout.setAlignment(Qt.AlignCenter)  # Центрируем весь контент

        # Заголовок
        title = QLabel("💰 Отчет о прибыли")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 20px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Контейнер для карточек
        cards_container = QWidget()
        cards_layout = QGridLayout(cards_container)  # Используем сетку для карточек
        cards_layout.setSpacing(20)  # Отступы между карточками

        # Получаем данные
        results = self.session.query(
            func.sum(Order.cost).label('total_revenue'),
            func.sum(Order.paid_amount).label('total_paid'),
            func.count(Order.id).label('total_orders'),
            func.avg(Order.cost).label('avg_order')
        ).one()

        # Создаем карточки статистики
        revenue_card = self.createStatsCard(
            "📈 Общая выручка",
            f"{results.total_revenue:,.0f} ₽",
            "#4CAF50"
        )
        paid_card = self.createStatsCard(
            "💵 Оплачено",
            f"{results.total_paid:,.0f} ₽",
            "#2196F3"
        )
        orders_card = self.createStatsCard(
            "📦 Всего заказов",
            str(results.total_orders),
            "#9C27B0"
        )
        avg_card = self.createStatsCard(
            "💎 Средний чек",
            f"{results.avg_order:,.0f} ₽",
            "#FF9800"
        )

        # Размещаем карточки в сетке 2x2
        cards_layout.addWidget(revenue_card, 0, 0)
        cards_layout.addWidget(paid_card, 0, 1)
        cards_layout.addWidget(orders_card, 1, 0)
        cards_layout.addWidget(avg_card, 1, 1)

        # Центрируем контейнер с карточками
        cards_container.setMaximumWidth(800)  # Ограничиваем максимальную ширину
        layout.addWidget(cards_container, alignment=Qt.AlignCenter)

        # Добавляем растягивающийся элемент снизу
        layout.addStretch()

        return tab_widget

    def createStatsCard(self, title, value, color):
        """Создание карточки статистики"""
        card = QWidget()
        card.setFixedSize(350, 150)  # Фиксированный размер карточки
        card.setStyleSheet(f"""
            QWidget {{
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }}
            QLabel {{
                background-color: transparent;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # Заголовок
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {color};
            font-weight: bold;
            font-size: 16px;
        """)
        title_label.setAlignment(Qt.AlignCenter)

        # Значение
        value_label = QLabel(value)
        value_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        """)
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        # Добавляем тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)

        return card

    def createDetailedAnalysisTab(self):
        """Создание вкладки детального анализа"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Панель фильтров (оставляем существующий код)
        filters_group = QGroupBox("Фильтры")
        filters_layout = QHBoxLayout()

        period_label = QLabel("Период:")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addYears(-1))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())

        filters_layout.addWidget(period_label)
        filters_layout.addWidget(self.date_from)
        filters_layout.addWidget(QLabel("-"))
        filters_layout.addWidget(self.date_to)

        apply_filter_btn = QPushButton("🔍 Применить")
        apply_filter_btn.clicked.connect(self.update_monthly_stats)
        filters_layout.addWidget(apply_filter_btn)

        export_btn = QPushButton("📊 Экспорт в Excel")
        export_btn.clicked.connect(self.export_monthly_stats)
        filters_layout.addWidget(export_btn)

        filters_layout.addStretch()
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        # Основная таблица статистики по месяцам
        self.monthly_table = QTableWidget()
        self.monthly_table.setColumnCount(5)
        self.monthly_table.setHorizontalHeaderLabels([
            "Месяц", "Кол-во заказов", "Выручка", "Оплачено", "Осталось"
        ])

        # Включаем сортировку и настраиваем стиль
        self.monthly_table.setSortingEnabled(True)
        self.monthly_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.monthly_table.setSelectionMode(QTableWidget.SingleSelection)

        # Подключаем обработчик клика
        self.monthly_table.itemClicked.connect(self.on_month_selected)

        # Настраиваем растягивание колонок
        header = self.monthly_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        layout.addWidget(self.monthly_table)

        # Добавляем таблицу для детализации заказов за месяц
        self.orders_detail_table = QTableWidget()
        self.orders_detail_table.setColumnCount(7)
        self.orders_detail_table.setHorizontalHeaderLabels([
            "ID", "Дата", "Клиент", "Услуга", "Стоимость", "Оплачено", "Статус"
        ])
        self.orders_detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.orders_detail_table.setSelectionMode(QTableWidget.SingleSelection)
        self.orders_detail_table.itemClicked.connect(self.on_order_selected)
        self.orders_detail_table.hide()  # Изначально скрываем таблицу

        # Настраиваем растягивание колонок
        header = self.orders_detail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout.addWidget(self.orders_detail_table)

        # Итоговая строка
        totals_group = QGroupBox("Итого")
        totals_layout = QHBoxLayout()

        self.total_orders_label = QLabel("Заказов: 0")
        self.total_revenue_label = QLabel("Выручка: 0 ₽")
        self.total_paid_label = QLabel("Оплачено: 0 ₽")
        self.total_remaining_label = QLabel("Осталось: 0 ₽")

        totals_layout.addWidget(self.total_orders_label)
        totals_layout.addWidget(self.total_revenue_label)
        totals_layout.addWidget(self.total_paid_label)
        totals_layout.addWidget(self.total_remaining_label)

        totals_group.setLayout(totals_layout)
        layout.addWidget(totals_group)

        # Загружаем начальные данные
        self.update_monthly_stats()

        return tab_widget

    def on_month_selected(self, item):
        """Обработчик выбора месяца в таблице"""
        try:
            # Получаем месяц из первой колонки выбранной строки
            row = item.row()
            month_item = self.monthly_table.item(row, 0)
            if not month_item:
                return

            selected_month = month_item.text()

            # Получаем заказы за выбранный месяц
            date_parts = selected_month.split('-')
            if len(date_parts) != 2:
                return

            year, month = date_parts

            # Формируем условие фильтра по месяцу
            month_filter = and_(
                func.strftime('%Y', Order.created_date) == year,
                func.strftime('%m', Order.created_date) == month
            )

            # Получаем данные заказов
            orders = (
                self.session.query(Order)
                .filter(month_filter)
                .order_by(Order.created_date)
                .all()
            )

            # Обновляем таблицу деталей
            self.orders_detail_table.setRowCount(len(orders))
            for i, order in enumerate(orders):
                # ID заказа
                id_item = QTableWidgetItem(str(order.id))
                id_item.setData(Qt.UserRole, order.id)  # Сохраняем ID для использования при клике
                self.orders_detail_table.setItem(i, 0, id_item)

                # Дата
                date_str = order.created_date.strftime('%d.%m.%Y') if order.created_date else ''
                self.orders_detail_table.setItem(i, 1, QTableWidgetItem(date_str))

                # Клиент
                self.orders_detail_table.setItem(i, 2, QTableWidgetItem(order.fio))

                # Услуга
                self.orders_detail_table.setItem(i, 3, QTableWidgetItem(order.service))

                # Стоимость
                cost_item = QTableWidgetItem(f"{order.cost:,.2f} ₽")
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.orders_detail_table.setItem(i, 4, cost_item)

                # Оплачено
                paid_item = QTableWidgetItem(f"{order.paid_amount:,.2f} ₽")
                paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.orders_detail_table.setItem(i, 5, paid_item)

                # Статус
                status_item = QTableWidgetItem(order.status)
                if order.remaining_amount > 0:
                    status_item.setForeground(QColor("#f44336"))
                self.orders_detail_table.setItem(i, 6, status_item)

            # Показываем таблицу деталей
            self.orders_detail_table.show()

            # Устанавливаем оптимальную ширину колонок
            self.orders_detail_table.resizeColumnsToContents()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных: {str(e)}")

    def on_order_selected(self, item):
        """Обработчик выбора заказа в детальной таблице"""
        try:
            # Получаем ID заказа из первой колонки
            row = item.row()
            id_item = self.orders_detail_table.item(row, 0)
            if not id_item:
                return

            order_id = id_item.data(Qt.UserRole)
            if not order_id:
                return

            # Получаем полные данные заказа
            order = self.session.query(Order).get(order_id)
            if not order:
                return

            # Создаем диалог с детальной информацией
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Детали заказа #{order.id}")
            dialog.setMinimumWidth(600)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: white;
                }
                QLabel {
                    padding: 5px;
                }
                QLabel[labelType="header"] {
                    font-weight: bold;
                    color: #2196F3;
                }
                QGroupBox {
                    margin-top: 10px;
                }
            """)

            layout = QVBoxLayout(dialog)

            # Основная информация
            main_info = QGroupBox("Основная информация")
            main_layout = QGridLayout()

            # Добавляем поля с информацией
            fields = [
                ("ID заказа:", str(order.id)),
                ("Дата создания:", order.created_date.strftime('%d.%m.%Y') if order.created_date else 'Не указана'),
                ("Клиент:", order.fio),
                ("Группа:", order.group),
                ("Услуга:", order.service),
                ("Направление:", order.direction or 'Не указано'),
                ("Тема:", order.theme or 'Не указана'),
                ("Статус:", order.status)
            ]

            for i, (label, value) in enumerate(fields):
                label_widget = QLabel(label)
                label_widget.setProperty('labelType', 'header')
                value_widget = QLabel(value)
                main_layout.addWidget(label_widget, i, 0)
                main_layout.addWidget(value_widget, i, 1)

            main_info.setLayout(main_layout)
            layout.addWidget(main_info)

            # Финансовая информация
            financial_info = QGroupBox("Финансовая информация")
            financial_layout = QGridLayout()

            financial_fields = [
                ("Стоимость:", f"{order.cost:,.2f} ₽"),
                ("Оплачено:", f"{order.paid_amount:,.2f} ₽"),
                ("Осталось:", f"{order.remaining_amount:,.2f} ₽"),
                ("Скидка:", order.discount or 'Нет'),
            ]

            for i, (label, value) in enumerate(financial_fields):
                label_widget = QLabel(label)
                label_widget.setProperty('labelType', 'header')
                value_widget = QLabel(value)
                if "Осталось" in label and order.remaining_amount > 0:
                    value_widget.setStyleSheet("color: #f44336;")
                financial_layout.addWidget(label_widget, i, 0)
                financial_layout.addWidget(value_widget, i, 1)

            financial_info.setLayout(financial_layout)
            layout.addWidget(financial_info)

            # Контактная информация
            contact_info = QGroupBox("Контактная информация")
            contact_layout = QGridLayout()

            contact_fields = [
                ("Телефон:", order.phone or 'Не указан'),
                ("Преподаватель:", order.teacher_name or 'Не указан'),
                ("Email преподавателя:", order.teacher_email or 'Не указан'),
            ]

            for i, (label, value) in enumerate(contact_fields):
                label_widget = QLabel(label)
                label_widget.setProperty('labelType', 'header')
                value_widget = QLabel(value)
                contact_layout.addWidget(label_widget, i, 0)
                contact_layout.addWidget(value_widget, i, 1)

            contact_info.setLayout(contact_layout)
            layout.addWidget(contact_info)

            # Дополнительная информация
            if order.comment:
                comment_group = QGroupBox("Комментарий")
                comment_layout = QVBoxLayout()
                comment_label = QLabel(order.comment)
                comment_label.setWordWrap(True)
                comment_layout.addWidget(comment_label)
                comment_group.setLayout(comment_layout)
                layout.addWidget(comment_group)

            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            layout.addWidget(close_btn, alignment=Qt.AlignCenter)

            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при показе деталей заказа: {str(e)}")

    def update_monthly_stats(self):
        """Обновление статистики с учетом фильтров"""
        try:
            # Формируем условие фильтра по датам
            date_filter = and_(
                Order.created_date >= self.date_from.date().toPyDate(),
                Order.created_date <= self.date_to.date().toPyDate()
            )

            # Получаем данные
            monthly_data = (
                self.session.query(
                    func.strftime('%Y-%m', Order.created_date).label('month'),
                    func.count(Order.id).label('orders'),
                    func.sum(Order.cost).label('revenue'),
                    func.sum(Order.paid_amount).label('paid'),
                    func.sum(Order.remaining_amount).label('remaining')
                )
                .filter(date_filter)
                .group_by('month')
                .order_by('month')
                .all()
            )

            # Обновляем таблицу
            self.monthly_table.setRowCount(len(monthly_data))

            total_orders = 0
            total_revenue = 0
            total_paid = 0
            total_remaining = 0

            for i, data in enumerate(monthly_data):
                # Добавляем данные в таблицу
                self.monthly_table.setItem(i, 0, QTableWidgetItem(data.month))
                self.monthly_table.setItem(i, 1, QTableWidgetItem(str(data.orders)))
                self.monthly_table.setItem(i, 2, QTableWidgetItem(f"{data.revenue:,.0f} ₽"))
                self.monthly_table.setItem(i, 3, QTableWidgetItem(f"{data.paid:,.0f} ₽"))
                self.monthly_table.setItem(i, 4, QTableWidgetItem(f"{data.remaining:,.0f} ₽"))

                # Суммируем итоги
                total_orders += data.orders
                total_revenue += data.revenue
                total_paid += data.paid
                total_remaining += data.remaining

                # Применяем стили
                for col in range(2, 5):
                    item = self.monthly_table.item(i, col)
                    if item:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # Подсветка долгов
                remaining_item = self.monthly_table.item(i, 4)
                if remaining_item and data.remaining > 0:
                    remaining_item.setForeground(QColor("#f44336"))

            # Обновляем итоговые значения
            self.total_orders_label.setText(f"Заказов: {total_orders}")
            self.total_revenue_label.setText(f"Выручка: {total_revenue:,.0f} ₽")
            self.total_paid_label.setText(f"Оплачено: {total_paid:,.0f} ₽")
            self.total_remaining_label.setText(f"Осталось: {total_remaining:,.0f} ₽")

            if total_remaining > 0:
                self.total_remaining_label.setStyleSheet("color: #f44336;")
            else:
                self.total_remaining_label.setStyleSheet("")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении статистики: {str(e)}")

    def export_monthly_stats(self):
        """Экспорт статистики в Excel"""
        try:
            # Запрашиваем путь для сохранения
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить статистику",
                f"Статистика_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Excel files (*.xlsx)"
            )

            if file_path:
                # Создаем DataFrame из данных таблицы
                data = []
                headers = []

                # Получаем заголовки
                for col in range(self.monthly_table.columnCount()):
                    headers.append(self.monthly_table.horizontalHeaderItem(col).text())

                # Получаем данные
                for row in range(self.monthly_table.rowCount()):
                    row_data = []
                    for col in range(self.monthly_table.columnCount()):
                        item = self.monthly_table.item(row, col)
                        # Очищаем числовые значения от символов валюты
                        value = item.text().replace(" ₽", "").replace(",", "")
                        row_data.append(value)
                    data.append(row_data)

                # Создаем DataFrame
                df = pd.DataFrame(data, columns=headers)

                # Конвертируем числовые колонки
                numeric_columns = ["Кол-во заказов", "Выручка", "Оплачено", "Осталось"]
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # Добавляем итоговую строку
                totals = df[numeric_columns].sum()
                totals_df = pd.DataFrame([totals], columns=numeric_columns)
                totals_df["Месяц"] = "ИТОГО:"
                df = pd.concat([df, totals_df], ignore_index=True)

                # Сохраняем в Excel с форматированием
                writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
                df.to_excel(writer, sheet_name='Статистика', index=False)

                # Получаем объект workbook и worksheet
                workbook = writer.book
                worksheet = writer.sheets['Статистика']

                # Форматы для чисел
                money_format = workbook.add_format({'num_format': '#,##0 ₽'})
                number_format = workbook.add_format({'num_format': '#,##0'})

                # Применяем форматы к колонкам
                worksheet.set_column('B:B', 15, number_format)  # Кол-во заказов
                worksheet.set_column('C:E', 15, money_format)  # Денежные колонки

                # Закрываем writer вместо save()
                writer.close()

                QMessageBox.information(self, "Успех", "Статистика успешно экспортирована!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте данных: {str(e)}")

    def createServicesAnalysisTab(self):
        """Создание вкладки анализа услуг"""
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)

        # Топ 10 услуг
        top_services_group = QGroupBox("🌟 Топ 10 популярных услуг")
        top_services_layout = QVBoxLayout()

        # Получаем данные по услугам
        top_services = (
            self.session.query(
                Order.service,
                func.count(Order.id).label('orders_count'),
                func.sum(Order.cost).label('total_revenue'),
                func.avg(Order.cost).label('avg_cost')
            )
            .group_by(Order.service)
            .order_by(desc('orders_count'))
            .limit(10)
            .all()
        )

        # Создаем карточки для каждой услуги
        for i, service in enumerate(top_services):
            card = self.createServiceCard(
                position=i + 1,
                name=service.service,
                count=service.orders_count,
                revenue=service.total_revenue,
                avg_cost=service.avg_cost
            )
            top_services_layout.addWidget(card)

        top_services_group.setLayout(top_services_layout)
        layout.addWidget(top_services_group)

        return tab_widget

    def createServiceCard(self, position, name, count, revenue, avg_cost):
        """Создание карточки услуги"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                background-color: transparent;
            }
        """)

        layout = QHBoxLayout(card)

        # Позиция и медаль
        medal = "🥇" if position == 1 else "🥈" if position == 2 else "🥉" if position == 3 else f"#{position}"
        position_label = QLabel(medal)
        position_label.setStyleSheet("font-size: 20px;")
        layout.addWidget(position_label)

        # Информация об услуге
        info_layout = QVBoxLayout()
        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        stats_label = QLabel(f"📊 Заказов: {count} | 💰 Выручка: {revenue:,.0f} ₽ | 💎 Средняя цена: {avg_cost:,.0f} ₽")

        info_layout.addWidget(name_label)
        info_layout.addWidget(stats_label)
        layout.addLayout(info_layout)

        # Добавляем тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(5)
        shadow.setXOffset(2)
        shadow.setYOffset(2)
        shadow.setColor(QColor("#cccccc"))
        card.setGraphicsEffect(shadow)

        return card
