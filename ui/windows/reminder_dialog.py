from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QMessageBox, QSpacerItem,
                             QSizePolicy, QTextEdit)
from PyQt5.QtCore import Qt, QDateTime, QUrl, QSettings
from PyQt5.QtGui import QDesktopServices
from datetime import datetime, timedelta
import re
from urllib.parse import quote


class ReminderDialog(QDialog):
    def __init__(self, order_data, parent=None):
        super().__init__(parent)
        self.order_data = order_data
        self.settings = QSettings('MPSP', 'OrderReminders')
        self.setup_ui()

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        self.setWindowTitle("Напоминание о заказе")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Информация о заказе
        info_text = (
            f"<h3>Заказ #{self.order_data['id']}</h3>"
            f"<p><b>Клиент:</b> {self.order_data['fio']}</p>"
            f"<p><b>Услуга:</b> {self.order_data['service']}</p>"
            f"<p><b>Дата создания:</b> {self.order_data['created_date'].strftime('%d.%m.%Y')}</p>"
            f"<p><b>Сумма к оплате:</b> {self.order_data['remaining_amount']:,.2f} ₽</p>"
        )
        info_label = QLabel(info_text)
        info_label.setTextFormat(Qt.RichText)
        layout.addWidget(info_label)

        # Предварительный просмотр сообщения
        message_label = QLabel("Текст сообщения:")
        layout.addWidget(message_label)

        self.message_edit = QTextEdit()
        self.message_edit.setPlainText(self.get_default_message())
        self.message_edit.setMinimumHeight(150)
        layout.addWidget(self.message_edit)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        # WhatsApp
        whatsapp_btn = QPushButton("📱 Написать в WhatsApp")
        whatsapp_btn.clicked.connect(self.send_whatsapp)
        whatsapp_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #128C7E;
            }
        """)

        # Напомнить позже
        self.remind_later_combo = QComboBox()
        self.remind_later_combo.addItems([
            "Через час",
            "Через день",
            "Через неделю",
            "Выбрать дату"
        ])

        remind_later_btn = QPushButton("⏰ Напомнить позже")
        remind_later_btn.clicked.connect(self.remind_later)
        remind_later_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        # Больше не напоминать
        dont_remind_btn = QPushButton("🔕 Больше не напоминать")
        dont_remind_btn.clicked.connect(self.dont_remind)
        dont_remind_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)

        # Закрыть
        close_btn = QPushButton("❌ Закрыть")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)

        # Добавляем кнопки в layout
        buttons_layout.addWidget(whatsapp_btn)
        buttons_layout.addWidget(self.remind_later_combo)
        buttons_layout.addWidget(remind_later_btn)
        buttons_layout.addWidget(dont_remind_btn)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def get_default_message(self):
        """Формирование текста сообщения по умолчанию"""
        return (
            f"Здравствуйте, {self.order_data['fio']}!\n\n"
            f"У вас есть заказ #{self.order_data['id']} от "
            f"{self.order_data['created_date'].strftime('%d.%m.%Y')} - "
            f"{self.order_data['service']}.\n"
            f"Хотели уточнить, актуален ли еще данный заказ?\n\n"
            f"Если да, то напоминаем о необходимости внесения оплаты.\n"
            f"Сумма к оплате: {self.order_data['remaining_amount']:,.2f} ₽\n\n"
            f"Для оплаты:\n"
            f"💳 Сбербанк: +79066322571\n"
            f"📱 WhatsApp: +79066322571"
        )

    def send_whatsapp(self):
        """Отправка сообщения в WhatsApp"""
        try:
            if not self.order_data.get('phone'):
                QMessageBox.warning(self, "Предупреждение",
                                    "У клиента не указан номер телефона!")
                return

            # Форматируем номер телефона
            phone = re.sub(r'[^\d]', '', self.order_data['phone'])
            if phone.startswith('8'):
                phone = '7' + phone[1:]
            elif not phone.startswith('7'):
                phone = '7' + phone

            # Получаем текст из редактора
            message = self.message_edit.toPlainText()

            # Формируем URL для WhatsApp
            url = f"https://wa.me/{phone}?text={quote(message)}"

            # Открываем WhatsApp
            QDesktopServices.openUrl(QUrl(url))

            # Сохраняем информацию о напоминании
            self.save_reminder_info('whatsapp_sent')

            # Закрываем диалог
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Ошибка при отправке сообщения: {str(e)}")

    def remind_later(self):
        """Обработка кнопки 'Напомнить позже'"""
        try:
            option = self.remind_later_combo.currentText()
            now = datetime.now()

            if option == "Через час":
                next_reminder = now + timedelta(hours=1)
            elif option == "Через день":
                next_reminder = now + timedelta(days=1)
            elif option == "Через неделю":
                next_reminder = now + timedelta(weeks=1)
            else:
                # TODO: Добавить диалог выбора даты
                next_reminder = now + timedelta(days=1)

            # Сохраняем время следующего напоминания
            self.save_reminder_info('postponed', next_reminder)

            QMessageBox.information(
                self,
                "Напоминание отложено",
                f"Следующее напоминание: {next_reminder.strftime('%d.%m.%Y %H:%M')}"
            )

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Ошибка при установке напоминания: {str(e)}")

    def dont_remind(self):
        """Отключение напоминаний для клиента"""
        try:
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                f"Отключить напоминания для клиента {self.order_data['fio']}?\n"
                "Это действие можно будет отменить в настройках.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Сохраняем настройку для клиента
                self.save_reminder_info('disabled')
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка",
                                 f"Ошибка при отключении напоминаний: {str(e)}")

    def save_reminder_info(self, action, next_reminder=None):
        """Сохранение информации о напоминании"""
        try:
            client_key = f"client_{self.order_data['fio']}"
            order_key = f"order_{self.order_data['id']}"

            # Сохраняем информацию о действии
            self.settings.setValue(f"{order_key}/last_action", action)
            self.settings.setValue(f"{order_key}/last_action_date",
                                   datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            if action == 'disabled':
                # Отключаем напоминания для клиента
                self.settings.setValue(f"{client_key}/reminders_disabled", True)

            elif action == 'postponed' and next_reminder:
                # Сохраняем время следующего напоминания
                self.settings.setValue(
                    f"{order_key}/next_reminder",
                    next_reminder.strftime('%Y-%m-%d %H:%M:%S')
                )

            self.settings.sync()

        except Exception as e:
            print(f"Ошибка при сохранении настроек: {e}")