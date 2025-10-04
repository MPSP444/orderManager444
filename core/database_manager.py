from sqlalchemy import create_engine, or_, and_, desc, func
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from .database import Base, Order
import uuid
import urllib.parse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from ui.windows.state_manager import StateManager


class DatabaseManager:
    """Менеджер базы данных"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Инициализация подключения к базе данных"""
        self.engine = create_engine('sqlite:///orders.db')
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        self.state_manager = StateManager()
        logger.info("База данных инициализирована")

    @contextmanager
    def session_scope(self):
        """Контекстный менеджер для работы с сессией"""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка в сессии: {str(e)}")
            raise
        finally:
            session.close()

    def get_order(self, order_id: int) -> Optional[Order]:
        """Получение заказа по ID"""
        with self.session_scope() as session:
            return session.query(Order).get(order_id)

    def create_order(self, data: Dict[str, Any]) -> Order:
        """Создание нового заказа"""
        with self.session_scope() as session:
            order = Order(**data)
            session.add(order)
            session.commit()
            self.state_manager.notify_all()  # Добавляем уведомление
            return order

    def update_order(self, order_id: int, data: Dict[str, Any]) -> bool:
        """Обновление заказа"""
        with self.session_scope() as session:
            order = session.query(Order).get(order_id)
            if order:
                for key, value in data.items():
                    setattr(order, key, value)
                order.recalculate_remaining()
                self.state_manager.notify_all()  # Добавляем уведомление
                return True
            return False

    def generate_review_link(self, data):
        """
        Генерирует ссылку для отзыва клиента

        Args:
            data: Словарь с данными о клиенте и заказе

        Returns:
            Ссылка на страницу отзыва
        """
        try:
            # Получаем ID заказа
            order_id = data.get('order_id')
            if not order_id:
                print(f"Ошибка: ID заказа не найден для клиента {data.get('fio', '')}")
                return None

            # Получаем данные из конфигурации
            from core.config import SITE_CONFIG

            base_url = SITE_CONFIG.get('base_url', 'https://mpsp.online')
            reviews_page = SITE_CONFIG.get('reviews_page', '/submit-review.html')

            # Получаем данные о заказе
            with self.db_manager.session_scope() as session:
                order = session.query(Order).get(order_id)
                if not order:
                    print(f"Ошибка: Заказ #{order_id} не найден в базе данных")
                    return None

                # Кодируем параметры для URL
                service_encoded = urllib.parse.quote(order.service or "")
                name_encoded = urllib.parse.quote(order.fio or "")

                # Генерируем уникальный идентификатор (можно использовать ID заказа)
                # Или создать новый токен если нужна дополнительная безопасность
                token = str(uuid.uuid4())

                # Сохраняем токен в заказе
                order.review_token = token
                session.commit()

                # Формируем ссылку
                review_link = f"{base_url}{reviews_page}?token={token}&order={order_id}&service={service_encoded}&name={name_encoded}"
                print(f"Сгенерирована ссылка для отзыва заказа #{order_id}: {review_link}")

                return review_link

        except Exception as e:
            print(f"Ошибка при генерации ссылки для отзыва: {str(e)}")
            return None

    def check_completed_orders(self) -> list:
        """Проверяет заказы, которые только что были отмечены как выполненные

        Returns:
            Список ID заказов, которые были только что отмечены как выполненные
        """
        completed_order_ids = []

        with self.session_scope() as session:
            try:
                # Получаем все заказы со статусом "Выполнен"
                recently_completed_orders = session.query(Order).filter(Order.status == 'Выполнен').all()

                # Проверяем, какие из них были только что отмечены как выполненные
                for order in recently_completed_orders:
                    if getattr(order, '_status_changed_to_completed', False):
                        completed_order_ids.append(order.id)
                        # Сбрасываем флаг, чтобы не показывать сообщение снова
                        order._status_changed_to_completed = False

                return completed_order_ids

            except Exception as e:
                logger.error(f"Ошибка при проверке выполненных заказов: {str(e)}")
                return []

    def get_orders_by_status(self, filters=None) -> List[Order]:
        """Получение заказов с полными данными по статусу"""
        with self.session_scope() as session:
            try:
                # Базовый запрос
                query = session.query(Order)

                # Применяем фильтры по статусу, если они есть
                if filters:
                    query = query.filter(Order.status.in_(filters))

                # Получаем заказы
                orders = query.all()

                # Преобразуем в словари с полными данными
                result = []
                for order in orders:
                    order_dict = {
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
                        'discount': order.discount,
                        'teacher_name': order.teacher_name,
                        'teacher_email': order.teacher_email,
                        'phone': order.phone,
                        'created_date': order.created_date.strftime('%d.%m.%Y') if order.created_date else None,
                        'deadline': order.deadline,
                        'payment_date': order.payment_date.strftime('%d.%m.%Y') if order.payment_date else None,
                        'comment': order.comment,
                        'status': order.status
                    }
                    result.append(order_dict)

                return result

            except Exception as e:
                logger.error(f"Ошибка при получении заказов: {str(e)}")
                return []
    def delete_order(self, order_id: int) -> bool:
        """Удаление заказа"""
        with self.session_scope() as session:
            order = session.query(Order).get(order_id)
            if order:
                session.delete(order)
                self.state_manager.notify_all()  # Добавляем уведомление
                return True
            return False

    def update_order_discount(self, order_id, discount, start_date, end_date):
        """Обновление скидки заказа"""
        with self.session_scope() as session:
            try:
                order = session.query(Order).get(order_id)
                if order:
                    order.discount = discount
                    order.discount_start_date = start_date
                    order.discount_end_date = end_date
                    session.commit()
                    return True
            except Exception as e:
                print(f"Ошибка при обновлении скидки: {str(e)}")
                return False
    def add_payment(self, order_id: int, amount: float) -> bool:
        """Добавление оплаты"""
        with self.session_scope() as session:
            order = session.query(Order).get(order_id)
            if order:
                order.add_payment(amount)
                self.state_manager.notify_all()  # Добавляем уведомление
                return True
            return False

    def get_order(self, order_id: int) -> Optional[Order]:
        """Оптимизированное получение заказов"""
        if not order_id:
            return None
        with self.session_scope() as session:
            try:
                return session.query(Order).get(order_id)
            except Exception as e:
                logger.error(f"Ошибка при получении заказа: {str(e)}")
                return None
            # Добавляем только нужные колонки
            query = query.with_entities(
                Order.id, Order.fio, Order.group,
                Order.service, Order.deadline, Order.cost,
                Order.paid_amount, Order.remaining_amount,
                Order.discount, Order.status
            )

            # Оптимизируем фильтры
            if filters:
                query = query.filter(Order.status.in_(filters))

            # Добавляем индекс по status если его нет
            if not session.bind.dialect.has_index(
                    session.bind, Order.__table__.name, 'ix_orders_status'
            ):
                session.execute(
                    'CREATE INDEX ix_orders_status ON orders (status)'
                )

            return query.all()
    def search_orders(self, search_text: str) -> List[Order]:
        """Поиск заказов по тексту"""
        with self.session_scope() as session:
            search_pattern = f"%{search_text}%"
            return session.query(Order).filter(
                or_(
                    Order.fio.ilike(search_pattern),
                    Order.group.ilike(search_pattern),
                    Order.service.ilike(search_pattern),
                    Order.phone.ilike(search_pattern)
                )
            ).all()

    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики"""
        with self.session_scope() as session:
            total_orders = session.query(Order).count()
            completed_orders = session.query(Order).filter(
                Order.status == 'Выполнен'
            ).count()
            total_income = session.query(func.sum(Order.paid_amount)).scalar() or 0
            active_orders = session.query(Order).filter(
                Order.status.in_(['Новый', 'В работе'])
            ).count()

            return {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'total_income': total_income,
                'active_orders': active_orders
            }

    def get_unique_services(self) -> List[str]:
        """Получение списка уникальных услуг"""
        with self.session_scope() as session:
            return [r[0] for r in session.query(Order.service).distinct().all()]

    def get_client_orders(self, fio: str) -> List[Order]:
        """Получение всех заказов клиента"""
        with self.session_scope() as session:
            return session.query(Order).filter(Order.fio == fio).all()

    def import_orders(self, data: List[Dict[str, Any]]) -> bool:
        """Импорт заказов из внешнего источника"""
        try:
            with self.session_scope() as session:
                for order_data in data:
                    order = Order(**order_data)
                    session.add(order)
                return True
        except Exception as e:
            logger.error(f"Ошибка при импорте данных: {str(e)}")
            return False