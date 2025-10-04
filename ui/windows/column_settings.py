from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                             QPushButton, QCheckBox, QScrollArea, QWidget)
from PyQt5.QtCore import Qt
import json
import os


class ColumnSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Список всех доступных колонок
        self.all_columns = {
            'ФИО': True,
            'Группа': True,
            'Услуги': True,
            'Направление': True,
            'Тема': True,
            'Кол-во': True,
            'Логин': True,
            'Пароль': True,
            'Сайт': True,
            'СТОИМОСТЬ': True,
            'Оплатил': True,
            'Осталось': True,
            'Общая сумма': True,
            'ФИО ПРЕПОДАВАТЕЛЯ': True,
            'ПОЧТА ПРЕПОДАВАТЕЛЯ': True,
            'Телефон': True,
            'Дата': True,
            'Срок': True,
            'Дата Оплаты': True,
            'Комментарий': True,
            'Статус': True,
            'Скидка': True
        }
        self.checkboxes = {}
        self.settings_file = 'column_settings.json'
        self.initUI()
        self.loadSettings()

    def initUI(self):
        self.setWindowTitle('Настройка отображения колонок')
        self.setGeometry(300, 300, 400, 500)

        layout = QVBoxLayout(self)

        # Создаем область прокрутки
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Создаем чекбоксы для каждой колонки
        for column in self.all_columns:
            checkbox = QCheckBox(column)
            checkbox.setChecked(self.all_columns[column])
            self.checkboxes[column] = checkbox
            scroll_layout.addWidget(checkbox)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Кнопки
        btn_layout = QHBoxLayout()

        select_all_btn = QPushButton('Выбрать все')
        select_all_btn.clicked.connect(self.selectAll)
        btn_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton('Снять все')
        deselect_all_btn.clicked.connect(self.deselectAll)
        btn_layout.addWidget(deselect_all_btn)

        save_btn = QPushButton('Сохранить')
        save_btn.clicked.connect(self.saveSettings)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def selectAll(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def deselectAll(self):
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def saveSettings(self):
        # Сохраняем состояние чекбоксов
        settings = {column: checkbox.isChecked()
                    for column, checkbox in self.checkboxes.items()}

        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

        self.accept()

    def loadSettings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # Применяем сохраненные настройки
                for column, checked in settings.items():
                    if column in self.checkboxes:
                        self.checkboxes[column].setChecked(checked)
            except:
                # Если возникла ошибка, используем настройки по умолчанию
                pass

    def getSelectedColumns(self):
        """Возвращает список выбранных колонок"""
        return [column for column, checkbox in self.checkboxes.items()
                if checkbox.isChecked()]