from datetime import datetime, timedelta
import logging
from sqlalchemy import and_
from core.database import Order

# Настройка логирования
logging.basicConfig(
    filename='discounts.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class DiscountManager:
    """Менеджер для управления скидками"""

    @staticmethod
    def apply_waiting_discount(session, order):
        """Применение скидки при переходе в статус ожидания оплаты"""
        try:
            # Устанавливаем даты действия скидки
            order.discount_start_date = datetime.now()
            order.discount_end_date = order.discount_start_date + timedelta(days=4)

            # Устанавливаем скидку 10%
            order.discount = "10%"

            # Пересчитываем остаток с учетом скидки
            order.recalculate_remaining()

            # Логируем применение скидки
            logging.info(
                f"Применена скидка для заказа #{order.id}. "
                f"Клиент: {order.fio}. "
                f"Действует до: {order.discount_end_date}"
            )

            return True

        except Exception as e:
            logging.error(f"Ошибка при применении скидки: {str(e)}")
            return False

    @staticmethod
    def check_expired_discounts(session):
        """Проверка и обнуление истекших скидок"""
        try:
            # Находим заказы с истекшими скидками
            expired_orders = session.query(Order).filter(
                and_(
                    Order.status == 'В ожидании оплаты',
                    Order.discount_end_date < datetime.now(),
                    Order.discount != "0%"
                )
            ).all()

            for order in expired_orders:
                # Обнуляем скидку
                order.discount = "0%"
                order.discount_start_date = None
                order.discount_end_date = None

                # Пересчитываем остаток
                order.recalculate_remaining()

                # Логируем обнуление скидки
                logging.info(
                    f"Скидка обнулена для заказа #{order.id}. "
                    f"Клиент: {order.fio}"
                )

            return expired_orders

        except Exception as e:
            logging.error(f"Ошибка при проверке истекших скидок: {str(e)}")
            return []

    @staticmethod
    def get_upcoming_expirations(session, days_threshold=1):
        """Получение списка скидок, которые скоро истекут"""
        try:
            threshold_date = datetime.now() + timedelta(days=days_threshold)

            # Находим заказы со скидками, которые скоро истекут
            upcoming_orders = session.query(Order).filter(
                and_(
                    Order.status == 'В ожидании оплаты',
                    Order.discount_end_date <= threshold_date,
                    Order.discount_end_date > datetime.now(),
                    Order.discount != "0%"
                )
            ).all()

            # Логируем информацию о скидках, которые скоро истекут
            for order in upcoming_orders:
                days_left = (order.discount_end_date - datetime.now()).days
                logging.info(
                    f"Скидка для заказа #{order.id} истекает через {days_left} дней. "
                    f"Клиент: {order.fio}"
                )

            return upcoming_orders

        except Exception as e:
            logging.error(f"Ошибка при проверке истекающих скидок: {str(e)}")
            return []