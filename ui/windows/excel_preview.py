from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                           QPushButton, QFileDialog, QMessageBox, QHBoxLayout)
from PyQt5.QtCore import Qt
import pandas as pd
from core.database import Order, init_database

class ExcelPreviewDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.df = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Импорт данных из Excel')
        self.setGeometry(100, 100, 1000, 600)

        layout = QVBoxLayout(self)

        # Кнопки
        btn_layout = QHBoxLayout()

        self.select_file_btn = QPushButton('Выбрать Excel файл')
        self.select_file_btn.clicked.connect(self.selectFile)
        btn_layout.addWidget(self.select_file_btn)

        self.import_btn = QPushButton('Импортировать')
        self.import_btn.clicked.connect(self.importData)
        self.import_btn.setEnabled(False)
        btn_layout.addWidget(self.import_btn)

        layout.addLayout(btn_layout)

        # Таблица для предпросмотра
        self.table = QTableWidget()
        layout.addWidget(self.table)

    def selectFile(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            'Выберите Excel файл',
            '',
            'Excel files (*.xlsx *.xls)'
        )

        if filename:
            try:
                # Читаем Excel файл
                self.df = pd.read_excel(filename)

                # Показываем данные в таблице
                self.table.setRowCount(len(self.df))
                self.table.setColumnCount(len(self.df.columns))

                # Устанавливаем заголовки
                self.table.setHorizontalHeaderLabels(self.df.columns)

                # Заполняем таблицу данными
                for i in range(len(self.df)):
                    for j in range(len(self.df.columns)):
                        value = str(self.df.iloc[i, j])
                        item = QTableWidgetItem(value)
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Делаем ячейки только для чтения
                        self.table.setItem(i, j, item)

                # Разрешаем импорт
                self.import_btn.setEnabled(True)

            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось прочитать файл:\n{str(e)}')

    def importData(self):
        try:
            # Создаем временный Excel файл
            temp_file = 'temp_import.xlsx'
            self.df.to_excel(temp_file, index=False)

            # Инициализируем сессию базы данных
            session = init_database()
            try:
                # Используем метод import_from_excel класса Order
                Order.import_from_excel(session, temp_file)
                session.commit()

                # Удаляем временный файл
                import os
                os.remove(temp_file)

                QMessageBox.information(self, 'Успех', 'Данные успешно импортированы!')
                self.accept()

            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при импорте:\n{str(e)}')