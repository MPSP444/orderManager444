import json
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt


class ImportReviewsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Импорт отзывов')
        self.setGeometry(300, 300, 400, 200)

        layout = QVBoxLayout()

        title = QLabel('Импорт отзывов из JSON файла')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 16px; font-weight: bold; margin-bottom: 20px;')
        layout.addWidget(title)

        self.status_label = QLabel('Готов к импорту отзывов')
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        import_btn = QPushButton('Выбрать JSON файл')
        import_btn.clicked.connect(self.import_reviews)
        layout.addWidget(import_btn)

        self.setLayout(layout)

    def import_reviews(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл отзывов", "", "JSON Files (*.json)")

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)

            if isinstance(reviews_data, list):
                reviews_list = reviews_data
            elif isinstance(reviews_data, dict) and 'reviews' in reviews_data:
                reviews_list = reviews_data['reviews']
            else:
                QMessageBox.warning(self, 'Ошибка формата', 'Неверный формат файла отзывов')
                return

            self.status_label.setText(f'Импорт {len(reviews_list)} отзывов...')
            QApplication.processEvents()

            successful, failed = self.review_manager.import_pending_reviews(reviews_list)

            if successful > 0:
                QMessageBox.information(self, 'Успех',
                                        f'Успешно импортировано {successful} отзывов. Не удалось импортировать: {failed}')
            else:
                QMessageBox.warning(self, 'Ошибка', f'Не удалось импортировать отзывы. Ошибок: {failed}')

            self.status_label.setText(f'Готов к импорту отзывов')

        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Произошла ошибка при импорте: {str(e)}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = ImportReviewsWidget()
    widget.show()
    sys.exit(app.exec_())