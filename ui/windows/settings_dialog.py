from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QSpinBox, QGroupBox
)
from PyQt5.QtCore import QSettings


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("OrderManager", "KanbanBoard")
        self.initUI()
        self.loadSettings()

    def initUI(self):
        """Инициализация интерфейса настроек"""
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Группа отображения
        display_group = QGroupBox("Отображение")
        display_layout = QVBoxLayout()

        # Автообновление
        self.auto_refresh = QCheckBox("Автоматическое обновление")
        display_layout.addWidget(self.auto_refresh)

        # Интервал обновления
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("Интервал обновления (сек):"))
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(5, 300)
        self.refresh_interval.setValue(30)
        refresh_layout.addWidget(self.refresh_interval)
        display_layout.addLayout(refresh_layout)

        # Размер кэша
        cache_layout = QHBoxLayout()
        cache_layout.addWidget(QLabel("Размер кэша (МБ):"))
        self.cache_size = QSpinBox()
        self.cache_size.setRange(10, 1000)
        self.cache_size.setValue(50)
        cache_layout.addWidget(self.cache_size)
        display_layout.addLayout(cache_layout)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        # Кнопки
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.saveSettings)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        # Стили
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                margin-top: 1ex;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QPushButton {
                padding: 5px 15px;
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
            QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)

    def loadSettings(self):
        """Загрузка настроек"""
        self.auto_refresh.setChecked(
            self.settings.value("auto_refresh", True, type=bool)
        )
        self.refresh_interval.setValue(
            self.settings.value("refresh_interval", 30, type=int)
        )
        self.cache_size.setValue(
            self.settings.value("cache_size", 50, type=int)
        )

    def saveSettings(self):
        """Сохранение настроек"""
        self.settings.setValue("auto_refresh", self.auto_refresh.isChecked())
        self.settings.setValue("refresh_interval", self.refresh_interval.value())
        self.settings.setValue("cache_size", self.cache_size.value())
        self.accept()