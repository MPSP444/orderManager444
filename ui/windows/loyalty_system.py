# В начале файла loyalty_system.py

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                           QLabel, QTableWidget, QTableWidgetItem, QPushButton,
                           QTextEdit, QComboBox, QMessageBox, QGroupBox,
                           QScrollArea,QLineEdit, QWidget, QHeaderView)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QColor, QFont
from core.database import init_database, Order
from sqlalchemy import func, desc
from datetime import datetime
from urllib.parse import quote
import webbrowser
import re
import json

class TemplateActionWidget(QWidget):
    """Виджет с выбором шаблона и кнопкой отправки"""
    def __init__(self, templates, callback, add_template_callback, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        # Выпадающий список шаблонов
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(200)  # Увеличиваем минимальную ширину
        self.template_combo.addItems(templates)
        self.template_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 4px;
                background: white;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
        """)
        layout.addWidget(self.template_combo)

        # Кнопка отправки
        send_btn = QPushButton("📤 Отправить")
        send_btn.clicked.connect(lambda: callback(self.template_combo.currentText()))
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 4px 12px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(send_btn)

        # Кнопка добавления нового шаблона
        add_btn = QPushButton("➕")
        add_btn.setToolTip("Добавить новый шаблон")
        add_btn.clicked.connect(add_template_callback)
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                max-width: 30px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        layout.addWidget(add_btn)

        layout.addStretch()  # Добавляем растягивающийся элемент


class NewTemplateDialog(QDialog):
    """Диалог создания нового шаблона"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новый шаблон")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Название шаблона
        name_layout = QHBoxLayout()
        name_label = QLabel("Название:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Текст шаблона
        layout.addWidget(QLabel("Текст шаблона:"))
        self.text_edit = QTextEdit()
        self.text_edit.setMinimumHeight(200)
        layout.addWidget(self.text_edit)

        # Информация о переменных
        variables_info = """
        Доступные переменные:
        {client} - имя клиента
        {order_count} - количество заказов
        {debt_message} - сумма долга
        {debt_details} - детали задолженности
        {discount} - размер скидки
        """
        info_label = QLabel(variables_info)
        info_label.setStyleSheet("color: #666;")
        layout.addWidget(info_label)

        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def get_template_data(self):
        return {
            'name': self.name_input.text(),
            'text': self.text_edit.toPlainText()
        }
class LoyaltySystem(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = init_database()
        self.message_templates = self.load_templates()
        self.tabs = None
        from core.database_manager import DatabaseManager
        self.db_manager = DatabaseManager()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("💎 Система лояльности")
        self.setGeometry(100, 100, 1200, 800)

        layout = QVBoxLayout(self)

        # Создаем вкладки
        self.tabs = QTabWidget()

        # Вкладка "Постоянные клиенты"
        loyal_tab = self.createLoyalClientsTab()
        self.tabs.addTab(loyal_tab, "👑 Постоянные клиенты")

        # Вкладка "Должники"
        debtors_tab = self.createDebtorsTab()
        self.tabs.addTab(debtors_tab, "⚠️ Должники")
        # Новая вкладка "Сгруппированные должники"
        grouped_debtors_tab = self.createGroupedDebtorsTab()
        self.tabs.addTab(grouped_debtors_tab, "📊 Сводка по должникам")

        # Вкладка "Рассылка"
        mailing_tab = self.createMailingTab()
        self.tabs.addTab(mailing_tab, "📨 Рассылка")

        layout.addWidget(self.tabs)

    def add_new_template(self):
        """Добавление нового шаблона"""
        dialog = NewTemplateDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            template_data = dialog.get_template_data()

            if not template_data['name'] or not template_data['text']:
                QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
                return

            # Добавляем новый шаблон
            self.message_templates[template_data['name']] = template_data['text']

            # Сохраняем шаблоны
            try:
                with open('message_templates.json', 'w', encoding='utf-8') as f:
                    json.dump(self.message_templates, f, ensure_ascii=False, indent=4)

                # Обновляем все комбобоксы в таблице
                self.update_template_combos()

                QMessageBox.information(self, "Успех", "Шаблон успешно добавлен!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении шаблона: {str(e)}")

    def update_template_combos(self):
        """Обновление всех комбобоксов с шаблонами"""
        # Обновляем комбобоксы во всех вкладках
        for tab_idx in range(self.tabs.count()):
            tab = self.tabs.widget(tab_idx)
            if hasattr(tab, 'findChildren'):
                for combo in tab.findChildren(QComboBox):
                    current_text = combo.currentText()
                    combo.clear()
                    combo.addItems(self.message_templates.keys())
                    # Пытаемся восстановить предыдущий выбор
                    index = combo.findText(current_text)
                    if index >= 0:
                        combo.setCurrentIndex(index)

    def createGroupedDebtorsTab(self):
        """Создание вкладки сгруппированных должников с правильным учетом скидок"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Таблица должников
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Выбрать", "ФИО клиента", "Общая сумма долга",
            "Количество заказов", "Телефон", "Действия"
        ])

        # Настройка размеров
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        table.setColumnWidth(0, 70)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 150)
        table.setColumnWidth(4, 150)
        table.setColumnWidth(5, 400)

        # Список исключаемых статусов
        excluded_statuses = ['Отменен', 'Отказ']

        # Получаем общее количество заказов
        all_orders_count = (
            self.session.query(
                Order.fio,
                func.count(Order.id).label('total_orders')
            )
            .filter(~Order.status.in_(excluded_statuses))
            .group_by(Order.fio)
            .all()
        )

        orders_count_dict = {order.fio: order.total_orders for order in all_orders_count}

        # Получаем все заказы с возможными долгами
        orders_with_debt = (
            self.session.query(
                Order.id,
                Order.fio,
                Order.phone,
                Order.cost,
                Order.paid_amount,
                Order.discount,
                Order.status
            )
            .filter(
                ~Order.status.in_(excluded_statuses)
            )
            .all()
        )

        # Группируем данные
        grouped_debtors = {}
        for order in orders_with_debt:
            if order.fio not in grouped_debtors:
                grouped_debtors[order.fio] = {
                    'fio': order.fio,
                    'phone': order.phone,
                    'total_debt': 0,
                    'orders_count': orders_count_dict.get(order.fio, 0)
                }

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
            grouped_debtors[order.fio]['total_debt'] += remaining_debt

        # Фильтруем должников (оставляем только тех, у кого есть долг)
        grouped_debtors = {
            fio: data for fio, data in grouped_debtors.items()
            if data['total_debt'] > 0
        }

        # Сортируем по сумме долга
        grouped_debtors = sorted(
            grouped_debtors.values(),
            key=lambda x: x['total_debt'],
            reverse=True
        )

        # Заполняем таблицу
        table.setRowCount(len(grouped_debtors))
        for i, debtor in enumerate(grouped_debtors):
            # Чекбокс
            checkbox = QTableWidgetItem()
            checkbox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox.setCheckState(Qt.Unchecked)
            table.setItem(i, 0, checkbox)

            # ФИО
            table.setItem(i, 1, QTableWidgetItem(debtor['fio']))

            # Общая сумма долга
            debt_item = QTableWidgetItem(f"{debtor['total_debt']:,.2f} ₽")
            debt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            debt_item.setForeground(QColor("#f44336"))
            table.setItem(i, 2, debt_item)

            # Количество заказов
            orders_item = QTableWidgetItem(str(debtor['orders_count']))
            orders_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 3, orders_item)

            # Телефон
            phone = self.session.query(Order.phone).filter(
                Order.fio == debtor['fio'],
                Order.phone.isnot(None),
                Order.phone != ''
            ).first()

            phone_number = phone[0] if phone else "Не указан"
            phone_item = QTableWidgetItem(phone_number)
            phone_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 4, phone_item)

            # Действия
            class DebtorInfo:
                def __init__(self, fio, total_debt, total_orders, phone):
                    self.fio = fio
                    self.total_debt = total_debt
                    self.total_orders = total_orders
                    self.phone = phone

            debtor_obj = DebtorInfo(
                fio=debtor['fio'],
                total_debt=debtor['total_debt'],
                total_orders=debtor['orders_count'],
                phone=phone_number if phone_number != "Не указан" else None
            )

            action_widget = TemplateActionWidget(
                templates=list(self.message_templates.keys()),
                callback=lambda template, d=debtor_obj: self.send_grouped_debt_message(d, template),
                add_template_callback=self.add_new_template
            )
            table.setCellWidget(i, 5, action_widget)

        # Добавляем кнопки массовых действий
        mass_actions = QHBoxLayout()

        template_combo = QComboBox()
        template_combo.addItems(self.message_templates.keys())
        template_combo.setMinimumWidth(200)
        mass_actions.addWidget(QLabel("Шаблон для массовой отправки:"))
        mass_actions.addWidget(template_combo)

        mass_send_btn = QPushButton("📤 Отправить выбранным")
        mass_send_btn.clicked.connect(lambda: self.send_mass_messages(table, template_combo.currentText()))
        mass_actions.addWidget(mass_send_btn)

        select_all_btn = QPushButton("✅ Выбрать все")
        select_none_btn = QPushButton("❌ Снять выбор")
        select_all_btn.clicked.connect(lambda: self.toggle_all_selections(table, True))
        select_none_btn.clicked.connect(lambda: self.toggle_all_selections(table, False))
        mass_actions.addWidget(select_all_btn)
        mass_actions.addWidget(select_none_btn)

        layout.addLayout(mass_actions)
        layout.addWidget(table)

        return widget


    def toggle_all_selections(self, table, select_all):
        """Выбор или снятие выбора со всех чекбоксов"""
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item:
                item.setCheckState(Qt.Checked if select_all else Qt.Unchecked)

    def send_mass_messages(self, table, template_name):
        """Массовая отправка сообщений выбранным должникам"""
        selected_rows = []
        processed_fios = set()  # Множество для отслеживания обработанных получателей
        success_count = 0

        # Сначала собираем всех выбранных получателей
        for row in range(table.rowCount()):
            if table.item(row, 0).checkState() == Qt.Checked:
                try:
                    class Debtor:
                        def __init__(self, fio, total_debt, total_orders, phone, discount=None):
                            self.fio = fio
                            self.total_debt = total_debt
                            self.total_orders = total_orders
                            self.phone = phone
                            self.discount = discount

                    fio = table.item(row, 1).text()

                    # Пропускаем, если уже обработали этого получателя
                    if fio in processed_fios:
                        continue

                    # Получаем данные клиента
                    client_orders = (
                        self.session.query(Order)
                        .filter(
                            Order.fio == fio,
                            ~Order.status.in_(['Отменен', 'Отказ'])
                        )
                        .all()
                    )

                    total_amount = 0
                    total_debt = 0

                    for order in client_orders:
                        actual_cost = order.cost
                        if order.discount and order.discount != "Не указано" and order.discount != "0%":
                            try:
                                discount_percent = float(order.discount.strip('%'))
                                actual_cost = order.cost * (1 - discount_percent / 100)
                            except (ValueError, AttributeError):
                                pass

                        total_amount += actual_cost
                        remaining = max(0, actual_cost - (order.paid_amount or 0))
                        total_debt += remaining

                    total_orders = len(client_orders)
                    phone = table.item(row, 4).text()
                    calculated_discount = self.calculate_discount(total_orders, total_amount)

                    debtor = Debtor(
                        fio=fio,
                        total_debt=total_debt,
                        total_orders=total_orders,
                        phone=phone,
                        discount=calculated_discount
                    )
                    selected_rows.append(debtor)
                    processed_fios.add(fio)  # Добавляем в обработанные

                except Exception as e:
                    print(f"Ошибка при обработке строки {row}: {e}")
                    continue

        if not selected_rows:
            QMessageBox.warning(self, "Предупреждение", "Не выбрано ни одного получателя!")
            return

        # Проходим по каждому получателю и показываем предпросмотр
        for debtor in selected_rows:
            try:
                preview = QMessageBox()
                preview.setIcon(QMessageBox.Information)
                preview.setWindowTitle("Предпросмотр сообщения")
                preview.setText(
                    f"Отправить сообщение для клиента {debtor.fio}?\n"
                    f"Телефон: {debtor.phone}\n"
                    f"Сумма долга: {debtor.total_debt:,.2f} руб.\n"
                    f"Рекомендуемая скидка: {debtor.discount}%"
                )
                preview.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                preview.setDetailedText(self.get_message_text(debtor, template_name))

                if preview.exec_() == QMessageBox.Yes:
                    self.send_whatsapp_message(debtor.phone, self.get_message_text(debtor, template_name))
                    success_count += 1

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Ошибка при отправке сообщения для {debtor.fio}: {str(e)}"
                )

        # В конце показываем общий результат
        if success_count > 0:
            QMessageBox.information(
                self,
                "Результат отправки",
                f"Успешно отправлено сообщений: {success_count} из {len(selected_rows)}"
            )
    def get_message_text(self, debtor, template_name):
        """Формирование текста сообщения"""
        template = self.message_templates.get(template_name)
        if not template:
            raise ValueError("Шаблон сообщения не найден!")

        message = str(template)
        replacements = {
            "{client}": str(debtor.fio),
            "{order_count}": str(debtor.total_orders),
            "{discount}": f"{debtor.discount}%",
            "{debt_message}": f"Общая сумма задолженности: {debtor.total_debt:,.2f} руб.",
            "{debt_details}": f"Количество заказов: {debtor.total_orders}"
        }

        for old, new in replacements.items():
            if old in message:
                message = message.replace(old, new)

        return message

    def send_grouped_debt_message(self, debtor, template_name):
        """Отправка сообщения сгруппированному должнику"""
        try:
            if not hasattr(debtor, 'phone') or not debtor.phone or debtor.phone == "Не указан":
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    f"У клиента {debtor.fio} не указан номер телефона! "
                    "Пожалуйста, добавьте номер телефона в карточку клиента."
                )
                return

            excluded_statuses = ['Отменен', 'Отказ']

            # Получаем все заказы клиента
            client_orders = (
                self.session.query(Order)
                .filter(
                    Order.fio == debtor.fio,
                    ~Order.status.in_(excluded_statuses)
                )
                .all()
            )

            if not client_orders:
                QMessageBox.warning(self, "Ошибка", "Не найдены активные заказы клиента!")
                return

            # Рассчитываем общую сумму с учетом скидок
            total_amount = 0
            total_debt = 0

            for order in client_orders:
                actual_cost = order.cost
                if order.discount and order.discount != "Не указано" and order.discount != "0%":
                    try:
                        discount_percent = float(order.discount.strip('%'))
                        actual_cost = order.cost * (1 - discount_percent / 100)
                    except (ValueError, AttributeError):
                        pass

                total_amount += actual_cost
                # Расчет долга с учетом скидки
                remaining = max(0, actual_cost - (order.paid_amount or 0))
                total_debt += remaining

            # Рассчитываем рекомендуемую скидку на основе количества заказов и общей суммы
            recommended_discount = self.calculate_discount(len(client_orders), total_amount)

            # Получаем шаблон
            template = self.message_templates.get(template_name)
            if not template:
                QMessageBox.warning(self, "Ошибка", "Шаблон сообщения не найден!")
                return

            message = str(template)

            # Подготавливаем все переменные для замены
            replacements = {
                "{client}": str(debtor.fio),
                "{order_count}": str(len(client_orders)),
                "{discount}": f"{recommended_discount}%",  # Добавляем рекомендуемую скидку
                "{debt_message}": f"Общая сумма задолженности: {total_debt:,.2f} руб.",
                "{debt_details}": (
                    f"Количество заказов с задолженностью: "
                    f"{len([o for o in client_orders if o.remaining_amount > 0])}"
                )
            }

            # Выполняем замену
            for old, new in replacements.items():
                if old in message:
                    message = message.replace(old, new)

            # Показываем предпросмотр сообщения
            preview = QMessageBox()
            preview.setIcon(QMessageBox.Information)
            preview.setWindowTitle("Предпросмотр сообщения")
            preview.setText(
                f"Отправить сообщение для клиента {debtor.fio}?\n"
                f"Телефон: {debtor.phone}\n"
                f"Сумма долга: {total_debt:,.2f} руб.\n"
                f"Рекомендуемая скидка: {recommended_discount}%"
            )
            preview.setDetailedText(message)
            preview.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            if preview.exec_() == QMessageBox.Yes:
                # Отправляем сообщение
                self.send_whatsapp_message(debtor.phone, message)
                QMessageBox.information(self, "Успех", f"Сообщение для {debtor.fio} успешно отправлено!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отправке сообщения: {str(e)}")
    def createLoyalClientsTab(self):
        """Создание вкладки постоянных клиентов с улучшенными кнопками"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Таблица клиентов
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "ФИО клиента", "Количество заказов",
            "Общая сумма", "Рекомендуемая скидка", "Действия"
        ])
        # Настройка размеров
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 150)
        table.setColumnWidth(4, 400)  # Увеличенная ширина для действий
        table.verticalHeader().setDefaultSectionSize(70)  # Увеличенная высота строк

        # Получаем данные о клиентах
        clients_data = (
            self.session.query(
                Order.fio,
                Order.phone,  # Добавляем получение телефона
                func.count(Order.id).label('order_count'),
                func.sum(Order.cost).label('total_amount')
            )
            .group_by(Order.fio, Order.phone)  # Группируем также по телефону
            .having(func.count(Order.id) >= 2)
            .order_by(desc('order_count'))
            .all()
        )

        # Устанавливаем размеры таблицы
        table.setRowCount(len(clients_data))
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 4):
            table.setColumnWidth(i, 120)
        table.setColumnWidth(4, 150)

        for i, client in enumerate(clients_data):
            # ФИО
            table.setItem(i, 0, QTableWidgetItem(client.fio))

            # Количество заказов
            order_count_item = QTableWidgetItem(str(client.order_count))
            order_count_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, order_count_item)

            # Общая сумма
            amount_item = QTableWidgetItem(f"{client.total_amount:,.2f} ₽")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(i, 2, amount_item)

            # Расчет скидки
            discount = self.calculate_discount(client.order_count, client.total_amount)
            discount_item = QTableWidgetItem(f"{discount}%")
            discount_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 3, discount_item)

            # Кнопка действий
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            button_layout.setSpacing(4)

            send_btn = ActionButton("Отправить", "💌")
            send_btn.clicked.connect(lambda checked, fio=client.fio, disc=discount:
                                     self.send_loyalty_message(fio, disc))
            button_layout.addWidget(send_btn)

            table.setCellWidget(i, 4, button_widget)

        # Стилизация таблицы
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 8;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)

        layout.addWidget(table)
        return widget

    def calculate_discount(self, order_count, total_amount):
        """Расчет скидки на основе количества заказов и суммы"""
        if order_count >= 10 or total_amount >= 25000:
            return 30
        elif order_count >= 5 or total_amount >= 10000:
            return 20
        elif order_count >= 3 or total_amount >= 8000:
            return 10
        return 0

    def createDebtorsTab(self):
        """Создание вкладки должников с сортировкой и корректным расчетом долгов"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Таблица должников
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "ФИО", "Телефон", "Сумма долга",
            "Срок задолженности", "Статус", "Действия"
        ])

        # Включаем сортировку
        table.setSortingEnabled(True)

        # Настройка размеров
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setColumnWidth(1, 150)
        table.setColumnWidth(2, 150)
        table.setColumnWidth(3, 150)
        table.setColumnWidth(4, 120)
        table.setColumnWidth(5, 400)
        table.verticalHeader().setDefaultSectionSize(70)

        # Получаем данные о должниках с учетом скидок и исключением отмененных заказов
        excluded_statuses = ['Отменен', 'Отказ']
        debtors = (
            self.session.query(Order)
            .filter(
                ~Order.status.in_(excluded_statuses)  # Исключаем отмененные заказы
            )
            .all()
        )

        # Фильтруем и обрабатываем должников
        actual_debtors = []
        for order in debtors:
            # Расчет фактической стоимости с учетом скидки
            actual_cost = order.cost
            if order.discount and order.discount != "Не указано" and order.discount != "0%":
                try:
                    discount_percent = float(order.discount.strip('%'))
                    actual_cost = order.cost * (1 - discount_percent / 100)
                except (ValueError, AttributeError):
                    pass

            # Расчет реального долга с учетом скидки
            actual_debt = max(0, actual_cost - (order.paid_amount or 0))

            if actual_debt > 0:  # Если есть реальный долг
                actual_debtors.append({
                    'order': order,
                    'actual_debt': actual_debt
                })

        # Сортируем по сумме долга
        actual_debtors.sort(key=lambda x: x['actual_debt'], reverse=True)

        # Заполняем таблицу
        table.setRowCount(len(actual_debtors))
        for i, debtor_data in enumerate(actual_debtors):
            debtor = debtor_data['order']
            actual_debt = debtor_data['actual_debt']

            # ФИО
            table.setItem(i, 0, QTableWidgetItem(debtor.fio))

            # Телефон
            phone_item = QTableWidgetItem(debtor.phone if debtor.phone else "Не указан")
            phone_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, phone_item)

            # Сумма долга (с учетом скидки)
            debt_item = QTableWidgetItem(f"{actual_debt:,.2f} ₽")
            debt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Сохраняем числовое значение для корректной сортировки
            debt_item.setData(Qt.UserRole, actual_debt)
            table.setItem(i, 2, debt_item)

            # Срок задолженности и статус
            if debtor.created_date:
                days_overdue = (datetime.now().date() - debtor.created_date).days
                days_item = QTableWidgetItem(f"{days_overdue} дн.")
                days_item.setTextAlignment(Qt.AlignCenter)
                # Сохраняем числовое значение для корректной сортировки
                days_item.setData(Qt.UserRole, days_overdue)
                table.setItem(i, 3, days_item)

                if days_overdue > 30:
                    status = "❗ Критично"
                    status_color = "#f44336"
                elif days_overdue > 14:
                    status = "⚠️ Внимание"
                    status_color = "#ff9800"
                else:
                    status = "ℹ️ Норма"
                    status_color = "#4caf50"

                status_item = QTableWidgetItem(status)
                status_item.setForeground(QColor(status_color))
                status_item.setTextAlignment(Qt.AlignCenter)
                # Сохраняем числовое значение для корректной сортировки
                status_item.setData(Qt.UserRole, days_overdue)
                table.setItem(i, 4, status_item)

            # Кнопки действий
            button_widget = QWidget()
            button_layout = QHBoxLayout(button_widget)
            button_layout.setContentsMargins(2, 2, 2, 2)
            button_layout.setSpacing(4)

            remind_btn = ActionButton("Напомнить", "⚠️")
            remind_btn.clicked.connect(lambda checked, d=debtor: self.send_debt_reminder(d))
            button_layout.addWidget(remind_btn)

            table.setCellWidget(i, 5, button_widget)

        # Обработчик сортировки
        table.horizontalHeader().sectionClicked.connect(
            lambda index: self.handle_sort(table, index)
        )

        # Стилизация таблицы
        table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                gridline-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #2196F3;
                font-weight: bold;
                cursor: pointer;
            }
            QHeaderView::section:hover {
                background-color: #e3f2fd;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
        """)

        layout.addWidget(table)
        return widget

    def handle_sort(self, table, column_index):
        """Обработчик сортировки таблицы"""
        # Получаем текущее направление сортировки
        header = table.horizontalHeader()
        if header.sortIndicatorSection() == column_index:
            # Если та же колонка, меняем направление
            order = Qt.DescendingOrder if header.sortIndicatorOrder() == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            # Новая колонка, сортируем по убыванию
            order = Qt.DescendingOrder

        # Применяем сортировку
        table.sortItems(column_index, order)


    def createMailingTab(self):
        """Создание вкладки рассылки"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Выбор шаблона
        template_group = QGroupBox("Шаблоны сообщений")
        template_layout = QVBoxLayout()

        self.template_combo = QComboBox()
        self.template_combo.addItems([
            "Скидка постоянным клиентам",
            "Специальное предложение",
            "Благодарность клиенту",
            "Напоминание о долге"
        ])
        self.template_combo.currentTextChanged.connect(self.load_template)
        template_layout.addWidget(self.template_combo)

        # Редактор шаблона
        self.template_editor = QTextEdit()
        template_layout.addWidget(self.template_editor)

        # Информация о доступных переменных
        variables_label = QLabel("""
            Доступные переменные:
            {client} - имя клиента
            {order_count} - количество заказов
            {debt_message} - сумма долга
            {debt_details} - детали задолженности
            {discount} - размер скидки
        """)
        template_layout.addWidget(variables_label)

        template_group.setLayout(template_layout)
        layout.addWidget(template_group)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("💾 Сохранить шаблон")
        save_btn.clicked.connect(self.save_template)
        buttons_layout.addWidget(save_btn)

        preview_btn = QPushButton("👁️ Предпросмотр")
        preview_btn.clicked.connect(self.preview_message)
        buttons_layout.addWidget(preview_btn)

        layout.addLayout(buttons_layout)

        return widget

    def load_templates(self):
        """Загрузка шаблонов сообщений"""
        try:
            with open('message_templates.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Возвращаем шаблоны по умолчанию
            return {
                "Благодарность клиенту": """Уважаемый {client}!

Мы очень рады видеть вас среди наших клиентов! За все время вы воспользовались нашими услугами {order_count} раз, и мы искренне благодарны вам за доверие.

В качестве нашей благодарности, мы хотим предложить вам скидку {discount} на следующий заказ!

Также хотели бы напомнить, что у вас есть неоплаченные заказы:
{debt_message}
{debt_details}

Мы ценим наше сотрудничество и всегда готовы помочь вам!

С уважением,
ООО MPSP
тел: +79066322571""",

                "Напоминание о долге": """Уважаемый {client}!

Напоминаем о необходимости оплаты:
{debt_message}

Подробности по неоплаченным заказам:
{debt_details}

С уважением,
ООО MPSP
тел: +79066322571"""
            }
    def send_whatsapp_message(self, phone, message):
        """Отправка сообщения через WhatsApp"""
        # Форматируем номер телефона
        phone = re.sub(r'[^\d]', '', phone)
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        elif not phone.startswith('7'):
            phone = '7' + phone

        # Формируем URL для WhatsApp
        url = f"https://wa.me/{phone}?text={quote(message)}"
        QDesktopServices.openUrl(QUrl(url))

    def load_template(self, template_name):
        """Загрузка выбранного шаблона в редактор"""
        if template_name in self.message_templates:
            self.template_editor.setText(self.message_templates[template_name])
        else:
            self.template_editor.clear()

    def save_template(self):
        """Сохранение текущего шаблона"""
        current_template = self.template_combo.currentText()
        template_text = self.template_editor.toPlainText()

        if not template_text.strip():
            QMessageBox.warning(self, "Предупреждение", "Шаблон не может быть пустым!")
            return

        self.message_templates[current_template] = template_text

        try:
            with open('message_templates.json', 'w', encoding='utf-8') as f:
                json.dump(self.message_templates, f, ensure_ascii=False, indent=4)
            QMessageBox.information(self, "Успех", "Шаблон успешно сохранен!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении шаблона: {str(e)}")

    def preview_message(self):
        """Предварительный просмотр сообщения с тестовыми данными"""
        template = self.template_editor.toPlainText()

        # Тестовые данные для предпросмотра
        test_data = {
            'client': 'Иванов Иван Иванович',
            'order_count': '5',
            'debt_message': '5000 руб.',
            'debt_details': 'Срок оплаты: 7 дней',
            'discount': '20'
        }

        try:
            preview_text = template.format(**test_data)

            preview_dialog = QDialog(self)
            preview_dialog.setWindowTitle("Предпросмотр сообщения")
            preview_dialog.setMinimumWidth(400)

            layout = QVBoxLayout(preview_dialog)

            # Текст сообщения
            text_edit = QTextEdit()
            text_edit.setPlainText(preview_text)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            # Кнопка закрытия
            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(preview_dialog.close)
            layout.addWidget(close_btn)

            preview_dialog.exec_()

        except KeyError as e:
            QMessageBox.warning(self, "Ошибка", f"Неизвестная переменная в шаблоне: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при формировании сообщения: {str(e)}")

    def send_loyalty_message(self, client_name, discount, phone=None):
        """Отправка сообщения о лояльности клиенту"""
        try:
            # Если телефон не передан, пытаемся получить его из базы
            if not phone:
                client_data = (
                    self.session.query(
                        Order.phone
                    )
                    .filter(Order.fio == client_name)
                    .order_by(Order.id.desc())  # Берем самый последний номер
                    .first()
                )
                phone = client_data.phone if client_data else None

            if not phone:
                QMessageBox.warning(self, "Ошибка",
                                    f"У клиента {client_name} не указан номер телефона!")
                return

            # Получаем все заказы клиента для расчета долга
            excluded_statuses = ['Отменен', 'Отказ']
            client_orders = (
                self.session.query(Order)
                .filter(
                    Order.fio == client_name,
                    ~Order.status.in_(excluded_statuses)
                )
                .all()
            )

            # Рассчитываем общую сумму и долг с учетом скидок
            total_amount = 0
            total_debt = 0

            for order in client_orders:
                actual_cost = order.cost
                if order.discount and order.discount != "Не указано" and order.discount != "0%":
                    try:
                        discount_percent = float(order.discount.strip('%'))
                        actual_cost = order.cost * (1 - discount_percent / 100)
                    except (ValueError, AttributeError):
                        pass

                total_amount += actual_cost
                remaining = max(0, actual_cost - (order.paid_amount or 0))
                total_debt += remaining

            # Получаем шаблон сообщения
            template_name = "Благодарность клиенту"
            template = self.message_templates.get(template_name)

            if not template:
                QMessageBox.warning(self, "Ошибка", "Шаблон сообщения не найден!")
                return

            message = str(template)

            # Подготавливаем данные для замены
            replacements = {
                "{client}": client_name,
                "{order_count}": str(len(client_orders)),
                "{discount}": f"{discount}%",
                "{debt_message}": f"Общая сумма задолженности: {total_debt:,.2f} руб.",
                "{debt_details}": (
                    f"Количество заказов с задолженностью: "
                    f"{len([o for o in client_orders if o.remaining_amount > 0])}"
                )
            }

            # Выполняем замены в шаблоне
            for old, new in replacements.items():
                message = message.replace(old, new)

            # Показываем предпросмотр сообщения
            preview = QMessageBox()
            preview.setIcon(QMessageBox.Information)
            preview.setWindowTitle("Предпросмотр сообщения")
            preview.setText(
                f"Отправить сообщение для клиента {client_name}?\n"
                f"Телефон: {phone}"
            )
            preview.setDetailedText(message)
            preview.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            if preview.exec_() == QMessageBox.Yes:
                formatted_phone = self.format_phone_number(phone)
                self.send_whatsapp_message(formatted_phone, message)
                QMessageBox.information(self, "Успех",
                                        f"Сообщение для {client_name} успешно отправлено!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Ошибка при отправке сообщения: {str(e)}")

    def send_debt_reminder(self, debtor):
        """Отправка напоминания о долге с учетом скидок"""
        try:
            if not debtor.phone:
                QMessageBox.warning(self, "Ошибка", "У клиента не указан номер телефона!")
                return

            excluded_statuses = ['Отменен', 'Отказ']

            # Получаем все активные заказы клиента
            client_orders = (
                self.session.query(Order)
                .filter(
                    Order.fio == debtor.fio,
                    ~Order.status.in_(excluded_statuses)
                )
                .all()
            )

            # Рассчитываем общую сумму и долг с учетом скидок
            total_amount = 0
            total_debt = 0
            orders_with_debt = 0

            for order in client_orders:
                # Расчет фактической стоимости с учетом скидки
                actual_cost = order.cost
                if order.discount and order.discount != "Не указано" and order.discount != "0%":
                    try:
                        discount_percent = float(order.discount.strip('%'))
                        actual_cost = order.cost * (1 - discount_percent / 100)
                    except (ValueError, AttributeError):
                        pass

                total_amount += actual_cost
                # Расчет долга с учетом скидки
                remaining = max(0, actual_cost - (order.paid_amount or 0))
                if remaining > 0:
                    orders_with_debt += 1
                    total_debt += remaining

            if total_debt <= 0:
                QMessageBox.information(self, "Информация",
                                        "У клиента нет активных задолженностей с учетом скидок!")
                return

            days_overdue = (datetime.now().date() - debtor.created_date).days if hasattr(debtor, 'created_date') else 0

            # Формируем сообщение
            template = self.message_templates.get("Напоминание о долге")
            if not template:
                QMessageBox.warning(self, "Ошибка", "Шаблон напоминания не найден!")
                return

            # Подготавливаем данные для замены
            message = template.format(
                client=debtor.fio,
                debt_message=f"Общая сумма задолженности: {total_debt:,.2f} руб.",
                debt_details=(
                    f"Количество заказов с долгом: {orders_with_debt}\n"
                    f"Срок задолженности: {days_overdue} дней"
                )
            )

            # Показываем предпросмотр сообщения
            preview = QMessageBox()
            preview.setIcon(QMessageBox.Information)
            preview.setWindowTitle("Предпросмотр сообщения")
            preview.setText(
                f"Отправить сообщение для {debtor.fio}?\n"
                f"Телефон: {debtor.phone}\n"
                f"Сумма долга (с учетом скидок): {total_debt:,.2f} руб."
            )
            preview.setDetailedText(message)
            preview.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

            if preview.exec_() == QMessageBox.Yes:
                self.send_whatsapp_message(debtor.phone, message)
                QMessageBox.information(self, "Успех",
                                        f"Сообщение для {debtor.fio} успешно отправлено!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Ошибка при отправке напоминания: {str(e)}")


    def format_phone_number(self, phone):
        """Форматирование номера телефона"""
        phone = re.sub(r'[^\d]', '', phone)
        if phone.startswith('8'):
            phone = '7' + phone[1:]
        elif not phone.startswith('7'):
            phone = '7' + phone
        return phone


class ActionButton(QPushButton):
    """Кастомная кнопка для действий в таблице"""

    def __init__(self, text, icon=None, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 12px;
                min-height: 25px;
                min-width: 100px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        if icon:
            self.setText(f"{icon} {text}")


