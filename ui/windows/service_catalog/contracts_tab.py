from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTreeWidget, QTreeWidgetItem,
                             QTextEdit, QSplitter, QGroupBox, QLineEdit,
                             QComboBox, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.database import init_database, Order
import json
from datetime import datetime
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTreeWidget, QTreeWidgetItem,
                             QTextEdit, QSplitter, QGroupBox, QLineEdit,
                             QComboBox, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from core.database import init_database, Order
import json
from datetime import datetime, timedelta  # Added timedelta import
import os


class ContractsTab(QWidget):
    """Вкладка управления договорами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = init_database()
        self.templates_data = self.load_templates_data()
        self.current_template = None
        self.initUI()

    def initUI(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout(self)

        # Создаем разделитель
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель - список шаблонов
        templates_group = QGroupBox("Шаблоны договоров")
        templates_layout = QVBoxLayout(templates_group)

        # Дерево шаблонов
        self.templates_tree = QTreeWidget()
        self.templates_tree.setHeaderLabel("Доступные шаблоны")
        self.templates_tree.setMinimumWidth(250)
        self.templates_tree.itemClicked.connect(self.on_template_selected)

        # Кнопки управления шаблонами
        template_buttons = QHBoxLayout()
        add_template_btn = QPushButton("➕ Добавить")
        add_template_btn.clicked.connect(self.add_template)
        edit_template_btn = QPushButton("✏️ Редактировать")
        edit_template_btn.clicked.connect(self.edit_template)
        delete_template_btn = QPushButton("❌ Удалить")
        delete_template_btn.clicked.connect(self.delete_template)

        template_buttons.addWidget(add_template_btn)
        template_buttons.addWidget(edit_template_btn)
        template_buttons.addWidget(delete_template_btn)

        templates_layout.addWidget(self.templates_tree)
        templates_layout.addLayout(template_buttons)

        splitter.addWidget(templates_group)

        # Правая панель
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)

        # Поля для заполнения
        fields_group = QGroupBox("Данные для договора")
        fields_layout = QVBoxLayout(fields_group)

        # ФИО клиента
        client_layout = QHBoxLayout()
        client_layout.addWidget(QLabel("ФИО клиента:"))
        self.client_input = QLineEdit()
        self.client_input.textChanged.connect(self.update_preview)
        client_layout.addWidget(self.client_input)

        # Кнопка выбора существующего клиента
        select_client_btn = QPushButton("📋 Выбрать")
        select_client_btn.clicked.connect(self.select_existing_client)
        client_layout.addWidget(select_client_btn)

        fields_layout.addLayout(client_layout)

        # Услуга
        service_layout = QHBoxLayout()
        service_layout.addWidget(QLabel("Услуга:"))
        self.service_combo = QComboBox()
        self.service_combo.currentTextChanged.connect(self.update_preview)
        service_layout.addWidget(self.service_combo)
        fields_layout.addLayout(service_layout)

        # Стоимость
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(QLabel("Стоимость:"))
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Введите сумму")
        self.cost_input.textChanged.connect(self.update_preview)
        cost_layout.addWidget(self.cost_input)
        fields_layout.addLayout(cost_layout)

        # Срок выполнения
        deadline_layout = QHBoxLayout()
        deadline_layout.addWidget(QLabel("Срок выполнения:"))
        self.deadline_combo = QComboBox()
        self.deadline_combo.addItems(['3 дня', '5 дней', '7 дней', '14 дней', '30 дней'])
        self.deadline_combo.currentTextChanged.connect(self.update_preview)
        deadline_layout.addWidget(self.deadline_combo)
        fields_layout.addLayout(deadline_layout)

        details_layout.addWidget(fields_group)

        # Предпросмотр договора
        preview_group = QGroupBox("Предпросмотр договора")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)

        details_layout.addWidget(preview_group)

        # Кнопки действий
        actions_layout = QHBoxLayout()

        self.generate_btn = QPushButton("📄 Сгенерировать договор")
        self.generate_btn.clicked.connect(self.generate_contract)

        self.send_btn = QPushButton("📤 Отправить клиенту")
        self.send_btn.clicked.connect(self.send_to_client)

        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.save_contract)

        actions_layout.addWidget(self.generate_btn)
        actions_layout.addWidget(self.send_btn)
        actions_layout.addWidget(self.save_btn)

        details_layout.addLayout(actions_layout)

        splitter.addWidget(details_widget)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # Загружаем данные
        self.load_templates()
        self.load_services()

        # Применяем стили
        self.apply_styles()

    def apply_styles(self):
        """Применение стилей"""
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
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #2196F3;
            }
            QTreeWidget {
                border: none;
            }
            QTreeWidget::item:selected {
                background: #e3f2fd;
                color: black;
            }
        """)

    def load_templates(self):
        """Загрузка шаблонов в дерево"""
        self.templates_tree.clear()

        categories = {
            "Стандартные договоры": [
                "Договор на курсовую работу",
                "Договор на дипломную работу"
            ],
            "Специальные договоры": [
                "Договор с рассрочкой",
                "Срочный договор"
            ]
        }

        for category, templates in categories.items():
            cat_item = QTreeWidgetItem([category])
            for template in templates:
                template_item = QTreeWidgetItem([template])
                cat_item.addChild(template_item)
            self.templates_tree.addTopLevelItem(cat_item)

    def load_templates_data(self):
        """Загрузка данных шаблонов"""
        try:
            with open('contract_templates.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.get_default_templates()

    def get_default_templates(self):
        """Получение шаблонов по умолчанию"""
        return {
            "Договор на курсовую работу": {
                "template": """
ДОГОВОР НА ВЫПОЛНЕНИЕ КУРСОВОЙ РАБОТЫ №{contract_number}

г. Воронеж                                                                      {date}

ООО "MPSP", именуемое в дальнейшем "Исполнитель", с одной стороны,
и {client_name}, именуемый(ая) в дальнейшем "Заказчик", с другой стороны,
заключили настоящий договор о нижеследующем:

1. ПРЕДМЕТ ДОГОВОРА
1.1. Исполнитель обязуется выполнить курсовую работу по теме: {service}
1.2. Срок выполнения работы: {deadline}
1.3. Стоимость работы составляет: {cost} рублей

2. ОБЯЗАННОСТИ СТОРОН
2.1. Исполнитель обязуется:
    - Выполнить работу качественно и в срок
    - Внести правки при необходимости
    - Обеспечить конфиденциальность

2.2. Заказчик обязуется:
    - Предоставить необходимые материалы
    - Оплатить работу в установленный срок

3. ПОРЯДОК ОПЛАТЫ
3.1. Оплата производится в следующем порядке:
    - Предоплата 50%: {prepayment} рублей
    - Окончательный расчет: {remaining} рублей

4. КОНТАКТНАЯ ИНФОРМАЦИЯ
Исполнитель: ООО "MPSP"
Тел: +7 906 632-25-71
Email: Mukam1@list.ru

Заказчик: {client_name}
Тел: {client_phone}

ПОДПИСИ СТОРОН

Исполнитель: ____________     Заказчик: ____________
"""
            },
            "Договор с рассрочкой": {
                "template": """
ДОГОВОР С РАССРОЧКОЙ ПЛАТЕЖА №{contract_number}

[Содержание договора с условиями рассрочки...]
"""
            }
        }

    def load_services(self):
        """Загрузка списка услуг"""
        services = self.session.query(Order.service).distinct().all()
        self.service_combo.clear()
        self.service_combo.addItems([service[0] for service in services if service[0]])

    def select_existing_client(self):
        """Выбор существующего клиента"""
        try:
            clients = self.session.query(
                Order.fio,
                Order.phone,
                Order.group
            ).distinct().all()

            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem

            dialog = QDialog(self)
            dialog.setWindowTitle("Выбор клиента")
            dialog.setModal(True)

            layout = QVBoxLayout(dialog)
            client_list = QListWidget()

            for client in clients:
                item = QListWidgetItem(f"{client.fio} ({client.group})")
                item.setData(Qt.UserRole, client)
                client_list.addItem(item)

            layout.addWidget(client_list)

            client_list.itemDoubleClicked.connect(lambda item: self.fill_client_data(item.data(Qt.UserRole)))
            client_list.itemDoubleClicked.connect(dialog.accept)

            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке клиентов: {str(e)}")

    def fill_client_data(self, client):
        """Заполнение данных клиента"""
        self.client_input.setText(client.fio)
        # Можно добавить заполнение других полей

    def on_template_selected(self, item, column):
        """Обработка выбора шаблона"""
        if not item.parent():  # Если это категория
            return

        template_name = item.text(0)
        if template_name in self.templates_data:
            self.current_template = template_name
            self.update_preview()

    def update_preview(self):
        """Обновление предпросмотра договора с улучшенной обработкой ошибок"""
        if not self.current_template:
            return

        try:
            template = self.templates_data[self.current_template]["template"]

            # Получаем телефон клиента из базы
            client_phone = self.session.query(Order.phone).filter(
                Order.fio == self.client_input.text()
            ).first()

            # Базовые данные для всех типов договоров
            contract_data = {
                "contract_number": datetime.now().strftime("%Y%m%d%H%M"),
                "date": datetime.now().strftime("%d.%m.%Y"),
                "client_name": self.client_input.text(),
                "service": self.service_combo.currentText(),
                "deadline": self.deadline_combo.currentText(),
                "cost": self.cost_input.text() or "0",
                "client_phone": client_phone[0] if client_phone and client_phone[0] else "Не указан"
            }

            # Расчет платежей в зависимости от типа договора
            try:
                cost_value = float(self.cost_input.text() or 0)

                # Стандартное разделение платежей
                contract_data.update({
                    "prepayment": cost_value / 2,
                    "remaining": cost_value / 2
                })

                # Дополнительные платежи для определенных типов договоров
                if "магистерск" in self.current_template.lower():
                    contract_data.update({
                        "prepayment": cost_value * 0.25,
                        "second_payment": cost_value * 0.25,
                        "third_payment": cost_value * 0.25,
                        "remaining": cost_value * 0.25
                    })
                elif "диплом" in self.current_template.lower():
                    contract_data.update({
                        "prepayment": cost_value * 0.3,
                        "intermediate": cost_value * 0.4,
                        "remaining": cost_value * 0.3
                    })
                elif "рассрочк" in self.current_template.lower():
                    contract_data.update({
                        "total_cost": cost_value,
                        "initial_payment": cost_value * 0.3,
                        "second_payment": cost_value * 0.25,
                        "third_payment": cost_value * 0.25,
                        "final_payment": cost_value * 0.2,
                        "initial_payment_date": (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y"),
                        "second_payment_date": (datetime.now() + timedelta(days=7)).strftime("%d.%m.%Y"),
                        "third_payment_date": (datetime.now() + timedelta(days=14)).strftime("%d.%m.%Y"),
                        "final_payment_date": (datetime.now() + timedelta(days=21)).strftime("%d.%m.%Y"),
                        "work_type": self.service_combo.currentText().split()[0]  # Первое слово из названия услуги
                    })

            except ValueError as e:
                print(f"Ошибка при расчете платежей: {e}")
                contract_data.update({
                    "prepayment": "0",
                    "remaining": "0",
                    "intermediate": "0"
                })

            # Форматирование числовых значений
            for key in contract_data:
                if isinstance(contract_data[key], float):
                    contract_data[key] = "{:.2f}".format(contract_data[key])

            # Заполняем шаблон с обработкой отсутствующих переменных
            filled_template = template
            for key, value in contract_data.items():
                placeholder = "{" + key + "}"
                if placeholder in template:
                    filled_template = filled_template.replace(placeholder, str(value))

            self.preview_text.setPlainText(filled_template)

        except Exception as e:
            print(f"Ошибка предпросмотра: {str(e)}")  # Для отладки
            self.preview_text.setPlainText(
                f"Ошибка при формировании предпросмотра. Пожалуйста, проверьте введенные данные.")
    def generate_contract(self):
        """Генерация договора"""
        try:
            if not self.validate_fields():
                return

            # Создаем PDF
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # Выбор места сохранения файла
            file_name = f"Договор_{self.client_input.text()}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить договор",
                file_name,
                "PDF files (*.pdf)"
            )

            if file_path:
                # Регистрируем шрифт
                try:
                    pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
                except:
                    pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/TTF/DejaVuSans.ttf'))

                # Создаем документ
                doc = SimpleDocTemplate(
                    file_path,
                    pagesize=A4,
                    rightMargin=20 * mm,
                    leftMargin=20 * mm,
                    topMargin=20 * mm,
                    bottomMargin=20 * mm
                )

                # Стили
                styles = getSampleStyleSheet()
                normal_style = ParagraphStyle(
                    'CustomNormal',
                    parent=styles['Normal'],
                    fontSize=12,
                    fontName='Arial'
                )
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=14,
                    fontName='Arial',
                    alignment=1,
                    spaceAfter=10 * mm
                )

                # Формируем содержимое
                elements = []

                # Разбиваем текст договора на параграфы
                contract_text = self.preview_text.toPlainText()
                for paragraph in contract_text.split('\n'):
                    if paragraph.strip():
                        if paragraph.startswith('ДОГОВОР'):
                            elements.append(Paragraph(paragraph, title_style))
                        else:
                            elements.append(Paragraph(paragraph, normal_style))
                    else:
                        elements.append(Spacer(1, 5 * mm))

                # Создаем документ
                doc.build(elements)
                QMessageBox.information(self, "Успех", "Договор успешно создан!")
                return file_path

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании договора: {str(e)}")
            return None

    def validate_fields(self):
        """Проверка заполнения обязательных полей"""
        if not self.current_template:
            QMessageBox.warning(self, "Предупреждение", "Выберите шаблон договора")
            return False

        if not self.client_input.text():
            QMessageBox.warning(self, "Предупреждение", "Введите ФИО клиента")
            return False

        if not self.service_combo.currentText():
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу")
            return False

        if not self.cost_input.text() or not self.cost_input.text().replace('.', '').isdigit():
            QMessageBox.warning(self, "Предупреждение", "Введите корректную стоимость")
            return False

        return True

    def send_to_client(self):
        """Отправка договора клиенту"""
        try:
            # Сначала генерируем договор
            contract_path = self.generate_contract()
            if not contract_path:
                return

            # Получаем телефон клиента
            client_phone = self.session.query(Order.phone).filter(
                Order.fio == self.client_input.text()
            ).first()

            if not client_phone or not client_phone[0]:
                QMessageBox.warning(self, "Предупреждение", "У клиента не указан номер телефона")
                return

            # Формируем текст сообщения
            message = f"""Здравствуйте, {self.client_input.text()}!

Направляем Вам договор на оказание услуг:
• Услуга: {self.service_combo.currentText()}
• Стоимость: {self.cost_input.text()} ₽
• Срок выполнения: {self.deadline_combo.currentText()}

Договор прикреплен к сообщению.

С уважением,
Команда MPSP"""

            # Отправляем сообщение в WhatsApp
            phone = ''.join(filter(str.isdigit, client_phone[0]))
            if not phone.startswith('7'):
                phone = '7' + phone

            from urllib.parse import quote
            import webbrowser
            url = f"https://wa.me/{phone}?text={quote(message)}"
            webbrowser.open(url)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отправке договора: {str(e)}")

    def save_contract(self):
        """Сохранение договора в базу"""
        try:
            if not self.validate_fields():
                return

            # Генерируем договор
            contract_path = self.generate_contract()
            if not contract_path:
                return

            # TODO: Добавить сохранение информации о договоре в базу данных
            QMessageBox.information(self, "Успех", "Договор успешно сохранен")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении договора: {str(e)}")

    def add_template(self):
        """Добавление нового шаблона"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("Добавление шаблона")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        # Название шаблона
        layout.addWidget(QLabel("Название шаблона:"))
        name_input = QLineEdit()
        layout.addWidget(name_input)

        # Текст шаблона
        layout.addWidget(QLabel("Текст шаблона:"))
        template_text = QTextEdit()
        template_text.setPlaceholderText("""Доступные переменные:
{contract_number} - номер договора
{date} - дата договора
{client_name} - ФИО клиента
{service} - услуга
{deadline} - срок выполнения
{cost} - стоимость
{prepayment} - предоплата
{remaining} - остаток
{client_phone} - телефон клиента""")
        layout.addWidget(template_text)

        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            template_name = name_input.text()
            if template_name and template_text.toPlainText():
                self.templates_data[template_name] = {
                    "template": template_text.toPlainText()
                }
                self.save_templates()
                self.load_templates()
            else:
                QMessageBox.warning(self, "Предупреждение", "Заполните все поля")

    def edit_template(self):
        """Редактирование шаблона"""
        if not self.current_template:
            QMessageBox.warning(self, "Предупреждение", "Выберите шаблон для редактирования")
            return

        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit

        dialog = QDialog(self)
        dialog.setWindowTitle("Редактирование шаблона")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        # Название шаблона
        layout.addWidget(QLabel("Название шаблона:"))
        name_input = QLineEdit(self.current_template)
        name_input.setReadOnly(True)
        layout.addWidget(name_input)

        # Текст шаблона
        layout.addWidget(QLabel("Текст шаблона:"))
        template_text = QTextEdit()
        template_text.setText(self.templates_data[self.current_template]["template"])
        layout.addWidget(template_text)

        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            self.templates_data[self.current_template]["template"] = template_text.toPlainText()
            self.save_templates()
            self.update_preview()

    def delete_template(self):
        """Удаление шаблона"""
        if not self.current_template:
            QMessageBox.warning(self, "Предупреждение", "Выберите шаблон для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить шаблон '{self.current_template}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            del self.templates_data[self.current_template]
            self.save_templates()
            self.load_templates()
            self.current_template = None
            self.preview_text.clear()

    def save_templates(self):
        """Сохранение шаблонов в файл"""
        try:
            with open('contract_templates.json', 'w', encoding='utf-8') as f:
                json.dump(self.templates_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении шаблонов: {str(e)}")