from datetime import datetime, timedelta

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
import pandas as pd
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String


Base = declarative_base()

_engine = None
_Session = None
_indexes_created = False

def get_engine():
    """Получение единого экземпляра engine"""
    global _engine
    if _engine is None:
        _engine = create_engine('sqlite:///orders.db')
    return _engine

def get_session_factory():
    """Получение фабрики сессий"""
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=get_engine())
    return _Session

def init_database():
    """Инициализация базы данных"""
    engine = get_engine()
    inspector = inspect(engine)

    # Проверяем существование таблицы через inspector
    if not inspector.has_table('orders'):
        Base.metadata.create_all(engine)
        create_indexes(engine)
        create_search_indices(engine)

    return get_session_factory()()

def create_indexes(engine):
    """Создание индексов один раз при инициализации БД"""
    global _indexes_created
    if _indexes_created:
        return

    with engine.connect() as conn:
        indexes = [
            'CREATE INDEX IF NOT EXISTS ix_orders_status ON orders (status)',
            'CREATE INDEX IF NOT EXISTS ix_orders_created_date ON orders (created_date)',
            'CREATE INDEX IF NOT EXISTS ix_orders_fio ON orders (fio)'
        ]

        for sql in indexes:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as e:
                print(f"Ошибка при создании индекса: {e}")

    _indexes_created = True

def create_search_indices(engine):
    """Создание индексов для оптимизации поиска"""
    with engine.connect() as conn:
        indices = [
            'CREATE INDEX IF NOT EXISTS idx_orders_fio_lower ON orders (lower(fio))',
            'CREATE INDEX IF NOT EXISTS idx_orders_group_lower ON orders (lower(group))',
            'CREATE INDEX IF NOT EXISTS idx_orders_service_lower ON orders (lower(service))',
            'CREATE INDEX IF NOT EXISTS idx_orders_phone_lower ON orders (lower(phone))',
            'CREATE INDEX IF NOT EXISTS idx_orders_teacher_name_lower ON orders (lower(teacher_name))'
        ]

        for index in indices:
            try:
                conn.execute(text(index))
                conn.commit()
            except Exception as e:
                print(f"Ошибка при создании индекса: {e}")

class Order(Base):
    """Модель заказа в базе данных"""
    __tablename__ = 'orders'

    __table_args__ = (
        Index('ix_orders_status', 'status'),
        Index('ix_orders_created_date', 'created_date'),
        Index('ix_orders_fio', 'fio'),
    )

    # Основная информация
    id = Column(Integer, primary_key=True)
    fio = Column(String(100), nullable=False)
    group = Column(String(50), nullable=False)
    service = Column(String(100), nullable=False)
    direction = Column(String(200))
    theme = Column(Text)
    quantity = Column(Integer, default=1)

    # Доступ к системе
    login = Column(String(100))
    password = Column(String(100))
    website = Column(String(200))

    # Финансовая информация
    cost = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float)
    total_amount = Column(Float)
    discount = Column(String(10))

    # Добавляем новые поля для управления скидками
    discount_start_date = Column(DateTime)
    discount_end_date = Column(DateTime)

    # Контактная информация
    teacher_name = Column(String(100))
    teacher_email = Column(String(100))
    phone = Column(String(20))

    # Даты и сроки
    created_date = Column(Date, default=datetime.now().date)
    deadline = Column(String(50))
    payment_date = Column(Date)

    # Дополнительная информация
    comment = Column(Text)
    status = Column(String(50), default='Новый')
    # Добавьте это новое поле
    review_token = Column(String(100))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'created_date' not in kwargs:
            self.created_date = datetime.now().date()
        if 'status' not in kwargs:
            self.status = 'Новый'
        if 'quantity' not in kwargs:
            self.quantity = 1
        if 'paid_amount' not in kwargs:
            self.paid_amount = 0.0

        if 'cost' in kwargs:
            self.remaining_amount = kwargs['cost'] - (kwargs.get('paid_amount', 0.0))

    def add_payment(self, amount):
        """Добавление оплаты к заказу

        Args:
            amount: Сумма оплаты
        """
        now = datetime.now()

        # Проверяем актуальность скидки перед добавлением оплаты
        if self.discount_end_date:
            if now.date() <= self.discount_end_date.date():
                # Если оплата в срок - сохраняем скидку и дату оплаты
                self.payment_date = now.date()
            else:
                # Если оплата после срока - обнуляем скидку
                print(
                    f"Обнуляем скидку для заказа {self.id} при оплате. Текущая дата: {now.date()}, срок истек: {self.discount_end_date.date()}")
                self.discount = "0%"
                self.discount_start_date = None
                self.discount_end_date = None

        # Добавляем оплату
        self.paid_amount = (self.paid_amount or 0.0) + amount
        self.recalculate_remaining()

        # Если вся сумма оплачена - меняем статус
        if self.remaining_amount <= 0:
            old_status = self.status
            self.status = 'Выполнен'
            self.payment_date = now.date()

            # Если статус изменился на "Выполнен", сохраняем информацию об этом
            # Используем статусное поле, хранящееся в памяти, а не в БД
            self._status_changed_to_completed = old_status != 'Выполнен'

    def recalculate_remaining(self):
        """Пересчет оставшейся суммы с учетом скидки"""
        try:
            print(f"\nПересчет остатка для заказа #{self.id}")
            print(f"Текущая стоимость: {self.cost}")
            print(f"Текущая скидка: {self.discount}")
            print(f"Оплачено: {self.paid_amount}")

            # Базовая стоимость
            cost = float(0 if self.cost == "Не указано" else self.cost)
            paid_amount = float(0 if self.paid_amount == "Не указано" else (self.paid_amount or 0))

            # Если есть скидка
            if self.discount and self.discount != "Не указано" and self.discount != "0%":
                try:
                    discount_percent = float(self.discount.strip('%'))
                    discount_amount = cost * (discount_percent / 100)
                    discounted_cost = cost - discount_amount
                    self.remaining_amount = discounted_cost - paid_amount
                    self.total_amount = discounted_cost
                    print(f"Применена скидка {self.discount}")
                    print(f"Новый остаток: {self.remaining_amount}")
                    return self.remaining_amount
                except (ValueError, AttributeError) as e:
                    print(f"Ошибка при применении скидки: {e}")

            # Без скидки
            self.remaining_amount = cost - paid_amount
            self.total_amount = cost
            print(f"Расчет без скидки, остаток: {self.remaining_amount}")
            return self.remaining_amount

        except Exception as e:
            print(f"Ошибка при пересчете остатка: {e}")
            return 0.0
    def update_discount_dates(self):
        """Обновление дат действия скидки"""
        # Обновляем даты только если заказ в статусе 'В ожидании оплаты'
        if self.status == 'В ожидании оплаты':
            # Если скидка еще не установлена или истекла
            if not self.discount or self.discount == "0%" or not self.discount_end_date:
                self.discount = "10%"
                self.discount_start_date = datetime.now()
                self.discount_end_date = self.discount_start_date + timedelta(days=4)

    def check_discount_expiration(self):
        """Проверка истечения срока действия скидки"""
        try:
            now = datetime.now()
            print(f"DEBUG: Checking discount expiration for order {self.id}")
            print(f"DEBUG: Current discount: {self.discount}")
            print(f"DEBUG: Discount dates: {self.discount_start_date} - {self.discount_end_date}")

            # Если нет скидки или дат - пропускаем
            if not self.discount or not self.discount_end_date:
                print("Нет активной скидки или даты окончания")
                return

            # Для выполненных заказов проверяем дату оплаты
            if self.status == 'Выполнен':
                if self.payment_date and self.payment_date <= self.discount_end_date.date():
                    print("Заказ выполнен, оплата произведена вовремя - сохраняем скидку")
                    return
                else:
                    print("Заказ выполнен, но оплата просрочена - обнуляем скидку")
                    self.discount = "0%"
                    self.discount_start_date = None
                    self.discount_end_date = None
                    return

            # Для остальных статусов проверяем срок действия
            if now > self.discount_end_date:
                print(f"Срок скидки истек {self.discount_end_date}")
                self.discount = "0%"
                self.discount_start_date = None
                self.discount_end_date = None
                self.recalculate_remaining()
                print(f"Скидка обнулена, новый остаток: {self.remaining_amount}")

        except Exception as e:
            print(f"Ошибка при проверке скидки: {e}")

    @classmethod
    def import_from_excel(cls, session, file_path):
        """Импорт данных из Excel"""
        import pandas as pd
        from datetime import datetime, timedelta
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"Начинаем чтение файла: {file_path}")
            df = pd.read_excel(file_path)
            logger.info(f"Найденные колонки в файле: {list(df.columns)}")

            total_rows = 0
            successful_imports = 0
            failed_imports = 0

            for index, row in df.iterrows():
                try:
                    total_rows += 1
                    logger.info(f"\nОбработка строки {index + 1}:")

                    order_data = {}

                    # Базовые поля с проверкой на NaN
                    field_mappings = {
                        'ФИО': 'fio',
                        'Группа': 'group',
                        'Услуга': 'service',
                        'Направление': 'direction',
                        'Тема': 'theme',
                        'Количество': 'quantity',
                        'Логин': 'login',
                        'Пароль': 'password',
                        'Сайт': 'website',
                        'Стоимость': 'cost',
                        'Оплачено': 'paid_amount',
                        'Остаток': 'remaining_amount',
                        'Общая сумма': 'total_amount',
                        'Скидка': 'discount',
                        'ФИО преподавателя': 'teacher_name',
                        'Email преподавателя': 'teacher_email',
                        'Телефон': 'phone',
                        'Комментарий': 'comment',
                        'Статус': 'status'
                    }

                    # Обработка базовых полей
                    for excel_name, db_field in field_mappings.items():
                        if excel_name in df.columns:
                            value = row[excel_name]
                            if pd.notna(value):  # Проверка на NaN
                                if isinstance(value, (int, float)):
                                    if db_field in ['cost', 'paid_amount', 'remaining_amount', 'total_amount']:
                                        order_data[db_field] = float(value)
                                    else:
                                        order_data[db_field] = int(value)
                                else:
                                    # Особая обработка для скидки
                                    if db_field == 'discount':
                                        discount_str = str(value).strip()
                                        if discount_str.endswith('%'):
                                            order_data[db_field] = discount_str
                                        else:
                                            order_data[db_field] = f"{discount_str}%"
                                    else:
                                        order_data[db_field] = str(value).strip()
                            else:
                                if db_field in ['cost', 'paid_amount', 'remaining_amount', 'total_amount']:
                                    order_data[db_field] = 0.0
                                elif db_field == 'quantity':
                                    order_data[db_field] = 1
                                elif db_field == 'discount':
                                    order_data[db_field] = "0%"
                                else:
                                    order_data[db_field] = None

                    # Обработка срока сдачи
                    if 'Срок сдачи' in df.columns:
                        deadline_value = str(row['Срок сдачи']).strip()
                        if pd.isna(row['Срок сдачи']) or deadline_value == 'Не указано' or not deadline_value:
                            order_data['deadline'] = '1 день'
                        else:
                            order_data['deadline'] = deadline_value
                    else:
                        order_data['deadline'] = '1 день'

                    # Обработка дат
                    date_fields = {
                        'Дата создания': 'created_date',
                        'Дата оплаты': 'payment_date',
                        'Дата начала скидки': 'discount_start_date',
                        'Дата окончания скидки': 'discount_end_date'
                    }

                    # Обработка всех дат включая даты скидок
                    for excel_date, db_date in date_fields.items():
                        if excel_date in df.columns and pd.notna(row[excel_date]):
                            try:
                                if isinstance(row[excel_date], str):
                                    try:
                                        # Пробуем разные форматы дат
                                        for date_format in ['%Y-%m-%d', '%d.%m.%Y', '%d.%m.%Y %H:%M:%S']:
                                            try:
                                                date_value = datetime.strptime(row[excel_date], date_format)
                                                break
                                            except ValueError:
                                                continue
                                        else:
                                            raise ValueError(f"Неподдерживаемый формат даты: {row[excel_date]}")
                                    except ValueError as e:
                                        logger.error(f"Ошибка обработки даты {excel_date}: {e}")
                                        if db_date == 'created_date':
                                            date_value = datetime.now()
                                        else:
                                            continue
                                else:
                                    date_value = row[excel_date]
                                    if isinstance(date_value, pd.Timestamp):
                                        date_value = date_value.to_pydatetime()

                                # Обработка дат скидок
                                if db_date in ['discount_start_date', 'discount_end_date']:
                                    order_data[db_date] = date_value
                                else:
                                    order_data[db_date] = date_value.date() if date_value else None

                            except Exception as e:
                                logger.error(f"Ошибка обработки даты {excel_date}: {e}")
                                if db_date == 'created_date':
                                    order_data[db_date] = datetime.now().date()

                    # Автоматическое заполнение дат скидок, если есть скидка, но нет дат
                    if order_data.get('discount') and order_data['discount'] != "0%" and not order_data.get(
                            'discount_start_date'):
                        order_data['discount_start_date'] = datetime.now()
                        order_data['discount_end_date'] = datetime.now() + timedelta(days=4)

                    # Проверка обязательных полей
                    required_fields = ['fio', 'group', 'service']
                    if all(field in order_data for field in required_fields):
                        new_order = cls(**order_data)
                        session.add(new_order)
                        successful_imports += 1

                        # Пересчет остатка с учетом скидки
                        new_order.recalculate_remaining()

                        if successful_imports % 100 == 0:
                            session.commit()
                    else:
                        failed_imports += 1
                        missing_fields = [field for field in required_fields if field not in order_data]
                        logger.error(f"Отсутствуют обязательные поля: {missing_fields}")

                except Exception as e:
                    failed_imports += 1
                    logger.error(f"Ошибка при импорте строки {index + 1}: {str(e)}")
                    continue

            session.commit()
            logger.info(f"""
            Импорт завершен:
            Всего строк: {total_rows}
            Успешно импортировано: {successful_imports}
            Ошибок: {failed_imports}
            """)
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Критическая ошибка при импорте: {str(e)}")
            raise Exception(f"Ошибка при импорте данных: {str(e)}")

    def to_dict(self):
        """Преобразование в словарь для сериализации"""
        return {
            'id': self.id,
            'fio': self.fio,
            'group': self.group,
            'service': self.service,
            'direction': self.direction,
            'theme': self.theme,
            'quantity': self.quantity,
            'login': self.login,
            'password': self.password,
            'website': self.website,
            'cost': self.cost,
            'paid_amount': self.paid_amount,
            'remaining_amount': self.remaining_amount,
            'total_amount': self.total_amount,
            'discount': self.discount,
            'teacher_name': self.teacher_name,
            'teacher_email': self.teacher_email,
            'phone': self.phone,
            'created_date': self.created_date.strftime('%d.%m.%Y') if self.created_date else None,
            'deadline': self.deadline,
            'payment_date': self.payment_date.strftime('%d.%m.%Y') if self.payment_date else None,
            'comment': self.comment,
            'status': self.status,
            'discount_start_date': self.discount_start_date.strftime('%d.%m.%Y %H:%M:%S') if self.discount_start_date else None,
            'discount_end_date': self.discount_end_date.strftime('%d.%m.%Y %H:%M:%S') if self.discount_end_date else None
        }

    def __repr__(self):
        return f"<Order(id={self.id}, fio='{self.fio}', status='{self.status}')>"