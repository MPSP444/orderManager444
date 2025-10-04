from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTreeWidget, QTreeWidgetItem,
                             QTextEdit, QSplitter, QGroupBox, QSpinBox,
                             QComboBox, QMessageBox, QInputDialog, QLineEdit)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.database import init_database, Order
from urllib.parse import quote
import webbrowser
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
from PyQt5.QtWidgets import QFileDialog

class ServicesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = init_database()
        self.services_data = self.load_services_data()
        self.initUI()

    def initUI(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Создаем разделитель
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель - дерево услуг
        services_group = QGroupBox("Каталог услуг")
        services_layout = QVBoxLayout(services_group)

        self.services_tree = QTreeWidget()
        self.services_tree.setHeaderLabel("Услуги")
        self.services_tree.setMinimumWidth(250)
        self.services_tree.itemClicked.connect(self.on_service_selected)

        self.populate_services_tree()
        services_layout.addWidget(self.services_tree)

        splitter.addWidget(services_group)

        # Правая панель
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        # Информация об услуге
        info_group = QGroupBox("Информация об услуге")
        info_layout = QVBoxLayout(info_group)

        self.service_title = QLabel("Выберите услугу")
        self.service_title.setFont(QFont("Arial", 14, QFont.Bold))
        info_layout.addWidget(self.service_title)

        self.service_info = QTextEdit()
        self.service_info.setReadOnly(True)
        info_layout.addWidget(self.service_info)

        details_layout.addWidget(info_group)

        # Калькулятор стоимости
        calc_group = QGroupBox("Калькулятор стоимости")
        calc_layout = QVBoxLayout(calc_group)

        # Количество страниц/часов
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Количество:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(1000)
        self.quantity_spin.valueChanged.connect(self.calculate_cost)
        quantity_layout.addWidget(self.quantity_spin)
        calc_layout.addLayout(quantity_layout)

        # Срочность
        urgency_layout = QHBoxLayout()
        urgency_layout.addWidget(QLabel("Срочность:"))
        self.urgency_combo = QComboBox()
        self.urgency_combo.addItems(["Стандартная", "Срочно (+30%)", "Очень срочно (+50%)"])
        self.urgency_combo.currentTextChanged.connect(self.calculate_cost)
        urgency_layout.addWidget(self.urgency_combo)
        calc_layout.addLayout(urgency_layout)

        # Итоговая стоимость
        self.total_cost_label = QLabel("Итоговая стоимость: 0 ₽")
        self.total_cost_label.setFont(QFont("Arial", 12, QFont.Bold))
        calc_layout.addWidget(self.total_cost_label)

        details_layout.addWidget(calc_group)

        # Кнопки действий
        actions_layout = QHBoxLayout()

        self.share_btn = QPushButton("🔗 Поделиться")
        self.share_btn.clicked.connect(self.share_service)

        self.whatsapp_btn = QPushButton("📱 Отправить в WhatsApp")
        self.whatsapp_btn.clicked.connect(self.send_to_whatsapp)

        self.create_order_btn = QPushButton("📝 Создать заказ")
        self.create_order_btn.clicked.connect(self.create_order)

        actions_layout.addWidget(self.share_btn)
        actions_layout.addWidget(self.whatsapp_btn)
        actions_layout.addWidget(self.create_order_btn)

        details_layout.addLayout(actions_layout)

        splitter.addWidget(details_widget)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Применяем стили
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
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
            QTreeWidget {
                border: none;
            }
            QTreeWidget::item:selected {
                background: #e3f2fd;
                color: black;
            }
            QSpinBox, QComboBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)

    def load_services_data(self):
        """Загрузка данных об услугах"""
        try:
            with open('services_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Возвращаем данные по умолчанию
            return {
                "Курсовые работы": {
                    "description": "Профессиональная подготовка курсовых работ",
                    "subcategories": {
                        "Экономика": {
                            "base_price": 2000,
                            "price_per_page": 150,
                            "min_pages": 20,
                            "max_pages": 60,
                            "uniqueness": "70-85%",
                            "requirements": [
                                "Оформление по ГОСТ",
                                "Антиплагиат",
                                "Нормоконтроль"
                            ],
                            "deadlines": {
                                "min": "3 дня",
                                "standard": "7 дней",
                                "max": "14 дней"
                            }
                        },
                        "Право": {
                            "base_price": 2200,
                            "price_per_page": 170,
                            "min_pages": 25,
                            "max_pages": 70,
                            "uniqueness": "75-90%",
                            "requirements": [
                                "Оформление по ГОСТ",
                                "Антиплагиат",
                                "Нормоконтроль",
                                "Актуальное законодательство"
                            ]
                        }
                    }
                },
                "Дипломные работы": {
                    "description": "Написание дипломных работ под ключ",
                    "subcategories": {
                        "Бакалавриат": {
                            "base_price": 8000,
                            "price_per_page": 200,
                            "min_pages": 50,
                            "max_pages": 100,
                            "uniqueness": "75-90%"
                        }
                    }
                }
            }

    def populate_services_tree(self):
        """Наполнение дерева услуг"""
        self.services_tree.clear()

        for category, data in self.services_data.items():
            cat_item = QTreeWidgetItem([category])

            if "subcategories" in data:
                for subcat in data["subcategories"].keys():
                    subcat_item = QTreeWidgetItem([subcat])
                    cat_item.addChild(subcat_item)

            self.services_tree.addTopLevelItem(cat_item)

    def on_service_selected(self, item, column):
        """Обработка выбора услуги"""
        # Получаем путь к услуге
        path = []
        current = item
        while current:
            path.insert(0, current.text(0))
            current = current.parent()

        # Обновляем информацию
        self.service_title.setText(" → ".join(path))

        # Если это подкатегория
        if item.parent():
            category = item.parent().text(0)
            subcategory = item.text(0)
            service_data = self.services_data[category]["subcategories"][subcategory]

            # Формируем HTML с информацией об услуге
            info = f"""
            <h3>Основная информация</h3>
            <ul>
                <li>Базовая стоимость: {service_data['base_price']}₽</li>
                <li>Стоимость за страницу: {service_data['price_per_page']}₽</li>
                <li>Объем: {service_data['min_pages']}-{service_data['max_pages']} страниц</li>
                <li>Уникальность: {service_data['uniqueness']}</li>
            </ul>

            <h3>Требования</h3>
            <ul>
            """
            for req in service_data.get('requirements', []):
                info += f"<li>{req}</li>"
            info += "</ul>"

            if 'deadlines' in service_data:
                info += f"""
                <h3>Сроки выполнения</h3>
                <ul>
                    <li>Минимальный: {service_data['deadlines']['min']}</li>
                    <li>Стандартный: {service_data['deadlines']['standard']}</li>
                    <li>Максимальный: {service_data['deadlines']['max']}</li>
                </ul>
                """

            self.service_info.setHtml(info)

            # Обновляем калькулятор
            self.quantity_spin.setMinimum(service_data['min_pages'])
            self.quantity_spin.setMaximum(service_data['max_pages'])
            self.calculate_cost()
        else:
            # Если это категория, показываем общее описание
            category_data = self.services_data[item.text(0)]
            self.service_info.setHtml(f"<h2>{item.text(0)}</h2><p>{category_data['description']}</p>")
            self.total_cost_label.setText("Выберите подкатегорию для расчета стоимости")

    def calculate_cost(self):
        """Расчет стоимости"""
        selected_items = self.services_tree.selectedItems()
        if not selected_items or not selected_items[0].parent():
            return

        item = selected_items[0]
        category = item.parent().text(0)
        subcategory = item.text(0)
        service_data = self.services_data[category]["subcategories"][subcategory]

        # Базовая стоимость
        base_cost = service_data['base_price']
        # Стоимость за страницы
        pages_cost = service_data['price_per_page'] * self.quantity_spin.value()

        # Наценка за срочность
        urgency_multiplier = 1.0
        if "Срочно" in self.urgency_combo.currentText():
            urgency_multiplier = 1.3
        elif "Очень срочно" in self.urgency_combo.currentText():
            urgency_multiplier = 1.5

        total = (base_cost + pages_cost) * urgency_multiplier
        self.total_cost_label.setText(f"Итоговая стоимость: {total:,.2f} ₽")

    def share_service(self):
        """Копирование информации в буфер обмена"""
        if not hasattr(self, 'service_title') or not self.service_title.text():
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу")
            return

        # Формируем текст для отправки
        text = f"""
📋 {self.service_title.text()}

📝 ОПИСАНИЕ УСЛУГИ:
{self.service_info.toPlainText().strip()}

💰 СТОИМОСТЬ:
{self.total_cost_label.text()}

📅 СРОКИ ВЫПОЛНЕНИЯ:
• Стандартный: 7 дней
• Срочный: 3-5 дней
• Максимальный: 14 дней

📞 КОНТАКТЫ:
• Тел/WhatsApp: +7 906 632-25-71
• Email: Mukam1@list.ru

✅ Готовы ответить на все вопросы!"""

        # Копируем в буфер обмена
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Успех", "Информация скопирована в буфер обмена")

    def send_to_whatsapp(self):
        """Отправка информации в WhatsApp"""
        if not hasattr(self, 'service_title') or not self.service_title.text():
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу")
            return

        phone_input, ok = QInputDialog.getText(
            self,
            'Отправка в WhatsApp',
            'Введите номер телефона:',
            QLineEdit.Normal,
            '+7'
        )

        if ok and phone_input:
            # Очищаем номер от всего, кроме цифр
            phone = ''.join(filter(str.isdigit, phone_input))
            if not phone.startswith('7'):
                phone = '7' + phone

            # Формируем сообщение
            message = f"""Здравствуйте! 👋

📋 {self.service_title.text()}

📝 Описание услуги:
{self.service_info.toPlainText().strip()}

💰 Стоимость:
{self.total_cost_label.text()}

✅ Готовы обсудить детали заказа!

📞 Свяжитесь с нами:
• Тел/WhatsApp: +7 906 632-25-71
• Email: Mukam1@list.ru"""

            # Отправляем в WhatsApp
            import webbrowser
            from urllib.parse import quote
            url = f"https://wa.me/{phone}?text={quote(message)}"
            webbrowser.open(url)

    def create_order(self):
        """Создание нового заказа"""
        if not hasattr(self, 'service_title') or not self.service_title.text():
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу")
            return

        try:
            # Открываем окно создания заказа
            from ui.windows.new_order_window import NewOrderWindow
            dialog = NewOrderWindow(self)

            # Заполняем поля
            dialog.services_combo.setCurrentText(self.service_title.text())

            # Устанавливаем количество, если есть
            if hasattr(self, 'quantity_spin'):
                dialog.quantity_spin.setValue(self.quantity_spin.value())

            # Устанавливаем стоимость
            try:
                cost_text = self.total_cost_label.text()
                cost = float(''.join(filter(str.isdigit, cost_text)))
                dialog.cost_spin.setValue(cost)
            except:
                pass

            # Устанавливаем срок на основе выбранной срочности
            if hasattr(self, 'urgency_combo'):
                urgency = self.urgency_combo.currentText()
                if "Срочно" in urgency:
                    dialog.deadline_combo.setCurrentText("3 дня")
                elif "Очень срочно" in urgency:
                    dialog.deadline_combo.setCurrentText("5 дней")
                else:
                    dialog.deadline_combo.setCurrentText("7 дней")

            # Показываем диалог
            dialog.exec_()

        except Exception as e:
            print(f"Ошибка при создании заказа: {e}")  # Для отладки
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании заказа: {str(e)}")

    def update_service_data(self, service_path, field, value):
        """Обновление данных об услуге"""
        try:
            current_dict = self.services_data
            for key in service_path[:-1]:
                current_dict = current_dict[key]
            current_dict[service_path[-1]][field] = value

            # Сохраняем изменения в файл
            with open('services_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.services_data, f, ensure_ascii=False, indent=4)

            return True
        except Exception as e:
            print(f"Ошибка при обновлении данных: {e}")
            return False