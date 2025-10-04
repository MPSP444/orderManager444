import sys

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QSpinBox, QPushButton, QLineEdit,
                             QTextEdit, QGroupBox, QCompleter, QMessageBox,
                             QDoubleSpinBox, QWidget, QFrame, QScrollArea, QGraphicsDropShadowEffect, QApplication,
                             QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QColor, QFont
from datetime import datetime, timedelta
import os
from sqlalchemy import func
from core.database import Order
from core.database_manager import DatabaseManager
from .state_manager import StateManager


class AnimatedGroupBox(QGroupBox):
    """Группа с эффектами"""
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self._setup_effects()

    def _setup_effects(self):
        self.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                margin-top: 15px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #0056b3;
                font-weight: bold;
            }
        """)

    def enterEvent(self, event):
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)


class ModernButton(QPushButton):
    """Кнопка с современным дизайном"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._setup_effects()

    def _setup_effects(self):
        self.setMinimumHeight(40)
        self.setCursor(Qt.PointingHandCursor)

        try:
            # Пробуем создать эффект тени
            self.shadow = QGraphicsDropShadowEffect()
            self.shadow.setBlurRadius(15)
            self.shadow.setColor(QColor(0, 0, 0, 80))
            self.shadow.setOffset(0, 2)
            self.setGraphicsEffect(self.shadow)
        except Exception as e:
            print(f"Не удалось создать эффект тени для кнопки: {e}")

        # В любом случае применяем базовые стили
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)

class ClientInfoWidget(QFrame):
    """Виджет для отображения информации о клиенте"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Заголовок и кнопка детальной информации в одной строке
        header_layout = QHBoxLayout()

        # Заголовок
        self.title = QLabel("Информация о клиенте")
        self.title.setFont(QFont("Arial", 12, QFont.Bold))
        self.title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(self.title)

        # Кнопка детальной информации
        self.detail_button = QPushButton("Подробный анализ")
        self.detail_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0D47A1;
            }
        """)
        self.detail_button.setFixedWidth(150)
        self.detail_button.clicked.connect(self.show_detailed_info)
        header_layout.addWidget(self.detail_button)

        self.layout.addLayout(header_layout)

        # Основной текст
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #e0e0e0;
            }
        """)
        self.layout.addWidget(self.info_label)

        # Стилизация
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)

        # Изначально скрываем виджет
        self.hide()

    def update_info(self, client_data):
        """Обновление информации о клиенте"""
        if not client_data:
            self.hide()
            return

        # Сохраняем имя клиента для кнопки детальной информации
        if 'client_name' in client_data:
            self.client_name = client_data['client_name']

        info_text = []

        # Статистика
        if client_data.get('total_orders', 0) > 0:
            stats = (f"📊 Статистика клиента:\n"
                     f"• Всего заказов: {client_data['total_orders']}\n"
                     f"• Общая сумма заказов: {client_data['total_amount']:,.0f} ₽\n"
                     f"• Оплачено всего: {client_data['total_paid']:,.0f} ₽")
            info_text.append(stats)

        # Предупреждения
        if client_data.get('warnings'):
            warnings = "⚠️ Предупреждения:\n" + "\n".join(client_data['warnings'])
            info_text.append(warnings)

        # Аналитика оплат
        if client_data.get('payment_analytics'):
            pa = client_data['payment_analytics']
            payment_info = [f"⏱️ Анализ сроков оплаты:"]

            if pa.get('average_days') is not None:
                payment_info.append(f"• Среднее время оплаты: {pa['average_days']:.1f} дней")
                payment_info.append(f"• Минимальный срок: {pa['min_days']} дней")
                payment_info.append(f"• Максимальный срок: {pa['max_days']} дней")

            # Добавляем детали оплат для каждого заказа
            if pa.get('details'):
                payment_info.append("\nИстория оплат:")
                for detail in pa['details'][:3]:  # Показываем только 3 последних заказа
                    days_text = f"{detail['days_to_pay']} дней" if detail['days_to_pay'] != 1 else "1 день"
                    payment_info.append(
                        f"• Заказ №{detail['id']}: спустя {days_text}"
                        f" (создан {detail['created_date'].strftime('%d.%m.%Y')}, "
                        f"оплачен {detail['payment_date'].strftime('%d.%m.%Y')})"
                    )

                if len(pa['details']) > 3:
                    payment_info.append("• ... (нажмите «Подробный анализ» для полной информации)")

            info_text.append("\n".join(payment_info))

        # Рекомендации
        if client_data.get('recommendations'):
            recommendations = "💡 Рекомендации:\n" + "\n".join(client_data['recommendations'])
            info_text.append(recommendations)

        # Обновляем текст
        self.info_label.setText("\n\n".join(info_text))
        self.show()

    def show_detailed_info(self):
        """Открытие окна с детальной информацией о клиенте"""
        if not self.client_name:
            return

        try:
            # Импортируем здесь, чтобы избежать циклических импортов
            from ui.windows.client_detail_window import ClientDetailWindow
            detail_window = ClientDetailWindow(self, client_name=self.client_name)
            detail_window.exec_()
        except Exception as e:
            print(f"Ошибка при открытии детальной информации: {e}")

    def _clear_containers(self):
        """Очистка всех контейнеров"""
        for container in [self.stats_container, self.debt_container,
                          self.recommendations_container]:
            while container.count():
                item = container.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()


class NewOrderWindow(QDialog):
    """Окно создания/редактирования заказа"""

    def __init__(self, parent=None, order=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.state_manager = StateManager()
        self.order_id = order.id if order else None  # Сохраняем только ID

        try:
            if self.order_id:  # Если это редактирование
                with self.db_manager.session_scope() as session:
                    # Получаем свежую копию заказа
                    order = session.query(Order).get(self.order_id)
                    if not order:
                        raise ValueError(f"Заказ с ID {self.order_id} не найден")

                    # Сохраняем копию данных
                    self.order_data = {
                        'id': order.id,
                        'fio': order.fio,
                        'group': order.group,
                        'service': order.service,
                        'direction': order.direction,
                        'theme': order.theme,
                        'quantity': order.quantity,
                        'login': order.login,
                        'password': order.password,
                        'website': order.website,
                        'cost': order.cost,
                        'paid_amount': order.paid_amount,
                        'remaining_amount': order.remaining_amount,
                        'total_amount': order.total_amount,
                        'teacher_name': order.teacher_name,
                        'teacher_email': order.teacher_email,
                        'phone': order.phone,
                        'deadline': order.deadline,
                        'comment': order.comment,
                        'status': order.status,
                        'discount': order.discount
                    }

            # Установка заголовка окна
            self.setWindowTitle("Редактирование заказа" if self.order_id else "Новый заказ")
            self.setMinimumWidth(900)
            self.setMinimumHeight(800)

            # Инициализация атрибутов
            self._setup_attributes()

            # Создание интерфейса
            self.initUI()

            # Загрузка данных для автозаполнения
            self.load_completion_data()

            # Загружаем список услуг
            self.load_services()

            # Если это редактирование - заполняем поля
            if hasattr(self, 'order_data'):
                self.fill_fields(self.order_data)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при инициализации окна: {str(e)}")

    def get_client_data(self, session, client_name):
        """Получение данных о клиенте с корректным расчетом сумм, скидок и анализом времени оплаты"""
        try:
            # Получаем все заказы клиента (включая отказы для полного анализа)
            all_orders = session.query(Order).filter(
                Order.fio == client_name
            ).all()

            # Получаем все активные заказы клиента (исключаем отказы)
            orders = [o for o in all_orders if o.status != 'Отказ']

            # Инициализируем счетчики
            total_orders = len(orders)
            total_amount = 0
            total_paid = 0
            unpaid_orders = []
            recent_orders = []
            payment_analytics = []  # Для анализа сроков оплаты

            # Обрабатываем каждый заказ
            for order in orders:
                # Проверяем срок действия скидки
                order.check_discount_expiration()

                # Получаем базовую стоимость
                base_cost = order.cost or 0

                # Рассчитываем скидку
                discount = float(order.discount.replace('%', '')) if order.discount else 0
                discount_amount = base_cost * (discount / 100)

                # Рассчитываем итоговую стоимость со скидкой
                final_cost = base_cost - discount_amount

                # Добавляем к общим суммам
                total_amount += final_cost
                total_paid += order.paid_amount or 0

                # Проверяем остаток
                remaining = max(0, final_cost - (order.paid_amount or 0))
                if remaining > 0:
                    unpaid_orders.append({
                        'id': order.id,
                        'service': order.service,
                        'remaining': remaining,
                        'created_date': order.created_date,
                        'discount': order.discount,
                        'base_cost': base_cost,
                        'final_cost': final_cost,
                        'status': order.status
                    })

                # Добавляем в последние заказы
                recent_orders.append({
                    'service': order.service,
                    'base_cost': base_cost,
                    'final_cost': final_cost,
                    'created_date': order.created_date,
                    'status': order.status
                })

                # Анализ времени оплаты (только для оплаченных заказов)
                if order.payment_date and order.created_date and order.status == 'Выполнен':
                    days_to_pay = (order.payment_date - order.created_date).days
                    payment_analytics.append({
                        'id': order.id,
                        'service': order.service,
                        'created_date': order.created_date,
                        'payment_date': order.payment_date,
                        'days_to_pay': days_to_pay,
                        'amount': final_cost
                    })

            # Сортируем последние заказы по дате
            recent_orders.sort(key=lambda x: x['created_date'], reverse=True)
            recent_orders = recent_orders[:3]  # Оставляем только последние 3

            # Рассчитываем рекомендуемую скидку на основе активных заказов
            recommended_discount = 0
            discount_reason = []

            if total_orders >= 10:
                recommended_discount = 30
                discount_reason.append(f"🌟 {total_orders} выполненных заказов")
            elif total_orders >= 5:
                recommended_discount = 20
                discount_reason.append(f"⭐ {total_orders} выполненных заказов")
            elif total_orders >= 3:
                recommended_discount = 10
                discount_reason.append(f"✨ {total_orders} выполненных заказов")

            if total_paid >= 50000:
                recommended_discount = max(recommended_discount, 25)
                discount_reason.append(f"💰 Общая сумма оплат: {total_paid:,.0f} ₽")

            # Формируем предупреждения только для активных неоплаченных заказов
            warnings = []
            if unpaid_orders:
                total_unpaid = sum(order['remaining'] for order in unpaid_orders)
                warnings.append(f"⚠️ Имеются неоплаченные заказы на сумму: {total_unpaid:,.0f} ₽")

                for order in unpaid_orders:
                    discount_info = f" (скидка {order['discount']})" if order['discount'] != "0%" else ""
                    warnings.append(
                        f"   • Заказ №{order['id']}: {order['service']} - {order['remaining']:,.0f} ₽{discount_info}"
                        f" (от {order['created_date'].strftime('%d.%m.%Y')})"
                    )

            # Формируем рекомендации на основе активных заказов
            recommendations = []
            if recent_orders:
                avg_final_cost = sum(order['final_cost'] for order in recent_orders) / len(recent_orders)
                recommendations.append(f"📊 Средняя стоимость последних заказов: {avg_final_cost:,.0f} ₽")

            if discount_reason:
                recommendations.append(
                    f"🎁 Рекомендуемая скидка {recommended_discount}% по причинам:\n" +
                    "\n".join(f"   • {reason}" for reason in discount_reason)
                )

            # Анализ сроков оплаты для рекомендаций
            payment_stats = {}
            if payment_analytics:
                # Сортируем по дате создания для правильного анализа
                payment_analytics.sort(key=lambda x: x['created_date'])

                payment_stats['total_analyzed'] = len(payment_analytics)
                payment_stats['average_days'] = sum(item['days_to_pay'] for item in payment_analytics) / len(
                    payment_analytics)
                payment_stats['max_days'] = max(item['days_to_pay'] for item in payment_analytics)
                payment_stats['min_days'] = min(item['days_to_pay'] for item in payment_analytics)

                # Добавляем подробную информацию об оплатах
                payment_stats['details'] = []
                for item in sorted(payment_analytics, key=lambda x: x['created_date'], reverse=True):
                    payment_stats['details'].append({
                        'id': item['id'],
                        'service': item['service'],
                        'created_date': item['created_date'],
                        'payment_date': item['payment_date'],
                        'days_to_pay': item['days_to_pay'],
                        'amount': item['amount']
                    })

                # Добавляем рекомендации на основе анализа оплат
                if payment_stats['average_days'] > 20:  # Если среднее время оплаты больше 20 дней
                    recommendations.append(
                        f"⏱️ Внимание! Средний срок оплаты: {payment_stats['average_days']:.1f} дней"
                    )
                    recommendations.append(
                        "💵 Рекомендуется брать предоплату не менее 70%, так как клиент обычно оплачивает с задержкой"
                    )
                elif unpaid_orders:
                    recommendations.append(
                        "⚠️ Рекомендуется сначала запросить оплату по существующим заказам"
                    )

                # Анализируем тренд оплат (улучшается или ухудшается?)
                if len(payment_analytics) >= 3:
                    # Последние три и первые три заказа для сравнения тренда
                    recent_payments = payment_analytics[-3:]
                    early_payments = payment_analytics[:3]

                    recent_avg = sum(item['days_to_pay'] for item in recent_payments) / len(recent_payments)
                    early_avg = sum(item['days_to_pay'] for item in early_payments) / len(early_payments)

                    if recent_avg > early_avg * 1.5:  # Значительное ухудшение
                        recommendations.append(
                            f"📉 Тренд платежной дисциплины ухудшается: с {early_avg:.1f} до {recent_avg:.1f} дней"
                        )
                        recommendations.append(
                            "⚠️ Рекомендуется пересмотреть условия работы и увеличить предоплату"
                        )
                    elif recent_avg < early_avg * 0.7:  # Значительное улучшение
                        recommendations.append(
                            f"📈 Тренд платежной дисциплины улучшается: с {early_avg:.1f} до {recent_avg:.1f} дней"
                        )
                        if recommended_discount < 5:
                            recommendations.append(
                                "💡 Можно предложить небольшую скидку (5%) за сохранение хорошей платежной дисциплины"
                            )

            # Получаем общее количество заказов (включая отказы) для информации
            total_orders_with_cancelled = len(all_orders)

            # Добавляем отмененные заказы в статистику
            cancelled_orders = [o for o in all_orders if o.status == 'Отказ']
            if cancelled_orders:
                warnings.append(f"ℹ️ Имеется {len(cancelled_orders)} отмененных заказов")

            return {
                'client_name': client_name,  # Добавляем имя клиента для дальнейшего использования
                'total_orders': total_orders,  # Только активные заказы
                'total_amount': total_amount,  # Сумма с учетом скидок, без отказов
                'total_paid': total_paid,
                'total_unpaid': sum(order['remaining'] for order in unpaid_orders) if unpaid_orders else 0,
                'total_orders_all': total_orders_with_cancelled,  # Общее количество всех заказов
                'recommended_discount': recommended_discount,
                'warnings': warnings,
                'recommendations': recommendations,
                'payment_analytics': payment_stats if payment_analytics else None,  # Добавляем аналитику оплат
                'cancelled_orders': len(cancelled_orders),  # Добавляем количество отмененных заказов
                'all_orders': all_orders  # Сохраняем полный список заказов для дополнительного анализа
            }

        except Exception as e:
            print(f"Ошибка получения данных клиента: {e}")
            return None
    def load_completion_data(self):
        """Загрузка данных для автозаполнения"""
        try:
            # Инициализируем пустые списки по умолчанию
            self._clients_list = []
            self._groups_list = []
            self._directions_list = []
            self._themes_list = []
            self._teachers_list = []
            self._services_list = []
            self._phones_list = []
            self._logins_list = []  # Добавляем список логинов
            self._passwords_list = []  # Добавляем список паролей

            # Получаем данные через DatabaseManager
            with self.db_manager.session_scope() as session:
                results = session.query(
                    Order.fio,
                    Order.group,
                    Order.direction,
                    Order.theme,
                    Order.teacher_name,
                    Order.service,
                    Order.phone,
                    Order.login,  # Добавляем логин
                    Order.password  # Добавляем пароль
                ).all()

                # Заполняем списки только если есть результаты
                if results:
                    self._clients_list = sorted(set(r[0] for r in results if r[0] and r[0] != 'Не указано'))
                    self._groups_list = sorted(set(r[1] for r in results if r[1] and r[1] != 'Не указано'))
                    self._directions_list = sorted(set(r[2] for r in results if r[2] and r[2] != 'Не указано'))
                    self._themes_list = sorted(set(r[3] for r in results if r[3] and r[3] != 'Не указано'))
                    self._teachers_list = sorted(set(r[4] for r in results if r[4] and r[4] != 'Не указано'))
                    self._services_list = sorted(set(r[5] for r in results if r[5] and r[5] != 'Не указано'))
                    self._phones_list = sorted(set(r[6] for r in results if r[6] and r[6] != 'Не указано'))
                    self._logins_list = sorted(set(r[7] for r in results if r[7] and r[7] != 'Не указано'))
                    self._passwords_list = sorted(set(r[8] for r in results if r[8] and r[8] != 'Не указано'))

            # Настраиваем автозаполнение
            self.setup_completers()

        except Exception as e:
            print(f"Ошибка загрузки данных для автозаполнения: {e}")

    def setup_completers(self):
        """Настройка автозаполнения для всех полей"""
        try:
            completers = {
                self.fio_input: self._clients_list,
                self.group_input: self._groups_list,
                self.direction_input: self._directions_list,
                self.theme_input: self._themes_list,
                self.teacher_input: self._teachers_list,
                self.phone_input: self._phones_list,
                self.login_input: self._logins_list,  # Добавляем автозаполнение для логина
                self.password_input: self._passwords_list  # Добавляем автозаполнение для пароля
            }

            for widget, data in completers.items():
                if data:  # Проверяем, что есть данные
                    completer = QCompleter(data)
                    completer.setCaseSensitivity(Qt.CaseInsensitive)
                    completer.setFilterMode(Qt.MatchContains)  # Поиск подстроки
                    widget.setCompleter(completer)

        except Exception as e:
            print(f"Ошибка при настройке автозаполнения: {e}")

    def on_fio_changed(self, text):
        """Обработчик изменения ФИО"""
        try:
            if not text:
                self.client_info.hide()
                return

            with self.db_manager.session_scope() as session:
                # Получаем последний заказ клиента для автозаполнения
                last_order = session.query(Order).filter(
                    Order.fio == text
                ).order_by(Order.created_date.desc()).first()

                if last_order:
                    # Автозаполнение полей из последнего заказа
                    self.group_input.setText(last_order.group)
                    self.phone_input.setText(last_order.phone or '')
                    self.teacher_input.setText(last_order.teacher_name or '')
                    self.teacher_email_input.setText(last_order.teacher_email or '')

                    # Добавляем автозаполнение логина и пароля
                    if last_order.login and last_order.login != 'Не указано':
                        self.login_input.setText(last_order.login)
                    if last_order.password and last_order.password != 'Не указано':
                        self.password_input.setText(last_order.password)

                # Получаем детальные данные о клиенте с аналитикой оплат
                client_data = self.get_client_data(session, text)
                if client_data:
                    self.client_info.update_info(client_data)

                    # Устанавливаем рекомендуемую скидку
                    if client_data['recommended_discount'] > 0:
                        recommended_discount = f"{client_data['recommended_discount']}%"
                        index = self.discount_combo.findText(recommended_discount)
                        if index >= 0:
                            self.discount_combo.setCurrentIndex(index)
                else:
                    self.client_info.hide()

        except Exception as e:
            print(f"Ошибка при обновлении информации о клиенте: {e}")
            self.client_info.hide()

    def _setup_attributes(self):
        """Инициализация базовых атрибутов"""
        # Кэшированные данные
        self._services_list = None
        self._clients_list = None
        self._groups_list = None
        self._directions_list = None
        self._themes_list = None
        self._teachers_list = None

        # UI компоненты
        self.client_info = ClientInfoWidget()
        self.discount_info_label = QLabel()
        self.discount_info_label.hide()

        # Основные поля ввода
        self.fio_input = QLineEdit()
        self.group_input = QLineEdit()
        self.services_combo = QComboBox()
        self.services_combo.setEditable(True)

        # Дополнительные поля
        self.direction_input = QLineEdit()
        self.theme_input = QLineEdit()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(1000)

        # Данные доступа
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.website_input = QLineEdit()

        # Финансовые поля
        # Улучшенные поля для сумм
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setMaximum(1000000)
        self.cost_spin.setPrefix("₽ ")
        self.cost_spin.setStyleSheet("""
                QDoubleSpinBox {
                    padding: 8px 15px;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    background: white;
                    font-size: 14px;
                    font-weight: bold;
                    color: #2196F3;
                }
                QDoubleSpinBox:focus {
                    border-color: #2196F3;
                    background: #f8f9fa;
                }
                QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                    width: 25px;
                    border-radius: 4px;
                    background: #f5f5f5;
                    border: 1px solid #e0e0e0;
                }
                QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                    background: #e0e0e0;
                }
            """)
        self.cost_spin.setMinimumWidth(200)

        # Аналогично для поля предоплаты
        self.prepay_spin = QDoubleSpinBox()
        self.prepay_spin.setMaximum(1000000)
        self.prepay_spin.setPrefix("₽ ")
        self.prepay_spin.setStyleSheet(self.cost_spin.styleSheet())
        self.prepay_spin.setMinimumWidth(200)

        self.discount_combo = QComboBox()
        self.discount_combo.addItems(['0%', '5%', '10%', '15%', '20%', '25%', '30%', '35%', '40%', '45%', '50%'])

        self.deadline_combo = QComboBox()
        self.deadline_combo.addItems(['1 день','2 дня','3 дня', '5 дней', '7 дней', '14 дней', '1 месяц'])

        # Контактные данные
        self.phone_input = QLineEdit()
        self.teacher_input = QLineEdit()
        self.teacher_email_input = QLineEdit()
        self.comment_text = QTextEdit()

    def _ensure_ui_elements_exist(self):
        """Проверка существования всех необходимых элементов UI"""
        required_elements = [
            'fio_input', 'group_input', 'phone_input',
            'teacher_input', 'teacher_email_input',
            'login_input', 'password_input', 'website_input'
        ]

        missing_elements = []
        for element in required_elements:
            if not hasattr(self, element):
                missing_elements.append(element)

        if missing_elements:
            raise RuntimeError(f"Отсутствуют необходимые элементы UI: {', '.join(missing_elements)}")

    def initUI(self):
        """Инициализация интерфейса"""
        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Создаем область прокрутки и сохраняем её как атрибут класса
        self.scroll_area = QScrollArea()  # Изменено имя на scroll_area
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
        """)

        # Создаем контейнер для содержимого
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(5, 5, 5, 5)

        # Добавляем группы полей
        content_layout.addWidget(self._create_main_group())
        content_layout.addWidget(self._create_access_group())
        content_layout.addWidget(self._create_finance_group())
        content_layout.addWidget(self._create_contact_group())

        # Устанавливаем виджет с контентом в область прокрутки
        self.scroll_area.setWidget(content_widget)

        # Добавляем скролл в основной layout
        main_layout.addWidget(self.scroll_area, 1)

        # Кнопки управления
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_order)
        save_btn.setMinimumWidth(120)
        save_btn.setMinimumHeight(30)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setMinimumHeight(30)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        main_layout.addLayout(button_layout)

        # Устанавливаем фиксированные размеры окна
        self.setMinimumWidth(900)
        self.setMinimumHeight(800)

        # Настраиваем размеры content_widget
        content_widget.setMinimumWidth(880)
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event):
        """Обработка изменения размера окна"""
        super().resizeEvent(event)
        # Обновляем размеры внутренних компонентов при изменении размера окна
        if hasattr(self, 'scroll_area'):
            scroll_width = self.scroll_area.width() - 20  # Используем scroll_area вместо scroll
            content_widget = self.scroll_area.widget()
            if content_widget:
                content_widget.setMinimumWidth(scroll_width)


    def _stage1_init(self):
        """Первый этап инициализации"""
        try:
            # Применяем стили
            self.apply_styles()
            # Запускаем следующий этап
            QTimer.singleShot(100, self._stage2_init)
        except Exception as e:
            print(f"Ошибка stage1: {e}")

    def _stage2_init(self):
        """Второй этап - загрузка данных"""
        try:
            # Загружаем данные для автозаполнения
            self.load_completion_data()
            # Запускаем следующий этап
            QTimer.singleShot(100, self._stage3_init)
        except Exception as e:
            print(f"Ошибка stage2: {e}")

    def _stage3_init(self):
        """Третий этап - настройка компонентов"""
        try:
            # Настраиваем автозаполнение
            self.setup_completers()
            # Загружаем список услуг
            self.load_services()
            # Если это редактирование - заполняем поля
            if self.order:
                self.fill_fields()
        except Exception as e:
            print(f"Ошибка stage3: {e}")

    def fill_fields(self, data=None):
        """Заполнение полей при редактировании"""
        try:
            if not data:
                return

            # Заполняем текстовые поля
            self.fio_input.setText(data.get('fio', ''))
            self.group_input.setText(data.get('group', ''))
            self.direction_input.setText(data.get('direction', ''))
            self.theme_input.setText(data.get('theme', ''))
            self.login_input.setText(data.get('login', ''))
            self.password_input.setText(data.get('password', ''))
            self.website_input.setText(data.get('website', ''))
            self.phone_input.setText(data.get('phone', ''))
            self.teacher_input.setText(data.get('teacher_name', ''))
            self.teacher_email_input.setText(data.get('teacher_email', ''))
            self.comment_text.setPlainText(data.get('comment', ''))

            # Заполняем числовые поля
            self.quantity_spin.setValue(int(data.get('quantity', 1)))
            self.cost_spin.setValue(float(data.get('cost', 0)))
            self.prepay_spin.setValue(float(data.get('paid_amount', 0)))

            # Заполняем комбобоксы
            if data.get('service'):
                index = self.services_combo.findText(data['service'])
                if index >= 0:
                    self.services_combo.setCurrentIndex(index)

            if data.get('deadline'):
                index = self.deadline_combo.findText(data['deadline'])
                if index >= 0:
                    self.deadline_combo.setCurrentIndex(index)

            if data.get('discount'):
                index = self.discount_combo.findText(data['discount'])
                if index >= 0:
                    self.discount_combo.setCurrentIndex(index)

            # Обновляем расчеты
            self.calculate_total_with_discount()

            # Обновляем информацию о клиенте
            self.on_fio_changed(data.get('fio', ''))

        except Exception as e:
            print(f"Ошибка при заполнении полей: {e}")

    def _update_dependent_fields(self):
        """Обновление зависимых полей"""
        try:
            # Обновляем состояние полей в зависимости от значений других полей
            if hasattr(self, 'cost_spin') and hasattr(self, 'prepay_spin'):
                self.calculate_total_with_discount()

            # Обновляем видимость информационных меток
            if hasattr(self, 'discount_info_label'):
                if self.discount_combo.currentText() != '0%':
                    self.discount_info_label.show()
                else:
                    self.discount_info_label.hide()

        except Exception as e:
            print(f"Ошибка при обновлении зависимых полей: {e}")


    def _create_main_group(self):
        """Создание группы основной информации"""
        group = AnimatedGroupBox("Основная информация")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # ФИО
        fio_layout = self._create_input_row(
            "ФИО*:", self.fio_input,
            placeholder="Введите ФИО клиента"
        )
        self.fio_input.textChanged.connect(self.on_fio_changed)
        layout.addLayout(fio_layout)

        # Информация о клиенте
        layout.addWidget(self.client_info)

        # Группа
        group_layout = self._create_input_row(
            "Группа*:", self.group_input,
            placeholder="Введите группу"
        )
        layout.addLayout(group_layout)

        # Услуги
        services_layout = self._create_input_row(
            "Услуги*:", self.services_combo
        )
        layout.addLayout(services_layout)

        return group

    def _create_access_group(self):
        """Создание группы данных для доступа"""
        group = AnimatedGroupBox("Данные для доступа")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Направление
        direction_layout = self._create_input_row(
            "Направление:", self.direction_input,
            placeholder="Введите направление"
        )
        layout.addLayout(direction_layout)

        # Тема
        theme_layout = self._create_input_row(
            "Тема:", self.theme_input,
            placeholder="Введите тему"
        )
        layout.addLayout(theme_layout)

        # Количество
        quantity_layout = self._create_input_row(
            "Количество:", self.quantity_spin
        )
        layout.addLayout(quantity_layout)

        # Логин
        login_layout = self._create_input_row(
            "Логин:", self.login_input,
            placeholder="Введите логин"
        )
        layout.addLayout(login_layout)

        # Пароль
        password_layout = self._create_input_row(
            "Пароль:", self.password_input,
            placeholder="Введите пароль"
        )
        layout.addLayout(password_layout)

        # Сайт
        website_layout = self._create_input_row(
            "Сайт:", self.website_input,
            placeholder="Введите адрес сайта"
        )
        layout.addLayout(website_layout)

        return group

    def _create_finance_group(self):
        """Создание группы финансовой информации"""
        group = AnimatedGroupBox("Финансовая информация")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Стоимость с кнопкой подсчета
        cost_container = QHBoxLayout()
        cost_container.setSpacing(5)  # Уменьшаем отступ между элементами

        # Создаем layout для стоимости с уменьшенной шириной метки
        cost_layout = self._create_input_row(
            "СТОИМОСТЬ*:", self.cost_spin
        )

        # Получаем SpinBox из layout'а и настраиваем его ширину
        self.cost_spin.setMinimumWidth(150)  # Уменьшаем минимальную ширину
        self.cost_spin.valueChanged.connect(self.calculate_total_with_discount)

        # Добавляем кнопку подсчета с уменьшенными размерами
        calculate_btn = ModernButton("Посчитать")
        calculate_btn.setMaximumWidth(120)  # Делаем кнопку уже
        calculate_btn.setMinimumHeight(30)  # Выравниваем высоту с полем ввода
        calculate_btn.clicked.connect(self.calculate_cost_with_quantity)

        # Компонуем элементы плотнее
        cost_container.addLayout(cost_layout)
        cost_container.addWidget(calculate_btn, alignment=Qt.AlignLeft)  # Выравниваем по левому краю
        cost_container.addStretch()  # Добавляем растягивающийся элемент справа
        layout.addLayout(cost_container)

        # Информация о скидке
        layout.addWidget(self.discount_info_label)

        # Скидка
        discount_layout = self._create_input_row(
            "Скидка:", self.discount_combo
        )
        self.discount_combo.currentTextChanged.connect(self.calculate_total_with_discount)
        layout.addLayout(discount_layout)

        # Срок
        deadline_layout = self._create_input_row(
            "Срок*:", self.deadline_combo
        )
        layout.addLayout(deadline_layout)

        # Предоплата
        prepay_layout = self._create_input_row(
            "Предоплата:", self.prepay_spin
        )
        self.prepay_spin.valueChanged.connect(self.calculate_total_with_discount)
        layout.addLayout(prepay_layout)

        # Остаток
        self.remaining_label = QLabel("Остаток: 0.00 ₽")
        self.remaining_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2196F3;
                padding: 10px;
            }
        """)
        layout.addWidget(self.remaining_label)

        return group

    def calculate_cost_with_quantity(self):
        """Расчет стоимости с учетом количества"""
        try:
            # Получаем базовую стоимость и количество
            base_cost = self.cost_spin.value()
            quantity = self.quantity_spin.value()

            # Рассчитываем общую стоимость
            total_cost = base_cost * quantity

            # Обновляем значение в спиннере стоимости
            self.cost_spin.setValue(total_cost)

            # Пересчитываем итоговую сумму с учетом скидки
            self.calculate_total_with_discount()

        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Ошибка при расчете стоимости: {str(e)}")


    def _create_contact_group(self):
        """Создание группы контактной информации"""
        group = AnimatedGroupBox("Контактная информация")
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # Телефон
        phone_layout = self._create_input_row(
            "Телефон:", self.phone_input,
            placeholder="Введите номер телефона"
        )
        layout.addLayout(phone_layout)

        # ФИО преподавателя
        teacher_layout = self._create_input_row(
            "ФИО ПРЕПОДАВАТЕЛЯ:", self.teacher_input,
            placeholder="Введите ФИО преподавателя"
        )
        layout.addLayout(teacher_layout)

        # Почта преподавателя
        email_layout = self._create_input_row(
            "ПОЧТА ПРЕПОДАВАТЕЛЯ:", self.teacher_email_input,
            placeholder="Введите email преподавателя"
        )
        layout.addLayout(email_layout)

        # Комментарий
        layout.addWidget(QLabel("Комментарий:"))
        self.comment_text.setPlaceholderText("Введите комментарий к заказу")
        self.comment_text.setMinimumHeight(100)
        layout.addWidget(self.comment_text)

        return group

    def _create_input_row(self, label_text, widget, placeholder=None):
        """Создание строки с полем ввода и подсказками"""
        layout = QHBoxLayout()
        layout.setSpacing(10)  # Уменьшаем отступы между элементами
        layout.setContentsMargins(5, 2, 5, 2)  # Делаем компактные отступы

        # Метка
        label = QLabel(label_text)
        label.setMinimumWidth(150)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Выравнивание по правому краю и центру
        layout.addWidget(label)

        # Контейнер для виджета и подсказок
        input_container = QVBoxLayout()
        input_container.setSpacing(2)  # Минимальный отступ между элементами
        input_container.setContentsMargins(0, 0, 0, 0)

        # Настраиваем виджет ввода
        if placeholder and hasattr(widget, 'setPlaceholderText'):
            widget.setPlaceholderText(placeholder)
        if hasattr(widget, 'setMinimumWidth'):
            widget.setMinimumWidth(250)

        input_container.addWidget(widget)
        widget.setMinimumHeight(30)  # Фиксированная высота для единообразия

        layout.addLayout(input_container)
        layout.addStretch()  # Добавляем растягивающийся элемент справа

        return layout

    def copy_to_clipboard(self, text):
        """Копирование текста в буфер обмена"""
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Успех", "Скопировано в буфер обмена")

    def load_services(self):
        """Загрузка списка услуг из базы данных"""
        try:
            with self.db_manager.session_scope() as session:
                # Получаем все уникальные услуги
                services = session.query(Order.service).distinct().all()
                unique_services = sorted(set(service[0] for service in services if service[0]))

                # Очищаем комбобокс
                self.services_combo.clear()

                if unique_services:
                    # Добавляем услуги в комбобокс
                    self.services_combo.addItems(unique_services)

                    # Если это редактирование, выбираем текущую услугу
                    if hasattr(self, 'order_data') and self.order_data.get('service'):
                        index = self.services_combo.findText(self.order_data['service'])
                        if index >= 0:
                            self.services_combo.setCurrentIndex(index)

                # Настраиваем автодополнение
                completer = QCompleter(unique_services)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                self.services_combo.setCompleter(completer)

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка при загрузке услуг: {str(e)}")



    def calculate_recommended_discount(self, total_orders):
        """Расчет рекомендуемой скидки"""
        if total_orders >= 10:
            return 30
        elif total_orders >= 5:
            return 20
        elif total_orders >= 3:
            return 10
        return 0

    def calculate_total_with_discount(self):
        """Расчет итоговой суммы с учетом скидки"""
        try:
            # Получаем базовую стоимость
            base_cost = self.cost_spin.value()
            if base_cost <= 0:
                self.discount_info_label.hide()
                self.remaining_label.setText("Остаток: 0.00 ₽")
                return

            # Получаем скидку
            discount_text = self.discount_combo.currentText()
            discount = float(discount_text.replace('%', '')) if discount_text else 0

            # Расчеты
            discount_amount = base_cost * (discount / 100)
            final_cost = base_cost - discount_amount
            prepayment = self.prepay_spin.value()

            # Правильный расчет остатка с учетом скидки
            remaining = max(0, final_cost - prepayment)

            # Обновляем информацию о скидке
            if discount > 0:
                self.discount_info_label.setText(
                    f"💰 Базовая стоимость: {base_cost:,.2f} ₽\n"
                    f"🎁 Скидка ({discount}%): {discount_amount:,.2f} ₽\n"
                    f"✨ Итоговая стоимость: {final_cost:,.2f} ₽"
                )
                self.discount_info_label.show()
            else:
                self.discount_info_label.hide()

            # Обновляем остаток
            self.remaining_label.setText(f"Остаток: {remaining:,.2f} ₽")
            self.remaining_label.setStyleSheet(
                f"color: {'#f44336' if remaining > 0 else '#4caf50'};"
                "font-size: 14px; font-weight: bold;"
            )

            return final_cost, remaining

        except Exception as e:
            print(f"Ошибка расчета стоимости: {e}")
            return base_cost, base_cost - prepayment

    def check_discount_expiration(self):
        """Проверка срока действия скидки"""
        if self.discount_end_date and datetime.now() > self.discount_end_date:
            self.discount = "0%"
            self.discount_start_date = None
            self.discount_end_date = None
            return True
        return False

    def recalculate_remaining(self):
        """Пересчет остатка с учетом скидки"""
        try:
            # Проверяем срок действия скидки
            self.check_discount_expiration()

            # Получаем базовую стоимость
            base_cost = self.cost or 0

            # Рассчитываем скидку
            discount = float(self.discount.replace('%', '')) if self.discount else 0
            discount_amount = base_cost * (discount / 100)

            # Рассчитываем итоговую стоимость со скидкой
            final_cost = base_cost - discount_amount

            # Рассчитываем остаток
            self.remaining_amount = max(0, final_cost - (self.paid_amount or 0))

            return self.remaining_amount

        except Exception as e:
            print(f"Ошибка при пересчете остатка: {e}")
            return 0

    def save_order(self):
        """Сохранение заказа"""
        try:
            if not self.validate_fields():
                return

            # Рассчитываем итоговую стоимость с учетом скидки
            final_cost, remaining = self.calculate_total_with_discount()

            # Собираем данные с формы
            base_cost = self.cost_spin.value()
            discount_text = self.discount_combo.currentText()
            prepayment = self.prepay_spin.value()

            # Функция для обработки пустых значений
            def get_value_or_default(value):
                return value.strip() if isinstance(value, str) and value.strip() else "Не указано"

            order_data = {
                'fio': self.fio_input.text(),  # Обязательное поле
                'group': self.group_input.text(),  # Обязательное поле
                'service': self.services_combo.currentText(),  # Обязательное поле
                'direction': get_value_or_default(self.direction_input.text()),
                'theme': get_value_or_default(self.theme_input.text()),
                'quantity': self.quantity_spin.value(),
                'login': get_value_or_default(self.login_input.text()),
                'password': get_value_or_default(self.password_input.text()),
                'website': get_value_or_default(self.website_input.text()),
                'cost': base_cost,  # Базовая стоимость без скидки
                'paid_amount': prepayment,
                'remaining_amount': remaining,
                'total_amount': final_cost,  # Итоговая стоимость со скидкой
                'discount': discount_text,
                'teacher_name': get_value_or_default(self.teacher_input.text()),
                'teacher_email': get_value_or_default(self.teacher_email_input.text()),
                'phone': get_value_or_default(self.phone_input.text()),
                'deadline': self.deadline_combo.currentText(),
                'comment': get_value_or_default(self.comment_text.toPlainText())
            }

            with self.db_manager.session_scope() as session:
                try:
                    if self.order_id:  # Редактирование существующего заказа
                        # Получаем заказ из базы по ID
                        order = session.query(Order).get(self.order_id)
                        if not order:
                            raise ValueError(f"Заказ с ID {self.order_id} не найден")

                        # Сохраняем текущий статус
                        current_status = order.status

                        # Обновляем данные
                        for key, value in order_data.items():
                            setattr(order, key, value)

                        # Восстанавливаем статус
                        order.status = current_status

                    else:  # Создание нового заказа
                        order_data['status'] = 'Новый'
                        order = Order(**order_data)
                        session.add(order)

                    # Пересчитываем остаток с учетом скидки
                    order.recalculate_remaining()

                    # Сохраняем изменения
                    session.flush()  # Убеждаемся, что у заказа есть ID

                    # Создаем папки для документов
                    try:
                        base_path = r"D:\Users\mgurbanmuradov\Documents\Общая"
                        client_path = os.path.join(base_path, order_data['fio'])
                        service_path = os.path.join(client_path, order_data['service'])

                        os.makedirs(service_path, exist_ok=True)

                        # Предлагаем создать файлы из шаблонов
                        from ui.windows.template_selector import TemplateSelector
                        reply = QMessageBox.question(
                            self,
                            'Создание файлов',
                            f"{'Заказ успешно обновлен!' if self.order_id else 'Заказ успешно создан!'}\nСоздать файлы из шаблонов?",
                            QMessageBox.Yes | QMessageBox.No
                        )

                        if reply == QMessageBox.Yes:
                            dialog = TemplateSelector(
                                self,
                                client_name=order_data['fio'],
                                service_name=order_data['service'],
                                direction=order_data.get('direction', '')
                            )
                            dialog.exec_()

                    except Exception as e:
                        QMessageBox.warning(self, "Предупреждение",
                                            f"Ошибка при создании папки: {str(e)}")

                    # Завершаем транзакцию
                    session.commit()

                    # Уведомляем об изменениях
                    self.state_manager.notify_all()
                    self.accept()

                except Exception as e:
                    session.rollback()
                    raise Exception(f"Ошибка при сохранении данных: {str(e)}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении: {str(e)}")



    def create_order_folders(self, client_fio, service_name):
        """Создание структуры папок для заказа"""
        try:
            # Базовый путь к папкам клиентов
            base_path = r"D:\Users\mgurbanmuradov\Documents\Общая"
            client_path = os.path.join(base_path, client_fio)
            service_path = os.path.join(client_path, service_name)

            # Создаем папки
            os.makedirs(service_path, exist_ok=True)

            # Спрашиваем пользователя об открытии папки
            reply = QMessageBox.question(
                self,
                'Открыть папку',
                'Открыть папку с документами?',
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                os.startfile(service_path)

        except Exception as e:
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"Ошибка при создании папки заказа: {str(e)}"
            )
    def create_client_folder(self, fio, service):
        """Создание структуры папок для клиента"""
        try:
            base_path = r"D:\Users\mgurbanmuradov\Documents\Общая"
            client_path = os.path.join(base_path, fio)
            works_path = os.path.join(client_path, "Работы")
            service_path = os.path.join(works_path, service)

            os.makedirs(service_path, exist_ok=True)
            return service_path

        except Exception as e:
            QMessageBox.warning(self, "Предупреждение",
                                f"Ошибка создания папки: {str(e)}")
            return None

    def validate_fields(self):
        """Проверка обязательных полей"""
        required = {
            'ФИО': self.fio_input.text(),
            'Группа': self.group_input.text(),
            'Услуга': self.services_combo.currentText(),
            'Стоимость': self.cost_spin.value()
        }

        empty = [name for name, value in required.items() if not value]

        if empty:
            QMessageBox.warning(
                self, "Предупреждение",
                f"Заполните обязательные поля: {', '.join(empty)}"
            )
            return False

        return True

    def apply_styles(self):
        """Применение единого стиля к окну"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 4px;
            }

            QGroupBox {
                background-color: #f7f9fc;
                border: 1px solid #cfd8e3;
                border-radius: 6px;
                margin-top: 6px;
                padding: 6px;
                font-weight: 600;
                font-size: 14px;
            }

            QLabel {
                color: #2c3e50;
                font-size: 14px;
                padding: 4px 6px;
                qproperty-alignment: AlignVCenter | AlignRight;
            }

            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #cfd8e3;
                border-radius: 4px;
                background-color: white;
                color: #2c3e50;
                font-size: 14px;
                min-width: 160px;
                margin: 2px 0;
            }

            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #0056b3;
                background-color: #e3f2fd;
            }

            QPushButton {
                background-color: #0056b3;
                color: white;
                border: none;
                padding: 5px 8px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 14px;
                margin-top: 4px;
            }

            QPushButton:hover {
                background-color: #004494;
            }

            QScrollArea {
                border: none;
                background-color: transparent;
            }

            QScrollBar:vertical {
                border: none;
                background: #dee2e6;
                width: 6px;
                border-radius: 3px;
            }

            QScrollBar::handle:vertical {
                background: #adb5bd;
                border-radius: 3px;
                min-height: 18px;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
