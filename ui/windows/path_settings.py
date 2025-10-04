import os
import json
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QLabel, QFileDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QHBoxLayout,
                             QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt
from ui.message_utils import show_info, show_error


class PathSettingsDialog(QDialog):
    """Диалоговое окно для управления путями"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = "paths_settings.json"
        self.paths = self.load_paths()
        self.initUI()

    def initUI(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle('Настройка путей')
        self.setGeometry(300, 300, 600, 400)

        # Основной layout
        main_layout = QVBoxLayout()

        # Таблица для отображения существующих путей
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(['Название', 'Путь'])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        # Кнопки для управления
        buttons_layout = QHBoxLayout()

        self.add_excel_btn = QPushButton("Добавить Excel для оплат")
        self.add_excel_btn.clicked.connect(lambda: self.add_path('payment_excel', 'Excel-файл оплат (*.xlsx)'))

        self.add_folder_btn = QPushButton("Добавить папку")
        self.add_folder_btn.clicked.connect(self.add_folder)

        self.delete_btn = QPushButton("Удалить выбранный")
        self.delete_btn.clicked.connect(self.delete_selected_path)

        buttons_layout.addWidget(self.add_excel_btn)
        buttons_layout.addWidget(self.add_folder_btn)
        buttons_layout.addWidget(self.delete_btn)

        main_layout.addLayout(buttons_layout)

        # Кнопка закрытия
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        main_layout.addWidget(self.close_btn)

        self.setLayout(main_layout)

        # Загружаем существующие пути
        self.load_paths_to_table()

        # Стилизация
        self.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 4px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)

        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

    def load_paths(self):
        """Загрузка сохраненных путей из JSON-файла"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка при загрузке путей: {str(e)}")
                return {}
        else:
            return {}

    def save_paths(self):
        """Сохранение путей в JSON-файл"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.paths, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении путей: {str(e)}")
            return False

    def load_paths_to_table(self):
        """Загрузка существующих путей в таблицу"""
        self.table.setRowCount(0)
        row = 0

        for key, path in self.paths.items():
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(key))
            self.table.setItem(row, 1, QTableWidgetItem(path))
            row += 1

    def add_path(self, default_key, file_filter):
        """Добавление пути к файлу"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            file_filter
        )

        if file_path:
            # Если это payment_excel, напрямую используем ключ
            if default_key == 'payment_excel':
                self.paths[default_key] = file_path
                self.save_paths()
                self.load_paths_to_table()
                show_info(self, "Успех", f"Путь к Excel-файлу успешно сохранен")
            else:
                # Запрашиваем имя ключа
                key, ok = QInputDialog.getText(
                    self,
                    "Введите название",
                    "Введите название для этого пути:"
                )

                if ok and key:
                    self.paths[key] = file_path
                    self.save_paths()
                    self.load_paths_to_table()
                    show_info(self, "Успех", f"Путь успешно сохранен как '{key}'")

    def add_folder(self):
        """Добавление пути к папке"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку",
            ""
        )

        if folder_path:
            # Запрашиваем имя ключа
            key, ok = QInputDialog.getText(
                self,
                "Введите название",
                "Введите название для этого пути:"
            )

            if ok and key:
                self.paths[key] = folder_path
                self.save_paths()
                self.load_paths_to_table()
                show_info(self, "Успех", f"Путь к папке успешно сохранен как '{key}'")

    def delete_selected_path(self):
        """Удаление выбранного пути"""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            key_item = self.table.item(selected_row, 0)
            if key_item:
                key = key_item.text()

                reply = QMessageBox.question(
                    self,
                    'Подтверждение удаления',
                    f'Вы действительно хотите удалить путь "{key}"?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.Yes:
                    if key in self.paths:
                        del self.paths[key]
                        self.save_paths()
                        self.load_paths_to_table()
                        show_info(self, "Успех", f"Путь '{key}' успешно удален")
        else:
            show_error(self, "Ошибка", "Выберите путь для удаления")