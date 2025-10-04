from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea,
                             QFrame, QHBoxLayout, QDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent
from core.database import Order
from core.database_manager import DatabaseManager
from ui.windows.payment_window import PaymentWindow
from ui.message_utils import show_warning, show_error


class KanbanColumn(QFrame):
    """Колонка канбан-доски с улучшенной обработкой перетаскивания"""
    status_changed = pyqtSignal(int, str)  # Сигнал: (order_id, new_status)

    def __init__(self, title, status, parent=None):
        super().__init__(parent)
        self.title = title
        self.status = status
        self.db_manager = DatabaseManager()
        self.orders = []  # Список заказов в колонке
        self.setup_ui()
        self.setAcceptDrops(True)

    def setup_ui(self):
        """Настройка интерфейса колонки"""
        self.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                min-width: 320px;
                max-width: 320px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Заголовок колонки
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 4px;
            }
        """)
        header_layout = QHBoxLayout(header)

        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 16px;
                font-weight: bold;
            }
        """)

        self.counter_label = QLabel("0")
        self.counter_label.setStyleSheet("""
            QLabel {
                background-color: #E0E0E0;
                color: #333333;
                padding: 2px 8px;
                border-radius: 10px;
            }
        """)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.counter_label)
        layout.addWidget(header)

        # Область для карточек
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                border-radius: 4px;
            }
        """)

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)

        self.scroll.setWidget(self.cards_widget)
        layout.addWidget(self.scroll)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обработка начала перетаскивания"""
        if event.mimeData().hasText():
            try:
                order_id = int(event.mimeData().text())
                with self.db_manager.session_scope() as session:
                    order = session.query(Order).get(order_id)
                    if order and order.status != self.status:  # Проверяем, что статус отличается
                        self.setStyleSheet("""
                            QFrame {
                                background-color: #E3F2FD;
                                border: 2px dashed #2196F3;
                                border-radius: 8px;
                                min-width: 320px;
                                max-width: 320px;
                            }
                        """)
                        event.accept()
                        return
            except (ValueError, Exception) as e:
                print(f"Ошибка при обработке dragEnter: {e}")
        event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Обработка перемещения при перетаскивании"""
        if event.mimeData().hasText():
            try:
                order_id = int(event.mimeData().text())
                with self.db_manager.session_scope() as session:
                    order = session.query(Order).get(order_id)
                    if order and order.status != self.status:
                        event.accept()
                        return
            except Exception:
                pass
        event.ignore()



    def dragLeaveEvent(self, event):
        """Обработка выхода перетаскивания за пределы"""
        self.setStyleSheet("""
            QFrame {
                background-color: #F5F5F5;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                min-width: 320px;
                max-width: 320px;
            }
        """)

    def dropEvent(self, event):
        """Обработка сброса карточки"""
        try:
            order_id = int(event.mimeData().text())

            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    event.ignore()
                    return

                old_status = order.status

                # Если перетаскиваем в ту же колонку - игнорируем
                if old_status == self.status:
                    event.ignore()
                    return

                # Проверка для статуса "Выполнен"
                if self.status == 'Выполнен':
                    remaining = order.recalculate_remaining()
                    if remaining > 0:
                        payment_window = PaymentWindow(self, order)
                        result = payment_window.exec_()

                        if result != QDialog.Accepted:
                            event.ignore()
                            return

                        # Важно: обновляем order из текущей сессии
                        session.refresh(order)
                        remaining = order.recalculate_remaining()

                        if remaining > 0:
                            show_warning(self, "Предупреждение",
                                         "Невозможно изменить статус на 'Выполнен'. Остались неоплаченные суммы.")
                            event.ignore()
                            return

                # Меняем статус
                order.status = self.status
                session.commit()

                # Принимаем событие и уведомляем об изменении
                event.accept()
                self.status_changed.emit(order_id, self.status, old_status)

        except ValueError:
            event.ignore()
        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при изменении статуса: {str(e)}")
            event.ignore()
        finally:
            # Восстанавливаем стиль
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.base_style['bg']};
                    border: 2px solid {self.base_style['border']};
                    border-radius: 8px;
                }}
            """)
    def update_cards(self, orders):
        """Обновление карточек в колонке"""
        try:
            # Очищаем текущие карточки
            self.clear()

            # Добавляем новые карточки
            for order_data in orders:
                from ui.components.order_card import OrderCard
                card = OrderCard(order_data)
                self.cards_layout.addWidget(card)

            # Обновляем счетчик
            self.counter_label.setText(str(len(orders)))

            # Обновляем размер контейнера
            self.cards_widget.adjustSize()

        except Exception as e:
            show_error(self, "Ошибка", f"Ошибка при обновлении карточек: {str(e)}")

    def clear(self):
        """Очистка всех карточек"""
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()