import json
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QListWidget, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt


class PathManager:
    """Класс для управления путями к файлам и папкам"""

    def __init__(self, config_file='paths_settings.json'):
        self.config_file = config_file
        self.paths = self._load_paths()

    def _load_paths(self):
        """Загрузка путей из JSON-файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка при загрузке путей: {str(e)}")
                return {}
        return {}

    def save_paths(self):
        """Сохранение путей в JSON-файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.paths, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении путей: {str(e)}")
            return False

    def get_path(self, path_key, default=None):
        """Получение пути по ключу"""
        path = self.paths.get(path_key, default)
        if path is None:
            print(f"ВНИМАНИЕ: Путь с ключом '{path_key}' не найден в настройках!")
        return path

    def add_path(self, path_key, path_value):
        """Добавление нового пути"""
        self.paths[path_key] = path_value
        return self.save_paths()

    def remove_path(self, path_key):
        """Удаление пути"""
        if path_key in self.paths:
            del self.paths[path_key]
            return self.save_paths()
        return False

    def get_all_paths(self):
        """Получение всех путей"""
        return self.paths


class PathManagerDialog(QDialog):
    """Диалоговое окно для управления путями"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.path_manager = PathManager()
        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle('Управление путями')
        self.setGeometry(300, 300, 600, 400)

        layout = QVBoxLayout()

        # Список путей
        self.path_list = QListWidget()
        self.path_list.setAlternatingRowColors(True)
        self.update_path_list()
        layout.addWidget(QLabel('Сохраненные пути:'))
        layout.addWidget(self.path_list)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.add_excel_btn = QPushButton('Добавить Excel файл')
        self.add_excel_btn.clicked.connect(self.add_excel_path)

        self.add_folder_btn = QPushButton('Добавить папку')
        self.add_folder_btn.clicked.connect(self.add_folder_path)

        self.remove_btn = QPushButton('Удалить')
        self.remove_btn.clicked.connect(self.remove_path)

        buttons_layout.addWidget(self.add_excel_btn)
        buttons_layout.addWidget(self.add_folder_btn)
        buttons_layout.addWidget(self.remove_btn)

        layout.addLayout(buttons_layout)

        # Кнопка закрытия
        close_layout = QHBoxLayout()
        self.close_btn = QPushButton('Закрыть')
        self.close_btn.clicked.connect(self.accept)
        close_layout.addStretch()
        close_layout.addWidget(self.close_btn)

        layout.addLayout(close_layout)

        self.setLayout(layout)

    def update_path_list(self):
        """Обновление списка путей"""
        self.path_list.clear()
        paths = self.path_manager.get_all_paths()
        for key, path in paths.items():
            self.path_list.addItem(f"{key}: {path}")

    def add_excel_path(self):
        """Добавление пути к Excel файлу"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Выберите Excel файл', '',
            'Excel файлы (*.xlsx *.xls);;Все файлы (*)'
        )

        if file_path:
            key, ok = self._get_path_key("Excel файл")
            if ok and key:
                self.path_manager.add_path(key, file_path)
                self.update_path_list()
                QMessageBox.information(self, 'Успех', f'Путь к файлу "{key}" успешно сохранен.')

    def add_folder_path(self):
        """Добавление пути к папке"""
        folder_path = QFileDialog.getExistingDirectory(
            self, 'Выберите папку', ''
        )

        if folder_path:
            key, ok = self._get_path_key("папке")
            if ok and key:
                self.path_manager.add_path(key, folder_path)
                self.update_path_list()
                QMessageBox.information(self, 'Успех', f'Путь к папке "{key}" успешно сохранен.')

    def remove_path(self):
        """Удаление выбранного пути"""
        selected_items = self.path_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите путь для удаления')
            return

        selected_text = selected_items[0].text()
        key = selected_text.split(':')[0].strip()

        reply = QMessageBox.question(
            self, 'Подтверждение', f'Вы уверены, что хотите удалить путь "{key}"?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.path_manager.remove_path(key)
            self.update_path_list()
            QMessageBox.information(self, 'Успех', f'Путь "{key}" успешно удален.')

    def _get_path_key(self, path_type):
        """Получение ключа для пути от пользователя"""
        from PyQt5.QtWidgets import QInputDialog
        key, ok = QInputDialog.getText(
            self, 'Ввод названия', f'Введите название для {path_type}:',
            text='payment_excel'  # Пример значения по умолчанию
        )
        return key, ok