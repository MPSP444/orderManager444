from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTabWidget, QWidget, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QScrollArea

class HelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Справка")
        self.setGeometry(300, 300, 600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                margin: 10px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QGroupBox {
                color: #2196F3;
                font-weight: bold;
                font-size: 16px;
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
        """)

        layout = QVBoxLayout(self)

        # Создаем вкладки
        tabs = QTabWidget()
        tabs.addTab(self.createShortcutsTab(), "Горячие клавиши")
        tabs.addTab(self.createAboutTab(), "О программе")
        layout.addWidget(tabs)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

    def createShortcutsTab(self):
        """Создание вкладки с горячими клавишами"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Основные операции
        basic_group = QGroupBox("Основные операции")
        basic_layout = QVBoxLayout()
        shortcuts = [
            ("Ctrl+N", "Создание нового заказа"),
            ("Ctrl+E", "Редактирование заказа"),
            ("Ctrl+O", "Внесение оплаты"),
            ("Ctrl+Q", "Отмена заказа"),
            ("Ctrl+Enter", "Открытие папки клиента")
        ]

        for shortcut, description in shortcuts:
            shortcut_layout = QHBoxLayout()
            shortcut_label = QLabel(shortcut)
            shortcut_label.setStyleSheet("font-weight: bold; color: #2196F3;")
            shortcut_label.setMinimumWidth(100)
            description_label = QLabel(description)

            shortcut_layout.addWidget(shortcut_label)
            shortcut_layout.addWidget(description_label)
            shortcut_layout.addStretch()
            basic_layout.addLayout(shortcut_layout)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        layout.addStretch()
        return tab

    def createAboutTab(self):
        """Создание вкладки о программе"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Создаем прокручиваемую область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: #F0F0F0;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                border-radius: 4px;
            }
        """)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Информация о программе
        program_group = QGroupBox("О программе")
        program_layout = QVBoxLayout()

        title_label = QLabel("Order Manager Pro")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        program_layout.addWidget(title_label)

        version_label = QLabel("Версия 12.04.0-17.03.2025")
        version_label.setAlignment(Qt.AlignCenter)
        program_layout.addWidget(version_label)

        description_label = QLabel(
            "Order Manager Pro - профессиональная система управления заказами, "
            "разработанная для эффективного ведения бизнеса и контроля выполнения работ."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        program_layout.addWidget(description_label)

        program_group.setLayout(program_layout)
        content_layout.addWidget(program_group)

        # Основные возможности
        features_group = QGroupBox("Основные возможности")
        features_layout = QVBoxLayout()

        features = {
            "Управление заказами": [
                "Создание и редактирование заказов",
                "Отслеживание статусов в реальном времени",
                "Канбан-доска для визуального управления",
                "Система напоминаний и уведомлений"
            ],
            "Работа с клиентами": [
                "Ведение базы клиентов",
                "История заказов каждого клиента",
                "Система лояльности и скидок",
                "Интеграция с WhatsApp для коммуникации"
            ],
            "Финансовый учет": [
                "Отслеживание платежей и задолженностей",
                "Автоматический расчет скидок",
                "Формирование чеков и квитанций",
                "Статистика и аналитика доходов"
            ],
            "Документооборот": [
                "Генерация договоров по шаблонам",
                "Создание отчетов и статистики",
                "Экспорт данных в Excel",
                "Автоматическое создание папок проектов"
            ]
        }

        for category, items in features.items():
            cat_label = QLabel(f"📌 {category}")
            cat_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 15px;")
            features_layout.addWidget(cat_label)

            for item in items:
                item_label = QLabel(f"  • {item}")
                item_label.setStyleSheet("color: #333; margin-left: 20px;")
                features_layout.addWidget(item_label)

            features_layout.addSpacing(10)

        features_group.setLayout(features_layout)
        content_layout.addWidget(features_group)

        # Преимущества системы
        advantages_group = QGroupBox("Преимущества системы")
        advantages_layout = QVBoxLayout()

        advantages = {
            "Функциональность": [
                "Комплексное решение для управления",
                "Автоматизация рутинных операций",
                "Гибкая система настроек",
                "Широкие возможности масштабирования"
            ],
            "Удобство использования": [
                "Современный интуитивный интерфейс",
                "Система горячих клавиш",
                "Быстрый доступ к функциям",
                "Поддержка различных тем оформления"
            ],
            "Безопасность": [
                "Контроль доступа к данным",
                "Система резервного копирования",
                "Журналирование действий",
                "Защита конфиденциальной информации"
            ]
        }

        for category, items in advantages.items():
            cat_label = QLabel(f"🌟 {category}")
            cat_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 15px;")
            advantages_layout.addWidget(cat_label)

            for item in items:
                item_label = QLabel(f"  • {item}")
                item_label.setStyleSheet("color: #333; margin-left: 20px;")
                advantages_layout.addWidget(item_label)

            advantages_layout.addSpacing(10)

        advantages_group.setLayout(advantages_layout)
        content_layout.addWidget(advantages_group)

        # Информация о разработчике
        developer_group = QGroupBox("Разработчик")
        developer_layout = QVBoxLayout()

        developer_info = [
            ("Компания:", "MPSP"),
            ("Телефон:", "+7 906 632-25-71"),
            ("Email:", "Mukam1@list.ru"),
            ("Сайт:", "https://vk.com/Gurbanmyradov99")
        ]

        for label, value in developer_info:
            info_layout = QHBoxLayout()
            label_widget = QLabel(label)
            label_widget.setStyleSheet("font-weight: bold;")
            label_widget.setMinimumWidth(100)
            value_widget = QLabel(value)

            info_layout.addWidget(label_widget)
            info_layout.addWidget(value_widget)
            info_layout.addStretch()
            developer_layout.addLayout(info_layout)

        developer_group.setLayout(developer_layout)
        content_layout.addWidget(developer_group)

        # Добавляем прокручиваемую область в основной layout
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        return tab

