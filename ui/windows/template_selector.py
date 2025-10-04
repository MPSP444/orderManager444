from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QCheckBox, QPushButton, QScrollArea, QWidget, QMessageBox,
                             QSizePolicy)
from PyQt5.QtCore import Qt
import os
import shutil
import sys


class TemplateSelector(QDialog):
    def __init__(self, parent=None, client_name="", service_name="", direction=""):
        super().__init__(parent)
        self.client_name = client_name
        self.service_name = service_name
        self.direction = direction
        self.selected_templates = []
        self.template_checkboxes = []

        # Получаем путь к корневой папке проекта (order_manager)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))  # Поднимаемся на два уровня вверх
        self.templates_dir = os.path.join(project_root, "Образцы")
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Выбор файлов-образцов")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Заголовок
        header = QLabel("Выберите файлы-образцы для копирования:")
        header.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)

        # Область прокрутки для списка файлов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.templates_layout = QVBoxLayout(scroll_content)

        # Загружаем и отображаем доступные шаблоны
        self.load_templates()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        # Кнопки
        buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("Выбрать все")
        select_all_btn.clicked.connect(self.select_all_templates)

        create_btn = QPushButton("Создать файлы")
        create_btn.clicked.connect(self.create_files)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(select_all_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(create_btn)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def load_templates(self):
        """Загрузка доступных шаблонов"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            QMessageBox.warning(self, "Предупреждение",
                                f"Папка с образцами не найдена.\nСоздана новая папка по пути:\n{self.templates_dir}")
            return

        # Очищаем текущий список
        for checkbox in self.template_checkboxes:
            self.templates_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.template_checkboxes.clear()

        try:
            # Получаем список всех файлов из корневой папки Образцы
            all_templates = []
            for file in os.listdir(self.templates_dir):
                if os.path.isfile(os.path.join(self.templates_dir, file)):
                    all_templates.append(os.path.join(self.templates_dir, file))

            if not all_templates:
                label = QLabel("Нет доступных шаблонов в папке Образцы")
                label.setStyleSheet("color: #666; padding: 20px;")
                self.templates_layout.addWidget(label)
                return

            # Разбиваем название услуги на ключевые слова
            service_keywords = set(word.lower() for word in self.service_name.split())

            # Группируем файлы по релевантности
            exact_service_match = []  # Точное совпадение с услугой
            partial_service_match = []  # Частичное совпадение с услугой
            direction_match = []  # Совпадение с направлением
            other_files = []  # Остальные файлы

            for template in all_templates:
                filename = os.path.basename(template).lower()

                # Проверяем точное совпадение с услугой
                if self.service_name.lower() in filename:
                    exact_service_match.append(template)
                    continue

                # Проверяем частичное совпадение (по ключевым словам услуги)
                if any(keyword in filename for keyword in service_keywords):
                    partial_service_match.append(template)
                    continue

                # Проверяем совпадение с направлением
                if self.direction and self.direction.lower() in filename:
                    direction_match.append(template)
                    continue

                other_files.append(template)

            # Добавляем группы в порядке приоритета
            if exact_service_match:
                self.add_template_group("✅ Рекомендуемые файлы:", exact_service_match, True)

            if partial_service_match:
                self.add_template_group("📁 Похожие файлы:", partial_service_match, False)

            if direction_match:
                self.add_template_group(f"📂 Файлы по направлению '{self.direction}':", direction_match, False)

            if other_files:
                # Сортируем остальные файлы по алфавиту
                other_files.sort(key=lambda x: os.path.basename(x).lower())
                self.add_template_group("📑 Другие шаблоны:", other_files, False)

            # Добавляем растягивающийся элемент в конец
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.templates_layout.addWidget(spacer)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке шаблонов: {str(e)}")
            error_label = QLabel(f"Ошибка загрузки шаблонов: {str(e)}")
            error_label.setStyleSheet("color: #ff0000; padding: 20px;")
            self.templates_layout.addWidget(error_label)

    def add_template_group(self, group_title, templates, auto_check=False):
        """Добавление группы шаблонов"""
        if templates:
            group_label = QLabel(group_title)
            group_label.setStyleSheet("font-weight: bold; color: #666;")
            self.templates_layout.addWidget(group_label)

            for template_path in templates:
                checkbox = QCheckBox(os.path.basename(template_path))
                checkbox.setProperty("template_path", template_path)
                checkbox.setChecked(auto_check)
                self.template_checkboxes.append(checkbox)
                self.templates_layout.addWidget(checkbox)

            # Добавляем разделитель
            separator = QLabel()
            separator.setStyleSheet("border-bottom: 1px solid #ddd; margin: 5px 0;")
            self.templates_layout.addWidget(separator)

    def select_all_templates(self):
        """Выбор всех шаблонов"""
        for checkbox in self.template_checkboxes:
            checkbox.setChecked(True)

    def create_files(self):
        """Создание файлов на основе выбранных шаблонов"""
        selected_paths = [cb.property("template_path") for cb in self.template_checkboxes if cb.isChecked()]

        if not selected_paths:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один файл!")
            return

        try:
            # Создаем базовый путь для сохранения
            base_path = r"D:\Users\mgurbanmuradov\Documents\Общая"
            client_path = os.path.join(base_path, self.client_name)
            service_path = os.path.join(client_path, self.service_name)

            if not os.path.exists(service_path):
                os.makedirs(service_path)

            # Копируем каждый выбранный файл
            for template_path in selected_paths:
                file_name = os.path.basename(template_path)
                name, ext = os.path.splitext(file_name)

                # Формируем новое имя файла
                new_name = f"{self.client_name} - {name}{ext}"
                new_path = os.path.join(service_path, new_name)

                # Копируем файл
                shutil.copy2(template_path, new_path)

            QMessageBox.information(self, "Успешно",
                                    f"Файлы успешно созданы в папке:\n{service_path}")

            # Открываем папку
            os.startfile(service_path)

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании файлов: {str(e)}")

    def get_selected_templates(self):
        """Получение списка выбранных шаблонов"""
        return [cb.property("template_path") for cb in self.template_checkboxes if cb.isChecked()]