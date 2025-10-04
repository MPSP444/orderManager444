from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QGroupBox, QTableWidget, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt
from sqlalchemy import func
from core.database import init_database, Order
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog

class DetailedInfoWindow(QDialog):
    def __init__(self, parent=None, client_fio=None):
        super().__init__(parent)
        self.client_fio = client_fio
        self.session = init_database()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Подробная информация: {self.client_fio}")
        self.setGeometry(300, 300, 1000, 600)

        layout = QVBoxLayout(self)

        # Общая статистика
        stats_group = QGroupBox("Общая статистика")
        stats_layout = QVBoxLayout()

        stats_data = self.get_client_statistics()

        # Основные показатели
        stats_layout.addWidget(QLabel(f"Всего заказов: {stats_data['total_orders']}"))
        stats_layout.addWidget(QLabel(f"Общая сумма всех заказов: {stats_data['total_cost']} руб."))
        stats_layout.addWidget(QLabel(f"Оплачено всего: {stats_data['total_paid']} руб."))
        stats_layout.addWidget(QLabel(f"Общий остаток: {stats_data['total_remaining']} руб."))

        # Статусы заказов
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel(f"Новых: {stats_data['status_new']}"))
        status_layout.addWidget(QLabel(f"В работе: {stats_data['status_in_progress']}"))
        # В секции статистики добавим:
        status_layout.addWidget(QLabel(f"В ожидании оплаты: {stats_data['status_waiting']}"))
        status_layout.addWidget(QLabel(f"Выполнено: {stats_data['status_completed']}"))
        status_layout.addWidget(QLabel(f"Отменено: {stats_data['status_canceled']}"))
        stats_layout.addLayout(status_layout)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Таблица всех заказов
        orders_group = QGroupBox("История заказов")
        orders_layout = QVBoxLayout()
        # Устанавливаем минимальный размер для GroupBox
        orders_group.setMinimumSize(900, 400)  # Ширина: 900, Высота: 400
        # Устанавливаем отступы внутри GroupBox
        orders_layout.setContentsMargins(10, 10, 10, 10)
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(10)
        self.orders_table.setHorizontalHeaderLabels([
            'ID', 'Дата', 'Услуга', 'Тема', 'Стоимость',
            'Оплачено', 'Остаток', 'Срок', 'Статус', 'Скидка'
        ])

        # Заполняем таблицу заказов
        self.fill_orders_table()

        orders_layout.addWidget(self.orders_table)
        orders_group.setLayout(orders_layout)
        layout.addWidget(orders_group)
        layout.addStretch(1)
        button_layout = QHBoxLayout()

        # Кнопка создания PDF
        pdf_btn = QPushButton("Сохранить в PDF")
        pdf_btn.clicked.connect(self.create_detailed_pdf)
        button_layout.addWidget(pdf_btn)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def get_client_statistics(self):
        """Получение статистики по клиенту"""
        try:
            orders = self.session.query(Order).filter(Order.fio == self.client_fio).all()

            stats = {
                'total_orders': len(orders),
                'total_cost': sum(order.cost for order in orders),
                'total_paid': sum(order.paid_amount for order in orders),
                'total_remaining': sum(order.remaining_amount for order in orders),
                'status_new': len([o for o in orders if o.status == 'Новый']),
                'status_in_progress': len([o for o in orders if o.status == 'В работе']),
                'status_waiting': len([o for o in orders if o.status == 'В ожидании оплаты']),
                'status_completed': len([o for o in orders if o.status == 'Выполнен']),
                'status_canceled': len([o for o in orders if o.status == 'Отменен'])
            }

            return stats

        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return None
    def fill_orders_table(self):
        """Заполнение таблицы заказов"""
        try:
            # Получаем все заказы клиента, отсортированные по дате
            orders = self.session.query(Order) \
                .filter(Order.fio == self.client_fio) \
                .order_by(Order.created_date.desc()) \
                .all()

            self.orders_table.setRowCount(len(orders))

            for row, order in enumerate(orders):
                # Заполняем данные о заказе
                self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.id)))

                # Форматируем дату
                date_str = order.created_date.strftime('%d.%m.%Y') if order.created_date else 'Не указана'
                self.orders_table.setItem(row, 1, QTableWidgetItem(date_str))

                self.orders_table.setItem(row, 2, QTableWidgetItem(str(order.service)))
                self.orders_table.setItem(row, 3, QTableWidgetItem(str(order.theme or '')))
                self.orders_table.setItem(row, 4, QTableWidgetItem(f"{order.cost} руб."))
                self.orders_table.setItem(row, 5, QTableWidgetItem(f"{order.paid_amount} руб."))
                self.orders_table.setItem(row, 6, QTableWidgetItem(f"{order.remaining_amount} руб."))
                self.orders_table.setItem(row, 7, QTableWidgetItem(str(order.deadline or '')))
                self.orders_table.setItem(row, 8, QTableWidgetItem(str(order.status)))
                self.orders_table.setItem(row, 9, QTableWidgetItem(str(order.discount or '')))

            # Настраиваем размеры колонок
            self.orders_table.resizeColumnsToContents()

        except Exception as e:
            print(f"Ошибка при заполнении таблицы: {e}")

    def create_detailed_pdf(self):
        """Создание подробного PDF отчета"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # Регистрируем шрифт с поддержкой кириллицы
            try:
                pdfmetrics.registerFont(TTFont('CustomFont', 'C:\\Windows\\Fonts\\times.ttf'))
            except:
                try:
                    pdfmetrics.registerFont(TTFont('CustomFont', '/usr/share/fonts/TTF/DejaVuSans.ttf'))
                except:
                    raise Exception("Не удалось загрузить шрифт с поддержкой кириллицы")

            file_name = f"Отчет_{self.client_fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчет",
                file_name,
                "PDF files (*.pdf)"
            )

            if file_path:
                # Создаем документ
                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=A4,
                    rightMargin=15 * mm,
                    leftMargin=15 * mm,
                    topMargin=15 * mm,
                    bottomMargin=15 * mm,
                    encoding='utf-8'  # Добавляем явное указание кодировки
                )

                elements = []

                # Создаем стили с нашим шрифтом
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=14,
                    spaceAfter=10,
                    alignment=1,
                    fontName='CustomFont'  # Используем наш шрифт
                )

                # Заголовок с явным указанием кодировки
                elements.append(Paragraph("ПОДРОБНАЯ ИНФОРМАЦИЯ О КЛИЕНТЕ", title_style))
                elements.append(Spacer(1, 10))

                # Получаем данные
                stats = self.get_client_statistics()
                client = self.session.query(Order).filter(Order.fio == self.client_fio).first()

                # Основная информация
                info_data = [
                    ['ФИО:', str(self.client_fio), 'Телефон:', str(client.phone if client else '-')],
                    ['Группа:', str(client.group if client else '-'), 'Отменено:', str(stats['status_canceled'])],
                    ['Всего заказов:', str(stats['total_orders']), 'Новых:', str(stats['status_new'])],
                    ['Общая сумма:', f"{stats['total_cost']:.1f} р.", 'В работе:', str(stats['status_in_progress'])],
                    ['Оплачено:', f"{stats['total_paid']:.1f} р.", 'Ожидают оплаты:', str(stats['status_waiting'])],
                    ['Остаток:', f"{stats['total_remaining']:.1f} р.", 'Выполнено:', str(stats['status_completed'])]
                ]

                # Таблица информации
                info_table = Table(info_data, colWidths=[35 * mm, 55 * mm, 45 * mm, 45 * mm])
                info_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'CustomFont'),  # Используем наш шрифт
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(info_table)
                elements.append(Spacer(1, 10))

                # Заказы
                headers = ['№', 'Статус', 'Услуга', 'Стоимость', 'Оплачено', 'Остаток', 'Дата']
                orders = self.session.query(Order) \
                    .filter(Order.fio == self.client_fio) \
                    .order_by(Order.created_date.desc()) \
                    .all()

                orders_data = [headers]

                # Статусы с эмодзи
                status_icons = {
                    'Выполнен': '✓',
                    'В ожидании оплаты': '●',
                    'В работе': '→',
                    'Отменен': '×',
                    'Новый': 'N'
                }

                for order in orders:
                    # Форматируем дату
                    date_str = order.created_date.strftime('%d.%m.%Y') if order.created_date else '-'

                    orders_data.append([
                        str(order.id),
                        status_icons.get(order.status, ''),
                        str(order.service),
                        f"{order.cost:.1f} р.",
                        f"{order.paid_amount:.1f} р.",
                        f"{order.remaining_amount:.1f} р.",
                        date_str
                    ])

                # Таблица заказов
                orders_table = Table(orders_data,
                                     colWidths=[15 * mm, 15 * mm, 60 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm])
                orders_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'CustomFont'),  # Используем наш шрифт
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (2, 1), (2, -1), 'LEFT'),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ]))
                elements.append(orders_table)

                # Создаем документ
                doc.build(elements)
                QMessageBox.information(self, "Успех", "Отчет успешно создан!")

        except Exception as e:
            print(f"Ошибка при создании отчета: {str(e)}")  # Для отладки
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании отчета: {str(e)}")



