import os

from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QPushButton, QFileDialog,
                             QFrame, QScrollArea, QTreeWidget, QTreeWidgetItem, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import react
from datetime import datetime, timedelta
from core.database import Order
from sqlalchemy import func, case
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy import case, func
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHeaderView  # Для управления заголовками колонок
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class ClientStatisticsWindow(QDialog):
    def __init__(self, session, client_fio, parent=None):
        super().__init__(None)  # Устанавливаем parent=None для полной независимости
        self.session = session
        self.client_fio = client_fio

        # Устанавливаем флаги окна
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinMaxButtonsHint)

        # Устанавливаем фиксированный размер окна
        self.setMinimumSize(1000, 700)  # Можете настроить размер как нужно

        # Отключаем автоматическое заполнение фона
        self.setAutoFillBackground(False)

        # Сбрасываем все стили
        self.setStyleSheet("")

        self.initUI()

    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle(f"Статистика и аналитика - {self.client_fio}")
        self.setMinimumSize(1000, 700)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Добавляем отступы
        main_layout.setSpacing(15)  # Увеличиваем расстояние между элементами

        # Заголовок
        header = QLabel(f"Аналитика клиента: {self.client_fio}")
        header.setFont(QFont("Arial", 14, QFont.Bold))
        header.setAlignment(Qt.AlignLeft)  # Выравниваем по левому краю
        header.setStyleSheet("padding: 10px;")
        main_layout.addWidget(header)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin: 2px;
                background: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
            }
        """)

        self.tabs.addTab(self.create_general_tab(), "📊 Общая статистика")
        self.tabs.addTab(self.create_orders_analysis_tab(), "📈 Анализ заказов")
        self.tabs.addTab(self.create_orders_history_tab(), "📅 История заказов")
        self.tabs.addTab(self.create_payment_history_tab(), "💰 История оплат")
        self.tabs.addTab(self.create_client_rating_tab(), "🏆 Рейтинг клиента")
        self.tabs.addTab(self.create_predictions_tab(), "🔮 Прогнозы")

        main_layout.addWidget(self.tabs)

        # Кнопки действий
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)  # Добавляем отступ сверху

        export_btn = QPushButton("📑 Экспорт в PDF")
        export_btn.setMinimumWidth(1000)  # Устанавливаем минимальную ширину кнопок
        export_btn.clicked.connect(self.export_to_pdf)

        close_btn = QPushButton("❌ Закрыть")
        close_btn.setMinimumWidth(1000)
        close_btn.clicked.connect(self.close)

        button_layout.addWidget(export_btn)
        button_layout.addStretch()  # Добавляем растягивающийся элемент
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        # Обновленные стили
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                background: transparent;
                padding: 5px;
            }
            QPushButton {
                padding: 8px 16px;
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QFrame {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                margin: 5px;
            }
        """)

    def create_general_tab(self):
        """Создание вкладки общей статистики"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Создаем таблицу для статистики
        stats_table = QTreeWidget()
        stats_table.setHeaderHidden(True)
        stats_table.setColumnCount(2)
        stats_table.setRootIsDecorated(False)
        stats_table.setAlternatingRowColors(True)
        stats_table.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
        """)

        # Получаем статистику
        stats = self.session.query(
            func.count(Order.id).label('total_orders'),
            func.sum(Order.cost).label('total_cost'),
            func.avg(Order.cost).label('avg_cost'),
            func.sum(Order.remaining_amount).label('total_debt')
        ).filter(Order.fio == self.client_fio).first()

        # Добавляем данные
        stats_data = [
            ("📦 Всего заказов:", f"{stats.total_orders}"),
            ("💰 Общая сумма заказов:", f"{stats.total_cost:,.2f}₽"),
            ("📊 Средний чек:", f"{stats.avg_cost:,.2f}₽"),
            ("⚠️ Текущая задолженность:", f"{stats.total_debt:,.2f}₽")
        ]

        for label_text, value_text in stats_data:
            item = QTreeWidgetItem(stats_table)
            item.setText(0, label_text)
            item.setText(1, value_text)
            item.setTextAlignment(1, Qt.AlignLeft)  # Меняем выравнивание на левое

        # Устанавливаем размеры колонок - делаем первую колонку шире, а вторую уже
        stats_table.setColumnWidth(0, 300)  # Уменьшаем ширину первой колонки
        stats_table.setColumnWidth(1, 150)  # Уменьшаем ширину второй колонки

        layout.addWidget(stats_table)
        return tab

    def create_orders_history_tab(self):
        """Создание вкладки истории заказов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        tree = QTreeWidget()
        tree.setHeaderLabels([
            "Дата создания", "Услуга", "Стоимость", "Скидка",
            "Оплачено", "Остаток", "Дата оплаты", "Статус"
        ])

        tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
        """)

        orders = self.session.query(Order).filter(
            Order.fio == self.client_fio
        ).order_by(Order.created_date.desc()).all()

        # Группируем по годам и месяцам
        for order in orders:
            year_str = order.created_date.strftime('%Y')
            month_str = order.created_date.strftime('%B %Y')

            # Ищем или создаем элемент года
            year_items = tree.findItems(year_str, Qt.MatchExactly)
            if year_items:
                year_item = year_items[0]
            else:
                year_item = QTreeWidgetItem(tree, [year_str])
                year_item.setExpanded(True)
                # Устанавливаем шрифт для года
                font = year_item.font(0)
                font.setBold(True)
                year_item.setFont(0, font)

            # Ищем или создаем элемент месяца
            month_item = None
            for i in range(year_item.childCount()):
                if year_item.child(i).text(0) == month_str:
                    month_item = year_item.child(i)
                    break
            if not month_item:
                month_item = QTreeWidgetItem(year_item, [month_str])
                month_item.setExpanded(True)
                # Устанавливаем шрифт для месяца
                font = month_item.font(0)
                font.setBold(True)
                month_item.setFont(0, font)

            # Добавляем заказ с полной датой создания
            order_item = QTreeWidgetItem(month_item)
            order_item.setText(0, order.created_date.strftime('%d.%m.%Y %H:%M'))  # Добавляем время
            order_item.setText(1, order.service)
            order_item.setText(2, f"{order.cost:,.2f}₽")
            order_item.setText(3, order.discount or "-")
            order_item.setText(4, f"{order.paid_amount:,.2f}₽")
            order_item.setText(5, f"{order.remaining_amount:,.2f}₽")
            order_item.setText(6, order.payment_date.strftime('%d.%m.%Y %H:%M') if order.payment_date else "-")
            order_item.setText(7, order.status)

            # Устанавливаем выравнивание для числовых значений
            for col in [2, 4, 5]:
                order_item.setTextAlignment(col, Qt.AlignLeft)  # Меняем на левое выравнивание

        # Устанавливаем размеры колонок
        header = tree.header()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Растягиваем колонку с услугой
        header.setStretchLastSection(False)

        # Фиксированные размеры для остальных колонок
        column_widths = [200, -1, 100, 80, 100, 100, 150, 100]
        for i, width in enumerate(column_widths):
            if width > 0:
                tree.setColumnWidth(i, width)

        layout.addWidget(tree)
        return tab


    def create_orders_analysis_tab(self):
        """Создание вкладки анализа заказов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Получаем статистику по типам заказов
        services_stats = self.session.query(
            Order.service,
            func.count(Order.id).label('count'),
            func.sum(Order.cost).label('total')
        ).filter(Order.fio == self.client_fio).group_by(Order.service).all()

        # Создаем таблицу популярных услуг
        services_frame = QFrame()
        services_frame.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        services_layout = QVBoxLayout(services_frame)

        title = QLabel("🔍 Анализ заказываемых услуг")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        services_layout.addWidget(title)

        for service, count, total in services_stats:
            service_info = QLabel(
                f"• {service}: {count} заказов на сумму {total:,.2f}₽"
            )
            services_layout.addWidget(service_info)

        layout.addWidget(services_frame)

        # Здесь будет добавлен график распределения заказов

        return tab

    def create_payment_history_tab(self):
        """Создание вкладки истории оплат"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        tree = QTreeWidget()
        tree.setHeaderLabels([
            "Дата оплаты", "Услуга", "Сумма оплаты", "Дата заказа",
            "Общая стоимость", "Остаток", "Скидка", "Статус"
        ])

        tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1565C0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
                font-weight: bold;
            }
        """)

        # Получаем заказы с оплатами
        orders = self.session.query(Order).filter(
            Order.fio == self.client_fio,
            Order.paid_amount > 0
        ).order_by(Order.payment_date.desc()).all()

        # Группируем по годам и месяцам
        for order in orders:
            if order.payment_date:
                year_str = order.payment_date.strftime('%Y')
                month_str = order.payment_date.strftime('%B %Y')

                # Ищем или создаем элемент года
                year_items = tree.findItems(year_str, Qt.MatchExactly)
                if year_items:
                    year_item = year_items[0]
                else:
                    year_item = QTreeWidgetItem(tree, [year_str])
                    year_item.setExpanded(True)
                    font = year_item.font(0)
                    font.setBold(True)
                    year_item.setFont(0, font)

                # Ищем или создаем элемент месяца
                month_item = None
                for i in range(year_item.childCount()):
                    if year_item.child(i).text(0) == month_str:
                        month_item = year_item.child(i)
                        break
                if not month_item:
                    month_item = QTreeWidgetItem(year_item, [month_str])
                    month_item.setExpanded(True)
                    font = month_item.font(0)
                    font.setBold(True)
                    month_item.setFont(0, font)

                # Добавляем платеж
                payment_item = QTreeWidgetItem(month_item)
                payment_item.setText(0, order.payment_date.strftime('%d.%m.%Y %H:%M'))
                payment_item.setText(1, order.service)
                payment_item.setText(2, f"{order.paid_amount:,.2f}₽")
                payment_item.setText(3, order.created_date.strftime('%d.%m.%Y %H:%M'))
                payment_item.setText(4, f"{order.cost:,.2f}₽")
                payment_item.setText(5, f"{order.remaining_amount:,.2f}₽")
                payment_item.setText(6, order.discount or "-")
                payment_item.setText(7, order.status)

                # Устанавливаем выравнивание для числовых значений
                for col in [2, 4, 5]:
                    payment_item.setTextAlignment(col, Qt.AlignLeft)

        # Устанавливаем размеры колонок
        header = tree.header()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setStretchLastSection(False)

        column_widths = [200, -1, 100, 150, 100, 100, 80, 100]
        for i, width in enumerate(column_widths):
            if width > 0:
                tree.setColumnWidth(i, width)

        layout.addWidget(tree)
        return tab

    def create_client_rating_tab(self):
        """Создание вкладки рейтинга клиента"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        try:
            # Сначала получаем статистику клиента
            client_stats = self.session.query(
                func.count(Order.id).label('orders_count'),
                func.sum(Order.cost).label('total_spent'),
                func.avg(Order.cost).label('avg_order'),
                func.sum(case((Order.remaining_amount > 0, 1), else_=0)).label('delayed_payments')
            ).filter(Order.fio == self.client_fio).first()

            # Получаем общее количество клиентов
            total_clients = self.session.query(func.count(func.distinct(Order.fio))).scalar()

            # Получаем позицию клиента
            position_by_orders = self.session.query(
                func.count(func.distinct(Order.fio))
            ).filter(
                self.session.query(func.count(Order.id))
                .filter(Order.fio != self.client_fio)
                .group_by(Order.fio)
                .having(func.count(Order.id) > client_stats.orders_count)
                .scalar_subquery()
            ).scalar() + 1

            # Создаем таблицу для рейтинга
            rating_table = QTreeWidget()
            rating_table.setHeaderHidden(True)
            rating_table.setColumnCount(2)
            rating_table.setRootIsDecorated(False)
            rating_table.setAlternatingRowColors(True)
            rating_table.setStyleSheet("""
                QTreeWidget {
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: white;
                    font-size: 13px;
                }
                QTreeWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                }
                QTreeWidget::item:selected {
                    background-color: #e3f2fd;
                    color: #1565C0;
                }
            """)

            # Добавляем данные
            rating_data = [
                ("🏆 Рейтинг клиента", ""),
                ("🎯 Позиция среди клиентов:", f"{position_by_orders} из {total_clients}"),
                ("📦 Количество заказов:", f"{client_stats.orders_count}"),
                ("💰 Общая сумма заказов:", f"{client_stats.total_spent:,.2f}₽"),
                ("📊 Средний чек:", f"{client_stats.avg_order:,.2f}₽"),
                ("⚠️ Просроченные платежи:", f"{client_stats.delayed_payments}")
            ]

            for label_text, value_text in rating_data:
                item = QTreeWidgetItem(rating_table)
                item.setText(0, label_text)
                item.setText(1, value_text)
                if not value_text:  # Для заголовка
                    font = item.font(0)
                    font.setBold(True)
                    item.setFont(0, font)
                else:
                    item.setTextAlignment(1, Qt.AlignLeft)

            # Устанавливаем размеры колонок
            rating_table.setColumnWidth(0, 200)
            rating_table.setColumnWidth(1, 150)

            layout.addWidget(rating_table)

            # Добавляем рекомендации
            recommendations = QTreeWidget()
            recommendations.setHeaderHidden(True)
            recommendations.setColumnCount(1)
            recommendations.setRootIsDecorated(False)
            recommendations.setStyleSheet(rating_table.styleSheet())

            # Заголовок рекомендаций
            header_item = QTreeWidgetItem(recommendations, ["💡 Рекомендации"])
            font = header_item.font(0)
            font.setBold(True)
            header_item.setFont(0, font)

            # Генерируем рекомендации
            recs = [
                "⭐ Премиум клиент - рекомендуется предложить VIP-обслуживание" if client_stats.orders_count >= 10
                else "✨ Постоянный клиент - рекомендуется увеличить скидку" if client_stats.orders_count >= 5
                else "📈 Новый клиент - рекомендуется предложить программу лояльности",

                "💎 Высокий средний чек - рекомендуется индивидуальное обслуживание"
                if client_stats.avg_order > 5000 else "",

                "✅ Отличная платежная дисциплина - можно предложить отсрочку платежа"
                if client_stats.delayed_payments == 0
                else "⚠️ Есть просрочки платежей - рекомендуется предоплата"
            ]

            for rec in recs:
                if rec:  # Добавляем только непустые рекомендации
                    QTreeWidgetItem(recommendations, [rec])

            recommendations.setColumnWidth(0, 400)
            layout.addWidget(recommendations)
            layout.addStretch()

        except Exception as e:
            error_label = QLabel(f"Ошибка при загрузке данных: {str(e)}")
            error_label.setStyleSheet("color: red;")
            layout.addWidget(error_label)

        return tab



    def create_predictions_tab(self):
        """Создание вкладки прогнозов"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Получаем историю заказов клиента
        orders = self.session.query(
            Order.created_date,
            Order.payment_date,
            Order.service,
            Order.cost,
            Order.paid_amount
        ).filter(
            Order.fio == self.client_fio
        ).order_by(Order.created_date).all()

        # Создаем фрейм для прогнозов
        predictions_frame = QFrame()
        predictions_frame.setStyleSheet("""
                    QFrame {
                        background: white;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        padding: 10px;
                    }
                """)
        predictions_layout = QVBoxLayout(predictions_frame)

        # Заголовок
        title = QLabel("🔮 Прогнозы и тенденции")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        predictions_layout.addWidget(title)

        # Анализ периодичности заказов
        if len(orders) >= 2:
            # Рассчитываем среднее время между заказами
            time_between_orders = []
            for i in range(1, len(orders)):
                delta = orders[i].created_date - orders[i - 1].created_date
                time_between_orders.append(delta.days)

            avg_time = sum(time_between_orders) / len(time_between_orders)

            # Прогноз следующего заказа
            last_order = orders[-1].created_date
            next_order = last_order + timedelta(days=avg_time)

            prediction = QLabel(f"📅 Следующий заказ ожидается около: {next_order.strftime('%d.%m.%Y')}")
            predictions_layout.addWidget(prediction)

        # Анализ платежного поведения
        if orders:
            payment_delays = []
            for order in orders:
                if order.payment_date and order.created_date:
                    delay = (order.payment_date - order.created_date).days
                    payment_delays.append(delay)

            if payment_delays:
                avg_payment_delay = sum(payment_delays) / len(payment_delays)
                payment_info = QLabel(f"⏱️ Среднее время оплаты: {avg_payment_delay:.1f} дней")
                predictions_layout.addWidget(payment_info)

        # Анализ предпочтений по услугам
        service_counts = {}
        for order in orders:
            service_counts[order.service] = service_counts.get(order.service, 0) + 1

        if service_counts:
            favorite_service = max(service_counts.items(), key=lambda x: x[1])[0]
            service_info = QLabel(f"👑 Предпочитаемая услуга: {favorite_service}")
            predictions_layout.addWidget(service_info)

        layout.addWidget(predictions_frame)

        # Добавляем прогноз роста расходов
        if len(orders) >= 2:
            costs = [order.cost for order in orders]
            avg_growth = (costs[-1] - costs[0]) / len(costs)

            growth_frame = QFrame()
            growth_frame.setStyleSheet("""
                        QFrame {
                            background: white;
                            border: 1px solid #ddd;
                            border-radius: 4px;
                            padding: 10px;
                            margin-top: 20px;
                        }
                    """)
            growth_layout = QVBoxLayout(growth_frame)

            growth_title = QLabel("📈 Прогноз расходов")
            growth_title.setFont(QFont("Arial", 12, QFont.Bold))
            growth_layout.addWidget(growth_title)

            if avg_growth > 0:
                trend = "рост"
                emoji = "📈"
            else:
                trend = "снижение"
                emoji = "📉"

            growth_info = QLabel(
                f"{emoji} Наблюдается {trend} среднего чека на "
                f"{abs(avg_growth):,.2f}₽ за заказ"
            )
            growth_layout.addWidget(growth_info)

            # Прогноз на следующий заказ
            next_cost = costs[-1] + avg_growth
            next_order_cost = QLabel(
                f"💰 Ожидаемая сумма следующего заказа: {next_cost:,.2f}₽"
            )
            growth_layout.addWidget(next_order_cost)

            layout.addWidget(growth_frame)

        return tab

    def export_to_pdf(self):
        """Экспорт статистики в PDF"""
        try:
            # Создаем имя файла
            file_name = f"Статистика_{self.client_fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить статистику",
                file_name,
                "PDF files (*.pdf)"
            )

            if file_path:
                # Регистрируем шрифт для поддержки кириллицы
                try:
                    pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
                except:
                    try:
                        pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/TTF/DejaVuSans.ttf'))
                    except:
                        QMessageBox.warning(self, "Предупреждение", "Проблема с загрузкой шрифта")
                        return

                # Создаем документ
                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=A4,
                    rightMargin=30,
                    leftMargin=30,
                    topMargin=30,
                    bottomMargin=30
                )

                elements = []
                styles = getSampleStyleSheet()

                # Настраиваем стили
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

                subtitle_style = ParagraphStyle(
                    'CustomSubtitle',
                    parent=styles['Heading2'],
                    fontSize=14,
                    fontName='Arial'
                )

                # Общий стиль для всех таблиц
                table_style = TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('PADDING', (0, 0), (-1, -1), 6),
                ])

                # 1. Титульная страница
                elements.append(Paragraph(f"Аналитический отчет", title_style))
                elements.append(Paragraph(f"Клиент: {self.client_fio}", subtitle_style))
                elements.append(
                    Paragraph(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
                elements.append(PageBreak())

                # 2. Общая статистика
                elements.append(Paragraph("Общая статистика", title_style))
                elements.append(Spacer(1, 10))

                stats = self.session.query(
                    func.count(Order.id).label('total_orders'),
                    func.sum(Order.cost).label('total_cost'),
                    func.avg(Order.cost).label('avg_cost'),
                    func.sum(Order.remaining_amount).label('total_debt')
                ).filter(Order.fio == self.client_fio).first()

                stats_data = [
                    ['Показатель', 'Значение'],
                    ['Всего заказов', str(stats.total_orders)],
                    ['Общая сумма заказов', f"{stats.total_cost:,.2f}₽"],
                    ['Средний чек', f"{stats.avg_cost:,.2f}₽"],
                    ['Текущая задолженность', f"{stats.total_debt:,.2f}₽"]
                ]

                stats_table = Table(stats_data, colWidths=[200, 300])
                stats_table.setStyle(table_style)
                elements.append(stats_table)
                elements.append(PageBreak())

                # 3. История заказов
                elements.append(Paragraph("История заказов", title_style))
                elements.append(Spacer(1, 10))

                orders = self.session.query(Order).filter(
                    Order.fio == self.client_fio
                ).order_by(Order.created_date.desc()).all()

                if orders:
                    orders_data = [['Дата создания', 'Услуга', 'Стоимость', 'Скидка', 'Статус']]
                    for order in orders:
                        orders_data.append([
                            order.created_date.strftime('%d.%m.%Y'),
                            order.service,
                            f"{order.cost:,.2f}₽",
                            order.discount or "-",
                            order.status
                        ])

                    orders_table = Table(orders_data, colWidths=[80, 200, 80, 70, 100])
                    orders_table.setStyle(table_style)
                    elements.append(orders_table)
                elements.append(PageBreak())

                # 4. История оплат
                elements.append(Paragraph("История оплат", title_style))
                elements.append(Spacer(1, 10))

                payments = self.session.query(Order).filter(
                    Order.fio == self.client_fio,
                    Order.paid_amount > 0
                ).order_by(Order.payment_date.desc()).all()

                if payments:
                    payments_data = [['Дата оплаты', 'Услуга', 'Сумма оплаты', 'Остаток', 'Статус']]
                    for payment in payments:
                        payments_data.append([
                            payment.payment_date.strftime('%d.%m.%Y') if payment.payment_date else "-",
                            payment.service,
                            f"{payment.paid_amount:,.2f}₽",
                            f"{payment.remaining_amount:,.2f}₽",
                            payment.status
                        ])

                    payments_table = Table(payments_data, colWidths=[80, 200, 80, 80, 90])
                    payments_table.setStyle(table_style)
                    elements.append(payments_table)
                elements.append(PageBreak())

                # 5. Рейтинг клиента
                elements.append(Paragraph("Рейтинг клиента", title_style))
                elements.append(Spacer(1, 10))

                # Получаем статистику для рейтинга
                client_stats = self.session.query(
                    func.count(Order.id).label('orders_count'),
                    func.sum(Order.cost).label('total_spent'),
                    func.avg(Order.cost).label('avg_order'),
                    func.sum(case((Order.remaining_amount > 0, 1), else_=0)).label('delayed_payments')
                ).filter(Order.fio == self.client_fio).first()

                total_clients = self.session.query(func.count(func.distinct(Order.fio))).scalar()

                position_by_orders = self.session.query(
                    func.count(func.distinct(Order.fio))
                ).filter(
                    self.session.query(func.count(Order.id))
                    .filter(Order.fio != self.client_fio)
                    .group_by(Order.fio)
                    .having(func.count(Order.id) > client_stats.orders_count)
                    .scalar_subquery()
                ).scalar() + 1

                rating_data = [
                    ['Показатель', 'Значение'],
                    ['Позиция среди клиентов', f"{position_by_orders} из {total_clients}"],
                    ['Количество заказов', f"{client_stats.orders_count}"],
                    ['Общая сумма заказов', f"{client_stats.total_spent:,.2f}₽"],
                    ['Средний чек', f"{client_stats.avg_order:,.2f}₽"],
                    ['Просроченные платежи', f"{client_stats.delayed_payments}"]
                ]

                rating_table = Table(rating_data, colWidths=[200, 300])
                rating_table.setStyle(table_style)
                elements.append(rating_table)
                elements.append(Spacer(1, 20))

                # 6. Рекомендации
                elements.append(Paragraph("Рекомендации", subtitle_style))
                elements.append(Spacer(1, 10))

                # Генерируем рекомендации
                recs = [
                    "⭐ Премиум клиент - рекомендуется предложить VIP-обслуживание"
                    if client_stats.orders_count >= 10
                    else "✨ Постоянный клиент - рекомендуется увеличить скидку"
                    if client_stats.orders_count >= 5
                    else "📈 Новый клиент - рекомендуется предложить программу лояльности",

                    "💎 Высокий средний чек - рекомендуется индивидуальное обслуживание"
                    if client_stats.avg_order > 5000 else "",

                    "✅ Отличная платежная дисциплина - можно предложить отсрочку платежа"
                    if client_stats.delayed_payments == 0
                    else "⚠️ Есть просрочки платежей - рекомендуется предоплата"
                ]

                for rec in recs:
                    if rec:
                        elements.append(Paragraph(rec, normal_style))
                        elements.append(Spacer(1, 5))

                # Генерируем документ
                doc.build(elements)
                QMessageBox.information(self, "Успех", "Отчет успешно сохранен!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании отчета: {str(e)}")


