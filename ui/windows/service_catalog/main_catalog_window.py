from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QPushButton, QLabel, QTreeWidget,
                             QTreeWidgetItem, QSpinBox,QComboBox,QGroupBox,QTextEdit, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from core.database import init_database, Order
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QLabel, QTreeWidget, QTreeWidgetItem,
                             QTextEdit, QSplitter, QGroupBox, QSpinBox,
                             QComboBox, QMessageBox, QInputDialog, QLineEdit,
                             QPushButton, QApplication)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from urllib.parse import quote
import webbrowser

class ServiceCatalogWindow(QMainWindow):
    """Главное окно справочника услуг и аналитики"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = init_database()
        self.initUI()

    def initUI(self):
        """Инициализация интерфейса"""
        # Настройка основного окна
        self.setWindowTitle("📚 Справочник услуг и аналитика")
        self.setGeometry(100, 100, 1200, 800)

        # Создаем центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Создаем вкладки
        self.tabs = QTabWidget()

        # Вкладка каталога услуг
        services_tab = self.createServicesTab()
        self.tabs.addTab(services_tab, "📋 Каталог услуг")

        # Вкладка аналитики клиентов
        analytics_tab = self.createAnalyticsTab()
        self.tabs.addTab(analytics_tab, "📊 Аналитика клиентов")

        # Вкладка договоров
        contracts_tab = self.createContractsTab()
        self.tabs.addTab(contracts_tab, "📄 Договоры и шаблоны")

        main_layout.addWidget(self.tabs)

        # Добавляем статусбар
        self.statusBar().showMessage('Готово к работе')

        # Применяем стили
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                padding: 8px 16px;
                margin: 2px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #2196F3;
            }
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QSplitter::handle {
                background-color: #ddd;
            }
        """)

    def createServicesTab(self):
        """Создание вкладки каталога услуг"""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Создаем разделитель для дерева и информации
        splitter = QSplitter(Qt.Horizontal)

        # Левая часть - дерево услуг
        services_tree = QTreeWidget()
        services_tree.setHeaderLabel("Услуги")
        services_tree.setMinimumWidth(250)
        services_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:hover {
                background: #f5f5f5;
            }
            QTreeWidget::item:selected {
                background: #e3f2fd;
                color: black;
            }
        """)

        # Добавляем категории услуг
        categories = {
            "Курсовые работы": {
                "icon": "📚",
                "subcategories": {
                    "Экономика": "💰",
                    "Право": "⚖️",
                    "IT": "💻",
                    "Маркетинг": "📊",
                    "Менеджмент": "📈"
                }
            },
            "Дипломные работы": {
                "icon": "🎓",
                "subcategories": {
                    "Бакалавриат": "📑",
                    "Магистратура": "📋"
                }
            },
            "Практика": {
                "icon": "✍️",
                "subcategories": {
                    "Отчеты": "📝",
                    "Дневники": "📓"
                }
            },
            "Консультации": {
                "icon": "💡",
                "subcategories": {
                    "Онлайн": "🖥️",
                    "Очные": "👥"
                }
            }
        }

        for category, data in categories.items():
            cat_item = QTreeWidgetItem([f"{data['icon']} {category}"])
            for subcat, icon in data['subcategories'].items():
                subcat_item = QTreeWidgetItem([f"{icon} {subcat}"])
                cat_item.addChild(subcat_item)
            services_tree.addTopLevelItem(cat_item)

        services_tree.expandAll()

        # Правая часть - информация об услуге
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)

        # Заголовок
        title_label = QLabel("Выберите услугу из списка")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2196F3;")
        info_layout.addWidget(title_label)

        # Основная информация
        info_group = QGroupBox("Информация об услуге")
        info_group_layout = QVBoxLayout(info_group)

        service_info = QTextEdit()
        service_info.setReadOnly(True)
        service_info.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background: white;
                padding: 10px;
            }
        """)
        info_group_layout.addWidget(service_info)

        info_layout.addWidget(info_group)

        # Калькулятор стоимости
        calc_group = QGroupBox("Калькулятор стоимости")
        calc_layout = QVBoxLayout(calc_group)

        # Количество страниц
        pages_layout = QHBoxLayout()
        pages_layout.addWidget(QLabel("Количество страниц:"))
        pages_spin = QSpinBox()
        pages_spin.setMinimum(1)
        pages_spin.setMaximum(500)
        pages_spin.setValue(20)
        pages_layout.addWidget(pages_spin)
        calc_layout.addLayout(pages_layout)

        # Срочность
        urgency_layout = QHBoxLayout()
        urgency_layout.addWidget(QLabel("Срочность:"))
        urgency_combo = QComboBox()
        urgency_combo.addItems([
            "Стандартная",
            "Срочно (+30%)",
            "Очень срочно (+50%)"
        ])
        urgency_layout.addWidget(urgency_combo)
        calc_layout.addLayout(urgency_layout)

        # Итоговая стоимость
        total_cost = QLabel("Итоговая стоимость: 0 ₽")
        total_cost.setFont(QFont("Arial", 12, QFont.Bold))
        total_cost.setStyleSheet("color: #2196F3;")
        calc_layout.addWidget(total_cost)

        info_layout.addWidget(calc_group)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        share_btn = QPushButton("🔗 Поделиться")
        share_btn.setStyleSheet("""
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

        whatsapp_btn = QPushButton("📱 Отправить в WhatsApp")
        whatsapp_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)

        order_btn = QPushButton("📝 Создать заказ")
        order_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)

        buttons_layout.addWidget(share_btn)
        buttons_layout.addWidget(whatsapp_btn)
        buttons_layout.addWidget(order_btn)

        info_layout.addLayout(buttons_layout)

        # Добавляем все в сплиттер
        splitter.addWidget(services_tree)
        splitter.addWidget(info_widget)
        splitter.setStretchFactor(1, 2)

        # Подключаем сигналы
        services_tree.itemClicked.connect(self.on_service_selected)
        pages_spin.valueChanged.connect(self.calculate_cost)
        urgency_combo.currentTextChanged.connect(self.calculate_cost)

        share_btn.clicked.connect(self.share_service)
        whatsapp_btn.clicked.connect(self.send_to_whatsapp)
        order_btn.clicked.connect(self.create_order)
        self.service_info = service_info
        self.title_label = title_label
        self.pages_spin = pages_spin
        self.urgency_combo = urgency_combo
        self.total_cost = total_cost
        layout.addWidget(splitter)
        return widget

    def share_service(self):
        """Копирование информации в буфер обмена"""
        if not hasattr(self, 'title_label') or not self.title_label.text():
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу")
            return

        # Формируем текст для отправки
        text = f"""
    📋 {self.title_label.text()}

    📝 ОПИСАНИЕ УСЛУГИ:
    {self.service_info.toPlainText().strip()}

    💰 СТОИМОСТЬ:
    {self.total_cost.text()}

    📅 СРОКИ ВЫПОЛНЕНИЯ:
    • Стандартный: 7 дней
    • Срочный: 3-5 дней
    • Максимальный: 14 дней

    📞 КОНТАКТЫ:
    • Тел/WhatsApp: +7 906 632-25-71
    • Email: Mukam1@list.ru

    ✅ Готовы ответить на все вопросы!"""

        # Копируем в буфер обмена
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Успех", "Информация скопирована в буфер обмена")

    def send_to_whatsapp(self):
        """Отправка информации в WhatsApp"""
        if not hasattr(self, 'title_label') or not self.title_label.text():
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

    📋 {self.title_label.text()}

    📝 Описание услуги:
    {self.service_info.toPlainText().strip()}

    💰 Стоимость:
    {self.total_cost.text()}

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
        if not hasattr(self, 'title_label') or not self.title_label.text():
            QMessageBox.warning(self, "Предупреждение", "Выберите услугу")
            return

        try:
            # Открываем окно создания заказа
            from ui.windows.new_order_window import NewOrderWindow
            dialog = NewOrderWindow(self)

            # Заполняем поля
            dialog.services_combo.setCurrentText(self.title_label.text())

            # Устанавливаем количество
            if hasattr(self, 'pages_spin'):
                dialog.quantity_spin.setValue(self.pages_spin.value())

            # Устанавливаем стоимость
            try:
                cost_text = self.total_cost.text()
                cost = float(''.join(filter(str.isdigit, cost_text)))
                dialog.cost_spin.setValue(cost)
            except:
                pass

            # Устанавливаем срок на основе выбранной срочности
            if hasattr(self, 'urgency_combo'):
                urgency = self.urgency_combo.currentText()
                if "Очень срочно" in urgency:
                    dialog.deadline_combo.setCurrentText("3 дня")
                elif "Срочно" in urgency:
                    dialog.deadline_combo.setCurrentText("5 дней")
                else:
                    dialog.deadline_combo.setCurrentText("7 дней")

            # Показываем диалог
            dialog.exec_()

        except Exception as e:
            print(f"Ошибка при создании заказа: {e}")  # Для отладки
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании заказа: {str(e)}")
    def on_service_selected(self, item, column):
        """Обработка выбора услуги"""
        # Получаем путь к услуге
        path = []
        current = item
        while current:
            path.insert(0, current.text(0))
            current = current.parent()

        # Получаем чистое название услуги (без эмодзи)
        service_name = ' → '.join([p.split(' ', 1)[1] if ' ' in p else p for p in path])

        # Обновляем заголовок
        self.title_label.setText(service_name)

        # Если это конечная услуга (не категория)
        if item.parent():
            category = item.parent().text(0).split(' ', 1)[1]  # Убираем эмодзи
            subcategory = item.text(0).split(' ', 1)[1]  # Убираем эмодзи

            # Формируем информацию об услуге
            info = f"""
            <h3>📝 Основная информация:</h3>
            <ul>
                <li>Категория: {category}</li>
                <li>Направление: {subcategory}</li>
                <li>Оформление: по ГОСТ</li>
                <li>Уникальность: от 70%</li>
            </ul>

            <h3>📚 Требования:</h3>
            <ul>
                <li>Титульный лист</li>
                <li>Содержание</li>
                <li>Введение</li>
                <li>Основная часть</li>
                <li>Заключение</li>
                <li>Список литературы</li>
            </ul>

            <h3>⏱️ Сроки выполнения:</h3>
            <ul>
                <li>Минимальный: 3-5 дней</li>
                <li>Стандартный: 7-10 дней</li>
                <li>Максимальный: 14 дней</li>
            </ul>
            """

            # Устанавливаем базовые параметры в зависимости от типа работы
            if "Курсовая" in category:
                self.pages_spin.setMinimum(20)
                self.pages_spin.setMaximum(60)
                self.pages_spin.setValue(30)
            elif "Диплом" in category:
                self.pages_spin.setMinimum(50)
                self.pages_spin.setMaximum(150)
                self.pages_spin.setValue(70)
            elif "Практика" in category:
                self.pages_spin.setMinimum(15)
                self.pages_spin.setMaximum(40)
                self.pages_spin.setValue(20)

            self.service_info.setHtml(info)
            self.calculate_cost()
        else:
            # Если выбрана категория
            self.service_info.setHtml(f"""
            <h2>{item.text(0)}</h2>
            <p>Выберите конкретную услугу для получения подробной информации.</p>
            """)

    def calculate_cost(self):
        """Расчет стоимости"""
        try:
            if not hasattr(self, 'pages_spin') or not hasattr(self, 'urgency_combo'):
                return

            # Базовая стоимость за страницу
            base_per_page = 150  # Базовая стоимость за страницу
            pages = self.pages_spin.value()

            # Наценка за срочность
            urgency_multiplier = 1.0
            urgency = self.urgency_combo.currentText()
            if "Срочно" in urgency:
                urgency_multiplier = 1.3
            elif "Очень срочно" in urgency:
                urgency_multiplier = 1.5

            # Минимальная стоимость в зависимости от типа работы
            min_cost = 2000  # Базовая минимальная стоимость

            # Расчет итоговой стоимости
            total = max(min_cost, pages * base_per_page) * urgency_multiplier

            # Обновляем label
            self.total_cost.setText(f"Итоговая стоимость: {total:,.0f} ₽")

        except Exception as e:
            print(f"Ошибка при расчете стоимости: {e}")
            self.total_cost.setText("Ошибка расчета")
    def createAnalyticsTab(self):
        """Создание вкладки аналитики клиентов"""
        from .analytics_tab import ClientAnalyticsTab
        return ClientAnalyticsTab(self)

    def createContractsTab(self):
        """Создание вкладки договоров"""
        from .contracts_tab import ContractsTab
        return ContractsTab(self)

    def onServiceSelected(self, item, column):
        """Обработка выбора услуги в дереве"""
        # Здесь будет загрузка информации о выбранной услуге
        path = []
        current = item
        while current:
            path.insert(0, current.text(0))
            current = current.parent()

        service_path = " -> ".join(path)

        # Пример отображения информации
        if not item.parent():  # Если это категория
            info = f"""
            <h2>{item.text(0)}</h2>
            <p>Выберите подкатегорию для просмотра подробной информации.</p>
            """
        else:  # Если это конкретная услуга
            info = f"""
            <h2>{service_path}</h2>
            <hr>
            <h3>📝 Основная информация</h3>
            <ul>
                <li>Объем: 20-60 страниц</li>
                <li>Уникальность: от 70%</li>
                <li>Оформление: по ГОСТ</li>
            </ul>
            <h3>💰 Стоимость</h3>
            <ul>
                <li>Базовая цена: от 2000₽</li>
                <li>За страницу: 150₽</li>
                <li>Срочность: +50%</li>
            </ul>
            <h3>⏱️ Сроки</h3>
            <ul>
                <li>Минимальный: 3 дня</li>
                <li>Стандартный: 7 дней</li>
                <li>Максимальный: 14 дней</li>
            </ul>
            """

        self.service_info.setHtml(info)