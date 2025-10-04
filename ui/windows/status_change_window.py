from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QMessageBox)
from core.database import init_database, Order
from ui.windows.kanban_styles import DIALOG_BACKGROUNDS, BUTTON_COLORS, DIALOG_STYLES


class StatusChangeWindow(QDialog):
    def __init__(self, parent=None, order=None):
        super().__init__(parent)
        self.order = order
        self.session = init_database()
        self.initUI()

        # Применяем стиль в зависимости от текущего статуса
        bg_color = DIALOG_BACKGROUNDS[self.order.status]
        button_color = BUTTON_COLORS[self.order.status]['normal']
        button_hover = BUTTON_COLORS[self.order.status]['hover']

        self.setStyleSheet(DIALOG_STYLES.format(
            bg_color=bg_color,
            button_color=button_color,
            button_hover=button_hover
        ))

    def initUI(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Изменение статуса")
        self.setGeometry(300, 300, 400, 150)

        layout = QVBoxLayout(self)

        # Информация о текущем статусе
        current_status_layout = QHBoxLayout()
        current_status_layout.addWidget(QLabel("Текущий статус:"))
        current_status_layout.addWidget(QLabel(self.order.status))
        layout.addLayout(current_status_layout)

        # Выбор нового статуса
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Новый статус:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Новый",
            "В работе",
            "В ожидании оплаты",
            "Выполнен",
            "Отменен"
        ])
        self.status_combo.setCurrentText(self.order.status)
        status_layout.addWidget(self.status_combo)
        layout.addLayout(status_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_status)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def save_status(self):
        """Сохранение нового статуса"""
        try:
            new_status = self.status_combo.currentText()
            if new_status != self.order.status:

                # Получаем свежую версию заказа
                new_session = init_database()
                try:
                    order = new_session.query(Order).filter(Order.id == self.order.id).first()
                    if not order:
                        raise Exception(f"Заказ с ID {self.order.id} не найден")

                    order.status = new_status
                    # Обновляем даты скидки при изменении статуса
                    if new_status == 'В ожидании оплаты':
                        order.update_discount_dates()
                    new_session.commit()
                    QMessageBox.information(self, "Успех", "Статус успешно изменен!")
                    self.accept()
                finally:
                    new_session.close()
            else:
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")
