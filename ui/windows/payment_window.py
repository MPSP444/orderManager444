from datetime import datetime
from core.database import Order
from core.database_manager import DatabaseManager
from .dialog_styles import DIALOG_WINDOW_STYLE
from .state_manager import StateManager
# Интеграция с менеджером путей
from ui.windows.payment_window_integration import integrate_path_manager_to_payment_window, modify_save_payment_method
import uuid
import urllib.parse
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QMessageBox, QFileDialog, QInputDialog, QApplication
)
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDoubleValidator, QDesktopServices


class PaymentWindow(QDialog):
    def __init__(self, parent=None, order=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.state_manager = StateManager()
        self.original_order_id = order.id

        try:
            self.load_order_data()
            # Применяем единый стиль
            self.setStyleSheet(DIALOG_WINDOW_STYLE)
            self.setup_ui()

            # Вот здесь должны быть эти вызовы
            integrate_path_manager_to_payment_window(self)
            modify_save_payment_method(self)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка инициализации окна: {str(e)}")
    def load_order_data(self):
        """Загрузка данных заказа"""
        with self.db_manager.session_scope() as session:
            order = session.query(Order).get(self.original_order_id)
            if not order:
                raise ValueError(f"Заказ с ID {self.original_order_id} не найден")

            # Сохраняем все необходимые данные
            self.current_data = {
                'id': order.id,
                'fio': order.fio,
                'group': order.group,
                'service': order.service,
                'cost': float(order.cost) if order.cost not in (None, 'Не указано') else 0.0,
                'paid_amount': float(order.paid_amount) if order.paid_amount not in (None, 'Не указано') else 0.0,
                'discount': order.discount if order.discount not in (None, 'Не указано') else None,
                'status': order.status
            }

            # Рассчитываем суммы
            if self.current_data['discount']:
                try:
                    discount_percent = float(self.current_data['discount'].strip('%'))
                    self.discount_amount = self.current_data['cost'] * (discount_percent / 100)
                    self.discounted_total = self.current_data['cost'] - self.discount_amount
                except (ValueError, AttributeError):
                    self.discount_amount = 0
                    self.discounted_total = self.current_data['cost']
            else:
                self.discount_amount = 0
                self.discounted_total = self.current_data['cost']

            self.remaining = max(0, self.discounted_total - self.current_data['paid_amount'])

    def offer_print_documents(self, order):
        """Предложение печати документов"""
        try:
            # Сохраняем ID заказа
            order_id = order.id if hasattr(order, 'id') else order

            msg = QMessageBox()
            msg.setWindowTitle("Печать документов")
            msg.setText("Выберите действие:")

            receipt_button = msg.addButton("Квитанция", QMessageBox.ActionRole)
            check_button = msg.addButton("Кассовый чек", QMessageBox.ActionRole)
            thanks_button = msg.addButton("Отправить благодарность", QMessageBox.ActionRole)
            review_button = msg.addButton("Благодарность + ссылка на отзыв", QMessageBox.ActionRole)  # Новая кнопка
            cancel_button = msg.addButton("Отмена", QMessageBox.RejectRole)

            msg.exec_()

            if msg.clickedButton() == receipt_button:
                with self.db_manager.session_scope() as session:
                    current_order = session.query(Order).get(order_id)
                    if current_order:
                        file_name = f"Квитанция_{current_order.fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        file_path, _ = QFileDialog.getSaveFileName(
                            self,
                            "Сохранить квитанцию",
                            file_name,
                            "PDF files (*.pdf)"
                        )
                        if file_path:
                            self.create_receipt_pdf(file_path, current_order)
                            QMessageBox.information(self, "Успех", "Квитанция успешно создана!")

            elif msg.clickedButton() == check_button:
                with self.db_manager.session_scope() as session:
                    current_order = session.query(Order).get(order_id)
                    if current_order:
                        file_name = f"Чек_{current_order.fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        file_path, _ = QFileDialog.getSaveFileName(
                            self,
                            "Сохранить чек",
                            file_name,
                            "PDF files (*.pdf)"
                        )
                        if file_path:
                            self.print_receipt(file_path, current_order)
                            QMessageBox.information(self, "Успех", "Чек успешно создан!")

            elif msg.clickedButton() == thanks_button:
                with self.db_manager.session_scope() as session:
                    current_order = session.query(Order).get(order_id)
                    if current_order:
                        self.send_thanks_message(current_order)

            elif msg.clickedButton() == review_button:  # Обработка новой кнопки
                # Передаем ID заказа вместо объекта
                self.send_thanks_with_review(order_id)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании документа: {str(e)}")

    def send_thanks_message(self, order):
        """Отправка благодарственного сообщения через WhatsApp с выбором шаблона"""
        try:
            # Проверяем наличие номера телефона
            phone = None

            if order.phone:
                # Очищаем телефон от лишних символов
                phone = order.phone.replace('+', '').replace('-', '').replace(' ', '')

            # Если телефона нет в базе, запрашиваем его
            if not phone:
                phone, ok = QInputDialog.getText(
                    self,
                    "Номер телефона",
                    "Введите номер телефона клиента (без +):"
                )
                if not ok or not phone:
                    return False

            # Создаем диалог для выбора шаблона
            template_msg = QMessageBox()
            template_msg.setWindowTitle("Выбор шаблона")
            template_msg.setText("Выберите шаблон благодарственного сообщения:")

            formal_btn = template_msg.addButton("Формальный", QMessageBox.ActionRole)
            friendly_btn = template_msg.addButton("Дружелюбный", QMessageBox.ActionRole)
            minimal_btn = template_msg.addButton("Минималистичный", QMessageBox.ActionRole)
            cancel_btn = template_msg.addButton("Отмена", QMessageBox.RejectRole)

            template_msg.exec_()

            # Определяем выбранный шаблон
            if template_msg.clickedButton() == formal_btn:
                thanks_message = (
                    "🌟 *Благодарим за Ваш заказ!* 🌟\n\n"
                    f"Уважаемый(ая) {order.fio}!\n\n"
                    "Мы искренне благодарны Вам за выбор нашей компании. 🙏\n"
                    "Ваша оплата успешно получена и зарегистрирована в нашей системе. ✅\n\n"
                    "Если у Вас возникнут вопросы или понадобится дополнительная информация, "
                    "наша команда всегда готова предоставить Вам необходимую поддержку.\n\n"
                    "С уважением,\n"
                    "Команда MPSP 💼"
                )
            elif template_msg.clickedButton() == friendly_btn:
                thanks_message = (
                    "🎉 *Ура! Спасибо за заказ!* 🎉\n\n"
                    f"Привет, {order.fio}! 👋\n\n"
                    "Мы очень рады, что ты выбрал(а) нас! 😊\n"
                    "Твоя оплата успешно получена! ✅💰\n\n"
                    "Если возникнут вопросы - просто напиши нам, мы всегда на связи! 📱\n\n"
                    "Отличного дня! ☀️\n"
                    "Команда MPSP 💙"
                )
            elif template_msg.clickedButton() == minimal_btn:
                thanks_message = (
                    "✅ *Оплата получена*\n\n"
                    f"Спасибо за заказ, {order.fio}!\n"
                    "Мы ценим Ваше доверие.\n\n"
                    "Команда MPSP 🤝"
                )
            else:
                # Пользователь нажал "Отмена"
                return False

            # Формируем ссылку для API через api.whatsapp.com
            # Это специальный API, который лучше сохраняет форматирование и эмодзи
            whatsapp_url = f"https://api.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(thanks_message)}"

            # Открываем WhatsApp в браузере
            QDesktopServices.openUrl(QUrl(whatsapp_url))

            QMessageBox.information(self, "Успех", "Сообщение с благодарностью отправлено!")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отправке сообщения: {str(e)}")
            return False

    def generate_review_link(self, order_id):
        """Генерирует короткую ссылку для отзыва клиента"""
        try:
            # Получаем данные о заказе
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    print(f"Ошибка: Заказ #{order_id} не найден в базе данных")
                    return None

                # Кодируем параметры для URL
                service_encoded = urllib.parse.quote(order.service or "")
                name_encoded = urllib.parse.quote(order.fio or "")

                # Генерируем уникальный, но короткий токен
                # Используем 8 символов из UUID для краткости
                token = str(uuid.uuid4()).split('-')[0][:8]

                # Сохраняем токен в заказе
                order.review_token = token

                # Добавляем ID клиента в токен для уникальности
                client_token = f"{token}_{order_id}"

                # Получаем данные из конфигурации
                from reviews_manager.config import SITE_CONFIG
                base_url = SITE_CONFIG.get('base_url', 'https://mpsp.online')
                reviews_page = SITE_CONFIG.get('reviews_page', '/submit-review.html')

                # Параметры для автозаполнения (добавляем статус=1 для автоматического одобрения)
                params = {
                    'token': client_token,
                    'order': order_id,
                    'name': name_encoded,
                    'service': service_encoded,
                    'auto_approve': 1  # Параметр для автоматического одобрения
                }

                # Формируем строку запроса
                query_string = urllib.parse.urlencode(params)

                # Формируем полную ссылку
                full_link = f"{base_url}{reviews_page}?{query_string}"

                # Сокращаем ссылку с помощью встроенного сервиса сокращения
                short_link = self.shorten_url(full_link)

                session.commit()
                print(f"Сгенерирована короткая ссылка для отзыва заказа #{order_id}: {short_link}")

                return short_link if short_link else full_link

        except Exception as e:
            print(f"Ошибка при генерации ссылки для отзыва: {str(e)}")
            return None

    def shorten_url(self, long_url):
        """Сокращает URL с помощью сервиса TinyURL"""
        try:
            # Метод через TinyURL API (простой и не требует регистрации)
            import requests

            tinyurl_api = f"https://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
            try:
                response = requests.get(tinyurl_api, timeout=5)
                if response.status_code == 200:
                    return response.text.strip()
            except Exception as e:
                print(f"Ошибка при сокращении через TinyURL: {str(e)}")

            # Если TinyURL не сработал, возвращаем исходный URL
            return long_url

        except Exception as e:
            print(f"Общая ошибка при сокращении URL: {str(e)}")
            return long_url

    def send_thanks_with_review(self, order_id):
        """Отправка благодарственного сообщения с ссылкой на отзыв через WhatsApp"""
        try:
            # Используем ID заказа вместо объекта
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    QMessageBox.warning(self, "Предупреждение", f"Заказ с ID {order_id} не найден")
                    return False

                # Сохраняем нужные данные из order для использования вне сессии
                order_data = {
                    'id': order.id,
                    'fio': order.fio,
                    'phone': order.phone
                }

                # Генерируем ссылку для отзыва внутри сессии
                review_link = self.generate_review_link(order.id)

            # Теперь используем только данные из order_data, а не сам объект order

            # Проверяем наличие номера телефона
            phone = None

            if order_data['phone']:
                # Очищаем телефон от лишних символов
                phone = order_data['phone'].replace('+', '').replace('-', '').replace(' ', '')

            # Если телефона нет в базе, запрашиваем его
            if not phone:
                phone, ok = QInputDialog.getText(
                    self,
                    "Номер телефона",
                    "Введите номер телефона клиента (без +):"
                )
                if not ok or not phone:
                    return False

            if not review_link:
                QMessageBox.warning(self, "Предупреждение", "Не удалось создать ссылку для отзыва")
                return False

            # Создаем диалог для выбора шаблона
            template_msg = QMessageBox()
            template_msg.setWindowTitle("Выбор шаблона")
            template_msg.setText("Выберите шаблон благодарственного сообщения с ссылкой на отзыв:")

            formal_btn = template_msg.addButton("Формальный", QMessageBox.ActionRole)
            friendly_btn = template_msg.addButton("Дружелюбный", QMessageBox.ActionRole)
            minimal_btn = template_msg.addButton("Минималистичный", QMessageBox.ActionRole)
            cancel_btn = template_msg.addButton("Отмена", QMessageBox.RejectRole)

            template_msg.exec_()

            # Определяем выбранный шаблон
            if template_msg.clickedButton() == formal_btn:
                thanks_message = (
                    "🌟 *Благодарим за Ваш заказ!* 🌟\n\n"
                    f"Уважаемый(ая) {order_data['fio']}!\n\n"
                    "Мы искренне благодарны Вам за выбор нашей компании. 🙏\n"
                    "Ваша оплата успешно получена и зарегистрирована в нашей системе. ✅\n\n"
                    "Нам очень важно Ваше мнение о работе с нами. Пожалуйста, поделитесь своими впечатлениями, "
                    "оставив отзыв по ссылке:\n"
                    f"{review_link}\n\n"
                    "С уважением,\n"
                    "Команда MPSP 💼"
                )
            elif template_msg.clickedButton() == friendly_btn:
                thanks_message = (
                    "🎉 *Ура! Спасибо за заказ!* 🎉\n\n"
                    f"Привет, {order_data['fio']}! 👋\n\n"
                    "Мы очень рады, что ты выбрал(а) нас! 😊\n"
                    "Твоя оплата успешно получена! ✅💰\n\n"
                    "Будем очень благодарны, если поделишься своими впечатлениями! "
                    "Оставь отзыв по ссылке 👇\n"
                    f"{review_link}\n\n"
                    "Отличного дня! ☀️\n"
                    "Команда MPSP 💙"
                )
            elif template_msg.clickedButton() == minimal_btn:
                thanks_message = (
                    "✅ *Оплата получена*\n\n"
                    f"Спасибо за заказ, {order_data['fio']}!\n"
                    "Мы ценим Ваше доверие.\n\n"
                    f"Оставить отзыв: {review_link}\n\n"
                    "Команда MPSP 🤝"
                )
            else:
                # Пользователь нажал "Отмена"
                return False

            # Формируем ссылку для API через api.whatsapp.com
            whatsapp_url = f"https://api.whatsapp.com/send?phone={phone}&text={urllib.parse.quote(thanks_message)}"

            # Открываем WhatsApp в браузере
            QDesktopServices.openUrl(QUrl(whatsapp_url))

            QMessageBox.information(self, "Успех", "Сообщение с благодарностью и ссылкой на отзыв отправлено!")

            # Устанавливаем флаг, что ссылка для отзыва уже была создана
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_data['id'])
                if order:
                    # Отмечаем, что для заказа уже была создана ссылка для отзыва
                    if not order.review_token:
                        order.review_token = "sent_with_thanks"
                    session.commit()

            return True

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при отправке сообщения: {str(e)}")
            return False

    def offer_review_link(self, order_id):
        """Предлагает создать ссылку для отзыва, если заказ полностью оплачен"""
        try:
            # Проверяем, есть ли уже ссылка для отзыва
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    return False

                # Если ссылка уже есть, не предлагаем снова
                if order.review_token:
                    return False

            # Если ссылки нет, предлагаем её создать
            reply = QMessageBox.question(
                self,
                "Отзыв клиента",
                "Заказ полностью оплачен! Хотите создать ссылку для отзыва клиента?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:
                self.generate_and_show_review_link(order_id)

        except Exception as e:
            print(f"Ошибка при предложении ссылки для отзыва: {str(e)}")
    def create_receipt(self, order):
        """Создание квитанции - обертка для обратной совместимости"""
        try:
            # Создаём имя файла
            file_name = f"Квитанция_{order.fio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить квитанцию",
                file_name,
                "PDF files (*.pdf)"
            )

            if file_path:
                self.create_receipt_pdf(file_path, order)
                QMessageBox.information(self, "Успех", "Квитанция успешно создана!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при создании квитанции: {str(e)}")

    def safe_float(self, value):
        """Безопасное преобразование в float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                if value.strip() == "Не указано":
                    return 0.0
                return float(value.replace(',', '.'))
            return 0.0
        except (ValueError, TypeError, AttributeError):
            return 0.0

    def recalculate_remaining(self):
        """Пересчет остатка с учетом скидки"""
        try:
            if hasattr(self, 'current_data'):
                cost = self.safe_float(self.current_data.get('cost', 0))
                paid = self.safe_float(self.current_data.get('paid_amount', 0))

                # Обработка скидки
                if self.current_data.get('discount'):
                    try:
                        discount_str = str(self.current_data['discount']).strip()
                        if discount_str != "Не указано":
                            discount_percent = float(discount_str.rstrip('%'))
                            discount_amount = cost * (discount_percent / 100)
                            self.discounted_total = cost - discount_amount
                        else:
                            self.discounted_total = cost
                    except (ValueError, TypeError):
                        self.discounted_total = cost
                else:
                    self.discounted_total = cost

                self.remaining = max(0, self.discounted_total - paid)
                return self.remaining
        except Exception as e:
            print(f"Ошибка при пересчете остатка: {e}")
            return 0.0

    def get_remaining_amount(self):
        """Получение остатка с учетом скидки"""
        try:
            if hasattr(self, 'remaining'):
                return self.remaining
            else:
                return self.recalculate_remaining()
        except Exception as e:
            print(f"Ошибка при получении остатка: {e}")
            return 0.0

    def validate_payment(self):
        """Проверка валидности платежа"""
        try:
            if not self.payment_input.text():
                raise ValueError("Введите сумму оплаты")

            payment_amount = self.safe_float(self.payment_input.text())
            if payment_amount <= 0:
                raise ValueError("Сумма оплаты должна быть больше 0")

            remaining = self.get_remaining_amount()
            if payment_amount > remaining:
                raise ValueError("Сумма оплаты превышает остаток")

            return True
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return False
    def _calculate_discounted_cost(self):
        """Расчет стоимости с учетом скидки"""
        try:
            if self.discount:
                discount_percent = float(self.discount.strip('%'))
                discount_amount = self.base_cost * (discount_percent / 100)
                return self.base_cost - discount_amount
            return self.base_cost
        except Exception:
            return self.base_cost

    def save_payment(self):
        """Сохранение оплаты"""
        try:
            if not self.validate_payment():
                return False

            payment_amount = float(self.payment_input.text())
            order_data = {}  # Создаем словарь для хранения необходимых данных
            old_status = None
            status_changed_to_completed = False
            review_link_created = False  # Флаг для отслеживания создания ссылки

            with self.db_manager.session_scope() as session:
                # Получаем свежую версию заказа
                order = session.query(Order).get(self.original_order_id)
                if not order:
                    QMessageBox.warning(self, "Ошибка", "Заказ не найден")
                    return False

                # Сохраняем старый статус для проверки изменения
                old_status = order.status
                review_link_created = bool(order.review_token)  # Проверяем, была ли уже создана ссылка

                # Обновляем данные заказа
                order.paid_amount = (order.paid_amount or 0) + payment_amount
                order.remaining_amount = self.discounted_total - order.paid_amount

                # Сохраняем дату при любой оплате (частичной или полной)
                order.payment_date = datetime.now().date()

                # Обновляем статус только при полной оплате
                if order.remaining_amount <= 0:
                    if order.status != 'Выполнен':
                        status_changed_to_completed = True
                    order.status = 'Выполнен'
                elif order.remaining_amount > 0 and order.status != 'В работе':
                    order.status = 'В ожидании оплаты'

                # Сохраняем данные заказа в словарь для использования после закрытия сессии
                order_data = {
                    'id': order.id,
                    'fio': order.fio,
                    'service': order.service,
                    'amount': payment_amount,
                    'status': order.status,
                    'old_status': old_status,
                    'status_changed_to_completed': status_changed_to_completed,
                    'review_link_created': review_link_created
                }

                # Сохраняем изменения
                session.commit()

                # Предлагаем печать документов
                self.offer_print_documents(order.id)

                # Уведомляем об изменениях
                self.state_manager.notify_all()

            # Теперь сессия закрыта, и мы работаем с сохраненными данными
            # Сообщаем об успешном сохранении данных заказа
            QMessageBox.information(self, "Успех", "Оплата успешно внесена!")

            # После успешного сохранения заказа, добавляем запись в Excel
            # используя сохраненные данные
            from ui.windows.excel_manager import ExcelManager
            excel_manager = ExcelManager(self)
            payment_data = {
                'order_id': order_data['id'],
                'fio': order_data['fio'],
                'amount': payment_amount
            }
            excel_manager.add_payment_to_excel(payment_data)

            # Если статус изменился на "Выполнен" и ссылка еще не была создана,
            # предлагаем создать ссылку для отзыва
            if order_data.get('status_changed_to_completed', False) and not order_data.get('review_link_created',
                                                                                           False):
                self.offer_review_link(order_data['id'])

            self.accept()
            return True

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении оплаты: {str(e)}")
            return False

    # Добавьте новый метод generate_and_show_review_link в класс PaymentWindow
    def generate_and_show_review_link(self, order_id):
        """Генерирует ссылку для отзыва и показывает ее пользователю"""
        try:
            # Генерируем ссылку для отзыва (уже сокращенную)
            short_link = self.generate_review_link(order_id)

            if not short_link:
                return False

            # Показываем сообщение с ссылками
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Ссылка для отзыва")
            msg_box.setText(f"Заказ #{order_id} выполнен! Предложите клиенту оставить отзыв.")

            # Отображаем короткую ссылку
            msg_box.setInformativeText(f"Сокращенная ссылка для отзыва:\n\n{short_link}")
            msg_box.setIcon(QMessageBox.Information)

            # Добавляем кнопки
            copy_button = msg_box.addButton("Копировать ссылку", QMessageBox.ActionRole)
            open_button = msg_box.addButton("Открыть в браузере", QMessageBox.ActionRole)
            send_button = msg_box.addButton("Отправить через WhatsApp", QMessageBox.ActionRole)
            cancel_button = msg_box.addButton("Закрыть", QMessageBox.RejectRole)

            # Показываем сообщение и ждем реакции пользователя
            msg_box.exec_()

            # Обрабатываем нажатие кнопок
            if msg_box.clickedButton() == copy_button:
                # Копируем ссылку в буфер обмена
                QApplication.clipboard().setText(short_link)
                QMessageBox.information(self, "Успех", "Ссылка скопирована в буфер обмена!")

            elif msg_box.clickedButton() == open_button:
                # Открываем ссылку в браузере
                QDesktopServices.openUrl(QUrl(short_link))

            elif msg_box.clickedButton() == send_button:
                # Отправляем через WhatsApp
                self.send_review_link_via_whatsapp(short_link, order_id)

            return True

        except Exception as e:
            print(f"Ошибка при генерации ссылки для отзыва: {str(e)}")
            return False
    # Добавьте метод для отправки ссылки через WhatsApp
    def send_review_link_via_whatsapp(self, review_link, order_id):
        """Отправляет ссылку на отзыв через WhatsApp"""
        try:
            # Получаем телефон клиента
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order or not order.phone:
                    # Если телефона нет в базе, запрашиваем его
                    phone, ok = QInputDialog.getText(
                        self,
                        "Номер телефона",
                        "Введите номер телефона клиента (без +):"
                    )
                    if not ok or not phone:
                        return False
                else:
                    # Очищаем телефон от лишних символов
                    phone = order.phone.replace('+', '').replace('-', '').replace(' ', '')

            # Формируем сообщение
            message = f"Спасибо за ваш заказ! Пожалуйста, оставьте отзыв о нашей работе: {review_link}"
            encoded_message = urllib.parse.quote(message)

            # Формируем ссылку для WhatsApp
            whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"

            # Открываем WhatsApp
            QDesktopServices.openUrl(QUrl(whatsapp_url))
            return True

        except Exception as e:
            print(f"Ошибка при отправке ссылки через WhatsApp: {str(e)}")
            return False

    # Добавьте метод для генерации ссылки на отзыв

    def setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Внесение оплаты")
        self.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout(self)

        # Информация о заказе
        info_group = QVBoxLayout()
        self.fio_label = QLabel(f"ФИО: {self.current_data['fio']}")
        self.group_label = QLabel(f"Группа: {self.current_data['group']}")
        self.service_label = QLabel(f"Услуга: {self.current_data['service']}")
        self.cost_label = QLabel(f"Стоимость: {self.current_data['cost']:.2f} руб.")
        self.paid_label = QLabel(f"Уже оплачено: {self.current_data['paid_amount']:.2f} руб.")
        self.remaining_label = QLabel(f"Осталось: {self.remaining:.2f} руб.")

        if self.current_data['discount']:
            self.discount_label = QLabel(f"Скидка: {self.current_data['discount']}")
            self.discounted_cost_label = QLabel(f"Сумма со скидкой: {self.discounted_total:.2f} руб.")
            info_group.addWidget(self.discount_label)
            info_group.addWidget(self.discounted_cost_label)

        for label in [self.fio_label, self.group_label, self.service_label,
                      self.cost_label, self.paid_label, self.remaining_label]:
            info_group.addWidget(label)

        layout.addLayout(info_group)

        # Поле для ввода суммы
        payment_layout = QHBoxLayout()
        self.payment_label = QLabel("Сумма оплаты:")
        self.payment_input = QLineEdit()
        self.payment_input.setPlaceholderText("Введите сумму")
        validator = QDoubleValidator(0, 999999.99, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.payment_input.setValidator(validator)

        # Кнопка заполнения остатка
        self.fill_remaining_btn = QPushButton("Заполнить остаток")
        self.fill_remaining_btn.clicked.connect(self.fill_remaining_amount)
        self.fill_remaining_btn.setObjectName("fill_remaining_btn")

        payment_layout.addWidget(self.payment_label)
        payment_layout.addWidget(self.payment_input)
        payment_layout.addWidget(self.fill_remaining_btn)

        layout.addLayout(payment_layout)

        # Кнопки управления
        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_payment)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)
        layout.addLayout(buttons_layout)

    def setup_style(self):
        """Настройка стилей"""
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton#fill_remaining_btn {
                background-color: #4CAF50;
            }
            QPushButton#fill_remaining_btn:hover {
                background-color: #388E3C;
            }
            QDialog {
                background-color: white;
                margin: 10px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)

    def fill_remaining_amount(self):
        """Заполнение оставшейся суммы"""
        try:
            # Используем расчитанный остаток из инициализации
            self.payment_input.setText(str(self.remaining))
        except Exception as e:
            print(f"Ошибка при заполнении остатка: {e}")

    def print_receipt(self, file_path, order):
        """Печать кассового чека"""
        try:
            # Импортируем все необходимые модули
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os

            # Получаем актуальные данные заказа в контексте сессии
            with self.db_manager.session_scope() as session:
                current_order = session.query(Order).get(order.id)
                if not current_order:
                    raise ValueError(f"Заказ с ID {order.id} не найден")

                # Создаем копию данных заказа
                order_data = {
                    'id': current_order.id,
                    'fio': current_order.fio,
                    'group': current_order.group,
                    'created_date': current_order.created_date,
                    'deadline': current_order.deadline,
                    'service': current_order.service,
                    'discount': current_order.discount,
                    'cost': current_order.cost,
                    'paid_amount': current_order.paid_amount,
                    'remaining_amount': current_order.remaining_amount,
                    'status': current_order.status
                }

            # Регистрируем шрифт с обработкой ошибок
            try:
                pdfmetrics.registerFont(TTFont('Courier', 'C:\\Windows\\Fonts\\cour.ttf'))
            except:
                try:
                    pdfmetrics.registerFont(TTFont('Courier', '/usr/share/fonts/TTF/DejaVuSansMono.ttf'))
                except Exception as e:
                    print(f"Ошибка при регистрации шрифта: {e}")
                    pdfmetrics.registerFont(TTFont('Courier', 'Helvetica'))

            # Создаем документ
            doc = SimpleDocTemplate(
                file_path,
                pagesize=(140 * mm, 280 * mm),
                rightMargin=5 * mm,
                leftMargin=5 * mm,
                topMargin=5 * mm,
                bottomMargin=5 * mm
            )

            elements = []

            # Стили
            title_style = ParagraphStyle(
                'CashTitle',
                fontName='Courier',
                fontSize=20,
                alignment=1,
                spaceAfter=4 * mm,
                leading=24
            )

            text_style = ParagraphStyle(
                'CashText',
                fontName='Courier',
                fontSize=14,
                leading=16,
                alignment=1
            )

            # Заголовок
            elements.append(Paragraph("КАССОВЫЙ ЧЕК", title_style))
            elements.append(Paragraph("ООО MPSP", text_style))
            elements.append(Paragraph(f"Тел: +7 906 632-25-71", text_style))
            elements.append(Paragraph("-" * 42, text_style))

            # Дата и время
            current_time = datetime.now().strftime('%d-%m-%Y %H:%M')
            elements.append(Paragraph(f"Дата: {current_time}", text_style))
            elements.append(Paragraph("-" * 42, text_style))

            # Информация о заказе
            data = [
                ["Номер заказа:", str(order_data['id'])],
                ["ФИО:", order_data['fio']],
                ["Группа:", order_data['group']],
                ["Дата заказа:",
                 order_data['created_date'].strftime('%d-%m-%Y') if order_data['created_date'] else 'Не указано'],
                ["Срок:", order_data['deadline'] or 'Не указано'],
                ["Услуга:", order_data['service']],
                ["Скидка:", f"{order_data['discount']}" if order_data['discount'] else "Не указано"],
                ["Стоимость:", f"{order_data['cost']:,.2f} ₽" if order_data['cost'] else "0.00 ₽"],
                ["Оплачено:", f"{order_data['paid_amount']:,.2f} ₽" if order_data['paid_amount'] else "0.00 ₽"],
                ["Остаток:",
                 f"{order_data['remaining_amount']:,.2f} ₽" if order_data['remaining_amount'] else "0.00 ₽"],
                ["Статус:", order_data['status']]
            ]

            # Создаем таблицу
            table = Table(data, colWidths=[40 * mm, 90 * mm])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Courier', 14),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))

            elements.append(table)
            elements.append(Paragraph("-" * 42, text_style))

            # Итоги
            total_data = [
                ["ИТОГО:", f"{order_data['cost']:,.2f} ₽" if order_data['cost'] else "0.00 ₽"],
                ["Оплачено:", f"{order_data['paid_amount']:,.2f} ₽" if order_data['paid_amount'] else "0.00 ₽"],
                ["Остаток:", f"{order_data['remaining_amount']:,.2f} ₽" if order_data['remaining_amount'] else "0.00 ₽"]
            ]

            total_table = Table(total_data, colWidths=[70 * mm, 60 * mm])
            total_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Courier', 16),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))

            elements.append(total_table)
            elements.append(Paragraph("-" * 42, text_style))

            # Информация для оплаты
            elements.append(Paragraph("ДЛЯ ОПЛАТЫ:", text_style))
            elements.append(Paragraph("Сбербанк: +79066322571", text_style))
            elements.append(Paragraph("WhatsApp: +79066322571", text_style))
            elements.append(Paragraph("-" * 42, text_style))

            # Подписи
            signature_data = [
                ["Подпись:", "_________________"],
                ["Дата:", "_________________"]
            ]

            signature_table = Table(signature_data, colWidths=[40 * mm, 90 * mm])
            signature_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Courier', 14),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))

            elements.append(signature_table)

            # Создаем документ
            doc.build(elements)

            # Проверяем, что файл создан
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл {file_path} не был создан")

            QMessageBox.information(self, "Успех", "Чек успешно создан!")

        except Exception as e:
            error_msg = f"Ошибка при создании чека: {str(e)}"
            print(error_msg)  # Для отладки
            QMessageBox.critical(self, "Ошибка", error_msg)

    def create_receipt_pdf(self, file_path, order):
        """Создание PDF квитанции"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os

            # Получаем актуальные данные заказа в контексте сессии
            with self.db_manager.session_scope() as session:
                current_order = session.query(Order).get(order.id)
                if not current_order:
                    raise ValueError(f"Заказ с ID {order.id} не найден")

                # Создаем копию данных заказа
                order_data = {
                    'id': current_order.id,
                    'fio': current_order.fio,
                    'group': current_order.group,
                    'phone': current_order.phone,
                    'theme': current_order.theme,
                    'service': current_order.service,
                    'cost': current_order.cost,
                    'paid_amount': current_order.paid_amount,
                    'remaining_amount': current_order.remaining_amount,
                    'status': current_order.status
                }

            # Регистрируем шрифт Arial
            try:
                pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
            except:
                try:
                    pdfmetrics.registerFont(TTFont('Arial', '/usr/share/fonts/TTF/DejaVuSans.ttf'))
                except Exception as e:
                    print(f"Ошибка при регистрации шрифта: {e}")
                    pdfmetrics.registerFont(TTFont('Arial', 'Helvetica'))

            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )

            elements = []
            styles = getSampleStyleSheet()

            # Создаем стили
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1,
                fontName='Arial'
            )

            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=12,
                fontName='Arial'
            )

            # Заголовок квитанции
            elements.append(Paragraph("Квитанция об оплате", title_style))
            elements.append(Spacer(1, 20))

            # Данные квитанции
            receipt_data = [
                ["Номер квитанции:", datetime.now().strftime('%Y%m%d%H%M%S')],
                ["Номер заказа:", str(order_data['id'])],
                ["Дата:", datetime.now().strftime('%d.%m.%Y %H:%M')],
                ["ФИО клиента:", order_data['fio']],
                ["Группа:", order_data['group']],
                ["Телефон:", order_data['phone'] or "Не указан"],
                ["Тема:", order_data['theme'] or "Не указано"],
                ["Услуга:", order_data['service']],
                ["Стоимость:", f"{order_data['cost']:,.2f} ₽" if order_data['cost'] else "0.00 ₽"],
                ["Оплачено:", f"{order_data['paid_amount']:,.2f} ₽" if order_data['paid_amount'] else "0.00 ₽"],
                ["Остаток:",
                 f"{order_data['remaining_amount']:,.2f} ₽" if order_data['remaining_amount'] else "0.00 ₽"],
                ["Статус:", order_data['status']]
            ]

            # Создаем таблицу с данными квитанции
            table = Table(receipt_data, colWidths=[150, 300])
            table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 40))

            # Подпись
            signature_data = [
                ["Подпись оператора:", "_________________"],
                ["Подпись клиента:", "_________________"]
            ]
            signature_table = Table(signature_data, colWidths=[150, 300])
            signature_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            elements.append(signature_table)

            # Добавляем информацию о компании
            company_style = ParagraphStyle(
                'Company',
                parent=styles['Normal'],
                fontSize=14,
                alignment=1,
                spaceAfter=10,
                fontName='Arial'
            )

            elements.append(Spacer(1, 20))
            elements.append(Paragraph("-" * 100, company_style))
            elements.append(Spacer(1, 20))

            elements.append(Paragraph("ООО MPSP", company_style))
            elements.append(Paragraph("WhatsApp: +79066322571", company_style))
            elements.append(Paragraph("Для перевода: +79066322571 Сбербанк", company_style))

            # Строим документ
            doc.build(elements)

            # Проверяем, что файл создан
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл {file_path} не был создан")

            QMessageBox.information(self, "Успех", "Квитанция успешно создана!")

        except Exception as e:
            error_msg = f"Ошибка при создании квитанции: {str(e)}"
            print(error_msg)  # Для отладки
            QMessageBox.critical(self, "Ошибка", error_msg)




