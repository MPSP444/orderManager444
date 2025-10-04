import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QWidget, QScrollArea,
                             QGridLayout, QFrame, QSizePolicy, QTableWidget,
                             QTableWidgetItem, QHeaderView, QProgressBar,
                             QGroupBox, QSpacerItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QBarSet, QBarSeries, QBarCategoryAxis
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from core.database import Order
from core.database_manager import DatabaseManager


class ClientDetailWindow(QDialog):
    """Окно с детальной информацией и аналитикой по клиенту"""

    def __init__(self, parent=None, client_name=None):
        super().__init__(parent)
        self.client_name = client_name
        self.db_manager = DatabaseManager()

        self.setWindowTitle(f"Детальная информация о клиенте: {client_name}")
        self.setMinimumSize(900, 700)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной layout
        main_layout = QVBoxLayout(self)

        # Заголовок
        header_layout = QHBoxLayout()

        self.title_label = QLabel(f"Аналитика клиента: {self.client_name}")
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2196F3;
            padding: 10px;
        """)
        header_layout.addWidget(self.title_label)

        # Кнопка экспорта (можно реализовать позже)
        export_btn = QPushButton("Экспорт данных")
        export_btn.setFixedWidth(150)
        export_btn.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        """)
        export_btn.clicked.connect(self.export_client_data)  # Добавляем обработчик
        header_layout.addWidget(export_btn)

        main_layout.addLayout(header_layout)

        # Создаем вкладки
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                background: white;
            }
            QTabBar::tab {
                background: #f5f5f5;
                border: 1px solid #ddd;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #2196F3;
                color: white;
                font-weight: bold;
            }
        """)

        # Создаем вкладки
        self.create_summary_tab()
        self.create_payment_history_tab()
        self.create_payment_analytics_tab()
        self.create_recommendations_tab()

        main_layout.addWidget(self.tab_widget, 1)

        # Кнопки внизу
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            background-color: #f44336;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        """)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

    def export_client_data(self):
        """Экспорт данных о клиенте в Excel файл"""
        try:
            from PyQt5.QtWidgets import QFileDialog, QMessageBox
            import pandas as pd
            from datetime import datetime
            import os
            import re

            # Запрашиваем путь для сохранения файла
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет",
                f"Анализ клиента {self.client_name}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "Excel Files (*.xlsx);;All Files (*)"
            )

            if not file_path:
                return

            # Добавляем расширение .xlsx если оно отсутствует
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'

            # Создаем writer для записи в Excel
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                workbook = writer.book

                # Создаем форматы для ячеек
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#2196F3',
                    'color': 'white',
                    'border': 1,
                    'align': 'center',
                    'valign': 'vcenter'
                })

                date_format = workbook.add_format({
                    'num_format': 'dd.mm.yyyy',
                    'align': 'center'
                })

                currency_format = workbook.add_format({
                    'num_format': '# ##0.00 ₽',
                    'align': 'right'
                })

                percent_format = workbook.add_format({
                    'num_format': '0.0%',
                    'align': 'center'
                })

                center_format = workbook.add_format({
                    'align': 'center',
                    'valign': 'vcenter'
                })

                # 1. Лист с общей информацией
                summary_data = {
                    'Параметр': [
                        'ФИО клиента',
                        'Всего заказов',
                        'Выполненных заказов',
                        'Отмененных заказов',
                        'Общая сумма заказов',
                        'Оплачено всего',
                        'Средний чек',
                        'Первый заказ',
                        'Последний заказ',
                        'Статус клиента',
                        'Индекс риска неплатежа',
                        'Платежная дисциплина',
                        'Лояльность',
                        'Регулярность заказов'
                    ],
                    'Значение': [
                        self.client_name,
                        self.summary_widgets["Всего заказов:"].text(),
                        self.summary_widgets["Выполненных заказов:"].text(),
                        self.summary_widgets["Отмененных заказов:"].text(),
                        self.summary_widgets["Общая сумма заказов:"].text(),
                        self.summary_widgets["Оплачено всего:"].text(),
                        self.summary_widgets["Средний чек:"].text(),
                        self.summary_widgets["Первый заказ:"].text(),
                        self.summary_widgets["Последний заказ:"].text(),
                        self.summary_widgets["Статус клиента:"].text(),
                        f"{self.risk_progress.value()}%",
                        self.discipline_value.text(),
                        self.loyalty_value.text(),
                        self.regularity_value.text()
                    ]
                }

                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Общая информация', index=False)

                # Форматирование листа общей информации
                summary_sheet = writer.sheets['Общая информация']
                summary_sheet.set_column('A:A', 25)
                summary_sheet.set_column('B:B', 40)

                # Применяем форматы
                for col_num, _ in enumerate(summary_df.columns.values):
                    summary_sheet.write(0, col_num, summary_df.columns[col_num], header_format)

                # 2. Лист с историей оплат
                payment_data = []
                for row in range(self.payment_table.rowCount()):
                    # Получаем стоимость и обрабатываем её
                    cost_text = self.payment_table.item(row, 2).text().replace('₽', '').strip()

                    # Функция для правильного преобразования цены в число
                    def parse_price(price_str):
                        # Удаляем все пробелы и символы валюты
                        price_str = re.sub(r'[^\d.,]', '', price_str)

                        # Обрабатываем разные форматы чисел
                        if ',' in price_str and '.' in price_str:
                            # Если есть и запятая, и точка - считаем запятую разделителем тысяч
                            price_str = price_str.replace(',', '')
                        elif ',' in price_str:
                            # Если есть только запятая - считаем её десятичным разделителем
                            price_str = price_str.replace(',', '.')

                        # Ищем все разделители "."
                        dots = price_str.count('.')
                        if dots > 1:
                            # Если точек больше одной, оставляем только последнюю как десятичный разделитель
                            parts = price_str.split('.')
                            price_str = ''.join(parts[:-1]) + '.' + parts[-1]

                        try:
                            return float(price_str)
                        except ValueError:
                            # Если все ещё не можем преобразовать, возвращаем 0
                            return 0.0

                    # Получаем значение "Дней до оплаты"
                    days_text = self.payment_table.item(row, 5).text()
                    try:
                        days_value = int(days_text) if days_text != '-' else 0
                    except ValueError:
                        days_value = 0

                    payment_data.append({
                        'ID': self.payment_table.item(row, 0).text(),
                        'Услуга': self.payment_table.item(row, 1).text(),
                        'Стоимость': parse_price(cost_text),
                        'Дата создания': self.payment_table.item(row, 3).text(),
                        'Дата оплаты': self.payment_table.item(row, 4).text(),
                        'Дней до оплаты': days_value,
                        'Статус': self.payment_table.item(row, 6).text(),
                        'Категория': self.payment_table.item(row, 7).text()
                    })

                payment_df = pd.DataFrame(payment_data)

                # Записываем в Excel
                payment_df.to_excel(writer, sheet_name='История оплат', index=False)

                # Форматирование листа истории оплат
                payment_sheet = writer.sheets['История оплат']
                payment_sheet.set_column('A:A', 8)
                payment_sheet.set_column('B:B', 40)
                payment_sheet.set_column('C:C', 15)
                payment_sheet.set_column('D:E', 15)
                payment_sheet.set_column('F:F', 15)
                payment_sheet.set_column('G:H', 15)

                # Применяем форматы к заголовкам
                for col_num, _ in enumerate(payment_df.columns.values):
                    payment_sheet.write(0, col_num, payment_df.columns[col_num], header_format)

                # Применяем форматы к ячейкам с ценами
                for row_num, row_data in enumerate(payment_df.values):
                    # Форматируем стоимость
                    payment_sheet.write(row_num + 1, 2, row_data[2], currency_format)

                # 3. Лист с аналитикой платежей
                if hasattr(self, 'payment_stats_widgets') and self.payment_stats_widgets:
                    analytics_data = {
                        'Параметр': [
                            'Средний срок оплаты',
                            'Медианный срок оплаты',
                            'Минимальный срок',
                            'Максимальный срок',
                            'Стандартное отклонение',
                            'Тренд сроков оплаты'
                        ],
                        'Значение': [
                            self.payment_stats_widgets["Средний срок оплаты:"].text(),
                            self.payment_stats_widgets["Медианный срок оплаты:"].text(),
                            self.payment_stats_widgets["Минимальный срок:"].text(),
                            self.payment_stats_widgets["Максимальный срок:"].text(),
                            self.payment_stats_widgets["Стандартное отклонение:"].text(),
                            self.payment_stats_widgets["Тренд сроков оплаты:"].text()
                        ]
                    }

                    analytics_df = pd.DataFrame(analytics_data)
                    analytics_df.to_excel(writer, sheet_name='Аналитика платежей', index=False)

                    analytics_sheet = writer.sheets['Аналитика платежей']
                    analytics_sheet.set_column('A:A', 25)
                    analytics_sheet.set_column('B:B', 40)

                    # Применяем форматы
                    for col_num, _ in enumerate(analytics_df.columns.values):
                        analytics_sheet.write(0, col_num, analytics_df.columns[col_num], header_format)

                # 4. Лист с рекомендациями
                recommendations_data = {
                    'Категория': [
                        'Условия работы',
                        'Управление рисками',
                        'Скидки',
                        'Бизнес-правила'
                    ],
                    'Рекомендации': [
                        self.payment_conditions_label.text().replace('<br>', '\n'),
                        self.risk_management_label.text().replace('<br>', '\n'),
                        self.discount_recommendations_label.text().replace('<br>', '\n'),
                        self.business_rules_label.text().replace('<br>', '\n')
                    ]
                }

                recommendations_df = pd.DataFrame(recommendations_data)
                recommendations_df.to_excel(writer, sheet_name='Рекомендации', index=False)

                recommendations_sheet = writer.sheets['Рекомендации']
                recommendations_sheet.set_column('A:A', 20)
                recommendations_sheet.set_column('B:B', 80)

                # Применяем форматы
                for col_num, _ in enumerate(recommendations_df.columns.values):
                    recommendations_sheet.write(0, col_num, recommendations_df.columns[col_num], header_format)

            # Показываем сообщение об успешном экспорте
            QMessageBox.information(
                self,
                "Экспорт завершен",
                f"Данные успешно экспортированы в файл:\n{file_path}",
                QMessageBox.Ok
            )

            # Открываем папку с файлом
            os.startfile(os.path.dirname(file_path))

        except ImportError as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Отсутствуют необходимые библиотеки",
                f"Для экспорта данных необходимо установить pandas и xlsxwriter:\n{str(e)}",
                QMessageBox.Ok
            )
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Ошибка при экспорте",
                f"Произошла ошибка при экспорте данных:\n{str(e)}",
                QMessageBox.Ok
            )


    def create_summary_tab(self):
        """Создание вкладки с общей информацией"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Создаем скролл для контента
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Создаем виджет содержимого
        content = QWidget()
        content_layout = QVBoxLayout(content)

        # Группа общей статистики
        stats_group = QGroupBox("Общая статистика")
        stats_grid = QGridLayout(stats_group)

        # Заполним сетку пустыми данными (будут обновлены при загрузке)
        labels = [
            "Всего заказов:", "Выполненных заказов:", "Отмененных заказов:",
            "Общая сумма заказов:", "Оплачено всего:", "Средний чек:",
            "Первый заказ:", "Последний заказ:", "Статус клиента:"
        ]

        self.summary_widgets = {}
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setStyleSheet("font-weight: bold;")

            value = QLabel("Загрузка...")
            value.setStyleSheet("color: #2196F3;")

            stats_grid.addWidget(label, i // 3, (i % 3) * 2)
            stats_grid.addWidget(value, i // 3, (i % 3) * 2 + 1)

            self.summary_widgets[label_text] = value

        content_layout.addWidget(stats_group)

        # Индикатор риска
        risk_group = QGroupBox("Оценка риска")
        risk_layout = QHBoxLayout(risk_group)

        risk_label = QLabel("Индекс риска неплатежа:")
        risk_label.setStyleSheet("font-weight: bold;")

        self.risk_progress = QProgressBar()
        self.risk_progress.setRange(0, 100)
        self.risk_progress.setValue(50)  # Будет обновлено при загрузке данных
        self.risk_progress.setTextVisible(True)
        self.risk_progress.setFormat("%v% (Средний риск)")
        self.risk_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4CAF50, stop:0.5 #FFC107, stop:1 #f44336);
                border-radius: 5px;
            }
        """)

        risk_layout.addWidget(risk_label)
        risk_layout.addWidget(self.risk_progress, 1)

        content_layout.addWidget(risk_group)

        # Категоризация клиента
        category_group = QGroupBox("Категоризация клиента")
        category_layout = QGridLayout(category_group)

        # Платежная дисциплина
        discipline_label = QLabel("Платежная дисциплина:")
        discipline_label.setStyleSheet("font-weight: bold;")
        self.discipline_value = QLabel("Загрузка...")
        self.discipline_value.setStyleSheet("color: #2196F3; font-weight: bold;")

        # Лояльность
        loyalty_label = QLabel("Лояльность:")
        loyalty_label.setStyleSheet("font-weight: bold;")
        self.loyalty_value = QLabel("Загрузка...")
        self.loyalty_value.setStyleSheet("color: #2196F3; font-weight: bold;")

        # Регулярность заказов
        regularity_label = QLabel("Регулярность заказов:")
        regularity_label.setStyleSheet("font-weight: bold;")
        self.regularity_value = QLabel("Загрузка...")
        self.regularity_value.setStyleSheet("color: #2196F3; font-weight: bold;")

        # Размещаем элементы в сетке
        category_layout.addWidget(discipline_label, 0, 0)
        category_layout.addWidget(self.discipline_value, 0, 1)
        category_layout.addWidget(loyalty_label, 1, 0)
        category_layout.addWidget(self.loyalty_value, 1, 1)
        category_layout.addWidget(regularity_label, 2, 0)
        category_layout.addWidget(self.regularity_value, 2, 1)

        content_layout.addWidget(category_group)

        # Добавляем пустое пространство снизу
        content_layout.addStretch()

        # Устанавливаем скролл
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "Общая информация")

    def create_payment_history_tab(self):
        """Создание вкладки с историей оплат"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Создаем таблицу для истории оплат
        self.payment_table = QTableWidget()
        self.payment_table.setColumnCount(8)
        self.payment_table.setHorizontalHeaderLabels([
            "ID", "Услуга", "Стоимость", "Дата создания",
            "Дата оплаты", "Дней до оплаты", "Статус", "Категория"
        ])

        # Настраиваем таблицу
        self.payment_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.payment_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.payment_table.setAlternatingRowColors(True)
        self.payment_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.payment_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #f0f0f0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)

        layout.addWidget(self.payment_table)

        self.tab_widget.addTab(tab, "История оплат")

    def create_payment_analytics_tab(self):
        """Создание вкладки с аналитикой платежей"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Контейнер для графиков
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)

        # График сроков оплаты
        self.payment_delay_chart = self.create_matplotlib_canvas()
        payment_delay_frame = QFrame()
        payment_delay_layout = QVBoxLayout(payment_delay_frame)
        payment_delay_layout.addWidget(QLabel("Сроки оплаты заказов (в днях)"))
        payment_delay_layout.addWidget(self.payment_delay_chart)

        # График среднего чека
        self.average_check_chart = self.create_matplotlib_canvas()
        average_check_frame = QFrame()
        average_check_layout = QVBoxLayout(average_check_frame)
        average_check_layout.addWidget(QLabel("Динамика среднего чека"))
        average_check_layout.addWidget(self.average_check_chart)

        # Добавляем графики в контейнер
        charts_layout.addWidget(payment_delay_frame)
        charts_layout.addWidget(average_check_frame)

        # Добавляем контейнер с графиками
        layout.addWidget(charts_widget)

        # Статистика по срокам оплаты
        stats_group = QGroupBox("Статистика сроков оплаты")
        stats_layout = QGridLayout(stats_group)

        # Метки для статистики
        labels = [
            "Средний срок оплаты:", "Медианный срок оплаты:", "Минимальный срок:",
            "Максимальный срок:", "Стандартное отклонение:", "Тренд сроков оплаты:"
        ]

        self.payment_stats_widgets = {}
        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            label.setStyleSheet("font-weight: bold;")

            value = QLabel("Загрузка...")
            value.setStyleSheet("color: #2196F3;")

            stats_layout.addWidget(label, i // 3, (i % 3) * 2)
            stats_layout.addWidget(value, i // 3, (i % 3) * 2 + 1)

            self.payment_stats_widgets[label_text] = value

        layout.addWidget(stats_group)

        self.tab_widget.addTab(tab, "Аналитика платежей")

    def create_recommendations_tab(self):
        """Создание вкладки с рекомендациями"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Создаем скролл для контента
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        # Создаем виджет содержимого
        content = QWidget()
        content_layout = QVBoxLayout(content)

        # Рекомендации по условиям работы
        conditions_group = QGroupBox("Рекомендуемые условия работы")
        conditions_layout = QVBoxLayout(conditions_group)

        self.payment_conditions_label = QLabel("Загрузка...")
        self.payment_conditions_label.setWordWrap(True)
        self.payment_conditions_label.setStyleSheet("""
            padding: 10px;
            background-color: #e3f2fd;
            border-radius: 5px;
            border-left: 4px solid #2196F3;
        """)
        conditions_layout.addWidget(self.payment_conditions_label)

        content_layout.addWidget(conditions_group)

        # Рекомендации по управлению рисками
        risk_group = QGroupBox("Управление рисками")
        risk_layout = QVBoxLayout(risk_group)

        self.risk_management_label = QLabel("Загрузка...")
        self.risk_management_label.setWordWrap(True)
        self.risk_management_label.setStyleSheet("""
            padding: 10px;
            background-color: #fff8e1;
            border-radius: 5px;
            border-left: 4px solid #FFC107;
        """)
        risk_layout.addWidget(self.risk_management_label)

        content_layout.addWidget(risk_group)

        # Рекомендации по скидкам
        discount_group = QGroupBox("Рекомендации по скидкам")
        discount_layout = QVBoxLayout(discount_group)

        self.discount_recommendations_label = QLabel("Загрузка...")
        self.discount_recommendations_label.setWordWrap(True)
        self.discount_recommendations_label.setStyleSheet("""
            padding: 10px;
            background-color: #e8f5e9;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        """)
        discount_layout.addWidget(self.discount_recommendations_label)

        content_layout.addWidget(discount_group)

        # Бизнес-правила
        rules_group = QGroupBox("Бизнес-правила для клиента")
        rules_layout = QVBoxLayout(rules_group)

        self.business_rules_label = QLabel("Загрузка...")
        self.business_rules_label.setWordWrap(True)
        self.business_rules_label.setStyleSheet("""
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
            border-left: 4px solid #9E9E9E;
        """)
        rules_layout.addWidget(self.business_rules_label)

        content_layout.addWidget(rules_group)

        # Добавляем пустое пространство снизу
        content_layout.addStretch()

        # Устанавливаем скролл
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "Рекомендации")

    def create_matplotlib_canvas(self):
        """Создание холста для графика matplotlib"""
        figure = plt.figure(figsize=(5, 4))
        canvas = FigureCanvas(figure)
        canvas.setMinimumSize(QSize(300, 200))
        return canvas

    def load_data(self):
        """Загрузка данных о клиенте"""
        if not self.client_name:
            return

        try:
            with self.db_manager.session_scope() as session:
                # Получаем все заказы клиента
                orders = session.query(Order).filter(
                    Order.fio == self.client_name
                ).order_by(Order.created_date).all()

                if not orders:
                    return

                # Загружаем данные для каждой вкладки
                self.load_summary_data(orders)
                self.load_payment_history(orders)
                self.load_payment_analytics(orders)
                self.load_recommendations(orders)

        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")

    def load_summary_data(self, orders):
        """Загрузка общей информации о клиенте"""
        try:
            # Общая статистика
            total_orders = len(orders)
            completed_orders = sum(1 for o in orders if o.status == 'Выполнен')
            cancelled_orders = sum(1 for o in orders if o.status == 'Отказ')

            # Расчет финансовых данных
            total_amount = sum(o.total_amount or 0 for o in orders if o.status != 'Отказ')
            total_paid = sum(o.paid_amount or 0 for o in orders if o.status != 'Отказ')
            avg_check = total_amount / (total_orders - cancelled_orders) if (total_orders - cancelled_orders) > 0 else 0

            # Даты
            first_order_date = min(o.created_date for o in orders).strftime('%d.%m.%Y') if orders else "—"
            last_order_date = max(o.created_date for o in orders).strftime('%d.%m.%Y') if orders else "—"

            # Определение статуса клиента
            if total_orders >= 10:
                client_status = "Постоянный клиент"
            elif total_orders >= 5:
                client_status = "Активный клиент"
            elif total_orders >= 2:
                client_status = "Повторный клиент"
            else:
                client_status = "Новый клиент"

            # Обновляем виджеты
            self.summary_widgets["Всего заказов:"].setText(f"{total_orders}")
            self.summary_widgets["Выполненных заказов:"].setText(f"{completed_orders}")
            self.summary_widgets["Отмененных заказов:"].setText(f"{cancelled_orders}")
            self.summary_widgets["Общая сумма заказов:"].setText(f"{total_amount:,.2f} ₽")
            self.summary_widgets["Оплачено всего:"].setText(f"{total_paid:,.2f} ₽")
            self.summary_widgets["Средний чек:"].setText(f"{avg_check:,.2f} ₽")
            self.summary_widgets["Первый заказ:"].setText(first_order_date)
            self.summary_widgets["Последний заказ:"].setText(last_order_date)
            self.summary_widgets["Статус клиента:"].setText(client_status)

            # Расчет и отображение риска
            risk_score = self.calculate_risk_score(orders)
            self.risk_progress.setValue(risk_score)

            risk_text = "Низкий риск"
            risk_color = "#4CAF50"
            if risk_score >= 75:
                risk_text = "Высокий риск"
                risk_color = "#f44336"
            elif risk_score >= 40:
                risk_text = "Средний риск"
                risk_color = "#FFC107"

            self.risk_progress.setFormat(f"{risk_score}% ({risk_text})")

            # Категоризация клиента
            # 1. Платежная дисциплина
            paid_orders = [o for o in orders if o.payment_date and o.status == 'Выполнен']
            if paid_orders:
                avg_days_to_pay = sum((o.payment_date - o.created_date).days for o in paid_orders) / len(paid_orders)

                if avg_days_to_pay <= 7:
                    discipline = "Отличная (оплата в течение недели)"
                    discipline_color = "#4CAF50"
                elif avg_days_to_pay <= 14:
                    discipline = "Хорошая (оплата в течение двух недель)"
                    discipline_color = "#8BC34A"
                elif avg_days_to_pay <= 30:
                    discipline = "Средняя (оплата в течение месяца)"
                    discipline_color = "#FFC107"
                else:
                    discipline = "Низкая (оплата более месяца)"
                    discipline_color = "#f44336"

                self.discipline_value.setText(discipline)
                self.discipline_value.setStyleSheet(f"color: {discipline_color}; font-weight: bold;")
            else:
                self.discipline_value.setText("Нет данных")

            # 2. Лояльность
            if total_orders >= 10:
                loyalty = "Высокая (10+ заказов)"
                loyalty_color = "#4CAF50"
            elif total_orders >= 5:
                loyalty = "Средняя (5-9 заказов)"
                loyalty_color = "#8BC34A"
            elif total_orders >= 2:
                loyalty = "Начальная (2-4 заказа)"
                loyalty_color = "#FFC107"
            else:
                loyalty = "Новый клиент (1 заказ)"
                loyalty_color = "#9E9E9E"

            self.loyalty_value.setText(loyalty)
            self.loyalty_value.setStyleSheet(f"color: {loyalty_color}; font-weight: bold;")

            # 3. Регулярность заказов
            if len(orders) >= 3:
                # Расчет среднего интервала между заказами
                dates = sorted([o.created_date for o in orders])
                intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
                avg_interval = sum(intervals) / len(intervals) if intervals else 0

                if avg_interval <= 30:
                    regularity = "Высокая (заказы ежемесячно)"
                    regularity_color = "#4CAF50"
                elif avg_interval <= 90:
                    regularity = "Средняя (заказы раз в квартал)"
                    regularity_color = "#8BC34A"
                elif avg_interval <= 180:
                    regularity = "Низкая (заказы раз в полгода)"
                    regularity_color = "#FFC107"
                else:
                    regularity = "Редкая (заказы реже, чем раз в полгода)"
                    regularity_color = "#f44336"

                self.regularity_value.setText(regularity)
                self.regularity_value.setStyleSheet(f"color: {regularity_color}; font-weight: bold;")
            else:
                self.regularity_value.setText("Недостаточно данных")

        except Exception as e:
            print(f"Ошибка при загрузке общей информации: {e}")

    def calculate_risk_score(self, orders):
        """Расчет оценки риска для клиента"""
        try:
            # Факторы риска:
            risk_factors = {
                'payment_delay': 0,  # Задержки платежей
                'unpaid_orders': 0,  # Неоплаченные заказы
                'cancellations': 0,  # Отмены заказов
                'payment_history': 0  # История платежей
            }

            # 1. Задержки платежей
            paid_orders = [o for o in orders if o.payment_date and o.created_date]
            if paid_orders:
                avg_days_to_pay = sum((o.payment_date - o.created_date).days for o in paid_orders) / len(paid_orders)

                if avg_days_to_pay > 30:
                    risk_factors['payment_delay'] = 40
                elif avg_days_to_pay > 14:
                    risk_factors['payment_delay'] = 20
                elif avg_days_to_pay > 7:
                    risk_factors['payment_delay'] = 10

            # 2. Неоплаченные заказы
            active_orders = [o for o in orders if o.status not in ['Выполнен', 'Отказ']]
            if active_orders:
                unpaid_ratio = len(active_orders) / len(orders)
                risk_factors['unpaid_orders'] = min(int(unpaid_ratio * 100), 30)

            # 3. Отмены заказов
            cancelled = sum(1 for o in orders if o.status == 'Отказ')
            if cancelled:
                cancel_ratio = cancelled / len(orders)
                risk_factors['cancellations'] = min(int(cancel_ratio * 100), 20)

            # 4. История платежей
            if len(orders) <= 2:
                # Новые клиенты - средний риск по умолчанию
                risk_factors['payment_history'] = 15
            elif len(paid_orders) / len(orders) < 0.5:
                # Менее половины заказов оплачено
                risk_factors['payment_history'] = 10

            # Общий риск (максимум 100)
            total_risk = sum(risk_factors.values())
            return min(total_risk, 100)

        except Exception as e:
            print(f"Ошибка при расчете риска: {e}")
            return 50  # Средний риск по умолчанию

    def load_payment_history(self, orders):
        """Загрузка истории оплат"""
        try:
            # Очищаем таблицу
            self.payment_table.setRowCount(0)

            # Заполняем таблицу данными
            for order in orders:
                row = self.payment_table.rowCount()
                self.payment_table.insertRow(row)

                # Расчет дней до оплаты
                days_to_pay = "-"
                payment_category = "-"

                if order.payment_date and order.created_date:
                    days = (order.payment_date - order.created_date).days
                    days_to_pay = str(days)

                    # Определение категории оплаты
                    if days <= 7:
                        payment_category = "Быстрая"
                        category_color = QColor("#4CAF50")  # Зеленый
                    elif days <= 14:
                        payment_category = "Средняя"
                        category_color = QColor("#8BC34A")  # Светло-зеленый
                    elif days <= 30:
                        payment_category = "Медленная"
                        category_color = QColor("#FFC107")  # Желтый
                    else:
                        payment_category = "Просроченная"
                        category_color = QColor("#f44336")  # Красный

                # ID заказа
                id_item = QTableWidgetItem(str(order.id))
                id_item.setTextAlignment(Qt.AlignCenter)
                self.payment_table.setItem(row, 0, id_item)

                # Услуга
                service_item = QTableWidgetItem(order.service)
                self.payment_table.setItem(row, 1, service_item)

                # Стоимость
                cost_value = order.total_amount or order.cost or 0
                cost_item = QTableWidgetItem(f"{cost_value:,.2f} ₽")
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.payment_table.setItem(row, 2, cost_item)

                # Дата создания
                created_date = order.created_date.strftime('%d.%m.%Y') if order.created_date else "-"
                created_item = QTableWidgetItem(created_date)
                created_item.setTextAlignment(Qt.AlignCenter)
                self.payment_table.setItem(row, 3, created_item)

                # Дата оплаты
                payment_date = order.payment_date.strftime('%d.%m.%Y') if order.payment_date else "-"
                payment_item = QTableWidgetItem(payment_date)
                payment_item.setTextAlignment(Qt.AlignCenter)
                self.payment_table.setItem(row, 4, payment_item)

                # Дней до оплаты
                days_item = QTableWidgetItem(days_to_pay)
                days_item.setTextAlignment(Qt.AlignCenter)
                self.payment_table.setItem(row, 5, days_item)

                # Статус
                status_item = QTableWidgetItem(order.status)
                if order.status == 'Выполнен':
                    status_item.setForeground(QColor("#4CAF50"))  # Зеленый
                elif order.status == 'Отказ':
                    status_item.setForeground(QColor("#f44336"))  # Красный
                elif order.status == 'В работе':
                    status_item.setForeground(QColor("#2196F3"))  # Синий
                self.payment_table.setItem(row, 6, status_item)

                # Категория оплаты
                category_item = QTableWidgetItem(payment_category)
                if payment_category != "-":
                    category_item.setForeground(category_color)
                self.payment_table.setItem(row, 7, category_item)

                # Красим строку для неоплаченных заказов
                if order.status != 'Выполнен' and order.status != 'Отказ' and order.created_date:
                    days_since_creation = (datetime.now().date() - order.created_date).days
                    if days_since_creation > 30:
                        for col in range(self.payment_table.columnCount()):
                            self.payment_table.item(row, col).setBackground(QColor(255, 200, 200))

        except Exception as e:
            print(f"Ошибка при загрузке истории оплат: {e}")

    def load_payment_analytics(self, orders):
        """Загрузка аналитики платежей"""
        try:
            # Получаем только оплаченные заказы
            paid_orders = [o for o in orders if o.payment_date and o.created_date and o.status == 'Выполнен']

            if not paid_orders or len(paid_orders) < 2:
                # Устанавливаем заглушки для графиков, если недостаточно данных
                self.payment_delay_chart.figure.clear()
                self.payment_delay_chart.figure.text(0.5, 0.5, "Недостаточно данных для анализа",
                                                     ha='center', va='center', fontsize=12)

                self.average_check_chart.figure.clear()
                self.average_check_chart.figure.text(0.5, 0.5, "Недостаточно данных для анализа",
                                                     ha='center', va='center', fontsize=12)

                self.payment_delay_chart.draw()
                self.average_check_chart.draw()

                # Устанавливаем заглушки для статистики
                for widget in self.payment_stats_widgets.values():
                    widget.setText("Недостаточно данных")

                return

            # Рассчитываем статистику сроков оплаты
            payment_days = [(o.payment_date - o.created_date).days for o in paid_orders]

            avg_days = sum(payment_days) / len(payment_days)
            median_days = sorted(payment_days)[len(payment_days) // 2]
            min_days = min(payment_days)
            max_days = max(payment_days)

            # Стандартное отклонение
            std_dev = (sum((x - avg_days) ** 2 for x in payment_days) / len(payment_days)) ** 0.5

            # Тренд сроков оплаты (улучшается или ухудшается)
            # Сортируем по дате создания
            sorted_orders = sorted(paid_orders, key=lambda o: o.created_date)
            recent_days = [(o.payment_date - o.created_date).days for o in sorted_orders[-3:]]
            old_days = [(o.payment_date - o.created_date).days for o in sorted_orders[:3]]

            if recent_days and old_days:
                recent_avg = sum(recent_days) / len(recent_days)
                old_avg = sum(old_days) / len(old_days)

                if recent_avg < old_avg * 0.8:
                    trend = "Значительное улучшение"
                    trend_color = "#4CAF50"  # Зеленый
                elif recent_avg < old_avg:
                    trend = "Улучшение"
                    trend_color = "#8BC34A"  # Светло-зеленый
                elif recent_avg > old_avg * 1.2:
                    trend = "Значительное ухудшение"
                    trend_color = "#f44336"  # Красный
                elif recent_avg > old_avg:
                    trend = "Ухудшение"
                    trend_color = "#FFC107"  # Желтый
                else:
                    trend = "Без изменений"
                    trend_color = "#9E9E9E"  # Серый
            else:
                trend = "Недостаточно данных"
                trend_color = "#9E9E9E"  # Серый

            # Обновляем виджеты статистики
            self.payment_stats_widgets["Средний срок оплаты:"].setText(f"{avg_days:.1f} дней")
            self.payment_stats_widgets["Медианный срок оплаты:"].setText(f"{median_days} дней")
            self.payment_stats_widgets["Минимальный срок:"].setText(f"{min_days} дней")
            self.payment_stats_widgets["Максимальный срок:"].setText(f"{max_days} дней")
            self.payment_stats_widgets["Стандартное отклонение:"].setText(f"{std_dev:.1f} дней")

            trend_widget = self.payment_stats_widgets["Тренд сроков оплаты:"]
            trend_widget.setText(trend)
            trend_widget.setStyleSheet(f"color: {trend_color}; font-weight: bold;")

            # График сроков оплаты
            self.payment_delay_chart.figure.clear()
            ax = self.payment_delay_chart.figure.add_subplot(111)

            # Сортируем заказы по дате создания
            sorted_by_date = sorted(paid_orders, key=lambda o: o.created_date)
            dates = [o.created_date.strftime('%d.%m.%y') for o in sorted_by_date]
            delays = [(o.payment_date - o.created_date).days for o in sorted_by_date]

            ax.bar(range(len(dates)), delays, color='#2196F3')
            ax.set_xticks(range(len(dates)))
            ax.set_xticklabels(dates, rotation=45, ha='right')
            ax.set_ylabel('Дней до оплаты')
            ax.set_title('Сроки оплаты заказов', fontsize=12)

            # Добавляем среднюю линию
            ax.axhline(y=avg_days, color='r', linestyle='-', alpha=0.7, label=f'Среднее: {avg_days:.1f} дней')
            ax.legend()

            self.payment_delay_chart.figure.tight_layout()
            self.payment_delay_chart.draw()

            # График среднего чека
            self.average_check_chart.figure.clear()
            ax = self.average_check_chart.figure.add_subplot(111)

            # Рассчитываем средний чек по месяцам
            orders_by_month = {}
            for order in orders:
                if not order.created_date:
                    continue
                month_key = order.created_date.strftime('%Y-%m')
                if month_key not in orders_by_month:
                    orders_by_month[month_key] = []
                orders_by_month[month_key].append(order)

            months = sorted(orders_by_month.keys())
            avg_checks = []

            for month in months:
                month_orders = orders_by_month[month]
                total = sum(o.total_amount or o.cost or 0 for o in month_orders)
                avg = total / len(month_orders)
                avg_checks.append(avg)

            # Укорачиваем месяцы для отображения если их много
            if len(months) > 6:
                display_months = [m[-2:] + '/' + m[:4][2:] for m in months]  # формат ММ/ГГ
            else:
                display_months = [m[-2:] + '/' + m[:4] for m in months]  # формат ММ/ГГГГ

            ax.plot(range(len(months)), avg_checks, 'o-', color='#4CAF50', markersize=8)
            ax.set_xticks(range(len(months)))
            ax.set_xticklabels(display_months, rotation=45, ha='right')
            ax.set_ylabel('Средний чек, ₽')
            ax.set_title('Динамика среднего чека', fontsize=12)

            # Форматирование оси Y для отображения валюты
            import matplotlib.ticker as ticker
            def currency_formatter(x, pos):
                return f'{x:,.0f} ₽'

            ax.yaxis.set_major_formatter(ticker.FuncFormatter(currency_formatter))

            self.average_check_chart.figure.tight_layout()
            self.average_check_chart.draw()

        except Exception as e:
            print(f"Ошибка при загрузке аналитики платежей: {e}")

    def load_recommendations(self, orders):
        """Загрузка рекомендаций"""
        try:
            # Получаем только оплаченные заказы для анализа
            paid_orders = [o for o in orders if o.payment_date and o.created_date and o.status == 'Выполнен']
            unpaid_orders = [o for o in orders if o.status != 'Выполнен' and o.status != 'Отказ']

            # Рассчитываем средний срок оплаты
            avg_days_to_pay = 0
            if paid_orders:
                avg_days_to_pay = sum((o.payment_date - o.created_date).days for o in paid_orders) / len(paid_orders)

            # Рассчитываем общую сумму неоплаченных заказов
            total_unpaid = sum(o.remaining_amount or 0 for o in unpaid_orders)

            # 1. Рекомендации по условиям работы
            payment_conditions = []

            if not orders:
                payment_conditions.append("🔹 Новый клиент — рекомендуется стандартная предоплата 50%")
            elif avg_days_to_pay <= 7:
                payment_conditions.append(
                    "🔹 Надежный клиент с быстрой оплатой — возможна работа с минимальной предоплатой (30%)")
                payment_conditions.append("🔹 Рекомендуется предлагать программу лояльности для таких клиентов")
            elif avg_days_to_pay <= 14:
                payment_conditions.append(
                    "🔹 Клиент с хорошей платежной дисциплиной — рекомендуется стандартная предоплата 50%")
            elif avg_days_to_pay <= 30:
                payment_conditions.append(
                    "🔹 Клиент со средней платежной дисциплиной — рекомендуется повышенная предоплата 70%")
                payment_conditions.append("🔹 Установить четкие сроки оплаты в договоре")
            else:
                payment_conditions.append(
                    "⚠️ Клиент с низкой платежной дисциплиной — рекомендуется работа по 100% предоплате")
                payment_conditions.append("🔹 Обязательное указание штрафных санкций за просрочку платежа в договоре")

            if unpaid_orders:
                payment_conditions.append(
                    f"⚠️ Имеются неоплаченные заказы на сумму {total_unpaid:,.2f} ₽ — рекомендуется сначала получить оплату по существующим заказам")

            self.payment_conditions_label.setText("<br>".join(payment_conditions))

            # 2. Рекомендации по управлению рисками
            risk_recommendations = []

            risk_score = self.calculate_risk_score(orders)
            if risk_score >= 75:
                risk_recommendations.append(
                    "⚠️ <b>Высокий риск неплатежа</b> — необходимы дополнительные меры безопасности:")
                risk_recommendations.append("🔹 Работа только по 100% предоплате")
                risk_recommendations.append("🔹 Четкое документальное оформление всех договоренностей")
                risk_recommendations.append("🔹 Возможно потребуется дополнительное обеспечение (гарантийный депозит)")
            elif risk_score >= 40:
                risk_recommendations.append("⚠️ <b>Средний риск неплатежа</b> — рекомендуются следующие меры:")
                risk_recommendations.append("🔹 Повышенная предоплата (не менее 70%)")
                risk_recommendations.append("🔹 Регулярный мониторинг состояния оплат")
                risk_recommendations.append("🔹 Автоматические напоминания о платеже за 3 дня до срока")
            else:
                risk_recommendations.append("✅ <b>Низкий риск неплатежа</b> — стандартные меры достаточны:")
                risk_recommendations.append("🔹 Обычные условия предоплаты")
                risk_recommendations.append("🔹 Стандартное отслеживание сроков оплаты")

            # Добавляем рекомендации по текущим неоплаченным заказам
            if unpaid_orders:
                overdue_orders = [o for o in unpaid_orders if
                                  o.created_date and (datetime.now().date() - o.created_date).days > 30]
                if overdue_orders:
                    risk_recommendations.append(
                        f"⚠️ <b>Внимание!</b> {len(overdue_orders)} заказ(ов) с просрочкой более 30 дней")
                    risk_recommendations.append(
                        "🔹 Рекомендуется срочно связаться с клиентом для уточнения сроков оплаты")

            self.risk_management_label.setText("<br>".join(risk_recommendations))

            # 3. Рекомендации по скидкам
            discount_recommendations = []

            total_orders = len(orders)
            completed_orders = sum(1 for o in orders if o.status == 'Выполнен')

            if total_orders >= 10 and avg_days_to_pay <= 14:
                discount_recommendations.append("✅ <b>Постоянный надежный клиент</b> — рекомендуемая скидка 25-30%")
                discount_recommendations.append("🔹 Предложить персональный сервис и дополнительные услуги")
            elif total_orders >= 5 and avg_days_to_pay <= 30:
                discount_recommendations.append("✅ <b>Активный клиент</b> — рекомендуемая скидка 15-20%")
                discount_recommendations.append("🔹 Предложить программу лояльности для увеличения числа заказов")
            elif total_orders >= 3:
                discount_recommendations.append("✅ <b>Регулярный клиент</b> — рекомендуемая скидка 10%")
            elif avg_days_to_pay > 30:
                discount_recommendations.append("⚠️ <b>Скидка не рекомендуется</b> из-за низкой платежной дисциплины")
                discount_recommendations.append("🔹 Предложить скидку только при условии сокращения сроков оплаты")
            else:
                discount_recommendations.append("🔹 <b>Стандартная система скидок</b> в зависимости от объема заказа")

            self.discount_recommendations_label.setText("<br>".join(discount_recommendations))

            # 4. Бизнес-правила
            business_rules = []

            # Правила в зависимости от категории клиента и его платежной дисциплины
            if total_orders < 3:
                business_rules.append("🔹 <b>Новый клиент</b> — применять стандартные условия договора")
                business_rules.append("🔹 Требовать предоплату не менее 50%")
                business_rules.append("🔹 Регулярно напоминать о сроках оплаты")
            elif avg_days_to_pay > 30:
                business_rules.append("⚠️ <b>Проблемная платежная дисциплина</b> — особые условия работы:")
                business_rules.append("🔹 Предоплата не менее 70%, желательно 100%")
                business_rules.append("🔹 Установить строгие сроки выполнения каждого этапа работ")
                business_rules.append("🔹 Предоставлять результаты только после поступления оплаты")
            elif avg_days_to_pay <= 7 and total_orders >= 5:
                business_rules.append("✅ <b>Привилегированный клиент</b> — особые условия работы:")
                business_rules.append("🔹 Возможность предоставления гибких условий оплаты")
                business_rules.append("🔹 Приоритетное выполнение заказов")
                business_rules.append("🔹 Возможность применения индивидуальных тарифов")
            else:
                business_rules.append("🔹 <b>Стандартные бизнес-правила</b>:")
                business_rules.append("🔹 Предоплата 50%, остаток при сдаче работы")
                business_rules.append("🔹 Стандартные сроки выполнения работ")

            self.business_rules_label.setText("<br>".join(business_rules))

        except Exception as e:
            print(f"Ошибка при загрузке рекомендаций: {e}")


# Если запускать файл напрямую для тестирования
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Для тестирования с конкретным клиентом
    window = ClientDetailWindow(client_name="Иванов Иван Иванович")
    window.show()

    sys.exit(app.exec_())